param(
    [string]$Repo = "git+https://github.com/DieterWang7/AutoSkill-LC.git",
    [string]$CodexHome = "$env:USERPROFILE\.codex"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/5] Install AutoSkill-LC from GitHub"
python -m pip install $Repo

Write-Host "[2/5] Install adapter into Codex home"
autoskill-lc codex-install --codex-home $CodexHome

Write-Host "[3/5] Show adapter status"
autoskill-lc codex-status --codex-home $CodexHome

Write-Host "[4/5] Uninstall adapter"
autoskill-lc codex-uninstall --codex-home $CodexHome

Write-Host "[5/5] Verify Codex core files still exist if they existed before"
if (Test-Path (Join-Path $CodexHome "config.toml")) {
    Write-Host "config.toml: OK"
}
if (Test-Path (Join-Path $CodexHome "history.jsonl")) {
    Write-Host "history.jsonl: OK"
}
if (Test-Path (Join-Path $CodexHome "sessions")) {
    Write-Host "sessions/: OK"
}
