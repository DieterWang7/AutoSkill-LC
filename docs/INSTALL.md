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

- `autoskill-lc/signals` - Conversation signals (*.json)
- `autoskill-lc/inventory` - Skill inventory (skills.json)
- `autoskill-lc/reports` - Governance reports
- `autoskill-lc/skills` - Skill storage

## Signal File Format

Create JSON files in `autoskill-lc/signals/`:

```json
[
  {
    "topic": "git release workflow",
    "evidence": ["user asked for release notes 3 times"],
    "confidence": 0.91,
    "observed_runs": 3,
    "existing_skill_id": null,
    "corrections": 0,
    "explicit_uninstall_request": false,
    "superseded_by": null,
    "last_observed_at": "2026-03-18T10:00:00Z"
  }
]
```

Fields:
- `topic` (required): Pattern topic or skill name
- `evidence`: List of supporting evidence strings
- `confidence`: 0.0-1.0 confidence score
- `observed_runs`: Number of times pattern observed
- `existing_skill_id`: ID of existing skill if pattern relates to one
- `corrections`: Number of user corrections
- `explicit_uninstall_request`: True if user requested removal
- `superseded_by`: ID of replacement skill
- `last_observed_at`: ISO 8601 timestamp

## Skill Inventory Format

Create `autoskill-lc/inventory/skills.json`:

```json
[
  {
    "skill_id": "skill-git-release",
    "title": "Git Release Notes",
    "version": "1.0.0",
    "usage_count": 15,
    "last_used_at": "2026-03-10T08:30:00Z",
    "status": "active"
  }
]
```

Fields:
- `skill_id` (required): Unique skill identifier
- `title` (required): Human-readable skill name
- `version` (required): Semantic version
- `usage_count`: Number of times skill was used
- `last_used_at`: ISO 8601 timestamp of last use
- `status`: "active", "deprecated", or other custom status

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

### Direct crontab entry

```cron
# Daily at 2 AM
0 2 * * * /usr/bin/autoskill-lc openclaw-maintain --workspace-dir ~/.openclaw
```

## Idempotent Installation

The installer is idempotent - running install multiple times is safe:

```bash
# First install
autoskill-lc openclaw-install --workspace-dir ~/.openclaw

# Safe to run again - updates config only
autoskill-lc openclaw-install --workspace-dir ~/.openclaw
```
