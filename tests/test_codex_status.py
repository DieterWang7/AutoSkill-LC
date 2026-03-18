import json
from pathlib import Path

from autoskill_lc.codex.status import build_codex_status


def test_build_codex_status_counts_sessions_and_reports(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    session_dir = codex_home / "sessions" / "2026"
    reports_dir = codex_home / "autoskill-lc" / "reports"
    signals_dir = codex_home / "autoskill-lc" / "signals"
    inventory_dir = codex_home / "autoskill-lc" / "inventory"
    session_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    signals_dir.mkdir(parents=True)
    inventory_dir.mkdir(parents=True)

    (session_dir / "session-1.jsonl").write_text("{}", encoding="utf-8")
    (signals_dir / "session-1.json").write_text("[]", encoding="utf-8")
    (inventory_dir / "skills.json").write_text("[]", encoding="utf-8")
    (reports_dir / "latest.json").write_text(
        json.dumps({"recommendationCount": 2}),
        encoding="utf-8",
    )

    payload = build_codex_status(codex_home)

    assert payload["counts"]["sessionFiles"] == 1
    assert payload["counts"]["signalFiles"] == 1
    assert payload["latestReport"]["recommendationCount"] == 2
    assert payload["checkpoint"]["exists"] is False


def test_build_codex_status_reports_install_and_skill_presence(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    data_dir = codex_home / "autoskill-lc"
    skill_dir = codex_home / "skills" / "autoskill-lc-governance"
    data_dir.mkdir(parents=True)
    skill_dir.mkdir(parents=True)
    (data_dir / "install-manifest.json").write_text("{}", encoding="utf-8")
    (skill_dir / "SKILL.md").write_text("# AutoSkill-LC\n", encoding="utf-8")

    payload = build_codex_status(codex_home)

    assert payload["installed"] is True
    assert payload["skillInstalled"] is True
    assert payload["paths"]["manifestPath"].endswith("install-manifest.json")
    assert payload["paths"]["checkpointPath"].endswith("checkpoint.md")
