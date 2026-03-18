# AutoSkill-LC Sustainable Evolution Architecture v1

## Purpose

This file defines how `AutoSkill-LC` should evolve continuously without
becoming noisy, destructive, or operationally opaque.

The target is not "auto-edit skills forever". The target is a governed loop:

1. collect usable conversation evidence
2. normalize and dedupe it
3. classify it by confidence and actionability
4. map it to the right skill target
5. generate minimal evolution patches
6. verify before apply
7. record every run for audit and rollback

## Non-negotiable rules

- evidence before mutation
- additive changes before invasive rewrites
- checkpoint and report are the operational truth
- low-information chatter must not enter the evolution path
- skill edits must be minimal, explainable, and reversible
- host-specific behavior belongs in adapters, not in the core engine

## Architecture layers

### 1. Ingestion

Responsible for turning host-native conversation artifacts into normalized
`signals`.

Current hosts:

- OpenClaw
- Codex

Future hosts:

- Claude
- ChatGPT
- Gemini

Required fields:

- `conversation_id`
- `conversation_title`
- `last_observed_at`
- `topic`
- `evidence`
- host-specific metadata needed by governance

### 2. Normalization

Responsible for cleaning noisy raw conversations before governance sees them.

Current responsibilities:

- filter greeting-only conversations
- compact long imperative requests into cleaner topics
- normalize timestamps
- dedupe repeated derived signals

Next responsibilities:

- semantic merge for near-duplicate topics
- host-specific cleanup dictionaries
- optional archival/TTL for stale signals

### 3. Governance

Responsible for deciding what the current evidence means.

Current buckets:

- `evidenceBackedEvolutions`
- `candidateOnly`
- `unresolvedRequirements`
- `toolingNeeded`
- `impossibleItems`

Decision rule:

- strong evidence can influence skill evolution
- weak evidence stays in report only
- unresolved/tooling/impossible items stay visible but do not mutate skills

### 4. Evolution

Responsible for turning approved evidence into concrete skill actions.

Target actions:

- map evidence to an existing skill
- decide whether to `add`, `upgrade`, `deprecate`, or `remove`
- generate a minimal patch
- annotate why the change happened

This layer must stay patch-oriented, not rewrite-oriented.

### 5. Verification

Responsible for proving that a generated change is safe enough to keep.

Verification types:

- structure validation
- semantic conflict checks
- regression examples
- rollback readiness

No "evolution complete" claim is valid without this layer.

### 6. Audit and rollback

Responsible for making every run explainable and reversible.

Operational truth files:

- `reports/latest-governance-report.json`
- `checkpoint.md`
- host inventory snapshots

Every evolution-capable run must answer:

- what was seen
- what was classified
- what was changed
- why it changed
- how to revert it

## Evolution gate model

AutoSkill-LC should only mutate a skill when all of the following are true:

1. the conversation carries real evidence
2. the evidence survives normalization
3. the topic is not merely a greeting or placeholder
4. the target skill can be identified, or a new skill is justified
5. the patch can be expressed as a minimal change
6. the change can be verified
7. the change can be rolled back

If any gate fails, the item must remain in the report only.

## Four evolution levels

### L1. Report only

- no skill mutation
- retain evidence in the report
- suitable for weak candidates

### L2. Candidate patch

- produce a patch proposal
- do not auto-apply
- suitable for moderate confidence items

### L3. Safe auto-apply

- apply low-risk, minimal changes automatically
- requires stable mapping and verification

### L4. Human approval

- required for structural or broad semantic changes
- report and patch must be reviewable before apply

## Minimal patch contract

A skill evolution patch should express only one of these operations:

- add a rule
- revise a specific section
- deprecate a narrow section
- add or update a change note header

The patch should include:

- timestamp
- reason
- evidence source
- checkpoint sequence
- summary of the exact delta

## Sustainable data flow

```text
host conversation
  -> exporter
  -> normalized signals
  -> checkpoint incremental filter
  -> governance engine
  -> report v2
  -> skill mapper
  -> patch generator
  -> verifier
  -> apply or hold
  -> checkpoint append
```

## Current maturity

Already implemented:

- host adapters for OpenClaw and Codex
- report v2
- checkpoint tracking
- low-information greeting filtering
- compact topic extraction for imperative requests
- OpenClaw chat display rendering through `report.display`

Not yet implemented:

- semantic merge of near-duplicate topics
- topic-to-skill mapper
- patch generator
- automated skill verifier
- rollback ledger beyond checkpoint summaries
- safe auto-apply policy tiers

## Priority order

### P0

- semantic merge
- topic-to-skill mapper
- patch generation contract

### P1

- verification layer
- rollback ledger
- stronger unresolved/tooling/impossible extraction

### P2

- cross-host consistency
- host capability matrix
- CI and doctor tooling

### P3

- safe auto-apply
- effect evaluation after skill evolution

## Relationship to roadmap

This file refines the roadmap rather than replacing it.

- Roadmap phases describe product milestones.
- This architecture defines the operational loop inside those milestones.

Use this file together with:

- `docs/ROADMAP.md`
- `docs/REPORT_V2.md`
- `CL_MAP.md`

## Rule for future CL work

When adding sustainable-evolution features:

- prefer additive files
- keep upstream execution flow intact
- record every CL-only file in `CL_MAP.md`
- if upstream changes overlap, re-apply the smallest possible wrapper
