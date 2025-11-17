"""Knowledge ingestion service used by admin endpoints."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import List

from fastapi import UploadFile

from ..ai.vector_store import LocalVectorStore


class IngestionService:
    """Handles ingestion of manual snippets and uploaded files."""

    def __init__(self, vector_store: LocalVectorStore) -> None:
        self.vector_store = vector_store

    def ingest_text(self, title: str, text: str, metadata: dict | None = None) -> List[str]:
        """Split text into manageable chunks and store them."""
        if not text.strip():
            raise ValueError("Text payload is empty.")
        metadata = metadata or {}
        metadata.setdefault("title", title)
        chunk_size = 800
        doc_ids = []
        for chunk in textwrap.wrap(text.strip(), chunk_size, drop_whitespace=False):
            doc_ids.append(self.vector_store.add_text(chunk, metadata=metadata))
        return doc_ids

    async def ingest_file(self, upload: UploadFile, metadata: dict | None = None) -> List[str]:
        """Persist uploaded file temporarily and pipe the bytes through ingest_text."""
        temp_path = Path(f"data/uploads/{upload.filename}")
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        contents = await upload.read()
        temp_path.write_bytes(contents)

        text = contents.decode("utf-8", errors="ignore")
        return self.ingest_text(title=upload.filename, text=text, metadata=metadata)
