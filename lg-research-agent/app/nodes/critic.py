from __future__ import annotations

from app.state import ResearchState
from shared.config import get_model
from shared.llm import generate_structured


CRITIQUE_SCHEMA = {
	"type": "object",
	"properties": {
		"assessment": {"type": "string"},
		"gaps": {
			"type": "array",
			"items": {"type": "string"},
			"maxItems": 3,
		},
	},
	"required": ["assessment", "gaps"],
}


def critic_node(state: ResearchState) -> ResearchState:
	findings = state.get("findings", [])
	findings_block = "\n".join(f"- {item}" for item in findings) or "- No findings"
	prompt = (
		"Review the research findings. State whether they are coherent and identify the most important gaps or caveats.\n\n"
		f"Query: {state.get('query', '')}\n"
		f"Findings:\n{findings_block}"
	)
	result = generate_structured(
		prompt=prompt,
		model=get_model("lg-research-agent"),
		schema=CRITIQUE_SCHEMA,
	)
	assessment = str(result.get("assessment", "")).strip()
	gaps = [str(gap).strip() for gap in result.get("gaps", []) if str(gap).strip()]
	critique = assessment
	if gaps:
		critique = f"{assessment} Gaps: {'; '.join(gaps)}"
	return {**state, "critique": critique.strip()}
