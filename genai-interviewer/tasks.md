# Tasks

## Session State Design

- Define the session state schema in `app/session.py` with fields for: topic, difficulty level, questions asked, answers, evaluations, and session config.
- Add a `create_session` function that initializes a new session with a topic, starting difficulty, and max question count.
- Add a `record_turn` function that appends a question, answer, and evaluation to the session history.
- Add a `get_history` function that returns the list of past questions (used for deduplication by the Question Generator).
- Add a `get_recent_evaluations` function that returns the last N evaluations (used by the Difficulty Manager).
- Add a `get_summary` function that computes session-level stats: total questions, ratings distribution, topic coverage.

## Question Generation

- Define the question output format in `app/question_generator.py`: question text, expected answer criteria (list of strings), topic, difficulty, question type.
- Write a `generate_question` function that takes topic, difficulty level, and session history, then calls the LLM to produce a structured question.
- Build the prompt template: instruct the model to produce a question at the given difficulty, include 3-5 expected answer criteria, and avoid questions already in the session history.
- Parse the LLM response into the structured question format. Use JSON output mode.
- Add a fallback: if the LLM output fails to parse, retry once with a simplified prompt.

## Answer Evaluation

- Define the evaluation output format in `app/evaluator.py`: correctness (rating + reasoning), completeness (rating + reasoning), depth (rating + reasoning), gaps list, overall rating.
- Write an `evaluate_answer` function that takes the question object and the candidate's answer, then calls the LLM to produce a structured evaluation.
- Build the evaluation prompt: include the question text, expected criteria, and candidate answer. Instruct the model to rate each dimension as strong/partial/weak with explicit reasoning. Require that gaps reference specific missing items from the criteria.
- Parse the LLM response into the evaluation format. Reject any evaluation where a rating has no reasoning.
- Use `gemini-3.1-pro-preview` for this call.

## Difficulty Adjustment

- Define difficulty as an integer scale (1-5) in `app/difficulty_manager.py`.
- Write an `adjust_difficulty` function that takes the current difficulty and a list of recent evaluations.
- Implement the adjustment logic: if the last 2 evaluations are both "strong" overall, increase by 1. If both "weak", decrease by 1. Otherwise, hold.
- Clamp the result to the 1-5 range.
- Return the new difficulty level.

## Feedback Generation

- Define the feedback output format in `app/feedback.py`: strengths (list), weaknesses (list), suggestion (string).
- Write a `generate_feedback` function that takes the evaluation object and the candidate's answer, then calls the LLM to produce structured feedback.
- Build the feedback prompt: instruct the model to reference specifics from the answer (not generic statements), list concrete strengths, list concrete weaknesses with what was expected, and give one actionable improvement suggestion.
- Parse the LLM response into the feedback format. Use JSON output mode.
- Use `gemini-3-flash-preview` for this call.

## Interview Loop

- Write the main interview loop in `app/interviewer.py`.
- On each iteration: get current difficulty from session → generate question → present question → collect answer → evaluate → adjust difficulty → generate feedback → record turn in session.
- After each turn, check stop conditions: max questions reached or candidate ends session.
- When the interview ends, call `get_summary` on the session and return the final summary.
- Add error handling: if any LLM call fails, log the error and skip to the next turn rather than crashing the session.

