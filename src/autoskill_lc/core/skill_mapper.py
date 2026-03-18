from __future__ import annotations

import re
from dataclasses import dataclass

from autoskill_lc.core.models import ConversationSignal, SkillRecord


@dataclass(frozen=True)
class SkillMatch:
    topic: str
    skill_id: str
    skill_title: str
    confidence: float
    match_type: str


def map_signal_to_skill(
    signal: ConversationSignal,
    skills: list[SkillRecord],
) -> SkillMatch | None:
    if signal.existing_skill_id:
        for skill in skills:
            if skill.skill_id == signal.existing_skill_id:
                return SkillMatch(
                    topic=signal.topic,
                    skill_id=skill.skill_id,
                    skill_title=skill.title,
                    confidence=1.0,
                    match_type="explicit",
                )

    signal_tokens = _tokens(signal.topic)
    signal_key = _normalized_phrase(signal.topic)
    best: SkillMatch | None = None

    for skill in skills:
        title_tokens = _tokens(skill.title)
        skill_tokens = _tokens(skill.skill_id)
        title_key = _normalized_phrase(skill.title)
        skill_key = _normalized_phrase(skill.skill_id)
        if (
            signal_tokens == title_tokens
            or signal_tokens == skill_tokens
            or signal_key == title_key
            or signal_key == skill_key
        ):
            candidate = SkillMatch(
                topic=signal.topic,
                skill_id=skill.skill_id,
                skill_title=skill.title,
                confidence=0.95,
                match_type="exact",
            )
        else:
            overlap = len(signal_tokens & title_tokens)
            union = len(signal_tokens | title_tokens) or 1
            score = overlap / union
            if score < 0.45:
                continue
            candidate = SkillMatch(
                topic=signal.topic,
                skill_id=skill.skill_id,
                skill_title=skill.title,
                confidence=round(score, 2),
                match_type="overlap",
            )
        if best is None or candidate.confidence > best.confidence:
            best = candidate

    return best


def map_signals_to_skills(
    signals: list[ConversationSignal],
    skills: list[SkillRecord],
) -> dict[str, SkillMatch]:
    mappings: dict[str, SkillMatch] = {}
    for signal in signals:
        match = map_signal_to_skill(signal, skills)
        if match is not None:
            mappings[signal.topic] = match
    return mappings


def _tokens(value: str) -> set[str]:
    raw = re.split(r"[\s/,_\-|，。；;:：和与]+", value.lower())
    tokens: set[str] = set()
    for item in raw:
        compact = re.sub(r"[^\w\u4e00-\u9fff]+", "", item)
        if compact:
            tokens.add(compact)
    return tokens


def _normalized_phrase(value: str) -> str:
    parts = [token for token in _tokens(value) if token]
    parts.sort()
    return "|".join(parts)
