# Architecture

## Overview

Codebase Copilot is a retrieval-augmented question answering system for local source repositories. It indexes files from a local codebase, splits them into semantically useful chunks, generates embeddings, stores vectors with searchable metadata, and retrieves the most relevant code snippets to answer developer questions.

The architecture is designed to stay practical and production-oriented:

- keep indexing deterministic and repeatable
- preserve source traceability through metadata
- separate ingestion, retrieval, and answer generation responsibilities
- support incremental upgrades from in-memory storage to a simple persistent database

Primary flow:

`Local Codebase -> Parse -> Chunk -> Embed -> Store -> Retrieve -> Build Context -> Answer`

## Core Features

### Local Codebase Indexing

The system scans a user-specified local repository, filters supported source files, parses them with language-aware logic, and prepares them for chunking and embedding.

### Intelligent Chunking

Files should not be split with naive fixed-width windows alone. The chunking system should prefer logical code boundaries such as:

- functions
- methods
- classes
- imports and module-level declarations
- documentation blocks associated with code

When a file cannot be parsed structurally, the system should fall back to a conservative line-based chunking strategy with overlap.

### Embedding Generation

Each chunk is converted into a vector embedding that represents the code and nearby descriptive context. Embeddings should be generated consistently so retrieval quality stays stable across indexing runs.

### Vector Storage With Metadata

Each embedded chunk is stored together with metadata needed for filtering, traceability, and answer grounding. This metadata is not optional. It is part of the retrieval contract.

### Relevant Snippet Retrieval

When a developer asks a question, the retriever converts the query into an embedding, searches the vector store, and returns the most relevant chunks ranked by semantic similarity and optional metadata filters.

### Developer Question Answering

The QA layer builds grounded context from retrieved chunks and uses an LLM to answer questions about the codebase. Answers should cite the underlying files and function names from retrieved metadata rather than producing generic explanations.

## Required Metadata Contract

The system must preserve file paths and function names in metadata for every stored chunk whenever that information can be determined.

Minimum metadata fields:

- `file_path`: repository-relative or canonical local path to the source file
- `language`: detected programming language
- `chunk_id`: stable identifier for the chunk
- `start_line`: first line number represented by the chunk
- `end_line`: last line number represented by the chunk
- `symbol_name`: function, method, class, or module symbol if available
- `symbol_type`: function, method, class, module, or unknown
- `imports`: optional imported modules or packages relevant to the chunk
- `doc_summary`: optional short extracted summary from nearby comments or docstrings
- `content_hash`: checksum used for deduplication and incremental re-indexing

Design rule:

- `file_path` must always be present
- `symbol_name` must be populated for function or method chunks when parsing succeeds
- retrieval results and final answers should surface `file_path` and `symbol_name` directly so developers can locate the source quickly

## Component Architecture

### File Parser

The file parser is responsible for language-aware ingestion of source files.

Responsibilities:

- detect supported languages from file extension and optional content heuristics
- extract structural units such as functions, classes, methods, comments, and docstrings
- normalize parsed output into a common internal representation for downstream chunking
- preserve line numbers and symbol boundaries

Production notes:

- use best-effort parsing and degrade gracefully on malformed files
- skip generated artifacts, binaries, vendored dependencies, and large irrelevant files
- emit parse diagnostics for observability

### Chunking System

The chunking system converts parsed file structures into retrieval-friendly units.

Responsibilities:

- create chunks at logical code boundaries when possible
- merge very small fragments with nearby context to avoid low-signal vectors
- apply overlap where necessary so symbol definitions do not lose critical context
- attach stable metadata including file path and symbol information

Production notes:

- favor chunks that can stand on their own during retrieval
- maintain predictable chunk size limits to control embedding cost and retrieval latency
- keep chunking rules configurable by language

### Embedding Generator

The embedding generator converts each chunk into a vector representation.

Responsibilities:

- normalize input text before embedding
- batch chunk embedding requests for efficiency
- maintain a consistent embedding format and model configuration
- expose deterministic retry and failure handling

Production notes:

- embedding requests should be idempotent for repeated indexing runs
- failed chunks should be retried with bounded limits and logged with enough detail for repair

### Vector Store

The vector store holds embeddings and metadata for retrieval.

Supported deployment shape:

- in-memory store for local development and tests
- simple persistent store for production or repeated local use, such as SQLite plus a vector extension or a small dedicated vector database

