from __future__ import annotations

import json
from pathlib import Path

from autoskill_lc.core.reporting import build_governance_report_payload
from autoskill_lc.core.models import ConversationSignal
from autoskill_lc.core.models import GovernanceRecommendation


def write_governance_report(
    report_path: Path,
    recommendations: list[GovernanceRecommendation],
    *,
    host: str,
    signals: list[ConversationSignal],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_governance_report_payload(
        host=host,
        recommendations=recommendations,
        signals=signals,
    )
    temp_path = report_path.with_suffix(report_path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(report_path)
