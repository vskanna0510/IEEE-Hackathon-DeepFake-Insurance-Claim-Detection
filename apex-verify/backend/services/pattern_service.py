"""
Pattern Analysis Service

Detects cross-claim fraud patterns by:
1. Maintaining a per-claim embedding store (SQLite + FAISS)
2. Clustering stored embeddings to identify fraud rings
3. Flagging claims that match known suspicious clusters

This service works alongside similarity_service.py. similarity_service finds
nearest neighbors; pattern_service detects organized fraud clusters.
"""
from __future__ import annotations

import os
import sqlite3
import json
from collections import defaultdict
from typing import Any, Dict, List, Optional
from datetime import datetime

import numpy as np

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "similar_images.db")
CLAIMS_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "claims.db")

os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)


def _ensure_claims_schema() -> None:
    conn = sqlite3.connect(CLAIMS_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_uuid TEXT UNIQUE,
            timestamp TEXT,
            authenticity_score REAL,
            risk_level TEXT,
            embedding_json TEXT,
            metadata_json TEXT
        )
    """)
    conn.commit()
    conn.close()


def store_claim(
    claim_uuid: str,
    authenticity_score: float,
    risk_level: str,
    embedding: Optional[np.ndarray],
    extra_metadata: Optional[Dict] = None,
) -> None:
    """Persist a claim record with its embedding for future pattern analysis."""
    _ensure_claims_schema()
    emb_json = json.dumps(embedding.flatten().tolist()) if embedding is not None else None
    conn = sqlite3.connect(CLAIMS_DB_PATH)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO claims 
               (claim_uuid, timestamp, authenticity_score, risk_level, embedding_json, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                claim_uuid,
                datetime.utcnow().isoformat(),
                float(authenticity_score),
                risk_level,
                emb_json,
                json.dumps(extra_metadata or {}),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def analyze_patterns(current_embedding: Optional[np.ndarray], top_k: int = 5) -> Dict[str, Any]:
    """
    Analyze cross-claim patterns relative to the current embedding.

    Returns:
    - cluster_match: whether the current claim matches a known fraud cluster
    - cluster_size: how many similar claims were found
    - similar_claim_uuids: UUIDs of the most similar past claims
    - pattern_risk_flag: True if cluster is large (≥3 similar claims)
    """
    _ensure_claims_schema()

    try:
        conn = sqlite3.connect(CLAIMS_DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT claim_uuid, risk_level, embedding_json, authenticity_score FROM claims ORDER BY id DESC LIMIT 200"
        ).fetchall()
        conn.close()
    except Exception:
        return _default_pattern_result()

    if not rows or current_embedding is None:
        return _default_pattern_result()

    # Build embedding matrix
    embeddings = []
    uuids = []
    risk_levels = []

    for row in rows:
        emb_json = row["embedding_json"]
        if emb_json:
            try:
                emb = np.array(json.loads(emb_json), dtype=np.float32)
                embeddings.append(emb)
                uuids.append(row["claim_uuid"])
                risk_levels.append(row["risk_level"])
            except Exception:
                pass

    if len(embeddings) < 2:
        return _default_pattern_result()

    emb_matrix = np.stack(embeddings)
    # Normalize
    norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True) + 1e-8
    emb_matrix = emb_matrix / norms

    curr_norm = current_embedding.flatten() / (np.linalg.norm(current_embedding) + 1e-8)
    similarities = (emb_matrix @ curr_norm).tolist()

    # Find top-k most similar
    indexed = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
    top = indexed[:top_k]

    # Define similarity threshold for "matching"
    THRESHOLD = 0.85
    matching = [(uuids[i], sim, risk_levels[i]) for i, sim in top if sim >= THRESHOLD]

    high_risk_similar = sum(1 for _, _, rl in matching if rl in ("HIGH", "CRITICAL"))
    cluster_size = len(matching)

    pattern_risk_flag = cluster_size >= 3 or high_risk_similar >= 2

    return {
        "cluster_match": cluster_size > 0,
        "cluster_size": cluster_size,
        "high_risk_similar_count": high_risk_similar,
        "similar_claim_uuids": [u for u, _, _ in matching],
        "pattern_risk_flag": pattern_risk_flag,
        "pattern_explanation": (
            f"Found {cluster_size} highly similar claims in database"
            + (f" ({high_risk_similar} rated HIGH/CRITICAL risk)" if high_risk_similar else "")
            if cluster_size > 0
            else "No significant pattern matches found."
        ),
    }


def _default_pattern_result() -> Dict[str, Any]:
    return {
        "cluster_match": False,
        "cluster_size": 0,
        "high_risk_similar_count": 0,
        "similar_claim_uuids": [],
        "pattern_risk_flag": False,
        "pattern_explanation": "Insufficient data for pattern analysis.",
    }


__all__ = ["store_claim", "analyze_patterns"]
