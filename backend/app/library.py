import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from .config import LIBRARY_FILE, ADMIN_TOKEN
from .safety import normalize_text
from .tinyfish import TinyFishClient

logger = logging.getLogger("library")

def load_library(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    path = filepath or LIBRARY_FILE
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load library: {e}")
        return []

def save_library(records: List[Dict[str, Any]], filepath: Optional[Path] = None) -> None:
    import time
    path = filepath or LIBRARY_FILE
    temp_path = path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # On Windows / OneDrive, atomic replace can transiently encounter WinError 5
    for attempt in range(5):
        try:
            temp_path.replace(path)
            return
        except PermissionError:
            time.sleep(0.05 * (attempt + 1))

    # Fallback if replace is locked by OS/sync agent
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Failed to save library: {e}")

STOP_WORDS = {
    "the", "is", "at", "which", "on", "a", "an", "and", "or", "for", "in", "to",
    "of", "by", "with", "from", "as", "what", "how", "when", "where", "who", "whom",
    "why", "can", "could", "would", "should", "will", "i", "my", "me", "we", "our",
    "you", "your", "he", "she", "it", "they", "them", "their", "this", "that", "these",
    "those", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "but", "if", "so", "than", "too", "very", "just", "about",
    "into", "through", "during", "before", "after", "above", "below", "up", "down",
    "off", "over", "under", "again", "further", "then", "once", "here", "there", "all",
    "any", "both", "each", "few", "more", "most", "some", "such", "no", "nor", "not",
    "only", "own", "same", "tell", "give", "please", "help"
}

def tokenize(text: str) -> List[str]:
    norm = normalize_text(text)
    return [t for t in re.split(r"\s+", norm) if len(t) > 2]

def rank_records(query: str, category: Optional[str] = None, records: Optional[List[Dict[str, Any]]] = None) -> List[Tuple[Dict[str, Any], float]]:
    """
    Keyword scoring and ranking over library records.
    Filters/boosts by category and weights field matches.
    """
    all_records = records if records is not None else load_library()
    raw_tokens = tokenize(query)
    # Filter out common stop words to prevent false-positive matches on words like 'the'
    query_tokens = [t for t in raw_tokens if t not in STOP_WORDS]

    if not query_tokens:
        return []

    scored: List[Tuple[Dict[str, Any], float]] = []

    for r in all_records:
        rec_categories = r.get("category", [])
        text_score = 0.0

        title_tokens = set(tokenize(r.get("title", "")))
        summary_tokens = set(tokenize(r.get("summary", "")))
        detail_tokens = set(tokenize(" ".join(r.get("steps", []) + r.get("documents", []))))

        # Title match
        for qt in query_tokens:
            if qt in title_tokens:
                text_score += 3.0

        # Summary match
        for qt in query_tokens:
            if qt in summary_tokens:
                text_score += 1.5

        # Steps & documents match
        for qt in query_tokens:
            if qt in detail_tokens:
                text_score += 1.0

        # If query matches category names directly
        for cat in rec_categories:
            if cat in query_tokens:
                text_score += 2.0

        score = text_score
        # Category boost only applies if text has relevant matches
        if text_score > 0:
            if category and category in rec_categories:
                if category != "other":
                    score += 4.0
                else:
                    score += 0.5
            elif category and category not in rec_categories and category != "other":
                score -= 2.0
        elif category and category != "other" and category in rec_categories:
            # If user explicitly chose a specific category (not other) but query is generic
            score += 1.5

        if score > 0:
            scored.append((r, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

def perform_recheck(
    record_id: Optional[str] = None,
    all_records: Optional[bool] = None,
    simulate_change: Optional[bool] = None,
    client: Optional[TinyFishClient] = None,
    filepath: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Recheck library records using TinyFish Fetch (ttl: 0) and SHA-256 of normalised text.
    Handles simulate_change: True (admin demo only).
    Max 10 URLs per call.
    """
    records = load_library(filepath)
    if not records:
        return []

    # Select target records
    targets: List[Dict[str, Any]] = []
    if record_id:
        targets = [r for r in records if r.get("id") == record_id]
    elif all_records:
        targets = records[:10]  # Max 10 URLs per call
    else:
        # Default to first record if none specified
        targets = records[:1]

    results: List[Dict[str, Any]] = []

    # Simulation mode
    if simulate_change:
        for r in targets:
            r["status"] = "changed"
            results.append({
                "id": r["id"],
                "status": "changed",
                "changed": True,
                "simulated": True,
                "error": None
            })
        save_library(records, filepath)
        return results

    # Live recheck mode
    if client is None:
        client = TinyFishClient()

    urls_to_fetch = [r["source_url"] for r in targets if r.get("source_url")][:10]
    fetched_data = {}
    fetch_failed = False
    fetch_error = None

    try:
        fetch_res = client.fetch(urls_to_fetch, live=True)
        for res_item in fetch_res.get("results", []):
            url = res_item.get("url") or res_item.get("final_url")
            text = res_item.get("text", "")
            if url:
                fetched_data[url] = text
        for err_item in fetch_res.get("errors", []):
            err_url = err_item.get("url")
            if err_url:
                fetched_data[err_url] = Exception(err_item.get("message", "Fetch error"))
    except Exception as e:
        fetch_failed = True
        fetch_error = str(e)

    for r in targets:
        r_id = r["id"]
        url = r.get("source_url")
        old_hash = r.get("content_hash", "")

        if fetch_failed or (url and isinstance(fetched_data.get(url), Exception)) or (url not in fetched_data):
            err_msg = fetch_error or str(fetched_data.get(url, "Fetch failed"))
            r["status"] = "needs_recheck"
            results.append({
                "id": r_id,
                "status": "needs_recheck",
                "changed": False,
                "simulated": False,
                "error": err_msg
            })
        else:
            new_text = fetched_data[url]
            norm_new = normalize_text(new_text)
            new_hash = hashlib.sha256(norm_new.encode("utf-8")).hexdigest()

            if new_hash != old_hash:
                # Content changed: keep old hash and set status changed
                r["status"] = "changed"
                results.append({
                    "id": r_id,
                    "status": "changed",
                    "changed": True,
                    "simulated": False,
                    "error": None
                })
            else:
                r["status"] = "current"
                results.append({
                    "id": r_id,
                    "status": "current",
                    "changed": False,
                    "simulated": False,
                    "error": None
                })

    save_library(records, filepath)
    return results
