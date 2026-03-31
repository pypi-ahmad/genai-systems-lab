# AI Interviewer

## Overview

An adaptive technical interview system that generates questions, evaluates answers, adjusts difficulty over time, and returns structured feedback. The project is built for iterative interview loops rather than single-prompt assessment.

## System Flow

The system starts from a topic, generates a question at the current difficulty, evaluates the candidate response, updates session state, adjusts difficulty, and repeats until the interview is complete.

```text
Topic -> Question Generator -> Candidate Answer -> Evaluator -> Difficulty Manager -> Feedback -> Next Question
```

## Architecture

The codebase separates question generation, answer evaluation, difficulty control, feedback generation, and session tracking so the interview loop remains explicit and configurable.

| Module | Responsibility |
|--------|----------------|
| app/question_generator.py | Generates topic-aware questions at the requested difficulty. |
| app/evaluator.py | Scores candidate answers with topic-specific rubrics. |
| app/difficulty_manager.py | Adjusts question difficulty from recent performance. |
| app/session.py | Tracks questions, answers, scores, and interview summary state. |
| app/interviewer.py | Runs the interactive interview loop and feedback cycle. |

## Features

- Adaptive interview loop with difficulty changes over time.
- Structured answer evaluation with explicit strengths and gaps.
- Session state tracking across multiple interview turns.
- Feedback generation tailored to the candidate response.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/ai-interviewer/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Python backend development"}'
```

## Evaluation

```text
POST /eval/ai-interviewer
```

Primary metrics: question quality, evaluation consistency, difficulty calibration, latency, and failure rate.
