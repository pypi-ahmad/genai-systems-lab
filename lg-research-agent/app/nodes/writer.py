from __future__ import annotations

from app.state import ResearchState
from shared.config import get_model
from shared.llm import generate_text


def writer_node(state: ResearchState) -> ResearchState:
	plan_block = "\n".join(f"- {step}" for step in state.get("plan", [])) or "- No plan"
	findings_block = "\n".join(f"- {item}" for item in state.get("findings", [])) or "- No findings"
	critique = state.get("critique", "").strip() or "No critique provided."

	prompt = (
		"Write a concise research summary with three sections: Key Findings, Caveats, and Recommended Next Steps.\n\n"
		f"Query: {state.get('query', '')}\n\n"
		f"Plan:\n{plan_block}\n\n"
		f"Findings:\n{findings_block}\n\n"
		f"Critique:\n{critique}"
	)
	report = generate_text(prompt=prompt, model=get_model("lg-research-agent")).strip()
	return {**state, "report": report, "success": bool(report)}
