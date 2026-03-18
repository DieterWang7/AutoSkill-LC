# AutoSkill-LC

AutoSkill-LC = 一个松耦合（Loosely-Coupled）、可自演化（Self-Evolving）、宿主无关（Host-Agnostic）的技能治理引擎。

OpenClaw 是首个官方适配器。Claude、ChatGPT、Gemini 适配器已在规划中。

## 功能说明

AutoSkill-LC 会观察用户与 AI 宿主之间的对话模式，并据此给出建议：
- 当出现反复出现但尚未覆盖的模式时，**ADD** 新技能
- 当纠错表明技能需要演进时，**UPGRADE** 技能
- 当技能长时间未活跃时，**DEPRECATE** 技能
- 当已弃用技能超过移除窗口时，**REMOVE** 技能

核心原则：
- 不改动宿主系统，且可随时移除
- 仅在调度时间执行维护，不常驻占用资源
- 所有建议都附带置信度与证据
- 回滚是一级工作流

## 快速开始

```bash
# 以开发模式安装
python -m pip install -e .[dev]

# 安装 OpenClaw 适配器
autoskill-lc openclaw-install --workspace-dir ~/.openclaw

# 运行维护（读取 signals、分析并写入报告）
autoskill-lc openclaw-maintain --workspace-dir ~/.openclaw

# 使用完后卸载
autoskill-lc openclaw-uninstall --workspace-dir ~/.openclaw --purge-data
```

## OpenClaw Cron 集成

可在 `crontab` 中加入每日维护任务：

```cron
# 每天凌晨 2 点
0 2 * * * /usr/bin/autoskill-lc openclaw-maintain --workspace-dir ~/.openclaw
```

或者使用 `systemd timer`，以获得对按需唤醒执行更细粒度的控制。

## 项目状态

**当前阶段：OpenClaw-first MVP**

当前版本聚焦于 OpenClaw 适配器稳定性。核心架构本身与宿主无关，后续会用同一套治理引擎支持 Claude、ChatGPT 和 Gemini 适配器。

| 适配器 | 状态 |
|--------|------|
| OpenClaw | 可用 |
| Claude | 规划中 |
| ChatGPT | 规划中 |
| Gemini | 规划中 |

在 OpenClaw 聊天中，推荐优先使用：

- `/autoskill-status`
- `/autoskill-maintain`
- `/autoskill-cl`

这些命令预期渲染报告的 `display` 层，而不是旧式 shell 日志输出。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                         宿主系统                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │OpenClaw │  │ Claude  │  │ ChatGPT │  │ Gemini  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
└───────┼────────────┼────────────┼────────────┼─────────────┘
        │            │            │            │
        └────────────┴──────┬─────┴────────────┘
                            │
              ┌─────────────▼─────────────┐
              │       宿主适配器           │
              │   (OpenClawAdapter 等)    │
              └─────────────┬─────────────┘
                            │
              ┌─────────────▼─────────────┐
              │        治理引擎            │
              │    （宿主无关核心）        │
              └─────────────┬─────────────┘
                            │
              ┌─────────────▼─────────────┐
              │         建议输出           │
              │  (ADD/UPGRADE/DEPRECATE/  │
              │        REMOVE)            │
              └───────────────────────────┘
```

## 目录结构

```
OpenClaw 生产宿主
├── /opt/openclaw/vendor/autoskill-lc/      # AutoSkill-LC 运行时代码 + venv
├── /root/.openclaw/extensions/
│   └── autoskill-lc-openclaw/              # OpenClaw 插件入口
├── /root/.openclaw/autoskill-lc/           # AutoSkill-LC 数据目录
│   ├── signals/                            # 对话信号文件（*.json）
│   ├── inventory/                          # 技能清单（skills.json）
│   └── reports/                            # 治理报告
└── /root/.openclaw/openclaw.json           # OpenClaw 配置文件

Codex 宿主
├── ~/.codex/autoskill-lc/                  # AutoSkill-LC 数据目录
│   ├── signals/
│   ├── inventory/
│   ├── reports/
│   └── install-manifest.json
└── ~/.codex/skills/autoskill-lc-governance/
    └── SKILL.md
