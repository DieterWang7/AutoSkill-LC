"""Tests for OpenClaw reporting module."""

import json
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.core.models import (
    GovernanceRecommendation,
    RecommendationAction,
)
from autoskill_lc.openclaw.reporting import write_governance_report


def test_write_governance_report_creates_structured_output(tmp_path: Path) -> None:
    """Test that report contains all required fields."""
    report_path = tmp_path / "report.json"
    recommendations = [
        GovernanceRecommendation(
            action=RecommendationAction.ADD,
            topic="test skill",
            rationale="test rationale",
            confidence=0.85,
            skill_id="skill-test",
            replacement_skill_id=None,
            evidence=("evidence1", "evidence2"),
        ),
        GovernanceRecommendation(
            action=RecommendationAction.UPGRADE,
            topic="upgrade skill",
            rationale="needs upgrade",
            confidence=0.75,
            skill_id="skill-upgrade",
            replacement_skill_id="skill-new",
            evidence=(),
        ),
    ]

    write_governance_report(report_path, recommendations, host="openclaw")

    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["host"] == "openclaw"
    assert payload["recommendationCount"] == 2
    assert len(payload["recommendations"]) == 2

    # Check first recommendation structure
    rec1 = payload["recommendations"][0]
    assert rec1["action"] == "add"
    assert rec1["topic"] == "test skill"
    assert rec1["confidence"] == 0.85
    assert rec1["rationale"] == "test rationale"
    assert rec1["skill_id"] == "skill-test"
    assert rec1["replacement_skill_id"] is None
    assert rec1["evidence"] == ["evidence1", "evidence2"]

    # Check second recommendation
    rec2 = payload["recommendations"][1]
    assert rec2["action"] == "upgrade"
    assert rec2["replacement_skill_id"] == "skill-new"


def test_write_governance_report_creates_parent_directories(tmp_path: Path) -> None:
    """Test that report creates parent directories if needed."""
    report_path = tmp_path / "nested" / "deep" / "report.json"
    recommendations: list[GovernanceRecommendation] = []

    write_governance_report(report_path, recommendations, host="openclaw")

    assert report_path.exists()


def test_write_governance_report_includes_timestamp(tmp_path: Path) -> None:
    """Test that report includes generation timestamp."""
    report_path = tmp_path / "report.json"
    recommendations: list[GovernanceRecommendation] = []

    before = datetime.now(timezone.utc)
    write_governance_report(report_path, recommendations, host="openclaw")
    after = datetime.now(timezone.utc)

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    generated_at = datetime.fromisoformat(payload["generatedAt"])

    assert before <= generated_at <= after


def test_write_governance_report_empty_recommendations(tmp_path: Path) -> None:
    """Test that empty recommendations list works correctly."""
    report_path = tmp_path / "report.json"

    write_governance_report(report_path, [], host="openclaw")

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["recommendationCount"] == 0
    assert payload["recommendations"] == []
