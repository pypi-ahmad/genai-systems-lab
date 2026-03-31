"""Task definitions for the Startup Team Simulator."""

import json

from crewai import Agent, Task

VISION_SCHEMA = {
    "mission": "One-sentence mission statement",
    "target_market": "Description of the target market",
    "value_proposition": "Core value proposition",
    "competitive_advantages": ["advantage 1", "advantage 2"],
    "success_metrics": [{"metric": "name", "target": "value"}],
    "go_to_market": "Go-to-market strategy description",
}

PRODUCT_SCHEMA = {
    "personas": [{"name": "string", "description": "string", "needs": ["string"]}],
    "mvp_features": [{"name": "string", "priority": "must|should|could|wont", "description": "string"}],
    "user_stories": [{"as_a": "string", "i_want": "string", "so_that": "string"}],
    "roadmap": [{"phase": "string", "milestone": "string", "features": ["string"]}],
}

ARCHITECTURE_SCHEMA = {
    "system_overview": "High-level architecture description",
    "tech_stack": [{"component": "string", "technology": "string", "rationale": "string"}],
    "data_model": [{"entity": "string", "fields": ["string"], "relationships": ["string"]}],
    "api_design": [{"endpoint": "string", "method": "string", "purpose": "string"}],
    "infrastructure": {"hosting": "string", "ci_cd": "string", "monitoring": "string"},
    "scalability": "Scalability strategy description",
    "risks": [{"risk": "string", "impact": "string", "mitigation": "string"}],
}

EXECUTION_SCHEMA = {
    "sprints": [{"number": 1, "goal": "string", "tasks": [{"task": "string", "effort_days": 0}]}],
    "milestones": [{"name": "string", "target_date": "string", "criteria": "string"}],
    "dependencies": [{"task": "string", "depends_on": ["string"]}],
    "risks": [{"risk": "string", "mitigation": "string"}],
    "mvp_definition_of_done": ["criterion 1", "criterion 2"],
}

REVIEW_SCHEMA = {
    "strengths": ["string"],
    "weaknesses": ["string"],
    "gaps": ["string"],
    "recommendations": ["string"],
}

PROPOSAL_SCHEMA = {
    "angle": "One-sentence description of the proposed direction",
    "target_market": "Who this serves",
    "differentiator": "What makes this unique",
    "monetization": "How this makes money",
    "risks": ["key risk 1", "key risk 2"],
    "rationale": "Why this direction is promising",
}

SELECTION_SCHEMA = {
    "selected_proposal": "Name of the role whose proposal was selected (or 'synthesis')",
    "reasoning": "Why this direction was chosen",
    "mission": "One-sentence mission statement",
    "target_market": "Description of the target market",
    "value_proposition": "Core value proposition",
    "competitive_advantages": ["advantage 1", "advantage 2"],
    "success_metrics": [{"metric": "name", "target": "value"}],
    "go_to_market": "Go-to-market strategy description",
}


def build_vision_task(agent: Agent, idea: str) -> Task:
    return Task(
        description=(
            f"Analyze the following startup idea and produce a strategic vision "
            f"document:\n\n{idea}\n\n"
            "Define the startup's mission, target market, value proposition, "
            "competitive advantages, key success metrics, and go-to-market strategy. "
            "Ground every claim in market reasoning — avoid generic statements.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(VISION_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the vision schema.",
        agent=agent,
    )


def build_product_task(agent: Agent, vision_task: Task) -> Task:
    return Task(
        description=(
            "Based on the CEO's vision document, define the product specification.\n\n"
            "Translate the strategic direction into a concrete product definition. "
            "Identify target user personas, define the MVP feature set, prioritize "
            "features using MoSCoW, write user stories for the top features, and "
            "lay out a phased roadmap with clear milestones.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(PRODUCT_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the product schema.",
        agent=agent,
        context=[vision_task],
    )


def build_architecture_task(agent: Agent, product_task: Task) -> Task:
    return Task(
        description=(
            "Based on the product specification, design the technical architecture.\n\n"
            "Choose a technology stack with clear rationale for each choice. Define "
            "the system architecture, data model, API design approach, and "
            "infrastructure requirements. Identify scalability strategy and "
            "technical risks with mitigation plans. Favor proven technologies "
            "for the MVP.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(ARCHITECTURE_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the architecture schema.",
        agent=agent,
        context=[product_task],
    )


def build_execution_task(agent: Agent, architecture_task: Task) -> Task:
    return Task(
        description=(
            "Based on the technical architecture, produce a detailed implementation "
            "plan.\n\n"
            "Break the build into 2-week sprints with specific tasks and effort "
            "estimates. Define a dependency graph, milestone definitions, risk "
            "mitigation actions, and a clear definition of done for the MVP. "
            "Be realistic with time estimates — account for integration, testing, "
            "and infrastructure setup.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(EXECUTION_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the execution schema.",
        agent=agent,
        context=[architecture_task],
    )


def build_proposal_task(agent: Agent, idea: str, perspective: str) -> Task:
    return Task(
        description=(
            f"You are brainstorming startup directions from a {perspective} perspective.\n\n"
            f"Startup idea: {idea}\n\n"
            f"As the {perspective}, propose ONE compelling angle for this startup. "
            "Think about what direction would make the startup most likely to succeed "
            f"from your {perspective} viewpoint. Consider the target market, what makes "
            "this angle unique, how it would make money, and key risks.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(PROPOSAL_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the proposal schema.",
        agent=agent,
    )


def build_selection_task(agent: Agent, proposal_tasks: list[Task]) -> Task:
    return Task(
        description=(
            "You have received startup direction proposals from three team members: "
            "the Product Manager, the CTO, and the Lead Engineer. Each proposes a "
            "different angle for the startup.\n\n"
            "Review all three proposals carefully. You may:\n"
            "- Select the strongest proposal as-is\n"
            "- Synthesize the best elements from multiple proposals\n"
            "- Modify a proposal to address weaknesses\n\n"
            "Explain your reasoning, then produce a strategic vision that will guide "
            "the rest of the team. Include the mission, target market, value "
            "proposition, competitive advantages, success metrics, and go-to-market "
            "strategy.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(SELECTION_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the selection schema.",
        agent=agent,
        context=proposal_tasks,
    )


def build_review_task(reviewer: Agent, target_task: Task, target_role: str) -> Task:
    return Task(
        description=(
            f"You are peer-reviewing the deliverable produced by the {target_role}. "
            "Critically evaluate the output for:\n"
            "- Completeness — are any required sections missing or shallow?\n"
            "- Feasibility — are the claims realistic and grounded?\n"
            "- Internal consistency — do the parts contradict each other?\n"
            "- Alignment — does it fit the overall startup plan?\n\n"
            "Identify specific strengths, weaknesses, gaps, and provide actionable "
            "recommendations for improvement. Be constructive but direct — vague "
            "praise is not useful.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(REVIEW_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output=(
            f"A JSON peer review of the {target_role}'s output matching the review schema."
        ),
        agent=reviewer,
        context=[target_task],
    )
