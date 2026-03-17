from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PLUGIN_ID = "autoskill-lc-openclaw-adapter"


@dataclass(frozen=True)
class OpenClawPaths:
    workspace_dir: Path
    data_dir: Path
    plugin_dir: Path
    adapter_dir: Path
    manifest_path: Path
    config_path: Path

    @classmethod
    def from_workspace(cls, workspace_dir: Path) -> "OpenClawPaths":
        workspace = workspace_dir.expanduser().resolve()
        data_dir = workspace / "autoskill-lc"
        plugin_dir = workspace / "plugins" / "autoskill-lc-openclaw"
        adapter_dir = workspace / "extensions" / PLUGIN_ID
        manifest_path = plugin_dir / "install-manifest.json"
        config_path = workspace / "openclaw.json"
        return cls(
            workspace_dir=workspace,
            data_dir=data_dir,
            plugin_dir=plugin_dir,
            adapter_dir=adapter_dir,
            manifest_path=manifest_path,
            config_path=config_path,
        )

