"""End-to-end orchestration for the multi-agent research workflow."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

from .critic import critique
from .memory import ResearchMemory
from .planner import create_plan
from .researcher import research_task
from .writer import write_report


logger = logging.getLogger(__name__)
MAX_RETRIES_PER_TASK = 1


def run_research(query: str) -> str:
	return asyncio.run(run_research_async(query))


async def run_research_async(query: str) -> str:
	cleaned_query = query.strip()
	if not cleaned_query:
		raise ValueError("Query must not be empty.")

	logger.info("Starting research workflow")
	memory = ResearchMemory(original_query=cleaned_query)

	logger.info("Generating research plan")
	plan = await asyncio.to_thread(create_plan, cleaned_query)
	memory.add_plan(plan)

	logger.info("Running %s research tasks in parallel", len(plan))
	task_results = await asyncio.gather(
		*[_process_task(task, memory) for task in plan]
	)

	for task_result in task_results:
		memory.add_critique(task_result.task, task_result.critique)
		memory.add_finding(task_result.task, task_result.finding)
		logger.info("Stored final result for task: %s", task_result.task)

	logger.info("Generating final report")
	report = await asyncio.to_thread(write_report, cleaned_query, memory.findings)
	logger.info("Research workflow completed")
	return report


@dataclass
class TaskResult:
	task: str
	finding: str
	critique: str


async def _process_task(task: str, memory: ResearchMemory) -> TaskResult:
	logger.info("Researching task: %s", task)
	result = await asyncio.to_thread(research_task, task, _build_context(memory, task=task))

	logger.info("Reviewing task: %s", task)
	review = await asyncio.to_thread(critique, task, result)

	retries = 0
	if _needs_improvement(review) and retries < MAX_RETRIES_PER_TASK:
		retries += 1
		logger.info("Retrying task after critique (%s/%s): %s", retries, MAX_RETRIES_PER_TASK, task)
		result = await asyncio.to_thread(
			research_task,
			task,
			_build_context(memory, task=task, critique_text=review),
		)
	else:
		logger.info("No retry needed for task: %s", task)

	return TaskResult(task=task, finding=result, critique=review)


def _build_context(
	memory: ResearchMemory,
	task: str | None = None,
	critique_text: str | None = None,
) -> str:
	context = {
		"original_query": memory.original_query,
		"plan": memory.plan,
		"findings": memory.findings,
	}
	if task:
		context["current_task"] = task
	if critique_text:
		context["critique"] = critique_text
	return json.dumps(context, indent=2)


def _needs_improvement(review: str) -> bool:
	normalized_review = review.lower()
	improvement_signals = (
		"improve",
		"improvement",
		"missing",
		"incomplete",
		"incorrect",
		"gap",
		"lacks",
		"should add",
		"should include",
		"needs",
		"revise",
	)
	return any(signal in normalized_review for signal in improvement_signals)
