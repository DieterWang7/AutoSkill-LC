from datetime import datetime, timedelta, timezone

from autoskill_lc.core.engine import GovernanceEngine, GovernancePolicy
from autoskill_lc.core.models import ConversationSignal, RecommendationAction, SkillRecord


def test_recommends_new_skill_for_recurring_uncovered_pattern() -> None:
    engine = GovernanceEngine(GovernancePolicy())
    signals = [
        ConversationSignal(
            topic="git release notes",
            evidence=("user repeatedly asks for the same release-note workflow",),
            confidence=0.91,
            observed_runs=3,
        )
    ]

    recommendations = engine.analyze(signals, [])

    assert len(recommendations) == 1
    assert recommendations[0].action == RecommendationAction.ADD
    assert recommendations[0].topic == "git release notes"


def test_recommends_upgrade_for_existing_skill_with_corrections() -> None:
    engine = GovernanceEngine()
    signals = [
        ConversationSignal(
            topic="openclaw cron maintenance",
            evidence=("user corrected the maintenance window and cleanup rule",),
            confidence=0.7,
            observed_runs=2,
            existing_skill_id="skill-openclaw-maintenance",
            corrections=2,
        )
    ]

    recommendations = engine.analyze(signals, [])

    assert len(recommendations) == 1
    assert recommendations[0].action == RecommendationAction.UPGRADE
    assert recommendations[0].skill_id == "skill-openclaw-maintenance"


def test_recommends_deprecate_for_stale_active_skill() -> None:
    engine = GovernanceEngine()
    now = datetime(2026, 3, 18, tzinfo=timezone.utc)
    skills = [
        SkillRecord(
            skill_id="skill-unused",
            title="legacy workflow",
            version="1.2.0",
            usage_count=4,
            last_used_at=now - timedelta(days=60),
            status="active",
        )
    ]

    recommendations = engine.analyze([], skills, now=now)

    assert len(recommendations) == 1
    assert recommendations[0].action == RecommendationAction.DEPRECATE
    assert recommendations[0].skill_id == "skill-unused"


def test_recommends_remove_for_deprecated_skill_past_removal_window() -> None:
    engine = GovernanceEngine()
    now = datetime(2026, 3, 18, tzinfo=timezone.utc)
    skills = [
        SkillRecord(
            skill_id="skill-deprecated",
            title="legacy prompt wrapper",
            version="0.8.0",
            usage_count=11,
            last_used_at=now - timedelta(days=150),
            status="deprecated",
        )
    ]

    recommendations = engine.analyze([], skills, now=now)

    assert len(recommendations) == 1
    assert recommendations[0].action == RecommendationAction.REMOVE
    assert recommendations[0].skill_id == "skill-deprecated"
