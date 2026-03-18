from datetime import datetime, timezone

from autoskill_lc.core.models import GovernanceRecommendation, RecommendationAction
from autoskill_lc.core.patches import build_patch_proposals
from autoskill_lc.core.skill_mapper import SkillMatch


def test_build_patch_proposals_uses_mapping_and_checkpoint_sequence() -> None:
    proposals = build_patch_proposals(
        [
            GovernanceRecommendation(
                action=RecommendationAction.UPGRADE,
                topic="OpenClaw cron maintenance",
                rationale="Needs update",
                confidence=0.9,
                evidence=("e1",),
            )
        ],
        {
            "OpenClaw cron maintenance": SkillMatch(
                topic="OpenClaw cron maintenance",
                skill_id="skill-openclaw-cron",
                skill_title="OpenClaw cron maintenance",
                skill_path="E:/skills/openclaw-cron/SKILL.md",
                confidence=0.95,
                match_type="exact",
            )
        },
        checkpoint_state={"sequence": 7},
        generated_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
    )

    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.proposal_id == "patch-0008-01"
    assert proposal.target_skill_id == "skill-openclaw-cron"
    assert proposal.target_skill_path == "E:/skills/openclaw-cron/SKILL.md"
    assert "optimized_at=" in proposal.header_note
