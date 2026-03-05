"""
Alert Service

Evaluates fraud scores and generates structured alert objects with:
- Risk category: LOW / MEDIUM / HIGH / CRITICAL
- Recommended actions per risk level
- Alert log (in-memory deque, last 100 alerts)
- Alert event payload suitable for SSE emission
"""
from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List

_alert_log: Deque[Dict[str, Any]] = deque(maxlen=100)


def evaluate_alert(
    claim_uuid: str,
    authenticity_score: float,
    breakdown: Dict[str, float],
    fraud_reasons: List[str],
    pattern_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Evaluate signals and generate a structured alert.

    Alert levels:
        CRITICAL (score < 20): Immediate escalation required
        HIGH     (score < 45): Requires human review
        MEDIUM   (score < 75): Flagged for monitoring
        LOW      (score >= 75): Likely authentic
    """
    score = float(authenticity_score)
    bp = breakdown or {}

    # Determine base alert level from authenticity score
    if score < 20:
        level = "CRITICAL"
    elif score < 45:
        level = "HIGH"
    elif score < 75:
        level = "MEDIUM"
    else:
        level = "LOW"

    # Escalate if pattern fraud ring detected
    if pattern_result and pattern_result.get("pattern_risk_flag"):
        if level == "MEDIUM":
            level = "HIGH"
        elif level == "LOW":
            level = "MEDIUM"

    actions = _recommended_actions(level, bp, fraud_reasons, pattern_result)

    alert = {
        "claim_uuid": claim_uuid,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "alert_level": level,
        "authenticity_score": round(score, 1),
        "recommended_actions": actions,
        "top_fraud_signals": fraud_reasons[:3],
        "pattern_flag": bool(pattern_result and pattern_result.get("pattern_risk_flag")),
    }

    _alert_log.append(alert)
    return alert


def _recommended_actions(
    level: str,
    bp: Dict[str, float],
    reasons: List[str],
    pattern_result: Dict | None,
) -> List[str]:
    actions: List[str] = []

    if level == "CRITICAL":
        actions.append("🚨 Immediately reject claim and escalate to fraud investigation team")
        actions.append("Freeze associated policy pending investigation")
        actions.append("Document all digital evidence and preserve audit trail")
    elif level == "HIGH":
        actions.append("⚠️ Flag claim for mandatory senior adjuster review")
        actions.append("Request original device files and metadata from claimant")
        actions.append("Contact claimant for additional statement and documentation")
    elif level == "MEDIUM":
        actions.append("📋 Route claim for secondary review before approval")
        actions.append("Request corroborating documentation (police report, repair estimate)")
    else:
        actions.append("✅ Claim appears authentic — proceed with standard processing")

    # Signal-specific recommendations
    if bp.get("tampering_probability", 0) > 0.7:
        actions.append("Commission independent digital forensics examination")
    if bp.get("ai_generation_probability", 0) > 0.7:
        actions.append("Verify claim images against claimant's original device")
    if bp.get("similarity_score", 0) > 0.75:
        actions.append("Cross-reference with linked claims and shared policy holders")
    if bp.get("metadata_score", 1) < 0.3:
        actions.append("Request original unedited JPEG files with intact EXIF data")
    if pattern_result and pattern_result.get("pattern_risk_flag"):
        similar_count = pattern_result.get("cluster_size", 0)
        actions.append(f"Investigate fraud ring — {similar_count} similar claims found in database")

    return actions


def get_recent_alerts(limit: int = 20) -> List[Dict[str, Any]]:
    """Return the most recent alerts from the in-memory log."""
    return list(reversed(list(_alert_log)))[:limit]


__all__ = ["evaluate_alert", "get_recent_alerts"]
