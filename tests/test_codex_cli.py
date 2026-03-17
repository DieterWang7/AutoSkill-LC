from pathlib import Path

from autoskill_lc.cli import build_parser, main


def test_cli_exposes_codex_install_and_uninstall() -> None:
    parser = build_parser()

    install_args = parser.parse_args(["codex-install", "--codex-home", "C:/tmp/.codex"])
    uninstall_args = parser.parse_args(["codex-uninstall", "--codex-home", "C:/tmp/.codex"])

    assert install_args.command == "codex-install"
    assert Path(install_args.codex_home) == Path("C:/tmp/.codex")
    assert uninstall_args.command == "codex-uninstall"


def test_cli_runs_codex_install_and_uninstall(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    (codex_home / "config.toml").parent.mkdir(parents=True)
    (codex_home / "config.toml").write_text("model='gpt-5.4'\n", encoding="utf-8")

    install_exit = main(["codex-install", "--codex-home", str(codex_home)])
    uninstall_exit = main(["codex-uninstall", "--codex-home", str(codex_home)])

    assert install_exit == 0
    assert uninstall_exit == 0
    assert (codex_home / "config.toml").exists()
    assert not (codex_home / "autoskill-lc" / "install-manifest.json").exists()
