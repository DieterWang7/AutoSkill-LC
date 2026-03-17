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

This also removes the AutoSkill-LC data directory including:
- signals
- inventory
- reports
- skills

## Safety model

The uninstaller only removes paths registered in its manifest or paths derived
from the known plugin id. It does not touch unrelated OpenClaw assets.

## Idempotent Uninstallation

The uninstaller is idempotent - running it multiple times is safe:

```bash
# First uninstall
autoskill-lc openclaw-uninstall --workspace-dir ~/.openclaw

# Safe to run again - no-op if already uninstalled
autoskill-lc openclaw-uninstall --workspace-dir ~/.openclaw
```

## Verification

After uninstall, verify removal:

```bash
# Check plugin directory is gone
ls ~/.openclaw/plugins/autoskill-lc-openclaw  # Should not exist

# Check adapter directory is gone
ls ~/.openclaw/extensions/autoskill-lc-openclaw-adapter  # Should not exist

# Check openclaw.json no longer has our entry
cat ~/.openclaw/openclaw.json | grep autoskill-lc  # Should be empty
```

## Rollback

If you need to restore after uninstall without `--purge-data`:

```bash
# Simply reinstall - data is preserved
autoskill-lc openclaw-install --workspace-dir ~/.openclaw
```

If you used `--purge-data`, data is permanently lost.

