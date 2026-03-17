# Uninstall

## Remove plugin wiring

```bash
autoskill-lc openclaw-uninstall --workspace-dir ~/.openclaw
```

Then restart the OpenClaw Gateway so the removed plugin stops being discovered.

This removes:

- the plugin entry from `openclaw.json`
- the adapter descriptor directory
- the plugin runtime directory

By default it preserves generated data under `autoskill-lc/`.

## Full purge

```bash
autoskill-lc openclaw-uninstall --workspace-dir ~/.openclaw --purge-data
```

This also removes the AutoSkill-LC data directory.

## Safety model

The uninstaller only removes paths registered in its manifest or paths derived
from the known plugin id. It does not touch unrelated OpenClaw assets.

