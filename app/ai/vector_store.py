"""Simple local vector store used for retrieval in the automation pipeline."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from hashlib import blake2b
from pathlib import Path
from typing import Iterable, List, Optional

from ..config import get_settings


@dataclass
class VectorDocument:
    """Represents a stored knowledge snippet."""

    doc_id: str
    text: str
    metadata: dict
    vector: List[float]


class LocalVectorStore:
    """Minimal persistence-backed vector store."""

    def __init__(self, storage_dir: Path | None = None) -> None:
        settings = get_settings()
        self.dimension = settings.local_embedding_dimension
        self.storage_dir = storage_dir or settings.chroma_path
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.storage_dir / "store.json"
        if not self.store_path.exists():
            self.store_path.write_text("[]", encoding="utf-8")

    def _load(self) -> List[VectorDocument]:
        payload = json.loads(self.store_path.read_text(encoding="utf-8"))
        docs: List[VectorDocument] = []
        for item in payload:
            docs.append(
                VectorDocument(
                    doc_id=item["doc_id"],
                    text=item["text"],
                    metadata=item.get("metadata", {}),
                    vector=item["vector"],
                )
            )
        return docs

    def _persist(self, docs: Iterable[VectorDocument]) -> None:
        serialized = [
            {
                "doc_id": doc.doc_id,
                "text": doc.text,
                "metadata": doc.metadata,
                "vector": doc.vector,
            }
            for doc in docs
        ]
        self.store_path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    def _embed(self, text: str) -> List[float]:
        digest = blake2b(text.encode("utf-8"), digest_size=32).digest()
        # Repeat digest to cover target dimension.
        values = list(digest) * ((self.dimension // len(digest)) + 1)
        vector = [v / 255.0 for v in values[: self.dimension]]
        return vector

    def add_text(self, text: str, metadata: Optional[dict] = None) -> str:
        docs = self._load()
        doc_id = blake2b(text.encode("utf-8"), digest_size=8).hexdigest()
        docs.append(
            VectorDocument(
                doc_id=doc_id, text=text, metadata=metadata or {}, vector=self._embed(text)
            )
        )
        self._persist(docs)
        return doc_id

    def similarity_search(self, query: str, limit: int = 3) -> List[VectorDocument]:
        docs = self._load()
        if not docs:
            return []
        query_vec = self._embed(query)
        scored = sorted(
            docs,
            key=lambda doc: self._cosine_similarity(query_vec, doc.vector),
            reverse=True,
        )
        return scored[:limit]

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
