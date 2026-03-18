# OpenClaw Server Safety Skill Merge Plan

## Goal

Merge these scattered materials into one operational skill:

- the existing OpenClaw server safety guide
- plugin deployment and directory conventions
- real incident learnings from server-side maintenance

The result should be a single `OpenClaw server safety` skill rather than
multiple overlapping skills.

## Why merge

Following Occam's razor:

- `plugin deployment and path rules` are not a separate capability
- they are one chapter of server-safe OpenClaw operations
- operators should not decide between several near-duplicate safety skills

## Target skill scope

The merged skill should cover:

1. runtime identity and path discovery
2. safe config mutation
3. service management discipline
4. plugin deployment and verification
5. gateway and dashboard troubleshooting
6. rollback and residue cleanup

It should not cover:

- generic Linux administration
- unrelated business-domain skills
- host-agnostic AutoSkill report logic

## Source material to merge

### Core source

- `E:/HUA-TeamAssistant Project/输入-参数 范式/操作安全指南-OpenClaw服务器_20260211.md`

### CL runtime conventions

- `docs/OPENCLAW_PLUGIN.md`
- `docs/INSTALL.md`
- `CL_MAP.md`

### Incident-derived learnings

- root vs ubuntu runtime mismatch
- system service vs root user service port conflicts
- `loaded without install provenance` handling
- plugin scan directory pollution
- gateway token and scope verification

## Proposed merged structure

### 1. Intent

- this skill is for production-safe OpenClaw server work
- it must preserve service continuity and reversibility

### 2. Mandatory invariants

- always identify the real service user first
- always identify the real OpenClaw home first
- always back up `openclaw.json` before changes
- always prefer incremental edits over overwrite
- always verify through CLI or gateway, not AI explanation alone

### 3. Runtime discovery

- who runs the gateway
- which service definition is authoritative
- whether a user service is shadowing a system service
- where runtime code, plugin entrypoint, and data directories live

### 4. Safe config mutation protocol

- backup
- surgical write
- diff/validate
- restart only when needed
- verify after restart

### 5. Service management protocol

- use `systemctl` and `journalctl`
- avoid `nohup`, `pkill`, `killall`
- detect and remove shadow services carefully

### 6. Plugin and skill deployment protocol

- plugin placement rules
- skill discovery rules
- when a new session is required
- how to validate with `plugins list`, `plugins doctor`,
  `gateway call`, `skills list --eligible`

### 7. Dashboard and gateway troubleshooting

- token issues
- missing scope
- stale UI session
- wrong gateway instance bound to port

### 8. Rollback and cleanup

- restore config backup
- stop wrong service
- move scan-directory backups out of live extension paths
- remove temporary runtime clones
- ensure no residue threads or ghost services remain

### 9. Incident appendix

Move date-specific incidents into appendices so the skill body stays compact.

Examples:

- Telegram session expiry incident
- local skill discovery and stale session incident
- root user service port conflict incident

## Recommended repository shape

Use additive files instead of rewriting core execution files.

### Skill location

- `docs/skills/openclaw-server-safety/SKILL.md`

### Optional appendices

- `docs/skills/openclaw-server-safety/appendices/*.md`

This keeps the operational knowledge versioned in-repo without forcing it into
runtime code.

## Status

The first CL version of the merged skill now exists at:

- `docs/skills/openclaw-server-safety/SKILL.md`
- `docs/skills/openclaw-server-safety/appendices/`

## Migration strategy

### Phase 1

Create the merged skill draft and map each safety-guide section into:

- stable rule
- operational checklist
- incident appendix

### Phase 2

Extract only stable rules into the final skill body.

### Phase 3

Keep dated incidents as appendices, not as the core instruction path.

## What should be folded in

These items should be merged into the skill body:

- root vs ubuntu identity checks
- `/root/.openclaw` vs `/home/ubuntu/.openclaw`
- systemd system service priority
- config backup before edits
- plugin directory hygiene
- runtime path convention:
  - `/opt/openclaw/vendor/autoskill-lc`
  - `/root/.openclaw/extensions/autoskill-lc-openclaw`
  - `/root/.openclaw/autoskill-lc`

## What should not be folded in directly

These items should stay as appendices or examples:

- full dated postmortems
- one-off credentials
- one-off login commands with real secrets
- historical dead paths that no longer represent the current runtime

## Final rule

`OpenClaw server safety` is the parent skill.

`plugin deployment and directory norms` are one subsection inside it, not a
separate skill.
