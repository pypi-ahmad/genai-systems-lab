"""Tests for the Startup Team Simulator."""

import json
import sys
import types

# --- Fake CrewAI stubs ---------------------------------------------------

class FakeAgent:
    def __init__(self, **kwargs):
        self.role = kwargs.get("role", "")
        self.goal = kwargs.get("goal", "")
        self.backstory = kwargs.get("backstory", "")
        self.llm = kwargs.get("llm", "")
        self.verbose = kwargs.get("verbose", False)


class FakeTask:
    def __init__(self, **kwargs):
        self.description = kwargs.get("description", "")
        self.expected_output = kwargs.get("expected_output", "")
        self.agent = kwargs.get("agent", None)
        self.context = kwargs.get("context", [])


class FakeProcess:
    sequential = "sequential"


class FakeTaskOutput:
    def __init__(self, raw: str):
        self.raw = raw


class FakeResult:
    def __init__(self, task_count: int):
        self.tasks_output = [
            FakeTaskOutput(json.dumps({"step": i})) for i in range(task_count)
        ]


class FakeCrew:
    def __init__(self, **kwargs):
        self.agents = kwargs.get("agents", [])
        self.tasks = kwargs.get("tasks", [])
        self.process = kwargs.get("process", None)
        self.verbose = kwargs.get("verbose", False)

    def kickoff(self, inputs=None):
        return FakeResult(len(self.tasks))


# Inject fake crewai module before importing app code
_fake_crewai = types.ModuleType("crewai")
_fake_crewai.Agent = FakeAgent
_fake_crewai.Task = FakeTask
_fake_crewai.Crew = FakeCrew
_fake_crewai.Process = FakeProcess
sys.modules["crewai"] = _fake_crewai

from app.agents import (
    REASONING_MODEL,
    SUMMARY_MODEL,
    build_ceo,
    build_cto,
    build_engineer,
    build_product_manager,
)
from app.tasks import (
    PROPOSAL_SCHEMA,
    SELECTION_SCHEMA,
    PRODUCT_SCHEMA,
    ARCHITECTURE_SCHEMA,
    EXECUTION_SCHEMA,
    REVIEW_SCHEMA,
    build_architecture_task,
    build_execution_task,
    build_product_task,
    build_proposal_task,
    build_review_task,
    build_selection_task,
    build_vision_task,
)
from app.crew import build_crew
from app.main import STEP_LABELS, _parse_json, run


# ---- Agent tests ---------------------------------------------------------

def test_build_ceo():
    agent = build_ceo()
    assert agent.role == "Chief Executive Officer"
    assert agent.llm == REASONING_MODEL
    assert "JSON" in agent.goal


def test_build_product_manager():
    agent = build_product_manager()
    assert agent.role == "Head of Product"
    assert agent.llm == REASONING_MODEL


def test_build_cto():
    agent = build_cto()
    assert agent.role == "Chief Technology Officer"
    assert agent.llm == REASONING_MODEL


def test_build_engineer():
    agent = build_engineer()
    assert agent.role == "Lead Engineer"
    assert agent.llm == SUMMARY_MODEL


# ---- Schema tests --------------------------------------------------------

def test_proposal_schema_keys():
    expected = {"angle", "target_market", "differentiator", "monetization", "risks", "rationale"}
    assert set(PROPOSAL_SCHEMA.keys()) == expected


def test_selection_schema_keys():
    expected = {
        "selected_proposal", "reasoning", "mission", "target_market",
        "value_proposition", "competitive_advantages", "success_metrics",
        "go_to_market",
    }
    assert set(SELECTION_SCHEMA.keys()) == expected


def test_product_schema_keys():
    assert "personas" in PRODUCT_SCHEMA
    assert "mvp_features" in PRODUCT_SCHEMA


def test_review_schema_keys():
    expected = {"strengths", "weaknesses", "gaps", "recommendations"}
    assert set(REVIEW_SCHEMA.keys()) == expected


# ---- Task builder tests --------------------------------------------------

def test_build_proposal_task():
    agent = build_cto()
    task = build_proposal_task(agent, "AI healthcare", "CTO")
    assert "CTO" in task.description
    assert "AI healthcare" in task.description
    assert task.agent is agent
    assert task.context == []  # proposals have no context


def test_build_proposal_task_embeds_schema():
    agent = build_product_manager()
    task = build_proposal_task(agent, "test idea", "Product Manager")
    assert "angle" in task.description
    assert "differentiator" in task.description


def test_build_selection_task():
    a1, a2, a3 = build_product_manager(), build_cto(), build_engineer()
    p1 = build_proposal_task(a1, "idea", "PM")
    p2 = build_proposal_task(a2, "idea", "CTO")
    p3 = build_proposal_task(a3, "idea", "Engineer")
    ceo = build_ceo()
    task = build_selection_task(ceo, [p1, p2, p3])
    assert task.agent is ceo
    assert len(task.context) == 3
    assert task.context == [p1, p2, p3]
    assert "selected_proposal" in task.description


