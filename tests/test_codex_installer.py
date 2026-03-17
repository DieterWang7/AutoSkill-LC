import json
from pathlib import Path

from autoskill_lc.codex.installer import (
    CodexInstallOptions,
    install_codex_adapter,
    uninstall_codex_adapter,
)


def test_install_codex_adapter_creates_manifest_and_skill(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"

    manifest = install_codex_adapter(CodexInstallOptions(codex_home=codex_home))

    manifest_path = codex_home / "autoskill-lc" / "install-manifest.json"
    skill_path = codex_home / "skills" / "autoskill-lc-governance" / "SKILL.md"
    inventory_path = codex_home / "autoskill-lc" / "inventory" / "skills.json"

    assert manifest_path.exists()
    assert skill_path.exists()
    assert inventory_path.exists()

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["adapterId"] == "autoskill-lc-codex-adapter"
    assert str(skill_path) in payload["managedFiles"]
    assert str(codex_home / "autoskill-lc" / "signals") in payload["managedDirectories"]


def test_uninstall_codex_adapter_removes_only_manifest_paths(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    sessions_dir = codex_home / "sessions" / "2026"
    other_skill_dir = codex_home / "skills" / "existing-skill"
    sessions_dir.mkdir(parents=True)
    other_skill_dir.mkdir(parents=True)
    (codex_home / "config.toml").write_text("model = 'gpt-5.4'\n", encoding="utf-8")
    (codex_home / "history.jsonl").write_text("{}\n", encoding="utf-8")
    (sessions_dir / "session.jsonl").write_text("{}\n", encoding="utf-8")
    (other_skill_dir / "SKILL.md").write_text("# Existing skill\n", encoding="utf-8")

    install_codex_adapter(CodexInstallOptions(codex_home=codex_home))
    uninstall_codex_adapter(CodexInstallOptions(codex_home=codex_home))

    assert (codex_home / "config.toml").exists()
    assert (codex_home / "history.jsonl").exists()
    assert (sessions_dir / "session.jsonl").exists()
    assert (other_skill_dir / "SKILL.md").exists()

    assert not (codex_home / "autoskill-lc" / "install-manifest.json").exists()
    assert not (codex_home / "skills" / "autoskill-lc-governance").exists()


def test_uninstall_without_manifest_is_safe_noop(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    (codex_home / "config.toml").parent.mkdir(parents=True)
    (codex_home / "config.toml").write_text("safe = true\n", encoding="utf-8")

    uninstall_codex_adapter(CodexInstallOptions(codex_home=codex_home))

    assert (codex_home / "config.toml").exists()
