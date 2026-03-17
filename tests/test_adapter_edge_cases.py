"""Tests for adapter edge cases and error handling."""

import json
from pathlib import Path

from autoskill_lc.openclaw.adapter import OpenClawAdapter


def test_adapter_handles_missing_signals_dir(tmp_path: Path) -> None:
    """Test that adapter returns empty list when signals dir doesn't exist."""
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    signals = adapter.collect_signals()
    assert signals == []


def test_adapter_handles_empty_signals_dir(tmp_path: Path) -> None:
    """Test that adapter returns empty list when signals dir is empty."""
    signals_dir = tmp_path / "autoskill-lc" / "signals"
    signals_dir.mkdir(parents=True)
    
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    signals = adapter.collect_signals()
    assert signals == []


def test_adapter_handles_invalid_json(tmp_path: Path) -> None:
    """Test that adapter skips invalid JSON files."""
    signals_dir = tmp_path / "autoskill-lc" / "signals"
    signals_dir.mkdir(parents=True)
    (signals_dir / "invalid.json").write_text("not valid json", encoding="utf-8")
    
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    signals = adapter.collect_signals()
    assert signals == []


def test_adapter_handles_empty_json_file(tmp_path: Path) -> None:
    """Test that adapter handles empty JSON files."""
    signals_dir = tmp_path / "autoskill-lc" / "signals"
    signals_dir.mkdir(parents=True)
    (signals_dir / "empty.json").write_text("", encoding="utf-8")
    
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    signals = adapter.collect_signals()
    assert signals == []


def test_adapter_handles_non_list_json(tmp_path: Path) -> None:
    """Test that adapter skips JSON files that aren't lists."""
    signals_dir = tmp_path / "autoskill-lc" / "signals"
    signals_dir.mkdir(parents=True)
    (signals_dir / "object.json").write_text('{"not": "a list"}', encoding="utf-8")
    
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    signals = adapter.collect_signals()
    assert signals == []


def test_adapter_skips_signals_without_topic(tmp_path: Path) -> None:
    """Test that adapter skips signals with empty or missing topic."""
    signals_dir = tmp_path / "autoskill-lc" / "signals"
    signals_dir.mkdir(parents=True)
    (signals_dir / "no-topic.json").write_text(
        json.dumps([{"confidence": 0.9, "observed_runs": 3}]),
        encoding="utf-8",
    )
    (signals_dir / "empty-topic.json").write_text(
        json.dumps([{"topic": "   ", "confidence": 0.9}]),
        encoding="utf-8",
    )
    
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    signals = adapter.collect_signals()
    assert signals == []


def test_adapter_handles_malformed_signal_fields(tmp_path: Path) -> None:
    """Test that adapter handles malformed signal fields gracefully."""
    signals_dir = tmp_path / "autoskill-lc" / "signals"
    signals_dir.mkdir(parents=True)
    (signals_dir / "malformed.json").write_text(
        json.dumps([
 {"topic": "valid signal", "confidence": "not a number"},
            {"topic": "another valid", "observed_runs": "not an int"},
        ]),
        encoding="utf-8",
    )
    
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    # Should not raise, but may skip malformed entries
    signals = adapter.collect_signals()
    # Both should be skipped due to type conversion errors
    assert len(signals) == 0


def test_adapter_handles_missing_inventory(tmp_path: Path) -> None:
    """Test that adapter returns empty list when inventory doesn't exist."""
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    skills = adapter.list_skills()
    assert skills == []


def test_adapter_skills_require_all_required_fields(tmp_path: Path) -> None:
    """Test that adapter skips skills missing required fields."""
    inventory_dir = tmp_path / "autoskill-lc" / "inventory"
    inventory_dir.mkdir(parents=True)
    (inventory_dir / "skills.json").write_text(
        json.dumps([
            {"skill_id": "s1", "title": "Skill 1"},  # missing version
            {"skill_id": "s2", "version": "1.0.0"},  # missing title
            {"title": "Skill 3", "version": "1.0.0"},  # missing skill_id
            {"skill_id": "s4", "title": "Skill 4", "version": "1.0.0"},  # valid
        ]),
        encoding="utf-8",
    )
    
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    skills = adapter.list_skills()
    assert len(skills) == 1
    assert skills[0].skill_id == "s4"


def test_adapter_parses_last_used_at_datetime(tmp_path: Path) -> None:
    """Test that adapter correctly parses last_used_at datetime."""
    inventory_dir = tmp_path / "autoskill-lc" / "inventory"
    inventory_dir.mkdir(parents=True)
    (inventory_dir / "skills.json").write_text(
        json.dumps([
            {
                "skill_id": "s1",
                "title": "Skill 1",
                "version": "1.0.0",
                "last_used_at": "2026-03-18T10:30:00Z",
            },
            {
                "skill_id": "s2",
                "title": "Skill 2",
                "version": "1.0.0",
                "last_used_at": "2026-03-18T10:30:00+00:00",
            },
            {
                "skill_id": "s3",
                "title": "Skill 3",
                "version": "1.0.0",
                "last_used_at": None,
            },
        ]),
        encoding="utf-8",
    )
    
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    skills = adapter.list_skills()
    
    assert len(skills) == 3
    assert skills[0].last_used_at is not None
    assert skills[1].last_used_at is not None
    assert skills[2].last_used_at is None


def test_adapter_handles_invalid_datetime(tmp_path: Path) -> None:
    """Test that adapter handles invalid datetime strings."""
    inventory_dir = tmp_path / "autoskill-lc" / "inventory"
    inventory_dir.mkdir(parents=True)
    (inventory_dir / "skills.json").write_text(
        json.dumps([
            {
                "skill_id": "s1",
                "title": "Skill 1",
                "version": "1.0.0",
                "last_used_at": "not a valid date",
            },
        ]),
        encoding="utf-8",
    )
    
    adapter = OpenClawAdapter.for_workspace(tmp_path)
    skills = adapter.list_skills()
    
    assert len(skills) == 1
    assert skills[0].last_used_at is None
