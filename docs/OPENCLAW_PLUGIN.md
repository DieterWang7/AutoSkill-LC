# OpenClaw Native Plugin Packaging

AutoSkill-LC now ships an OpenClaw plugin wrapper package in addition to the
Python runtime.

## What changed

- root `package.json` declares `openclaw.extensions`
- plugin root lives in `extensions/autoskill-lc-openclaw/`
- plugin manifest is `extensions/autoskill-lc-openclaw/openclaw.plugin.json`
- plugin ships a skill pack under `extensions/autoskill-lc-openclaw/skills/`

This matches the OpenClaw plugin packaging contract for
`openclaw plugins install <npm-spec>` and local installs such as:

```bash
openclaw plugins install .
```

## Runtime model

The plugin wrapper is intentionally thin.

- OpenClaw loads the Node plugin package
- slash commands call the Python runtime with `python -m autoskill_lc.cli`
- governance state still lives under `~/.openclaw/autoskill-lc/`

## Commands exposed by the plugin

- `/autoskill-status`
- `/autoskill-maintain`
- `/autoskill-ingest <export-json-path>`

## Current limitation

The plugin wrapper requires the Python package to be available on the host.
The OpenClaw plugin install step does not install Python dependencies by
itself.
