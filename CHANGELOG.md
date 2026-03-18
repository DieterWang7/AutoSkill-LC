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
- Human-readable `display` report layer with Chinese operator summary
- Incremental maintenance using `last_processed_at`
- `conversation_id` and `conversation_title` signal fields
- `checkpointPath` in OpenClaw and Codex status payloads
- `CL_MAP.md` as the CL-side upgrade map

### Changed

- Functional checkpoint filename standardized from Chinese to English:
  - `checkpoint.md`
- OpenClaw server safety guidance split into an independent external skill
- Documentation updated for report v2, checkpoint tracking, and naming policy
- OpenClaw plugin display now renders `report.display` instead of legacy shell logs
- OpenClaw slash commands now fall back to `openclaw.json` when `pluginConfig`
  is missing from the command handler context, avoiding `spawnSync python ENOENT`
- Report/checkpoint timestamp parsing now interprets historical naive
  datetimes in the local host timezone so older `checkpoint.md` entries do not
  break maintenance with `offset-naive and offset-aware` datetime errors or
  produce negative window durations
- Legacy checkpoint values that were accidentally written with a future-looking
  `+00:00` offset are now reinterpreted as local wall-clock time when safe, so
  incremental filtering and window summaries remain usable on upgraded hosts
- OpenClaw and Codex exporters now skip greeting-only conversations such as
  `hello/hi/你好`, so low-information chatter no longer becomes candidate
  governance items
- Topic extraction now compacts long imperative requests into cleaner themes,
  for example turning `请继续实现 GitHub 安装和服务器自动同步，这需要工具实现。`
  into `GitHub 安装和服务器自动同步`

### Notes

- Functional/runtime files must use English names
- Narrative and non-functional docs may use Chinese names
