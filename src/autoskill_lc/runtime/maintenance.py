from __future__ import annotations

from datetime import datetime

from autoskill_lc.adapters.base import HostAdapter
from autoskill_lc.core.engine import GovernanceEngine
from autoskill_lc.core.models import GovernanceRecommendation
from autoskill_lc.runtime.checkpoints import (
    filter_signals_for_incremental_run,
    read_checkpoint_state,
    write_checkpoint_entry,
)
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
    checkpoint_state: dict[str, object] | None = None
    if job.checkpoint_path is not None:
        checkpoint_state = read_checkpoint_state(job.checkpoint_path)
        signals = filter_signals_for_incremental_run(signals, checkpoint_state)
    skills = adapter.list_skills()
    recommendations = governance_engine.analyze(signals, skills, now=now)
    adapter.emit_report(
        recommendations,
        report_path=job.report_path,
        signals=signals,
        generated_at=now,
        checkpoint_state=checkpoint_state,
    )
    if job.checkpoint_path is not None:
        write_checkpoint_entry(
            job.checkpoint_path,
            host=adapter.name,
            signals=signals,
            recommendations=recommendations,
            run_at=now or datetime.now(),
        )
    return recommendations
