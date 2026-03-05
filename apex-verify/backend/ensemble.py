from __future__ import annotations

from typing import Dict, List, Tuple


def compute_ensemble_score(
    sam2_confidence: float,
    ela_score: float,
    region_ela_score: float,
    similarity_score: float,
    ai_gen_score: float,
    metadata_score: float,
) -> Tuple[float, str, List[str]]:
    """
    Compute the overall authenticity score and qualitative fraud reasons.

    score =
        0.25 * sam2_confidence +
        0.20 * ela_score +
        0.15 * region_ela_score +
        0.20 * similarity_score +
        0.10 * ai_gen_score +
        0.10 * metadata_score

    The returned score is in [0, 100].
    """
    # Clamp all inputs to [0, 1]
    def clamp01(x: float) -> float:
        return float(max(0.0, min(1.0, x)))

    sam2_confidence = clamp01(sam2_confidence)
    ela_score = clamp01(ela_score)
    region_ela_score = clamp01(region_ela_score)
    similarity_score = clamp01(similarity_score)
    ai_gen_score = clamp01(ai_gen_score)
    metadata_score = clamp01(metadata_score)

    score_0_1 = (
        0.25 * sam2_confidence
        + 0.20 * ela_score
        + 0.15 * region_ela_score
        + 0.20 * similarity_score
        + 0.10 * ai_gen_score
        + 0.10 * metadata_score
    )
    score = float(max(0.0, min(1.0, score_0_1)) * 100.0)

    if score >= 80.0:
        risk_level = "Low Risk"
    elif score >= 50.0:
        risk_level = "Medium Risk"
    else:
        risk_level = "High Risk"

    reasons: List[str] = []

    if ai_gen_score > 0.6:
        reasons.append("AI-generation detector indicates high likelihood of synthetic content")
    elif ai_gen_score < 0.3:
        reasons.append("AI-generation detector indicates low likelihood of synthetic content")

    if ela_score > 0.6 or region_ela_score > 0.6:
        reasons.append("Strong ELA anomalies suggesting localized manipulation")
    elif ela_score < 0.3 and region_ela_score < 0.3:
        reasons.append("ELA and regional analysis show low levels of compression anomalies")

    if similarity_score > 0.7:
        reasons.append("Image is highly similar to previous claims (possible reuse)")
    elif similarity_score < 0.3:
        reasons.append("Image is dissimilar to known claims (no immediate duplication found)")

    if metadata_score < 0.4:
        reasons.append("Metadata appears inconsistent or edited")
    elif metadata_score > 0.7:
        reasons.append("Metadata is complete and consistent with original capture")

    if sam2_confidence < 0.3:
        reasons.append("Segmentation model has low confidence on detected objects")
    elif sam2_confidence > 0.7:
        reasons.append("Segmentation model confidently localizes key objects")

    return score, risk_level, reasons


def aggregate_signals_payload(signals: Dict[str, float]) -> List[Dict[str, float]]:
    """
    Prepare a signal breakdown list suitable for frontend visualization.
    """
    breakdown = []
    for key, value in signals.items():
        breakdown.append({"signal": key, "score": float(value * 100.0)})
    return breakdown


__all__ = ["compute_ensemble_score", "aggregate_signals_payload"]

