from __future__ import annotations

import importlib.util
from pathlib import Path


QA_MODEL = "gemini-3.1-pro-preview"


def _load_symbol(module_name: str, symbol_name: str):
	try:
		module = __import__(f"{__package__}.{module_name}", fromlist=[symbol_name])
		return getattr(module, symbol_name)
	except (ImportError, AttributeError, TypeError):
		module_path = Path(__file__).resolve().parents[2] / "shared" / "llm" / f"{module_name}.py"
		spec = importlib.util.spec_from_file_location(
			f"shared_llm_{module_name}",
			module_path,
		)
		if spec is None or spec.loader is None:
			raise RuntimeError(f"Unable to load module '{module_name}'.")

		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return getattr(module, symbol_name)


generate_text = _load_symbol("gemini", "generate_text")


def _build_qa_prompt(query: str, context: str) -> str:
	return f"""
You are a codebase question-answering assistant.

Answer the developer's question using only the supplied code context.

Developer question:
{query}

Code context:
{context}

Rules:
- Stay grounded in the provided code context.
- Do not invent functions, files, behavior, or architecture that are not shown.
- If the context is insufficient, say so clearly.
- Give a clear explanation in plain language.
- Reference file paths when they are relevant to the answer.
- Prefer precise statements over broad guesses.
""".strip()


def answer_question(query: str, context: str) -> str:
	query_text = query.strip()
	if not query_text:
		raise ValueError("Query must not be empty.")

	context_text = context.strip()
	if not context_text:
		return "I could not answer the question because no relevant code context was provided."

	return generate_text(
		prompt=_build_qa_prompt(query=query_text, context=context_text),
		model=QA_MODEL,
	)


__all__ = ["QA_MODEL", "answer_question"]
