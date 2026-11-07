import collections
import logging
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import (
    ALLOWED_ORIGINS,
    ADMIN_TOKEN,
    GEMINI_API_KEY,
    TINYFISH_API_KEY,
    UNIVERSITY_NAME
)
from .models import (
    HealthResponse,
    EmergencyResponse,
    AskRequest,
    AskResponse,
    DraftRequest,
    DraftResponse,
    LibraryItemSummary,
    RecheckRequest,
    RecheckResponse,
    Contact
)
from .library import load_library, perform_recheck
from .answer import process_ask_request
from .draft import generate_complaint_draft

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("rightway")

app = FastAPI(title="RightWay Backend", version="1.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory IP rate limiter: 30 requests per minute per IP
IP_REQUESTS: Dict[str, collections.deque] = collections.defaultdict(collections.deque)
RATE_LIMIT_PER_MINUTE = 30

@app.middleware("http")
async def rate_limit_and_log_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Skip rate limiting for test mocks if needed or enforce consistently
    timestamps = IP_REQUESTS[client_ip]
    while timestamps and now - timestamps[0] > 60:
        timestamps.popleft()

    if len(timestamps) >= RATE_LIMIT_PER_MINUTE:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Maximum 30 requests per minute."}
        )

    timestamps.append(now)

    response = await call_next(request)

    # Privacy logging: log only method, path, status_code (DO NOT log body or user messages)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} (client: {client_ip})")
    return response

@app.get("/", include_in_schema=False)
def root():
    return {
        "name": "RightWay API",
        "status": "online",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred."}
    )

@app.get("/api/health", response_model=HealthResponse)
def get_health():
    records = load_library()
    dates = [r.get("fetched_at") for r in records if r.get("fetched_at")]
    last_checked = max(dates) if dates else None

    # Strict secret protection: Never expose actual keys or tokens
    return HealthResponse(
        ok=True,
        library_count=len(records),
        last_checked=last_checked,
        gemini_configured=bool(GEMINI_API_KEY),
        tinyfish_configured=bool(TINYFISH_API_KEY)
    )

@app.get("/api/emergency", response_model=EmergencyResponse)
def get_emergency():
    records = load_library()
    contacts: List[Contact] = []
    for r in records:
        if r.get("type") in ["emergency", "crisis"]:
            for c in r.get("contacts", []):
                contacts.append(Contact(**dict(c)))

    return EmergencyResponse(
        contacts=contacts,
        note="If you are in immediate danger, call 112 (India's emergency number)."
    )

@app.post("/api/ask", response_model=AskResponse)
def post_ask(payload: AskRequest):
    return process_ask_request(payload)

@app.post("/api/draft", response_model=DraftResponse)
def post_draft(payload: DraftRequest):
    return generate_complaint_draft(payload)

@app.get("/api/library", response_model=List[LibraryItemSummary])
def get_library():
    records = load_library()
    summaries = []
    for r in records:
        summaries.append(LibraryItemSummary(
            id=r["id"],
            title=r["title"],
            type=r["type"],
            category=r["category"],
            source_url=r["source_url"],
            fetched_at=r["fetched_at"],
            status=r.get("status", "current")
        ))
    return summaries

@app.post("/api/recheck", response_model=RecheckResponse)
def post_recheck(
    payload: RecheckRequest,
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")
):
    if not x_admin_token or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing X-Admin-Token"
        )

    results = perform_recheck(
        record_id=payload.record_id,
        all_records=payload.all,
        simulate_change=payload.simulate_change
    )
    return RecheckResponse(results=results)
