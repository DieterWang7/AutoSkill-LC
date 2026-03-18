import json
from pathlib import Path

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
