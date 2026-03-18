from autoskill_lc.core.apply_policy import ApplyTier, evaluate_apply_policy
from autoskill_lc.core.models import RecommendationAction
from autoskill_lc.core.patches import PatchProposal
from autoskill_lc.core.verifier import VerificationResult


def test_evaluate_apply_policy_marks_high_confidence_upgrade_safe() -> None:
    proposal = PatchProposal(
        proposal_id="patch-1",
        topic="topic",
        action=RecommendationAction.UPGRADE,
        target_skill_id="skill-1",
        target_skill_title="Skill 1",
        confidence=0.9,
        checkpoint_sequence=1,
        header_note="note",
        operations=("update_skill_section",),
        evidence=("e1",),
    )
    verification = VerificationResult(proposal_id="patch-1", passed=True, issues=())

    decisions = evaluate_apply_policy([proposal], [verification])

    assert decisions[0].tier is ApplyTier.SAFE_AUTO_APPLY


def test_evaluate_apply_policy_marks_add_for_review() -> None:
    proposal = PatchProposal(
        proposal_id="patch-2",
        topic="topic",
        action=RecommendationAction.ADD,
        target_skill_id=None,
        target_skill_title=None,
        confidence=0.95,
        checkpoint_sequence=1,
        header_note="note",
        operations=("create_skill_stub",),
        evidence=("e1",),
    )
    verification = VerificationResult(proposal_id="patch-2", passed=True, issues=())

    decisions = evaluate_apply_policy([proposal], [verification])

    assert decisions[0].tier is ApplyTier.HUMAN_REVIEW
