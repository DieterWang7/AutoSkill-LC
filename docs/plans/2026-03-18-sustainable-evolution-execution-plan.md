# AutoSkill-LC Sustainable Evolution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn AutoSkill-LC from a report-producing governance engine into a sustainable skill-evolution system with semantic merge, skill mapping, patch generation, verification, and rollback discipline.

**Architecture:** Build on the existing report/checkpoint pipeline without rewriting the core engine. Add the missing sustainable-evolution modules as thin additive layers around normalized signals, governance output, and host adapters.

**Tech Stack:** Python, pytest, Node-based OpenClaw plugin wrapper, markdown/json runtime artifacts

---

## Scope

This plan follows:

- `DEVOLUTION.md`
- `docs/ROADMAP.md`
- `docs/REPORT_V2.md`

The execution order is intentionally conservative:

1. improve semantic quality before mutation
2. add mapping before patching
3. add patching before auto-apply
4. add verification before claiming sustainable evolution

## Feature checklist

### Feature A: Semantic merge

Purpose:

- merge near-duplicate topics before governance and reporting
- reduce report fragmentation

Deliverables:

- topic similarity normalization module
- merge policy tests
- merged topic summary in report/checkpoint context

Target files:

- Create: `src/autoskill_lc/core/semantic_merge.py`
- Modify: `src/autoskill_lc/runtime/maintenance.py`
- Modify: `src/autoskill_lc/core/reporting.py`
- Test: `tests/test_semantic_merge.py`

Acceptance:

- semantically similar topics converge into one canonical topic
- duplicate governance items are reduced

### Feature B: Topic-to-skill mapper

Purpose:

- determine which skill should absorb a given evidence-backed topic

Deliverables:

- mapper contract
- exact-match, alias, and fallback mapping logic
- report visibility for mapping confidence

Target files:

- Create: `src/autoskill_lc/core/skill_mapper.py`
- Modify: `src/autoskill_lc/core/models.py`
- Modify: `src/autoskill_lc/openclaw/adapter.py`
- Modify: `src/autoskill_lc/codex/adapter.py`
- Test: `tests/test_skill_mapper.py`

Acceptance:

- known topics map to existing skills when appropriate
- ambiguous topics remain candidates instead of misrouting

### Feature C: Patch generation contract

Purpose:

- turn a recommendation plus mapped target into a minimal patch proposal

Deliverables:

- patch proposal schema
- markdown header note contract
- minimal section-level patch generation

Target files:

- Create: `src/autoskill_lc/core/patches.py`
- Modify: `src/autoskill_lc/core/models.py`
- Modify: `src/autoskill_lc/core/reporting.py`
- Test: `tests/test_patches.py`

Acceptance:

- every patch proposal records reason, evidence, timestamp, and checkpoint link
- no full-file rewrites for narrow changes

### Feature D: Verification layer

Purpose:

- ensure skill mutations are safe before apply

Deliverables:

- structural verifier
- semantic conflict checks
- regression example contract

Target files:

- Create: `src/autoskill_lc/core/verifier.py`
- Modify: `src/autoskill_lc/core/patches.py`
- Test: `tests/test_verifier.py`

Acceptance:

- failing verification blocks apply
- verifier output is visible in governance reporting

### Feature E: Rollback ledger

Purpose:

- move from checkpoint summary to rollback-ready history

Deliverables:

- per-run patch ledger
- skill mutation audit trail
- rollback target lookup by checkpoint sequence

Target files:

- Create: `src/autoskill_lc/runtime/ledger.py`
- Modify: `src/autoskill_lc/runtime/checkpoints.py`
- Modify: `src/autoskill_lc/runtime/maintenance.py`
- Test: `tests/test_ledger.py`

Acceptance:

- each mutation-capable run can identify what to revert
- audit output links checkpoint, report, and patch proposal

### Feature F: Apply policy tiers

Purpose:

- separate report-only, candidate patch, safe auto-apply, and human approval

Deliverables:

- policy thresholds
- host-aware apply decisions
- explicit report status for pending approval

Target files:

- Create: `src/autoskill_lc/core/apply_policy.py`
- Modify: `src/autoskill_lc/runtime/maintenance.py`
- Modify: `src/autoskill_lc/core/reporting.py`
- Test: `tests/test_apply_policy.py`

Acceptance:

- low-risk changes can be marked auto-applicable
- high-risk changes remain pending

## Recommended execution order

### Wave 1

- Feature A: Semantic merge
- Feature B: Topic-to-skill mapper

Reason:

- patch generation is weak until topic identity and target identity are stable

### Wave 2

- Feature C: Patch generation contract
- Feature D: Verification layer

Reason:

- mutation needs a clean artifact and a safety gate before any apply logic

### Wave 3

- Feature E: Rollback ledger
- Feature F: Apply policy tiers

Reason:

- auto-apply without rollback and verification is not sustainable evolution

## Task-level execution notes

For every feature:

1. write failing tests first
2. run the narrow test and confirm failure
3. implement minimal code
4. run the narrow test again
5. run full `pytest -q`
6. update docs only after code and tests are green
7. commit before moving to the next feature

## Definition of done

The sustainable-evolution program is ready for the next stage when:

- semantic duplicates are merged
- evidence-backed topics can map to a target skill
- patch proposals are generated instead of free-form rewrite suggestions
- verification can block unsafe mutations
- rollback history exists beyond summary-only checkpoint logs
- report v2 can express mutation readiness and approval state

## Immediate next task

Start with **Feature A: Semantic merge**.

This is the first missing component that improves report quality and directly
reduces candidate noise without changing host contracts.
