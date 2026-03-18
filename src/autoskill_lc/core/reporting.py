from __future__ import annotations

from datetime import datetime, timezone

from autoskill_lc.core.models import (
    ConversationSignal,
    GovernanceRecommendation,
    RecommendationAction,
    ReportClassification,
)

REPORT_SCHEMA_VERSION = "2.0"


def build_governance_report_payload(
    *,
    host: str,
    recommendations: list[GovernanceRecommendation],
    signals: list[ConversationSignal],
    generated_at: datetime | None = None,
    checkpoint_state: dict[str, object] | None = None,
) -> dict[str, object]:
    report_time = generated_at or datetime.now(timezone.utc)
    recommendation_by_topic: dict[str, GovernanceRecommendation] = {
        item.topic: item for item in recommendations
    }
    evidence_backed = []
    candidate_only = []
    unresolved_requirements = []
    tooling_needed = []
    impossible_items = []

    for signal in signals:
        if signal.report_classification is ReportClassification.EVIDENCE_BACKED:
            evidence_backed.append(
                _serialize_evidence_backed(signal, recommendation_by_topic.get(signal.topic))
            )
        elif signal.report_classification is ReportClassification.UNRESOLVED:
            unresolved_requirements.append(_serialize_unresolved(signal))
        elif signal.report_classification is ReportClassification.TOOLING_NEEDED:
            tooling_needed.append(_serialize_tooling(signal))
        elif signal.report_classification is ReportClassification.IMPOSSIBLE:
            impossible_items.append(_serialize_impossible(signal))
        else:
            candidate_only.append(_serialize_candidate(signal))

    payload = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "host": host,
        "generatedAt": report_time.isoformat(),
        "recommendationCount": len(recommendations),
        "recommendations": [_serialize_recommendation(item) for item in recommendations],
        "summary": {
            "evidenceBackedCount": len(evidence_backed),
            "candidateOnlyCount": len(candidate_only),
            "unresolvedRequirementCount": len(unresolved_requirements),
            "toolingNeedCount": len(tooling_needed),
            "impossibleItemCount": len(impossible_items),
            "actions": _summarize_actions(recommendations),
            "window": _build_window_summary(
                signals=signals,
                recommendations=recommendations,
                generated_at=report_time,
                checkpoint_state=checkpoint_state or {},
            ),
        },
        "evidenceBackedEvolutions": evidence_backed,
        "candidateOnly": candidate_only,
        "unresolvedRequirements": unresolved_requirements,
        "toolingNeeded": tooling_needed,
        "impossibleItems": impossible_items,
        "display": _build_display_payload(
            evidence_backed=evidence_backed,
            recommendations=recommendations,
            unresolved_requirements=unresolved_requirements,
            tooling_needed=tooling_needed,
            impossible_items=impossible_items,
            window=_build_window_summary(
                signals=signals,
                recommendations=recommendations,
                generated_at=report_time,
                checkpoint_state=checkpoint_state or {},
            ),
        ),
    }
    return payload


def _serialize_recommendation(item: GovernanceRecommendation) -> dict[str, object]:
    return {
        "action": item.action.value,
        "topic": item.topic,
        "confidence": item.confidence,
        "rationale": item.rationale,
        "skill_id": item.skill_id,
        "replacement_skill_id": item.replacement_skill_id,
        "evidence": list(item.evidence),
    }


def _serialize_evidence_backed(
    signal: ConversationSignal,
    recommendation: GovernanceRecommendation | None,
) -> dict[str, object]:
    return {
        "topic": signal.topic,
        "confidence": signal.confidence,
        "evidence": list(signal.evidence),
        "recommendationAction": recommendation.action.value if recommendation else None,
        "skillId": recommendation.skill_id if recommendation else signal.existing_skill_id,
        "rationale": recommendation.rationale if recommendation else None,
        "lastObservedAt": signal.last_observed_at.isoformat() if signal.last_observed_at else None,
    }


def _serialize_candidate(signal: ConversationSignal) -> dict[str, object]:
    return {
        "topic": signal.topic,
        "confidence": signal.confidence,
        "evidence": list(signal.evidence),
        "reason": "Evidence is not yet strong enough to modify a skill.",
        "nextStep": signal.next_step,
    }


def _serialize_unresolved(signal: ConversationSignal) -> dict[str, object]:
    return {
        "topic": signal.topic,
        "requirement": signal.missing_requirement or signal.topic,
        "evidence": list(signal.evidence),
        "nextStep": signal.next_step,
        "confidence": signal.confidence,
    }


def _serialize_tooling(signal: ConversationSignal) -> dict[str, object]:
    return {
        "topic": signal.topic,
        "requirement": signal.missing_requirement or signal.topic,
        "evidence": list(signal.evidence),
        "referenceProjects": list(signal.tool_references[:3]),
        "confidence": signal.confidence,
    }


def _serialize_impossible(signal: ConversationSignal) -> dict[str, object]:
    return {
        "topic": signal.topic,
        "requirement": signal.missing_requirement or signal.topic,
        "evidence": list(signal.evidence),
        "prerequisites": list(signal.prerequisites),
        "confidence": signal.confidence,
    }


