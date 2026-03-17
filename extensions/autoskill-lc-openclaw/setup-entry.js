import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const DEFAULT_WORKSPACE = path.join(os.homedir(), ".openclaw");

export default function register(api) {
  api.registerGatewayMethod("autoskill-lc-openclaw.setup-status", ({ respond }) => {
    const reportPath = path.join(
      DEFAULT_WORKSPACE,
      "autoskill-lc",
      "reports",
      "latest-governance-report.json"
    );
    respond(true, {
      workspaceDir: DEFAULT_WORKSPACE,
      reportPath,
      reportExists: fs.existsSync(reportPath)
    });
  });
}
