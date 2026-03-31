import json
import os
from datetime import datetime, timezone

from app.embedder import generate_embedding
from app.vector_store import VectorStore


class KnowledgeMemory:
    def __init__(self, path: str | None = None):
        self._store = VectorStore()
        self._entries: list[dict] = []
        self._path = path
        if path and os.path.exists(path):
            self.load()

    def add_memory(self, text: str, source: str = "") -> None:
        text = text.strip()
        if not text:
            return
        embedding = generate_embedding(text)
        entry = {
            "text": text,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._entries.append(entry)
        self._store.add_documents([{
            "text": text,
            "embedding": embedding,
            "metadata": {"source": source, "index": len(self._entries) - 1},
        }])

    def retrieve_memory(self, query: str, top_k: int = 5) -> list[dict]:
        if not self._entries:
            return []
        query_embedding = generate_embedding(query)
        results = self._store.search(query_embedding, top_k=top_k)
        return [
            {
                "text": r["text"],
                "score": r["score"],
                "source": r["metadata"].get("source", ""),
            }
            for r in results
        ]

    def list_memories(self) -> list[dict]:
        return list(self._entries)

    def save(self) -> None:
        if not self._path:
            return
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        data = {
            "entries": self._entries,
            "documents": self._store._documents,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self) -> None:
        if not self._path or not os.path.exists(self._path):
            return
        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._entries = data.get("entries", [])
        self._store._documents = data.get("documents", [])