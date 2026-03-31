from __future__ import annotations

from app.state import ResearchState
from shared.config import get_model
from shared.llm import generate_structured


FINDINGS_SCHEMA = {
	"type": "object",
	"properties": {
		"findings": {
			"type": "array",
			"items": {
				"type": "object",
				"properties": {
					"title": {"type": "string"},
					"detail": {"type": "string"},
				},
				"required": ["title", "detail"],
			},
			"minItems": 2,
			"maxItems": 5,
		}
	},
	"required": ["findings"],
}


def researcher_node(state: ResearchState) -> ResearchState:
	query = state.get("query", "").strip()
	plan = state.get("plan", [])
	plan_block = "\n".join(f"- {step}" for step in plan) or "- Investigate the request directly"
	prompt = (
		"Produce concise research findings for the query below. Each finding should be factual, "
		"specific, and useful for a final synthesis.\n\n"
		f"Query: {query}\n"
		f"Plan:\n{plan_block}"
	)
	result = generate_structured(
		prompt=prompt,
		model=get_model("lg-research-agent"),
		schema=FINDINGS_SCHEMA,
	)
	findings: list[str] = []
	for item in result.get("findings", []):
		title = str(item.get("title", "")).strip()
		detail = str(item.get("detail", "")).strip()
		if title and detail:
			findings.append(f"{title}: {detail}")
	return {**state, "findings": findings[:5]}
