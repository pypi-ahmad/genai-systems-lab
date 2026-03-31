from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

for module_name in [name for name in sys.modules if name == "app" or name.startswith("app.")]:
    sys.modules.pop(module_name, None)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app import main as research_main
from app.nodes import critic, planner, researcher, writer


def test_run_executes_graph(monkeypatch):
    monkeypatch.setattr(planner, "generate_structured", lambda **_: {"steps": ["Map the topic", "Summarize tradeoffs"]})
    monkeypatch.setattr(
        researcher,
        "generate_structured",
        lambda **_: {"findings": [{"title": "Memory compression", "detail": "Reduces context growth."}]},
    )
    monkeypatch.setattr(critic, "generate_structured", lambda **_: {"assessment": "Coherent findings.", "gaps": ["Need benchmarks"]})
    monkeypatch.setattr(writer, "generate_text", lambda **_: "## Key Findings\nMemory compression reduces context growth.")

    result = research_main.run("Research agent memory systems", api_key="test-key")

    assert result["status"] == "completed"
    assert result["success"] is True
    assert result["plan"] == ["Map the topic", "Summarize tradeoffs"]
    assert result["findings"] == ["Memory compression: Reduces context growth."]
    assert "Need benchmarks" in result["critique"]
    assert result["report"].startswith("## Key Findings")


def test_run_requires_query():
    result = research_main.run("   ", api_key="test-key")
    assert result["status"] == "error"
    assert result["success"] is False


def test_run_returns_completed_status(monkeypatch):
    monkeypatch.setattr(
        research_main,
        "build_graph",
        lambda: type(
            "Graph",
            (),
            {"invoke": staticmethod(lambda state: {**state, "report": "done", "plan": ["a"], "findings": [], "critique": "ok"})},
        )(),
    )

    result = research_main.run("agent memory", api_key="test-key")

    assert result["status"] == "completed"
    assert result["report"] == "done"