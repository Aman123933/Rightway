import json
import pytest
from unittest.mock import patch, MagicMock
import httpx
from app.tinyfish import TinyFishClient, validate_record_against_text
from scripts.build_library import build_library
from app.config import LIBRARY_FILE

class TestTinyFishClient:
    def test_auth_header_sent(self):
        client = TinyFishClient(api_key="test-tf-key")
        with patch("httpx.Client.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"results": []}
            mock_get.return_value = mock_resp

            client.search("test query", use_cache=False)
            mock_get.assert_called_once()
            headers = mock_get.call_args[1]["headers"]
            assert headers["X-API-Key"] == "test-tf-key"

    def test_sse_complete_parsing(self):
        sse_lines = [
            "event: message\n",
            'data: {"type": "STARTED", "run_id": "r1"}\n',
            "\n",
            "event: message\n",
            'data: {"type": "PROGRESS", "message": "loading"}\n',
            "\n",
            "event: message\n",
            'data: {"type": "COMPLETE", "run_id": "r1", "status": "COMPLETED", "result": {"id": "rec1", "title": "Test Rec"}}\n'
        ]
        result = TinyFishClient._parse_sse_stream(sse_lines)
        assert result is not None
        assert result["id"] == "rec1"
        assert result["title"] == "Test Rec"

    def test_timeout_then_retry(self):
        client = TinyFishClient(api_key="test-key")
        with patch("httpx.Client.get") as mock_get:
            # First attempt raises TimeoutException, second succeeds
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"results": [{"url": "https://test.edu"}]}
            mock_get.side_effect = [httpx.ReadTimeout("Timeout error"), mock_resp]

            res = client.search("test query retry", use_cache=False)
            assert len(res["results"]) == 1
            assert mock_get.call_count == 2

    def test_invented_phone_and_email_dropped(self):
        record = {
            "id": "rec-1",
            "source_quote": "Official grievance desk is available for students.",
            "portal_url": "https://fake-portal.com",
            "contacts": [
                {
                    "label": "Grievance Officer",
                    "phone": "99999-99999",  # Invented
                    "email": "invented@fake.com",  # Invented
                    "url": "https://real-site.edu",
                    "source_id": "rec-1"
                }
            ]
        }
        source_text = "Official grievance desk is available for students. Visit https://real-site.edu for info."
        validated = validate_record_against_text(record, source_text)
        assert validated is not None
        contact = validated["contacts"][0]
        # Invented phone and email must be set to None
        assert contact["phone"] is None
        assert contact["email"] is None
        assert contact["url"] == "https://real-site.edu"
        # Invented portal_url not in text must be set to None
        assert validated["portal_url"] is None

    def test_non_substring_quote_drops_record(self):
        record = {
            "id": "rec-2",
            "source_quote": "This quote does not exist in the source document anywhere.",
            "contacts": []
        }
        source_text = "UGC Anti-Ragging guidelines strictly prohibit all forms of hazing."
        validated = validate_record_against_text(record, source_text)
        assert validated is None

    def test_failure_leaves_library_unchanged(self, tmp_path):
        test_lib_file = tmp_path / "library.json"
        initial_data = [{"id": "initial-rec", "title": "Initial"}]
        with open(test_lib_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        mock_client = MagicMock()
        mock_client.run_agent_sse.side_effect = RuntimeError("Network down")
        mock_client.fetch.side_effect = RuntimeError("Network down")

        with patch("scripts.build_library.LIBRARY_FILE", test_lib_file):
            with patch("scripts.build_library.TINYFISH_API_KEY", "test-key"):
                res = build_library(client=mock_client)
                assert res == initial_data
                # File content unchanged
                with open(test_lib_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                assert saved == initial_data
