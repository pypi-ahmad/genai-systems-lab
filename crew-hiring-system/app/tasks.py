"""Task definitions for the Hiring Decision Crew."""

import json
import re

from crewai import Agent, Task

# ---------------------------------------------------------------------------
# Role-specific scoring criteria
# ---------------------------------------------------------------------------

ROLE_CRITERIA: dict[str, dict] = {
    "software_engineer": {
        "label": "Software Engineer",
        "keywords": [
            "software engineer", "backend engineer", "frontend engineer",
            "full-stack", "fullstack", "web developer", "platform engineer",
            "devops engineer", "sre", "site reliability",
        ],
        "screening_priorities": (
            "Experience relevance (40%): Hands-on coding and system-building "
            "experience in similar domains.\n"
            "Skill match (30%): Overlap with required languages, frameworks, "
            "and infrastructure.\n"
            "Education fit (15%): CS degree or equivalent practical training.\n"
            "Red flags (15%): Unexplained gaps, very short tenures, no "
            "progression."
        ),
        "technical_priorities": (
            "Coding & system design (35%): Evidence of building production "
            "systems, code quality signals.\n"
            "Architecture thinking (25%): Scalability, reliability, and "
            "trade-off awareness.\n"
            "Tooling ecosystem (20%): Familiarity with CI/CD, cloud, "
            "observability.\n"
            "Seniority calibration (20%): Does scope of past work match the "
            "target level?"
        ),
        "behavioral_priorities": (
            "Collaboration (30%): Cross-team work, code reviews, mentoring.\n"
            "Technical communication (25%): Writing, documentation, "
            "presentation signals.\n"
            "Ownership & initiative (25%): Led projects, drove improvements "
            "without being asked.\n"
            "Growth trajectory (20%): Learning new tech, expanding scope "
            "over time."
        ),
        "decision_weights": {
            "technical_score": 0.40,
            "behavioral_score": 0.30,
            "screening_score": 0.30,
        },
    },
    "data_scientist": {
        "label": "Data Scientist",
        "keywords": [
            "data scientist", "machine learning engineer", "ml engineer",
            "data analyst", "research scientist", "applied scientist",
            "nlp engineer", "cv engineer", "ai engineer",
        ],
        "screening_priorities": (
            "Experience relevance (25%): ML/analytics project experience.\n"
            "Skill match (35%): Proficiency in ML frameworks, statistics, "
            "and data tools.\n"
            "Education fit (25%): Advanced degree or equivalent research "
            "background.\n"
            "Red flags (15%): Only toy projects, no production ML, "
            "exaggerated claims."
        ),
        "technical_priorities": (
            "ML proficiency (35%): Model selection, training pipelines, "
            "evaluation methodology.\n"
            "Statistical depth (25%): Experiment design, hypothesis testing, "
            "causal inference.\n"
            "Engineering skills (20%): Data pipelines, deployment, code "
            "quality.\n"
            "Research aptitude (20%): Publications, novel approaches, "
            "staying current."
        ),
        "behavioral_priorities": (
            "Cross-functional communication (30%): Explaining results to "
            "non-technical stakeholders.\n"
            "Collaboration (25%): Working with engineering, product, and "
            "business teams.\n"
            "Growth potential (25%): Learning new methods, adapting to "
            "new domains.\n"
            "Leadership (20%): Mentoring, project ownership, driving "
            "data culture."
        ),
        "decision_weights": {
            "technical_score": 0.45,
            "behavioral_score": 0.25,
            "screening_score": 0.30,
        },
    },
    "product_manager": {
        "label": "Product Manager",
        "keywords": [
            "product manager", "program manager", "technical product manager",
            "product owner", "product lead",
        ],
        "screening_priorities": (
            "Experience relevance (35%): Product ownership and launch "
            "track record.\n"
            "Domain match (25%): Industry or domain alignment.\n"
            "Skill match (25%): Analytical tools, roadmapping, customer "
            "research.\n"
            "Red flags (15%): No shipped products, vague ownership claims."
        ),
        "technical_priorities": (
            "Technical fluency (30%): Ability to work with engineers and "
            "understand architecture.\n"
            "Analytical skills (30%): Data-driven decisions, metrics "
            "definition, A/B testing.\n"
            "Product sense (25%): Prioritisation frameworks, trade-off "
            "reasoning.\n"
            "Execution (15%): Shipping velocity, stakeholder management."
        ),
        "behavioral_priorities": (
            "Communication (35%): Written specs, presentations, stakeholder "
            "alignment.\n"
            "Leadership (25%): Influencing without authority, driving "
            "consensus.\n"
            "Collaboration (25%): Cross-functional team effectiveness.\n"
            "Growth potential (15%): Strategic thinking, scaling ambitions."
        ),
        "decision_weights": {
            "technical_score": 0.25,
            "behavioral_score": 0.45,
            "screening_score": 0.30,
        },
    },
}

