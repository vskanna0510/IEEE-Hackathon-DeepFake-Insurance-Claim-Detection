"""
Scoring Service — computes structured fraud confidence breakdown.

Returns a richer payload than the legacy ensemble score, including
physics and context sub-scores for a complete fraud confidence breakdown.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


WEIGHTS = {
    "sam2_confidence": 0.20,
    "ela_score": 0.17,
    "region_ela_score": 0.13,
    "similarity_score": 0.17,
    "ai_gen_score": 0.13,
    "metadata_score": 0.10,
    "physics_score": 0.05,
    "context_score": 0.05,
}


def compute_confidence_breakdown(
    sam2_confidence: float,
    ela_score: float,
    region_ela_score: float,
    similarity_score: float,
    ai_gen_score: float,
    metadata_score: float,
    physics_score: float = 0.5,
    context_score: float = 0.5,
) -> Dict[str, Any]:
    """
    Compute a structured fraud confidence breakdown.

    All inputs are in [0, 1] where:
      - Higher SAM2 confidence → image regions are well-defined (less suspicious)
      - Higher ELA scores     → more compression anomalies (more suspicious)
      - Higher similarity     → more duplicate-like (more suspicious)
      - Higher AI gen score   → more likely AI-generated (more suspicious)
      - Lower metadata score  → less consistent metadata (more suspicious)
      - Lower physics score   → more lighting/shadow inconsistency (more suspicious)
      - Lower context score   → more inconsistency with real-world events (more suspicious)

    Returns authenticity_score in [0, 100] (higher = more authentic).
    """
    def clamp(x: float) -> float:
        return float(max(0.0, min(1.0, x)))

    sam2 = clamp(sam2_confidence)
    ela = clamp(ela_score)
    r_ela = clamp(region_ela_score)
    sim = clamp(similarity_score)
    ai = clamp(ai_gen_score)
    meta = clamp(metadata_score)
    phys = clamp(physics_score)
    ctx = clamp(context_score)

    # Invert fraud-indicating signals so higher composite = more authentic
    # ELA, region_ela, similarity, ai_gen  → these increase with fraud
    # SAM2_confidence, metadata, physics, context → these decrease with fraud
    authenticity_raw = (
        WEIGHTS["sam2_confidence"] * sam2
        + WEIGHTS["ela_score"] * (1.0 - ela)
        + WEIGHTS["region_ela_score"] * (1.0 - r_ela)
        + WEIGHTS["similarity_score"] * (1.0 - sim)
        + WEIGHTS["ai_gen_score"] * (1.0 - ai)
        + WEIGHTS["metadata_score"] * meta
        + WEIGHTS["physics_score"] * phys
        + WEIGHTS["context_score"] * ctx
    )

    authenticity_score = round(float(clamp(authenticity_raw)) * 100.0, 1)

    # Risk level
    if authenticity_score >= 75:
        risk_level = "LOW"
    elif authenticity_score >= 45:
        risk_level = "MEDIUM"
    elif authenticity_score >= 20:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    # Per-dimension fraud probabilities (inverted where needed)
    tampering_probability = round((ela * 0.6 + r_ela * 0.4), 3)
    ai_generation_probability = round(ai, 3)
    metadata_fraud_score = round(1.0 - meta, 3)
    region_consistency_score = round(1.0 - r_ela, 3)
    physics_consistency_score = round(phys, 3)
    context_consistency_score = round(ctx, 3)
    similarity_risk = round(sim, 3)

    fraud_reasons: List[str] = _build_reasons(
        ela, r_ela, sim, ai, meta, sam2, phys, ctx
    )

    return {
        "authenticity_score": authenticity_score,
        "risk_level": risk_level,
        "breakdown": {
            "metadata_score": round(meta, 3),
            "tampering_probability": tampering_probability,
            "ai_generation_probability": ai_generation_probability,
            "similarity_score": similarity_risk,
            "region_consistency_score": region_consistency_score,
            "physics_consistency_score": physics_consistency_score,
            "context_consistency_score": context_consistency_score,
        },
        "fraud_reasons": fraud_reasons,
    }


def _build_reasons(
    ela: float,
    r_ela: float,
    sim: float,
    ai: float,
    meta: float,
    sam2: float,
    phys: float,
    ctx: float,
) -> List[str]:
    reasons: List[str] = []

    if ai > 0.65:
        reasons.append("AI-generation detector indicates high likelihood of synthetic content")
    if ela > 0.60 or r_ela > 0.60:
        reasons.append("Strong ELA anomalies detected — possible region manipulation")
    if sim > 0.72:
        reasons.append("Image highly similar to previous claims — possible reuse or duplication")
    if meta < 0.40:
        reasons.append("Metadata inconsistencies detected — possible EXIF tampering")
    if sam2 < 0.30:
        reasons.append("Low segmentation confidence — object regions poorly defined")
    if phys < 0.40:
        reasons.append("Physical inconsistencies — shadow/lighting mismatch detected")
    if ctx < 0.40:
        reasons.append("Context mismatch — claim details inconsistent with verified real-world events")

    if not reasons:
        reasons.append("No significant fraud indicators detected")

    return reasons


__all__ = ["compute_confidence_breakdown"]
