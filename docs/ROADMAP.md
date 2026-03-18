# Roadmap

## Phase 0

- bootstrap repository structure
- define contracts for governance, adapters, and runtime
- add the first tests for recommendation rules

## Phase 1

- implement OpenClaw adapter
- support archived conversation ingestion
- emit governance reports without mutating host state

## Phase 2

- add scheduled maintenance runtime
- wire host cron or external schedulers
- support report-driven approval flows
- promote governance report to v2 with unresolved/tooling/impossible buckets

## Phase 3

- support skill mirroring and rollback
- add stale skill cleanup policies
- add replacement-aware deprecate flows
- add host-specific signal extractors so report v2 sections are filled from
  real conversations instead of hand-authored signals

## Phase 4

- add Claude, ChatGPT, and Gemini adapters
- stabilize the adapter contract
- publish examples and compatibility notes
