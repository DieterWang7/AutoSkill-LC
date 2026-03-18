from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum


class RecommendationAction(StrEnum):
    ADD = "add"
    UPGRADE = "upgrade"
    DEPRECATE = "deprecate"
    REMOVE = "remove"


class ReportClassification(StrEnum):
    EVIDENCE_BACKED = "evidence_backed"
    CANDIDATE_ONLY = "candidate_only"
    UNRESOLVED = "unresolved"
    TOOLING_NEEDED = "tooling_needed"
    IMPOSSIBLE = "impossible"


@dataclass(frozen=True)
class ConversationSignal:
    topic: str
    evidence: tuple[str, ...] = ()
    confidence: float = 0.0
    observed_runs: int = 1
    conversation_id: str | None = None
    conversation_title: str | None = None
    existing_skill_id: str | None = None
    corrections: int = 0
    explicit_uninstall_request: bool = False
    superseded_by: str | None = None
    last_observed_at: datetime | None = None
    report_classification: ReportClassification = ReportClassification.CANDIDATE_ONLY
    missing_requirement: str | None = None
    next_step: str | None = None
    tool_references: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillRecord:
    skill_id: str
    title: str
    version: str
    usage_count: int = 0
    last_used_at: datetime | None = None
    status: str = "active"
    skill_path: str | None = None


@dataclass(frozen=True)
class GovernanceRecommendation:
    action: RecommendationAction
    topic: str
    rationale: str
    confidence: float
    skill_id: str | None = None
    replacement_skill_id: str | None = None
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
