# Runtime Layout

## Current production convention

- runtime code: `/opt/openclaw/vendor/autoskill-lc`
- plugin entrypoint: `/root/.openclaw/extensions/autoskill-lc-openclaw`
- governance data: `/root/.openclaw/autoskill-lc`
- config: `/root/.openclaw/openclaw.json`

## Why this layout

- runtime code should not live under `/root` long term
- plugin entrypoints must remain inside the OpenClaw extension scan path
- governance data should stay with the OpenClaw home for auditability
- config must remain where the authoritative service actually reads it

## Common mistake

Do not assume `/home/ubuntu/.openclaw` is production just because SSH lands on
`ubuntu`.

Always verify the real gateway owner and active service first.