def test_build_vision_task():
    agent = build_ceo()
    task = build_vision_task(agent, "test idea")
    assert "test idea" in task.description
    assert task.agent is agent


def test_build_product_task_has_context():
    ceo = build_ceo()
    pm = build_product_manager()
    vision = build_vision_task(ceo, "idea")
    product = build_product_task(pm, vision)
    assert product.context == [vision]


def test_build_architecture_task_has_context():
    pm = build_product_manager()
    cto = build_cto()
    dummy_vision = build_vision_task(build_ceo(), "idea")
    product = build_product_task(pm, dummy_vision)
    arch = build_architecture_task(cto, product)
    assert arch.context == [product]


def test_build_execution_task_has_context():
    cto = build_cto()
    eng = build_engineer()
    dummy_product = build_product_task(build_product_manager(), build_vision_task(build_ceo(), "x"))
    arch = build_architecture_task(cto, dummy_product)
    exec_task = build_execution_task(eng, arch)
    assert exec_task.context == [arch]


def test_build_review_task():
    reviewer = build_cto()
    target = build_vision_task(build_ceo(), "idea")
    review = build_review_task(reviewer, target, "CEO")
    assert review.agent is reviewer
    assert review.context == [target]
    assert "CEO" in review.description
    assert "strengths" in review.description


# ---- Crew tests ----------------------------------------------------------

def test_build_crew_returns_crew():
    crew = build_crew("test idea", verbose=False)
    assert isinstance(crew, FakeCrew)


def test_build_crew_has_four_agents():
    crew = build_crew("test idea", verbose=False)
    assert len(crew.agents) == 4


def test_build_crew_has_eleven_tasks():
    crew = build_crew("test idea", verbose=False)
    assert len(crew.tasks) == 11


def test_build_crew_task_order():
    crew = build_crew("test idea", verbose=False)
    tasks = crew.tasks
    # First 3: proposals (no context)
    for t in tasks[0:3]:
        assert t.context == []
    # Task 3: selection — context is the 3 proposals
    assert tasks[3].context == [tasks[0], tasks[1], tasks[2]]
    # Task 4: product — context is the selection
    assert tasks[4].context == [tasks[3]]
    # Task 5: architecture — context is product
    assert tasks[5].context == [tasks[4]]
    # Task 6: execution — context is architecture
    assert tasks[6].context == [tasks[5]]
    # Tasks 7-10: reviews — each has context of one task
    assert tasks[7].context == [tasks[3]]   # PM reviews CEO selection
    assert tasks[8].context == [tasks[4]]   # CTO reviews PM product
    assert tasks[9].context == [tasks[5]]   # Eng reviews CTO arch
    assert tasks[10].context == [tasks[6]]  # CEO reviews Eng exec


def test_build_crew_sequential_process():
    crew = build_crew("test idea", verbose=False)
    assert crew.process == FakeProcess.sequential


def test_build_crew_proposal_agents():
    crew = build_crew("test idea", verbose=False)
    roles = [t.agent.role for t in crew.tasks[:3]]
    assert "Head of Product" in roles
    assert "Chief Technology Officer" in roles
    assert "Lead Engineer" in roles


def test_build_crew_selection_agent_is_ceo():
    crew = build_crew("test idea", verbose=False)
    assert crew.tasks[3].agent.role == "Chief Executive Officer"


# ---- Run output tests ----------------------------------------------------

def test_step_labels_count():
    assert len(STEP_LABELS) == 11


def test_step_labels_has_proposals():
    assert "Proposal: Product Manager" in STEP_LABELS
    assert "Proposal: CTO" in STEP_LABELS
    assert "Proposal: Lead Engineer" in STEP_LABELS


def test_step_labels_has_selection():
    assert "CEO Selection" in STEP_LABELS


def test_step_labels_order():
    assert STEP_LABELS[0] == "Proposal: Product Manager"
    assert STEP_LABELS[3] == "CEO Selection"
    assert STEP_LABELS[4] == "Product Specification"
    assert STEP_LABELS[7] == "Review: CEO Selection"


def test_parse_json_valid():
    raw = '{"a": 1}'
    assert _parse_json(raw) == {"a": 1}


def test_parse_json_markdown_fences():
    raw = '```json\n{"a": 1}\n```'
    assert _parse_json(raw) == {"a": 1}


def test_parse_json_invalid():
    assert _parse_json("not json") is None


def test_run_returns_structured_steps():
    result = run("test idea", api_key="test-key")
    assert result["idea"] == "test idea"
    for label in STEP_LABELS:
        assert label in result["steps"]
