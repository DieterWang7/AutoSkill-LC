# AutoSkill-LC

AutoSkill-LC is a loosely-coupled self-evolving skill governance engine.

The project starts from the AutoSkill lineage, but shifts the center of gravity
from a single host integration to a host-agnostic core. OpenClaw is the first
official adapter. Claude, ChatGPT, Gemini, and future coding agents can be
supported through separate adapters without rewriting the governance engine.

## Design goals

- keep host systems untouched and removable
- run maintenance only when scheduled
- evolve skills from conversation evidence
- emit explainable recommendations for add, upgrade, deprecate, and remove
- make rollback a first-class workflow

## Current scope

The bootstrap in this repository provides:

- a host-neutral governance engine
- adapter contracts for host integrations
- runtime contracts for scheduled maintenance
- an OpenClaw adapter bootstrap with install and uninstall flows
- tests for the first recommendation rules

## Planned adapters

- OpenClaw
- Claude
- ChatGPT
- Gemini

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/ROADMAP.md](docs/ROADMAP.md) for the first implementation roadmap.

## Bootstrap commands

```bash
python -m pip install -e .[dev]
autoskill-lc openclaw-install --workspace-dir ~/.openclaw
autoskill-lc openclaw-maintain --workspace-dir ~/.openclaw
autoskill-lc openclaw-uninstall --workspace-dir ~/.openclaw
```

OpenClaw plugin discovery and `plugins.*` config changes require a Gateway
restart after install or uninstall.

More details:

- [docs/ADAPTERS.md](docs/ADAPTERS.md)
- [docs/INSTALL.md](docs/INSTALL.md)
- [docs/UNINSTALL.md](docs/UNINSTALL.md)
