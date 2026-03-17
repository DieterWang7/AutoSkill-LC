from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from autoskill_lc.core.models import (
    ConversationSignal,
    GovernanceRecommendation,
    RecommendationAction,
    SkillRecord,
)


@dataclass(frozen=True)
class GovernancePolicy:
    min_new_skill_confidence: float = 0.75
    min_new_skill_runs: int = 2
    min_upgrade_confidence: float = 0.6
    stale_after_days: int = 45
    removable_after_days: int = 120


class GovernanceEngine:
    """Host-neutral recommendation engine for skill lifecycle decisions."""

    def __init__(self, policy: GovernancePolicy | None = None) -> None:
        self.policy = policy or GovernancePolicy()

    def analyze(
        self,
        signals: list[ConversationSignal],
        skills: list[SkillRecord],
        *,
        now: datetime | None = None,
    ) -> list[GovernanceRecommendation]:
        current_time = now or datetime.now(timezone.utc)
        touched_skill_ids = {
            signal.existing_skill_id for signal in signals if signal.existing_skill_id
        }
        recommendations: list[GovernanceRecommendation] = []

        for signal in signals:
            recommendation = self._from_signal(signal)
            if recommendation is not None:
                recommendations.append(recommendation)

        for skill in skills:
            if skill.skill_id in touched_skill_ids:
                continue
            recommendation = self._from_skill_staleness(skill, current_time)
            if recommendation is not None:
                recommendations.append(recommendation)

        return recommendations

    def _from_signal(
        self,
        signal: ConversationSignal,
    ) -> GovernanceRecommendation | None:
        if signal.existing_skill_id and signal.explicit_uninstall_request:
            return GovernanceRecommendation(
                action=RecommendationAction.REMOVE,
                topic=signal.topic,
                rationale="The host conversation explicitly requested removal.",
                confidence=max(signal.confidence, 0.9),
                skill_id=signal.existing_skill_id,
                evidence=signal.evidence,
            )

        if signal.existing_skill_id and signal.superseded_by:
            return GovernanceRecommendation(
                action=RecommendationAction.DEPRECATE,
                topic=signal.topic,
                rationale="A newer replacement skill supersedes the current one.",
                confidence=max(signal.confidence, 0.8),
                skill_id=signal.existing_skill_id,
                replacement_skill_id=signal.superseded_by,
                evidence=signal.evidence,
            )

        if signal.existing_skill_id and (
            signal.corrections > 0
            or signal.confidence >= self.policy.min_upgrade_confidence
        ):
            return GovernanceRecommendation(
                action=RecommendationAction.UPGRADE,
                topic=signal.topic,
                rationale="Repeated corrections indicate the skill should evolve.",
                confidence=max(signal.confidence, 0.65),
                skill_id=signal.existing_skill_id,
                evidence=signal.evidence,
            )

        if (
            signal.existing_skill_id is None
            and signal.confidence >= self.policy.min_new_skill_confidence
            and signal.observed_runs >= self.policy.min_new_skill_runs
        ):
            return GovernanceRecommendation(
                action=RecommendationAction.ADD,
                topic=signal.topic,
                rationale="A recurring pattern without coverage suggests a new skill.",
                confidence=signal.confidence,
                evidence=signal.evidence,
            )

        return None

    def _from_skill_staleness(
        self,
        skill: SkillRecord,
        now: datetime,
    ) -> GovernanceRecommendation | None:
        if skill.last_used_at is None:
            return None

        age = now - skill.last_used_at
        removable_after = timedelta(days=self.policy.removable_after_days)
        stale_after = timedelta(days=self.policy.stale_after_days)

        if skill.status == "deprecated" and age >= removable_after:
            return GovernanceRecommendation(
                action=RecommendationAction.REMOVE,
                topic=skill.title,
                rationale="The deprecated skill remained unused beyond the removal window.",
                confidence=0.85,
                skill_id=skill.skill_id,
            )

        if skill.status == "active" and age >= stale_after:
            return GovernanceRecommendation(
                action=RecommendationAction.DEPRECATE,
                topic=skill.title,
                rationale="The skill has been inactive long enough to enter review.",
                confidence=0.7,
                skill_id=skill.skill_id,
            )

        return None

