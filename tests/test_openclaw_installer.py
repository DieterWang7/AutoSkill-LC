import json
from pathlib import Path

from autoskill_lc.openclaw.config import PLUGIN_ID
from autoskill_lc.openclaw.installer import (
    OpenClawInstallOptions,
    install_openclaw_adapter,
    uninstall_openclaw_adapter,
)


def test_install_openclaw_adapter_writes_config_and_manifest(tmp_path: Path) -> None:
    workspace = tmp_path / "openclaw"
    options = OpenClawInstallOptions(workspace_dir=workspace)

    install_openclaw_adapter(options)

    config = json.loads((workspace / "openclaw.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (workspace / "plugins" / "autoskill-lc-openclaw" / "install-manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert PLUGIN_ID in config["plugins"]["entries"]
    assert str(workspace / "extensions" / PLUGIN_ID) in config["plugins"]["load"]["paths"]
    assert manifest["pluginId"] == PLUGIN_ID


def test_uninstall_openclaw_adapter_removes_plugin_wiring(tmp_path: Path) -> None:
    workspace = tmp_path / "openclaw"
    options = OpenClawInstallOptions(workspace_dir=workspace)

    install_openclaw_adapter(options)
    uninstall_openclaw_adapter(options, purge_data=True)

    config = json.loads((workspace / "openclaw.json").read_text(encoding="utf-8"))

    assert PLUGIN_ID not in config["plugins"]["entries"]
    assert not (workspace / "extensions" / PLUGIN_ID).exists()
    assert not (workspace / "plugins" / "autoskill-lc-openclaw").exists()
    assert not (workspace / "autoskill-lc").exists()
