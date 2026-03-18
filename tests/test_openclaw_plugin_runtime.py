from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_openclaw_plugin_commands_load_disk_config_when_context_config_missing(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    workspace_dir = tmp_path / ".openclaw"
    workspace_dir.mkdir(parents=True)

    (workspace_dir / "openclaw.json").write_text(
        json.dumps(
            {
                "plugins": {
                    "entries": {
                        "autoskill-lc-openclaw": {
                            "enabled": True,
                            "config": {
                                "pythonCommand": sys.executable,
                                "workspaceDir": str(workspace_dir),
                                "reportName": "latest-governance-report.json",
                            },
                        }
                    }
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    script = f"""
import plugin from {json.dumps((root / "extensions" / "autoskill-lc-openclaw" / "index.js").as_uri())};

const commands = new Map();
const api = {{
  registerCommand(definition) {{
    commands.set(definition.name, definition);
  }},
  registerGatewayMethod() {{}},
  registerCli() {{}}
}};

plugin(api);
const command = commands.get("autoskill-cl");
const result = command.handler({{
  pluginConfig: undefined,
  args: "",
  cwd: {json.dumps(str(workspace_dir))}
}});
console.log(JSON.stringify(result));
"""

    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=root,
        env={
            **os.environ,
            "PYTHONPATH": str(root / "src"),
        },
        check=True,
    )

    payload = json.loads(completed.stdout)
    text = payload["text"]

    assert "spawnSync python ENOENT" not in text
    assert "AutoSkill-LC 执行报告" in text
    assert str(workspace_dir / "autoskill-lc" / "reports" / "latest-governance-report.json") in text
