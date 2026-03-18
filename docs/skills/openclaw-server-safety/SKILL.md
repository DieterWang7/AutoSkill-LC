---
name: openclaw-server-safety
description: Production-safe OpenClaw server operations, including runtime discovery, service control, plugin deployment, verification, rollback, and cleanup.
status: ready
source: CL merged operational guide
---

# OpenClaw Server Safety

## Use this skill when

- operating a real OpenClaw server
- editing production `openclaw.json`
- deploying or repairing plugins
- troubleshooting gateway, dashboard, or skill discovery problems

## Core rule

Do not trust assumptions. Discover the real runtime first.

## Outcome target

Every operation must leave the server in this state:

- the authoritative gateway service is known
- config changes are reversible
- plugin and skill paths are explicit
- no shadow services or residue threads remain
- verification comes from CLI, gateway, and logs

## Mandatory order

1. identify the real service user
2. identify the real OpenClaw home
3. identify the authoritative service definition
4. back up config before edits
5. make surgical changes only
6. verify through CLI, gateway, and service status
7. clean residual services, backups, and temporary runtime copies

## Must verify first

- `whoami`
- `systemctl status openclaw-gateway.service --no-pager -l`
- `systemctl cat openclaw-gateway.service`
- `journalctl -u openclaw-gateway.service -n 120 --no-pager`
- `loginctl user-status root`
- `/root/.openclaw/openclaw.json` or the actual discovered config path

If a user service exists, verify it separately before touching production:

- `env XDG_RUNTIME_DIR=/run/user/0 systemctl --user status openclaw-gateway.service --no-pager -l`

## OpenClaw path convention

- runtime code: `/opt/openclaw/vendor/autoskill-lc`
- plugin entrypoint: `/root/.openclaw/extensions/autoskill-lc-openclaw`
- governance data: `/root/.openclaw/autoskill-lc`
- config: `/root/.openclaw/openclaw.json`

Treat deployment and directory conventions as part of this safety skill, not as
a separate skill.

## Hard prohibitions

- no blind overwrite of `openclaw.json`
- no `pkill`, `killall`, or ad-hoc `nohup` restarts
- no edits against the wrong user home
- no backup directories left inside live plugin scan paths

## Runtime discovery checklist

Confirm all of these before changing anything:

- which user owns the real gateway process
- which service definition is active
- whether a root user service is shadowing a system service
- whether the OpenClaw home is `/root/.openclaw` or another path
- whether the plugin scan directory contains stale backups or duplicates

## Safe config mutation protocol

1. back up the active `openclaw.json`
2. edit only the minimum required keys
3. keep existing unrelated entries intact
4. restart only the authoritative service
5. verify after restart

## Service management protocol

Use:

- `systemctl`
- `journalctl`
- `loginctl`

Never use broad process killing as a first-line fix.

If a shadow service exists:

- confirm which service owns the live port
- stop and disable only the wrong one
- re-verify the correct service afterwards

## Deployment and verification chapter

Plugin deployment and directory conventions belong inside this skill.

Always verify:

- `openclaw plugins list`
- `openclaw plugins doctor`
- `openclaw gateway call ...`
- `openclaw skills list --eligible`

When skills are newly installed, verify in a new session before concluding the
skill is missing.

## Dashboard and gateway troubleshooting

Check these before blaming skill files:

- wrong gateway instance bound to the port
- stale dashboard token
- missing scope such as `operator.read`
- stale UI session vs fresh CLI truth

## Rollback and cleanup rule

Every change must have:

- a config backup
- a path inventory
- a residue cleanup step

Residue cleanup includes:

- moving backup plugin folders out of live scan paths
- removing temporary runtime clones after migration
- stopping wrong shadow services
- ensuring no orphan process or ghost service remains

## Evidence sources

Trust these first:

- `systemctl status`
- `systemctl cat`
- `journalctl`
- `openclaw plugins doctor`
- `openclaw gateway call`
- `openclaw skills list --eligible`

## Appendices

See appendices for dated incidents, postmortems, and path migration notes.
