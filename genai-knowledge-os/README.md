# Personal Knowledge OS

## Overview

A modular knowledge system that ingests local notes, stores vectorized chunks, retrieves relevant context, summarizes content, and generates cross-document insights with optional memory persistence. The project is designed for personal knowledge workflows rather than enterprise search infrastructure.

## System Flow

Documents are ingested into a vector store, user questions retrieve the most relevant chunks, summarization condenses the result, and an insight layer can generate higher-level cross-document observations that are stored in memory.

```text
Documents -> Ingest -> Chunker -> Embedder -> Vector Store -> Retriever -> Summarizer / Insight Engine -> Answer + Memory
```

## Architecture

The implementation separates ingestion, retrieval, summarization, insight generation, and memory storage so the system can support both simple lookup and higher-level synthesis workflows.

| Module | Responsibility |
|--------|----------------|
| app/ingest.py | Loads markdown and text notes from local directories. |
| app/retriever.py | Performs hybrid semantic and keyword retrieval from the vector store. |
| app/summarizer.py | Produces concise summaries from retrieved context. |
| app/insight_engine.py | Generates cross-document insights and patterns. |
| app/memory.py | Persists useful insights for later retrieval. |

## Features

- Local note ingestion with persistent vector storage.
- Hybrid retrieval combining semantic and keyword signals.
- Cross-document insight generation for non-obvious connections.
- Persistent memory layer for reusable synthesized knowledge.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/knowledge-os/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Summarize my research on AI agents"}'
```

## Evaluation

```text
POST /eval/knowledge-os
```

Primary metrics: retrieval relevance, summary quality, insight novelty, latency, and failure rate.
