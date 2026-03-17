from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from autoskill_lc.codex.config import CodexPaths


DEFAULT_SIGNAL_CONFIDENCE = 0.5
DEFAULT_OBSERVED_RUNS = 1
MAX_EVIDENCE_ITEMS = 6
MAX_EVIDENCE_CHARS = 240
FALLBACK_TOPIC = "codex-session"


@dataclass(frozen=True)
class SignalIngestResult:
    input_path: Path
    output_path: Path
    signal_count: int
    session_id: str


def ingest_codex_session(
    codex_home: Path,
    input_path: Path,
    *,
    session_id: str | None = None,
    topic: str | None = None,
) -> SignalIngestResult:
    paths = CodexPaths.from_home(codex_home)
    lines = input_path.read_text(encoding="utf-8").splitlines()
    events = _parse_jsonl(lines)
    signal = _events_to_signal(events, session_id=session_id, topic=topic, fallback_id=input_path.stem)

    signals_dir = paths.data_dir / "signals"
    signals_dir.mkdir(parents=True, exist_ok=True)

    output_path = signals_dir / f"{_slugify(signal['session_id'])}.json"
    payload = [_finalize_signal(signal)]
    _write_json_atomic(output_path, payload)
    return SignalIngestResult(
        input_path=input_path,
        output_path=output_path,
        signal_count=1,
        session_id=signal["session_id"],
    )


def ingest_codex_sessions_directory(
    codex_home: Path,
    sessions_dir: Path | None = None,
) -> list[SignalIngestResult]:
    paths = CodexPaths.from_home(codex_home)
    root = (sessions_dir or paths.sessions_dir).expanduser().resolve()
    results: list[SignalIngestResult] = []
    if not root.exists():
        return results

    for path in sorted(root.rglob("*.jsonl")):
        results.append(ingest_codex_session(codex_home, path))
    return results


def _parse_jsonl(lines: list[str]) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(raw, dict):
            events.append(raw)
    return events


def _events_to_signal(
    events: list[dict[str, object]],
    *,
    session_id: str | None,
    topic: str | None,
    fallback_id: str,
) -> dict[str, object]:
    messages = _extract_messages(events)
    derived_session_id = session_id or _derive_session_id(events) or fallback_id
    derived_topic = _first_non_empty(
        topic,
        _derive_topic(events, messages),
        derived_session_id,
        FALLBACK_TOPIC,
    )
    return {
        "session_id": derived_session_id,
        "topic": derived_topic,
        "evidence": _evidence_from_messages(messages),
        "confidence": DEFAULT_SIGNAL_CONFIDENCE,
        "observed_runs": DEFAULT_OBSERVED_RUNS,
        "existing_skill_id": None,
        "corrections": 0,
        "explicit_uninstall_request": False,
        "superseded_by": None,
        "last_observed_at": _latest_timestamp(events),
    }


def _extract_messages(events: list[dict[str, object]]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for event in events:
        role, text = _extract_message(event)
        if text:
            messages.append({"role": role or "unknown", "text": text})
    return messages


def _extract_message(event: dict[str, object]) -> tuple[str | None, str | None]:
    direct_role = _optional_text(event.get("role"))
    direct_text = _extract_text_value(event.get("content"))
    if direct_role and direct_text:
        return direct_role, direct_text

    message = event.get("message")
    if isinstance(message, dict):
        role = _optional_text(message.get("role")) or direct_role
        text = _extract_text_value(message.get("content")) or _extract_text_value(message)
        if text:
            return role, text

    item = event.get("item")
    if isinstance(item, dict):
        role = _optional_text(item.get("role")) or _optional_text(item.get("sender"))
        text = _extract_text_value(item.get("content")) or _extract_text_value(item)
        if text:
            return role, text

    return direct_role, direct_text


def _extract_text_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            text = _extract_text_value(item)
            if text:
                parts.append(text)
        combined = " ".join(parts).strip()
        return combined or None
    if isinstance(value, dict):
        for key in ("text", "content", "message", "value"):
            text = _extract_text_value(value.get(key))
            if text:
                return text
    return None


def _derive_session_id(events: list[dict[str, object]]) -> str | None:
    for event in events:
        for key in ("session_id", "sessionId", "id"):
            value = _optional_text(event.get(key))
            if value:
                return value
        message = event.get("message")
        if isinstance(message, dict):
            for key in ("session_id", "sessionId", "id"):
                value = _optional_text(message.get(key))
                if value:
                    return value
    return None


def _derive_topic(events: list[dict[str, object]], messages: list[dict[str, str]]) -> str | None:
    for event in events:
        for key in ("title", "topic", "summary"):
            value = _optional_text(event.get(key))
            if value:
                return value
        message = event.get("message")
        if isinstance(message, dict):
            for key in ("title", "topic"):
                value = _optional_text(message.get(key))
                if value:
                    return value
    for message in messages:
        if message["role"].lower() in {"user", "human"}:
            return _trim_text(message["text"], length=80)
    if messages:
        return _trim_text(messages[0]["text"], length=80)
    return None


def _evidence_from_messages(messages: list[dict[str, str]]) -> tuple[str, ...]:
    evidence: list[str] = []
    for message in messages[:MAX_EVIDENCE_ITEMS]:
        evidence.append(f'{message["role"]}: {_trim_text(message["text"])}')
    return tuple(evidence)


def _latest_timestamp(events: list[dict[str, object]]) -> str | None:
    candidates: list[datetime] = []
    for event in events:
        for key in ("timestamp", "created_at", "updated_at", "time"):
            value = _optional_timestamp(event.get(key))
            if value:
                candidates.append(value)
        message = event.get("message")
        if isinstance(message, dict):
            for key in ("timestamp", "created_at", "updated_at"):
                value = _optional_timestamp(message.get(key))
                if value:
                    candidates.append(value)
    if not candidates:
        return None
    return max(candidates).isoformat()


def _optional_timestamp(value: object) -> datetime | None:
    text = _optional_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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
    return slug or "autoskill-codex"


def _finalize_signal(signal: dict[str, object]) -> dict[str, object]:
    return {
        "topic": signal["topic"],
        "evidence": signal["evidence"],
        "confidence": signal["confidence"],
        "observed_runs": signal["observed_runs"],
        "existing_skill_id": signal["existing_skill_id"],
        "corrections": signal["corrections"],
        "explicit_uninstall_request": signal["explicit_uninstall_request"],
        "superseded_by": signal["superseded_by"],
        "last_observed_at": signal["last_observed_at"],
    }


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)

