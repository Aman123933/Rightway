import sys
import httpx

def run_smoke(base_url: str):
    base = base_url.rstrip("/")
    print(f"--- Running RightWay Smoke Tests against: {base} ---")
    all_passed = True

    with httpx.Client(timeout=10.0) as client:
        # 1. Health check
        try:
            r = client.get(f"{base}/api/health")
            data = r.json()
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            assert data.get("ok") is True
            assert "library_count" in data
            # Check secret safety
            assert "api_key" not in str(data).lower()
            print("[PASS] GET /api/health")
        except Exception as e:
            print(f"[FAIL] GET /api/health: {e}")
            all_passed = False

        # 2. Emergency contacts
        try:
            r = client.get(f"{base}/api/emergency")
            data = r.json()
            assert r.status_code == 200
            assert "contacts" in data
            assert "112" in data.get("note", "")
            print("[PASS] GET /api/emergency")
        except Exception as e:
            print(f"[FAIL] GET /api/emergency: {e}")
            all_passed = False

        # 3. Ask (Normal query)
        try:
            payload = {"message": "How do I claim a fee refund after withdrawing admission?", "category": "fee_refund"}
            r = client.post(f"{base}/api/ask", json=payload)
            data = r.json()
            assert r.status_code == 200
            assert data["safety"]["triggered"] is False
            assert "answer" in data
            assert len(data.get("sources", [])) > 0
            print("[PASS] POST /api/ask (Normal)")
        except Exception as e:
            print(f"[FAIL] POST /api/ask (Normal): {e}")
            all_passed = False

        # 4. Ask (Urgent query)
        try:
            payload = {"message": "Seniors are ragging me in hostel room 102 please help!"}
            r = client.post(f"{base}/api/ask", json=payload)
            data = r.json()
            assert r.status_code == 200
            assert data["safety"]["triggered"] is True
            assert "ragging" in data["safety"]["categories"]
            assert len(data["safety"]["contacts"]) > 0
            assert "112" in data["safety"]["message"]
            print("[PASS] POST /api/ask (Urgent)")
        except Exception as e:
            print(f"[FAIL] POST /api/ask (Urgent): {e}")
            all_passed = False

    if all_passed:
        print("\nALL SMOKE TESTS PASSED!")
        return 0
    else:
        print("\nSMOKE TESTS FAILED!")
        return 1

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    sys.exit(run_smoke(url))
