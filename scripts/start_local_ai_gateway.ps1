param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8787,
    [int]$WaitSeconds = 25
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot ".strattonai-runtime"
$stdoutLog = Join-Path $runtimeDir "local-ai.stdout.log"
$stderrLog = Join-Path $runtimeDir "local-ai.stderr.log"
$pidFile = Join-Path $runtimeDir "local-ai.pid"
$stateFile = Join-Path $runtimeDir "local-ai.state.json"
$startOllamaScript = Join-Path $PSScriptRoot "start_ollama.ps1"

function Test-AiGatewayListening {
    param([string]$TargetUrl)

    try {
        $response = Invoke-WebRequest -Uri "$TargetUrl/health" -TimeoutSec 2 -UseBasicParsing
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Resolve-PythonPath {
    $candidates = @(
        $env:STRATTONAI_PYTHON,
        "C:\Users\$env:USERNAME\.lmstudio\extensions\backends\vendor\_amphibian\cpython3.11-win-x86@6\python.exe",
        "C:\Users\$env:USERNAME\.lmstudio\extensions\backends\vendor\_amphibian\app-harmony-win-x86@7\Scripts\python.exe"
    ) | Where-Object { $_ }

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $discovered = Get-ChildItem "C:\Users\$env:USERNAME\.lmstudio\extensions\backends\vendor\_amphibian" -Recurse -Filter python.exe -ErrorAction SilentlyContinue |
        Sort-Object FullName |
        Select-Object -First 1 -ExpandProperty FullName

    if ($discovered) {
        return $discovered
    }

    throw "Could not resolve a working Python executable for the local AI gateway."
}

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

$gatewayUrl = "http://$BindHost`:$Port"
if (Test-AiGatewayListening -TargetUrl $gatewayUrl) {
    Write-Host "Local AI gateway is already available at $gatewayUrl"
    exit 0
}

if (Test-Path $startOllamaScript) {
    try {
        & $startOllamaScript | Out-Null
    }
    catch {
        Write-Warning "Ollama startup helper failed. The AI gateway will continue and may fall back to deterministic mode."
    }
}

$pythonPath = Resolve-PythonPath
$process = Start-Process `
    -FilePath $pythonPath `
    -ArgumentList @("-m", "research.local_ai_gateway", "--host", $BindHost, "--port", "$Port") `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru `
    -WindowStyle Hidden

Set-Content -Path $pidFile -Value $process.Id -Encoding ascii
Set-Content -Path $stateFile -Value (@{
    pid = $process.Id
    url = $gatewayUrl
    port = $Port
    updatedAt = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json) -Encoding utf8

$deadline = (Get-Date).AddSeconds($WaitSeconds)
while ((Get-Date) -lt $deadline) {
    if (Test-AiGatewayListening -TargetUrl $gatewayUrl) {
        Write-Host "Local AI gateway is ready at $gatewayUrl"
        exit 0
    }

    try {
        $null = Get-Process -Id $process.Id -ErrorAction Stop
    }
    catch {
        break
    }

    Start-Sleep -Milliseconds 500
}

$errorTail = if (Test-Path $stderrLog) { (Get-Content $stderrLog -Tail 20 -ErrorAction SilentlyContinue) -join [Environment]::NewLine } else { "" }
throw "Local AI gateway did not become ready within $WaitSeconds seconds.`n$errorTail"
