from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.core.applier import apply_patch_proposals
from autoskill_lc.core.apply_policy import ApplyDecision, ApplyTier
from autoskill_lc.core.models import RecommendationAction
from autoskill_lc.core.patches import PatchProposal
from autoskill_lc.core.verifier import VerificationResult


def test_apply_patch_proposals_updates_skill_and_writes_manifest(tmp_path: Path) -> None:
    skill_path = tmp_path / "skills" / "skill-1" / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text("# Skill 1\n\nOriginal body.\n", encoding="utf-8")

    proposal = PatchProposal(
        proposal_id="patch-1",
        topic="topic",
        action=RecommendationAction.UPGRADE,
        target_skill_id="skill-1",
        target_skill_title="Skill 1",
        target_skill_path=str(skill_path),
        confidence=0.9,
        checkpoint_sequence=1,
        header_note="note",
        operations=("update_skill_section",),
        evidence=("e1",),
    )

    applied = apply_patch_proposals(
        [proposal],
        verifications=[VerificationResult(proposal_id="patch-1", passed=True, issues=())],
        decisions=[
            ApplyDecision(
                proposal_id="patch-1",
                tier=ApplyTier.SAFE_AUTO_APPLY,
                reason="high-confidence narrow upgrade",
            )
        ],
        rollback_dir=tmp_path / "rollbacks",
        generated_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
    )

    assert len(applied) == 1
    updated = skill_path.read_text(encoding="utf-8")
    assert "AutoSkill-LC Evolution" in updated
    assert "patch-1" in updated
    assert (tmp_path / "rollbacks" / "patch-1.json").exists()
