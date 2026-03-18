from __future__ import annotations

import re
from dataclasses import dataclass

from autoskill_lc.core.models import ConversationSignal


@dataclass(frozen=True)
class SemanticMergeGroup:
    canonical_topic: str
    source_topics: tuple[str, ...]
    conversation_ids: tuple[str, ...]


@dataclass(frozen=True)
class SemanticMergeResult:
    signals: list[ConversationSignal]
    groups: list[SemanticMergeGroup]


def merge_signals(signals: list[ConversationSignal]) -> SemanticMergeResult:
    grouped: dict[str, list[ConversationSignal]] = {}
    for signal in signals:
        grouped.setdefault(_topic_key(signal.topic), []).append(signal)

    merged_signals: list[ConversationSignal] = []
    groups: list[SemanticMergeGroup] = []

    for items in grouped.values():
        canonical_topic = _canonical_topic(items)
        merged_signals.append(
            ConversationSignal(
                topic=canonical_topic,
                evidence=_merge_evidence(items),
                confidence=max(item.confidence for item in items),
                observed_runs=sum(item.observed_runs for item in items),
                conversation_id=_first_non_empty(item.conversation_id for item in items),
                conversation_title=_first_non_empty(item.conversation_title for item in items),
                existing_skill_id=_first_non_empty(item.existing_skill_id for item in items),
                corrections=sum(item.corrections for item in items),
                explicit_uninstall_request=any(
                    item.explicit_uninstall_request for item in items
                ),
                superseded_by=_first_non_empty(item.superseded_by for item in items),
                last_observed_at=max(
                    (item.last_observed_at for item in items if item.last_observed_at),
                    default=None,
                ),
                report_classification=_strongest_classification(items),
                missing_requirement=_first_non_empty(
                    item.missing_requirement for item in items
                ),
                next_step=_first_non_empty(item.next_step for item in items),
                tool_references=_merge_tuple_values(item.tool_references for item in items),
                prerequisites=_merge_tuple_values(item.prerequisites for item in items),
            )
        )
        groups.append(
            SemanticMergeGroup(
                canonical_topic=canonical_topic,
                source_topics=tuple(dict.fromkeys(item.topic for item in items)),
                conversation_ids=tuple(
                    dict.fromkeys(
                        item.conversation_id for item in items if item.conversation_id
                    )
                ),
            )
        )

    return SemanticMergeResult(signals=merged_signals, groups=groups)


def _topic_key(topic: str) -> str:
    text = topic.lower().strip()
    text = text.replace("github", "github")
    parts = re.split(r"\s*(?:and|与|和|\+|/|,|，|；|;)\s*", text)
    normalized_parts: list[str] = []
    for part in parts:
        compact = re.sub(r"[\W_]+", "", part)
        if compact:
            normalized_parts.append(compact)
    normalized_parts.sort()
    if normalized_parts:
        return "|".join(normalized_parts)
    return re.sub(r"[\W_]+", "", text)


def _canonical_topic(items: list[ConversationSignal]) -> str:
    def score(item: ConversationSignal) -> tuple[int, int, str]:
        ascii_penalty = 0 if any(ord(ch) > 127 for ch in item.topic) else 1
        return (ascii_penalty, len(item.topic), item.topic)

    return sorted(items, key=score)[0].topic


def _merge_evidence(items: list[ConversationSignal]) -> tuple[str, ...]:
    merged: list[str] = []
    for item in items:
        for evidence in item.evidence:
            if evidence not in merged:
                merged.append(evidence)
    return tuple(merged)


def _merge_tuple_values(values: list[tuple[str, ...]] | object) -> tuple[str, ...]:
    merged: list[str] = []
    for group in values:
        for value in group:
            if value not in merged:
                merged.append(value)
    return tuple(merged)


def _first_non_empty(values) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _strongest_classification(items: list[ConversationSignal]):
    ranked = {
        "evidence_backed": 5,
        "tooling_needed": 4,
        "unresolved": 3,
        "impossible": 2,
        "candidate_only": 1,
    }
    return max(
        items,
        key=lambda item: ranked.get(item.report_classification.value, 0),
    ).report_classification