def _build_display_payload(
    *,
    evidence_backed: list[dict[str, object]],
    recommendations: list[GovernanceRecommendation],
    unresolved_requirements: list[dict[str, object]],
    tooling_needed: list[dict[str, object]],
    impossible_items: list[dict[str, object]],
    window: dict[str, object],
) -> dict[str, object]:
    identified_items = [
        {
            "topic": item["topic"],
            "action": item["recommendationAction"],
            "skillId": item["skillId"],
        }
        for item in evidence_backed
    ]
    governance_items = [
        {
            "action": item.action.value,
            "topic": item.topic,
            "skillId": item.skill_id,
            "replacementSkillId": item.replacement_skill_id,
        }
        for item in recommendations
    ]
    forgotten_items = [
        {
            "requirement": item["requirement"],
            "reminder": "用户提过但本次未完成，建议主动提醒并继续处理。",
            "plan": item.get("nextStep"),
        }
        for item in unresolved_requirements
    ]
    tooling_items = [
        {
            "requirement": item["requirement"],
            "referenceProjects": item["referenceProjects"],
        }
        for item in tooling_needed
    ]
    impossible_display = [
        {
            "requirement": item["requirement"],
            "reason": "当前缺少必要前提，暂时不能落地。",
            "prerequisites": item["prerequisites"],
        }
        for item in impossible_items
    ]

    return {
        "identifiedExperiences": {
            "text": _count_text("本次识别出的经验", identified_items),
            "items": identified_items,
        },
        "governanceSuggestions": {
            "text": _count_text("治理建议", governance_items),
            "items": governance_items,
        },
        "forgottenRequirements": {
            "text": _count_text("遗忘需求提醒", forgotten_items),
            "items": forgotten_items,
        },
        "toolingNeeds": {
            "text": _count_text("需要工具实现", tooling_items),
            "items": tooling_items,
        },
        "impossibleItems": {
            "text": _count_text("当前不可实现", impossible_display),
            "items": impossible_display,
        },
        "checkpointWindowSummary": {
            "text": _window_text(
                window=window,
                identified_items=identified_items,
                governance_items=governance_items,
            )
        },
    }


def _count_text(label: str, items: list[dict[str, object]]) -> str:
    if not items:
        return f"{label}：无"
    return f"{label}：{len(items)} 条"


def _build_window_summary(
    *,
    signals: list[ConversationSignal],
    recommendations: list[GovernanceRecommendation],
    generated_at: datetime,
    checkpoint_state: dict[str, object],
) -> dict[str, object]:
    last_checkpoint = _repair_legacy_future_timestamp(
        _parse_datetime(checkpoint_state.get("last_processed_at")),
        generated_at,
    )
    hours = 0.0
    if last_checkpoint is not None:
        hours = round((generated_at - last_checkpoint).total_seconds() / 3600, 1)
    dialogue_count = _dialogue_count(signals)
    return {
        "hoursSinceLastCheckpoint": hours,
        "dialogueCount": dialogue_count,
        "lastCheckpointAt": last_checkpoint.isoformat() if last_checkpoint else None,
        "recommendationCount": len(recommendations),
    }


def _dialogue_count(signals: list[ConversationSignal]) -> int:
    seen: set[str] = set()
    count = 0
    for signal in signals:
        marker = signal.conversation_id or signal.conversation_title or signal.topic
        if marker in seen:
            continue
        seen.add(marker)
        count += 1
    return count


def _window_text(
    *,
    window: dict[str, object],
    identified_items: list[dict[str, object]],
    governance_items: list[dict[str, object]],
) -> str:
    hours = float(window.get("hoursSinceLastCheckpoint", 0.0))
    dialogue_count = int(window.get("dialogueCount", 0))
    if identified_items:
        core = "；".join(str(item["topic"]) for item in identified_items[:3])
    else:
        core = "暂无可沉淀经验"
    if governance_items:
        return (
            f"过去到上个检查点合计 {hours:.1f} 小时的 {dialogue_count} 条对话的核心沉淀："
            f"{core}；另外有 {len(governance_items)} 条治理建议待处理。"
        )
    return (
        f"过去到上个检查点合计 {hours:.1f} 小时的 {dialogue_count} 条对话的核心沉淀："
        f"{core}。"
    )


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


def _repair_legacy_future_timestamp(
    parsed: datetime | None,
    reference: datetime,
) -> datetime | None:
    if parsed is None or parsed <= reference:
        return parsed
    local_tz = _local_timezone()
    reinterpreted = parsed.replace(tzinfo=local_tz)
    if reinterpreted <= reference:
        return reinterpreted
    return parsed


def _summarize_actions(
    recommendations: list[GovernanceRecommendation],
) -> dict[str, int]:
    counts = {action.value: 0 for action in RecommendationAction}
    for item in recommendations:
        counts[item.action.value] += 1
    return counts
