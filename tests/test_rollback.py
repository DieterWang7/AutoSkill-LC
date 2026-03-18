import json
from pathlib import Path

from autoskill_lc.runtime.rollback import rollback_from_manifest


def test_rollback_from_manifest_restores_original_content(tmp_path: Path) -> None:
    skill_path = tmp_path / "skills" / "skill-1" / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text("updated\n", encoding="utf-8")
    manifest_path = tmp_path / "rollbacks" / "patch-1.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "proposalId": "patch-1",
                "skillPath": str(skill_path),
                "generatedAt": "2026-03-18T00:00:00+00:00",
                "originalContent": "original\n",
                "updatedContent": "updated\n",
            }
        ),
        encoding="utf-8",
    )

    result = rollback_from_manifest(manifest_path)

    assert result.restored is True
    assert skill_path.read_text(encoding="utf-8") == "original\n"
