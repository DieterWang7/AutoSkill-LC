---
name: autoskill-lc-governance
description: Use AutoSkill-LC governance reports, maintenance commands, and exported conversation ingestion for OpenClaw.
---

# AutoSkill-LC Governance

Use this skill when the workspace has the `autoskill-lc-openclaw` plugin enabled.

## What this plugin provides

- `/autoskill-status` to inspect report and data paths
- `/autoskill-maintain` to run the Python maintenance pipeline
- `/autoskill-ingest <export-json-path>` to ingest exported OpenClaw conversation JSON

## Expected workflow

1. Export or prepare an OpenClaw conversation JSON file.
2. Run `/autoskill-ingest <path>`.
3. Run `/autoskill-maintain`.
4. Review the latest governance report under `~/.openclaw/autoskill-lc/reports/`.

## Constraints

- The Python package `autoskill-lc` must be installed and available via `python -m autoskill_lc.cli`.
- The plugin does not patch OpenClaw core behavior.
- Install or uninstall changes require a Gateway restart.
