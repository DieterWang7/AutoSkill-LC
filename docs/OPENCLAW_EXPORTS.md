# OpenClaw Export Ingestion

AutoSkill-LC can convert exported OpenClaw conversations into normalized
signal files under `autoskill-lc/signals`.

## Command

```bash
autoskill-lc openclaw-ingest-export \
  --workspace-dir ~/.openclaw \
  --input ./conversation.json
```

## Supported input shapes

### 1. Single conversation object

```json
{
  "sessionId": "session-42",
  "title": "weekly cleanup workflow",
  "messages": [
    { "role": "user", "content": "Please refine the cleanup workflow." },
    { "role": "assistant", "content": "I will update the workflow and notes." }
  ],
  "confidence": 0.81,
  "observed_runs": 4,
  "updated_at": "2026-03-18T08:30:00Z"
}
```

### 2. Batch export

```json
{
  "conversations": [
    {
      "sessionId": "session-42",
      "title": "weekly cleanup workflow",
      "messages": [
        { "role": "user", "content": "Please refine the cleanup workflow." }
      ]
    }
  ]
}
```

### 3. Already normalized signals

```json
{
  "signals": [
    {
      "topic": "release-note drafting",
      "evidence": ["user asked for the same release-note flow again"],
      "confidence": 0.93,
      "observed_runs": 3
    }
  ]
}
```

## Output

The command writes one normalized signal file to:

```text
<workspace>/autoskill-lc/signals/<session-id>.json
```

If no usable topic exists, AutoSkill-LC falls back to:

```text
openclaw-conversation
```
