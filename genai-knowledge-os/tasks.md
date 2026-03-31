# Tasks

## Document Ingestion

- Create a file loader in `app/ingest.py` that reads `.txt` and `.md` files from a given directory.
- Normalize loaded content into a common dict format with keys: `text`, `filename`, `source_path`.
- Add a timestamp to each ingested document record.
- Return a list of document dicts ready for downstream processing.
- Add basic validation to skip empty files and unsupported extensions.

## Chunking System

- Implement `chunk_document()` in `app/chunker.py` that splits a document's text into segments.
- Make chunk size and overlap configurable via function parameters.
- Attach source metadata (filename, chunk index) to each chunk dict.
- Handle edge cases: documents shorter than chunk size, empty text.
- Return a list of chunk dicts with keys: `text`, `filename`, `chunk_index`, `start_char`, `end_char`.

## Embedding Generation

- Implement `embed_chunks()` in `app/embedder.py` that converts a list of chunk texts into vectors.
- Wrap the embedding API call behind a clean interface.
- Support batched embedding to avoid per-chunk API calls.
- Return a list of dicts with keys: `text`, `embedding`, `metadata`.
- Add error handling for failed API calls with retry logic.

## Vector Store Implementation

- Implement `VectorStore` class in `app/vector_store.py` with `add()` and `search()` methods.
- Store embeddings, chunk text, and metadata together.
- Implement cosine similarity search returning top-k results with scores.
- Add `save()` and `load()` methods for persisting the store to disk as JSON.
- Handle the empty-store case gracefully in search.

## Retrieval Logic

- Implement `retrieve()` in `app/retriever.py` that takes a query string and returns relevant chunks.
- Embed the query using the same embedder interface.
- Call the vector store's search method and return ranked results.
- Accept a configurable `top_k` parameter.
- Return a list of result dicts with keys: `text`, `score`, `metadata`.

## Memory Storage

- Implement `MemoryStore` class in `app/memory.py` with `add()`, `list()`, and `search()` methods.
- Store each memory entry as a dict with keys: `content`, `source`, `timestamp`.
- Persist memory entries to a JSON file on disk.
- Load existing memories from disk on initialization.
- Add a `search()` method that finds memories relevant to a query using keyword or embedding match.

## Summarization

- Implement `summarize_text()` in `app/summarizer.py` that summarizes a single block of text using an LLM.
- Implement `summarize_chunks()` that combines and summarizes a list of retrieved chunks.
- Use `gemini-3-flash-preview` for all summarization calls.
- Return a plain-text summary string.
- Handle long inputs by truncating or splitting before sending to the LLM.

## Insight Generation

- Implement `generate_insights()` in `app/insight_engine.py` that takes a topic or question.
- Retrieve relevant chunks from the vector store and relevant entries from memory.
- Combine retrieved context and send to `gemini-3.1-pro-preview` with a prompt for cross-document reasoning.
- Return a structured response with identified themes, connections, and contradictions.
- Handle cases where insufficient context is available by returning a clear message.

