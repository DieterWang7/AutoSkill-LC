from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.core.apply_policy import ApplyDecision
from autoskill_lc.core.patches import PatchProposal
from autoskill_lc.core.verifier import VerificationResult


@dataclass(frozen=True)
class LedgerEntry:
    generated_at: str
    checkpoint_sequence: int
    report_path: str
    proposal_count: int
    applied_count: int
    proposals: list[dict[str, object]]
    verifications: list[dict[str, object]]
    decisions: list[dict[str, object]]
    applied_changes: list[dict[str, object]]


def write_ledger_entry(
    ledger_path: Path,
    *,
    proposals: list[PatchProposal],
    verifications: list[VerificationResult],
    decisions: list[ApplyDecision],
    applied_changes: list[dict[str, object]],
    checkpoint_sequence: int,
    report_path: Path,
    generated_at: datetime | None = None,
) -> LedgerEntry:
    run_at = generated_at or datetime.now(timezone.utc)
    entry = LedgerEntry(
        generated_at=run_at.isoformat(),
        checkpoint_sequence=checkpoint_sequence,
        report_path=str(report_path),
        proposal_count=len(proposals),
        applied_count=len(applied_changes),
        proposals=[asdict(item) for item in proposals],
        verifications=[asdict(item) for item in verifications],
        decisions=[asdict(item) for item in decisions],
        applied_changes=applied_changes,
    )
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    return entry