DEFAULT_CRITERIA: dict = {
    "label": "General",
    "keywords": [],
    "screening_priorities": (
        "Experience relevance (30%): Years and depth of relevant work.\n"
        "Skill match (30%): Overlap with stated requirements.\n"
        "Education fit (20%): Academic background alignment.\n"
        "Red flags (20%): Gaps, inconsistencies, lack of progression."
    ),
    "technical_priorities": (
        "Core competence (30%): Depth in the primary skill area.\n"
        "Breadth (25%): Range of applicable skills.\n"
        "Problem-solving (25%): Evidence of tackling complex challenges.\n"
        "Seniority calibration (20%): Scope matches the target level."
    ),
    "behavioral_priorities": (
        "Collaboration (25%): Teamwork and cross-functional signals.\n"
        "Communication (25%): Written and verbal effectiveness.\n"
        "Leadership (25%): Initiative, mentoring, ownership.\n"
        "Growth potential (25%): Trajectory and learning agility."
    ),
    "decision_weights": {
        "technical_score": 0.35,
        "behavioral_score": 0.35,
        "screening_score": 0.30,
    },
}


def resolve_role_criteria(job_description: str) -> dict:
    """Pick the best-matching role criteria from the job description text."""
    if not job_description:
        return DEFAULT_CRITERIA
    lower = job_description.lower()
    for criteria in ROLE_CRITERIA.values():
        for kw in criteria["keywords"]:
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                return criteria
    return DEFAULT_CRITERIA


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------

SCREENING_SCHEMA = {
    "candidate_summary": "Brief overview of the candidate",
    "experience_years": "Total years of relevant experience",
    "skill_matches": ["skill that matches the JD"],
    "skill_gaps": ["required skill the candidate lacks"],
    "red_flags": ["concerning pattern or gap"],
    "education_fit": "How well education aligns with role requirements",
    "overall_match_score": "0.0 – 1.0 relevance score",
}

TECHNICAL_SCHEMA = {
    "technical_strengths": ["strong technical area"],
    "technical_concerns": ["area of weakness or uncertainty"],
    "skill_depth_assessment": "Depth vs breadth analysis",
    "seniority_calibration": "junior | mid | senior | staff",
    "recommended_interview_questions": ["targeted follow-up question"],
    "technical_score": "0.0 – 1.0 technical competence score",
}

BEHAVIORAL_SCHEMA = {
    "collaboration_signals": ["evidence of teamwork"],
    "leadership_indicators": ["evidence of leadership"],
    "communication_assessment": "Written and interpersonal communication evaluation",
    "culture_fit_notes": "Alignment with team values and working style",
    "growth_potential": "Capacity for development and learning",
    "behavioral_score": "0.0 – 1.0 behavioral competence score",
}

DECISION_SCHEMA = {
    "decision": "hire | reject",
    "confidence": "0.0 – 1.0 confidence in the decision",
    "technical_score": "0.0 – 1.0 technical competence score from the technical evaluation",
    "behavioral_score": "0.0 – 1.0 behavioral competence score from the behavioral evaluation",
    "key_strengths": ["top strength supporting the decision"],
    "key_concerns": ["remaining concern"],
    "compensation_guidance": "Suggested level / band based on evaluation",
    "onboarding_recommendations": ["focus area for first 90 days"],
    "dissenting_considerations": "Arguments for the opposite decision",
    "rationale": "Paragraph explaining the decision",
}

