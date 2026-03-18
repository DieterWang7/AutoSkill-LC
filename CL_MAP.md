# AutoSkill-LC CL Map

## Purpose

This file is the CL-side upgrade map for `AutoSkill-LC`.

It answers four questions:

1. which files are CL-specific additions
2. which upstream files were modified lightly
3. which areas must be reviewed after syncing from upstream
4. which changes are host-runtime critical

The rule is simple:

- prefer additive files over invasive rewrites
- keep upstream execution flow intact whenever possible
- if upstream changes conflict with CL additions, update the smallest possible
  surface

## CL-specific additive files

These files or directories do not exist in the upstream bootstrap baseline and
should be preserved during future sync work.

### Root packaging for OpenClaw

- `package.json`
- `index.js`
- `setup-entry.js`
- `openclaw.plugin.json`
- `.npmignore`

### Core governance additions

- `src/autoskill_lc/core/reporting.py`
- `src/autoskill_lc/runtime/checkpoints.py`

### Codex adapter additions

- `src/autoskill_lc/codex/adapter.py`
- `src/autoskill_lc/codex/config.py`
- `src/autoskill_lc/codex/exporter.py`
- `src/autoskill_lc/codex/installer.py`
- `src/autoskill_lc/codex/reporting.py`
- `src/autoskill_lc/codex/status.py`
- `docs/CODEX_ADAPTER.md`
- `examples/codex/fresh-install-and-safe-uninstall.ps1`

### OpenClaw operational packaging and docs

- `docs/OPENCLAW_PLUGIN.md`
- `docs/OPENCLAW_EXPORTS.md`
- `examples/openclaw/server-e2e.sh`
- `extensions/autoskill-lc-openclaw/`

### Governance report v2 docs

- `docs/REPORT_V2.md`
- `docs/OPENCLAW_SERVER_SAFETY_SKILL_MERGE.md`

### External CL-managed skill source

This skill is intentionally outside the AutoSkill-LC runtime repo:

- `E:/HUA-TeamAssistant Project/HUA-Skills&Tools-Viceroy/skills/skill分类-服务器和网络/openclaw-server-safety/SKILL.md`

And linked into the active Codex skills directory via junction:

- `E:/C pan user/.codex/skills/openclaw-server-safety`

## Lightly modified upstream-facing files

These files are part of the normal execution surface and may need manual merge
review after pulling upstream updates.

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/INSTALL.md`
- `docs/ROADMAP.md`
- `src/autoskill_lc/adapters/base.py`
- `src/autoskill_lc/cli.py`
- `src/autoskill_lc/core/models.py`
- `src/autoskill_lc/openclaw/adapter.py`
- `src/autoskill_lc/openclaw/reporting.py`
- `src/autoskill_lc/openclaw/status.py`
- `src/autoskill_lc/runtime/maintenance.py`
- `src/autoskill_lc/openclaw/exporter.py`
- `src/autoskill_lc/codex/exporter.py`
- `src/autoskill_lc/codex/status.py`

## Runtime-critical path assumptions

### OpenClaw production

- runtime code: `/opt/openclaw/vendor/autoskill-lc`
- plugin entrypoint: `/root/.openclaw/extensions/autoskill-lc-openclaw`
- governance data: `/root/.openclaw/autoskill-lc`
- config: `/root/.openclaw/openclaw.json`

### Codex

- data: `~/.codex/autoskill-lc`
- optional skill: `~/.codex/skills/autoskill-lc-governance`

## Host-specific contracts added by CL

### Report v2

Reports now include these extra sections in addition to raw recommendations:

- `evidenceBackedEvolutions`
- `candidateOnly`
- `unresolvedRequirements`
- `toolingNeeded`
- `impossibleItems`

### Signal metadata extensions

Signals may include:

- `conversation_id`
- `conversation_title`
- `report_classification`
- `missing_requirement`
- `next_step`
- `tool_references`
- `prerequisites`

### Checkpoint markdown

Each maintenance run now writes:

- `~/.openclaw/autoskill-lc/checkpoint.md`
- `~/.codex/autoskill-lc/checkpoint.md`

The checkpoint file records:

- sequence
- run time
- conversation id
- conversation title
- upgraded skills
- removed/deprecated skills

It also stores `last_processed_at` in frontmatter so repeated maintenance runs
can skip already-processed signals and only analyze newer material.

## Upstream sync checklist

When syncing with upstream AutoSkill changes, review in this order:

1. `src/autoskill_lc/core/models.py`
2. `src/autoskill_lc/runtime/maintenance.py`
3. `src/autoskill_lc/adapters/base.py`
4. `src/autoskill_lc/openclaw/adapter.py`
5. `src/autoskill_lc/openclaw/reporting.py`
6. `src/autoskill_lc/openclaw/exporter.py`
7. `src/autoskill_lc/codex/exporter.py`
8. `src/autoskill_lc/cli.py`
9. `package.json` and root OpenClaw packaging files

## CL modification notes

### 2026-03-18 report v2

- added host-neutral report builder
- added signal metadata for evidence, unresolved requirements, tooling needs,
  and impossible items

### 2026-03-18 checkpoint tracking

- no existing `checkpoint.md` or checkpoint tracking file was found in the repo
- added `runtime/checkpoints.py` instead of rewriting the governance engine
- maintenance now reads `last_processed_at` from markdown frontmatter
- maintenance now appends a new checkpoint entry in reverse chronological order
- exporters now persist `conversation_id` and `conversation_title`
- status now exposes `checkpointPath`

### 2026-03-18 OpenClaw display migration

- OpenClaw plugin commands now render `report.display`
- added `/autoskill-cl` as a display-oriented alias
- legacy workspace script output is no longer the authoritative report source
- production cleanup should archive:
  - `workspace/scripts/autoskill_cl.sh`
  - `workspace/logs/autoskill_cl_*.log`
  - and replace HEARTBEAT references with plugin-command guidance

### 2026-03-18 OpenClaw command config fallback

- `extensions/autoskill-lc-openclaw/index.js` now falls back to
  `~/.openclaw/openclaw.json` when slash-command context omits `pluginConfig`
- this is required because Gateway methods and slash-command handlers do not
  always receive identical config payloads in production
- keep this fallback during future upstream sync unless OpenClaw guarantees
  command-context config injection

### 2026-03-18 UTC normalization for historical checkpoints

- normalize naive ISO datetimes to UTC across report/checkpoint parsing
- this preserves compatibility with older `checkpoint.md` entries written
  before timezone handling was hardened
- touched files:
  - `src/autoskill_lc/core/reporting.py`
  - `src/autoskill_lc/runtime/checkpoints.py`
  - `src/autoskill_lc/runtime/maintenance.py`
  - `src/autoskill_lc/openclaw/adapter.py`
  - `src/autoskill_lc/codex/adapter.py`
  - `src/autoskill_lc/openclaw/exporter.py`
  - `src/autoskill_lc/codex/exporter.py`

## Naming rule

- functional/runtime files must use English names
- non-functional narrative documents may use Chinese names

## Merge policy

- if upstream adds new execution behavior, keep upstream as the source of truth
- re-apply CL changes as adapters, packaging, docs, or optional metadata only
- avoid rewriting upstream files when an additive helper or wrapper can solve
  the problem
- document every new CL-only file here before release
