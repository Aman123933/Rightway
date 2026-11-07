# RightWay Backend

RightWay is an official student rights and grievance navigator built for Tiny Hacks 2026. A student describes a campus problem, and RightWay returns the applicable regulatory rule, the office to approach, actionable steps, official time limits, and required documents—each backed by official source links and verified "last checked" dates.

Urgent safety triggers (ragging, harassment, violence, self-harm) completely bypass AI and immediately surface emergency helplines and national contacts (including India's 112).

---

## How TinyFish is Used

RightWay uses TinyFish web automation and extraction infrastructure to keep student rights grounded in live, factual institutional pages:
- **TinyFish Search (`api.search.tinyfish.ai`)**: Discovers official college and regulator domains and locates relevant grievance cells, anti-ragging committees, and refund policies.
- **TinyFish Fetch (`api.fetch.tinyfish.ai`)**: Pulls clean markdown/text content from verified institution and regulator URLs, and performs live rechecks (`ttl: 0`) to detect policy alterations.
- **TinyFish Agent (`agent.tinyfish.ai/v1/automation/run-sse`)**: Orchestrates browser automation on priority grievance and anti-ragging regulation pages to extract structured records via Server-Sent Events (SSE).

---

## Environment Variables

Configure these in `backend/.env` (see `backend/.env.example`):

| Variable | Description | Default |
|---|---|---|
| `TINYFISH_API_KEY` | API Key for TinyFish Search, Fetch, and Agent | *(Required for live web runs)* |
| `GEMINI_API_KEY` | Google Gemini API Key | *(Required for draft generation & router fallback)* |
| `GEMINI_MODEL` | Gemini Model ID | `gemini-2.5-flash` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | `*` |
| `ADMIN_TOKEN` | Token for administrative recheck endpoint | `change-this-secret-admin-token` |
| `UNIVERSITY_NAME` | Default institution name for source discovery | `Vishveshwarya Group of Institutions, Greater Noida` |

---

## Running Locally

1. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```
2. **Start the FastAPI server:**
   ```bash
   cd backend
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Or from root:
   ```bash
   export PYTHONPATH=backend
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

---

## API Endpoints & Curl Examples

### 1. Health Check
```bash
curl -X GET http://127.0.0.1:8000/api/health
```

### 2. Emergency Contacts
```bash
curl -X GET http://127.0.0.1:8000/api/emergency
```

### 3. Ask / Route Question (Normal)
```bash
curl -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I claim a refund for fee after cancelling my admission?", "category": "fee_refund"}'
```

### 4. Ask / Route Question (Urgent Safety Trigger)
```bash
curl -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Help, seniors are ragging me in hostel room 204!"}'
```

### 5. Generate Complaint Draft
```bash
curl -X POST http://127.0.0.1:8000/api/draft \
  -H "Content-Type: application/json" \
  -d '{
    "category": "fee_refund",
    "details": "Withdrew admission on 10th August. Institution has not processed caution deposit refund.",
    "record_ids": ["ugc-fee-refund-rule-2023"]
  }'
```

### 6. Get Library Index
```bash
curl -X GET http://127.0.0.1:8000/api/library
```

### 7. Admin Recheck
```bash
curl -X POST http://127.0.0.1:8000/api/recheck \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: change-this-secret-admin-token" \
  -d '{"record_id": "ugc-fee-refund-rule-2023", "simulate_change": true}'
```

---

## Running Tests

Run test suite with mocked network:
```bash
pytest -q
```
Run live smoke test against local server:
```bash
python backend/scripts/smoke.py http://127.0.0.1:8000
```

---

## Deployment & Hosting Notes

- **Render Web Service (`render.yaml`)**:
  Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Ephemeral Storage**: Render free-tier disk is ephemeral; any runtime `library.json` hash updates or rechecks reset to seed files upon restart.
- **Cold Starts**: Setup a free uptime pinger targeting `GET /api/health` every 10–14 minutes to prevent free instances from spinning down.

---

## Limits & Rate Limiting

- **API Rate Limiter**: 30 requests per minute per IP address on FastAPI endpoints.
- **Gemini Client Limiter**: 8 requests per minute and 400 requests per day client-side throttle with memory cache to respect free tier limits.
- **Input Length**:
  - `POST /api/ask`: Maximum 1,000 characters.
  - `POST /api/draft`: Maximum 1,500 characters.

---

## AI Disclosure

- **Zero-AI Safety Gate**: Queries containing urgent terms (ragging, violence, self-harm, harassment) never touch an LLM. Emergency contacts and static crisis resources are returned immediately.
- **Deterministic Answers**: Rule answers, time limits, and contacts are assembled deterministically from verified institutional library records. The LLM is never permitted to invent phone numbers, emails, offices, or rules.
- **AI-Assisted Drafting**: Gemini (`google-genai`) is used strictly to structure formal complaint drafts from cited regulations. Student input is treated as untrusted data within strict prompt delimiters.
