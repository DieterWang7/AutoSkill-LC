from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from autoskill_lc.codex.adapter import CodexAdapter
from autoskill_lc.codex.exporter import ingest_codex_session, ingest_codex_sessions_directory
from autoskill_lc.codex.installer import (
    CodexInstallOptions,
    install_codex_adapter,
    uninstall_codex_adapter,
)
from autoskill_lc.codex.status import build_codex_status
from autoskill_lc.openclaw.adapter import OpenClawAdapter
from autoskill_lc.openclaw.exporter import ingest_openclaw_export
from autoskill_lc.openclaw.installer import (
    OpenClawInstallOptions,
    install_openclaw_adapter,
    uninstall_openclaw_adapter,
)
from autoskill_lc.openclaw.status import build_openclaw_status
from autoskill_lc.runtime.contracts import MaintenanceJob
from autoskill_lc.runtime.maintenance import run_maintenance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="autoskill-lc")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("openclaw-install")
    install_parser.add_argument("--workspace-dir", required=True)
    install_parser.add_argument("--report-name", default="latest-governance-report.json")

    uninstall_parser = subparsers.add_parser("openclaw-uninstall")
    uninstall_parser.add_argument("--workspace-dir", required=True)
    uninstall_parser.add_argument("--purge-data", action="store_true")

    maintain_parser = subparsers.add_parser("openclaw-maintain")
    maintain_parser.add_argument("--workspace-dir", required=True)
    maintain_parser.add_argument("--report-name", default="latest-governance-report.json")

    status_parser = subparsers.add_parser("openclaw-status")
    status_parser.add_argument("--workspace-dir", required=True)

    ingest_parser = subparsers.add_parser("openclaw-ingest-export")
    ingest_parser.add_argument("--workspace-dir", required=True)
    ingest_parser.add_argument("--input", required=True)
    ingest_parser.add_argument("--session-id")
    ingest_parser.add_argument("--topic")

    codex_status_parser = subparsers.add_parser("codex-status")
    codex_status_parser.add_argument("--codex-home", required=True)

    codex_install_parser = subparsers.add_parser("codex-install")
    codex_install_parser.add_argument("--codex-home", required=True)
    codex_install_parser.add_argument("--no-skill", action="store_true")

    codex_uninstall_parser = subparsers.add_parser("codex-uninstall")
    codex_uninstall_parser.add_argument("--codex-home", required=True)

    codex_ingest_parser = subparsers.add_parser("codex-ingest-session")
    codex_ingest_parser.add_argument("--codex-home", required=True)
    codex_ingest_parser.add_argument("--input", required=True)
    codex_ingest_parser.add_argument("--session-id")
    codex_ingest_parser.add_argument("--topic")

    codex_ingest_all_parser = subparsers.add_parser("codex-ingest-all")
    codex_ingest_all_parser.add_argument("--codex-home", required=True)
    codex_ingest_all_parser.add_argument("--sessions-dir")

    codex_maintain_parser = subparsers.add_parser("codex-maintain")
    codex_maintain_parser.add_argument("--codex-home", required=True)
    codex_maintain_parser.add_argument("--report-name", default="latest-governance-report.json")

    return parser


def _make_install_options(args: argparse.Namespace) -> OpenClawInstallOptions:
    return OpenClawInstallOptions(
        workspace_dir=Path(args.workspace_dir),
        report_name=getattr(args, "report_name", "latest-governance-report.json"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "openclaw-install":
            options = _make_install_options(args)
            install_openclaw_adapter(options)
            print(f"Installed AutoSkill-LC OpenClaw adapter into {options.workspace_dir}")
            return 0

        if args.command == "openclaw-uninstall":
            options = OpenClawInstallOptions(workspace_dir=Path(args.workspace_dir))
            uninstall_openclaw_adapter(options, purge_data=args.purge_data)
            print(f"Uninstalled AutoSkill-LC OpenClaw adapter from {options.workspace_dir}")
            return 0

        if args.command == "openclaw-maintain":
            options = _make_install_options(args)
            adapter = OpenClawAdapter.for_workspace(options.workspace_dir)
            report_path = options.data_dir / "reports" / options.report_name
            recommendations = run_maintenance(
                adapter,
                job=MaintenanceJob(
                    adapter_name=adapter.name,
                    report_path=report_path,
                ),
            )
            print(
                json.dumps(
                    {
                        "ok": True,
                        "reportPath": str(report_path),
                        "recommendationCount": len(recommendations),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if args.command == "openclaw-status":
            payload = build_openclaw_status(Path(args.workspace_dir))
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "openclaw-ingest-export":
            input_path = Path(args.input)
            if not input_path.exists():
                raise FileNotFoundError(f"Input export file does not exist: {input_path}")
            result = ingest_openclaw_export(
                Path(args.workspace_dir),
                input_path,
                session_id=args.session_id,
                topic=args.topic,
            )
            print(
                json.dumps(
                    {
                        "ok": True,
                        "inputPath": str(result.input_path),
                        "outputPath": str(result.output_path),
                        "signalCount": result.signal_count,
                        "sessionId": result.session_id,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if args.command == "codex-status":
            payload = build_codex_status(Path(args.codex_home))
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "codex-install":
            options = CodexInstallOptions(
                codex_home=Path(args.codex_home),
                install_skill=not args.no_skill,
            )
            manifest = install_codex_adapter(options)
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 0

        if args.command == "codex-uninstall":
            uninstall_codex_adapter(CodexInstallOptions(codex_home=Path(args.codex_home)))
            print(
                json.dumps(
                    {
                        "ok": True,
                        "codexHome": str(Path(args.codex_home).expanduser().resolve()),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if args.command == "codex-ingest-session":
            input_path = Path(args.input)
            if not input_path.exists():
                raise FileNotFoundError(f"Input session file does not exist: {input_path}")
            result = ingest_codex_session(
                Path(args.codex_home),
                input_path,
                session_id=args.session_id,
                topic=args.topic,
            )
            print(
                json.dumps(
                    {
                        "ok": True,
                        "inputPath": str(result.input_path),
                        "outputPath": str(result.output_path),
                        "signalCount": result.signal_count,
                        "sessionId": result.session_id,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if args.command == "codex-ingest-all":
            sessions_dir = Path(args.sessions_dir) if args.sessions_dir else None
            results = ingest_codex_sessions_directory(
                Path(args.codex_home),
                sessions_dir=sessions_dir,
            )
            print(
                json.dumps(
                    {
                        "ok": True,
                        "ingestedFiles": len(results),
                        "signalsWritten": sum(item.signal_count for item in results),
                        "outputs": [str(item.output_path) for item in results],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if args.command == "codex-maintain":
            codex_home = Path(args.codex_home)
            adapter = CodexAdapter.for_home(codex_home)
            report_path = adapter.paths.data_dir / "reports" / args.report_name
            recommendations = run_maintenance(
                adapter,
                job=MaintenanceJob(
                    adapter_name=adapter.name,
                    report_path=report_path,
                ),
            )
            print(
                json.dumps(
                    {
                        "ok": True,
                        "reportPath": str(report_path),
                        "recommendationCount": len(recommendations),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        parser.error(f"Unsupported command: {args.command}")
        return 2
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
