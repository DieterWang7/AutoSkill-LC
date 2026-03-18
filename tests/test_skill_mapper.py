from autoskill_lc.core.models import ConversationSignal, SkillRecord
from autoskill_lc.core.skill_mapper import map_signal_to_skill, map_signals_to_skills


def test_map_signal_to_skill_prefers_explicit_skill_id() -> None:
    signal = ConversationSignal(
        topic="whatever",
        existing_skill_id="skill-openclaw-maintenance",
    )
    skills = [
        SkillRecord(
            skill_id="skill-openclaw-maintenance",
            title="OpenClaw maintenance",
            version="1.0.0",
        )
    ]

    match = map_signal_to_skill(signal, skills)

    assert match is not None
    assert match.match_type == "explicit"
    assert match.confidence == 1.0
    assert match.skill_path is None


def test_map_signal_to_skill_matches_by_overlap() -> None:
    signal = ConversationSignal(topic="GitHub 安装和服务器自动同步")
    skills = [
        SkillRecord(
            skill_id="skill-server-sync",
            title="服务器自动同步 GitHub 安装",
            version="1.0.0",
        )
    ]

    match = map_signal_to_skill(signal, skills)

    assert match is not None
    assert match.skill_id == "skill-server-sync"
    assert match.confidence >= 0.45


def test_map_signals_to_skills_returns_topic_index() -> None:
    mappings = map_signals_to_skills(
        [ConversationSignal(topic="OpenClaw cron maintenance")],
        [
            SkillRecord(
                skill_id="skill-openclaw-cron",
                title="OpenClaw cron maintenance",
                version="1.0.0",
            )
        ],
    )

    assert "OpenClaw cron maintenance" in mappings


def test_map_signal_to_skill_carries_skill_path() -> None:
    signal = ConversationSignal(topic="OpenClaw cron maintenance")
    skills = [
        SkillRecord(
            skill_id="skill-openclaw-cron",
            title="OpenClaw cron maintenance",
            version="1.0.0",
            skill_path="E:/skills/openclaw-cron/SKILL.md",
        )
    ]

    match = map_signal_to_skill(signal, skills)

    assert match is not None
    assert match.skill_path == "E:/skills/openclaw-cron/SKILL.md"
