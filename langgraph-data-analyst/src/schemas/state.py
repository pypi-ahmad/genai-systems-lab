"""LangGraph state schema for the data analyst workflow.

The state is a :class:`TypedDict` that flows through every node in the
analysis graph.  All fields use last-writer-wins semantics and default
to their zero-values so nodes can do partial updates.
"""

from __future__ import annotations

from typing_extensions import TypedDict


class AnalystState(TypedDict, total=False):
    """Typed dictionary representing the full graph state.

    Attributes:
        user_query: The user's natural-language analysis question.
        dataframe_path: Path to the uploaded data file.
        plan: Multi-step analysis plan produced by the planner.
        intermediate_steps: Accumulated reasoning / tool-call traces.
        code: Python source code to execute.
        execution_result: Captured output from code execution.
        validation_result: Validator verdict on the execution output.
        validation_passed: Whether the validator approved the output.
        final_report: Final Markdown report.
        error: Description of the most recent error, if any.
        retry_count: Number of plan → execute → validate cycles completed.
    """

    user_query: str
    dataframe_path: str
    plan: str
    intermediate_steps: list
    code: str
    execution_result: str
    validation_result: str
    validation_passed: bool
    final_report: str
    error: str | None
    retry_count: int
