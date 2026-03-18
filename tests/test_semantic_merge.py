from datetime import datetime, timezone

from autoskill_lc.core.models import ConversationSignal, ReportClassification
from autoskill_lc.core.semantic_merge import merge_signals


def test_merge_signals_merges_similar_topics() -> None:
    result = merge_signals(
        [
            ConversationSignal(
                topic="GitHub 安装和服务器自动同步",
                evidence=("e1",),
                confidence=0.7,
                observed_runs=2,
                conversation_id="c1",
                report_classification=ReportClassification.EVIDENCE_BACKED,
                last_observed_at=datetime(2026, 3, 18, 10, tzinfo=timezone.utc),
            ),
            ConversationSignal(
                topic="服务器自动同步 和 GitHub 安装",
                evidence=("e2",),
                confidence=0.8,
                observed_runs=1,
                conversation_id="c2",
                report_classification=ReportClassification.CANDIDATE_ONLY,
                last_observed_at=datetime(2026, 3, 18, 11, tzinfo=timezone.utc),
            ),
        ]
    )

    assert len(result.signals) == 1
    merged = result.signals[0]
    assert merged.topic == "GitHub 安装和服务器自动同步"
    assert merged.observed_runs == 3
    assert merged.evidence == ("e1", "e2")
    assert merged.last_observed_at == datetime(2026, 3, 18, 11, tzinfo=timezone.utc)
    assert merged.report_classification is ReportClassification.EVIDENCE_BACKED


def test_merge_signals_preserves_distinct_topics() -> None:
    result = merge_signals(
        [
            ConversationSignal(topic="OpenClaw cron"),
            ConversationSignal(topic="Codex install flow"),
        ]
    )

    assert len(result.signals) == 2
