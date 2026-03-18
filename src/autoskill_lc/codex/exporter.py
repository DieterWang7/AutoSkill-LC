from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.codex.config import CodexPaths


DEFAULT_SIGNAL_CONFIDENCE = 0.5
DEFAULT_OBSERVED_RUNS = 1
MAX_EVIDENCE_ITEMS = 6
MAX_EVIDENCE_CHARS = 240
FALLBACK_TOPIC = "codex-session"
TOOL_REFERENCE_DEFAULTS = (
    "openai/codex",
    "openclaw/openclaw",
    "microsoft/vscode",
)
LOW_INFORMATION_TEXTS = {
    "hello",
    "hi",
    "hey",
    "你好",
    "您好",
    "在吗",
    "在么",
    "收到",
    "ok",
    "okay",
    "好的",
}


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
    signals = _events_to_signals(events, session_id=session_id, topic=topic, fallback_id=input_path.stem)
    if not signals:
        raise ValueError("No valid conversation signals could be extracted from the input.")

    signals_dir = paths.data_dir / "signals"
    signals_dir.mkdir(parents=True, exist_ok=True)

    output_path = signals_dir / f"{_slugify(str(signals[0]['session_id']))}.json"
    payload = [_finalize_signal(signal) for signal in signals]
    _write_json_atomic(output_path, payload)
    return SignalIngestResult(
        input_path=input_path,
        output_path=output_path,
        signal_count=len(payload),
        session_id=str(signals[0]["session_id"]),
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


def _events_to_signals(
    events: list[dict[str, object]],
    *,
    session_id: str | None,
    topic: str | None,
    fallback_id: str,
) -> list[dict[str, object]]:
    messages = _extract_messages(events)
    derived_session_id = session_id or _derive_session_id(events) or fallback_id
    derived_topic = _first_non_empty(
        topic,
        _derive_topic(events, messages),
        derived_session_id,
        FALLBACK_TOPIC,
    )
    base_signal = {
        "session_id": derived_session_id,
        "conversation_id": derived_session_id,
        "conversation_title": _optional_title(events) or derived_topic,
        "topic": derived_topic,
        "evidence": _evidence_from_messages(messages),
        "confidence": DEFAULT_SIGNAL_CONFIDENCE,
        "observed_runs": DEFAULT_OBSERVED_RUNS,
        "existing_skill_id": None,
        "corrections": 0,
        "explicit_uninstall_request": False,
        "superseded_by": None,
        "last_observed_at": _latest_timestamp(events),
        "report_classification": "candidate_only",
    }
    derived: list[dict[str, object]] = []
    if not _is_low_information_conversation(messages):
        derived.append(base_signal)
    derived.extend(_derived_report_signals(base_signal=base_signal, messages=messages))
    return _dedupe_signals(derived)


def _extract_messages(events: list[dict[str, object]]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for event in events:
        role, text = _extract_message(event)
        if text:
            messages.append({"role": role or "unknown", "text": text})
    return messages


def _extract_message(event: dict[str, object]) -> tuple[str | None, str | None]:
    payload = event.get("payload")
    if isinstance(payload, dict):
        payload_role, payload_text = _extract_message_from_payload(
            payload,
            event_type=_optional_text(event.get("type")),
        )
        if payload_role and payload_text:
            return payload_role, payload_text

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


def _extract_message_from_payload(
    payload: dict[str, object],
    *,
    event_type: str | None,
) -> tuple[str | None, str | None]:
    payload_type = _optional_text(payload.get("type"))
    if event_type == "event_msg":
        if payload_type == "user_message":
            return "user", _optional_text(payload.get("message"))
        if payload_type == "agent_message":
            return "assistant", _optional_text(payload.get("message"))
    if payload_type == "message":
        role = _optional_text(payload.get("role"))
        text = _extract_text_from_content_blocks(payload.get("content"))
        if role and text:
            return role, text
    return None, None


def _derived_report_signals(
    *,
    base_signal: dict[str, object],
    messages: list[dict[str, str]],
) -> list[dict[str, object]]:
    derived: list[dict[str, object]] = []
    user_messages = [item for item in messages if item["role"].lower() in {"user", "human"}]
    assistant_messages = [item for item in messages if item["role"].lower() == "assistant"]

    tooling_message = _first_matching_text(user_messages, ("工具实现", "自动同步", "github 安装", "ssh", "cron", "插件"))
    if tooling_message:
        derived.append(
            {
                **base_signal,
                "report_classification": "tooling_needed",
                "missing_requirement": tooling_message,
                "tool_references": list(TOOL_REFERENCE_DEFAULTS),
            }
        )

    unresolved_message = _first_matching_text(
        assistant_messages + user_messages,
        ("还没完成", "未完成", "下一步", "待处理", "请继续"),
    )
    if unresolved_message:
        derived.append(
            {
                **base_signal,
                "report_classification": "unresolved",
                "missing_requirement": _first_matching_text(user_messages, ("请", "需要", "实现", "继续"))
                or str(base_signal["topic"]),
                "next_step": unresolved_message,
            }
        )

    impossible_message = _first_matching_text(
        assistant_messages + user_messages,
        ("无法实现", "做不到", "不可能", "没有提供", "缺少对应 api"),
    )
    if impossible_message:
        derived.append(
            {
                **base_signal,
                "report_classification": "impossible",
                "missing_requirement": impossible_message,
                "prerequisites": ["Host or tool API support"],
            }
        )
    return derived


def _first_matching_text(messages: list[dict[str, str]], keywords: tuple[str, ...]) -> str | None:
    for message in messages:
        text = message["text"]
        lowered = text.lower()
        if any(keyword.lower() in lowered for keyword in keywords):
            return _trim_text(text)
    return None


def _is_low_information_conversation(messages: list[dict[str, str]]) -> bool:
    if not messages:
        return True
    meaningful = [message for message in messages if not _is_low_information_text(message["text"])]
    return not meaningful


def _is_low_information_text(text: str) -> bool:
    compact = re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE).lower()
    if not compact:
        return True
    if compact in LOW_INFORMATION_TEXTS:
        return True
    return len(compact) <= 4 and compact in LOW_INFORMATION_TEXTS


def _dedupe_signals(signals: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: list[dict[str, object]] = []
    seen: set[tuple[str, str, str | None]] = set()
    for signal in signals:
        key = (
            str(signal.get("conversation_id") or ""),
            str(signal.get("report_classification") or ""),
            str(signal.get("missing_requirement") or signal.get("topic") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
    return deduped


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


def _extract_text_from_content_blocks(value: object) -> str | None:
    if not isinstance(value, list):
        return _extract_text_value(value)
    parts: list[str] = []
    for item in value:
        if isinstance(item, dict):
            text = _extract_text_value(item.get("text"))
            if text:
                parts.append(text)
    combined = " ".join(parts).strip()
    return combined or None


def _derive_session_id(events: list[dict[str, object]]) -> str | None:
    for event in events:
        for key in ("session_id", "sessionId", "id"):
            value = _optional_text(event.get(key))
            if value:
                return value
        payload = event.get("payload")
        if isinstance(payload, dict):
            for key in ("session_id", "sessionId", "id"):
                value = _optional_text(payload.get(key))
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
        payload = event.get("payload")
        if isinstance(payload, dict):
            for key in ("title", "topic", "summary"):
                value = _optional_text(payload.get(key))
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
            if _is_low_information_text(message["text"]):
                continue
            return _compact_topic_text(message["text"])
    if messages:
        for message in messages:
            if _is_low_information_text(message["text"]):
                continue
            return _compact_topic_text(message["text"])
    return None


def _optional_title(events: list[dict[str, object]]) -> str | None:
    for event in events:
        for key in ("title", "topic", "summary"):
            value = _optional_text(event.get(key))
            if value:
                return value
        payload = event.get("payload")
        if isinstance(payload, dict):
            for key in ("title", "topic", "summary"):
                value = _optional_text(payload.get(key))
                if value:
                    return value
        message = event.get("message")
        if isinstance(message, dict):
            for key in ("title", "topic"):
                value = _optional_text(message.get(key))
                if value:
                    return value
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
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=_local_timezone())
    return parsed


def _local_timezone():
    return datetime.now().astimezone().tzinfo or timezone.utc


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


def _compact_topic_text(value: str) -> str:
    text = _trim_text(value, length=80).strip("。！？!?；;，, ")
    text = re.sub(r"^(请|麻烦|帮我|请你)+", "", text).strip()
    text = re.sub(r"^(继续|继续实现|实现|优化|补齐|完成)+", "", text).strip()
    text = re.split(r"[，。！？!?；;]", text, maxsplit=1)[0].strip()
    text = re.sub(r"(这|并且|而且)?需要工具实现.*$", "", text).strip()
    text = re.sub(r"(这个需求|该需求).*$", "", text).strip()
    return text or _trim_text(value, length=80)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    slug = slug.strip("-._")
    return slug or "autoskill-codex"


def _finalize_signal(signal: dict[str, object]) -> dict[str, object]:
    return {
        "conversation_id": signal["conversation_id"],
        "conversation_title": signal["conversation_title"],
        "topic": signal["topic"],
        "evidence": signal["evidence"],
        "confidence": signal["confidence"],
        "observed_runs": signal["observed_runs"],
        "existing_skill_id": signal["existing_skill_id"],
        "corrections": signal["corrections"],
        "explicit_uninstall_request": signal["explicit_uninstall_request"],
        "superseded_by": signal["superseded_by"],
        "last_observed_at": signal["last_observed_at"],
        "report_classification": signal.get("report_classification"),
        "missing_requirement": signal.get("missing_requirement"),
        "next_step": signal.get("next_step"),
        "tool_references": signal.get("tool_references"),
        "prerequisites": signal.get("prerequisites"),
    }


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)
