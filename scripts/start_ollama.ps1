param(
    [switch]$ResetModelsPath,
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 11434
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot ".strattonai-runtime"
$modelsDir = Join-Path $repoRoot "models\\ollama"
$stdoutLog = Join-Path $runtimeDir "ollama.stdout.log"
$stderrLog = Join-Path $runtimeDir "ollama.stderr.log"
$pidFile = Join-Path $runtimeDir "ollama.pid"
$ollamaPath = Join-Path $env:LOCALAPPDATA "Programs\\Ollama\\ollama.exe"

function Test-OllamaListening {
    param(
        [string]$BindAddress,
        [int]$TargetPort
    )

    try {
        $null = Invoke-WebRequest -Uri "http://$BindAddress`:$TargetPort/api/tags" -TimeoutSec 2 -UseBasicParsing
        return $true
    }
    catch {
        return $false
    }
}

if (-not (Test-Path $ollamaPath)) {
    throw "Ollama executable not found at $ollamaPath"
}

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
New-Item -ItemType Directory -Path $modelsDir -Force | Out-Null

$env:OLLAMA_MODELS = $modelsDir
if ($ResetModelsPath -or [Environment]::GetEnvironmentVariable("OLLAMA_MODELS", "User") -ne $modelsDir) {
    [Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $modelsDir, "User")
}

if (Test-OllamaListening -BindAddress $BindHost -TargetPort $Port) {
    Write-Host "Ollama is already available at http://$BindHost`:$Port using $modelsDir"
    exit 0
}

$serveCommand = "`$env:OLLAMA_MODELS = '$modelsDir'; & '$ollamaPath' serve"
$process = Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList @("-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $serveCommand) `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru `
    -WindowStyle Hidden

Set-Content -Path $pidFile -Value $process.Id -Encoding ascii

$deadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline) {
    if (Test-OllamaListening -BindAddress $BindHost -TargetPort $Port) {
        Write-Host "Ollama is ready at http://$BindHost`:$Port using $modelsDir"
        exit 0
    }
    Start-Sleep -Milliseconds 500
}

$errorTail = if (Test-Path $stderrLog) { (Get-Content $stderrLog -Tail 20 -ErrorAction SilentlyContinue) -join [Environment]::NewLine } else { "" }
throw "Ollama did not become ready within 20 seconds.`n$errorTail"
