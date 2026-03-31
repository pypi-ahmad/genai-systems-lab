from __future__ import annotations


class BrowserMemory:
    def __init__(self, goal: str) -> None:
        self.goal = goal
        self._steps: list[dict] = []

    def add_step(self, action: dict, result: dict) -> None:
        self._steps.append({
            "step": len(self._steps) + 1,
            "action": action,
            "result": result,
        })

    def get_history(self) -> str:
        if not self._steps:
            return ""
        lines = []
        for s in self._steps:
            act = s["action"]
            res = s["result"]
            lines.append(
                f"Step {s['step']}: {act['action']} {act.get('args', {})} -> {res['message']}"
            )
        return "\n".join(lines)

    def step_count(self) -> int:
        return len(self._steps)