import pytest
from unittest.mock import MagicMock
from app.models import AskRequest, AnswerPayload, Contact
from app.answer import process_ask_request
from app.verify import verify_answer
from app.router import determine_category

class TestAskRouteAnswer:
    @pytest.fixture
    def test_library(self):
        return [
            {
                "id": "ugc-fee-refund",
                "type": "rule",
                "category": ["fee_refund"],
                "title": "UGC Fee Refund Guidelines",
                "summary": "Full fee refund must be provided if student withdraws before deadline.",
                "steps": ["Submit withdrawal application", "Collect refund check"],
                "time_limits": ["15 days"],
                "documents": ["Fee receipt", "Application letter"],
                "contacts": [
                    {
                        "label": "Admissions Office",
                        "phone": "011-23232701",
                        "email": "refund@ugc.ac.in",
                        "hours": "9am-5pm",
                        "url": "https://ugc.gov.in",
                        "source_id": "ugc-fee-refund"
                    }
                ],
                "portal_url": "https://ugc.gov.in/refund-portal",
                "source_url": "https://ugc.gov.in/fee-regulations",
                "source_quote": "Full fee refund must be provided if student withdraws before deadline. Contact 011-23232701.",
                "fetched_at": "2026-11-07T10:00:00Z",
                "content_hash": "hash1",
                "status": "current"
            },
            {
                "id": "emergency-ragging",
                "type": "emergency",
                "category": ["ragging"],
                "title": "Anti-Ragging Helpline",
                "summary": "Immediate anti-ragging response.",
                "steps": ["Call helpline"],
                "time_limits": ["Immediate"],
                "documents": [],
                "contacts": [
                    {
                        "label": "Anti-Ragging Desk",
                        "phone": "1800-180-5522",
                        "email": "help@antiragging.in",
                        "hours": "24x7",
                        "url": "https://antiragging.in",
                        "source_id": "emergency-ragging"
                    }
                ],
                "portal_url": "https://antiragging.in",
                "source_url": "https://antiragging.in",
                "source_quote": "Anti-ragging helpline 1800-180-5522 available 24x7.",
                "fetched_at": "2026-11-07T10:00:00Z",
                "content_hash": "hash2",
                "status": "current"
            }
        ]

    def test_category_routing(self):
        # 1. User specified category takes precedence
        cat1 = determine_category("scholarship", "Can I get my fee refund?")
        assert cat1 == "scholarship"

        # 2. Keyword routing works
        cat2 = determine_category(None, "I need a fee refund after cancellation")
        assert cat2 == "fee_refund"

        cat3 = determine_category(None, "When is the re-evaluation of marksheet exam?")
        assert cat3 == "exam_evaluation"

    def test_gemini_fallback_used_only_when_unclear(self):
        # When clear from keywords, gemini mock should NOT be called
        mock_gemini = MagicMock()
        cat = determine_category(None, "I want my fee refund back", gemini_client=mock_gemini)
        assert cat == "fee_refund"
        mock_gemini.generate.assert_not_called()

        # When unclear, gemini client is called
        mock_gemini.generate.return_value = '{"category": "hostel"}'
        cat_unclear = determine_category(None, "My room window is completely broken", gemini_client=mock_gemini)
        assert cat_unclear == "hostel"
        mock_gemini.generate.assert_called_once()

    def test_low_score_returns_not_found(self, test_library):
        req = AskRequest(message="Where is the quantum physics laboratory telescope?")
        resp = process_ask_request(req, library_records=test_library)
        assert resp.not_found is True
        assert resp.fallback == "Contact your institution's grievance cell."
        assert len(resp.sources) == 0

    def test_verify_strips_invented_phone(self):
        cited_records = [
            {
                "source_quote": "Official admissions cell is at gate 1. Email: contact@college.edu",
                "contacts": [],
                "portal_url": None,
                "source_url": "https://college.edu"
            }
        ]
        answer = AnswerPayload(
            summary="Test summary",
            office=Contact(
                label="Admissions",
                phone="98765-43210",  # Invented phone not in cited records
                email="contact@college.edu",  # Present in quote
                url=None,
                source_id="rec-1"
            ),
            steps=[],
            time_limits=[],
            documents=[],
            portal_url="https://invented-fake-portal.com"  # Invented portal
        )
        verified = verify_answer(answer, cited_records)
        assert verified.office.phone is None
        assert verified.office.email == "contact@college.edu"
        assert verified.portal_url is None

    def test_returned_sources_have_date_and_status(self, test_library):
        req = AskRequest(message="How to get fee refund for admission cancellation?")
        resp = process_ask_request(req, library_records=test_library)
        assert resp.not_found is False
        assert len(resp.sources) > 0
        for src in resp.sources:
            assert src.fetched_at == "2026-11-07T10:00:00Z"
            assert src.status == "current"
            assert src.url.startswith("http")
            assert len(src.quote) > 0
