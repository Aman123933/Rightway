# RightWay — Student Rights & Grievance Navigator

**Hackathon:** Tiny Hacks 2026  
**Team:** Chill.exe (Anushika, Aman Saini)

RightWay is an official student rights and grievance navigator. A student describes a campus problem and receives: the exact regulatory rule that applies, the responsible office/committee to approach, step-by-step procedures, official time limits, and required documents—each backed by an official source link and a "last checked" date. Urgent safety triggers (ragging, harassment, assault, self-harm) bypass AI completely and surface emergency helplines immediately.

---

## Architecture (8 lines)
1. **Frontend (Vite + React 18 + Tailwind CSS)**: Minimal, accessible SPA with live character counters, responsive tables/cards, and a global emergency panel.
2. **Global Emergency Gate**: Pinned emergency modal and high-contrast alert layer serving official 112 notes and 24x7 crisis helplines.
3. **FastAPI Gateway**: Rate-limited HTTP interface handling `/api/health`, `/api/emergency`, `/api/ask`, `/api/draft`, `/api/library`, and `/api/recheck`.
4. **Deterministic Safety Filter**: Zero-AI regex boundary scanner routing urgent queries to crisis contacts with no LLM involvement.
5. **Deterministic Retrieval & Grounding**: Keyword-weighted token ranker mapping queries to verified institutional and national regulation records.
6. **Gemini 2.5 Flash Lite**: Scoped strictly to formal grievance complaint drafting with prompt-injection delimiters; never invents rules or dates.
7. **TinyFish Web Infrastructure**: Search finds institution domains; Fetch parses and rechecks pages (`ttl: 0`); Agent extracts structured regulation procedures via SSE.
8. **Ephemeral Storage & Recheck Cache**: In-memory and file-backed content hash monitor with admin-authenticated live and simulated rechecks.

---

## How TinyFish is Used

RightWay uses TinyFish web automation and extraction infrastructure to keep student rights grounded in live, factual institutional pages:
- **TinyFish Search (`api.search.tinyfish.ai`)**: Discovers official college and regulator domains and locates relevant grievance cells, anti-ragging committees, and refund policies.
- **TinyFish Fetch (`api.fetch.tinyfish.ai`)**: Pulls clean markdown/text content from verified institution and regulator URLs, and performs live rechecks (`ttl: 0`) to detect policy alterations.
- **TinyFish Agent (`agent.tinyfish.ai/v1/automation/run-sse`)**: Orchestrates browser automation on priority grievance and anti-ragging regulation pages to extract structured records via Server-Sent Events (SSE).

---

## Environment Variables

### Backend (`backend/.env`):
| Variable | Description | Default |
|---|---|---|
| `TINYFISH_API_KEY` | API Key for TinyFish Search, Fetch, and Agent | *(Required for live web runs)* |
| `GEMINI_API_KEY` | Google Gemini API Key | *(Required for draft generation & router fallback)* |
| `GEMINI_MODEL` | Gemini Model ID | `gemini-3.5-flash-lite` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | `*` |
| `ADMIN_TOKEN` | Token for administrative recheck endpoint | `change-this-secret-admin-token` |
| `UNIVERSITY_NAME` | Institution name for source discovery | `Vishveshwarya Group of Institutions, Greater Noida` |

### Frontend (`frontend/.env`):
| Variable | Description | Default |
|---|---|---|
| `VITE_API_URL` | Base URL of the FastAPI backend | `http://127.0.0.1:8000` |

---

## How to Run

### 1. Backend Setup:
```bash
# Install dependencies
pip install -r backend/requirements.txt

# (Optional) Discover sources and compile official library
python backend/scripts/discover_sources.py
python backend/scripts/build_library.py

# Start FastAPI server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup:
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## Testing

- **Frontend Tests (Vitest + React Testing Library)**:
  ```bash
  cd frontend
  npm test
  ```
  Runs 23 unit tests verifying app shell, emergency panel, home live counter, answer cards, draft generation, and sources rechecking.

- **Frontend Production Build**:
  ```bash
  cd frontend
  npm run build
  ```

- **Backend Tests (Pytest)**:
  ```bash
  pytest -q
  ```

- **Live Backend Smoke Test**:
  ```bash
  python backend/scripts/smoke.py http://127.0.0.1:8000
  ```

---

## Deployment

- **Frontend (Vercel Hobby — Free)**:
  1. Deploy `/frontend` to Vercel.
  2. Set `VITE_API_URL` environment variable to your deployed backend URL.
  3. `vercel.json` is preconfigured with SPA rewrites to `/index.html`.
- **Backend (Render — Free Web Service)**:
  1. Configured via `backend/render.yaml`.
  2. Build command: `pip install -r backend/requirements.txt`.
  3. Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`.
  4. Set `ALLOWED_ORIGINS` to your frontend's Vercel URL.

---

## Known Limits

1. **Public Official Pages Only**: RightWay indexes only public, officially published documents and portal pages.
2. **PDF Readability**: Complex scanned PDF circulars may parse with lower text fidelity than HTML gazettes.
3. **Keyword Safety Gate Limits**: The zero-AI safety gate checks explicit words and phrases; indirect wording can be missed, which is why the "Need help now?" button is permanently pinned on every page.
4. **Free Tier Cold Starts**: Free server instances sleep after inactivity and may take 45–60 seconds to wake up.
5. **National Regulator Fallback**: If an institution's website lacks grievance, fee refund, or anti-ragging pages, the library contains national regulator regulations (UGC/AICTE) only.
6. **Human Verification**: Automatically discovered pages should be human-reviewed before official institutional deployments.
7. **Ephemeral Server Rechecks**: Free tier disk storage is ephemeral; recheck statuses reset when the server restarts.

---

## AI Disclosure

- **Zero-AI Safety Gate**: Queries containing urgent terms (ragging, violence, self-harm, harassment) never touch an LLM. Emergency contacts and static crisis resources are returned immediately.
- **Deterministic Answers**: Rule answers, time limits, and contacts are assembled deterministically from verified institutional library records. The LLM is never permitted to invent phone numbers, emails, offices, or rules.
- **AI-Assisted Drafting**: Gemini (`google-genai`) is used strictly to structure formal complaint drafts from cited regulations. Student input is treated as untrusted data within strict prompt delimiters.

---

## Team
**Chill.exe** — Anushika, Aman Saini
