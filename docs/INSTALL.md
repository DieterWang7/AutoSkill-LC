# Install

## Local bootstrap

```bash
python -m pip install -e .[dev]
autoskill-lc openclaw-install --workspace-dir ~/.openclaw
```

Then restart the OpenClaw Gateway so plugin discovery and `plugins.entries`
changes are applied.

## What installation creates

- plugin runtime home under `plugins/autoskill-lc-openclaw`
- adapter descriptor under `extensions/autoskill-lc-openclaw-adapter`
- data directories under `autoskill-lc/`
- a manifest file for uninstall and rollback
- one plugin entry in `openclaw.json`

## Data directories

- `autoskill-lc/signals`
- `autoskill-lc/inventory`
- `autoskill-lc/reports`
- `autoskill-lc/skills`

## Scheduled maintenance

The bootstrap is designed for wake-on-schedule execution.

The intended host flow is:

1. OpenClaw archives or exports normalized signals
2. host cron launches `autoskill-lc openclaw-maintain`
3. AutoSkill-LC writes a report and exits

The scheduler job itself should be created with `openclaw cron add` or the
Gateway cron API instead of direct `jobs.json` edits.

### Example cron job

```bash
openclaw cron add \
  --name "AutoSkill-LC maintenance" \
  --cron "0 3 * * *" \
  --session isolated \
  --message "Run autoskill-lc openclaw-maintain for ~/.openclaw and summarize the report path." \
  --announce
```

For tighter control, the host can instead trigger a local wrapper script that
executes:

```bash
autoskill-lc openclaw-maintain --workspace-dir ~/.openclaw
```
