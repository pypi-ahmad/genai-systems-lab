from __future__ import annotations

import ast
import builtins
import importlib.util
import re
from pathlib import Path
from typing import TypedDict

import numpy as np


FALLBACK_CHUNK_SIZE = 60
FALLBACK_CHUNK_OVERLAP = 10
CONTEXT_LINES = 2

SCRIPT_BLOCK_PATTERN = re.compile(
	r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+\w+|"
	r"^(?:export\s+)?class\s+\w+|"
	r"^(?:export\s+)?(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\([^\)]*\)\s*=>",
)


class CodeChunk(TypedDict):
	text: str
	path: str
	chunk_index: int


class DocumentMetadata(TypedDict):
	path: str
	chunk_index: int


class VectorDocument(TypedDict):
	text: str
	embedding: list[float]
	metadata: DocumentMetadata


class SearchResult(TypedDict):
	text: str
	metadata: DocumentMetadata
	score: float


if not hasattr(builtins, "_codebase_copilot_vector_store"):
	builtins._codebase_copilot_vector_store = []

VECTOR_STORE: list[VectorDocument] = builtins._codebase_copilot_vector_store


class ParsedFile(TypedDict):
	path: str
	content: str


def _load_local_symbol(module_name: str, symbol_name: str):
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


def _load_scan_directory():
	return _load_local_symbol("file_parser", "scan_directory")


def _load_generate_embeddings_batch():
	return _load_local_symbol("embedder", "generate_embeddings_batch")


def _make_chunk(text: str, file_path: str, chunk_index: int) -> CodeChunk:
	return {
		"text": text.strip(),
		"path": file_path,
		"chunk_index": chunk_index,
	}


def _slice_lines(lines: list[str], start_line: int, end_line: int) -> str:
	start_index = max(0, start_line - 1)
	end_index = min(len(lines), end_line)
	return "\n".join(lines[start_index:end_index]).strip()


def _expand_python_context_start(lines: list[str], start_line: int, max_lines: int) -> int:
	expanded_start = start_line
	remaining_lines = max_lines

	while expanded_start > 1 and remaining_lines > 0:
		previous_line = lines[expanded_start - 2].strip()
		if previous_line and not previous_line.startswith("#"):
			if not previous_line.startswith("import ") and not previous_line.startswith("from "):
				break

		expanded_start -= 1
		remaining_lines -= 1

	return expanded_start


def _python_node_start_line(node: ast.AST) -> int:
	decorator_lines = [
		decorator.lineno
		for decorator in getattr(node, "decorator_list", [])
		if hasattr(decorator, "lineno")
	]
	if decorator_lines:
		return min(decorator_lines)
	return getattr(node, "lineno", 1)


def _collect_python_chunk_nodes(module: ast.AST) -> list[tuple[ast.AST, int]]:
	collected_nodes: list[tuple[ast.AST, int]] = []

	class PythonChunkCollector(ast.NodeVisitor):
		def __init__(self) -> None:
			self.nesting_level = 0

		def visit_ClassDef(self, node: ast.ClassDef) -> None:
			collected_nodes.append((node, self.nesting_level))
			self.nesting_level += 1
			self.generic_visit(node)
			self.nesting_level -= 1

		def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
			collected_nodes.append((node, self.nesting_level))
			self.nesting_level += 1
			self.generic_visit(node)
			self.nesting_level -= 1

		def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
			collected_nodes.append((node, self.nesting_level))
			self.nesting_level += 1
			self.generic_visit(node)
			self.nesting_level -= 1

	collector = PythonChunkCollector()
	collector.visit(module)

	collected_nodes.sort(
		key=lambda item: (
			_python_node_start_line(item[0]),
			getattr(item[0], "end_lineno", getattr(item[0], "lineno", 1)),
		)
	)
	return collected_nodes


def _chunk_python(file_content: str, file_path: str) -> list[CodeChunk]:
	try:
		module = ast.parse(file_content)
	except SyntaxError:
		return []

	lines = file_content.splitlines()
	chunks: list[CodeChunk] = []

	for node, _nesting_level in _collect_python_chunk_nodes(module):
		start_line = _expand_python_context_start(
			lines,
			_python_node_start_line(node),
			CONTEXT_LINES,
		)
		end_line = getattr(node, "end_lineno", node.lineno)
		end_line = min(len(lines), end_line + CONTEXT_LINES)
		text = _slice_lines(lines, start_line, end_line)

		if text:
			chunks.append(_make_chunk(text, file_path, len(chunks)))

	return chunks


def _find_script_block_starts(lines: list[str]) -> list[int]:
	starts: list[int] = []

	for index, line in enumerate(lines, start=1):
		if SCRIPT_BLOCK_PATTERN.match(line.strip()):
			starts.append(index)

	return starts


