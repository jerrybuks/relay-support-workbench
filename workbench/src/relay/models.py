from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["agent", "supervisor", "observer"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DemoSession(Contract):
    role: Role = "agent"


class Ask(Contract):
    question: str = Field(min_length=3, max_length=1500)
    remember: bool = True


class Proposal(Contract):
    amount_naira: int = Field(ge=100, le=100_000)
    rationale: str = Field(min_length=10, max_length=1000)
    case_version: int = Field(ge=1)


class Decision(Contract):
    decision: Literal["approve", "reject"]
    reason: str = Field(min_length=5, max_length=500)


class Actor(BaseModel):
    workspace: str
    tenant: str = "kora"
    role: Role
    name: str
    csrf: str


class Health(BaseModel):
    status: Literal["ok"]
    product: Literal["relay"]
    checkpoint: str
    provider: Literal["fixture", "openai", "openrouter"]
    database: Literal["ready"]
    external_actions: Literal[False]


class PublicActor(BaseModel):
    role: Role
    name: str
    tenant: str


class SessionResponse(BaseModel):
    actor: PublicActor
    csrf_token: str
    mode: Literal["local-demo"]
    checkpoint: str
    provider: Literal["fixture", "openai", "openrouter"] = "fixture"


class CaseSummary(BaseModel):
    id: str
    customer: str
    initials: str
    subject: str
    category: str
    priority: str
    route: str
    shipment_id: str
    status: Literal["open", "awaiting_approval", "resolved"]
    version: int


class CaseList(BaseModel):
    items: list[CaseSummary]
    total: int


class Shipment(BaseModel):
    id: str
    service: str
    status: str
    delay_hours: int
    fee_naira: int
    delivered: bool
    events: list[str]


class CaseDetail(CaseSummary):
    message: str
    shipment: Shipment


class Citation(BaseModel):
    id: str
    title: str
    version: str
    excerpt: str
    chunk_id: str | None = None
    start: int | None = None
    end: int | None = None
    score: float | None = None


class Investigation(BaseModel):
    id: str
    provider: Literal["fixture", "openai", "openrouter"]
    model: str | None
    status: Literal["supported", "insufficient_evidence", "unavailable"]
    answer: str
    citations: list[Citation]
    tools: list[dict[str, Any]]
    suggested_credit_naira: int | None
    trace: dict[str, Any]


class Exchange(BaseModel):
    question: str
    answer: Investigation


class PublicProposal(BaseModel):
    id: str
    case_id: str
    amount: int
    rationale: str
    status: Literal["pending", "approved", "rejected"]
    created: float
    decision_reason: str | None
    proposer_role: Role


class CaseResponse(BaseModel):
    case: CaseDetail
    messages: list[Exchange]
    proposals: list[PublicProposal]


class ResolutionResponse(BaseModel):
    id: str
    status: Literal["pending", "approved", "rejected"]
    amount_naira: int
