import json
import logging
from typing import Optional, List
from .config import GEMINI_API_KEY, GEMINI_MODEL
from .safety import normalize_text, _load_terms

logger = logging.getLogger("router")

ALLOWED_CATEGORIES = [
    "ragging",
    "harassment",
    "fee_refund",
    "scholarship",
    "exam_evaluation",
    "attendance",
    "hostel",
    "discrimination",
    "admission",
    "other"
]

def route_category_keyword(message: str) -> Optional[str]:
    norm = normalize_text(message)
    if not norm:
        return None

    terms_data = _load_terms()
    keyword_map = terms_data.get("keyword_map", {})

    scores = {cat: 0 for cat in ALLOWED_CATEGORIES}

    for cat, kws in keyword_map.items():
        for kw in kws:
            norm_kw = normalize_text(kw)
            if norm_kw and norm_kw in norm:
                scores[cat] += len(norm_kw.split())

    best_cat = max(scores, key=scores.get)
    if scores[best_cat] > 0:
        return best_cat
    return None

def route_category_gemini(message: str, model_client: Optional[any] = None) -> str:
    """
    Asks Gemini to categorize under 200 input tokens into one of the allowed categories.
    Falls back to 'other' on error.
    """
    if not GEMINI_API_KEY and model_client is None:
        return "other"

    try:
        if model_client is not None:
            # Used for testing / mock injection
            resp_text = model_client.generate(message)
        else:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                f"Classify this student problem into exactly one category: {ALLOWED_CATEGORIES}.\n"
                f"Message: {message[:200]}\n"
                f"Respond with JSON: {{\"category\": \"chosen_category\"}}"
            )
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            resp_text = response.text or ""

        # Parse JSON or match category
        for cat in ALLOWED_CATEGORIES:
            if cat in resp_text.lower():
                return cat
    except Exception as e:
        logger.warning(f"Gemini category routing failed: {e}")

    return "other"

def determine_category(
    user_category: Optional[str],
    message: str,
    gemini_client: Optional[any] = None
) -> str:
    if user_category and user_category in ALLOWED_CATEGORIES:
        return user_category

    kw_cat = route_category_keyword(message)
    if kw_cat:
        return kw_cat

    if GEMINI_API_KEY or gemini_client is not None:
        return route_category_gemini(message, model_client=gemini_client)

    return "other"