```

## 宿主路径约定

OpenClaw 与 Codex 使用不同的文件系统角色划分：

- OpenClaw 的运行时代码应位于 OpenClaw 数据目录之外
- OpenClaw 的插件、配置与状态保留在 `~/.openclaw` 下
- Codex 适配器数据保留在 `~/.codex/autoskill-lc`

当前推荐的 OpenClaw 生产布局：

- runtime: `/opt/openclaw/vendor/autoskill-lc`
- plugin entrypoint: `/root/.openclaw/extensions/autoskill-lc-openclaw`
- governance data: `/root/.openclaw/autoskill-lc`
- config: `/root/.openclaw/openclaw.json`

当前推荐的 Codex 布局：

- data: `~/.codex/autoskill-lc`
- optional skill: `~/.codex/skills/autoskill-lc-governance`

## Signal 文件格式

将 JSON 文件放入 `autoskill-lc/signals/`：

```json
[
  {
    "topic": "git release workflow",
    "evidence": ["user asked for release notes 3 times"],
    "confidence": 0.91,
    "observed_runs": 3,
    "existing_skill_id": null,
    "corrections": 0,
    "explicit_uninstall_request": false,
    "superseded_by": null,
    "last_observed_at": "2026-03-18T10:00:00Z"
  }
]
```

## Skill Inventory 格式

放置于 `autoskill-lc/inventory/skills.json`：

```json
[
  {
    "skill_id": "skill-git-release",
    "title": "Git Release Notes",
    "version": "1.0.0",
    "usage_count": 15,
    "last_used_at": "2026-03-10T08:30:00Z",
    "status": "active"
  }
]
```

## 报告输出

AutoSkill-LC Report v2 会将对话证据划分为五类：

- `evidenceBackedEvolutions`：已有充分证据、值得并入技能的经验
- `candidateOnly`：证据较弱或不完整，暂不应修改技能
- `unresolvedRequirements`：用户提到但尚未完成的需求
- `toolingNeeded`：需要外部工具或集成支持的需求
- `impossibleItems`：受宿主限制或前置条件缺失而暂时无法完成的请求

同时，它还会为操作人员生成可读的 `display` 区域，包含：

- 已识别的经验
- 治理建议
- 被遗漏的用户需求
- 附带三个参考项目的 tooling-needed 项
- 附带前置条件的 impossible 项
- 单行 checkpoint 窗口摘要

报告会写入 `autoskill-lc/reports/latest-governance-report.json`：

```json
{
  "schemaVersion": "2.0",
  "host": "openclaw",
  "generatedAt": "2026-03-18T14:00:00+00:00",
  "recommendationCount": 2,
  "summary": {
    "evidenceBackedCount": 1,
    "candidateOnlyCount": 1,
    "unresolvedRequirementCount": 1,
    "toolingNeedCount": 1,
    "impossibleItemCount": 0,
    "actions": {
      "add": 1,
      "upgrade": 1,
      "deprecate": 0,
      "remove": 0
    }
  },
  "recommendations": [
    {
      "action": "add",
      "topic": "git release workflow",
      "confidence": 0.91,
      "rationale": "A recurring pattern without coverage suggests a new skill.",
      "skill_id": null,
      "replacement_skill_id": null,
      "evidence": ["user asked for release notes 3 times"]
    }
  ],
  "evidenceBackedEvolutions": [
    {
      "topic": "git release workflow",
      "confidence": 0.91,
      "evidence": ["user asked for release notes 3 times"],
      "recommendationAction": "add",
      "skillId": null,
      "rationale": "A recurring pattern without coverage suggests a new skill.",
      "lastObservedAt": "2026-03-18T10:00:00+00:00"
    }
  ],
  "candidateOnly": [
    {
      "topic": "single anecdotal optimization idea",
      "confidence": 0.31,
      "evidence": ["one weak example only"],
      "reason": "Evidence is not yet strong enough to modify a skill.",
      "nextStep": null
    }
  ],
  "unresolvedRequirements": [
    {
      "topic": "install provenance cleanup",
      "requirement": "Clean install provenance warning",
      "evidence": ["user requested cleanup but the task was deferred"],
      "nextStep": "Validate npm install provenance flow",
      "confidence": 0.6
    }
  ],
  "toolingNeeded": [
    {
      "topic": "nightly repository audit",
      "requirement": "Add scheduled repository audit",
      "evidence": ["requires automation support"],
      "referenceProjects": ["openai/codex", "openclaw/openclaw", "microsoft/vscode"],
      "confidence": 0.72
    }
  ],
  "impossibleItems": []
}
```

## 扩展 Signal 字段

Signal 还可以携带可选的报告治理提示：

```json
[
  {
    "topic": "install provenance cleanup",
    "evidence": ["user requested cleanup but the task was deferred"],
    "confidence": 0.6,
    "report_classification": "unresolved",
    "missing_requirement": "Clean install provenance warning",
    "next_step": "Validate npm install provenance flow",
    "tool_references": ["openai/codex", "openclaw/openclaw"],
    "prerequisites": ["Host install provenance API"]
  }
]
```

支持的 `report_classification` 值：

- `evidence_backed`
- `candidate_only`
- `unresolved`
- `tooling_needed`
- `impossible`

在实际运行中，exporter 也可以从对话文本中自动推导这些分类，因此宿主无需手写 signal JSON，也能开始生成 unresolved/tooling/impossible 这些区块。

## Checkpoint 日志

每次维护运行还会写入一个 markdown checkpoint 文件：

- OpenClaw：`~/.openclaw/autoskill-lc/checkpoint.md`
- Codex：`~/.codex/autoskill-lc/checkpoint.md`

该 checkpoint 按时间倒序记录以下内容：

- sequence
- run time
- conversation ID
- conversation title
- upgraded skills
- removed 或 deprecated skills

Markdown frontmatter 中会保存 `last_processed_at`，以便后续重复运行时跳过更旧的 signals，只聚焦新加入的对话材料。

## 文档

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - 系统架构
- [docs/ROADMAP.md](docs/ROADMAP.md) - 开发路线图
- [docs/INSTALL.md](docs/INSTALL.md) - 详细安装说明
- [docs/UNINSTALL.md](docs/UNINSTALL.md) - 安全卸载说明
- [docs/ADAPTERS.md](docs/ADAPTERS.md) - 适配器开发指南
- [docs/REPORT_V2.md](docs/REPORT_V2.md) - 治理报告 v2 schema
- [docs/OPENCLAW_SERVER_SAFETY_SKILL_MERGE.md](docs/OPENCLAW_SERVER_SAFETY_SKILL_MERGE.md) - OpenClaw server safety skill 合并方案
- [CL_MAP.md](CL_MAP.md) - 面向 CL 的升级映射

## 开发

```bash
# 运行测试
python -m pytest -q

# 带覆盖率运行
python -m pytest --cov=autoskill_lc

# 类型检查
python -m mypy src/autoskill_lc
```

## 许可证

MIT License，详见 LICENSE 文件。
