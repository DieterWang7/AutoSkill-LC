from __future__ import annotations

from dataclasses import dataclass

from autoskill_lc.core.patches import PatchProposal
from autoskill_lc.core.models import RecommendationAction


@dataclass(frozen=True)
class VerificationResult:
    proposal_id: str
    passed: bool
    issues: tuple[str, ...]


def verify_patch_proposals(proposals: list[PatchProposal]) -> list[VerificationResult]:
    results: list[VerificationResult] = []
    for proposal in proposals:
        issues: list[str] = []
        if not proposal.evidence:
            issues.append("missing evidence")
        if not proposal.header_note:
            issues.append("missing header note")
        if (
            proposal.action
            in {RecommendationAction.UPGRADE, RecommendationAction.DEPRECATE, RecommendationAction.REMOVE}
            and not proposal.target_skill_id
        ):
            issues.append("missing target skill")
        if proposal.confidence < 0.5:
            issues.append("confidence too low")
        results.append(
            VerificationResult(
                proposal_id=proposal.proposal_id,
                passed=not issues,
                issues=tuple(issues),
            )
        )
    return results
