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
) -> dict[str, object]:
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
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "recommendationCount": len(recommendations),
        "recommendations": [_serialize_recommendation(item) for item in recommendations],
        "summary": {
            "evidenceBackedCount": len(evidence_backed),
            "candidateOnlyCount": len(candidate_only),
            "unresolvedRequirementCount": len(unresolved_requirements),
            "toolingNeedCount": len(tooling_needed),
            "impossibleItemCount": len(impossible_items),
            "actions": _summarize_actions(recommendations),
        },
        "evidenceBackedEvolutions": evidence_backed,
        "candidateOnly": candidate_only,
        "unresolvedRequirements": unresolved_requirements,
        "toolingNeeded": tooling_needed,
        "impossibleItems": impossible_items,
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


def _summarize_actions(
    recommendations: list[GovernanceRecommendation],
) -> dict[str, int]:
    counts = {action.value: 0 for action in RecommendationAction}
    for item in recommendations:
        counts[item.action.value] += 1
    return counts
