from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TypedDict


DEFAULT_TOP_K = 5


class RetrievedChunk(TypedDict):
	text: str
	path: str


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


generate_embedding = _load_symbol("embedder", "generate_embedding")
search = _load_symbol("indexer", "search")


def retrieve(query: str) -> list[RetrievedChunk]:
	query_text = query.strip()
	if not query_text:
		raise ValueError("Query must not be empty.")

	query_embedding = generate_embedding(query_text)
	results = search(query_embedding, top_k=DEFAULT_TOP_K)

	return [
		{
			"text": result["text"],
			"path": result["metadata"]["path"],
		}
		for result in results
	]


__all__ = ["DEFAULT_TOP_K", "RetrievedChunk", "retrieve"]
