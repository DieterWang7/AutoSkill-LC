from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.adapters.base import HostCapabilities
from autoskill_lc.core.models import ConversationSignal, GovernanceRecommendation, RecommendationAction
from autoskill_lc.runtime.contracts import MaintenanceJob
from autoskill_lc.runtime.maintenance import run_maintenance


@dataclass
class FakeAdapter:
    name: str = "fake-host"
    capabilities: HostCapabilities = field(default_factory=HostCapabilities)
    report_path: Path | None = None
    last_report: list[GovernanceRecommendation] = field(default_factory=list)

    def collect_signals(self) -> list[ConversationSignal]:
        return [
            ConversationSignal(
                topic="skill suggestions",
                evidence=("pattern repeated in multiple sessions",),
                confidence=0.88,
                observed_runs=3,
            )
        ]

    def list_skills(self) -> list[object]:
        return []

    def emit_report(
        self,
        recommendations: list[GovernanceRecommendation],
        *,
        report_path: Path,
    ) -> None:
        self.report_path = report_path
        self.last_report = recommendations


def test_run_maintenance_collects_signals_and_emits_report() -> None:
    adapter = FakeAdapter()
    job = MaintenanceJob(
        adapter_name="fake-host",
        report_path=Path("reports/governance.json"),
    )

    recommendations = run_maintenance(
        adapter,
        job=job,
        now=datetime(2026, 3, 18, tzinfo=timezone.utc),
    )

    assert adapter.report_path == Path("reports/governance.json")
    assert adapter.last_report == recommendations
    assert len(recommendations) == 1
    assert recommendations[0].action == RecommendationAction.ADD
