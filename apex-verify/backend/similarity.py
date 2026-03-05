from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Tuple

import faiss
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "data", "faiss.index")
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "similar_images.db")


@dataclass
class SimilarMatch:
    id: int
    distance: float
    metadata: Dict


class CLIPSimilaritySearch:
    """
    CLIP-based embedding + FAISS similarity over historical claims.

    The FAISS index and associated metadata are seeded by `seed_faiss.py`.
    """

    def __init__(self, clip_model_id: str = "openai/clip-vit-base-patch32") -> None:
        self.processor = CLIPProcessor.from_pretrained(clip_model_id)
        self.model = CLIPModel.from_pretrained(clip_model_id).to(DEVICE)
        self.model.eval()

        if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(SQLITE_DB_PATH):
            self.index = None
        else:
            self.index = faiss.read_index(FAISS_INDEX_PATH)

    def _embed_image(self, image: Image.Image) -> np.ndarray:
        inputs = self.processor(images=image, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            outputs = self.model.get_image_features(**inputs)
        embeddings = outputs / outputs.norm(p=2, dim=-1, keepdim=True)
        return embeddings.cpu().numpy().astype("float32")

    def _fetch_metadata(self, ids: List[int]) -> Dict[int, Dict]:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            q_marks = ",".join("?" for _ in ids)
            rows = conn.execute(f"SELECT id, claim_id, file_name, description FROM images WHERE id IN ({q_marks})", ids)
            meta: Dict[int, Dict] = {}
            for row in rows:
                meta[row["id"]] = {
                    "claim_id": row["claim_id"],
                    "file_name": row["file_name"],
                    "description": row["description"],
                }
            return meta
        finally:
            conn.close()

    def search(self, image: Image.Image, k: int = 3) -> Dict:
        if self.index is None:
            return {
                "similarity_score": 0.5,  # neutral
                "matches": [],
                "index_ready": False,
            }

        emb = self._embed_image(image)
        distances, indices = self.index.search(emb, min(k, self.index.ntotal))

        idxs = indices[0].tolist()
        dists = distances[0].tolist()

        # Convert L2 distances to similarity in [0,1] (heuristic)
        # Assume typical distance range [0, 2]; map 0 -> 1.0, 2 -> 0.0
        similarities = [max(0.0, min(1.0, 1.0 - (d / 2.0))) for d in dists]

        meta_map = self._fetch_metadata([i for i in idxs if i >= 0])

        matches: List[Dict] = []
        for idx, dist, sim in zip(idxs, dists, similarities):
            if idx < 0:
                continue
            meta = meta_map.get(idx, {})
            matches.append(
                {
                    "id": idx,
                    "distance": float(dist),
                    "similarity": float(sim),
                    "metadata": meta,
                }
            )

        # Use the maximum similarity as the global similarity_score
        global_similarity = max([m["similarity"] for m in matches], default=0.5)

        return {
            "similarity_score": float(global_similarity),
            "matches": matches,
            "index_ready": True,
        }


_SIM_SEARCH: CLIPSimilaritySearch | None = None


def get_similarity_search() -> CLIPSimilaritySearch:
    global _SIM_SEARCH
    if _SIM_SEARCH is None:
        _SIM_SEARCH = CLIPSimilaritySearch()
    return _SIM_SEARCH


__all__ = ["CLIPSimilaritySearch", "get_similarity_search"]

