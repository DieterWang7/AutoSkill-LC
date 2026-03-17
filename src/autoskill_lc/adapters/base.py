from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from autoskill_lc.core.models import ConversationSignal, GovernanceRecommendation, SkillRecord


@dataclass(frozen=True)
class HostCapabilities:
    supports_cron: bool = False
    supports_hot_uninstall: bool = True
    supports_conversation_archive: bool = True
    supports_skill_mirroring: bool = True


class HostAdapter(Protocol):
    name: str
    capabilities: HostCapabilities

    def collect_signals(self) -> list[ConversationSignal]:
        """Return conversation-derived signals from the host."""

    def list_skills(self) -> list[SkillRecord]:
        """Return the host-visible skill inventory snapshot."""

    def emit_report(
        self,
        recommendations: list[GovernanceRecommendation],
        *,
        report_path: Path,
    ) -> None:
        """Persist governance recommendations for review."""
