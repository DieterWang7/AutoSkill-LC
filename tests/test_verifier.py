from autoskill_lc.core.models import RecommendationAction
from autoskill_lc.core.patches import PatchProposal
from autoskill_lc.core.verifier import verify_patch_proposals


def test_verify_patch_proposals_flags_missing_target_for_upgrade() -> None:
    results = verify_patch_proposals(
        [
            PatchProposal(
                proposal_id="patch-1",
                topic="topic",
                action=RecommendationAction.UPGRADE,
                target_skill_id=None,
                target_skill_title=None,
                confidence=0.9,
                checkpoint_sequence=1,
                header_note="note",
                operations=("update_skill_section",),
                evidence=("e1",),
            )
        ]
    )

    assert results[0].passed is False
    assert "missing target skill" in results[0].issues