Responsibilities:

- store vectors alongside the full metadata contract
- support nearest-neighbor lookup by query embedding
- support metadata filters such as language or file path prefix
- support upsert and delete operations for incremental re-indexing

Production notes:

- the storage layer should treat metadata as first-class searchable data, not just blob payload
- incremental indexing should update only changed chunks using `content_hash`

### Retriever

The retriever is the main search layer used at question time.

Responsibilities:

- embed the developer query
- run top-k vector search
- optionally combine semantic similarity with exact metadata filters or symbol matches
- rerank results when necessary to prioritize precise symbol-level hits

Production notes:

- retrieving only semantically similar chunks is often insufficient for code questions
- exact symbol matches and file path priors should be incorporated when available

### Context Builder

The context builder prepares retrieved chunks for the QA model.

Responsibilities:

- deduplicate overlapping chunks
- group related chunks by file and symbol
- order snippets to preserve code readability
- format context so the QA model sees file path, symbol name, line range, and snippet content together

Production notes:

- context must remain compact enough for efficient prompting
- low-value or redundant chunks should be removed before model invocation
- the builder should prefer fewer, higher-quality snippets over large noisy context windows

### QA Agent

The QA agent turns grounded context into a developer-facing answer.

Responsibilities:

- interpret the developer’s question
- reason over retrieved code and metadata
- produce an answer that is anchored to actual code snippets
- include file paths and function names in the response when relevant

Production notes:

- the QA agent should avoid answering beyond retrieved evidence unless the response clearly states uncertainty
- prompts should instruct the model to stay grounded in retrieved code and metadata

## End-to-End Flows

### Indexing Flow

1. Accept a local repository path.
2. Enumerate candidate files and exclude unsupported or ignored paths.
3. Parse files with the language-aware parser.
4. Convert parsed structures into chunks.
5. Generate embeddings for each chunk.
6. Store vectors and metadata in the vector store.
7. Record indexing statistics, failures, and content hashes for incremental refresh.

### Question Answering Flow

1. Accept a developer question.
2. Convert the question into an embedding.
3. Retrieve top candidate chunks from the vector store.
4. Rerank or filter using metadata such as symbol names and file paths.
5. Build compact, traceable context for the QA model.
6. Generate a grounded answer.
7. Return the answer together with supporting file paths and function names.

## Model Usage

### `gemini-3.1-pro-preview`

Use for reasoning-heavy code understanding and answer generation.

Recommended responsibilities:

- answering complex developer questions
- comparing multiple retrieved snippets
- explaining control flow, dependencies, and architectural intent
- resolving ambiguous code references using surrounding context

### `gemini-3-flash-preview`

Use for lightweight or latency-sensitive responses when deeper reasoning is not required.

Recommended responsibilities:

- simple follow-up responses
- brief snippet summaries
- low-complexity reformulations of already grounded answers

Practical routing rule:

- default to `gemini-3.1-pro-preview` for code reasoning over retrieved snippets
- use `gemini-3-flash-preview` only when the request is simple and the retrieved evidence is already clear

## Production-Oriented Design Notes

### Incremental Indexing

Re-indexing the entire repository every time is wasteful. The system should detect added, changed, and deleted files and update only affected chunks.

### Observability

Each stage should emit structured logs and metrics for:

- files scanned
- files skipped
- parse failures
- chunk counts
- embedding latency
- store upserts
- retrieval latency
- answer generation latency

### Failure Isolation

Bad files, parser errors, and transient embedding failures should not stop the full indexing job. The pipeline should continue, report partial failures, and support later repair.

### Grounded Responses

The answering layer should always preserve traceability back to source. Production answers should be explainable in terms of retrieved chunks, with direct references to file paths and symbol names.

### Storage Evolution

The architecture should allow a simple progression:

1. start with in-memory vectors for local development
2. move to a lightweight persistent store for repeated use
3. keep the retriever and metadata contract unchanged so storage can be swapped without redesigning the full system

## High-Level Summary

Codebase Copilot is built as a clean retrieval pipeline: parse code intelligently, chunk it around real code structure, embed and store it with strong metadata, retrieve the most relevant snippets, and answer developer questions with grounded reasoning. The critical architectural requirement is preserving `file_path` and `symbol_name` metadata across the full pipeline so every answer stays actionable for engineers working in the codebase.
