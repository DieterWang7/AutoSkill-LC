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

## Output

Generated files are stored under:

```text
<CODEX_HOME>/autoskill-lc/
```

Including:

- `signals/*.json`
- `inventory/skills.json`
- `reports/*.json`
