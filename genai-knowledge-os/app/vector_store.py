import json
import os

import numpy as np


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class VectorStore:
    def __init__(self, path: str | None = None):
        self._documents: list[dict] = []
        self._path = path
        if path and os.path.exists(path):
            self.load()

    def add_documents(self, documents: list[dict]) -> None:
        for doc in documents:
            text = str(doc.get("text", "")).strip()
            embedding = doc.get("embedding")
            if not text or not isinstance(embedding, list) or not embedding:
                continue
            self._documents.append({
                "text": text,
                "embedding": [float(v) for v in embedding],
                "metadata": doc.get("metadata", {}),
            })

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        if not query_embedding or not self._documents:
            return []
        query_vec = np.asarray(query_embedding, dtype=float)
        scored = []
        for doc in self._documents:
            doc_vec = np.asarray(doc["embedding"], dtype=float)
            score = _cosine_similarity(query_vec, doc_vec)
            scored.append({
                "text": doc["text"],
                "score": score,
                "metadata": doc["metadata"],
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def save(self) -> None:
        if not self._path:
            return
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._documents, f)

    def load(self) -> None:
        if not self._path or not os.path.exists(self._path):
            return
        with open(self._path, "r", encoding="utf-8") as f:
            self._documents = json.load(f)

    def __len__(self) -> int:
        return len(self._documents)