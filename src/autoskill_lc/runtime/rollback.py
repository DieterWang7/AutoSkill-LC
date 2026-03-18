from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RollbackResult:
    manifest_path: str
    skill_path: str
    restored: bool


def rollback_from_manifest(manifest_path: Path) -> RollbackResult:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    skill_path = Path(str(payload["skillPath"])).expanduser()
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(str(payload["originalContent"]), encoding="utf-8")
    return RollbackResult(
        manifest_path=str(manifest_path),
        skill_path=str(skill_path),
        restored=True,
    )
