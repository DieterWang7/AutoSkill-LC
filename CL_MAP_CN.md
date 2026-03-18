# AutoSkill-LC CL 映射

## 目的

这个文件是 `AutoSkill-LC` 在 CL 侧的升级映射说明。

它回答四个问题：

1. 哪些文件是 CL 专属新增
2. 哪些上游文件只做了轻量修改
3. 从上游同步后，哪些区域必须复查
4. 哪些变更对宿主运行时至关重要

规则很简单：

- 优先采用新增式文件，而不是侵入式重写
- 在可能的情况下，尽量保持上游执行流程不变
- 如果上游变更与 CL 新增内容冲突，只修改尽可能小的表面范围

## CL 专属新增文件

这些文件或目录在上游 bootstrap 基线中不存在，后续同步时应保留。

### 面向 OpenClaw 的根级打包文件

- `package.json`
- `index.js`
- `setup-entry.js`
- `openclaw.plugin.json`
- `.npmignore`

### 核心治理增强

- `src/autoskill_lc/core/reporting.py`
- `src/autoskill_lc/runtime/checkpoints.py`

### Codex 适配器新增

- `src/autoskill_lc/codex/adapter.py`
- `src/autoskill_lc/codex/config.py`
- `src/autoskill_lc/codex/exporter.py`
- `src/autoskill_lc/codex/installer.py`
- `src/autoskill_lc/codex/reporting.py`
- `src/autoskill_lc/codex/status.py`
- `docs/CODEX_ADAPTER.md`
- `examples/codex/fresh-install-and-safe-uninstall.ps1`

### OpenClaw 运维打包与文档

- `docs/OPENCLAW_PLUGIN.md`
- `docs/OPENCLAW_EXPORTS.md`
- `examples/openclaw/server-e2e.sh`
- `extensions/autoskill-lc-openclaw/`

### 治理报告 v2 文档

- `docs/REPORT_V2.md`
- `docs/OPENCLAW_SERVER_SAFETY_SKILL_MERGE.md`

### 外部由 CL 管理的技能源

该技能故意放在 AutoSkill-LC 运行时仓库之外：

- `E:/HUA-TeamAssistant Project/HUA-Skills&Tools-Viceroy/skills/skill分类-服务器和网络/openclaw-server-safety/SKILL.md`

并通过 junction 链接到当前激活的 Codex 技能目录：

- `E:/C pan user/.codex/skills/openclaw-server-safety`

## 轻量修改的上游接口文件

这些文件属于正常执行路径的一部分，在拉取上游更新后可能需要手工复查合并。

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/INSTALL.md`
- `docs/ROADMAP.md`
- `src/autoskill_lc/adapters/base.py`
- `src/autoskill_lc/cli.py`
- `src/autoskill_lc/core/models.py`
- `src/autoskill_lc/openclaw/adapter.py`
- `src/autoskill_lc/openclaw/reporting.py`
- `src/autoskill_lc/openclaw/status.py`
- `src/autoskill_lc/runtime/maintenance.py`
- `src/autoskill_lc/openclaw/exporter.py`
- `src/autoskill_lc/codex/exporter.py`
- `src/autoskill_lc/codex/status.py`

## 运行时关键路径假设

### OpenClaw 生产环境

- runtime code: `/opt/openclaw/vendor/autoskill-lc`
- plugin entrypoint: `/root/.openclaw/extensions/autoskill-lc-openclaw`
- governance data: `/root/.openclaw/autoskill-lc`
- config: `/root/.openclaw/openclaw.json`

### Codex

- data: `~/.codex/autoskill-lc`
- optional skill: `~/.codex/skills/autoskill-lc-governance`

## CL 增加的宿主契约

### Report v2

报告现在除了原始 recommendations 外，还包含这些新增区块：

- `evidenceBackedEvolutions`
- `candidateOnly`
- `unresolvedRequirements`
- `toolingNeeded`
- `impossibleItems`

### Signal 元数据扩展

Signals 现在可以包含：

- `conversation_id`
- `conversation_title`
- `report_classification`
- `missing_requirement`
- `next_step`
- `tool_references`
- `prerequisites`

### Checkpoint markdown

每次维护运行现在都会写入：

- `~/.openclaw/autoskill-lc/checkpoint.md`
- `~/.codex/autoskill-lc/checkpoint.md`

checkpoint 文件会记录：

- sequence
- run time
- conversation id
- conversation title
- upgraded skills
- removed/deprecated skills

同时会在 frontmatter 中保存 `last_processed_at`，这样重复执行维护时就能跳过已处理的 signals，只分析更新的材料。

## 上游同步检查清单

当与上游 AutoSkill 变更同步时，按以下顺序复查：

1. `src/autoskill_lc/core/models.py`
2. `src/autoskill_lc/runtime/maintenance.py`
3. `src/autoskill_lc/adapters/base.py`
4. `src/autoskill_lc/openclaw/adapter.py`
5. `src/autoskill_lc/openclaw/reporting.py`
6. `src/autoskill_lc/openclaw/exporter.py`
7. `src/autoskill_lc/codex/exporter.py`
8. `src/autoskill_lc/cli.py`
9. `package.json` 与根目录 OpenClaw 打包文件

## CL 修改说明

### 2026-03-18 report v2

- 新增宿主中立的 report builder
- 新增 signal metadata，用于承载证据、未完成需求、tooling needs 与 impossible items

### 2026-03-18 checkpoint tracking

- 仓库中原先没有发现 `checkpoint.md` 或其他 checkpoint 跟踪文件
- 新增 `runtime/checkpoints.py`，而不是重写治理引擎
- maintenance 现在会从 markdown frontmatter 读取 `last_processed_at`
- maintenance 现在会以倒序追加新的 checkpoint 条目
- exporters 现在会持久化 `conversation_id` 与 `conversation_title`
- status 现在暴露 `checkpointPath`

## 命名规则

- 功能性 / 运行时文件必须使用英文名称
- 非功能性的叙述型文档可以使用中文名称

## 合并策略

- 如果上游新增执行行为，应以上游为事实来源
- 仅将 CL 侧改动重新应用为适配器、打包、文档或可选元数据
- 如果可以通过新增 helper 或 wrapper 解决，就避免重写上游文件
- 每一个新的 CL-only 文件都必须在发版前记录到这里
