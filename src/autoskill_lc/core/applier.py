from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from autoskill_lc.core.apply_policy import ApplyDecision, ApplyTier
from autoskill_lc.core.models import RecommendationAction
from autoskill_lc.core.patches import PatchProposal
from autoskill_lc.core.verifier import VerificationResult


@dataclass(frozen=True)
class AppliedChange:
    proposal_id: str
    skill_path: str
    rollback_manifest_path: str
    applied_at: str


def apply_patch_proposals(
    proposals: list[PatchProposal],
    *,
    verifications: list[VerificationResult],
    decisions: list[ApplyDecision],
    rollback_dir: Path,
    generated_at: datetime | None = None,
) -> list[AppliedChange]:
    verification_by_id = {item.proposal_id: item for item in verifications}
    decision_by_id = {item.proposal_id: item for item in decisions}
    run_at = generated_at or datetime.now(timezone.utc)
    applied: list[AppliedChange] = []

    for proposal in proposals:
        decision = decision_by_id.get(proposal.proposal_id)
        verification = verification_by_id.get(proposal.proposal_id)
        if decision is None or verification is None:
            continue
        if decision.tier is not ApplyTier.SAFE_AUTO_APPLY or not verification.passed:
            continue
        if proposal.action is not RecommendationAction.UPGRADE or not proposal.target_skill_path:
            continue
        skill_path = Path(proposal.target_skill_path).expanduser()
        if not skill_path.exists():
            continue
        original = skill_path.read_text(encoding="utf-8")
        updated = _apply_upgrade_patch(original, proposal, run_at)
        if updated == original:
            continue
        manifest_path = _write_rollback_manifest(
            rollback_dir,
            proposal=proposal,
            original_content=original,
            updated_content=updated,
            generated_at=run_at,
            skill_path=skill_path,
        )
        skill_path.write_text(updated, encoding="utf-8")
        applied.append(
            AppliedChange(
                proposal_id=proposal.proposal_id,
                skill_path=str(skill_path),
                rollback_manifest_path=str(manifest_path),
                applied_at=run_at.isoformat(),
            )
        )
    return applied


def _apply_upgrade_patch(
    content: str,
    proposal: PatchProposal,
    generated_at: datetime,
) -> str:
    note = (
        "<!-- AutoSkill-LC Evolution: "
        f"{generated_at.isoformat()} | proposal={proposal.proposal_id} | "
        f"topic={proposal.topic} | reason={proposal.header_note} -->"
    )
    if note in content:
        return content
    change_block = [
        "",
        "## AutoSkill-LC Evolution",
        f"- Time: {generated_at.isoformat()}",
        f"- Proposal: {proposal.proposal_id}",
        f"- Topic: {proposal.topic}",
        f"- Reason: {proposal.header_note}",
        f"- Evidence: {'; '.join(proposal.evidence) if proposal.evidence else 'n/a'}",
    ]
    base = content.rstrip()
    return f"{note}\n{base}\n" + "\n".join(change_block) + "\n"


def _write_rollback_manifest(
    rollback_dir: Path,
    *,
    proposal: PatchProposal,
    original_content: str,
    updated_content: str,
    generated_at: datetime,
    skill_path: Path,
) -> Path:
    rollback_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = rollback_dir / f"{proposal.proposal_id}.json"
    payload = {
        "proposalId": proposal.proposal_id,
        "skillPath": str(skill_path),
        "generatedAt": generated_at.isoformat(),
        "originalContent": original_content,
        "updatedContent": updated_content,
    }
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path
