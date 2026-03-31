"""Session state management for the AI Interviewer."""

from dataclasses import dataclass, field

DIFFICULTY_LEVELS = ("easy", "medium", "hard")


@dataclass
class Score:
    correctness: str  # "strong" | "partial" | "weak"
    completeness: str
    depth: str
    gaps: list[str] = field(default_factory=list)
    overall: str = "partial"


@dataclass
class Turn:
    question: str
    expected_criteria: list[str]
    topic: str
    difficulty: str
    answer: str | None = None
    score: Score | None = None


class InterviewSession:
    def __init__(self, role: str, topic: str, difficulty: str = "easy", max_questions: int = 5):
        if difficulty not in DIFFICULTY_LEVELS:
            raise ValueError(f"difficulty must be one of {DIFFICULTY_LEVELS}")

        self.role = role
        self.topic = topic
        self.difficulty = difficulty
        self.max_questions = max_questions
        self.turns: list[Turn] = []

    def add_question(self, question: str, expected_criteria: list[str], topic: str, difficulty: str) -> int:
        turn = Turn(
            question=question,
            expected_criteria=expected_criteria,
            topic=topic,
            difficulty=difficulty,
        )
        self.turns.append(turn)
        return len(self.turns) - 1

    def add_answer(self, turn_index: int, answer: str) -> None:
        self.turns[turn_index].answer = answer

    def update_score(self, turn_index: int, score: Score) -> None:
        self.turns[turn_index].score = score

    def get_history(self) -> list[str]:
        return [turn.question for turn in self.turns]

    def get_recent_scores(self, n: int = 2) -> list[Score]:
        scored = [turn.score for turn in self.turns if turn.score is not None]
        return scored[-n:]

    def get_summary(self) -> dict:
        scored_turns = [t for t in self.turns if t.score is not None]
        total = len(scored_turns)

        if total == 0:
            return {
                "role": self.role,
                "topic": self.topic,
                "total_questions": 0,
                "current_difficulty": self.difficulty,
                "ratings": {},
                "topics_covered": [],
            }

        ratings = {"strong": 0, "partial": 0, "weak": 0}
        for turn in scored_turns:
            overall = turn.score.overall
            if overall in ratings:
                ratings[overall] += 1

        topics_covered = list({turn.topic for turn in self.turns})

        return {
            "role": self.role,
            "topic": self.topic,
            "total_questions": total,
            "current_difficulty": self.difficulty,
            "ratings": ratings,
            "topics_covered": topics_covered,
        }
