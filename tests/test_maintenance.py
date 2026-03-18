import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.adapters.base import HostCapabilities
from autoskill_lc.core.reporting import build_governance_report_payload
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


@dataclass
class FileWritingFakeAdapter(FakeAdapter):
    def emit_report(
        self,
        recommendations: list[GovernanceRecommendation],
        *,
        report_path: Path,
        signals: list[ConversationSignal],
        generated_at: datetime | None = None,
        checkpoint_state: dict[str, object] | None = None,
    ) -> None:
        super().emit_report(
            recommendations,
            report_path=report_path,
            signals=signals,
            generated_at=generated_at,
            checkpoint_state=checkpoint_state,
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        payload = build_governance_report_payload(
            host=self.name,
            recommendations=recommendations,
            signals=signals,
            generated_at=generated_at,
            checkpoint_state=checkpoint_state,
        )
        report_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def test_run_maintenance_collects_signals_and_emits_report(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    job = MaintenanceJob(
        adapter_name="fake-host",
        report_path=tmp_path / "reports" / "governance.json",
    )

    recommendations = run_maintenance(
        adapter,
        job=job,
        now=datetime(2026, 3, 18, tzinfo=timezone.utc),
    )

    assert adapter.report_path == tmp_path / "reports" / "governance.json"
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
        report_path=tmp_path / "reports" / "governance.json",
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


def test_run_maintenance_enriches_report_with_evolution_artifacts(tmp_path: Path) -> None:
    adapter = FileWritingFakeAdapter()
    report_path = tmp_path / "autoskill-lc" / "reports" / "governance.json"
    checkpoint_path = tmp_path / "autoskill-lc" / "checkpoint.md"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        "---\nsequence: 4\nlast_processed_at: 2026-03-18T10:00:00+00:00\n---\n",
        encoding="utf-8",
    )
    adapter.collect_signals = lambda: [  # type: ignore[method-assign]
        ConversationSignal(
            topic="GitHub 安装和服务器自动同步",
            evidence=("user asked for server sync repeatedly",),
            confidence=0.88,
            observed_runs=3,
            last_observed_at=datetime(2026, 3, 18, 11, 0, tzinfo=timezone.utc),
            existing_skill_id="skill-server-sync",
        )
    ]
    adapter.list_skills = lambda: [  # type: ignore[method-assign]
        type(
            "Skill",
            (),
            {
                "skill_id": "skill-server-sync",
                "title": "服务器自动同步 GitHub 安装",
                "version": "1.0.0",
                "usage_count": 1,
                "last_used_at": datetime(2026, 3, 17, 11, 0, tzinfo=timezone.utc),
                "status": "active",
            },
        )()
    ]

    run_maintenance(
        adapter,
        job=MaintenanceJob(
            adapter_name="fake-host",
            report_path=report_path,
            checkpoint_path=checkpoint_path,
        ),
        now=datetime(2026, 3, 18, 12, 0, tzinfo=timezone.utc),
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["summary"]["semanticMergeGroupCount"] == 1
    assert payload["summary"]["skillMappingCount"] == 1
    assert payload["summary"]["patchProposalCount"] == 1
    assert "semanticMerge" in payload
    assert "skillMappings" in payload
    assert "patchProposals" in payload
    assert "verificationResults" in payload
    assert "applyDecisions" in payload
    assert payload["ledger"]["proposalCount"] == 1
    ledger_path = tmp_path / "autoskill-lc" / "ledger.jsonl"
    assert ledger_path.exists()


def test_run_maintenance_writes_ledger_even_without_patch_proposals(tmp_path: Path) -> None:
    adapter = FileWritingFakeAdapter()
    report_path = tmp_path / "autoskill-lc" / "reports" / "governance.json"
    checkpoint_path = tmp_path / "autoskill-lc" / "checkpoint.md"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        "---\nsequence: 1\nlast_processed_at: 2026-03-18T10:00:00+00:00\n---\n",
        encoding="utf-8",
    )
    adapter.collect_signals = lambda: []  # type: ignore[method-assign]
    adapter.list_skills = lambda: []  # type: ignore[method-assign]

    run_maintenance(
        adapter,
        job=MaintenanceJob(
            adapter_name="fake-host",
            report_path=report_path,
            checkpoint_path=checkpoint_path,
        ),
        now=datetime(2026, 3, 18, 12, 0, tzinfo=timezone.utc),
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["ledger"]["proposalCount"] == 0
    assert (tmp_path / "autoskill-lc" / "ledger.jsonl").exists()


def test_run_maintenance_applies_safe_upgrade_and_writes_rollback_manifest(
    tmp_path: Path,
) -> None:
    adapter = FileWritingFakeAdapter()
    skill_path = tmp_path / "skills" / "skill-server-sync" / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text("# Skill\n\nOriginal body.\n", encoding="utf-8")
    report_path = tmp_path / "autoskill-lc" / "reports" / "governance.json"
    checkpoint_path = tmp_path / "autoskill-lc" / "checkpoint.md"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        "---\nsequence: 2\nlast_processed_at: 2026-03-18T10:00:00+00:00\n---\n",
        encoding="utf-8",
    )
    adapter.collect_signals = lambda: [  # type: ignore[method-assign]
        ConversationSignal(
            topic="GitHub 安装和服务器自动同步",
            evidence=("user asked for server sync repeatedly",),
            confidence=0.88,
            observed_runs=3,
            last_observed_at=datetime(2026, 3, 18, 11, 0, tzinfo=timezone.utc),
            existing_skill_id="skill-server-sync",
        )
    ]
    adapter.list_skills = lambda: [  # type: ignore[method-assign]
        type(
            "Skill",
            (),
            {
                "skill_id": "skill-server-sync",
                "title": "服务器自动同步 GitHub 安装",
                "version": "1.0.0",
                "usage_count": 1,
                "last_used_at": datetime(2026, 3, 17, 11, 0, tzinfo=timezone.utc),
                "status": "active",
                "skill_path": str(skill_path),
            },
        )()
    ]

    run_maintenance(
        adapter,
        job=MaintenanceJob(
            adapter_name="fake-host",
            report_path=report_path,
            checkpoint_path=checkpoint_path,
        ),
        now=datetime(2026, 3, 18, 12, 0, tzinfo=timezone.utc),
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["summary"]["appliedChangeCount"] == 1
    assert len(payload["appliedChanges"]) == 1
    assert "AutoSkill-LC Evolution" in skill_path.read_text(encoding="utf-8")
    assert (tmp_path / "autoskill-lc" / "rollbacks" / "patch-0003-01.json").exists()
