# Adapters

## Principle

Each host integration must be replaceable and removable without touching host
core logic.

The adapter contract is intentionally narrow:

- collect normalized conversation signals
- list current skill inventory
- emit governance reports

## OpenClaw

The first adapter targets OpenClaw.

Bootstrap behavior:

- writes one plugin entry into `openclaw.json`
- creates an isolated plugin home under `plugins/autoskill-lc-openclaw`
- writes an adapter descriptor into `extensions/autoskill-lc-openclaw-adapter`
- stores AutoSkill-LC data under `autoskill-lc/`

The adapter does not patch OpenClaw core. It only gives OpenClaw a path to a
plugin and a maintenance contract.

After install or uninstall, OpenClaw Gateway must be restarted because
`plugins.*` is part of the restart-required configuration surface.

## Future adapters

- Claude
- ChatGPT
- Gemini

Future adapters should reuse the same governance engine and report schema.
