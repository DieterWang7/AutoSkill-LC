from __future__ import annotations

from datetime import datetime

from autoskill_lc.adapters.base import HostAdapter
from autoskill_lc.core.engine import GovernanceEngine
from autoskill_lc.core.models import GovernanceRecommendation
from autoskill_lc.runtime.contracts import MaintenanceJob


def run_maintenance(
    adapter: HostAdapter,
    *,
    engine: GovernanceEngine | None = None,
    job: MaintenanceJob,
    now: datetime | None = None,
) -> list[GovernanceRecommendation]:
    """Run one host-neutral maintenance pass and persist its report."""

    governance_engine = engine or GovernanceEngine()
    signals = adapter.collect_signals()
    skills = adapter.list_skills()
    recommendations = governance_engine.analyze(signals, skills, now=now)
    adapter.emit_report(recommendations, report_path=job.report_path)
    return recommendations

