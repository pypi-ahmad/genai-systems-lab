"""Agent definitions for the Hiring Decision Crew."""

from crewai import Agent

EVALUATION_MODEL = "gemini/gemini-3.1-pro-preview"
EXTRACTION_MODEL = "gemini/gemini-3-flash-preview"


def build_resume_screener() -> Agent:
    return Agent(
        role="Senior Resume Analyst",
        goal=(
            "Extract key qualifications, experience timeline, skill matches, "
            "and red flags from the candidate's resume relative to the job "
            "description. Produce a structured screening report with an "
            "overall match score."
        ),
        backstory=(
            "Talent acquisition specialist with 10+ years screening technical "
            "resumes. Trained to identify both explicit qualifications and "
            "implicit signals — career progression patterns, project "
            "complexity indicators, and employment gaps."
        ),
        llm=EXTRACTION_MODEL,
        verbose=True,
    )


def build_technical_interviewer() -> Agent:
    return Agent(
        role="Senior Technical Interviewer",
        goal=(
            "Evaluate the candidate's technical competence, skill depth, and "
            "seniority calibration based on the resume screening report. "
            "Identify strengths, concerns, and recommended follow-up "
            "interview questions."
        ),
        backstory=(
            "Staff engineer with experience conducting 500+ technical "
            "interviews across backend, frontend, and infrastructure roles. "
            "Evaluates depth versus breadth, practical experience versus "
            "theoretical knowledge, and ability to operate at the required "
            "seniority level."
        ),
        llm=EVALUATION_MODEL,
        verbose=True,
    )


def build_behavioral_interviewer() -> Agent:
    return Agent(
        role="Senior Behavioral Interviewer",
        goal=(
            "Assess the candidate's teamwork, communication, leadership "
            "potential, and culture alignment from resume signals and prior "
            "evaluation context. Surface collaboration patterns and growth "
            "indicators."
        ),
        backstory=(
            "Organizational psychologist turned hiring specialist. Reads "
            "between the lines of career moves, role transitions, and project "
            "descriptions to assess collaboration style, ownership patterns, "
            "and growth mindset."
        ),
        llm=EVALUATION_MODEL,
        verbose=True,
    )


def build_hiring_manager() -> Agent:
    return Agent(
        role="Hiring Manager",
        goal=(
            "Synthesize all prior evaluations into a final hiring "
            "recommendation with a clear decision, confidence score, key "
            "strengths, concerns, and onboarding guidance."
        ),
        backstory=(
            "Engineering director who has built and scaled multiple teams. "
            "Makes hiring decisions balancing immediate team needs with "
            "long-term growth, weighing both hard skills and team dynamics. "
            "Biased toward clear, defensible decisions with specific reasoning."
        ),
        llm=EVALUATION_MODEL,
        verbose=True,
    )


def build_bias_auditor() -> Agent:
    return Agent(
        role="Bias Auditor",
        goal=(
            "Review the full evaluation chain for cognitive biases, "
            "demographic assumptions, and unfair reasoning patterns. "
            "Flag any finding where the rationale relies on proxies for "
            "protected characteristics rather than job-relevant evidence. "
            "Produce a structured audit with a bias risk level."
        ),
        backstory=(
            "Industrial-organizational psychologist specialising in fair "
            "hiring practices and algorithmic bias detection. Trained on "
            "EEOC guidelines, adverse impact analysis, and structured "
            "interview research. Identifies halo effects, affinity bias, "
            "confirmation bias, and reasoning gaps that correlate with "
            "protected-class proxies."
        ),
        llm=EVALUATION_MODEL,
        verbose=True,
    )


def build_comparative_analyst() -> Agent:
    return Agent(
        role="Comparative Analyst",
        goal=(
            "Compare multiple candidates evaluated for the same role. "
            "Produce a ranked list with head-to-head analysis, highlighting "
            "relative strengths, weaknesses, and a clear top recommendation."
        ),
        backstory=(
            "Senior talent strategist who specialises in shortlist "
            "decisions. Compares candidates on a level playing field by "
            "normalising scores, surfacing differentiators, and accounting "
            "for bias-audit findings. Ensures the final ranking is "
            "defensible and tied to role requirements."
        ),
        llm=EVALUATION_MODEL,
        verbose=True,
    )