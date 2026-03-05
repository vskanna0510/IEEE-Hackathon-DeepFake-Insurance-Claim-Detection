"""
Similarity Service — wraps CLIP + FAISS search and persists embeddings.
"""
from __future__ import annotations

import asyncio
import os
import sqlite3
from typing import Any, Dict

import numpy as np
from PIL import Image

from similarity import get_similarity_search

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "similar_images.db")


async def run(image: Image.Image) -> Dict[str, Any]:
    """Embed image, search FAISS index, and return matches."""
    loop = asyncio.get_event_loop()
    search = get_similarity_search()
    result = await loop.run_in_executor(None, search.search, image)
    return result


async def store_embedding(claim_id: str, image: Image.Image, metadata: Dict[str, Any]) -> None:
    """Store a new CLIP embedding into FAISS index & SQLite for future pattern matching."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _store_sync, claim_id, image, metadata)


def _store_sync(claim_id: str, image: Image.Image, metadata: Dict[str, Any]) -> None:
    """Synchronous embedding storage (runs in executor)."""
    import faiss
    import json

    search = get_similarity_search()
    if search.index is None:
        return  # No index initialized

    emb = search._embed_image(image)  # shape (1, 512)

    # Get next ID
    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id TEXT,
                file_name TEXT,
                description TEXT
            )"""
        )
        cursor = conn.execute(
            "INSERT INTO images (claim_id, file_name, description) VALUES (?, ?, ?)",
            (claim_id, metadata.get("file_name", ""), metadata.get("description", "")),
        )
        new_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()

    # Add to FAISS index
    id_array = np.array([new_id], dtype=np.int64)
    search.index.add_with_ids(emb, id_array)

    index_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss.index")
    faiss.write_index(search.index, index_path)


__all__ = ["run", "store_embedding"]
