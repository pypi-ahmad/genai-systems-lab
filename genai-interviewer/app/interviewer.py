"""Run an adaptive technical interview loop."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

from app.session import InterviewSession, Score
from app.question_generator import generate_question
from app.evaluator import evaluate_answer
from app.difficulty_manager import adjust_difficulty
from app.feedback import generate_feedback

DEFAULT_MIN_QUESTIONS = 5
DEFAULT_MAX_QUESTIONS = 7
QUIT_COMMANDS = {"quit", "exit", "q"}

CONSOLE = Console()


def _get_logger() -> logging.Logger:
    logger = logging.getLogger("ai_interviewer")
    if logger.handlers:
        return logger

    handler = RichHandler(rich_tracebacks=True, markup=False, show_time=False)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


LOG = _get_logger()


def _score_to_overall(score: float) -> str:
    if score > 0.75:
        return "strong"
    if score < 0.4:
        return "weak"
    return "partial"


def _print_summary(session: InterviewSession) -> None:
    summary = session.get_summary()
    lines = [
        f"Topic: {summary['topic']}",
        f"Role: {summary['role']}",
        f"Questions answered: {summary['total_questions']}",
        f"Final difficulty: {summary['current_difficulty']}",
    ]
    ratings = summary.get("ratings", {})
    if ratings:
        lines.append(f"Strong: {ratings.get('strong', 0)} | Partial: {ratings.get('partial', 0)} | Weak: {ratings.get('weak', 0)}")
    CONSOLE.print(Panel("\n".join(lines), title="Interview Summary", border_style="green"))


def _load_voice():
    """Lazy-import the voice module. Returns None if unavailable."""
    try:
        from app import voice
        return voice
    except Exception:
        return None


def _get_answer_text(voice_mod) -> str:
    """Collect candidate answer via voice (STT) mode."""
    return voice_mod.listen(prompt_text="Listening for your answer...")


def _present_text(text: str, voice_mod) -> None:
    """Speak text aloud via TTS."""
    voice_mod.speak(text)


def run_interview(
    topic: str,
    role: str = "Software Engineer",
    difficulty: str = "easy",
    min_questions: int = DEFAULT_MIN_QUESTIONS,
    max_questions: int = DEFAULT_MAX_QUESTIONS,
    voice: bool = False,
) -> dict:
    voice_mod = None
    if voice:
        voice_mod = _load_voice()
        if voice_mod is None:
            CONSOLE.print("[red]Voice module failed to load. Falling back to text mode.[/red]")

    session = InterviewSession(
        role=role,
        topic=topic,
        difficulty=difficulty,
        max_questions=max_questions,
    )

    mode_label = "voice" if voice_mod else "text"
    CONSOLE.print(Panel(
        f"Topic: {topic}\nRole: {role}\nDifficulty: {difficulty}\nQuestions: {min_questions}–{max_questions}\nMode: {mode_label}\n\nType 'quit' to end early.",
        title="AI Interviewer",
        border_style="blue",
    ))

    question_num = 0

    while question_num < max_questions:
        question_num += 1
        LOG.info("Turn %d/%d | difficulty=%s", question_num, max_questions, session.difficulty)

        # --- Generate question ---
        LOG.info("Generating question...")
        question = generate_question(
            topic=topic,
            difficulty=session.difficulty,
            history=session.get_history(),
        )
        turn_index = session.add_question(
            question=question,
            expected_criteria=[],
            topic=topic,
            difficulty=session.difficulty,
        )
        CONSOLE.print(f"\n[bold]Question {question_num}[/bold] ({session.difficulty}):")
        CONSOLE.print(Panel(question, border_style="cyan"))

        if voice_mod:
            _present_text(question, voice_mod)

        # --- Collect answer ---
        try:
            if voice_mod:
                answer = _get_answer_text(voice_mod)
                CONSOLE.print(f"[dim]Heard:[/dim] {answer}")
            else:
                answer = CONSOLE.input("[bold green]Your answer:[/bold green] ")
        except (EOFError, KeyboardInterrupt):
            LOG.info("Input ended — stopping interview.")
            break

        if answer.strip().lower() in QUIT_COMMANDS:
            answered = len([t for t in session.turns if t.answer is not None])
            if answered >= min_questions:
                LOG.info("Candidate quit after %d questions.", answered)
                session.turns.pop()
                break
            CONSOLE.print(f"[yellow]Please answer at least {min_questions} questions before quitting.[/yellow]")
            question_num -= 1
            session.turns.pop()
            continue

        session.add_answer(turn_index, answer)
        LOG.info("Answer recorded (%d chars).", len(answer))

        # --- Evaluate ---
        LOG.info("Evaluating answer...")
        evaluation = evaluate_answer(question=question, answer=answer, topic=topic)
        score_val = evaluation["score"]
        overall = _score_to_overall(score_val)

        session_score = Score(
            correctness=overall,
            completeness=overall,
            depth=overall,
            gaps=evaluation.get("missing_points", []),
            overall=overall,
        )
        session.update_score(turn_index, session_score)
        LOG.info("Score: %.2f (%s)", score_val, overall)

        # --- Adjust difficulty ---
        new_difficulty = adjust_difficulty(current=session.difficulty, score=score_val)
        if new_difficulty != session.difficulty:
            LOG.info("Difficulty: %s → %s", session.difficulty, new_difficulty)
        session.difficulty = new_difficulty

        # --- Generate feedback ---
        LOG.info("Generating feedback...")
        feedback = generate_feedback(
            question=question,
            answer=answer,
            evaluation=evaluation,
        )
        CONSOLE.print(Panel(feedback, title=f"Feedback (score: {score_val:.2f})", border_style="yellow"))

        if voice_mod:
            _present_text(feedback, voice_mod)

    # --- Summary ---
    _print_summary(session)
    summary = session.get_summary()

    if voice_mod:
        summary_text = (
            f"Interview complete. You answered {summary['total_questions']} questions. "
            f"Final difficulty: {summary['current_difficulty']}."
        )
        _present_text(summary_text, voice_mod)

    return summary