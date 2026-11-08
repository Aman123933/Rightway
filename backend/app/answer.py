import logging
from typing import Dict, List, Optional, Any
from .models import (
    AskRequest,
    AskResponse,
    SafetyInfo,
    AnswerPayload,
    SourceRef,
    Contact
)
from .safety import check_safety
from .router import determine_category
from .library import load_library, rank_records
from .verify import verify_answer

logger = logging.getLogger("answer")

SCORE_THRESHOLD = 1.0

def process_ask_request(
    req: AskRequest,
    gemini_client: Optional[Any] = None,
    library_records: Optional[List[Dict[str, Any]]] = None
) -> AskResponse:
    records = library_records if library_records is not None else load_library()
    message = req.message

    # Handle empty or whitespace-only messages early
    if not message or not message.strip():
        return AskResponse(
            safety=SafetyInfo(triggered=False, categories=[], message="", contacts=[]),
            category=req.category or "other",
            not_found=True,
            answer=AnswerPayload(
                summary="",
                office=None,
                steps=[],
                time_limits=[],
                documents=[],
                portal_url=None
            ),
            sources=[],
            fallback="Contact your institution's grievance cell."
        )

    # 1. Safety Gate Check (zero AI)
    safety_check = check_safety(message)
    if safety_check["triggered"]:
        emergency_contacts: List[Contact] = []
        emergency_sources: List[SourceRef] = []

        # Return contacts ONLY from library records of type emergency or crisis
        for r in records:
            if r.get("type") in ["emergency", "crisis"]:
                for c in r.get("contacts", []):
                    c_dict = dict(c)
                    emergency_contacts.append(Contact(**c_dict))
                emergency_sources.append(SourceRef(
                    id=r["id"],
                    title=r["title"],
                    url=r["source_url"],
                    quote=r["source_quote"],
                    fetched_at=r["fetched_at"],
                    status=r["status"]
                ))

        note_112 = "If you are in immediate danger, call 112 (India's emergency number)."
        return AskResponse(
            safety=SafetyInfo(
                triggered=True,
                categories=safety_check["categories"],
                message=f"Urgent safety alert. {note_112}",
                contacts=emergency_contacts
            ),
            category=req.category,
            not_found=False,
            answer=AnswerPayload(
                summary="Urgent assistance triggered. Please use the emergency contacts provided immediately.",
                office=emergency_contacts[0] if emergency_contacts else None,
                steps=[
                    "Call 112 immediately if in physical danger.",
                    "Reach out to the 24x7 helpline contacts listed below."
                ],
                time_limits=["Immediate 24x7 response"],
                documents=[],
                portal_url=emergency_contacts[0].url if emergency_contacts else None
            ),
            sources=emergency_sources,
            fallback=None
        )

    # 2. Determine category
    category = determine_category(req.category, message, gemini_client=gemini_client)

    # 3. Retrieve top 3 records for category and query
    ranked = rank_records(message, category=category, records=records)

    # Filter by threshold
    qualified = [(r, score) for r, score in ranked if score >= SCORE_THRESHOLD]

    if not qualified:
        return AskResponse(
            safety=SafetyInfo(triggered=False, categories=[], message="", contacts=[]),
            category=category,
            not_found=True,
            answer=AnswerPayload(
                summary="",
                office=None,
                steps=[],
                time_limits=[],
                documents=[],
                portal_url=None
            ),
            sources=[],
            fallback="Contact your institution's grievance cell."
        )

    top_results = [r for r, _ in qualified[:3]]

    # 4. Deterministic answer assembly from record fields
    top_record = top_results[0]
    summary = top_record.get("summary", "")

    # Office contact: first available contact across top results
    office_contact: Optional[Contact] = None
    for r in top_results:
        if r.get("contacts"):
            c_data = r["contacts"][0]
            office_contact = Contact(**c_data)
            break

    # Deduplicate steps, time limits, documents preserving order
    all_steps = []
    all_time_limits = []
    all_documents = []
    portal_url = None

    for r in top_results:
        for s in r.get("steps", []):
            if s not in all_steps:
                all_steps.append(s)
        for tl in r.get("time_limits", []):
            if tl not in all_time_limits:
                all_time_limits.append(tl)
        for doc in r.get("documents", []):
            if doc not in all_documents:
                all_documents.append(doc)
        if not portal_url and r.get("portal_url"):
            portal_url = r["portal_url"]

    # Build sources
    sources = [
        SourceRef(
            id=r["id"],
            title=r["title"],
            url=r["source_url"],
            quote=r["source_quote"],
            fetched_at=r["fetched_at"],
            status=r["status"]
        )
        for r in top_results
    ]

    raw_answer = AnswerPayload(
        summary=summary,
        office=office_contact,
        steps=all_steps,
        time_limits=all_time_limits,
        documents=all_documents,
        portal_url=portal_url
    )

    # 5. Verify groundedness
    verified_answer = verify_answer(raw_answer, top_results)

    return AskResponse(
        safety=SafetyInfo(triggered=False, categories=[], message="", contacts=[]),
        category=category,
        not_found=False,
        answer=verified_answer,
        sources=sources,
        fallback=None
    )
