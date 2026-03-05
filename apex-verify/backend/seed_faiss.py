from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np
from PIL import Image

from similarity import CLIPSimilaritySearch, FAISS_INDEX_PATH, SQLITE_DB_PATH


DATA_DIR = Path(__file__).parent / "data"
IMAGES_DIR = DATA_DIR / "images"


def _init_db() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY,
                claim_id TEXT,
                file_name TEXT,
                description TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _load_images() -> List[Tuple[str, Image.Image]]:
    if not IMAGES_DIR.exists():
        return []
    image_files = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        image_files.extend(IMAGES_DIR.glob(ext))

    pairs: List[Tuple[str, Image.Image]] = []
    for path in image_files:
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            continue
        pairs.append((path.name, img))
    return pairs


def seed() -> None:
    """
    Build a FAISS index and SQLite metadata DB from images under backend/data/images.
    """
    _init_db()

    pairs = _load_images()
    if not pairs:
        print("No images found in data/images; FAISS index will not be created.")
        return

    search = CLIPSimilaritySearch()

    embeddings = []
    meta_rows = []

    for idx, (file_name, img) in enumerate(pairs):
        emb = search._embed_image(img)  # shape (1, d)
        embeddings.append(emb[0])
        claim_id = f"CLAIM-{idx+1:05d}"
        meta_rows.append((idx, claim_id, file_name, f"Seeded image {file_name}"))

    emb_matrix = np.vstack(embeddings).astype("float32")
    dim = emb_matrix.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(emb_matrix)

    os.makedirs(DATA_DIR, exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)

    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        conn.executemany(
            "INSERT OR REPLACE INTO images (id, claim_id, file_name, description) VALUES (?, ?, ?, ?)",
            meta_rows,
        )
        conn.commit()
    finally:
        conn.close()

    print(f"Seeded FAISS index with {len(pairs)} images.")


if __name__ == "__main__":
    seed()

