# Tasks

## Document Ingestion

- Create a file loader in `app/ingest.py` that reads `.pdf`, `.txt`, and `.md` files from a given directory.
- Add a PDF text extraction method using a lightweight parser.
- Normalize loaded content into a common dict format with keys: `text`, `filename`, `source_path`, `file_type`.
- Attach a timestamp and page count to each ingested document record.
- Skip empty files, binary files, and unsupported extensions with a logged warning.
- Return a list of document dicts ready for downstream processing.

## Chunking Strategy

- Implement `chunk_document()` in `app/chunker.py` that splits a document's text into segments.
- Make chunk size and overlap configurable via function parameters.
- Use paragraph boundaries as preferred split points before falling back to sentence or character splits.
- Preserve page number or section heading in chunk metadata when available.
- Attach source metadata to each chunk dict: `filename`, `chunk_index`, `start_char`, `end_char`.
- Handle edge cases: documents shorter than chunk size, empty text, single-line documents.
- Return a list of chunk dicts ready for embedding.

## Embedding Generation

- Implement `embed_chunks()` in `app/embedder.py` that converts a list of chunk texts into vectors.
- Wrap the Gemini embedding API call behind a clean interface.
- Support batched embedding to minimize per-chunk API calls.
- Normalize empty or whitespace-only chunks before embedding.
- Add retry handling for transient API failures.
- Return a list of dicts with keys: `text`, `embedding`, `metadata`.

## Vector Store

- Implement `VectorStore` class in `app/vector_store.py` with `add()` and `search()` methods.
- Store embeddings, chunk text, and metadata together in a single record.
- Implement cosine similarity search returning top-k results with scores.
- Add `save()` and `load()` methods for persisting the store to disk as JSON.
- Support metadata filtering by filename and file type during search.
- Handle the empty-store case gracefully in search.

## Retrieval Logic

- Implement `retrieve()` in `app/retriever.py` that takes a query string and returns relevant chunks.
- Embed the query using the same embedder interface.
- Call the vector store's search method and return ranked results.
- Accept a configurable `top_k` parameter with a sensible default.
- Add a score threshold to filter out low-relevance results.
- Return a list of result dicts with keys: `text`, `score`, `metadata`.

## QA Engine with Grounding

- Implement `answer_question()` in `app/qa_engine.py` that takes a question and retrieved context.
- Build a prompt that includes retrieved chunks as grounding evidence.
- Route reasoning requests to `gemini-3.1-pro-preview`.
- Instruct the model to answer strictly from provided context and flag when evidence is insufficient.
- Return a structured response with the answer text and a list of source references used.
- Add a fallback response when retrieval returns no relevant chunks.

## Citation System

- Implement `attach_citations()` in `app/citation.py` that maps answer sentences to source chunks.
- Accept the generated answer and the list of retrieved chunks as input.
- Use text overlap or embedding similarity to link each claim to its supporting chunk.
- Return a list of citation objects with keys: `claim`, `source_filename`, `chunk_index`, `relevance_score`.
- Handle cases where a claim has no matching source by marking it as unsupported.

## Structured Extraction

- Implement `extract_fields()` in `app/extractor.py` that pulls structured data from document text.
- Accept a document or chunk text and a list of target field names as input.
- Build a prompt instructing the LLM to extract values for the requested fields.
- Use `gemini-3-flash-preview` for extraction calls.
- Return a dict mapping each field name to its extracted value or `null` if not found.
- Handle multi-value fields by returning a list of values.

