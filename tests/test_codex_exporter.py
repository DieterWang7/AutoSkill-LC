import json
from pathlib import Path

from autoskill_lc.codex.exporter import ingest_codex_session


def test_ingest_codex_session_converts_jsonl_messages_to_signal(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    session_path = tmp_path / "rollout-1.jsonl"
    session_path.write_text(
        "\n".join(
            [
                json.dumps({"type": "session_meta", "sessionId": "sess-1", "cwd": "/repo"}),
                json.dumps(
                    {
                        "type": "message",
                        "message": {"role": "user", "content": "Refine the release note workflow."},
                        "timestamp": "2026-03-18T09:00:00Z",
                    }
                ),
                json.dumps(
                    {
                        "type": "message",
                        "message": {"role": "assistant", "content": "I will update the workflow."},
                        "timestamp": "2026-03-18T09:00:05Z",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = ingest_codex_session(codex_home, session_path)
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))

    assert result.session_id == "sess-1"
    assert result.signal_count == 1
    assert payload[0]["conversation_id"] == "sess-1"
    assert payload[0]["conversation_title"] == "Refine the release note workflow."
    assert payload[0]["topic"] == "Refine the release note workflow."
    assert payload[0]["last_observed_at"] == "2026-03-18T09:00:05+00:00"
    assert payload[0]["evidence"][0].startswith("user: ")
