import re
from typing import Dict, List, Any, Optional
from .models import AnswerPayload, Contact

def extract_all_text_from_records(records: List[Dict[str, Any]]) -> str:
    parts = []
    for r in records:
        parts.append(r.get("source_quote", ""))
        parts.append(r.get("portal_url") or "")
        parts.append(r.get("source_url") or "")
        for c in r.get("contacts", []):
            if isinstance(c, dict):
                parts.append(c.get("phone") or "")
                parts.append(c.get("email") or "")
                parts.append(c.get("url") or "")
            elif hasattr(c, "phone"):
                parts.append(c.phone or "")
                parts.append(c.email or "")
                parts.append(c.url or "")
    return " ".join(parts)

def verify_answer(answer: AnswerPayload, cited_records: List[Dict[str, Any]]) -> AnswerPayload:
    """
    Every phone, email and URL in the response must appear in the cited records,
    otherwise remove it.
    """
    grounded_corpus = extract_all_text_from_records(cited_records)

    # Verify portal_url
    if answer.portal_url and answer.portal_url not in grounded_corpus:
        answer.portal_url = None

    # Verify office contact
    if answer.office:
        contact_dict = answer.office.model_dump() if hasattr(answer.office, "model_dump") else dict(answer.office)
        if contact_dict.get("phone") and contact_dict["phone"] not in grounded_corpus:
            contact_dict["phone"] = None
        if contact_dict.get("email") and contact_dict["email"] not in grounded_corpus:
            contact_dict["email"] = None
        if contact_dict.get("url") and contact_dict["url"] not in grounded_corpus:
            contact_dict["url"] = None

        answer.office = Contact(**contact_dict)

    return answer
