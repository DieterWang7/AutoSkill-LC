import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const PLUGIN_ID = "autoskill-lc-openclaw";
const DEFAULT_REPORT_NAME = "latest-governance-report.json";

function resolveWorkspaceDir(config) {
  const raw = config?.workspaceDir || path.join(os.homedir(), ".openclaw");
  return raw.startsWith("~") ? path.join(os.homedir(), raw.slice(1)) : raw;
}

function loadConfiguredPluginEntry(workspaceDir) {
  const payload = readJson(path.join(workspaceDir, "openclaw.json"));
  const entry = payload?.plugins?.entries?.[PLUGIN_ID];
  if (!entry || typeof entry !== "object") {
    return {};
  }
  const config = entry.config;
  return config && typeof config === "object" ? config : {};
}

function resolvePluginConfig(maybeConfig, runtimeCwd) {
  const explicitConfig =
    maybeConfig && typeof maybeConfig === "object" ? maybeConfig : {};
  const fallbackWorkspaceDir = resolveWorkspaceDir({
    workspaceDir:
      explicitConfig.workspaceDir || runtimeCwd || path.join(os.homedir(), ".openclaw")
  });
  const diskConfig = loadConfiguredPluginEntry(fallbackWorkspaceDir);
  return {
    ...diskConfig,
    ...explicitConfig
  };
}

function resolveDataDir(config) {
  return path.join(resolveWorkspaceDir(config), "autoskill-lc");
}

function resolveReportPath(config) {
  return path.join(resolveDataDir(config), "reports", config?.reportName || DEFAULT_REPORT_NAME);
}

function resolveCheckpointPath(config) {
  return path.join(resolveDataDir(config), "checkpoint.md");
}

function summarizeStatus(config) {
  const workspaceDir = resolveWorkspaceDir(config);
  const dataDir = resolveDataDir(config);
  const reportPath = resolveReportPath(config);
  const checkpointPath = resolveCheckpointPath(config);
  return {
    workspaceDir,
    dataDir,
    signalsDir: path.join(dataDir, "signals"),
    inventoryPath: path.join(dataDir, "inventory", "skills.json"),
    reportPath,
    reportExists: fs.existsSync(reportPath),
    checkpointPath,
    checkpointExists: fs.existsSync(checkpointPath)
  };
}

function runPythonCli(config, args) {
  const pythonCommand = config?.pythonCommand || "python";
  return spawnSync(pythonCommand, ["-m", "autoskill_lc.cli", ...args], {
    encoding: "utf-8",
    windowsHide: true
  });
}

function formatRunResult(result) {
  if (result.error) {
    return `AutoSkill-LC failed to start Python CLI: ${result.error.message}`;
  }

  if (typeof result.status === "number" && result.status !== 0) {
    return [
      `AutoSkill-LC command exited with code ${result.status}.`,
      result.stderr?.trim(),
      result.stdout?.trim()
    ]
      .filter(Boolean)
      .join("\n");
  }

  return result.stdout?.trim() || "AutoSkill-LC command completed.";
}

function readJson(pathname) {
  if (!fs.existsSync(pathname)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(pathname, "utf-8"));
  } catch {
    return null;
  }
}

function formatItems(items, formatter) {
  if (!Array.isArray(items) || items.length === 0) {
    return ["- 无"];
  }
  return items.map((item, index) => formatter(item, index));
}

function renderDisplayReport(status, payload) {
  const display = payload?.display;
  if (!display) {
    return [
      "AutoSkill-LC 已执行，但报告里没有 display 区块。",
      `报告路径：${status.reportPath}`
    ].join("\n");
  }

  const lines = [
    "AutoSkill-LC 执行报告",
    "",
    `1. ${display.identifiedExperiences?.text || "本次识别出的经验：无"}`,
    ...formatItems(display.identifiedExperiences?.items, (item) => {
      return `- ${item.topic}${item.action ? ` | 动作: ${item.action}` : ""}${item.skillId ? ` | skill: ${item.skillId}` : ""}`;
    }),
    "",
    `2. ${display.governanceSuggestions?.text || "治理建议：无"}`,
    ...formatItems(display.governanceSuggestions?.items, (item) => {
      return `- ${item.topic}${item.action ? ` | 动作: ${item.action}` : ""}${item.skillId ? ` | skill: ${item.skillId}` : ""}${item.replacementSkillId ? ` | 替代: ${item.replacementSkillId}` : ""}`;
    }),
    "",
    `3. ${display.forgottenRequirements?.text || "遗忘需求提醒：无"}`,
    ...formatItems(display.forgottenRequirements?.items, (item) => {
      return `- ${item.requirement}${item.plan ? ` | 方案: ${item.plan}` : ""}`;
    }),
    "",
    `4. ${display.toolingNeeds?.text || "需要工具实现：无"}`,
    ...formatItems(display.toolingNeeds?.items, (item) => {
      const refs = Array.isArray(item.referenceProjects) ? item.referenceProjects.join(", ") : "";
      return `- ${item.requirement}${refs ? ` | 参考项目: ${refs}` : ""}`;
    }),
    "",
    `5. ${display.impossibleItems?.text || "当前不可实现：无"}`,
    ...formatItems(display.impossibleItems?.items, (item) => {
      const prerequisites = Array.isArray(item.prerequisites) ? item.prerequisites.join(", ") : "";
      return `- ${item.requirement}${item.reason ? ` | 原因: ${item.reason}` : ""}${prerequisites ? ` | 前提: ${prerequisites}` : ""}`;
    }),
    "",
    `6. ${display.checkpointWindowSummary?.text || "过去到上个检查点暂无可用总结。"}`,
    "",
    `报告路径：${status.reportPath}`,
    `检查点：${status.checkpointPath}`
  ];
  return lines.join("\n");
}

