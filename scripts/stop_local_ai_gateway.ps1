param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot ".strattonai-runtime"
$pidFile = Join-Path $runtimeDir "local-ai.pid"
$stateFile = Join-Path $runtimeDir "local-ai.state.json"

if (-not (Test-Path $pidFile)) {
    Write-Host "Local AI gateway is not running."
    exit 0
}

$rawPid = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $rawPid) {
    Remove-Item $pidFile -ErrorAction SilentlyContinue
    Remove-Item $stateFile -ErrorAction SilentlyContinue
    Write-Host "Local AI gateway is not running."
    exit 0
}

try {
    Stop-Process -Id ([int]$rawPid) -Force -ErrorAction Stop
    Write-Host "Stopped local AI gateway."
}
catch {
    Write-Host "Local AI gateway process was not running."
}

Remove-Item $pidFile -ErrorAction SilentlyContinue
Remove-Item $stateFile -ErrorAction SilentlyContinue
