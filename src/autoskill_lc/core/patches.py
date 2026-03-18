from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from autoskill_lc.core.models import GovernanceRecommendation, RecommendationAction
from autoskill_lc.core.skill_mapper import SkillMatch


@dataclass(frozen=True)
class PatchProposal:
    proposal_id: str
    topic: str
    action: RecommendationAction
    target_skill_id: str | None
    target_skill_title: str | None
    confidence: float
    checkpoint_sequence: int
    header_note: str
    operations: tuple[str, ...]
    evidence: tuple[str, ...]


def build_patch_proposals(
    recommendations: list[GovernanceRecommendation],
    mappings: dict[str, SkillMatch],
    *,
    checkpoint_state: dict[str, object] | None = None,
    generated_at: datetime | None = None,
) -> list[PatchProposal]:
    report_time = generated_at or datetime.now(timezone.utc)
    sequence = int((checkpoint_state or {}).get("sequence", 0))
    proposals: list[PatchProposal] = []
    for index, recommendation in enumerate(recommendations, start=1):
        mapping = mappings.get(recommendation.topic)
        target_skill_id = recommendation.skill_id or (mapping.skill_id if mapping else None)
        target_skill_title = mapping.skill_title if mapping else None
        proposals.append(
            PatchProposal(
                proposal_id=f"patch-{sequence + 1:04d}-{index:02d}",
                topic=recommendation.topic,
                action=recommendation.action,
                target_skill_id=target_skill_id,
                target_skill_title=target_skill_title,
                confidence=recommendation.confidence,
                checkpoint_sequence=sequence,
                header_note=_header_note(report_time, recommendation),
                operations=_operations_for(recommendation.action, target_skill_id),
                evidence=recommendation.evidence,
            )
        )
    return proposals


def _header_note(report_time: datetime, recommendation: GovernanceRecommendation) -> str:
    return (
        f"optimized_at={report_time.isoformat()} | reason={recommendation.rationale} | "
        f"topic={recommendation.topic}"
    )


def _operations_for(
    action: RecommendationAction,
    target_skill_id: str | None,
) -> tuple[str, ...]:
    if action is RecommendationAction.ADD:
        return ("create_skill_stub", "add_change_note")
    if action is RecommendationAction.UPGRADE:
        return ("update_skill_section", "add_change_note")
    if action is RecommendationAction.DEPRECATE:
        return ("mark_skill_deprecated", "add_change_note")
    if target_skill_id:
        return ("remove_skill_reference", "add_change_note")
    return ("review_required",)
