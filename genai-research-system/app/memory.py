"""Shared memory for the multi-agent research workflow."""

from dataclasses import dataclass, field


@dataclass
class ResearchMemory:
	original_query: str
	plan: list[str] = field(default_factory=list)
	findings: dict[str, str] = field(default_factory=dict)
	critiques: dict[str, str] = field(default_factory=dict)

	def add_plan(self, tasks: list[str]) -> None:
		self.plan = list(tasks)

	def add_finding(self, task: str, result: str) -> None:
		self.findings[task] = result

	def add_critique(self, task: str, critique: str) -> None:
		self.critiques[task] = critique

	def get_context(self) -> dict[str, object]:
		return {
			"original_query": self.original_query,
			"plan": list(self.plan),
			"findings": dict(self.findings),
			"critiques": dict(self.critiques),
		}
