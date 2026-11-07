from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Common Contact model
class Contact(BaseModel):
    label: str
    phone: Optional[str] = None
    email: Optional[str] = None
    hours: Optional[str] = None
    url: Optional[str] = None
    source_id: str

# Record Model
RecordType = Literal["rule", "office", "portal", "emergency", "crisis", "procedure"]
RecordStatus = Literal["current", "needs_recheck", "changed"]

class LibraryRecord(BaseModel):
    id: str
    type: RecordType
    category: List[str]
    title: str
    summary: str
    steps: List[str] = Field(default_factory=list)
    time_limits: List[str] = Field(default_factory=list)
    documents: List[str] = Field(default_factory=list)
    contacts: List[Contact] = Field(default_factory=list)
    portal_url: Optional[str] = None
    source_url: str
    source_quote: str
    fetched_at: str
    content_hash: str
    status: RecordStatus = "current"

# Health
class HealthResponse(BaseModel):
    ok: bool
    library_count: int
    last_checked: Optional[str] = None
    gemini_configured: bool
    tinyfish_configured: bool

# Emergency
class EmergencyResponse(BaseModel):
    contacts: List[Contact]
    note: str = "If you are in immediate danger, call 112 (India's emergency number)."

# Safety Info
class SafetyInfo(BaseModel):
    triggered: bool
    categories: List[str] = Field(default_factory=list)
    message: str = ""
    contacts: List[Contact] = Field(default_factory=list)

# Answer payload
class AnswerPayload(BaseModel):
    summary: str
    office: Optional[Contact] = None
    steps: List[str] = Field(default_factory=list)
    time_limits: List[str] = Field(default_factory=list)
    documents: List[str] = Field(default_factory=list)
    portal_url: Optional[str] = None

# Source reference in response
class SourceRef(BaseModel):
    id: str
    title: str
    url: str
    quote: str
    fetched_at: str
    status: str

# Ask Request & Response
class AskRequest(BaseModel):
    message: str = Field(..., max_length=1000)
    category: Optional[str] = None

class AskResponse(BaseModel):
    safety: SafetyInfo
    category: Optional[str] = None
    not_found: bool = False
    answer: AnswerPayload
    sources: List[SourceRef] = Field(default_factory=list)
    fallback: Optional[str] = None

# Draft Request & Response
class DraftRequest(BaseModel):
    category: str
    details: str = Field(..., max_length=1500)
    record_ids: List[str] = Field(default_factory=list)

class DraftResponse(BaseModel):
    draft: str
    ai_used: bool
    label: str

# Library Item Summary
class LibraryItemSummary(BaseModel):
    id: str
    title: str
    type: RecordType
    category: List[str]
    source_url: str
    fetched_at: str
    status: RecordStatus

# Recheck Request & Response
class RecheckRequest(BaseModel):
    record_id: Optional[str] = None
    all: Optional[bool] = None
    simulate_change: Optional[bool] = None

class RecheckResultItem(BaseModel):
    id: str
    status: RecordStatus
    changed: bool
    simulated: bool
    error: Optional[str] = None

class RecheckResponse(BaseModel):
    results: List[RecheckResultItem]
