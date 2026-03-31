from __future__ import annotations

import importlib.util
from pathlib import Path

from shared.api.step_events import emit_step
from shared.config import set_byok_api_key, reset_byok_api_key


def _load_symbol(module_name: str, symbol_name: str):
	try:
		module = __import__(f"{__package__}.{module_name}", fromlist=[symbol_name])
		return getattr(module, symbol_name)
	except (ImportError, AttributeError, TypeError):
		module_path = Path(__file__).with_name(f"{module_name}.py")
		spec = importlib.util.spec_from_file_location(
			f"codebase_copilot_{module_name}",
			module_path,
		)
		if spec is None or spec.loader is None:
			raise RuntimeError(f"Unable to load module '{module_name}'.")

		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return getattr(module, symbol_name)


index_codebase = _load_symbol("indexer", "index_codebase")
retrieve = _load_symbol("retriever", "retrieve")
build_context = _load_symbol("context_builder", "build_context")
answer_question = _load_symbol("qa_agent", "answer_question")


def run(input: str, api_key: str) -> dict:
	"""Run codebase Q&A and return structured output.

	Input format: ``<codebase_path>\n<question>``
	If no newline is found, the entire input is treated as the question
	and the current directory is used as the codebase path.
	"""
	token = set_byok_api_key(api_key)
	try:
		if "\n" in input:
			codebase_path, question = input.split("\n", 1)
		else:
			codebase_path, question = ".", input

		codebase_path = codebase_path.strip()
		question = question.strip()
		if not question:
			return {"error": "A question is required."}

		emit_step("indexer", "running")
		index_codebase(codebase_path)
		emit_step("indexer", "done")

		emit_step("retriever", "running")
		retrieved_chunks = retrieve(question)
		emit_step("retriever", "done")

		emit_step("store", "running")
		context = build_context(retrieved_chunks)
		emit_step("store", "done")

		emit_step("generator", "running")
		answer = answer_question(question, context)
		emit_step("generator", "done")

		referenced_files = list(dict.fromkeys(c["path"] for c in retrieved_chunks))
		return {"answer": answer, "referenced_files": referenced_files}
	finally:
		reset_byok_api_key(token)
