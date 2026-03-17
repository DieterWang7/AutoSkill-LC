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
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "host": host,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "recommendationCount": len(recommendations),
        "recommendations": [item.to_dict() for item in recommendations],
    }
    temp_path = report_path.with_suffix(report_path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(report_path)

