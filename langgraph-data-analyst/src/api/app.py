"""FastAPI application for the LangGraph Data Analyst service."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.graph.workflow import workflow

logger = logging.getLogger(__name__)

app = FastAPI(
    title="LangGraph Data Analyst",
    version="1.0.0",
)


class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1)


class AnalyzeResponse(BaseModel):
    final_report: str


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Run the LangGraph analysis workflow and return the final report."""
    logger.info("POST /analyze — query=%.120s file_path=%s", request.query, request.file_path)

    try:
        result = await _run_workflow(request.query, request.file_path)
    except Exception:
        logger.exception("Workflow failed for query: %.120s", request.query)
        raise HTTPException(status_code=500, detail="Analysis workflow failed.")

    final_report = result.get("final_report", "")
    if not final_report:
        logger.warning("Workflow produced empty report for query: %.120s", request.query)
        raise HTTPException(status_code=500, detail="Workflow produced no report.")

    logger.info("POST /analyze — report generated (%d chars)", len(final_report))
    return AnalyzeResponse(final_report=final_report)


async def _run_workflow(query: str, file_path: str) -> dict:
    """Invoke the LangGraph workflow. Runs synchronously inside the event loop."""
    state = {
        "user_query": query,
        "dataframe_path": file_path,
        "retry_count": 0,
    }
    return workflow.invoke(state)
