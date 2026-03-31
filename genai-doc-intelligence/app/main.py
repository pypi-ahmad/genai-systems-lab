import os

from app.ingest import load_documents
from app.chunker import chunk_document
from app.embedder import batch_embeddings
from app.vector_store import VectorStore
from app.retriever import init_store, retrieve
from app.qa_engine import answer_query
from app.citation import attach_citations
from app.extractor import extract_key_information
from shared.api.step_events import emit_step
from shared.config import set_byok_api_key, reset_byok_api_key


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STORE_PATH = os.path.join(DATA_DIR, "vectors.json")


def run(input: str, api_key: str) -> dict:
    """Run a document query and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        store = VectorStore(STORE_PATH)
        init_store(store)
        return query(input)
    finally:
        reset_byok_api_key(token)


def ingest(folder_path: str, store: VectorStore) -> int:
    documents = load_documents(folder_path)
    if not documents:
        print("No documents found.")
        return 0

    all_chunks = []
    for doc in documents:
        texts = chunk_document(doc["text"])
        for i, text in enumerate(texts):
            all_chunks.append({
                "text": text,
                "metadata": {"source": doc["source"], "chunk_id": i},
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


def query(question: str) -> dict:
    emit_step("retriever", "running")
    chunks = retrieve(question, top_k=5)
    emit_step("retriever", "done")
    if not chunks:
        return {"answer": "No relevant documents found.", "sources": []}

    emit_step("qa", "running")
    raw_answer = answer_query(question, chunks)
    emit_step("qa", "done")

    emit_step("extractor", "running")
    cited_answer = attach_citations(raw_answer, chunks)
    emit_step("extractor", "done")
    sources = list({c["metadata"].get("source", "") for c in chunks if c["metadata"].get("source")})

    return {"answer": cited_answer, "sources": sources}


def extract(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return extract_key_information(text)
