# AI, Libraries & Tools Disclosure

This document discloses all libraries, foundational models, cloud infrastructure, and AI development tools utilized in **RightWay** for Tiny Hacks 2026.

---

## 1. Libraries & Frameworks

### Backend (Python 3.11+)
- **FastAPI** (`fastapi`): High-performance asynchronous web framework providing REST endpoints, automatic OpenAPI documentation, and exception handling.
- **Pydantic v2** (`pydantic`): Strict data schema validation, model serialization, and string boundary enforcement (e.g. 1000 char message cap, 1500 char details cap).
- **Uvicorn** (`uvicorn`): Production ASGI web server running the FastAPI application.
- **HTTPX** (`httpx`): Asynchronous and synchronous HTTP client used for calling TinyFish Search and Fetch APIs with retry logic.
- **Google GenAI SDK** (`google-genai`): Official Google GenAI SDK interfacing with Gemini models.
- **Python-Dotenv** (`python-dotenv`): Secure loading of local `.env` environment variables without committing secrets.
- **Pytest** (`pytest`): Automated test runner executing unit, integration, and security scans (92 testcases).
- **Starlette** (`starlette`): ASGI toolkit powering FastAPI's middleware, TestClient, static file serving, and SPA fallback routing.

### Frontend (React 18 + Vite)
- **React 18** (`react`, `react-dom`): Component-based user interface framework.
- **Vite** (`vite`): Fast development server and production bundler for modern JavaScript / JSX.
- **React Router DOM** (`react-router-dom`): Client-side SPA routing (`/`, `/answer`, `/draft`, `/sources`, `/about`).
- **Tailwind CSS** (`tailwindcss`, `postcss`, `autoprefixer`): Utility-first CSS styling for responsive, accessible, high-contrast layouts.
- **Lucide React** (`lucide-react`): Consistent, thin-stroke icon library for accessible button labels and indicators.
- **Vitest & React Testing Library** (`vitest`, `@testing-library/react`): Modern unit testing environment for React components.

---

## 2. Foundation Models & AI Services

- **Google Gemini 3.5 Flash-Lite** (`gemini-3.5-flash-lite` via `google-genai`):
  - **Purpose**: Strictly scoped to formatting formal complaint letters based solely on retrieved regulation excerpts and student factual inputs.
  - **Zero-AI Safety Gate**: Urgent keywords (ragging, sexual harassment, violence, suicidal ideation) completely bypass Gemini and route directly to static emergency contacts.
  - **Prompt-Injection Defenses**: Student text is isolated inside `<STUDENT_DETAILS>` XML delimiters with explicit model instructions to ignore embedded commands.
  - **Client-Side Throttling**: Enforces a strict limit of 8 requests per minute and 400 per day with in-memory hashing cache to protect free tier quotas.
  - **Deterministic Fallback**: If `GEMINI_API_KEY` is missing, rate-limited (HTTP 429), or fails, a deterministic standard letter template is returned with `ai_used: false`.

---

## 3. Web Automation & Cloud Infrastructure

- **TinyFish Web Agent Infrastructure**:
  - `api.search.tinyfish.ai`: Queries live web results to discover official university domains and regulation circulars.
  - `api.fetch.tinyfish.ai`: Headless browser-backed content extraction (`ttl: 0` for live rechecks) to retrieve clean text and verify content hash updates.
  - `agent.tinyfish.ai/v1/automation/run-sse`: Server-Sent Events browser automation agent for extracting structured rules from multi-step dynamic university portals.
- **Render**: Containerized deployment hosting the FastAPI backend and built frontend SPA via multi-stage `Dockerfile` and `render.yaml`.
- **Vercel**: Optional frontend hosting with preconfigured SPA routing via `frontend/vercel.json`.
- **Hugging Face Spaces**: Fallback Docker hosting option using the root `Dockerfile`.

---

## 4. AI Coding Tools Used During Development

- **Google Antigravity AI Assistant** (powered by Gemini): Used for architectural planning, pair programming, test suite authoring, refactoring, and automated debugging throughout the Tiny Hacks 2026 hackathon.
