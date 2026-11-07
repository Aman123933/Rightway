import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.config import SOURCES_FILE, LIBRARY_FILE, TINYFISH_API_KEY
from app.tinyfish import TinyFishClient, validate_record_against_text

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("build_library")

AGENT_GOAL = """
Extract official student rights and grievance information into a JSON record with keys:
id, type (rule|office|portal|emergency|crisis|procedure), category (list of strings), title, summary (max 60 words), steps (list of strings), time_limits (list of strings), documents (list of strings), contacts (list of objects with label, phone, email, hours, url, source_id), portal_url, source_url, source_quote (exact verbatim quote under 200 chars from text).
"""

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def build_library(client: Optional[TinyFishClient] = None) -> List[Dict]:
    if not SOURCES_FILE.exists():
        logger.error(f"Sources file not found at {SOURCES_FILE}")
        return []

    # If TinyFish key is missing, leave existing library.json untouched
    if not TINYFISH_API_KEY and client is None:
        logger.warning("TINYFISH_API_KEY missing. Leaving existing library.json untouched.")
        if LIBRARY_FILE.exists():
            with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    if client is None:
        client = TinyFishClient()

    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        sources = json.load(f)

    existing_library = []
    if LIBRARY_FILE.exists():
        try:
            with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
                existing_library = json.load(f)
        except Exception:
            pass

    records: List[Dict] = []
    agent_used_count = 0

    try:
        for src in sources:
            url = src.get("url")
            cat_tag = src.get("category_tag", "other")
            if not url:
                continue

            # Decide whether to use Agent (at most 5 pages)
            is_priority = any(k in url.lower() or k in cat_tag.lower() for k in ["ragging", "grievance", "regulation"])
            if is_priority and agent_used_count < 5:
                try:
                    logger.info(f"Running Agent on priority page: {url}")
                    extracted = client.run_agent_sse(url=url, goal=AGENT_GOAL)
                    agent_used_count += 1
                    # Also fetch raw page text to validate quotes and contacts
                    fetch_res = client.fetch([url])
                    page_text = ""
                    for res_item in fetch_res.get("results", []):
                        if res_item.get("url") == url or res_item.get("final_url") == url:
                            page_text = res_item.get("text", "")
                            break

                    if not page_text and "text" in extracted:
                        page_text = extracted["text"]

                    if page_text:
                        validated = validate_record_against_text(extracted, page_text)
                        if validated:
                            validated["source_url"] = url
                            validated["fetched_at"] = datetime.now(timezone.utc).isoformat()
                            validated["content_hash"] = compute_hash(page_text)
                            validated["status"] = "current"
                            records.append(validated)
                            continue
                except Exception as e:
                    logger.warning(f"Agent extraction failed for {url}: {e}. Falling back to fetch.")

            # Fallback or standard: Fetch
            try:
                fetch_res = client.fetch([url])
                for res_item in fetch_res.get("results", []):
                    text = res_item.get("text", "")
                    if len(text.strip()) < 100:
                        continue
                    # If we already have a record for this url in existing_library, check quote
                    for existing in existing_library:
                        if existing.get("source_url") == url:
                            validated = validate_record_against_text(dict(existing), text)
                            if validated:
                                validated["fetched_at"] = datetime.now(timezone.utc).isoformat()
                                validated["content_hash"] = compute_hash(text)
                                validated["status"] = "current"
                                records.append(validated)
                                break
            except Exception as e:
                logger.warning(f"Fetch failed for {url}: {e}")

        # If call fails or records empty, leave existing library untouched
        if not records:
            logger.warning("No records successfully extracted/validated. Preserving existing library.json.")
            return existing_library

        # Atomic write
        temp_file = LIBRARY_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        temp_file.replace(LIBRARY_FILE)
        logger.info(f"Successfully built library with {len(records)} records.")
        return records

    except Exception as err:
        logger.error(f"Library build encountered fatal error: {err}. Leaving existing library.json untouched.")
        return existing_library

if __name__ == "__main__":
    build_library()
