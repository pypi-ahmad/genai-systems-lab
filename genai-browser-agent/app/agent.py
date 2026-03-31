from __future__ import annotations

import logging

from app.actions import STOP, execute
from app.browser import BrowserController
from app.memory import BrowserMemory
from app.perception import get_observation
from app.planner import decide_next_action
from shared.api.step_events import emit_step

logger = logging.getLogger(__name__)

MAX_STEPS = 15


def run_agent(goal: str) -> dict:
    browser = BrowserController(headless=True)
    memory = BrowserMemory(goal=goal)

    try:
        for step in range(1, MAX_STEPS + 1):
            emit_step("perception", "running")
            observation = get_observation(browser)
            emit_step("perception", "done")
            logger.info("Step %d | Observation: %s", step, observation[:120])

            emit_step("planner", "running")
            action = decide_next_action(
                goal=goal,
                observation=observation,
                history=memory.get_history(),
            )
            emit_step("planner", "done")
            logger.info("Step %d | Action: %s %s", step, action["action"], action.get("args", {}))

            if action["action"] == STOP:
                emit_step("memory", "running")
                memory.add_step(action, {"success": True, "message": "Agent stopped."})
                emit_step("memory", "done")
                logger.info("Step %d | Agent decided to stop.", step)
                break

            emit_step("executor", "running")
            result = execute(action, browser)
            emit_step("executor", "done")

            emit_step("memory", "running")
            memory.add_step(action, result)
            emit_step("memory", "done")
            logger.info("Step %d | Result: %s", step, result["message"])

            if not result["success"]:
                logger.warning("Step %d | Action failed: %s", step, result["message"])
        else:
            logger.warning("Max steps (%d) reached without completion.", MAX_STEPS)
    finally:
        browser.close()

    return {
        "goal": goal,
        "steps": memory.step_count(),
        "history": memory.get_history(),
    }