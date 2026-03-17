from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from autoskill_lc.openclaw.config import OpenClawPaths, PLUGIN_ID


ADAPTER_ENTRYPOINT = """export default {
  id: "autoskill-lc-openclaw-adapter",
  name: "AutoSkill-LC OpenClaw Adapter",
  register(api) {
    api.registerCommand({
      name: "autoskill-status",
      description: "Show AutoSkill-LC adapter status",
      handler: () => ({
        text: "AutoSkill-LC adapter is installed. Run scheduled maintenance externally.",
      }),
    });
  },
};
"""

ADAPTER_DESCRIPTOR = {
    "id": PLUGIN_ID,
    "name": "AutoSkill-LC OpenClaw Adapter",
    "version": "0.1.0",
    "entry": "index.js",
    "configSchema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "runtimeMode": {
                "type": "string",
                "enum": ["scheduled"],
            },
            "reportName": {
                "type": "string",
            },
            "paths": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "dataDir": {"type": "string"},
                    "signalsDir": {"type": "string"},
                    "inventoryDir": {"type": "string"},
                    "reportsDir": {"type": "string"},
                    "skillsDir": {"type": "string"},
                },
                "required": [
                    "dataDir",
                    "signalsDir",
                    "inventoryDir",
                    "reportsDir",
                    "skillsDir",
                ],
            },
        },
        "required": ["runtimeMode", "reportName", "paths"],
    },
    "uiHints": {
        "runtimeMode": {
            "label": "Runtime Mode",
        },
        "reportName": {
            "label": "Report File Name",
            "placeholder": "latest-governance-report.json",
        },
    },
}


@dataclass(frozen=True)
class OpenClawInstallOptions:
    workspace_dir: Path
    report_name: str = "latest-governance-report.json"

    @property
    def paths(self) -> OpenClawPaths:
        return OpenClawPaths.from_workspace(self.workspace_dir)

    @property
    def data_dir(self) -> Path:
        return self.paths.data_dir


def install_openclaw_adapter(options: OpenClawInstallOptions) -> None:
    paths = options.paths
    _ensure_directories(paths)
    _write_adapter_files(paths)
    _write_manifest(options)
    _upsert_openclaw_config(options)


def uninstall_openclaw_adapter(
    options: OpenClawInstallOptions,
    *,
    purge_data: bool = False,
) -> None:
    paths = options.paths
    _remove_openclaw_config(paths)
    _safe_rmtree(paths.adapter_dir)
    _safe_rmtree(paths.plugin_dir)
    if purge_data:
        _safe_rmtree(paths.data_dir)


def _ensure_directories(paths: OpenClawPaths) -> None:
    directories = [
        paths.plugin_dir,
        paths.adapter_dir,
        paths.data_dir / "signals",
        paths.data_dir / "inventory",
        paths.data_dir / "reports",
        paths.data_dir / "skills",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def _write_adapter_files(paths: OpenClawPaths) -> None:
    (paths.adapter_dir / "index.js").write_text(ADAPTER_ENTRYPOINT, encoding="utf-8")
    (paths.adapter_dir / "openclaw.plugin.json").write_text(
        json.dumps(ADAPTER_DESCRIPTOR, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (paths.plugin_dir / "README.txt").write_text(
        "AutoSkill-LC OpenClaw plugin runtime home.\n",
        encoding="utf-8",
    )


def _write_manifest(options: OpenClawInstallOptions) -> None:
    paths = options.paths
    payload = {
        "pluginId": PLUGIN_ID,
        "workspaceDir": str(paths.workspace_dir),
        "pluginDir": str(paths.plugin_dir),
        "adapterDir": str(paths.adapter_dir),
        "dataDir": str(paths.data_dir),
        "reportName": options.report_name,
    }
    paths.manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _upsert_openclaw_config(options: OpenClawInstallOptions) -> None:
    paths = options.paths
    root = _load_json_dict(paths.config_path)
    plugins = root.setdefault("plugins", {})
    load = plugins.setdefault("load", {})
    load_paths = load.setdefault("paths", [])
    adapter_dir_value = str(paths.adapter_dir)
    if adapter_dir_value not in load_paths:
        load_paths.append(adapter_dir_value)

    entries = plugins.setdefault("entries", {})
    entries[PLUGIN_ID] = {
        "enabled": True,
        "config": {
            "runtimeMode": "scheduled",
            "reportName": options.report_name,
            "paths": {
                "dataDir": str(paths.data_dir),
                "signalsDir": str(paths.data_dir / "signals"),
                "inventoryDir": str(paths.data_dir / "inventory"),
                "reportsDir": str(paths.data_dir / "reports"),
                "skillsDir": str(paths.data_dir / "skills"),
            },
        },
    }
    _save_json(paths.config_path, root)


def _remove_openclaw_config(paths: OpenClawPaths) -> None:
    root = _load_json_dict(paths.config_path)
    plugins = root.get("plugins")
    if not isinstance(plugins, dict):
        return

    load = plugins.get("load")
    if isinstance(load, dict):
        load_paths = load.get("paths")
        if isinstance(load_paths, list):
            load["paths"] = [item for item in load_paths if str(item) != str(paths.adapter_dir)]

    entries = plugins.get("entries")
    if isinstance(entries, dict):
        entries.pop(PLUGIN_ID, None)

    _save_json(paths.config_path, root)


def _load_json_dict(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return payload


def _save_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _safe_rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
