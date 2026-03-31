from __future__ import annotations

import json
import os
from pathlib import Path

from app.state import WorkflowState

CHECKPOINT_PATH = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, "state.json"
)


def load_checkpoint(path: str | None = None) -> WorkflowState | None:
    """Load a previously saved state from disk.

    Returns ``None`` if the file does not exist or is invalid JSON.
    """
    target = Path(path or CHECKPOINT_PATH).resolve()
    if not target.is_file():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or "task" not in data:
        return None
    return WorkflowState(**data)


def checkpoint_node(state: WorkflowState) -> dict:
    """Persist current state to disk and advance to the next step.

    If validation passed (iteration == 0) or retries are exhausted,
    advance ``current_step`` by 1 and reset ``iteration``.
    When all steps are done, set ``completed`` to ``True``.
    """
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    iteration = state.get("iteration", 0)

    from app.nodes.validator import MAX_STEP_RETRIES

    advance = iteration == 0 or iteration >= MAX_STEP_RETRIES
    updates: dict = {}

    if advance:
        next_step = current_step + 1
        updates["current_step"] = next_step
        updates["iteration"] = 0
        if next_step >= len(plan):
            updates["completed"] = True
    else:
        updates["iteration"] = iteration

    # Save full state snapshot for recovery
    snapshot = {**state, **updates}
    path = Path(CHECKPOINT_PATH).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")

    return updates
