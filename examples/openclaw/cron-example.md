# OpenClaw cron example

Use OpenClaw Gateway cron to wake AutoSkill-LC only when maintenance is needed.

## Isolated scheduled run

```bash
openclaw cron add \
  --name "AutoSkill-LC maintenance" \
  --cron "0 3 * * *" \
  --session isolated \
  --message "Run autoskill-lc openclaw-maintain --workspace-dir ~/.openclaw and summarize the generated governance report." \
  --announce
```

## Notes

- prefer `isolated` session mode for background governance work
- prefer OpenClaw CLI or Gateway API for cron management
- avoid editing `~/.openclaw/cron/jobs.json` while the Gateway is running
- restart Gateway after plugin install or uninstall

