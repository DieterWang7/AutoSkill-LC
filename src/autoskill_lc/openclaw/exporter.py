from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from autoskill_lc.openclaw.config import OpenClawPaths


DEFAULT_SIGNAL_CONFIDENCE = 0.55
DEFAULT_OBSERVED_RUNS = 1
MAX_EVIDENCE_ITEMS = 6
MAX_EVIDENCE_CHARS = 240
FALLBACK_TOPIC = "openclaw-conversation"


@dataclass(frozen=True)
class SignalIngestResult:
    input_path: Path
    output_path: Path
    signal_count: int
    session_id: str


def ingest_openclaw_export(
    workspace_dir: Path,
    input_path: Path,
    *,
    session_id: str | None = None,
    topic: str | None = None,
) -> SignalIngestResult:
    paths = OpenClawPaths.from_workspace(workspace_dir)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    signals = _extract_signals(payload, session_id=session_id, topic=topic)
    if not signals:
        raise ValueError("No valid conversation signals could be extracted from the input.")

    signals_dir = paths.data_dir / "signals"
    signals_dir.mkdir(parents=True, exist_ok=True)

    resolved_session_id = session_id or _derive_session_id(payload) or input_path.stem
    output_path = signals_dir / f"{_slugify(resolved_session_id)}.json"
    _write_json_atomic(output_path, signals)
    return SignalIngestResult(
        input_path=input_path,
        output_path=output_path,
        signal_count=len(signals),
        session_id=resolved_session_id,
    )


def _extract_signals(
    payload: object,
    *,
    session_id: str | None,
    topic: str | None,
) -> list[dict[str, object]]:
    if isinstance(payload, dict):
        raw_signals = payload.get("signals")
        if isinstance(raw_signals, list):
            return [
                _normalize_signal(item, topic=topic)
                for item in raw_signals
                if isinstance(item, dict)
            ]

        conversations = payload.get("conversations")
        if isinstance(conversations, list):
            return [
                _conversation_to_signal(item, session_id=session_id, topic=topic)
                for item in conversations
                if isinstance(item, dict)
            ]

        return [_conversation_to_signal(payload, session_id=session_id, topic=topic)]

    if isinstance(payload, list):
        return [
            _conversation_to_signal(item, session_id=session_id, topic=topic)
            for item in payload
            if isinstance(item, dict)
        ]

    return []


def _normalize_signal(raw: dict[str, object], *, topic: str | None) -> dict[str, object]:
    normalized_topic = _first_non_empty(topic, _coerce_text(raw.get("topic")), FALLBACK_TOPIC)
    return {
        "conversation_id": _optional_text(
            raw.get("conversation_id")
            or raw.get("session_id")
            or raw.get("sessionId")
            or raw.get("id")
        ),
        "conversation_title": _first_non_empty(
            _coerce_text(raw.get("conversation_title")),
            _coerce_text(raw.get("title")),
        ),
        "topic": normalized_topic,
        "evidence": _coerce_evidence(raw.get("evidence")),
        "confidence": _coerce_float(raw.get("confidence"), DEFAULT_SIGNAL_CONFIDENCE),
        "observed_runs": _coerce_int(raw.get("observed_runs"), DEFAULT_OBSERVED_RUNS),
        "existing_skill_id": _optional_text(raw.get("existing_skill_id")),
        "corrections": _coerce_int(raw.get("corrections"), 0),
        "explicit_uninstall_request": bool(raw.get("explicit_uninstall_request", False)),
        "superseded_by": _optional_text(raw.get("superseded_by")),
        "last_observed_at": _optional_timestamp(
            raw.get("last_observed_at") or raw.get("updated_at")
        ),
    }


def _conversation_to_signal(
    raw: dict[str, object],
    *,
    session_id: str | None,
    topic: str | None,
) -> dict[str, object]:
    messages = _coerce_messages(raw.get("messages") or raw.get("turns") or raw.get("conversation"))
    derived_topic = _first_non_empty(
        topic,
        _coerce_text(raw.get("topic")),
        _coerce_text(raw.get("title")),
        _derive_topic_from_messages(messages),
        session_id,
        _derive_session_id(raw),
        FALLBACK_TOPIC,
    )
    evidence = _coerce_evidence(raw.get("evidence"))
    if not evidence:
        evidence = _evidence_from_messages(messages)

    return {
        "conversation_id": _first_non_empty(
            _coerce_text(raw.get("conversation_id")),
            _coerce_text(raw.get("session_id")),
            _coerce_text(raw.get("sessionId")),
            _coerce_text(raw.get("id")),
        ),
        "conversation_title": _first_non_empty(
            _coerce_text(raw.get("conversation_title")),
            _coerce_text(raw.get("title")),
            derived_topic,
        ),
        "topic": derived_topic,
        "evidence": evidence,
        "confidence": _coerce_float(raw.get("confidence"), DEFAULT_SIGNAL_CONFIDENCE),
        "observed_runs": _coerce_int(raw.get("observed_runs"), DEFAULT_OBSERVED_RUNS),
        "existing_skill_id": _optional_text(raw.get("existing_skill_id")),
        "corrections": _coerce_int(raw.get("corrections"), 0),
        "explicit_uninstall_request": bool(raw.get("explicit_uninstall_request", False)),
        "superseded_by": _optional_text(raw.get("superseded_by")),
        "last_observed_at": _optional_timestamp(
            raw.get("last_observed_at")
            or raw.get("updated_at")
            or raw.get("timestamp")
        ),
    }


def _coerce_messages(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    messages: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        role = _first_non_empty(
            _coerce_text(item.get("role")),
            _coerce_text(item.get("sender")),
            "unknown",
        )
        text = _first_non_empty(
            _coerce_text(item.get("content")),
            _coerce_text(item.get("text")),
            _coerce_text(item.get("message")),
        )
        if text:
            messages.append({"role": role, "text": text})
    return messages


def _evidence_from_messages(messages: list[dict[str, str]]) -> tuple[str, ...]:
    evidence: list[str] = []
    for message in messages[:MAX_EVIDENCE_ITEMS]:
        evidence.append(f'{message["role"]}: {_trim_text(message["text"])}')
    return tuple(evidence)


def _derive_topic_from_messages(messages: list[dict[str, str]]) -> str | None:
    for message in messages:
        if message["role"].lower() in {"user", "human"}:
            return _trim_text(message["text"], length=80)
    if messages:
        return _trim_text(messages[0]["text"], length=80)
    return None


def _derive_session_id(value: object) -> str | None:
    if isinstance(value, dict):
        return _optional_text(value.get("session_id") or value.get("sessionId") or value.get("id"))
    return None


def _coerce_evidence(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = _trim_text(value)
        return (text,) if text else ()
    if isinstance(value, list):
        items = [_trim_text(str(item)) for item in value if str(item).strip()]
        return tuple(items[:MAX_EVIDENCE_ITEMS])
    return (_trim_text(str(value)),)


def _coerce_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_text(value: object) -> str | None:
    return _coerce_text(value)


def _coerce_float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _optional_timestamp(value: object) -> str | None:
    text = _coerce_text(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.isoformat()


def _first_non_empty(*values: str | None) -> str:
    for value in values:
        if value:
            return value
    return FALLBACK_TOPIC


def _trim_text(value: str, *, length: int = MAX_EVIDENCE_CHARS) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= length:
        return text
    return text[: length - 1].rstrip() + "..."


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    slug = slug.strip("-._")
    return slug or "autoskill-openclaw"


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)
