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
    path = filepath or LIBRARY_FILE
    temp_path = path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    temp_path.replace(path)

def tokenize(text: str) -> List[str]:
    norm = normalize_text(text)
    return [t for t in re.split(r"\s+", norm) if len(t) > 2]

def rank_records(query: str, category: Optional[str] = None, records: Optional[List[Dict[str, Any]]] = None) -> List[Tuple[Dict[str, Any], float]]:
    """
    Keyword scoring and ranking over library records.
    Filters/boosts by category and weights field matches.
    """
    all_records = records if records is not None else load_library()
    query_tokens = tokenize(query)

    scored: List[Tuple[Dict[str, Any], float]] = []

    for r in all_records:
        rec_categories = r.get("category", [])
        score = 0.0

        # Category match boost
        if category and category in rec_categories:
            score += 5.0
        elif category and category not in rec_categories and category != "other":
            # If a specific category was requested and this record doesn't match, reduce score
            score -= 2.0

        # Title match
        title_norm = normalize_text(r.get("title", ""))
        for qt in query_tokens:
            if qt in title_norm:
                score += 3.0

        # Summary match
        summary_norm = normalize_text(r.get("summary", ""))
        for qt in query_tokens:
            if qt in summary_norm:
                score += 1.5

        # Steps & documents match
        combined_details = normalize_text(" ".join(r.get("steps", []) + r.get("documents", [])))
        for qt in query_tokens:
            if qt in combined_details:
                score += 1.0

        # If query matches category names directly
        for cat in rec_categories:
            if cat in query_tokens:
                score += 2.0

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
