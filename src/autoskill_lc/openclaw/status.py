from __future__ import annotations

import json
from pathlib import Path

from autoskill_lc.openclaw.config import OpenClawPaths, PLUGIN_ID


def build_openclaw_status(workspace_dir: Path) -> dict[str, object]:
    paths = OpenClawPaths.from_workspace(workspace_dir)
    latest_report_path = _latest_report(paths.data_dir / "reports")
    latest_report_payload = _load_json(latest_report_path)
    return {
        "pluginId": PLUGIN_ID,
        "workspaceDir": str(paths.workspace_dir),
        "installed": paths.adapter_dir.exists() and paths.manifest_path.exists(),
        "paths": {
            "dataDir": str(paths.data_dir),
            "pluginDir": str(paths.plugin_dir),
            "adapterDir": str(paths.adapter_dir),
            "configPath": str(paths.config_path),
            "manifestPath": str(paths.manifest_path),
            "checkpointPath": str(paths.checkpoint_path),
        },
        "counts": {
            "signalFiles": _count_json_files(paths.data_dir / "signals"),
            "inventoryFiles": _count_json_files(paths.data_dir / "inventory"),
            "reportFiles": _count_json_files(paths.data_dir / "reports"),
        },
        "latestReport": {
            "path": str(latest_report_path) if latest_report_path else None,
            "recommendationCount": _extract_recommendation_count(latest_report_payload),
        },
        "checkpoint": {
            "path": str(paths.checkpoint_path),
            "exists": paths.checkpoint_path.exists(),
        },
    }


def _count_json_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return len(list(directory.glob("*.json")))


def _latest_report(directory: Path) -> Path | None:
    if not directory.exists():
        return None
    reports = sorted(
        directory.glob("*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return reports[0] if reports else None


def _load_json(path: Path | None) -> object:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _extract_recommendation_count(payload: object) -> int | None:
    if not isinstance(payload, dict):
        return None
    try:
        return int(payload.get("recommendationCount"))
    except (TypeError, ValueError):
        return None
