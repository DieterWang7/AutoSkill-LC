from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.adapters.base import HostCapabilities
from autoskill_lc.core.models import (
    ConversationSignal,
    GovernanceRecommendation,
    RecommendationAction,
    ReportClassification,
)
from autoskill_lc.runtime.contracts import MaintenanceJob
from autoskill_lc.runtime.maintenance import run_maintenance


@dataclass
class FakeAdapter:
    name: str = "fake-host"
    capabilities: HostCapabilities = field(default_factory=HostCapabilities)
    report_path: Path | None = None
    last_report: list[GovernanceRecommendation] = field(default_factory=list)
    last_signals: list[ConversationSignal] = field(default_factory=list)

    def collect_signals(self) -> list[ConversationSignal]:
        return [
            ConversationSignal(
                topic="skill suggestions",
                evidence=("pattern repeated in multiple sessions",),
                confidence=0.88,
                observed_runs=3,
                report_classification=ReportClassification.EVIDENCE_BACKED,
            )
        ]

    def list_skills(self) -> list[object]:
        return []

    def emit_report(
        self,
        recommendations: list[GovernanceRecommendation],
        *,
        report_path: Path,
        signals: list[ConversationSignal],
        generated_at: datetime | None = None,
        checkpoint_state: dict[str, object] | None = None,
    ) -> None:
        self.report_path = report_path
        self.last_report = recommendations
        self.last_signals = signals


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
    assert len(adapter.last_signals) == 1
    assert adapter.last_signals[0].topic == "skill suggestions"
    assert len(recommendations) == 1
    assert recommendations[0].action == RecommendationAction.ADD


def test_run_maintenance_only_processes_signals_newer_than_checkpoint(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    checkpoint_path = tmp_path / "checkpoint.md"
    checkpoint_path.write_text(
        "---\nsequence: 2\nlast_processed_at: 2026-03-18T10:00:00+00:00\n---\n",
        encoding="utf-8",
    )
    adapter.collect_signals = lambda: [  # type: ignore[method-assign]
        ConversationSignal(
            topic="old-skill",
            evidence=("old evidence",),
            confidence=0.88,
            observed_runs=3,
            last_observed_at=datetime(2026, 3, 18, 9, 0, tzinfo=timezone.utc),
        ),
        ConversationSignal(
            topic="new-skill",
            evidence=("new evidence",),
            confidence=0.88,
            observed_runs=3,
            last_observed_at=datetime(2026, 3, 18, 11, 0, tzinfo=timezone.utc),
        ),
    ]
    job = MaintenanceJob(
        adapter_name="fake-host",
        report_path=Path("reports/governance.json"),
        checkpoint_path=checkpoint_path,
    )

    recommendations = run_maintenance(
        adapter,
        job=job,
        now=datetime(2026, 3, 18, 12, 0, tzinfo=timezone.utc),
    )

    assert len(adapter.last_signals) == 1
    assert adapter.last_signals[0].topic == "new-skill"
    assert len(recommendations) == 1