BIAS_SCHEMA = {
    "bias_flags": [
        {
            "bias_type": "Name of the bias (e.g. affinity, halo, confirmation, anchoring, attribution, gender, age, education-prestige)",
            "source_step": "screening | technical | behavioral | decision",
            "evidence": "Exact quote or paraphrase from the evaluation that shows this bias",
            "impact": "How it may have skewed the score or recommendation",
            "recommendation": "Specific corrective action",
        }
    ],
    "bias_risk_level": "low | medium | high",
    "overall_assessment": "Summary of bias audit findings",
    "adjusted_confidence": "0.0 – 1.0 confidence after accounting for detected biases (same as original if no significant bias found)",
}

COMPARISON_SCHEMA = {
    "ranking": [
        {
            "rank": "1-based position",
            "candidate": "Candidate identifier (file name or summary label)",
            "decision": "hire | reject",
            "confidence": "0.0 – 1.0",
            "technical_score": "0.0 – 1.0",
            "behavioral_score": "0.0 – 1.0",
            "key_differentiators": ["what sets this candidate apart"],
            "relative_weaknesses": ["compared to the other candidates"],
        }
    ],
    "recommendation": "Top candidate and reasoning",
    "comparison_notes": "Head-to-head analysis highlights",
}


def build_screening_task(
    agent: Agent, resume: str, job_description: str, criteria: dict | None = None,
) -> Task:
    c = criteria or DEFAULT_CRITERIA
    return Task(
        description=(
            "Analyze the following resume against the job description.\n\n"
            f"=== RESUME ===\n{resume}\n\n"
            f"=== JOB DESCRIPTION ===\n{job_description}\n\n"
            f"=== SCORING PRIORITIES ({c['label']} role) ===\n"
            f"{c['screening_priorities']}\n\n"
            "Use the priorities above to weight your evaluation. Extract the "
            "candidate summary, total years of relevant experience, matching "
            "skills, skill gaps, red flags, education fit, and an overall "
            "match score (0.0–1.0). Be specific — cite exact skills and "
            "timelines from the resume.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(SCREENING_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the screening schema.",
        agent=agent,
    )


def build_technical_task(
    agent: Agent, screening_task: Task, criteria: dict | None = None,
) -> Task:
    c = criteria or DEFAULT_CRITERIA
    return Task(
        description=(
            "Using the resume screening report, evaluate the candidate's "
            "technical competence.\n\n"
            f"=== SCORING PRIORITIES ({c['label']} role) ===\n"
            f"{c['technical_priorities']}\n\n"
            "Use the priorities above to weight your evaluation. Assess "
            "technical strengths and concerns, depth versus breadth "
            "of skills, calibrate seniority level (junior/mid/senior/staff), "
            "propose targeted interview questions, and assign a technical "
            "score (0.0–1.0). Reference specific skills and experience from "
            "the screening report.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(TECHNICAL_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the technical schema.",
        agent=agent,
        context=[screening_task],
    )


def build_behavioral_task(
    agent: Agent, screening_task: Task, technical_task: Task,
    criteria: dict | None = None,
) -> Task:
    c = criteria or DEFAULT_CRITERIA
    return Task(
        description=(
            "Using the resume screening and technical evaluation, assess the "
            "candidate's behavioral and soft-skill profile.\n\n"
            f"=== SCORING PRIORITIES ({c['label']} role) ===\n"
            f"{c['behavioral_priorities']}\n\n"
            "Use the priorities above to weight your evaluation. Identify "
            "collaboration signals, leadership indicators, "
            "communication style, culture fit, and growth potential. Assign "
            "a behavioral score (0.0–1.0). Ground every assessment in "
            "concrete resume signals — role transitions, team mentions, "
            "project descriptions.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(BEHAVIORAL_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the behavioral schema.",
        agent=agent,
        context=[screening_task, technical_task],
    )


def build_decision_task(
    agent: Agent,
    screening_task: Task,
    technical_task: Task,
    behavioral_task: Task,
    criteria: dict | None = None,
) -> Task:
    c = criteria or DEFAULT_CRITERIA
    weights = c["decision_weights"]
    weight_text = ", ".join(
        f"{k.replace('_', ' ').title()}: {int(v * 100)}%"
        for k, v in weights.items()
    )
    return Task(
        description=(
            "Synthesize the screening, technical, and behavioral evaluations "
            "into a final hiring decision.\n\n"
            f"=== DECISION WEIGHTS ({c['label']} role) ===\n"
            f"{weight_text}\n\n"
            "Apply these weights when combining the three evaluation scores "
            "into your confidence calculation. "
            "Decide hire or reject with a confidence score (0.0–1.0). "
            "Copy the technical_score from the technical evaluation and the "
            "behavioral_score from the behavioral evaluation into your "
            "output as-is. "
            "List key strengths and concerns, provide compensation guidance, "
            "onboarding recommendations, dissenting considerations (argue "
            "the opposite side), and a rationale paragraph. Justify every "
            "point by referencing specific findings from the prior analyses.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(DECISION_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the decision schema.",
        agent=agent,
        context=[screening_task, technical_task, behavioral_task],
    )


def build_bias_audit_task(
    agent: Agent,
    screening_task: Task,
    technical_task: Task,
    behavioral_task: Task,
    decision_task: Task,
) -> Task:
    return Task(
        description=(
            "You are an independent bias auditor. Review ALL prior "
            "evaluations (screening, technical, behavioral, and final "
            "decision) for cognitive biases and unfair reasoning.\n\n"
            "=== BIAS CATEGORIES TO CHECK ===\n"
            "1. Affinity bias: Favouring candidates similar to the "
            "evaluator's background.\n"
            "2. Halo/horn effect: Letting one strong/weak trait colour "
            "the entire assessment.\n"
            "3. Confirmation bias: Selectively citing evidence that "
            "supports an early impression while ignoring contradictions.\n"
            "4. Anchoring bias: Over-weighting the first piece of "
            "information (e.g. years of experience, school name).\n"
            "5. Attribution bias: Attributing successes to the candidate "
            "and failures to circumstances, or vice versa.\n"
            "6. Demographic proxies: Any reasoning that uses name, "
            "age, gender, ethnicity, nationality, school prestige, or "
            "company brand as a proxy for competence.\n"
            "7. Education-prestige bias: Penalising non-traditional "
            "education or over-rewarding elite institutions.\n\n"
            "For each detected bias, identify the exact evaluation step, "
            "quote the problematic reasoning, explain the impact, and "
            "suggest a corrective action.\n\n"
            "Rate the overall bias risk as low (no significant issues), "
            "medium (some flags but decision likely still defensible), or "
            "high (bias may have materially altered the outcome).\n\n"
            "Provide an adjusted_confidence score: keep it the same as the "
            "original decision confidence if bias risk is low, reduce it "
            "proportionally for medium/high risk.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(BIAS_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the bias audit schema.",
        agent=agent,
        context=[screening_task, technical_task, behavioral_task, decision_task],
    )


def build_comparison_task(
    agent: Agent,
    candidate_summaries: list[dict],
) -> Task:
    """Build a task that compares multiple candidates side by side.

    Each entry in *candidate_summaries* should contain the keys
    ``candidate``, ``decision``, and ``bias_audit`` representing the
    parsed JSON outputs from the per-candidate pipeline.
    """
    summaries_text = json.dumps(candidate_summaries, indent=2)
    return Task(
        description=(
            "You are a comparative analyst. Below are the evaluation "
            "summaries for multiple candidates applying for the same role. "
            "Rank them from strongest to weakest.\n\n"
            f"=== CANDIDATE EVALUATIONS ===\n{summaries_text}\n\n"
            "For each candidate, provide their rank, the original decision/"
            "confidence/scores, key differentiators relative to the other "
            "candidates, and relative weaknesses.\n\n"
            "Finish with an overall recommendation (the top candidate and "
            "why) and comparison notes summarising the head-to-head "
            "analysis.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(COMPARISON_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the comparison schema.",
        agent=agent,
    )
