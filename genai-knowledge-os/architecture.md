# Architecture

## Overview

The Personal Knowledge OS is a modular system for ingesting, organizing, retrieving, and reasoning over personal documents. It converts unstructured text into a searchable vector store, maintains a persistent memory of key insights, and uses LLM-powered components to summarize content and surface connections across documents.

Primary flow:

`Documents → Ingest → Chunk → Embed → Store → Retrieve → Reason`

## Core Components

### 1. Ingestion Pipeline (`ingest.py`)

- Loads documents from local files (`.txt`, `.md`; `.pdf` support optional later).
- Normalizes content into a common internal format with metadata (filename, source path, timestamp).
- Serves as the single entry point for all new content entering the system.

### 2. Chunker (`chunker.py`)

- Breaks ingested documents into meaningful, overlapping segments.
- Uses configurable chunk size and overlap to balance context preservation with retrieval precision.
- Attaches source metadata (document name, chunk index, position) to each chunk.

### 3. Embedder (`embedder.py`)

- Converts text chunks into dense vector representations.
- Wraps the embedding model behind a clean interface so the provider can be swapped without affecting downstream components.
- Supports batched embedding for efficiency during bulk ingestion.

### 4. Vector Store (`vector_store.py`)

- Stores embedding vectors alongside chunk text and metadata.
- Supports similarity search by cosine distance.
- Persists data to disk so the knowledge base survives across sessions.
- Designed for a simple local-first implementation, replaceable with a managed vector database later.

### 5. Retriever (`retriever.py`)

- Accepts a natural-language query, embeds it, and fetches the top-k most relevant chunks from the vector store.
- Returns ranked results with scores and source metadata.
- Acts as the primary interface between the user's question and the stored knowledge.

### 6. Memory System (`memory.py`)

- Stores important insights, facts, and user-confirmed knowledge over time.
- Operates as a persistent layer separate from the vector store — captures distilled knowledge rather than raw chunks.
- Supports adding, listing, and searching stored memories.
- Feeds into the retriever and insight engine to enrich responses with accumulated context.

### 7. Summarizer (`summarizer.py`)

- Produces concise summaries of full documents or groups of retrieved chunks.
- Uses an LLM to distill content while preserving key details and structure.
- Can be invoked on ingestion (to generate document-level summaries) or at query time (to compress retrieval results).

### 8. Insight Engine (`insight_engine.py`)

- Connects ideas across multiple documents and memory entries.
- Given a topic or question, retrieves relevant chunks and memories, then uses an LLM to identify themes, contradictions, patterns, and novel connections.
- Designed for open-ended exploration rather than single-answer retrieval.

## System Flow

### 1. Document Ingestion

The user provides one or more files. The ingestion pipeline reads each file, normalizes the content, and passes it downstream.

### 2. Chunking

Each document is split into overlapping segments. Metadata linking each chunk back to its source document is preserved.

### 3. Embedding and Storage

Chunks are converted to vectors and stored in the vector store alongside their text and metadata. Optionally, a document-level summary is generated and stored in memory.

### 4. Query and Retrieval

The user asks a question. The retriever embeds the query, searches the vector store, and returns the most relevant chunks.

### 5. Summarization

Retrieved chunks (or full documents) are passed to the summarizer to produce a concise answer or overview.

### 6. Insight Generation

For exploratory questions, the insight engine pulls from both the vector store and the memory system to surface cross-document connections, recurring themes, and novel observations.

### 7. Memory Update

Key insights, confirmed facts, or user-flagged information are persisted to the memory system for future retrieval.

## Model Usage

### `gemini-3.1-pro-preview`

Use for reasoning-heavy tasks that require deep comprehension and cross-document analysis.

Recommended responsibilities:

- Insight Engine (connecting ideas, identifying patterns)
- Complex query answering when simple retrieval is insufficient

### `gemini-3-flash-preview`

Use for high-throughput, lower-latency tasks where speed matters more than deep reasoning.

Recommended responsibilities:

- Summarizer (document and chunk summarization)
- Memory extraction (distilling key facts from content)

This split keeps costs and latency low for routine operations while reserving the stronger model for tasks that benefit from deeper reasoning.

## Design Principles

- **Modular**: Each component has a single responsibility and a clean interface. Components can be developed, tested, and replaced independently.
- **Extensible**: New document types, embedding providers, or vector stores can be added without rewriting existing components.
- **Local-first**: The system works entirely on local files and a local vector store. No external services are required beyond the LLM API.
- **Persistent**: Both the vector store and the memory system persist to disk, so knowledge accumulates across sessions.
- **Composable**: The retriever, summarizer, memory, and insight engine can be combined in different ways to support varied query patterns — from simple lookup to open-ended exploration.

## Entry Point (`main.py`)

- Provides the top-level interface for ingestion and querying.
- Orchestrates the flow between components: ingest → chunk → embed → store for documents; retrieve → summarize / reason for queries.
- Keeps orchestration logic thin — delegates all real work to the individual components.

## High-Level Architecture Summary

The system is organized as a pipeline of independent components connected through simple data interfaces. Documents flow in through ingestion, get chunked and embedded into a persistent vector store, and are queryable through a retriever. A memory system captures distilled knowledge over time. A summarizer compresses content on demand, and an insight engine reasons across the full knowledge base to surface connections. The result is a clean, extensible personal knowledge system that grows smarter as more content is added.