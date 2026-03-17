# Architecture

## Positioning

AutoSkill-LC is designed as a host-agnostic governance engine for skill
lifecycle management.

The engine does not own the host runtime. It only consumes conversation
signals and skill inventory snapshots, then produces governance
recommendations.

## Layers

### 1. Core engine

Responsibilities:

- normalize conversation-derived signals
- decide whether a skill should be added, upgraded, deprecated, or removed
- provide explainable recommendations with evidence and confidence

### 2. Adapter layer

Each host gets an isolated adapter.

Examples:

- `adapter-openclaw`
- `adapter-claude`
- `adapter-chatgpt`
- `adapter-gemini`

Responsibilities:

- collect archived conversation signals
- read current skill inventory
- mirror approved skills into the host workspace
- expose host capabilities such as cron and hot uninstall

### 3. Runtime layer

Responsibilities:

- run maintenance jobs on schedule
- keep idle resource usage near zero
- generate reports instead of mutating host state silently

### 4. Governance reporting

Responsibilities:

- serialize recommendations
- keep evidence trails
- support review, rollback, and audit flows

## Non-goals

- patching host core logic
- forcing a custom gateway or backend
- requiring a permanently running sidecar

## OpenClaw-first strategy

OpenClaw is the first adapter because it already has a clear plugin and cron
story. The core engine must stay independent so later adapters can reuse the
same logic.