function formatStatusText(status) {
  const payload = readJson(status.reportPath);
  if (payload?.display) {
    return [
      "AutoSkill-LC OpenClaw plugin",
      `workspace: ${status.workspaceDir}`,
      `signals: ${status.signalsDir}`,
      `inventory: ${status.inventoryPath}`,
      `report: ${status.reportPath}`,
      `checkpoint: ${status.checkpointPath}`,
      "",
      renderDisplayReport(status, payload)
    ].join("\n");
  }
  return [
    "AutoSkill-LC OpenClaw plugin",
    `workspace: ${status.workspaceDir}`,
    `signals: ${status.signalsDir}`,
    `inventory: ${status.inventoryPath}`,
    `report: ${status.reportPath}`,
    `report-exists: ${status.reportExists}`,
    `checkpoint: ${status.checkpointPath}`,
    `checkpoint-exists: ${status.checkpointExists}`
  ].join("\n");
}

function formatMaintainText(config, result) {
  const status = summarizeStatus(config);
  if (result.error || (typeof result.status === "number" && result.status !== 0)) {
    return formatRunResult(result);
  }
  const payload = readJson(status.reportPath);
  if (!payload) {
    return [
      "AutoSkill-LC 已执行，但未读取到报告文件。",
      `报告路径：${status.reportPath}`,
      formatRunResult(result)
    ].join("\n");
  }
  return renderDisplayReport(status, payload);
}

export default function register(api) {
  api.registerGatewayMethod(`${PLUGIN_ID}.status`, ({ pluginConfig, respond }) => {
    const resolvedConfig = resolvePluginConfig(pluginConfig);
    respond(true, summarizeStatus(resolvedConfig));
  });

  api.registerCommand({
    name: "autoskill-status",
    description: "Show AutoSkill-LC OpenClaw plugin status",
    handler: (ctx) => {
      const config = resolvePluginConfig(ctx.pluginConfig, ctx.cwd);
      const status = summarizeStatus(config);
      return {
        text: formatStatusText(status)
      };
    }
  });

  api.registerCommand({
    name: "autoskill-maintain",
    description: "Run AutoSkill-LC maintenance via the Python CLI",
    handler: (ctx) => {
      const config = resolvePluginConfig(ctx.pluginConfig, ctx.cwd);
      const workspaceDir = resolveWorkspaceDir(config);
      const reportName = config?.reportName || DEFAULT_REPORT_NAME;
      const result = runPythonCli(config, [
        "openclaw-maintain",
        "--workspace-dir",
        workspaceDir,
        "--report-name",
        reportName
      ]);
      return {
        text: formatMaintainText(config, result)
      };
    }
  });

  api.registerCommand({
    name: "autoskill-cl",
    description: "Run AutoSkill-LC maintenance and display the governance summary",
    handler: (ctx) => {
      const config = resolvePluginConfig(ctx.pluginConfig, ctx.cwd);
      const workspaceDir = resolveWorkspaceDir(config);
      const reportName = config?.reportName || DEFAULT_REPORT_NAME;
      const result = runPythonCli(config, [
        "openclaw-maintain",
        "--workspace-dir",
        workspaceDir,
        "--report-name",
        reportName
      ]);
      return {
        text: formatMaintainText(config, result)
      };
    }
  });

  api.registerCommand({
    name: "autoskill-ingest",
    description: "Ingest an exported OpenClaw conversation JSON via the Python CLI",
    acceptsArgs: true,
    handler: (ctx) => {
      const exportPath = ctx.args?.trim();
      if (!exportPath) {
        return {
          text: "Usage: /autoskill-ingest <export-json-path>"
        };
      }

      const config = resolvePluginConfig(ctx.pluginConfig, ctx.cwd);
      const workspaceDir = resolveWorkspaceDir(config);
      const result = runPythonCli(config, [
        "openclaw-ingest-export",
        "--workspace-dir",
        workspaceDir,
        "--input",
        exportPath
      ]);
      return {
        text: formatRunResult(result)
      };
    }
  });

  api.registerCli(
    ({ program }) => {
      program
        .command("autoskill-status")
        .description("Show AutoSkill-LC OpenClaw plugin status")
        .action(() => {
          const status = summarizeStatus({});
          console.log(JSON.stringify(status, null, 2));
        });
    },
    { commands: ["autoskill-status"] }
  );
}
