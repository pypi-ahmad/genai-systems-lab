import os

from app.ingest import load_documents
from app.chunker import chunk_text
from app.embedder import batch_embeddings
from app.vector_store import VectorStore
from app.retriever import init_store, retrieve
from app.summarizer import summarize
from app.insight_engine import generate_insights
from app.memory import KnowledgeMemory
from shared.api.step_events import emit_step
from shared.config import set_byok_api_key, reset_byok_api_key


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STORE_PATH = os.path.join(DATA_DIR, "vectors.json")
MEMORY_PATH = os.path.join(DATA_DIR, "memory.json")


def run(input: str, api_key: str) -> dict:
    """Run a knowledge query and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        emit_step("store", "running")
        store = VectorStore(STORE_PATH)
        init_store(store)
        memory = KnowledgeMemory(MEMORY_PATH)
        emit_step("store", "done")
        return query(input, memory)
    finally:
        reset_byok_api_key(token)


def ingest(folder_path: str, store: VectorStore) -> int:
    documents = load_documents(folder_path)
    if not documents:
        print("No documents found.")
        return 0

    all_chunks = []
    for doc in documents:
        texts = chunk_text(doc["text"])
        for i, text in enumerate(texts):
            all_chunks.append({
                "text": text,
                "metadata": {"source": doc["source"], "chunk_index": i},
            })

    chunk_texts = [c["text"] for c in all_chunks]
    embeddings = batch_embeddings(chunk_texts)

    docs_to_store = []
    for chunk, embedding in zip(all_chunks, embeddings):
        docs_to_store.append({
            "text": chunk["text"],
            "embedding": embedding,
            "metadata": chunk["metadata"],
        })

    store.add_documents(docs_to_store)
    store.save()
    print(f"Ingested {len(documents)} document(s), {len(all_chunks)} chunk(s) stored.")
    return len(all_chunks)


def query(question: str, memory: KnowledgeMemory) -> dict:
    emit_step("retriever", "running")
    results = retrieve(question, top_k=5)
    emit_step("retriever", "done")
    if not results:
        return {"answer": "No relevant documents found.", "sources": [], "insights": ""}

    chunk_texts = [r["text"] for r in results]
    context = "\n\n".join(chunk_texts)

    emit_step("summarizer", "running")
    answer = summarize(context)
    emit_step("summarizer", "done")

    sources = list({r["metadata"].get("source", "") for r in results if r["metadata"].get("source")})

    insights = ""
    if len(chunk_texts) >= 2:
        emit_step("insights", "running")
        insights = generate_insights(chunk_texts)
        if insights:
            memory.add_memory(insights, source="insight_engine")
            memory.save()
        emit_step("insights", "done")

    return {"answer": answer, "sources": sources, "insights": insights}
