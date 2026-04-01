"""Common Pydantic models shared across projects."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    """Standard request envelope for LLM calls."""

    prompt: str = Field(..., min_length=1)
    model: str = Field(default="gemini-3-flash-preview")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    output_schema: dict[str, Any] | None = Field(
        default=None,
        description="JSON schema for structured output.",
    )


class LLMResponse(BaseModel):
    """Standard response envelope from LLM calls."""

    text: str = ""
    structured: dict[str, Any] | None = None
    model: str = ""
    latency_ms: float = 0.0


class ErrorDetail(BaseModel):
    """Standardised error payload."""

    error: str
    detail: str = ""
    code: int = 500


class StatusResponse(BaseModel):
    """Health-check / status response."""

    status: str = "ok"
    version: str = ""
    project: str = ""


class BaseRequest(BaseModel):
    """Generic project request envelope."""

    input: str = ""
    session_id: int | None = None


class RunMemoryEntryResponse(BaseModel):
    """Safe abstracted memory captured during a run."""

    step: str
    content: str
    type: Literal["thought", "action", "observation"]


class RunTimelineEntryResponse(BaseModel):
    """Persisted execution timeline entry for replay."""

    timestamp: float = 0.0
    step: str
    event: str
    data: str


class RunExplanationStepResponse(BaseModel):
    """Concise explanation of one major execution step."""

    step: str
    what_happened: str
    why_it_mattered: str


class RunExplanationDecisionResponse(BaseModel):
    """Important decision inferred from observable run artifacts."""

    decision: str
    reason: str


class BaseResponse(BaseModel):
    """Generic project response envelope."""

    output: str = ""
    latency: float = 0.0
    confidence: float = 0.0
    session_id: int | None = None
    session_memory: list[str] = Field(default_factory=list)
    used_session_context: bool = False
    success: bool = True
    memory: list[RunMemoryEntryResponse] = Field(default_factory=list)
    timeline: list[RunTimelineEntryResponse] = Field(default_factory=list)


class AuthRequest(BaseModel):
    """Authentication request payload."""

    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class AuthUserResponse(BaseModel):
    """Authenticated user summary."""

    id: int
    email: str


class AuthConfigResponse(BaseModel):
    """Frontend auth capabilities exposed by the API."""

    public_signup: bool = False


class AuthResponse(BaseModel):
    """Authentication response payload."""

    token: str
    user: AuthUserResponse


class HistoryRunResponse(BaseModel):
    """Serialized saved run payload."""

    id: int
    user_id: int
    session_id: int | None = None
    project: str
    input: str
    output: str
    memory: list[RunMemoryEntryResponse] = Field(default_factory=list)
    timeline: list[RunTimelineEntryResponse] = Field(default_factory=list)
    latency: float = 0.0
    confidence: float = 0.0
    success: bool = True
    timestamp: str | None = None
    share_token: str | None = None
    is_public: bool = False
    expires_at: str | None = None


class RunExplanationResponse(BaseModel):
    """Structured explanation generated for a saved run."""

    steps_taken: list[RunExplanationStepResponse] = Field(default_factory=list)
    key_decisions: list[RunExplanationDecisionResponse] = Field(default_factory=list)
    final_reasoning: str = ""
    final_outcome: str = ""


class HistoryResponse(BaseModel):
    """Saved run history response."""

    count: int = 0
    runs: list[HistoryRunResponse] = Field(default_factory=list)


class SessionResponse(BaseModel):
    """Serialized active session state."""

    id: int
    user_id: int
    memory: list[str] = Field(default_factory=list)
    entry_count: int = 0
    updated_at: str | None = None


class ShareRunRequest(BaseModel):
    """Request to share a run publicly."""

    expires_in_hours: int | None = Field(default=None, ge=1, le=720)


class ShareRunResponse(BaseModel):
    """Response after sharing a run."""

    share_token: str
    is_public: bool = True
    expires_at: str | None = None


class SharedRunResponse(BaseModel):
    """Public view of a shared run (no user_id exposed)."""

    id: int
    project: str
    input: str
    output: str
    memory: list[RunMemoryEntryResponse] = Field(default_factory=list)
    timeline: list[RunTimelineEntryResponse] = Field(default_factory=list)
    latency: float = 0.0
    confidence: float = 0.0
    timestamp: str | None = None


class ProjectMetricsResponse(BaseModel):
    """Per-project operational metrics."""

    name: str
    latency: float = 0.0
    success_rate: float = 0.0


class MetricsResponse(BaseModel):
    """Aggregate operational metrics for the API."""

    total_requests: int = 0
    avg_latency: float = 0.0
    success_rate: float = 0.0
    projects: list[ProjectMetricsResponse] = Field(default_factory=list)


class TimeSeriesMetricPointResponse(BaseModel):
    """One persisted run metric for charting performance over time."""

    timestamp: str
    latency: float = 0.0
    confidence: float = 0.0
    success: bool = False


class LeaderboardEntryResponse(BaseModel):
    """Benchmark leaderboard entry for one project."""

    project: str
    accuracy: float = 0.0
    latency: float = 0.0
    score: float = 0.0
