from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ADAPTER_ID = "autoskill-lc-codex-adapter"


@dataclass(frozen=True)
class CodexPaths:
    codex_home: Path
    data_dir: Path
    sessions_dir: Path
    history_path: Path

    @classmethod
    def from_home(cls, codex_home: Path) -> "CodexPaths":
        home = codex_home.expanduser().resolve()
        data_dir = home / "autoskill-lc"
        sessions_dir = home / "sessions"
        history_path = home / "history.jsonl"
        return cls(
            codex_home=home,
            data_dir=data_dir,
            sessions_dir=sessions_dir,
            history_path=history_path,
        )

