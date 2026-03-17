from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.codex.config import ADAPTER_ID, CodexPaths, SKILL_ID


SKILL_CONTENT = """---
name: AutoSkill-LC Governance
description: Review AutoSkill-LC governance status, reports, and Codex-local skill signals.
---

# AutoSkill-LC Governance

Use AutoSkill-LC data under `~/.codex/autoskill-lc/` to inspect:

- signals generated from Codex sessions
- inventory snapshots
- governance reports

When discussing changes, prefer the latest report in `reports/` and the latest
signal files in `signals/`.
"""


@dataclass(frozen=True)
class CodexInstallOptions:
    codex_home: Path
    install_skill: bool = True

    @property
    def paths(self) -> CodexPaths:
        return CodexPaths.from_home(self.codex_home)


def install_codex_adapter(options: CodexInstallOptions) -> dict[str, object]:
    paths = options.paths
    managed_files: list[str] = []
    managed_directories: list[str] = []

    _ensure_directory(paths.data_dir, managed_directories)
    _ensure_directory(paths.data_dir / "signals", managed_directories)
    _ensure_directory(paths.data_dir / "inventory", managed_directories)
    _ensure_directory(paths.data_dir / "reports", managed_directories)

    inventory_path = paths.data_dir / "inventory" / "skills.json"
    _write_json_file_if_missing(inventory_path, [], managed_files)

    if options.install_skill:
        _ensure_directory(paths.skills_root, managed_directories)
        _ensure_directory(paths.skill_dir, managed_directories)
        _write_text_file(paths.skill_file, SKILL_CONTENT, managed_files)

    manifest = {
        "adapterId": ADAPTER_ID,
        "skillId": SKILL_ID,
        "codexHome": str(paths.codex_home),
        "installedAt": datetime.now(timezone.utc).isoformat(),
        "managedFiles": sorted(set(managed_files + [str(paths.manifest_path)])),
        "managedDirectories": sorted(set(managed_directories)),
        "installSkill": bool(options.install_skill),
    }
    paths.manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def uninstall_codex_adapter(options: CodexInstallOptions) -> None:
    paths = options.paths
    manifest = _load_manifest(paths.manifest_path)
    if not manifest:
        return
    if manifest.get("adapterId") != ADAPTER_ID:
        return

    managed_files = [
        Path(item)
        for item in manifest.get("managedFiles", [])
        if isinstance(item, str) and item
    ]
    managed_directories = [
        Path(item)
        for item in manifest.get("managedDirectories", [])
        if isinstance(item, str) and item
    ]

    for file_path in sorted(managed_files, key=lambda item: len(item.parts), reverse=True):
        _safe_unlink(file_path)

    for directory in sorted(
        managed_directories,
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        _safe_rmdir(directory)


def _load_manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _ensure_directory(path: Path, managed_directories: list[str]) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        managed_directories.append(str(path))


def _write_json_file_if_missing(
    path: Path,
    payload: object,
    managed_files: list[str],
) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    managed_files.append(str(path))


def _write_text_file(path: Path, content: str, managed_files: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    managed_files.append(str(path))


def _safe_unlink(path: Path) -> None:
    if path.exists() and path.is_file():
        path.unlink()


def _safe_rmdir(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        return
    try:
        path.rmdir()
    except OSError:
        return
