from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from autoskill_lc.core.reporting import build_governance_report_payload
from autoskill_lc.core.models import GovernanceRecommendation
from autoskill_lc.core.models import ConversationSignal


def write_governance_report(
    report_path: Path,
    recommendations: list[GovernanceRecommendation],
    *,
    host: str,
    signals: list[ConversationSignal],
    generated_at: datetime | None = None,
    checkpoint_state: dict[str, object] | None = None,
) -> None:
    """Write a structured governance report to the specified path.
    
    Args:
        report_path: Path where the report should be written
        recommendations: List of governance recommendations to include
        host: Name of the host adapter that generated this report
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    payload = build_governance_report_payload(
        host=host,
        recommendations=recommendations,
        signals=signals,
        generated_at=generated_at,
        checkpoint_state=checkpoint_state,
    )
    
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
