import collections
import logging
import time
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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
from .library import load_library, perform_recheck, save_library
from .answer import process_ask_request
from .draft import generate_complaint_draft

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("rightway")

# Frontend dist resolution for single-link deploy
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if not FRONTEND_DIST.exists():
    alt_dist = Path("/app/frontend/dist")
    if alt_dist.exists():
        FRONTEND_DIST = alt_dist

# Startup database / library seed check
@asynccontextmanager
async def lifespan(app: FastAPI):
    records = load_library()
    if not records:
        logger.info("Library is empty on startup. Seeding initial verified regulations...")
        seed_records = [
            {
                "id": "ugc-sgrc-procedure-2023",
                "type": "procedure",
                "category": ["other", "fee_refund", "admission"],
                "title": "UGC Student Grievance Redressal Committee (SGRC) Procedure",
                "summary": "Students submit grievances regarding fee refunds or administration to the SGRC. The committee must conclude proceedings and send its report within 15 days.",
                "steps": [
                    "File written or online grievance to SGRC",
                    "Attend SGRC hearing if requested",
                    "Receive SGRC decision within 15 days",
                    "If dissatisfied, file appeal to Ombudsperson within 15 days"
                ],
                "time_limits": [
                    "15 days for SGRC resolution",
                    "15 days to file appeal to Ombudsperson"
                ],
                "documents": [
                    "Written complaint / grievance form",
                    "Admission receipt or proof of payment",
                    "Relevant institutional correspondence"
                ],
                "contacts": [
                    {
                        "label": "UGC Grievance Helpdesk",
                        "phone": None,
                        "email": None,
                        "hours": "10:00 AM - 5:00 PM",
                        "url": "https://ugc.gov.in",
                        "source_id": "ugc-sgrc-procedure-2023"
                    }
                ],
                "portal_url": "https://samarth.edu.in",
                "source_url": "https://thc.nic.in/Central%20Governmental%20Regulations/University%20Grant%20Commission%20%28Redressal%20of%20Grievances%20of%20Students%29%20Regulations,%202023.pdf",
                "source_quote": "The SGRC shall send its report with recommendations, if any, to the competent authority of the institution and a copy thereof to the aggrieved student, within a period of 15 days",
                "fetched_at": "2026-11-07T12:00:00Z",
                "content_hash": "a4f89d3170a4c56891ebc419ec4bfa1e6f18318e47265f6c8d37a1c72688be5d",
                "status": "current"
            },
            {
                "id": "ugc-fee-refund-rule-2023",
                "type": "rule",
                "category": ["fee_refund"],
                "title": "UGC Mandatory Fee Refund and Non-Retention of Certificates",
                "summary": "Institutions cannot retain original certificates and must process fee refunds for students withdrawing admission in accordance with UGC guidelines.",
                "steps": [
                    "Submit written withdrawal application to registrar or admissions office",
                    "Request refund voucher and receipt",
                    "If delayed beyond 15 days, lodge complaint with SGRC"
                ],
                "time_limits": [
                    "15 days for institution to process refund after withdrawal"
                ],
                "documents": [
                    "Withdrawal application",
                    "Original fee payment receipts",
                    "Bank account details for NEFT/RTGS"
                ],
                "contacts": [],
                "portal_url": None,
                "source_url": "https://thc.nic.in/Central%20Governmental%20Regulations/University%20Grant%20Commission%20%28Redressal%20of%20Grievances%20of%20Students%29%20Regulations,%202023.pdf",
                "source_quote": "delay in, or denial of, the refund of fees due to a student who withdraws admission within the time mentioned in the prospectus, or as may be notified by the Commission",
                "fetched_at": "2026-11-07T12:00:00Z",
                "content_hash": "7bc3a90623d68f2371bbbe96b7b25ea3adcf4d6bb0e9b9220fcbf1e2f758f89a",
                "status": "current"
            },
            {
                "id": "national-antiragging-helpline",
                "type": "emergency",
                "category": ["ragging"],
                "title": "National Anti-Ragging 24x7 Toll Free Helpline",
                "summary": "National 24x7 toll-free helpline and online complaint portal operated under UGC regulations for immediate anti-ragging intervention and rescue.",
                "steps": [
                    "Call toll-free helpline 1800-180-5522 immediately",
                    "Send details via email to helpline@antiragging.in",
                    "Register incident on the national anti-ragging web portal",
                    "In case of physical danger call 112"
                ],
                "time_limits": [
                    "Immediate 24x7 helpline response"
                ],
                "documents": [
                    "Incident description",
                    "Names of individuals involved if known",
                    "Location and hostel room number"
                ],
                "contacts": [
                    {
                        "label": "National Anti-Ragging Helpline",
                        "phone": "1800-180-5522",
                        "email": "helpline@antiragging.in",
                        "hours": "24x7",
                        "url": "https://www.antiragging.in",
                        "source_id": "national-antiragging-helpline"
                    }
                ],
                "portal_url": "https://www.antiragging.in",
                "source_url": "https://drrmlims.ac.in/QuickLink/UGC_Regulation",
                "source_quote": "National Anti-Ragging 24x7 Toll Free Helpline: 1800-180-5522. Email: helpline@antiragging.in. In case of emergency contact 112. UGC Anti-Ragging Regulations mandate zero tolerance.",
                "fetched_at": "2026-11-07T12:00:00Z",
                "content_hash": "557a530eb7b02c81525414d7a7b8e5c54d193630f5fa9e92fae33ecb0e8bfa51",
                "status": "current"
            },
            {
                "id": "telemanas-crisis-helpline",
                "type": "crisis",
                "category": ["self_harm", "harassment"],
                "title": "Tele-MANAS National Mental Health & Crisis Helpline",
                "summary": "Government of India 24x7 toll-free mental health support providing immediate confidential counseling for distress, anxiety, harassment, or self-harm thoughts.",
                "steps": [
                    "Call toll-free 14416 or 1800-891-4416",
                    "Speak with a trained mental health counselor in your language",
                    "Receive crisis intervention support and emergency escalation"
                ],
                "time_limits": [
                    "24x7 immediate round-the-clock availability"
                ],
                "documents": [],
                "contacts": [
                    {
                        "label": "Tele-MANAS Crisis Helpline",
                        "phone": "14416",
                        "email": None,
                        "hours": "24x7",
                        "url": "https://telemanas.mohfw.gov.in",
                        "source_id": "telemanas-crisis-helpline"
                    }
                ],
                "portal_url": "https://telemanas.mohfw.gov.in",
                "source_url": "https://telemanas.mohfw.gov.in",
                "source_quote": "Tele-MANAS provides 24x7, free, confidential mental health services across India. Call toll-free 14416 or 1800-891-4416.",
                "fetched_at": "2026-11-07T12:00:00Z",
                "content_hash": "28e23fcbe8981451f22e7cd3dbe2580cefa2d585ea1548b111e13dbd74e892c5",
                "status": "current"
            },
            {
                "id": "ugc-ombudsperson-appeal",
                "type": "procedure",
                "category": ["other", "discrimination", "exam_evaluation", "attendance"],
                "title": "Appeals to University Ombudsperson",
                "summary": "Any student aggrieved by SGRC decision may appeal to the University Ombudsperson. The Ombudsperson hears both sides and issues an order within 30 days.",
                "steps": [
                    "Obtain copy of SGRC decision",
                    "Submit appeal memo to Ombudsperson within 15 days of SGRC decision",
                    "Attend hearing convened by Ombudsperson",
                    "Ombudsperson issues final recommendations within 30 days"
                ],
                "time_limits": [
                    "15 days to file appeal after SGRC order",
                    "30 days for Ombudsperson to hear and decide appeal"
                ],
                "documents": [
                    "SGRC complaint and written decision",
                    "Grounds of appeal",
                    "Supporting evidence or medical certificates"
                ],
                "contacts": [],
                "portal_url": None,
                "source_url": "https://thc.nic.in/Central%20Governmental%20Regulations/University%20Grant%20Commission%20%28Redressal%20of%20Grievances%20of%20Students%29%20Regulations,%202023.pdf",
                "source_quote": "Any student aggrieved by the decision of the Students' Grievance Redressal Committee may prefer an appeal to the Ombudsperson, within a period of fifteen days",
                "fetched_at": "2026-11-07T12:00:00Z",
                "content_hash": "ccb810931d876357494f48b94f10738d21c97ef78ad3a0c0ad52c1cb7ee92501",
                "status": "current"
            }
        ]
        save_library(seed_records)
    yield

app = FastAPI(title="RightWay Backend", version="1.0.0", lifespan=lifespan)

if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend-assets")

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
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "name": "RightWay API",
        "status": "online",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    status_code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
    return JSONResponse(
        status_code=status_code,
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

# Catch-all SPA route for frontend client-side routing (does not interfere with /api)
@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    if full_path.startswith("api/") or full_path in ["docs", "openapi.json", "redoc"]:
        raise HTTPException(status_code=404, detail="Not Found")

    target_file = FRONTEND_DIST / full_path
    if target_file.is_file():
        return FileResponse(str(target_file))

    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    raise HTTPException(status_code=404, detail="Not Found")
