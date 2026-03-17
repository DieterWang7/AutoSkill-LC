import json
from pathlib import Path


def test_package_json_declares_openclaw_extension() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "package.json").read_text(encoding="utf-8"))

    assert payload["openclaw"]["extensions"] == [
        "./extensions/autoskill-lc-openclaw/index.js"
    ]
    assert payload["openclaw"]["setupEntry"] == "./extensions/autoskill-lc-openclaw/setup-entry.js"


def test_openclaw_plugin_manifest_exposes_skill_pack() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads(
        (
            root
            / "extensions"
            / "autoskill-lc-openclaw"
            / "openclaw.plugin.json"
        ).read_text(encoding="utf-8")
    )

    assert payload["id"] == "autoskill-lc-openclaw"
    assert payload["skills"] == ["./skills"]
