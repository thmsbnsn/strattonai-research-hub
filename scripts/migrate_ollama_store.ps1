param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$repoModelsRoot = Join-Path $repoRoot "models"
$repoOllamaStore = Join-Path $repoModelsRoot "ollama"
$currentOllamaStore = Join-Path $env:USERPROFILE ".ollama\models"

New-Item -ItemType Directory -Path $repoModelsRoot -Force | Out-Null

Get-Process | Where-Object { $_.Path -like "*Ollama*" } | ForEach-Object {
    try {
        Stop-Process -Id $_.Id -Force -ErrorAction Stop
    }
    catch {
    }
}

Start-Sleep -Seconds 2

if ((Test-Path $repoOllamaStore) -and -not $Force) {
    $repoItem = Get-Item $repoOllamaStore
    if (-not $repoItem.Attributes.ToString().Contains("ReparsePoint")) {
        throw "Destination already exists at $repoOllamaStore. Re-run with -Force only if you have handled it intentionally."
    }
}

if (Test-Path $repoOllamaStore) {
    Remove-Item $repoOllamaStore -Force
}

Move-Item -Path $currentOllamaStore -Destination $repoOllamaStore
cmd /c mklink /J "$currentOllamaStore" "$repoOllamaStore" | Out-Null

$env:OLLAMA_MODELS = $repoOllamaStore
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $repoOllamaStore, "User")

Write-Host "Ollama models migrated to $repoOllamaStore"
Write-Host "User OLLAMA_MODELS now points to $([Environment]::GetEnvironmentVariable('OLLAMA_MODELS', 'User'))"
