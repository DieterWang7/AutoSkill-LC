from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from autoskill_lc.core.models import RecommendationAction
from autoskill_lc.core.patches import PatchProposal
from autoskill_lc.core.verifier import VerificationResult


class ApplyTier(StrEnum):
    REPORT_ONLY = "report_only"
    CANDIDATE_PATCH = "candidate_patch"
    SAFE_AUTO_APPLY = "safe_auto_apply"
    HUMAN_REVIEW = "human_review"


@dataclass(frozen=True)
class ApplyDecision:
    proposal_id: str
    tier: ApplyTier
    reason: str


def evaluate_apply_policy(
    proposals: list[PatchProposal],
    verifications: list[VerificationResult],
) -> list[ApplyDecision]:
    verification_by_id = {item.proposal_id: item for item in verifications}
    decisions: list[ApplyDecision] = []
    for proposal in proposals:
        verification = verification_by_id.get(proposal.proposal_id)
        if verification is None or not verification.passed:
            decisions.append(
                ApplyDecision(
                    proposal_id=proposal.proposal_id,
                    tier=ApplyTier.REPORT_ONLY,
                    reason="verification failed",
                )
            )
            continue
        if proposal.action in {RecommendationAction.ADD, RecommendationAction.REMOVE}:
            decisions.append(
                ApplyDecision(
                    proposal_id=proposal.proposal_id,
                    tier=ApplyTier.HUMAN_REVIEW,
                    reason="structural change requires review",
                )
            )
            continue
        if (
            proposal.action is RecommendationAction.UPGRADE
            and proposal.confidence >= 0.85
            and proposal.target_skill_path
        ):
            decisions.append(
                ApplyDecision(
                    proposal_id=proposal.proposal_id,
                    tier=ApplyTier.SAFE_AUTO_APPLY,
                    reason="high-confidence narrow upgrade",
                )
            )
            continue
        if proposal.action is RecommendationAction.UPGRADE and not proposal.target_skill_path:
            decisions.append(
                ApplyDecision(
                    proposal_id=proposal.proposal_id,
                    tier=ApplyTier.CANDIDATE_PATCH,
                    reason="upgrade target path is unknown",
                )
            )
            continue
        decisions.append(
            ApplyDecision(
                proposal_id=proposal.proposal_id,
                tier=ApplyTier.CANDIDATE_PATCH,
                reason="patch is valid but still requires approval",
            )
        )
    return decisions