def _chunk_script(file_content: str, file_path: str) -> list[CodeChunk]:
	lines = file_content.splitlines()
	starts = _find_script_block_starts(lines)

	if not starts:
		return []

	chunks: list[CodeChunk] = []

	for index, start_line in enumerate(starts):
		next_start = starts[index + 1] if index + 1 < len(starts) else len(lines) + 1
		block_start = max(1, start_line - CONTEXT_LINES)
		block_end = min(len(lines), next_start - 1 + CONTEXT_LINES)
		text = _slice_lines(lines, block_start, block_end)

		if text:
			chunks.append(_make_chunk(text, file_path, len(chunks)))

	return chunks


def _fallback_chunks(file_content: str, file_path: str) -> list[CodeChunk]:
	lines = file_content.splitlines()
	if not lines:
		return []

	chunks: list[CodeChunk] = []
	start = 0

	while start < len(lines):
		end = min(len(lines), start + FALLBACK_CHUNK_SIZE)
		text = "\n".join(lines[start:end]).strip()

		if text:
			chunks.append(_make_chunk(text, file_path, len(chunks)))

		if end >= len(lines):
			break

		start = max(end - FALLBACK_CHUNK_OVERLAP, start + 1)

	return chunks


def chunk_code(file_content: str, file_path: str = "") -> list[CodeChunk]:
	suffix = Path(file_path).suffix.lower()

	if suffix == ".py":
		chunks = _chunk_python(file_content, file_path)
		if chunks:
			return chunks

	if suffix in {".js", ".ts"}:
		chunks = _chunk_script(file_content, file_path)
		if chunks:
			return chunks

	return _fallback_chunks(file_content, file_path)


def chunk_files(files: list[ParsedFile]) -> list[CodeChunk]:
	chunks: list[CodeChunk] = []

	for parsed_file in files:
		chunks.extend(
			chunk_code(
				file_content=parsed_file["content"],
				file_path=parsed_file["path"],
			)
		)

	return chunks


def _build_document_metadata(chunk: CodeChunk) -> DocumentMetadata:
	return {
		"path": chunk["path"],
		"chunk_index": chunk["chunk_index"],
	}


def _cosine_similarity(query_vector: np.ndarray, document_vector: np.ndarray) -> float:
	query_norm = np.linalg.norm(query_vector)
	document_norm = np.linalg.norm(document_vector)

	if query_norm == 0.0 or document_norm == 0.0:
		return 0.0

	return float(np.dot(query_vector, document_vector) / (query_norm * document_norm))


def add_documents(chunks: list[dict]) -> None:
	for chunk in chunks:
		text = str(chunk.get("text", "")).strip()
		embedding = chunk.get("embedding")

		if not text:
			continue
		if not isinstance(embedding, list) or not embedding:
			raise ValueError("Each chunk must include a non-empty 'embedding' list.")

		path = str(chunk.get("path", ""))
		chunk_index = int(chunk.get("chunk_index", 0))

		VECTOR_STORE.append(
			{
				"text": text,
				"embedding": [float(value) for value in embedding],
				"metadata": {
					"path": path,
					"chunk_index": chunk_index,
				},
			}
		)


def index_codebase(path: str) -> list[VectorDocument]:
	scan_directory = _load_scan_directory()
	generate_embeddings_batch = _load_generate_embeddings_batch()

	files = scan_directory(path)
	chunks = chunk_files(files)
	texts = [chunk["text"] for chunk in chunks]

	VECTOR_STORE.clear()
	if not texts:
		return []

	embeddings = generate_embeddings_batch(texts)
	if len(embeddings) != len(chunks):
		raise RuntimeError("Embedding count did not match chunk count during indexing.")

	documents = [
		{
			"text": chunk["text"],
			"path": chunk["path"],
			"chunk_index": chunk["chunk_index"],
			"embedding": embedding,
		}
		for chunk, embedding in zip(chunks, embeddings, strict=False)
	]

	add_documents(documents)
	return list(VECTOR_STORE)


def search(query_embedding: list[float], top_k: int = 5) -> list[SearchResult]:
	if not query_embedding:
		raise ValueError("Query embedding must not be empty.")
	if top_k <= 0:
		return []
	if not VECTOR_STORE:
		return []

	query_vector = np.asarray(query_embedding, dtype=float)
	results: list[SearchResult] = []

	for document in VECTOR_STORE:
		document_vector = np.asarray(document["embedding"], dtype=float)
		score = _cosine_similarity(query_vector, document_vector)
		results.append(
			{
				"text": document["text"],
				"metadata": document["metadata"],
				"score": score,
			}
		)

	results.sort(key=lambda item: item["score"], reverse=True)
	return results[:top_k]


def index_directory(directory: str | Path) -> list[CodeChunk]:
	scan_directory = _load_scan_directory()
	return chunk_files(scan_directory(directory))


__all__ = [
	"CodeChunk",
	"DocumentMetadata",
	"SearchResult",
	"VectorDocument",
	"VECTOR_STORE",
	"add_documents",
	"chunk_code",
	"chunk_files",
	"index_codebase",
	"index_directory",
	"search",
]
