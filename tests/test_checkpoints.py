import json
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.core.models import (
    ConversationSignal,
    GovernanceRecommendation,
    RecommendationAction,
)
from autoskill_lc.runtime.checkpoints import (
    filter_signals_for_incremental_run,
    read_checkpoint_state,
    write_checkpoint_entry,
)


def test_write_checkpoint_entry_creates_markdown_log_with_latest_entry_first(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.md"
    recommendations = [
        GovernanceRecommendation(
            action=RecommendationAction.UPGRADE,
            topic="nightly cleanup",
            rationale="Repeated corrections justify an upgrade.",
            confidence=0.82,
            skill_id="skill-cleanup",
        ),
        GovernanceRecommendation(
            action=RecommendationAction.REMOVE,
            topic="old cleanup",
            rationale="Deprecated long enough.",
            confidence=0.73,
            skill_id="skill-old",
        ),
    ]
    signals = [
        ConversationSignal(
            topic="nightly cleanup",
            conversation_id="conv-42",
            conversation_title="Nightly cleanup workflow",
            last_observed_at=datetime(2026, 3, 18, 12, 30, tzinfo=timezone.utc),
        )
    ]

    write_checkpoint_entry(
        checkpoint_path,
        host="openclaw",
        signals=signals,
        recommendations=recommendations,
        run_at=datetime(2026, 3, 18, 13, 0, tzinfo=timezone.utc),
    )

    content = checkpoint_path.read_text(encoding="utf-8")
    assert "last_processed_at: 2026-03-18T12:30:00+00:00" in content
    assert "## 0001 | 2026-03-18T13:00:00+00:00 | openclaw" in content
    assert "- 对话ID: conv-42" in content
    assert "- 对话标题: Nightly cleanup workflow" in content
    assert "- 升级的 skill: skill-cleanup" in content
    assert "- 卸载的 skill: skill-old" in content


def test_filter_signals_for_incremental_run_uses_checkpoint_timestamp() -> None:
    previous_state = {
        "last_processed_at": "2026-03-18T12:00:00+00:00",
        "sequence": 3,
    }
    signals = [
        ConversationSignal(
            topic="old",
            last_observed_at=datetime(2026, 3, 18, 11, 0, tzinfo=timezone.utc),
        ),
        ConversationSignal(
            topic="new",
            last_observed_at=datetime(2026, 3, 18, 13, 0, tzinfo=timezone.utc),
        ),
        ConversationSignal(
            topic="unknown-time",
            last_observed_at=None,
        ),
    ]

    filtered = filter_signals_for_incremental_run(signals, previous_state)

    assert [item.topic for item in filtered] == ["new", "unknown-time"]


def test_filter_signals_for_incremental_run_accepts_naive_checkpoint_timestamp() -> None:
    local_tz = datetime.now().astimezone().tzinfo or timezone.utc
    previous_state = {
        "last_processed_at": "2026-03-18T12:00:00",
        "sequence": 3,
    }
    signals = [
        ConversationSignal(
            topic="old",
            last_observed_at=datetime(2026, 3, 18, 11, 0, tzinfo=local_tz),
        ),
        ConversationSignal(
            topic="new",
            last_observed_at=datetime(2026, 3, 18, 13, 0, tzinfo=local_tz),
        ),
    ]

    filtered = filter_signals_for_incremental_run(signals, previous_state)

    assert [item.topic for item in filtered] == ["new"]


def test_filter_signals_for_incremental_run_repairs_legacy_future_utc_timestamp() -> None:
    local_tz = datetime.now().astimezone().tzinfo or timezone.utc
    previous_state = {
        "last_processed_at": "2026-03-18T09:39:00+00:00",
        "sequence": 3,
    }
    signals = [
        ConversationSignal(
            topic="old",
            last_observed_at=datetime(2026, 3, 18, 9, 30, tzinfo=local_tz),
        ),
        ConversationSignal(
            topic="new",
            last_observed_at=datetime(2026, 3, 18, 10, 0, tzinfo=local_tz),
        ),
    ]

    filtered = filter_signals_for_incremental_run(signals, previous_state)

    assert [item.topic for item in filtered] == ["new"]


def test_read_checkpoint_state_returns_defaults_when_missing(tmp_path: Path) -> None:
    state = read_checkpoint_state(tmp_path / "checkpoint.md")
    assert state["sequence"] == 0
    assert state["last_processed_at"] is None


def test_write_checkpoint_entry_keeps_previous_last_processed_at_when_no_new_signal(
    tmp_path: Path,
) -> None:
    checkpoint_path = tmp_path / "checkpoint.md"
    checkpoint_path.write_text(
        "---\nsequence: 1\nlast_processed_at: 2026-03-18T12:30:00+00:00\n---\n\n# AutoSkill-LC Checkpoints\n\n",
        encoding="utf-8",
    )

    write_checkpoint_entry(
        checkpoint_path,
        host="codex",
        signals=[],
        recommendations=[],
        run_at=datetime(2026, 3, 18, 13, 0, tzinfo=timezone.utc),
    )

    content = checkpoint_path.read_text(encoding="utf-8")
    assert "sequence: 2" in content
    assert "last_processed_at: 2026-03-18T12:30:00+00:00" in content


def test_write_checkpoint_entry_uses_run_time_when_signal_has_no_timestamp(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.md"

    write_checkpoint_entry(
        checkpoint_path,
        host="openclaw",
        signals=[
            ConversationSignal(
                topic="hello",
                conversation_id="conv-1",
                conversation_title="hello",
            )
        ],
        recommendations=[],
        run_at=datetime(2026, 3, 18, 13, 0, tzinfo=timezone.utc),
    )

    content = checkpoint_path.read_text(encoding="utf-8")
    assert "last_processed_at: 2026-03-18T13:00:00+00:00" in content
