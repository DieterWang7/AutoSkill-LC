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

AutoSkill-LC Report v2 classifies conversation evidence into five buckets:

- `evidenceBackedEvolutions`: confirmed experience worth merging into a skill
- `candidateOnly`: weak or incomplete evidence that should not mutate a skill yet
- `unresolvedRequirements`: user requirements mentioned but not completed
- `toolingNeeded`: requirements that need external tooling or integration work
- `impossibleItems`: requests blocked by host limitations or missing prerequisites

It also adds a human-readable `display` section for operators, with:

- identified experiences
- governance suggestions
- forgotten user requirements
- tooling-needed items with three reference projects
- impossible items with prerequisites
- one-line checkpoint window summary

Reports are written to `autoskill-lc/reports/latest-governance-report.json`:

```json
{
  "schemaVersion": "2.0",
  "host": "openclaw",
  "generatedAt": "2026-03-18T14:00:00+00:00",
  "recommendationCount": 2,
  "summary": {
    "evidenceBackedCount": 1,
    "candidateOnlyCount": 1,
    "unresolvedRequirementCount": 1,
    "toolingNeedCount": 1,
    "impossibleItemCount": 0,
    "actions": {
      "add": 1,
      "upgrade": 1,
      "deprecate": 0,
      "remove": 0
    }
  },
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
  ],
  "evidenceBackedEvolutions": [
    {
      "topic": "git release workflow",
      "confidence": 0.91,
      "evidence": ["user asked for release notes 3 times"],
      "recommendationAction": "add",
      "skillId": null,
      "rationale": "A recurring pattern without coverage suggests a new skill.",
      "lastObservedAt": "2026-03-18T10:00:00+00:00"
    }
  ],
  "candidateOnly": [
    {
      "topic": "single anecdotal optimization idea",
      "confidence": 0.31,
      "evidence": ["one weak example only"],
      "reason": "Evidence is not yet strong enough to modify a skill.",
      "nextStep": null
    }
  ],
  "unresolvedRequirements": [
    {
      "topic": "install provenance cleanup",
      "requirement": "Clean install provenance warning",
      "evidence": ["user requested cleanup but the task was deferred"],
      "nextStep": "Validate npm install provenance flow",
      "confidence": 0.6
    }
  ],
  "toolingNeeded": [
    {
      "topic": "nightly repository audit",
      "requirement": "Add scheduled repository audit",
      "evidence": ["requires automation support"],
      "referenceProjects": ["openai/codex", "openclaw/openclaw", "microsoft/vscode"],
      "confidence": 0.72
    }
  ],
  "impossibleItems": []
}
```

## Extended Signal Fields

Signals may optionally carry report governance hints:

```json
[
  {
    "topic": "install provenance cleanup",
    "evidence": ["user requested cleanup but the task was deferred"],
    "confidence": 0.6,
    "report_classification": "unresolved",
    "missing_requirement": "Clean install provenance warning",
    "next_step": "Validate npm install provenance flow",
    "tool_references": ["openai/codex", "openclaw/openclaw"],
    "prerequisites": ["Host install provenance API"]
  }
]
```

Supported `report_classification` values:

- `evidence_backed`
- `candidate_only`
- `unresolved`
- `tooling_needed`
- `impossible`

## Checkpoint Log

Each maintenance run also writes a markdown checkpoint file:

- OpenClaw: `~/.openclaw/autoskill-lc/checkpoint.md`
- Codex: `~/.codex/autoskill-lc/checkpoint.md`

The checkpoint keeps reverse-chronological entries with:

- sequence
- run time
- conversation ID
- conversation title
- upgraded skills
- removed or deprecated skills

The markdown frontmatter stores `last_processed_at`, so repeat runs can skip
older signals and focus on newly added conversation material.

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [docs/ROADMAP.md](docs/ROADMAP.md) - Development roadmap
- [docs/INSTALL.md](docs/INSTALL.md) - Detailed installation
- [docs/UNINSTALL.md](docs/UNINSTALL.md) - Safe uninstallation
- [docs/ADAPTERS.md](docs/ADAPTERS.md) - Adapter development guide
- [docs/REPORT_V2.md](docs/REPORT_V2.md) - Governance report v2 schema
- [docs/OPENCLAW_SERVER_SAFETY_SKILL_MERGE.md](docs/OPENCLAW_SERVER_SAFETY_SKILL_MERGE.md) - OpenClaw server safety skill merge plan
- [CL_MAP.md](CL_MAP.md) - CL-specific upgrade map

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
