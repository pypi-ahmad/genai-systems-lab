# Architecture

## Overview

The AI Interviewer is a multi-component system that conducts adaptive technical interviews through a structured loop of question generation, answer evaluation, difficulty adjustment, and feedback delivery. Each component owns a single responsibility and communicates through a shared session state managed by the Session Manager.

Primary flow:

`Question Generation → Candidate Answer → Evaluation → Difficulty Adjustment → Next Question`

## Component Responsibilities

### Question Generator (`question_generator.py`)

- Generates interview questions for a given topic and difficulty level.
- Accepts constraints from the Difficulty Manager (target difficulty, topic area, question type).
- Produces structured question objects containing the question text, expected answer criteria, and metadata (topic, difficulty, question type).
- Avoids repeating questions already asked in the current session.

### Evaluator (`evaluator.py`)

- Evaluates the candidate's answer against the expected answer criteria from the question.
- Produces a structured evaluation containing:
  - **Correctness**: Whether the core concepts are addressed accurately.
  - **Completeness**: Whether the answer covers the expected scope.
  - **Depth**: Whether the answer demonstrates understanding beyond surface-level recall.
  - **Specific gaps**: Concrete items the candidate missed or got wrong.
- Does not produce vague scores. Every rating must be backed by explicit reasoning tied to the answer content.

### Difficulty Manager (`difficulty_manager.py`)

- Tracks the candidate's performance trajectory across the session.
- Adjusts difficulty for the next question based on recent evaluation results.
- Uses a simple adaptive strategy:
  - Consistent strong evaluations → increase difficulty.
  - Consistent weak evaluations → decrease difficulty.
  - Mixed results → hold current level.
- Exposes the current difficulty level and topic weighting to the Question Generator.

### Feedback Generator (`feedback.py`)

- Transforms raw evaluation output into structured, candidate-facing feedback.
- Feedback includes:
  - What the candidate did well (with specifics from their answer).
  - What was missed or incorrect (with references to expected criteria).
  - A concrete suggestion for improvement.
- Keeps tone constructive and actionable. Avoids generic praise or criticism.

### Session Manager (`session.py`)

- Maintains the full conversation state for a single interview session.
- Tracks:
  - Questions asked (with metadata).
  - Candidate answers.
  - Evaluation results per question.
  - Current difficulty level.
  - Session-level statistics (total questions, accuracy trend, topic coverage).
- Provides session context to all other components so they can make informed decisions without duplicating state logic.

### Interviewer (`interviewer.py`)

- Orchestrates the interview loop by coordinating all components.
- Manages the turn-by-turn cycle: generate question → collect answer → evaluate → adjust difficulty → generate feedback → repeat.
- Enforces session boundaries (max questions, time limits, topic coverage goals).
- Produces a final session summary when the interview ends.

## System Flow

### 1. Session Initialization

The Session Manager creates a new session with the target role, topic list, starting difficulty, and configuration (max questions, difficulty range).

### 2. Question Generation

The Question Generator receives the current difficulty level, topic focus, and session history from the Session Manager. It produces a new question that hasn't been asked before in this session.

### 3. Candidate Answer

The system presents the question and collects the candidate's answer. The answer is stored in the session alongside the question.

### 4. Evaluation

The Evaluator receives the question (with expected criteria) and the candidate's answer. It produces a structured evaluation with correctness, completeness, depth, and specific gap analysis. No vague scoring — every judgment is grounded in the answer content.

### 5. Difficulty Adjustment

The Difficulty Manager reviews the latest evaluation and the session's performance history. It updates the difficulty level for the next question.

### 6. Feedback Delivery

The Feedback Generator transforms the evaluation into candidate-facing feedback. The feedback is stored in the session and presented to the candidate.

### 7. Loop or Conclude

The Interviewer checks session boundaries. If the interview continues, it loops back to step 2 with updated difficulty and topic weighting. If complete, it triggers a final session summary.

## Model Usage

### `gemini-3.1-pro-preview`

Use for tasks requiring precise reasoning and structured judgment.

Responsibilities:

- Evaluator: answer evaluation against criteria, gap identification, structured scoring with justification.
- Question Generator: producing well-calibrated questions with clear expected-answer criteria.

### `gemini-3-flash-preview`

Use for generation tasks where speed matters more than deep reasoning.

Responsibilities:

- Feedback Generator: transforming evaluations into candidate-facing feedback.
- Session summary generation at interview end.

This keeps evaluation accuracy on the stronger model while using the faster model for output formatting and synthesis.

## Structured Evaluation Format

Every evaluation must follow a consistent structure:

```
{
  "correctness": { "rating": "strong" | "partial" | "weak", "reasoning": "..." },
  "completeness": { "rating": "strong" | "partial" | "weak", "reasoning": "..." },
  "depth": { "rating": "strong" | "partial" | "weak", "reasoning": "..." },
  "gaps": ["specific gap 1", "specific gap 2"],
  "overall": "strong" | "partial" | "weak"
}
```

Ratings without reasoning are invalid. The Evaluator prompt must enforce this constraint.

## Design Notes

- Session state is the single source of truth. Components read from it rather than maintaining their own state.
- The difficulty adjustment algorithm should be simple and tunable. Start with a windowed average over recent evaluations; avoid over-engineering adaptive logic early.
- Question deduplication is handled by checking session history before finalizing a question.
- The system should be extensible to different interview types (behavioral, system design, coding) by swapping Question Generator prompts and evaluation criteria without changing the core loop.
- All LLM calls should use structured output (JSON) to keep downstream parsing reliable.
- Logging should capture the full question-answer-evaluation chain per turn for debugging and prompt iteration.

## High-Level Architecture Summary

The system is organized around the Interviewer orchestrator, five specialized components, and a shared session state. The Interviewer drives the turn-by-turn loop. The Question Generator produces calibrated questions, the Evaluator delivers grounded structured judgments, the Difficulty Manager adapts challenge level, the Feedback Generator delivers actionable guidance, and the Session Manager holds all state. The result is a clean, adaptive interview loop with strong separation of concerns and consistent structured evaluation throughout.