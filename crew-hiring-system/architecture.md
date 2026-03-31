# Architecture

## Overview

The Hiring Decision Crew is a CrewAI-based sequential pipeline where four specialized agents collaborate to evaluate a job candidate and produce a structured hiring recommendation. Each agent performs a focused evaluation stage — resume screening, technical assessment, behavioral assessment, and final synthesis — passing its structured output forward as context for the next stage. CrewAI manages agent orchestration, task delegation, and output chaining. There is no custom routing logic.

Primary flow:

```
Resume + Job Description → Resume Screener → Technical Interviewer → Behavioral Interviewer → Hiring Manager → Decision
```

## Crew Configuration

All agents execute within a single `Crew` configured with `process=Process.sequential`. The four tasks run in order, each building on the accumulated evaluation context. There are no conditional branches or loops — the pipeline runs exactly four steps, once.

```python
crew = Crew(
    agents=[resume_screener, technical_interviewer, behavioral_interviewer, hiring_manager],
    tasks=[screening_task, technical_task, behavioral_task, decision_task],
    process=Process.sequential,
    verbose=True,
)
```

### Why sequential

- Each evaluation stage depends on the findings of the previous stage. The Technical Interviewer needs the resume summary to focus on claimed skills; the Behavioral Interviewer needs both to probe gaps; the Hiring Manager needs all three to synthesize.
- A linear pass keeps token usage predictable and produces a clear audit trail for the hiring decision.
- Sequential execution mirrors real-world interview pipelines where each stage gates the next.

## Agents

Each agent is a CrewAI `Agent` with a defined role, goal, and backstory that constrains its evaluation behavior.

### Resume Screener

Performs initial resume analysis against job requirements.

- **Role:** Senior Resume Analyst
- **Goal:** Extract key qualifications, experience timeline, skill matches, and red flags from the candidate's resume relative to the job description.
- **Backstory:** Experienced talent acquisition specialist with 10+ years screening technical resumes. Trained to identify both explicit qualifications and implicit signals — career progression patterns, project complexity, and gaps.
- **Model:** `gemini-3-flash-preview` — resume extraction is a structured parsing task; speed matters more than deep reasoning.
- **Output:** JSON object with keys: `candidate_summary`, `experience_years`, `skill_matches`, `skill_gaps`, `red_flags`, `education_fit`, `overall_match_score` (0–100).

### Technical Interviewer

Assesses the candidate's technical depth and problem-solving ability.

- **Role:** Senior Technical Interviewer
- **Goal:** Evaluate the candidate's technical competence based on their resume, claimed skills, and typical proficiency expectations for the target role.
- **Backstory:** Staff engineer with experience conducting 500+ technical interviews across multiple domains. Evaluates depth vs. breadth, practical experience vs. theoretical knowledge, and ability to operate at the seniority level required.
- **Model:** `gemini-3.1-pro-preview` — technical evaluation requires reasoning about skill depth, technology tradeoffs, and seniority calibration.
- **Output:** JSON object with keys: `technical_strengths`, `technical_concerns`, `skill_depth_assessment`, `seniority_calibration`, `recommended_interview_questions`, `technical_score` (0–100).

### Behavioral Interviewer

Assesses soft skills, culture fit, and collaboration patterns.

- **Role:** Senior Behavioral Interviewer
- **Goal:** Evaluate the candidate's teamwork, communication, leadership potential, and alignment with team culture based on resume signals and prior evaluation context.
- **Backstory:** Organizational psychologist turned hiring specialist. Skilled at reading between the lines of career moves, role transitions, and project descriptions to assess collaboration style, ownership patterns, and growth mindset.
- **Model:** `gemini-3.1-pro-preview` — behavioral assessment requires nuanced reasoning about interpersonal patterns, motivation signals, and culture alignment.
- **Output:** JSON object with keys: `collaboration_signals`, `leadership_indicators`, `communication_assessment`, `culture_fit_notes`, `growth_potential`, `behavioral_score` (0–100).

### Hiring Manager

Synthesizes all evaluations into a final hiring recommendation.

- **Role:** Hiring Manager
- **Goal:** Produce a final hiring decision by weighing technical evaluation, behavioral assessment, and resume screening results against the role's requirements and team needs.
- **Backstory:** Engineering director who has built and scaled multiple teams. Makes hiring decisions balancing immediate team needs with long-term growth, considering both hard skills and team dynamics. Biased toward clear, defensible decisions with specific reasoning.
- **Model:** `gemini-3.1-pro-preview` — final synthesis requires weighing competing signals, identifying decision-relevant patterns across evaluations, and producing calibrated recommendations.
- **Output:** JSON object with keys: `decision` (hire / no_hire / strong_hire / further_evaluation), `confidence` (0–100), `key_strengths`, `key_concerns`, `compensation_guidance`, `onboarding_recommendations`, `dissenting_considerations`, `rationale`.

## Tasks

Each CrewAI `Task` binds an agent to a specific evaluation stage. Tasks execute in order, and each task receives the output of all preceding tasks as context. All tasks require agents to return structured JSON matching a predefined schema embedded in the task description.

### screening_task

- **Agent:** Resume Screener
- **Description:** Analyze the candidate's resume against the job description and produce a structured screening report.
- **Expected output:** JSON matching `SCREENING_SCHEMA`.
- **Context:** Resume text + job description (user input).

