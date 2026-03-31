# Document Intelligence

## Overview

A document processing pipeline that ingests text documents, chunks and embeds them, retrieves grounded context, answers questions with source references, and extracts structured information from individual files. It is built for lightweight local document QA and extraction workflows.

## System Flow

Documents are loaded into a vector store through ingestion and chunking, then a user query retrieves the most relevant chunks for answer generation or a specific file is passed to the extractor for structured field extraction.

```text
Documents -> Ingest -> Chunker -> Embedder -> Vector Store -> Retriever -> QA Engine / Extractor -> Output
```

## Architecture

The project separates document ingestion, vector search, answer generation, citation attachment, and structured extraction so retrieval and extraction can evolve independently.

| Module | Responsibility |
|--------|----------------|
| app/ingest.py | Loads markdown and text files with source metadata. |
| app/chunker.py | Splits documents into retrieval-friendly chunks. |
| app/retriever.py | Runs semantic and reranked chunk retrieval from the vector store. |
| app/qa_engine.py | Generates grounded answers from retrieved chunks. |
| app/extractor.py | Extracts key points, clauses, and risks as structured JSON. |

## Features

- Local ingestion for markdown and text document collections.
- Vector-store-backed retrieval for grounded question answering.
- Citation attachment for answer traceability.
- Structured extraction path for clauses, key points, and risks.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/document-intelligence/run \
  -H "Content-Type: application/json" \
  -d '{"input": "What risks are mentioned in the documents?"}'
```

## Evaluation

```text
POST /eval/document-intelligence
```

Primary metrics: answer accuracy, citation correctness, extraction completeness, latency, and failure rate.
