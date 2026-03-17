import json
from pathlib import Path

from autoskill_lc.openclaw.adapter import OpenClawAdapter


def test_openclaw_adapter_loads_signals_and_inventory(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    signals_dir = workspace / "autoskill-lc" / "signals"
    inventory_dir = workspace / "autoskill-lc" / "inventory"
    signals_dir.mkdir(parents=True)
    inventory_dir.mkdir(parents=True)

    (signals_dir / "session-1.json").write_text(
        json.dumps(
            [
                {
                    "topic": "openclaw session hygiene",
                    "evidence": ["user repeated the cleanup workflow"],
                    "confidence": 0.82,
                    "observed_runs": 3,
                }
            ]
        ),
        encoding="utf-8",
    )
    (inventory_dir / "skills.json").write_text(
        json.dumps(
            [
                {
                    "skill_id": "skill-1",
                    "title": "existing cleanup skill",
                    "version": "1.0.0",
                    "usage_count": 5,
                    "status": "active",
                }
            ]
        ),
        encoding="utf-8",
    )

    adapter = OpenClawAdapter.for_workspace(workspace)
    signals = adapter.collect_signals()
    skills = adapter.list_skills()

    assert len(signals) == 1
    assert signals[0].topic == "openclaw session hygiene"
    assert len(skills) == 1
    assert skills[0].skill_id == "skill-1"

