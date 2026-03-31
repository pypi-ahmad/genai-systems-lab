# Tasks

## 1. File Scanning System

- Define the root input format for a local codebase path.
- Add a file scanning module in `app/indexer.py`.
- Define supported source file extensions for the first version.
- Add directory walking logic that recursively discovers files.
- Add ignore rules for common directories such as `.git`, `node_modules`, `dist`, `build`, and `__pycache__`.
- Add file size checks to skip unusually large files.
- Return a normalized list of candidate files for parsing.
- Add a small test that verifies ignored paths are excluded.

## 2. Code Parsing

- Add a parser interface in `app/file_parser.py`.
- Define a normalized parsed-file structure with file path, language, symbols, and line ranges.
- Implement language detection from file extension.
- Add a Python parser that extracts functions, classes, and methods.
- Add a fallback parser that treats unsupported files as plain text.
- Preserve repository-relative file paths in parser output.
- Preserve function and method names in parser output metadata.
- Add tests for parsing a simple file with multiple functions.

## 3. Chunking Logic

- Add a chunking module in `app/context_builder.py` or a dedicated helper within `app/indexer.py`.
- Define a chunk data structure with content and metadata.
- Create symbol-based chunks for parsed functions, methods, and classes.
- Add a fallback line-window chunking strategy for files without symbols.
- Add configurable chunk size and overlap settings.
- Record `start_line` and `end_line` for every chunk.
- Attach `file_path`, `symbol_name`, and `symbol_type` to each chunk.
- Add tests that verify chunk boundaries and metadata preservation.

## 4. Embedding Generation

- Add an embedding generator interface in `app/embedder.py`.
- Define the input text format used for each chunk embedding.
- Add a method that batches chunk embedding requests.
- Normalize empty or whitespace-only chunks before embedding.
- Add retry handling for transient embedding failures.
- Return embeddings together with the original chunk metadata.
- Add a test that validates embedding input preparation without calling the real model.

## 5. Vector Storage

- Add a vector store interface in `app/retriever.py` or a small storage helper.
- Define the record schema for vector plus metadata storage.
- Implement an in-memory vector store for the first version.
- Add methods to insert or upsert chunk vectors.
- Add a method to query top-k nearest neighbors.
- Add metadata filtering by file path and language.
- Ensure stored records preserve `file_path` and `symbol_name`.
- Add tests for insert, update, and similarity lookup behavior.

## 6. Retrieval Logic

- Add a retriever interface in `app/retriever.py`.
- Convert the developer question into an embedding query.
- Query the vector store for the top-k candidate chunks.
- Add a simple reranking step that boosts exact symbol-name matches.
- Add a deduplication step for near-identical chunks.
- Return retrieval results with scores and metadata.
- Add tests for retrieval ranking and symbol-name prioritization.

## 7. Context Construction

- Add a context builder interface in `app/context_builder.py`.
- Group retrieved chunks by file path and symbol name.
- Remove redundant overlapping snippets.
- Format each snippet with file path, symbol name, and line range.
- Add a token or character budget for the final context window.
- Truncate low-priority snippets when the budget is exceeded.
- Return a structured prompt-ready context payload.
- Add tests for grouping, ordering, and truncation behavior.

## 8. QA Agent

- Add a QA agent interface in `app/qa_agent.py`.
- Define the QA prompt format using the developer question and constructed context.
- Route complex reasoning requests to `gemini-3.1-pro-preview`.
- Add an optional fast path for simple responses with `gemini-3-flash-preview`.
- Require the answer formatter to include file paths and function names when relevant.
- Add a fallback response when retrieval returns insufficient evidence.
- Add tests for prompt construction and response formatting.

