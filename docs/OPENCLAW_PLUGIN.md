# OpenClaw Native Plugin Packaging

AutoSkill-LC now ships an OpenClaw plugin wrapper package in addition to the
Python runtime.

## What changed

- root `package.json` declares `openclaw.extensions`
- root `index.js`, `setup-entry.js`, and `openclaw.plugin.json` provide a
  direct local-directory plugin root
- plugin root lives in `extensions/autoskill-lc-openclaw/`
- plugin manifest is `extensions/autoskill-lc-openclaw/openclaw.plugin.json`
- plugin ships a skill pack under `extensions/autoskill-lc-openclaw/skills/`

This matches the OpenClaw plugin packaging contract for
`openclaw plugins install <npm-spec>` and local installs such as:

```bash
openclaw plugins install .
```

## Enable after install

After installing, explicitly enable the plugin and restart the Gateway:

```bash
openclaw plugins enable autoskill-lc-openclaw
openclaw gateway restart
```

Then verify:

```bash
openclaw plugins list
```

And test inside OpenClaw chat:

```text
/autoskill-status
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

If `/autoskill-status` falls through to the model, the plugin was discovered
but its commands were not registered into the running Gateway process. In
practice this usually means one of:

- the plugin is not enabled
- the Gateway was not restarted after install
- the plugin entrypoint did not load successfully

## Server E2E helper

For a full server-side validation run:

```bash
bash examples/openclaw/server-e2e.sh
```

This helper syncs the repository, runs `pytest`, validates the plugin package
root with `npm pack --dry-run`, installs the plugin, enables it, and restarts
the Gateway.
