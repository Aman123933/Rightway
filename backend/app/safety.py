import json
import re
import unicodedata
from typing import Dict, List, Any
from .config import TERMS_FILE

_CACHED_TERMS = None

def _load_terms() -> Dict[str, Any]:
    global _CACHED_TERMS
    if _CACHED_TERMS is not None:
        return _CACHED_TERMS
    try:
        with open(TERMS_FILE, "r", encoding="utf-8") as f:
            _CACHED_TERMS = json.load(f)
    except Exception:
        # Fallback terms in case file is missing
        _CACHED_TERMS = {
            "urgent_terms": {
                "ragging": ["ragging", "ragged", "ragger", "raggers", "rag", "रैगिंग"],
                "harassment": ["sexual harassment", "harassment", "harassed", "eve teasing", "molestation", "stalking", "छेड़छाड़", "उत्पीड़न"],
                "violence_threat": ["violence", "physical assault", "assault", "beaten up", "kill threat", "maar peet", "मारपीट", "धमकी"],
                "self_harm": ["suicide", "suicidal", "kill myself", "end my life", "self harm", "khudkushi", "आत्महत्या", "खुदकुशी"]
            },
            "keyword_map": {}
        }
    return _CACHED_TERMS

def normalize_text(text: str) -> str:
    """
    Normalise text: lowercase, strip accents, replace punctuation with spaces,
    and collapse extra whitespace.
    """
    if not text:
        return ""
    # Unicode NFKD normalisation to strip accents
    text = unicodedata.normalize("NFKD", text)
    # Remove combining marks
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    # Replace punctuation and symbols with space (preserve word chars \w)
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def check_safety(message: str) -> Dict[str, Any]:
    """
    Check if a student message triggers urgent safety flags.
    Matches whole words or phrases only.
    'bragging' or 'dragging' must NOT trigger 'ragging'.
    Returns:
        {"triggered": bool, "categories": List[str]}
    """
    if not message or not message.strip():
        return {"triggered": False, "categories": []}

    norm_msg = normalize_text(message)
    if not norm_msg:
        return {"triggered": False, "categories": []}

    terms_data = _load_terms()
    urgent_terms = terms_data.get("urgent_terms", {})

    triggered_categories = []

    for category, term_list in urgent_terms.items():
        for term in term_list:
            norm_term = normalize_text(term)
            if not norm_term:
                continue
            # Whole word / phrase boundary match
            pattern = rf"(?<!\w){re.escape(norm_term)}(?!\w)"
            if re.search(pattern, norm_msg):
                if category not in triggered_categories:
                    triggered_categories.append(category)
                break  # Category already triggered, move to next category

    return {
        "triggered": len(triggered_categories) > 0,
        "categories": triggered_categories
    }
