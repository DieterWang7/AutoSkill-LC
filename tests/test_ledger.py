import json
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.core.apply_policy import ApplyDecision, ApplyTier
from autoskill_lc.core.models import RecommendationAction
from autoskill_lc.core.patches import PatchProposal
from autoskill_lc.core.verifier import VerificationResult
from autoskill_lc.runtime.ledger import write_ledger_entry


def test_write_ledger_entry_appends_jsonl(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    entry = write_ledger_entry(
        ledger_path,
        proposals=[
            PatchProposal(
                proposal_id="patch-1",
                topic="topic",
                action=RecommendationAction.UPGRADE,
                target_skill_id="skill-1",
                target_skill_title="Skill 1",
                target_skill_path="E:/skills/skill-1/SKILL.md",
                confidence=0.9,
                checkpoint_sequence=1,
                header_note="note",
                operations=("update_skill_section",),
                evidence=("e1",),
            )
        ],
        verifications=[
            VerificationResult(proposal_id="patch-1", passed=True, issues=())
        ],
        decisions=[
            ApplyDecision(
                proposal_id="patch-1",
                tier=ApplyTier.SAFE_AUTO_APPLY,
                reason="high-confidence narrow upgrade",
            )
        ],
        applied_changes=[],
        checkpoint_sequence=1,
        report_path=Path("reports/latest.json"),
        generated_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
    )

    assert entry.proposal_count == 1
    assert entry.applied_count == 0
    payload = json.loads(ledger_path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["checkpoint_sequence"] == 1
