from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SchedulePolicy:
    mode: str = "host-cron"
    wake_only: bool = True
    max_runtime_seconds: int = 300


@dataclass(frozen=True)
class MaintenanceJob:
    adapter_name: str
    report_path: Path
    checkpoint_path: Path | None = None
    dry_run: bool = True
    policy: SchedulePolicy = SchedulePolicy()
