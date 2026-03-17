# AutoSkill-LC

AutoSkill-LC = Loosely-Coupled, Self-Evolving, Host-Agnostic Skill Governance Engine.

OpenClaw is the first official adapter. Claude, ChatGPT, Gemini adapters are planned.

## What This Does

AutoSkill-LC watches conversation patterns between users and AI hosts, then recommends:
- **ADD** new skills when recurring uncovered patterns emerge
- **UPGRADE** skills when corrections indicate evolution is needed
- **DEPRECATE** skills that have been inactive for too long
- **REMOVE** deprecated skills past their removal window

Key principles:
- Host systems remain untouched and removable
- Runs maintenance only when scheduled (no resident resource usage)
- All recommendations include confidence scores and evidence
- Rollback is a first-class workflow

## Quick Start

```bash
# Install in development mode
python -m pip install -e .[dev]

# Install OpenClaw adapter
autoskill-lc openclaw-install --workspace-dir ~/.openclaw

# Run maintenance (reads signals, analyzes, writes report)
autoskill-lc openclaw-maintain --workspace-dir ~/.openclaw

# Uninstall when done
autoskill-lc openclaw-uninstall --workspace-dir ~/.openclaw --purge-data
```

## OpenClaw Cron Integration

Add to your crontab for daily maintenance:

```cron
# Daily at 2 AM
0 2 * * * /usr/bin/autoskill-lc openclaw-maintain --workspace-dir ~/.openclaw
```

Or use systemd timer for more control over wake-only execution.

## Project Status

**Current: OpenClaw-first MVP**

This release focuses on OpenClaw adapter stability. The core architecture is host-agnostic - Claude, ChatGPT, and Gemini adapters will follow using the same governance engine.

| Adapter | Status |
|---------|--------|
| OpenClaw | Available |
| Claude | Planned |
| ChatGPT | Planned |
| Gemini | Planned |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Host Systems                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │OpenClaw │  │ Claude  │  │ ChatGPT │  │ Gemini  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
└───────┼────────────┼────────────┼────────────┼─────────────┘
        │            │            │            │
        └────────────┴──────┬─────┴────────────┘
                            │
              ┌─────────────▼─────────────┐
              │   Host Adapters           │
              │   (OpenClawAdapter, etc)  │
              └─────────────┬─────────────┘
                            │
              ┌─────────────▼─────────────┐
              │   Governance Engine       │
              │   (Host-agnostic core)    │
              └─────────────┬─────────────┘
                            │
              ┌─────────────▼─────────────┐
              │   Recommendations         │
              │   (ADD/UPGRADE/DEPRECATE/ │
              │    REMOVE)                │
              └───────────────────────────┘
```

## Directory Structure

```
OpenClaw production host
├── /opt/openclaw/vendor/autoskill-lc/      # AutoSkill-LC runtime code + venv
├── /root/.openclaw/extensions/
│   └── autoskill-lc-openclaw/              # OpenClaw plugin entrypoint
├── /root/.openclaw/autoskill-lc/           # AutoSkill-LC data directory
│   ├── signals/                            # Conversation signals (*.json)
│   ├── inventory/                          # Skill inventory (skills.json)
│   └── reports/                            # Governance reports
└── /root/.openclaw/openclaw.json           # OpenClaw configuration

Codex host
├── ~/.codex/autoskill-lc/                  # AutoSkill-LC data directory
│   ├── signals/
│   ├── inventory/
│   ├── reports/
│   └── install-manifest.json
└── ~/.codex/skills/autoskill-lc-governance/
    └── SKILL.md
```

## Host Path Conventions

OpenClaw and Codex use different filesystem roles:

- OpenClaw runtime code belongs outside the OpenClaw data directory.
- OpenClaw plugin/config/state stays under `~/.openclaw`.
- Codex adapter data stays under `~/.codex/autoskill-lc`.

Current recommended production layout for OpenClaw:

- runtime: `/opt/openclaw/vendor/autoskill-lc`
- plugin entrypoint: `/root/.openclaw/extensions/autoskill-lc-openclaw`
- governance data: `/root/.openclaw/autoskill-lc`
- config: `/root/.openclaw/openclaw.json`

Current recommended layout for Codex:

- data: `~/.codex/autoskill-lc`
- optional skill: `~/.codex/skills/autoskill-lc-governance`

## Signal File Format

Place JSON files in `autoskill-lc/signals/`:

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

## Skill Inventory Format

Place in `autoskill-lc/inventory/skills.json`:

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

## Report Output

Reports are written to `autoskill-lc/reports/latest-governance-report.json`:

```json
{
  "host": "openclaw",
  "generatedAt": "2026-03-18T14:00:00+00:00",
  "recommendationCount": 2,
  "recommendations": [
    {
      "action": "add",
      "topic": "git release workflow",
      "confidence": 0.91,
      "rationale": "A recurring pattern without coverage suggests a new skill.",
      "skill_id": null,
      "replacement_skill_id": null,
      "evidence": ["user asked for release notes 3 times"]
    }
  ]
}
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [docs/ROADMAP.md](docs/ROADMAP.md) - Development roadmap
- [docs/INSTALL.md](docs/INSTALL.md) - Detailed installation
- [docs/UNINSTALL.md](docs/UNINSTALL.md) - Safe uninstallation
- [docs/ADAPTERS.md](docs/ADAPTERS.md) - Adapter development guide

## Development

```bash
# Run tests
python -m pytest -q

# Run with coverage
python -m pytest --cov=autoskill_lc

# Type checking
python -m mypy src/autoskill_lc
```

## License

MIT License - see LICENSE file for details.
