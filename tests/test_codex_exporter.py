import json
from pathlib import Path

import pytest

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


def test_ingest_codex_session_extracts_tooling_and_unresolved_signals(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    session_path = tmp_path / "rollout-2.jsonl"
    session_path.write_text(
        "\n".join(
            [
                json.dumps({"type": "session_meta", "sessionId": "sess-2", "title": "autoskill follow-up"}),
                json.dumps(
                    {
                        "type": "message",
                        "message": {
                            "role": "user",
                            "content": "请继续实现 GitHub 安装和服务器自动同步，这需要工具实现。",
                        },
                        "timestamp": "2026-03-18T10:00:00Z",
                    }
                ),
                json.dumps(
                    {
                        "type": "message",
                        "message": {
                            "role": "assistant",
                            "content": "还没完成，下一步需要补服务器同步流程。",
                        },
                        "timestamp": "2026-03-18T10:00:05Z",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = ingest_codex_session(codex_home, session_path)
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))

    assert result.signal_count == 3
    classifications = {item.get("report_classification"): item for item in payload}
    assert classifications["candidate_only"]["topic"] == "autoskill follow-up"
    assert classifications["tooling_needed"]["missing_requirement"] == "请继续实现 GitHub 安装和服务器自动同步，这需要工具实现。"
    assert classifications["tooling_needed"]["tool_references"] == [
        "openai/codex",
        "openclaw/openclaw",
        "microsoft/vscode",
    ]
    assert classifications["unresolved"]["next_step"] == "还没完成，下一步需要补服务器同步流程。"


def test_ingest_codex_session_extracts_impossible_signal(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    session_path = tmp_path / "rollout-3.jsonl"
    session_path.write_text(
        "\n".join(
            [
                json.dumps({"type": "session_meta", "sessionId": "sess-3"}),
                json.dumps(
                    {
                        "type": "message",
                        "message": {
                            "role": "assistant",
                            "content": "这个需求当前无法实现，因为宿主没有提供对应 API。",
                        },
                        "timestamp": "2026-03-18T11:00:00Z",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = ingest_codex_session(codex_home, session_path)
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))

    impossible = [item for item in payload if item.get("report_classification") == "impossible"]
    assert len(impossible) == 1
    assert impossible[0]["missing_requirement"] == "这个需求当前无法实现，因为宿主没有提供对应 API。"
    assert impossible[0]["prerequisites"] == ["Host or tool API support"]


def test_ingest_codex_session_skips_greeting_only_conversation(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    session_path = tmp_path / "rollout-greeting.jsonl"
    session_path.write_text(
        "\n".join(
            [
                json.dumps({"type": "session_meta", "sessionId": "sess-greeting"}),
                json.dumps(
                    {
                        "type": "message",
                        "message": {"role": "user", "content": "hello"},
                        "timestamp": "2026-03-18T10:00:00Z",
                    }
                ),
                json.dumps(
                    {
                        "type": "message",
                        "message": {"role": "assistant", "content": "hi"},
                        "timestamp": "2026-03-18T10:00:01Z",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="No valid conversation signals"):
        ingest_codex_session(codex_home, session_path)
