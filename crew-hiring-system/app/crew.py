"""Crew assembly and execution for the Hiring Decision Crew."""

import json

from crewai import Crew, Process

from app.agents import (
    build_behavioral_interviewer,
    build_bias_auditor,
    build_comparative_analyst,
    build_hiring_manager,
    build_resume_screener,
    build_technical_interviewer,
)
from app.tasks import (
    build_behavioral_task,
    build_bias_audit_task,
    build_comparison_task,
    build_decision_task,
    build_screening_task,
    build_technical_task,
    resolve_role_criteria,
)


def build_crew(
    resume: str, job_description: str, verbose: bool = True
) -> Crew:
    criteria = resolve_role_criteria(job_description)

    screener = build_resume_screener()
    technical = build_technical_interviewer()
    behavioral = build_behavioral_interviewer()
    manager = build_hiring_manager()
    auditor = build_bias_auditor()

    screening_task = build_screening_task(screener, resume, job_description, criteria)
    technical_task = build_technical_task(technical, screening_task, criteria)
    behavioral_task = build_behavioral_task(
        behavioral, screening_task, technical_task, criteria,
    )
    decision_task = build_decision_task(
        manager, screening_task, technical_task, behavioral_task, criteria,
    )
    bias_audit_task = build_bias_audit_task(
        auditor, screening_task, technical_task, behavioral_task, decision_task,
    )

    return Crew(
        agents=[screener, technical, behavioral, manager, auditor],
        tasks=[
            screening_task, technical_task, behavioral_task,
            decision_task, bias_audit_task,
        ],
        process=Process.sequential,
        verbose=verbose,
    )


def run(resume: str, job_description: str, verbose: bool = True) -> str:
    crew = build_crew(resume, job_description, verbose)
    try:
        result = crew.kickoff()
    except Exception as exc:
        raise RuntimeError(f"Crew execution failed: {exc}") from exc
    return str(result)


# ---------------------------------------------------------------------------
# Multi-candidate comparison
# ---------------------------------------------------------------------------

def _parse_json(raw: str) -> dict | None:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def run_comparison(
    resumes: list[tuple[str, str]],
    job_description: str,
    verbose: bool = True,
) -> tuple[list[list], dict | None]:
    """Evaluate multiple candidates and compare them.

    *resumes* is a list of ``(label, resume_text)`` pairs.

    Returns ``(per_candidate_outputs, comparison_result)`` where
    ``per_candidate_outputs`` is a list of per-candidate task-output lists
    and ``comparison_result`` is the parsed comparison JSON (or ``None``
    if there is only one candidate).
    """
    all_outputs: list[list] = []
    candidate_summaries: list[dict] = []

    for label, resume_text in resumes:
        crew = build_crew(resume_text, job_description, verbose=verbose)
        result = crew.kickoff()
        task_outputs = result.tasks_output if hasattr(result, "tasks_output") else []
        all_outputs.append(task_outputs)

        # Build a compact summary for the comparison step
        decision_raw = task_outputs[3].raw if len(task_outputs) > 3 else "{}"
        bias_raw = task_outputs[4].raw if len(task_outputs) > 4 else "{}"
        candidate_summaries.append({
            "candidate": label,
            "decision": _parse_json(decision_raw) or {},
            "bias_audit": _parse_json(bias_raw) or {},
        })

    comparison_result = None
    if len(resumes) > 1:
        analyst = build_comparative_analyst()
        comparison_task = build_comparison_task(analyst, candidate_summaries)
        comparison_crew = Crew(
            agents=[analyst],
            tasks=[comparison_task],
            process=Process.sequential,
            verbose=verbose,
        )
        comp_result = comparison_crew.kickoff()
        comp_outputs = (
            comp_result.tasks_output
            if hasattr(comp_result, "tasks_output")
            else []
        )
        if comp_outputs:
            comparison_result = _parse_json(comp_outputs[0].raw)

    return all_outputs, comparison_result