### technical_task

- **Agent:** Technical Interviewer
- **Description:** Based on the resume screening report, assess the candidate's technical capabilities for the target role.
- **Expected output:** JSON matching `TECHNICAL_SCHEMA`.
- **Context:** Resume screening report.

### behavioral_task

- **Agent:** Behavioral Interviewer
- **Description:** Based on the resume and technical evaluation, assess the candidate's behavioral and soft-skill fit.
- **Expected output:** JSON matching `BEHAVIORAL_SCHEMA`.
- **Context:** Resume screening report + technical evaluation.

### decision_task

- **Agent:** Hiring Manager
- **Description:** Synthesize all prior evaluations and produce a final hiring recommendation with clear rationale.
- **Expected output:** JSON matching `DECISION_SCHEMA`.
- **Context:** All prior outputs (screening + technical + behavioral).

## Model Usage

| Model | Agents | Rationale |
|---|---|---|
| `gemini-3.1-pro-preview` | Technical Interviewer, Behavioral Interviewer, Hiring Manager | Evaluation and synthesis tasks require strong analytical reasoning and calibrated judgment |
| `gemini-3-flash-preview` | Resume Screener | Resume extraction is a structured parsing task — speed and cost efficiency matter more than deep reasoning |

### Cost and latency considerations

- The Hiring Manager task produces the longest output since it synthesizes all prior evaluations with detailed rationale.
- The Resume Screener uses the cheaper, faster model since its primary job is structured information extraction rather than judgment.
- Total pipeline runs four LLM calls in sequence. Expect 30–60 seconds end-to-end depending on resume length and output detail.
- For batch candidate evaluation, the pipeline can be run in parallel per candidate since each crew instance is independent.

## Data Flow

```
User Input (resume + job description)
    │
    ▼
┌──────────────────┐  screening report  ┌────────────────────────┐
│  Resume Screener │ ────────────────── │ Technical Interviewer   │
│  (flash)         │                    │ (pro)                   │
└──────────────────┘                    └────────────────────────┘
                                                  │
                                         technical evaluation
                                                  │
                                                  ▼
                                        ┌────────────────────────┐
                                        │ Behavioral Interviewer  │
                                        │ (pro)                   │
                                        └────────────────────────┘
                                                  │
                                        behavioral evaluation
                                                  │
                                                  ▼
                                        ┌────────────────────────┐
                                        │    Hiring Manager       │
                                        │    (pro)                │
                                        └────────────────────────┘
                                                  │
                                                  ▼
                                           Final Decision
```

Each agent receives the full accumulated context — not just the immediately preceding output. The Technical Interviewer references the resume summary to focus on claimed skills. The Behavioral Interviewer references both to probe gaps between technical claims and collaboration evidence. The Hiring Manager sees all three evaluations to produce a calibrated final decision.

## Production Design Notes

### Output structure

- All agents return JSON objects matching predefined schemas defined in `tasks.py` (`SCREENING_SCHEMA`, `TECHNICAL_SCHEMA`, `BEHAVIORAL_SCHEMA`, `DECISION_SCHEMA`).
- Each task's description embeds the full JSON schema so the LLM sees the expected shape.
- The runtime parses each task's raw output as JSON when possible and preserves the raw text when parsing fails.
- Final output is four labeled JSON sections — one per evaluation stage.

### Error handling

- Wrap `crew.kickoff()` in a try/except. If any agent fails, log which evaluation stage failed and the partial outputs collected so far.
- CrewAI's built-in retry mechanism handles transient LLM failures. Configure `max_retry_limit` on the crew for additional resilience.
- If the Resume Screener fails, abort early — downstream agents have no context to work with.

### Observability

- Enable `verbose=True` on the crew to log agent reasoning and task transitions during development.
- Log each task's input length, output length, and execution time for cost tracking.
- Store the full pipeline output (all four evaluations) as a JSON artifact for audit and compliance.

### Configuration

| Parameter | Default | Purpose |
|---|---|---|
| `EVALUATION_MODEL` | `gemini-3.1-pro-preview` | Model for Technical, Behavioral, and Hiring Manager |
| `EXTRACTION_MODEL` | `gemini-3-flash-preview` | Model for Resume Screener |
| `VERBOSE` | `True` | Enable crew execution logging |
| `MAX_RETRY_LIMIT` | `3` | Retry limit for failed LLM calls |

### Testing

- Each agent can be tested in isolation by constructing a `Task` with hardcoded context and asserting the output structure matches its schema.
- Integration test the full crew with a mock LLM that returns canned responses per agent role, verifying all four stages execute and the final output contains a decision with rationale.
- Test edge cases: empty resume (should fail fast with clear error), resume with no relevant experience (should produce low scores but still complete), and LLM timeout (should retry or fail gracefully).

## Summary

The system is a four-agent CrewAI sequential pipeline for structured candidate evaluation. The Resume Screener extracts qualifications and flags, the Technical Interviewer assesses skill depth and seniority calibration, the Behavioral Interviewer evaluates soft skills and culture fit, and the Hiring Manager synthesizes all evaluations into a final recommendation. State flows forward through CrewAI's task chaining — no custom orchestrator, no branching logic. The stronger reasoning model handles evaluation and synthesis; the faster model handles resume extraction. Each stage produces structured JSON for auditability, and the final decision includes confidence scoring and dissenting considerations.
