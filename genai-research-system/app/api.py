from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.service import normalize_formats, normalize_tone, run_research_workflow
from shared.api import create_app


class ResearchRunRequest(BaseModel):
    query: str = Field(..., min_length=1)
    tone: str = Field(default="formal")
    formats: list[str] = Field(default_factory=lambda: ["report"])


class ResearchRunResponse(BaseModel):
    run_id: str
    query: str
    tone: str
    formats: list[str]
    report: str = ""
    blog: str = ""
    linkedin_post: str = ""
    twitter_thread: str = ""
    best_case: dict[str, Any] = Field(default_factory=dict)
    worst_case: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    node_timings: dict[str, float] = Field(default_factory=dict)
    trace: list[dict[str, Any]] = Field(default_factory=list)


router = APIRouter(prefix="/research", tags=["research"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "project": "genai-research-system"}


@router.post("/run", response_model=ResearchRunResponse)
async def run_research(body: ResearchRunRequest) -> ResearchRunResponse:
    result = run_research_workflow(
        body.query,
        tone=normalize_tone(body.tone),
        formats=normalize_formats(body.formats),
    )
    return ResearchRunResponse(**{key: value for key, value in result.items() if key != "state"})


app = create_app(
    title="Flagship Multi-Agent Research System",
    version="2.0.0",
    description="Dedicated API for the flagship multi-agent research workflow.",
)
app.include_router(router)