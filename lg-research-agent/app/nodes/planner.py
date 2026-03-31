from __future__ import annotations

from app.state import ResearchState
from shared.config import get_model
from shared.llm import generate_structured


PLAN_SCHEMA = {
	"type": "object",
	"properties": {
		"steps": {
			"type": "array",
			"items": {"type": "string"},
			"minItems": 2,
			"maxItems": 5,
		}
	},
	"required": ["steps"],
}


def planner_node(state: ResearchState) -> ResearchState:
	query = state.get("query", "").strip()
	prompt = (
		"Break the research request into 3 to 5 focused investigation steps. "
		"Keep each step concrete and answerable.\n\n"
		f"Request: {query}"
	)
	result = generate_structured(
		prompt=prompt,
		model=get_model("lg-research-agent"),
		schema=PLAN_SCHEMA,
	)
	steps = [str(step).strip() for step in result.get("steps", []) if str(step).strip()]
	return {**state, "plan": steps[:5]}
