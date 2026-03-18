"""Tests for OpenClaw reporting module."""

import json
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.core.models import (
    ConversationSignal,
    GovernanceRecommendation,
    RecommendationAction,
    ReportClassification,
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
    signals = [
        ConversationSignal(
            topic="test skill",
            evidence=("evidence1", "evidence2"),
            confidence=0.85,
            report_classification=ReportClassification.EVIDENCE_BACKED,
        ),
        ConversationSignal(
            topic="tooling gap",
            evidence=("requires repo automation",),
            confidence=0.72,
            report_classification=ReportClassification.TOOLING_NEEDED,
            missing_requirement="Add scheduled repository audit",
            tool_references=(
                "openai/codex",
                "openclaw/openclaw",
                "microsoft/vscode",
            ),
        ),
        ConversationSignal(
            topic="impossible request",
            evidence=("host API does not expose session memory deletion hook",),
            confidence=0.64,
            report_classification=ReportClassification.IMPOSSIBLE,
            missing_requirement="Delete active host memory without host support",
            prerequisites=("Host memory deletion API",),
        ),
        ConversationSignal(
            topic="forgotten request",
            evidence=("user requested install provenance cleanup but thread moved on",),
            confidence=0.6,
            report_classification=ReportClassification.UNRESOLVED,
            missing_requirement="Clean install provenance warning",
            next_step="Add npm install provenance validation flow",
        ),
        ConversationSignal(
            topic="weak candidate",
            evidence=("single anecdote without source material",),
            confidence=0.31,
            report_classification=ReportClassification.CANDIDATE_ONLY,
        ),
    ]

    write_governance_report(
        report_path,
        recommendations,
        host="openclaw",
        signals=signals,
    )

    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["schemaVersion"] == "2.0"
    assert payload["host"] == "openclaw"
    assert payload["recommendationCount"] == 2
    assert len(payload["recommendations"]) == 2
    assert payload["summary"]["evidenceBackedCount"] == 1
    assert payload["summary"]["candidateOnlyCount"] == 1
    assert payload["summary"]["unresolvedRequirementCount"] == 1
    assert payload["summary"]["toolingNeedCount"] == 1
    assert payload["summary"]["impossibleItemCount"] == 1

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

    evidence_item = payload["evidenceBackedEvolutions"][0]
    assert evidence_item["topic"] == "test skill"
    assert evidence_item["recommendationAction"] == "add"

    candidate_item = payload["candidateOnly"][0]
    assert candidate_item["topic"] == "weak candidate"

    unresolved_item = payload["unresolvedRequirements"][0]
    assert unresolved_item["requirement"] == "Clean install provenance warning"
    assert unresolved_item["nextStep"] == "Add npm install provenance validation flow"

    tooling_item = payload["toolingNeeded"][0]
    assert tooling_item["requirement"] == "Add scheduled repository audit"
    assert tooling_item["referenceProjects"] == [
        "openai/codex",
        "openclaw/openclaw",
        "microsoft/vscode",
    ]

    impossible_item = payload["impossibleItems"][0]
    assert impossible_item["requirement"] == "Delete active host memory without host support"
    assert impossible_item["prerequisites"] == ["Host memory deletion API"]


def test_write_governance_report_creates_parent_directories(tmp_path: Path) -> None:
    """Test that report creates parent directories if needed."""
    report_path = tmp_path / "nested" / "deep" / "report.json"
    recommendations: list[GovernanceRecommendation] = []

    write_governance_report(report_path, recommendations, host="openclaw", signals=[])

    assert report_path.exists()


def test_write_governance_report_includes_timestamp(tmp_path: Path) -> None:
    """Test that report includes generation timestamp."""
    report_path = tmp_path / "report.json"
    recommendations: list[GovernanceRecommendation] = []

    before = datetime.now(timezone.utc)
    write_governance_report(report_path, recommendations, host="openclaw", signals=[])
    after = datetime.now(timezone.utc)

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    generated_at = datetime.fromisoformat(payload["generatedAt"])

    assert before <= generated_at <= after


def test_write_governance_report_empty_recommendations(tmp_path: Path) -> None:
    """Test that empty recommendations list works correctly."""
    report_path = tmp_path / "report.json"

    write_governance_report(report_path, [], host="openclaw", signals=[])

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["recommendationCount"] == 0
    assert payload["recommendations"] == []
    assert payload["evidenceBackedEvolutions"] == []
    assert payload["candidateOnly"] == []
    assert payload["unresolvedRequirements"] == []
    assert payload["toolingNeeded"] == []
    assert payload["impossibleItems"] == []
