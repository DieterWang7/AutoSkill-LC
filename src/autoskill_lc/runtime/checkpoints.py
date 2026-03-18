from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.core.models import ConversationSignal, GovernanceRecommendation, RecommendationAction


def read_checkpoint_state(checkpoint_path: Path) -> dict[str, object]:
    if not checkpoint_path.exists():
        return {"sequence": 0, "last_processed_at": None}
    text = checkpoint_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {"sequence": 0, "last_processed_at": None}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {"sequence": 0, "last_processed_at": None}
    header = text[4:end].splitlines()
    state: dict[str, object] = {"sequence": 0, "last_processed_at": None}
    for line in header:
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip() or None
        if key == "sequence":
            try:
                state["sequence"] = int(value or 0)
            except ValueError:
                state["sequence"] = 0
        elif key == "last_processed_at":
            state["last_processed_at"] = value
    return state


def filter_signals_for_incremental_run(
    signals: list[ConversationSignal],
    state: dict[str, object],
) -> list[ConversationSignal]:
    last_processed = _parse_datetime(state.get("last_processed_at"))
    if last_processed is None:
        return signals
    filtered: list[ConversationSignal] = []
    for signal in signals:
        if signal.last_observed_at is None or signal.last_observed_at > last_processed:
            filtered.append(signal)
    return filtered


def write_checkpoint_entry(
    checkpoint_path: Path,
    *,
    host: str,
    signals: list[ConversationSignal],
    recommendations: list[GovernanceRecommendation],
    run_at: datetime,
) -> None:
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    previous = read_checkpoint_state(checkpoint_path)
    sequence = int(previous.get("sequence", 0)) + 1
    next_sequence = f"{sequence:04d}"
    previous_last_processed_at = _parse_datetime(previous.get("last_processed_at"))
    last_processed_at = (
        _latest_observed_at(signals)
        or previous_last_processed_at
        or (run_at if signals else None)
    )
    previous_body = _read_existing_body(checkpoint_path)

    upgraded = [item.skill_id for item in recommendations if item.action is RecommendationAction.UPGRADE and item.skill_id]
    removed = [
        item.skill_id
        for item in recommendations
        if item.action in {RecommendationAction.DEPRECATE, RecommendationAction.REMOVE}
        and item.skill_id
    ]

    primary_signal = signals[0] if signals else None
    entry_lines = [
        f"## {next_sequence} | {run_at.isoformat()} | {host}",
        f"- 对话ID: {primary_signal.conversation_id if primary_signal and primary_signal.conversation_id else 'unknown'}",
        f"- 对话标题: {primary_signal.conversation_title if primary_signal and primary_signal.conversation_title else (primary_signal.topic if primary_signal else 'unknown')}",
        f"- 升级的 skill: {', '.join(upgraded) if upgraded else '无'}",
        f"- 卸载的 skill: {', '.join(removed) if removed else '无'}",
        "",
    ]

    header_lines = [
        "---",
        f"sequence: {sequence}",
        f"last_processed_at: {last_processed_at.isoformat() if last_processed_at else ''}",
        "---",
        "",
        "# AutoSkill-LC Checkpoints",
        "",
    ]
    body = "\n".join(entry_lines)
    if previous_body:
        body = body + previous_body
    checkpoint_path.write_text(
        "\n".join(header_lines) + body,
        encoding="utf-8",
    )


def _read_existing_body(checkpoint_path: Path) -> str:
    if not checkpoint_path.exists():
        return ""
    text = checkpoint_path.read_text(encoding="utf-8")
    marker = "\n# AutoSkill-LC Checkpoints\n\n"
    idx = text.find(marker)
    if idx == -1:
        return ""
    body = text[idx + len(marker):]
    return body


def _latest_observed_at(signals: list[ConversationSignal]) -> datetime | None:
    observed = [item.last_observed_at for item in signals if item.last_observed_at is not None]
    if not observed:
        return None
    return max(observed)


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=_local_timezone())
    return parsed


def _local_timezone():
    return datetime.now().astimezone().tzinfo or timezone.utc
