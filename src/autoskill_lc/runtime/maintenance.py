from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.adapters.base import HostAdapter
from autoskill_lc.core.apply_policy import evaluate_apply_policy
from autoskill_lc.core.applier import apply_patch_proposals
from autoskill_lc.core.engine import GovernanceEngine
from autoskill_lc.core.patches import build_patch_proposals
from autoskill_lc.core.reporting import enrich_governance_report_payload
from autoskill_lc.core.semantic_merge import merge_signals
from autoskill_lc.core.skill_mapper import map_signals_to_skills
from autoskill_lc.core.verifier import verify_patch_proposals
from autoskill_lc.core.models import GovernanceRecommendation
from autoskill_lc.runtime.checkpoints import (
    filter_signals_for_incremental_run,
    read_checkpoint_state,
    write_checkpoint_entry,
)
from autoskill_lc.runtime.contracts import MaintenanceJob
from autoskill_lc.runtime.ledger import write_ledger_entry


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
    semantic_merge = merge_signals(signals)
    signals = semantic_merge.signals
    skills = adapter.list_skills()
    recommendations = governance_engine.analyze(signals, skills, now=now)
    mappings = map_signals_to_skills(signals, skills)
    proposals = build_patch_proposals(
        recommendations,
        mappings,
        checkpoint_state=checkpoint_state,
        generated_at=now,
    )
    verifications = verify_patch_proposals(proposals)
    decisions = evaluate_apply_policy(proposals, verifications)
    rollback_dir = _rollback_dir_for(job.report_path)
    applied_changes = [
        {
            "proposalId": item.proposal_id,
            "skillPath": item.skill_path,
            "rollbackManifestPath": item.rollback_manifest_path,
            "appliedAt": item.applied_at,
        }
        for item in apply_patch_proposals(
            proposals,
            verifications=verifications,
            decisions=decisions,
            rollback_dir=rollback_dir,
            generated_at=now,
        )
    ]
    adapter.emit_report(
        recommendations,
        report_path=job.report_path,
        signals=signals,
        generated_at=now,
        checkpoint_state=checkpoint_state,
    )
    ledger_path = _ledger_path_for(job.report_path)
    ledger = write_ledger_entry(
        ledger_path,
        proposals=proposals,
        verifications=verifications,
        decisions=decisions,
        applied_changes=applied_changes,
        checkpoint_sequence=int((checkpoint_state or {}).get("sequence", 0)),
        report_path=job.report_path,
        generated_at=now,
    )
    ledger_entry = {
        "path": str(ledger_path),
        "checkpointSequence": ledger.checkpoint_sequence,
        "proposalCount": ledger.proposal_count,
        "appliedCount": ledger.applied_count,
        "generatedAt": ledger.generated_at,
    }
    _enrich_report_file(
        job.report_path,
        semantic_merge=semantic_merge,
        mappings=mappings,
        proposals=proposals,
        verifications=verifications,
        decisions=decisions,
        ledger_entry=ledger_entry,
        applied_changes=applied_changes,
    )
    if job.checkpoint_path is not None:
        write_checkpoint_entry(
            job.checkpoint_path,
            host=adapter.name,
            signals=signals,
            recommendations=recommendations,
            run_at=now or datetime.now(timezone.utc),
        )
    return recommendations


def _ledger_path_for(report_path: Path) -> Path:
    if report_path.parent.name == "reports":
        return report_path.parent.parent / "ledger.jsonl"
    return report_path.parent / "ledger.jsonl"


def _rollback_dir_for(report_path: Path) -> Path:
    if report_path.parent.name == "reports":
        return report_path.parent.parent / "rollbacks"
    return report_path.parent / "rollbacks"


def _enrich_report_file(
    report_path: Path,
    *,
    semantic_merge,
    mappings,
    proposals,
    verifications,
    decisions,
    ledger_entry,
    applied_changes,
) -> None:
    if not report_path.exists():
        return
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    enriched = enrich_governance_report_payload(
        payload,
        semantic_merge=semantic_merge,
        mappings=mappings,
        proposals=proposals,
        verifications=verifications,
        decisions=decisions,
        ledger_entry=ledger_entry,
        applied_changes=applied_changes,
    )
    report_path.write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
