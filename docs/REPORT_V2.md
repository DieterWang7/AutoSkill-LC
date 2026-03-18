# Report V2

## Goal

Report v2 separates "what can be merged into a skill now" from everything that
should only be tracked or escalated.

## Sections

### 1. recommendations

The raw governance engine output:

- `add`
- `upgrade`
- `deprecate`
- `remove`

### 2. evidenceBackedEvolutions

Conversation evidence is strong enough to justify skill evolution.

Expected use:

- merge reusable experience into an existing skill
- create a new skill when no coverage exists
- preserve evidence and rationale for audit

### 3. candidateOnly

Interesting but unproven material.

Expected use:

- do not mutate skill bodies
- keep as a queue for future confirmation

### 4. unresolvedRequirements

User requests that appeared in conversation but were not completed.

Expected use:

- remind the operator
- propose the next implementation step

### 5. toolingNeeded

Requirements that need tool support rather than prompt-only refinement.

Expected use:

- list up to three reference projects
- explain why tooling is required

### 6. impossibleItems

Requests blocked by host limitations or missing prerequisites.

Expected use:

- explain the blocker
- list prerequisites or the reason it is not currently feasible

### 7. display

A human-readable operator layer that must present:

- `本次识别出的经验`
- `治理建议`
- `遗忘需求提醒`
- `需要工具实现`
- `当前不可实现`
- `过去到上个检查点...核心沉淀`

If a section has no items, it must explicitly say `无`.

## Signal metadata

Signals can optionally include:

- `report_classification`
- `missing_requirement`
- `next_step`
- `tool_references`
- `prerequisites`

These fields are adapter-neutral and can be emitted by OpenClaw, Codex, or any
future host without changing the report schema.

## Design rule

Report v2 is an AutoSkill-LC core capability, not a standalone skill. This
keeps the evidence gate inside the governance engine lifecycle and avoids
creating overlapping policy skills.
