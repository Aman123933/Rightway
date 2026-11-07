import json
import logging
import re
import sys
from urllib.parse import urlparse
from typing import Dict, List, Optional, Set
from app.config import UNIVERSITY_NAME, SOURCES_FILE, TINYFISH_API_KEY
from app.tinyfish import TinyFishClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("discover_sources")

REGULATOR_DOMAINS = {
    "ugc.gov.in",
    "ugc.ac.in",
    "aicte-india.org",
    "antiragging.in",
    "thc.nic.in",
    "telemanas.mohfw.gov.in"
}

DISCOVERY_QUERIES = [
    ("grievance redressal cell", "other"),
    ("anti-ragging committee helpline", "ragging"),
    ("fee refund policy cancellation", "fee_refund"),
    ("scholarship financial aid", "scholarship"),
    ("hostel rules and regulations", "hostel"),
    ("student welfare and contact details", "other"),
    ("examination and evaluation rules", "exam_evaluation"),
    ("student handbook or prospectus", "admission")
]

def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

def is_allowed_domain(domain: str, official_domain: str) -> bool:
    if not domain:
        return False
    if domain == official_domain or domain.endswith("." + official_domain):
        return True
    if domain in REGULATOR_DOMAINS:
        return True
    if domain.endswith(".gov.in") or domain.endswith(".nic.in"):
        return True
    return False

def discover_official_domain(client: TinyFishClient, university_name: str) -> str:
    query = f"{university_name} official website"
    resp = client.search(query)
    results = resp.get("results", [])
    if not results:
        raise ValueError(f"No search results returned for '{query}'")

    top_results = results[:3]
    domains = [extract_domain(r.get("url", "")) for r in top_results if r.get("url")]
    unique_domains = list(dict.fromkeys(domains))

    if len(unique_domains) > 1:
        # Check if they are subdomains or variants of the top result
        top_domain = unique_domains[0]
        for d in unique_domains[1:]:
            if not (d.endswith(top_domain) or top_domain.endswith(d)):
                raise ValueError(
                    f"Ambiguous official domain detected: {unique_domains}. Cannot determine official domain safely."
                )

    official_domain = unique_domains[0]
    print(f"Official domain discovered: {official_domain}")
    return official_domain

def run_discovery(client: Optional[TinyFishClient] = None) -> List[Dict]:
    if client is None:
        client = TinyFishClient()

    print(f"Starting source discovery for: {UNIVERSITY_NAME}")
    official_domain = discover_official_domain(client, UNIVERSITY_NAME)

    candidate_map: Dict[str, Dict] = {}

    for query_suffix, category_tag in DISCOVERY_QUERIES:
        full_query = f"{official_domain} {query_suffix}"
        try:
            search_res = client.search(full_query)
            for item in search_res.get("results", []):
                url = item.get("url", "").strip()
                if not url:
                    continue
                d = extract_domain(url)
                if not is_allowed_domain(d, official_domain):
                    continue
                if url not in candidate_map:
                    candidate_map[url] = {
                        "url": url,
                        "category_tag": category_tag,
                        "query": full_query,
                        "domain": d,
                        "discovered": True
                    }
        except Exception as e:
            logger.warning(f"Search failed for '{full_query}': {e}")

    # Fetch candidates in batches of up to 10
    candidate_urls = list(candidate_map.keys())
    valid_sources: List[Dict] = []

    for i in range(0, len(candidate_urls), 10):
        batch = candidate_urls[i:i+10]
        try:
            fetch_res = client.fetch(batch)
            for res_item in fetch_res.get("results", []):
                url = res_item.get("url") or res_item.get("final_url")
                text = res_item.get("text", "") or ""
                # Drop pages with very little text (< 100 chars)
                if len(text.strip()) < 100:
                    continue
                if url in candidate_map:
                    src_entry = dict(candidate_map[url])
                    src_entry["text_length"] = len(text.strip())
                    valid_sources.append(src_entry)
        except Exception as e:
            logger.warning(f"Batch fetch failed: {e}")

    # Keep at most 20 pages total
    valid_sources = valid_sources[:20]

    # Preserve any existing verified starter sources from sources.json
    existing_sources = []
    if SOURCES_FILE.exists():
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                existing_sources = json.load(f)
        except Exception:
            pass

    # Merge verified and newly discovered (avoid duplicates by url)
    final_sources = list(existing_sources)
    existing_urls = {s.get("url") for s in final_sources if s.get("url")}

    for s in valid_sources:
        if s["url"] not in existing_urls and len(final_sources) < 20:
            final_sources.append(s)
            existing_urls.add(s["url"])

    final_sources = final_sources[:20]

    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(final_sources, f, indent=2, ensure_ascii=False)

    print("\nDiscovered Sources Table:")
    print(f"{'Domain':<25} | {'Category':<15} | {'Length':<8} | URL")
    print("-" * 80)
    for s in final_sources:
        d = s.get("domain", extract_domain(s.get("url", "")))
        cat = s.get("category_tag", "general")
        length = s.get("text_length", 0)
        url = s.get("url", "")
        print(f"{d:<25} | {cat:<15} | {length:<8} | {url[:45]}")

    return final_sources

if __name__ == "__main__":
    try:
        run_discovery()
    except Exception as err:
        print(f"Discovery error: {err}", file=sys.stderr)
        sys.exit(1)
