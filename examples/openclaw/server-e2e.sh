#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${1:-https://github.com/DieterWang7/AutoSkill-LC.git}"
WORKDIR="${2:-$HOME/autoskill-lc}"

echo "[1/6] Prepare workspace: ${WORKDIR}"
if [ -d "${WORKDIR}/.git" ]; then
  git -C "${WORKDIR}" fetch --all --tags
  git -C "${WORKDIR}" reset --hard origin/main
else
  rm -rf "${WORKDIR}"
  git clone "${REPO_URL}" "${WORKDIR}"
fi

cd "${WORKDIR}"

echo "[2/6] Install Python package"
python3 -m pip install -e .[dev]

echo "[3/6] Run Python test suite"
python3 -m pytest -q

echo "[4/6] Validate OpenClaw package root"
npm pack --dry-run >/dev/null

echo "[5/6] Install and enable plugin"
openclaw plugins install .
openclaw plugins enable autoskill-lc-openclaw || true

echo "[6/6] Restart Gateway and show plugin list"
openclaw gateway restart || true
openclaw plugins list || true

echo "Next checks inside OpenClaw:"
echo "  /autoskill-status"
echo "  /autoskill-ingest /tmp/autoskill-test-conversation.json"
echo "  /autoskill-maintain"
