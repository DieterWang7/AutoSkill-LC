from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.adapters.base import HostCapabilities
from autoskill_lc.codex.config import CodexPaths
from autoskill_lc.codex.reporting import write_governance_report
from autoskill_lc.core.models import (
    ConversationSignal,
    GovernanceRecommendation,
    ReportClassification,
    SkillRecord,
)


def _load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


@dataclass
class CodexAdapter:
    codex_home: Path
    name: str = "codex"
    capabilities: HostCapabilities = HostCapabilities(
        supports_cron=False,
        supports_hot_uninstall=True,
        supports_conversation_archive=True,
        supports_skill_mirroring=True,
    )

    @classmethod
    def for_home(cls, codex_home: Path) -> "CodexAdapter":
        return cls(codex_home=codex_home.expanduser().resolve())

    @property
    def paths(self) -> CodexPaths:
        return CodexPaths.from_home(self.codex_home)

    def collect_signals(self) -> list[ConversationSignal]:
        signals_dir = self.paths.data_dir / "signals"
        results: list[ConversationSignal] = []
        if not signals_dir.exists():
            return results

        for path in sorted(signals_dir.glob("*.json")):
            payload = _load_json(path, default=[])
            if not isinstance(payload, list):
                continue
            for raw in payload:
                if not isinstance(raw, dict):
                    continue
                topic = _optional_str(raw.get("topic"))
                if not topic:
                    continue
                results.append(
                    ConversationSignal(
                        topic=topic,
                        evidence=_coerce_evidence(raw.get("evidence")),
                        confidence=float(raw.get("confidence", 0.0)),
                        observed_runs=int(raw.get("observed_runs", 1)),
                        conversation_id=_optional_str(
                            raw.get("conversation_id") or raw.get("session_id")
                        ),
                        conversation_title=_optional_str(
                            raw.get("conversation_title") or raw.get("title")
                        ),
                        existing_skill_id=_optional_str(raw.get("existing_skill_id")),
                        corrections=int(raw.get("corrections", 0)),
                        explicit_uninstall_request=bool(
                            raw.get("explicit_uninstall_request", False)
                        ),
                        superseded_by=_optional_str(raw.get("superseded_by")),
                        last_observed_at=_optional_datetime(raw.get("last_observed_at")),
                        report_classification=_report_classification(
                            raw.get("report_classification")
                        ),
                        missing_requirement=_optional_str(raw.get("missing_requirement")),
                        next_step=_optional_str(raw.get("next_step")),
                        tool_references=_coerce_str_tuple(raw.get("tool_references")),
                        prerequisites=_coerce_str_tuple(raw.get("prerequisites")),
                    )
                )
        return results

    def list_skills(self) -> list[SkillRecord]:
        inventory_path = self.paths.data_dir / "inventory" / "skills.json"
        payload = _load_json(inventory_path, default=[])
        results: list[SkillRecord] = []
        if not isinstance(payload, list):
            return results

        for raw in payload:
            if not isinstance(raw, dict):
                continue
            skill_id = _optional_str(raw.get("skill_id"))
            title = _optional_str(raw.get("title"))
            version = _optional_str(raw.get("version"))
            if not skill_id or not title or not version:
                continue
            results.append(
                SkillRecord(
                    skill_id=skill_id,
                    title=title,
                    version=version,
                    usage_count=int(raw.get("usage_count", 0)),
                    last_used_at=_optional_datetime(raw.get("last_used_at")),
                    status=str(raw.get("status", "active")),
                )
            )
        return results

    def emit_report(
        self,
        recommendations: list[GovernanceRecommendation],
        *,
        report_path: Path,
        signals: list[ConversationSignal],
        generated_at: datetime | None = None,
        checkpoint_state: dict[str, object] | None = None,
    ) -> None:
        write_governance_report(
            report_path,
            recommendations,
            host=self.name,
            signals=signals,
            generated_at=generated_at,
            checkpoint_state=checkpoint_state,
        )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_evidence(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, list):
        return tuple(str(item) for item in value if str(item).strip())
    return (str(value),)


def _coerce_str_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, list):
        return tuple(str(item) for item in value if str(item).strip())
    return (str(value),)


def _optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=_local_timezone())
        return parsed
    return None


def _local_timezone():
    return datetime.now().astimezone().tzinfo or timezone.utc


def _report_classification(value: object) -> ReportClassification:
    text = _optional_str(value)
    if not text:
        return ReportClassification.CANDIDATE_ONLY
    try:
        return ReportClassification(text)
    except ValueError:
        return ReportClassification.CANDIDATE_ONLY
