from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.core.models import GovernanceRecommendation


def write_governance_report(
    report_path: Path,
    recommendations: list[GovernanceRecommendation],
    *,
    host: str,
) -> None:
    """Write a structured governance report to the specified path.
    
    Args:
        report_path: Path where the report should be written
        recommendations: List of governance recommendations to include
        host: Name of the host adapter that generated this report
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    def serialize_rec(r: GovernanceRecommendation) -> dict[str, object]:
        return {
            "action": r.action.value,
            "topic": r.topic,
            "confidence": r.confidence,
            "rationale": r.rationale,
            "skill_id": r.skill_id,
            "replacement_skill_id": r.replacement_skill_id,
            "evidence": list(r.evidence) if r.evidence else [],
        }
    
    payload = {
        "host": host,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "recommendationCount": len(recommendations),
        "recommendations": [serialize_rec(item) for item in recommendations],
    }
    
    temp_path = report_path.with_suffix(".tmp")
    try:
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temp_path.replace(report_path)
    except OSError:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise

