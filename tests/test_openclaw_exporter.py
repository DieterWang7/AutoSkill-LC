import json
from pathlib import Path

import pytest

from autoskill_lc.openclaw.exporter import ingest_openclaw_export


def test_ingest_openclaw_export_converts_conversation_messages_to_signal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    export_path = tmp_path / "conversation.json"
    export_path.write_text(
        json.dumps(
            {
                "sessionId": "session-42",
                "title": "weekly cleanup workflow",
                "messages": [
                    {"role": "user", "content": "Please refine the cleanup workflow."},
                    {"role": "assistant", "content": "I will update the workflow and notes."},
                ],
                "confidence": 0.81,
                "observed_runs": 4,
                "updated_at": "2026-03-18T08:30:00Z",
            }
        ),
        encoding="utf-8",
    )

    result = ingest_openclaw_export(workspace, export_path)
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))

    assert result.session_id == "session-42"
    assert result.signal_count == 1
    assert payload[0]["conversation_id"] == "session-42"
    assert payload[0]["conversation_title"] == "weekly cleanup workflow"
    assert payload[0]["topic"] == "weekly cleanup workflow"
    assert payload[0]["confidence"] == 0.81
    assert payload[0]["last_observed_at"] == "2026-03-18T08:30:00+00:00"
    assert payload[0]["evidence"][0].startswith("user: ")


def test_ingest_openclaw_export_preserves_normalized_signals(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    export_path = tmp_path / "signals.json"
    export_path.write_text(
        json.dumps(
            {
                "signals": [
                    {
                        "topic": "release-note drafting",
                        "evidence": ["user asked for the same release-note flow again"],
                        "confidence": 0.93,
                        "observed_runs": 3,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = ingest_openclaw_export(workspace, export_path)
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))

    assert result.signal_count == 1
    assert payload[0]["topic"] == "release-note drafting"
    assert payload[0]["observed_runs"] == 3


def test_ingest_openclaw_export_extracts_report_classifications_and_timestamps(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    export_path = tmp_path / "conversation.json"
    export_path.write_text(
        json.dumps(
            {
                "id": "oc-1",
                "title": "autoskill nightly sync",
                "messages": [
                    {
                        "role": "user",
                        "content": "请继续实现 GitHub 安装和服务器自动同步，这需要工具实现。",
                        "created_at": "2026-03-18T10:00:00Z",
                    },
                    {
                        "role": "assistant",
                        "content": "这个需求当前无法实现，因为宿主没有提供对应 API。",
                        "updated_at": "2026-03-18T10:03:00Z",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = ingest_openclaw_export(workspace, export_path)
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))

    assert result.signal_count == 4
    assert payload[0]["last_observed_at"] == "2026-03-18T10:03:00+00:00"
    tooling = [item for item in payload if item.get("report_classification") == "tooling_needed"]
    impossible = [item for item in payload if item.get("report_classification") == "impossible"]
    unresolved = [item for item in payload if item.get("report_classification") == "unresolved"]
    assert len(tooling) == 1
    assert len(impossible) == 1
    assert len(unresolved) == 1


def test_ingest_openclaw_export_skips_greeting_only_conversation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    export_path = tmp_path / "conversation.json"
    export_path.write_text(
        json.dumps(
            {
                "id": "oc-greeting",
                "messages": [
                    {"role": "user", "content": "hello", "created_at": "2026-03-18T10:00:00Z"},
                    {"role": "assistant", "content": "hi", "updated_at": "2026-03-18T10:00:01Z"},
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="No valid conversation signals"):
        ingest_openclaw_export(workspace, export_path)


def test_ingest_openclaw_export_derives_compact_topic_from_long_request(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    export_path = tmp_path / "conversation.json"
    export_path.write_text(
        json.dumps(
            {
                "id": "oc-compact-topic",
                "messages": [
                    {
                        "role": "user",
                        "content": "请继续实现 GitHub 安装和服务器自动同步，这需要工具实现。",
                        "created_at": "2026-03-18T10:00:00Z",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = ingest_openclaw_export(workspace, export_path)
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))

    assert payload[0]["topic"] == "GitHub 安装和服务器自动同步"
