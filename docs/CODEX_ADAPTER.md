# Codex Adapter

AutoSkill-LC can ingest local Codex CLI session logs and turn them into
normalized governance signals.

## Supported source

Codex stores local session data under `CODEX_HOME`, commonly:

```text
~/.codex/sessions/**/*.jsonl
```

This aligns with public Codex issue discussions that reference session files
under `~/.codex/sessions/...jsonl` and command history under
`CODEX_HOME/history.jsonl`.

## Commands

Install AutoSkill-LC into a local Codex home:

```bash
python -m pip install "git+https://github.com/DieterWang7/AutoSkill-LC.git"
autoskill-lc codex-install --codex-home ~/.codex
```

Uninstall only AutoSkill-LC managed files:

```bash
autoskill-lc codex-uninstall --codex-home ~/.codex
```

Ingest one session file:

```bash
autoskill-lc codex-ingest-session \
  --codex-home ~/.codex \
  --input ~/.codex/sessions/2026/rollout-123.jsonl
```

Ingest every session file under `CODEX_HOME/sessions`:

```bash
autoskill-lc codex-ingest-all --codex-home ~/.codex
```

Run maintenance:

```bash
autoskill-lc codex-maintain --codex-home ~/.codex
```

Inspect adapter status:

```bash
autoskill-lc codex-status --codex-home ~/.codex
```

## Install safety

The installer only writes under:

- `<CODEX_HOME>/autoskill-lc/**`
- `<CODEX_HOME>/skills/autoskill-lc-governance/**`

It records created files and directories in:

```text
<CODEX_HOME>/autoskill-lc/install-manifest.json
```

Uninstall deletes only manifest-listed paths. It does not modify:

- `<CODEX_HOME>/config.toml`
- `<CODEX_HOME>/history.jsonl`
- `<CODEX_HOME>/sessions/**`
- other skills under `<CODEX_HOME>/skills/*`

## Fresh install helper

On Windows, you can run:

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\codex\fresh-install-and-safe-uninstall.ps1
```

This performs a fresh GitHub install, prints adapter status, uninstalls the
adapter, and verifies that Codex core files remain intact.

## Output

Generated files are stored under:

```text
<CODEX_HOME>/autoskill-lc/
```

Including:

- `signals/*.json`
- `inventory/skills.json`
- `reports/*.json`
