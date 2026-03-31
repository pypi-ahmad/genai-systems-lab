# Tasks

## 1 — Define Agents

File: `app/agents.py`

- [ ] Import `Agent` from `crewai`.
- [ ] Define `EVALUATION_MODEL = "gemini/gemini-3.1-pro-preview"` and `EXTRACTION_MODEL = "gemini/gemini-3-flash-preview"` constants.
- [ ] Create `build_resume_screener() -> Agent` with role `"Senior Resume Analyst"`, goal to extract key qualifications, experience timeline, skill matches, and red flags from the candidate's resume relative to the job description, and backstory as an experienced talent acquisition specialist with 10+ years screening technical resumes. Use `EXTRACTION_MODEL`.
- [ ] Create `build_technical_interviewer() -> Agent` with role `"Senior Technical Interviewer"`, goal to evaluate the candidate's technical competence, skill depth, and seniority calibration based on the resume screening report, and backstory as a staff engineer with experience conducting 500+ technical interviews. Use `EVALUATION_MODEL`.
- [ ] Create `build_behavioral_interviewer() -> Agent` with role `"Senior Behavioral Interviewer"`, goal to assess teamwork, communication, leadership potential, and culture alignment from resume signals and prior evaluation context, and backstory as an organizational psychologist turned hiring specialist. Use `EVALUATION_MODEL`.
- [ ] Create `build_hiring_manager() -> Agent` with role `"Hiring Manager"`, goal to synthesize all evaluations into a final hiring recommendation with confidence scoring and clear rationale, and backstory as an engineering director who has built and scaled multiple teams. Use `EVALUATION_MODEL`.
- [ ] Each builder function should return a fully configured `Agent` instance with `verbose=True`.

## 2 — Define Tasks

File: `app/tasks.py`

- [ ] Import `Task` from `crewai`.
- [ ] Define `SCREENING_SCHEMA` dict with required keys: `candidate_summary`, `experience_years`, `skill_matches`, `skill_gaps`, `red_flags`, `education_fit`, `overall_match_score`.
- [ ] Define `TECHNICAL_SCHEMA` dict with required keys: `technical_strengths`, `technical_concerns`, `skill_depth_assessment`, `seniority_calibration`, `recommended_interview_questions`, `technical_score`.
- [ ] Define `BEHAVIORAL_SCHEMA` dict with required keys: `collaboration_signals`, `leadership_indicators`, `communication_assessment`, `culture_fit_notes`, `growth_potential`, `behavioral_score`.
- [ ] Define `DECISION_SCHEMA` dict with required keys: `decision`, `confidence`, `key_strengths`, `key_concerns`, `compensation_guidance`, `onboarding_recommendations`, `dissenting_considerations`, `rationale`.
- [ ] Create `build_screening_task(agent, resume: str, job_description: str) -> Task` that assigns the Resume Screener agent to analyze the resume against the job description. Embed `SCREENING_SCHEMA` in the task description. Set `expected_output` to describe the JSON structure.
- [ ] Create `build_technical_task(agent, screening_task) -> Task` that assigns the Technical Interviewer agent to assess technical capabilities. Pass `screening_task` as context. Embed `TECHNICAL_SCHEMA` in the description.
- [ ] Create `build_behavioral_task(agent, screening_task, technical_task) -> Task` that assigns the Behavioral Interviewer agent to assess soft skills and culture fit. Pass both prior tasks as context. Embed `BEHAVIORAL_SCHEMA` in the description.
- [ ] Create `build_decision_task(agent, screening_task, technical_task, behavioral_task) -> Task` that assigns the Hiring Manager agent to produce a final recommendation. Pass all prior tasks as context. Embed `DECISION_SCHEMA` in the description.
- [ ] Each task description should instruct the agent to return structured JSON matching its schema.

## 3 — Build Crew

File: `app/crew.py`

- [ ] Import `Crew`, `Process` from `crewai`.
- [ ] Import agent builders from `app.agents` and task builders from `app.tasks`.
- [ ] Define `build_crew(resume: str, job_description: str, verbose: bool = True) -> Crew`.
- [ ] Inside `build_crew`, instantiate all four agents using the builder functions.
- [ ] Inside `build_crew`, instantiate all four tasks using the builder functions, passing the corresponding agent, `resume`, and `job_description` to the screening task, and chaining context through subsequent tasks.
- [ ] Construct and return a `Crew` with `process=Process.sequential`, passing agents and tasks in order: Resume Screener → Technical Interviewer → Behavioral Interviewer → Hiring Manager.
- [ ] Pass `verbose` through to the `Crew` constructor.

## 4 — Execute Workflow

File: `app/crew.py` (extend from task 3)

- [ ] Define `run(resume: str, job_description: str, verbose: bool = True) -> str` that calls `build_crew(resume, job_description, verbose)` and then `crew.kickoff()`.
- [ ] Extract the final output from the kickoff result.
- [ ] Return the full pipeline output as a string.
- [ ] Wrap `crew.kickoff()` in a try/except. On failure, raise `RuntimeError` with the agent name and error message.

