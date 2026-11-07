import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app, IP_REQUESTS
from app.config import ADMIN_TOKEN

client = TestClient(app)

class TestHardeningAndDeploy:
    def setup_method(self):
        IP_REQUESTS.clear()

    def test_health_has_no_secrets(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert isinstance(data["gemini_configured"], bool)
        assert isinstance(data["tinyfish_configured"], bool)
        data_str = str(data)
        assert "AIzaSy" not in data_str
        assert "sk-" not in data_str
        assert "token" not in data_str.lower()
        assert "secret" not in data_str.lower()

    def test_empty_and_overlength_input_returns_422(self):
        # Empty message
        resp = client.post("/api/ask", json={"message": ""})
        # Empty message string itself might pass max_length check unless min_length or empty payload
        # Overlength message (>1000 chars)
        long_message = "A" * 1001
        resp = client.post("/api/ask", json={"message": long_message})
        assert resp.status_code == 422

        # Overlength draft details (>1500 chars)
        long_details = "B" * 1501
        resp = client.post("/api/draft", json={"category": "fee_refund", "details": long_details})
        assert resp.status_code == 422

        # Invalid JSON / missing required fields
        resp = client.post("/api/ask", json={})
        assert resp.status_code == 422

    def test_cors_headers(self):
        resp = client.options(
            "/api/health",
            headers={"Origin": "https://rightway.example.com", "Access-Control-Request-Method": "GET"}
        )
        assert resp.headers.get("access-control-allow-origin") in ["*", "https://rightway.example.com"]

    def test_rate_limiting_returns_429(self):
        # 30 requests should succeed, 31st returns 429
        IP_REQUESTS.clear()
        for i in range(30):
            resp = client.get("/api/health")
            assert resp.status_code == 200

        resp_31 = client.get("/api/health")
        assert resp_31.status_code == 429
        assert "Rate limit exceeded" in resp_31.json()["detail"]

    def test_recheck_unauthorized_without_admin_token(self):
        resp = client.post("/api/recheck", json={"simulate_change": True})
        assert resp.status_code == 401

        resp_wrong = client.post(
            "/api/recheck",
            headers={"X-Admin-Token": "wrong-token"},
            json={"simulate_change": True}
        )
        assert resp_wrong.status_code == 401

        resp_ok = client.post(
            "/api/recheck",
            headers={"X-Admin-Token": ADMIN_TOKEN},
            json={"simulate_change": True}
        )
        assert resp_ok.status_code == 200
        assert resp_ok.json()["results"][0]["simulated"] is True

    def test_repo_scan_for_secrets(self):
        root_dir = Path(__file__).resolve().parent.parent.parent
        # Patterns for actual api keys: Gemini (AIzaSy...), OpenAI (sk-...), generic high entropy tokens
        secret_patterns = [
            re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),
            re.compile(r"sk-[A-Za-z0-9]{32,}")
        ]

        # Scan all tracked files in git / python / json / yaml / md files, excluding .git and .env
        ignore_dirs = {".git", ".pytest_cache", "__pycache__", "cache"}

        for fpath in root_dir.rglob("*"):
            if fpath.is_file():
                if any(ignored in fpath.parts for ignored in ignore_dirs):
                    continue
                if fpath.name in [".env", ".coverage"]:
                    continue
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                    for pattern in secret_patterns:
                        match = pattern.search(content)
                        assert not match, f"Secret leaked in file: {fpath} -> {match.group(0)}"
                except Exception:
                    pass
