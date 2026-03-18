# Changelog

## v0.2.0 - 2026-03-18

### Added

- Report v2 with five governance sections:
  - `evidenceBackedEvolutions`
  - `candidateOnly`
  - `unresolvedRequirements`
  - `toolingNeeded`
  - `impossibleItems`
- Host-neutral checkpoint tracking in `checkpoint.md`
- Incremental maintenance using `last_processed_at`
- `conversation_id` and `conversation_title` signal fields
- `checkpointPath` in OpenClaw and Codex status payloads
- `CL_MAP.md` as the CL-side upgrade map

### Changed

- Functional checkpoint filename standardized from Chinese to English:
  - `checkpoint.md`
- OpenClaw server safety guidance split into an independent external skill
- Documentation updated for report v2, checkpoint tracking, and naming policy

### Notes

- Functional/runtime files must use English names
- Narrative and non-functional docs may use Chinese names
