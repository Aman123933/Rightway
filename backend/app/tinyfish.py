import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx
from .config import CACHE_DIR, TINYFISH_API_KEY

logger = logging.getLogger("tinyfish")

SEARCH_ENDPOINT = "https://api.search.tinyfish.ai"
FETCH_ENDPOINT = "https://api.fetch.tinyfish.ai"
AGENT_ENDPOINT = "https://agent.tinyfish.ai/v1/automation/run-sse"

class TinyFishClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or TINYFISH_API_KEY

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise ValueError("TINYFISH_API_KEY is not configured.")
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def _get_cache_path(self, prefix: str, key_str: str) -> Any:
        h = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{prefix}_{h}.json"

    def search(self, query: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        TinyFish Search: GET https://api.search.tinyfish.ai?query=... (timeout 10s).
        Retries once on failure.
        """
        cache_file = self._get_cache_path("search", query)
        if use_cache and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        headers = self._get_headers()
        last_error = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(SEARCH_ENDPOINT, params={"query": query}, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
                    return data
            except Exception as e:
                last_error = e
                logger.warning(f"TinyFish search attempt {attempt + 1} failed: {e}")

        raise last_error or RuntimeError("TinyFish search failed.")

    def fetch(self, urls: List[str], live: bool = False, use_cache: bool = True) -> Dict[str, Any]:
        """
        TinyFish Fetch: POST https://api.fetch.tinyfish.ai
        body: {"urls": [...up to 10], "ttl": 0 if live else None}
        Timeout: 150s. Retries once on failure.
        """
        if len(urls) > 10:
            urls = urls[:10]

        cache_key = json.dumps({"urls": sorted(urls), "live": live})
        cache_file = self._get_cache_path("fetch", cache_key)
        if not live and use_cache and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        payload: Dict[str, Any] = {"urls": urls}
        if live:
            payload["ttl"] = 0

        headers = self._get_headers()
        last_error = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=150.0) as client:
                    resp = client.post(FETCH_ENDPOINT, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
                    return data
            except Exception as e:
                last_error = e
                logger.warning(f"TinyFish fetch attempt {attempt + 1} failed: {e}")

        raise last_error or RuntimeError("TinyFish fetch failed.")

    def run_agent_sse(self, url: str, goal: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        TinyFish Agent: POST https://agent.tinyfish.ai/v1/automation/run-sse
        body: {"url": url, "goal": goal}
        Parses SSE stream and extracts COMPLETE event's result.
        Timeout: 120s. Retries once on failure.
        """
        cache_key = json.dumps({"url": url, "goal": goal})
        cache_file = self._get_cache_path("agent", cache_key)
        if use_cache and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"
        payload = {"url": url, "goal": goal}

        last_error = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=120.0) as client:
                    with client.stream("POST", AGENT_ENDPOINT, json=payload, headers=headers) as response:
                        response.raise_for_status()
                        result = self._parse_sse_stream(response.iter_lines())
                        if result is not None:
                            with open(cache_file, "w", encoding="utf-8") as f:
                                json.dump(result, f, ensure_ascii=False)
                            return result
                        raise ValueError("No COMPLETE event received in SSE stream.")
            except Exception as e:
                last_error = e
                logger.warning(f"TinyFish agent attempt {attempt + 1} failed: {e}")

        raise last_error or RuntimeError("TinyFish agent execution failed.")

    @staticmethod
    def _parse_sse_stream(lines_iter) -> Optional[Dict[str, Any]]:
        """Parse SSE lines looking for COMPLETE event payload"""
        current_data = []
        for line in lines_iter:
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            line = line.strip()
            if not line:
                if current_data:
                    joined = "\n".join(current_data)
                    current_data = []
                    try:
                        parsed = json.loads(joined)
                        if parsed.get("type") == "COMPLETE":
                            return parsed.get("result", {})
                    except Exception:
                        pass
                continue
            if line.startswith("data:"):
                data_part = line[5:].strip()
                current_data.append(data_part)

        if current_data:
            joined = "\n".join(current_data)
            try:
                parsed = json.loads(joined)
                if parsed.get("type") == "COMPLETE":
                    return parsed.get("result", {})
            except Exception:
                pass
        return None

def validate_record_against_text(record: Dict[str, Any], source_text: str) -> Optional[Dict[str, Any]]:
    """
    Validation rules:
    - Every email, phone and URL in contacts and portal_url must appear in the source text,
      otherwise drop that field.
    - source_quote must be a verbatim substring of source text, otherwise drop the record (return None).
    """
    if not source_text:
        return None

    # Check source_quote
    quote = record.get("source_quote", "")
    if not quote or quote not in source_text:
        return None

    # Portal URL check
    portal_url = record.get("portal_url")
    if portal_url and portal_url not in source_text:
        record["portal_url"] = None

    # Contacts check
    valid_contacts = []
    for c in record.get("contacts", []):
        contact_dict = dict(c)
        # Check phone
        if contact_dict.get("phone") and contact_dict["phone"] not in source_text:
            contact_dict["phone"] = None
        # Check email
        if contact_dict.get("email") and contact_dict["email"] not in source_text:
            contact_dict["email"] = None
        # Check url
        if contact_dict.get("url") and contact_dict["url"] not in source_text:
            contact_dict["url"] = None

        valid_contacts.append(contact_dict)

    record["contacts"] = valid_contacts
    return record
