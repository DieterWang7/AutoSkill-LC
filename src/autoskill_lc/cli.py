from __future__ import annotations

import argparse
from pathlib import Path

from autoskill_lc.openclaw.adapter import OpenClawAdapter
from autoskill_lc.openclaw.installer import (
    OpenClawInstallOptions,
    install_openclaw_adapter,
    uninstall_openclaw_adapter,
)
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

    return parser


def _make_install_options(args: argparse.Namespace) -> OpenClawInstallOptions:
    return OpenClawInstallOptions(
        workspace_dir=Path(args.workspace_dir),
        report_name=args.report_name,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "openclaw-install":
            options = _make_install_options(args)
            if not options.workspace_dir.exists():
                print(f"Error: Workspace directory does not exist: {options.workspace_dir}")
                return 1
            install_openclaw_adapter(options)
            print(f"OpenClaw adapter installed to: {options.workspace_dir}")
            print(f"Data directory: {options.data_dir}")
            return 0

        if args.command == "openclaw-uninstall":
            options = OpenClawInstallOptions(workspace_dir=Path(args.workspace_dir))
            if not options.workspace_dir.exists():
                print(f"Error: Workspace directory does not exist: {options.workspace_dir}")
                return 1
            uninstall_openclaw_adapter(options, purge_data=args.purge_data)
            print(f"OpenClaw adapter uninstalled from: {options.workspace_dir}")
            if args.purge_data:
                print("All data purged.")
            return 0

        if args.command == "openclaw-maintain":
            options = _make_install_options(args)
            if not options.workspace_dir.exists():
                print(f"Error: Workspace directory does not exist: {options.workspace_dir}")
                return 1
            adapter = OpenClawAdapter.for_workspace(options.workspace_dir)
            report_path = options.data_dir / "reports" / options.report_name
            recommendations = run_maintenance(
                adapter,
                job=MaintenanceJob(
                    adapter_name=adapter.name,
                    report_path=report_path,
                ),
            )
            print(f"Maintenance completed. Report written to: {report_path}")
            print(f"Recommendations generated: {len(recommendations)}")
            for rec in recommendations:
                print(f"  - [{rec.action.value}] {rec.topic} (confidence: {rec.confidence:.2f})")
            return 0

        parser.error(f"Unsupported command: {args.command}")
        return 2
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

