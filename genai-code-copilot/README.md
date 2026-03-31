# Codebase Copilot

## Overview

A repository-aware code assistant that indexes local source files, builds retrieval-friendly code chunks, finds relevant context by query, and generates grounded answers about the codebase. The project emphasizes traceability over generic code explanations.

## System Flow

A codebase is scanned and chunked into indexed documents, a developer question is embedded and matched against those chunks, and the retrieved evidence is assembled into prompt context for the answering model.

```text
Codebase Path -> Scanner -> Chunker -> Embedder -> Vector Store -> Retriever -> Context Builder -> QA Agent -> Answer
```

## Architecture

The implementation is split into ingestion, embedding, retrieval, and answer generation layers so file parsing and vector search remain independent from the final QA step.

| Module | Responsibility |
|--------|----------------|
| app/file_parser.py | Scans supported source files and loads their contents. |
| app/indexer.py | Chunks code, generates embeddings, and manages the in-memory vector store. |
| app/retriever.py | Retrieves the most relevant code chunks for a developer query. |
| app/context_builder.py | Formats retrieved chunks into prompt-ready context. |
| app/qa_agent.py | Answers questions using only the retrieved code evidence. |

## Features

- Repository scanning and chunking for supported source file types.
- Embedding-backed retrieval over indexed code context.
- Grounded answers that stay tied to retrieved source snippets.
- API-first workflow for grounded codebase question answering.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/codebase-copilot/run \
  -H "Content-Type: application/json" \
  -d '{"input": "./my-project\nHow does the authentication middleware work?"}'
```

## Evaluation

```text
POST /eval/codebase-copilot
```

Primary metrics: answer relevance, retrieval precision, citation usefulness, latency, and failure rate.
