from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ADAPTER_ID = "autoskill-lc-codex-adapter"
SKILL_ID = "autoskill-lc-governance"


@dataclass(frozen=True)
class CodexPaths:
    codex_home: Path
    data_dir: Path
    sessions_dir: Path
    history_path: Path
    manifest_path: Path
    checkpoint_path: Path
    skills_root: Path
    skill_dir: Path
    skill_file: Path

    @classmethod
    def from_home(cls, codex_home: Path) -> "CodexPaths":
        home = codex_home.expanduser().resolve()
        data_dir = home / "autoskill-lc"
        sessions_dir = home / "sessions"
        history_path = home / "history.jsonl"
        manifest_path = data_dir / "install-manifest.json"
        checkpoint_path = data_dir / "checkpoint.md"
        skills_root = home / "skills"
        skill_dir = skills_root / SKILL_ID
        skill_file = skill_dir / "SKILL.md"
        return cls(
            codex_home=home,
            data_dir=data_dir,
            sessions_dir=sessions_dir,
            history_path=history_path,
            manifest_path=manifest_path,
            checkpoint_path=checkpoint_path,
            skills_root=skills_root,
            skill_dir=skill_dir,
            skill_file=skill_file,
        )
