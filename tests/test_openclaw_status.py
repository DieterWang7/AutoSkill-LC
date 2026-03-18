import json
from pathlib import Path

from autoskill_lc.openclaw.config import PLUGIN_ID
from autoskill_lc.openclaw.status import build_openclaw_status


def test_build_openclaw_status_reports_installation_and_latest_report(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    adapter_dir = workspace / "extensions" / PLUGIN_ID
    plugin_dir = workspace / "plugins" / "autoskill-lc-openclaw"
    reports_dir = workspace / "autoskill-lc" / "reports"
    signals_dir = workspace / "autoskill-lc" / "signals"
    inventory_dir = workspace / "autoskill-lc" / "inventory"

    adapter_dir.mkdir(parents=True)
    plugin_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    signals_dir.mkdir(parents=True)
    inventory_dir.mkdir(parents=True)

    (plugin_dir / "install-manifest.json").write_text("{}", encoding="utf-8")
    (signals_dir / "session-a.json").write_text("[]", encoding="utf-8")
    (inventory_dir / "skills.json").write_text("[]", encoding="utf-8")
    (reports_dir / "latest.json").write_text(
        json.dumps({"recommendationCount": 4}),
        encoding="utf-8",
    )

    payload = build_openclaw_status(workspace)

    assert payload["installed"] is True
    assert payload["pluginId"] == PLUGIN_ID
    assert payload["counts"]["signalFiles"] == 1
    assert payload["latestReport"]["recommendationCount"] == 4
    assert payload["checkpoint"]["exists"] is False
    assert payload["paths"]["checkpointPath"].endswith("checkpoint.md")
