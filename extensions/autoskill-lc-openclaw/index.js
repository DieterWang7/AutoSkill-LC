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

function resolveDataDir(config) {
  return path.join(resolveWorkspaceDir(config), "autoskill-lc");
}

function resolveReportPath(config) {
  return path.join(resolveDataDir(config), "reports", config?.reportName || DEFAULT_REPORT_NAME);
}

function summarizeStatus(config) {
  const workspaceDir = resolveWorkspaceDir(config);
  const dataDir = resolveDataDir(config);
  const reportPath = resolveReportPath(config);
  return {
    workspaceDir,
    dataDir,
    signalsDir: path.join(dataDir, "signals"),
    inventoryPath: path.join(dataDir, "inventory", "skills.json"),
    reportPath,
    reportExists: fs.existsSync(reportPath)
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

export default function register(api) {
  api.registerGatewayMethod(`${PLUGIN_ID}.status`, ({ pluginConfig, respond }) => {
    respond(true, summarizeStatus(pluginConfig));
  });

  api.registerCommand({
    name: "autoskill-status",
    description: "Show AutoSkill-LC OpenClaw plugin status",
    handler: (ctx) => {
      const status = summarizeStatus(ctx.pluginConfig);
      return {
        text: [
          "AutoSkill-LC OpenClaw plugin",
          `workspace: ${status.workspaceDir}`,
          `signals: ${status.signalsDir}`,
          `inventory: ${status.inventoryPath}`,
          `report: ${status.reportPath}`,
          `report-exists: ${status.reportExists}`
        ].join("\n")
      };
    }
  });

  api.registerCommand({
    name: "autoskill-maintain",
    description: "Run AutoSkill-LC maintenance via the Python CLI",
    handler: (ctx) => {
      const workspaceDir = resolveWorkspaceDir(ctx.pluginConfig);
      const reportName = ctx.pluginConfig?.reportName || DEFAULT_REPORT_NAME;
      const result = runPythonCli(ctx.pluginConfig, [
        "openclaw-maintain",
        "--workspace-dir",
        workspaceDir,
        "--report-name",
        reportName
      ]);
      return {
        text: formatRunResult(result)
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

      const workspaceDir = resolveWorkspaceDir(ctx.pluginConfig);
      const result = runPythonCli(ctx.pluginConfig, [
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
