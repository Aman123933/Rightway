import json
import hashlib
import pytest
from unittest.mock import MagicMock
from app.library import load_library, save_library, perform_recheck, rank_records
from app.safety import normalize_text

class TestLibraryAndRecheck:
    @pytest.fixture
    def sample_library(self, tmp_path):
        lib_file = tmp_path / "library.json"
        text = "Official UGC regulation text 2023 for student grievance."
        h = hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()
        data = [
            {
                "id": "rec-1",
                "type": "rule",
                "category": ["fee_refund"],
                "title": "UGC Fee Refund Guidelines",
                "summary": "Full refund must be made within 15 days.",
                "steps": ["Apply for refund"],
                "time_limits": ["15 days"],
                "documents": ["Receipt"],
                "contacts": [],
                "portal_url": None,
                "source_url": "https://ugc.gov.in/fee-rule",
                "source_quote": "Full refund must be made within 15 days.",
                "fetched_at": "2026-11-07T12:00:00Z",
                "content_hash": h,
                "status": "current"
            }
        ]
        with open(lib_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return lib_file, text, h

    def test_unchanged_page_stays_current(self, sample_library):
        lib_file, text, h = sample_library
        mock_client = MagicMock()
        mock_client.fetch.return_value = {
            "results": [
                {"url": "https://ugc.gov.in/fee-rule", "text": text}
            ]
        }
        results = perform_recheck(record_id="rec-1", client=mock_client, filepath=lib_file)
        assert len(results) == 1
        assert results[0]["status"] == "current"
        assert results[0]["changed"] is False
        assert results[0]["simulated"] is False
        assert results[0]["error"] is None

        # Content hash unchanged
        records = load_library(lib_file)
        assert records[0]["status"] == "current"
        assert records[0]["content_hash"] == h

    def test_changed_page_flagged_changed(self, sample_library):
        lib_file, text, old_h = sample_library
        new_text = "Updated UGC regulation text 2024: refunds now in 30 days."
        mock_client = MagicMock()
        mock_client.fetch.return_value = {
            "results": [
                {"url": "https://ugc.gov.in/fee-rule", "text": new_text}
            ]
        }
        results = perform_recheck(record_id="rec-1", client=mock_client, filepath=lib_file)
        assert len(results) == 1
        assert results[0]["status"] == "changed"
        assert results[0]["changed"] is True
        assert results[0]["simulated"] is False

        # Status updated to changed, old content hash preserved
        records = load_library(lib_file)
        assert records[0]["status"] == "changed"
        assert records[0]["content_hash"] == old_h

    def test_fetch_error_keeps_old_copy_and_sets_needs_recheck(self, sample_library):
        lib_file, text, old_h = sample_library
        mock_client = MagicMock()
        mock_client.fetch.side_effect = RuntimeError("Connection timed out to host")

        results = perform_recheck(record_id="rec-1", client=mock_client, filepath=lib_file)
        assert len(results) == 1
        assert results[0]["status"] == "needs_recheck"
        assert results[0]["changed"] is False
        assert results[0]["simulated"] is False
        assert "Connection timed out" in results[0]["error"]

        # Content preserved, status updated
        records = load_library(lib_file)
        assert records[0]["status"] == "needs_recheck"
        assert records[0]["content_hash"] == old_h

    def test_simulated_change_flagged(self, sample_library):
        lib_file, text, h = sample_library
        results = perform_recheck(record_id="rec-1", simulate_change=True, filepath=lib_file)
        assert len(results) == 1
        assert results[0]["status"] == "changed"
        assert results[0]["changed"] is True
        assert results[0]["simulated"] is True

        records = load_library(lib_file)
        assert records[0]["status"] == "changed"

    def test_ranking_search(self, sample_library):
        lib_file, _, _ = sample_library
        records = load_library(lib_file)
        ranked = rank_records("fee refund 15 days", category="fee_refund", records=records)
        assert len(ranked) > 0
        assert ranked[0][0]["id"] == "rec-1"
        assert ranked[0][1] > 0
