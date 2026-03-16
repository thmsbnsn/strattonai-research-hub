param(
    [switch]$Rebuild,
    [switch]$InstallDeps,
    [switch]$NoBrowser,
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 4173,
    [int]$WaitSeconds = 30
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot ".strattonai-runtime"
$stdoutLog = Join-Path $runtimeDir "preview.stdout.log"
$stderrLog = Join-Path $runtimeDir "preview.stderr.log"
$pidFile = Join-Path $runtimeDir "preview.pid"
$distIndex = Join-Path $repoRoot "dist\\index.html"
$url = "http://$BindHost`:$Port/"

function Test-StrattonAiUrl {
    param([string]$TargetUrl)

    try {
        $null = Invoke-WebRequest -Uri $TargetUrl -TimeoutSec 2 -UseBasicParsing
        return $true
    }
    catch {
        return $false
    }
}

function Get-PreviewProcessFromPidFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return $null
    }

    $rawPid = Get-Content $Path -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $rawPid) {
        Remove-Item $Path -ErrorAction SilentlyContinue
        return $null
    }

    try {
        return Get-Process -Id ([int]$rawPid) -ErrorAction Stop
    }
    catch {
        Remove-Item $Path -ErrorAction SilentlyContinue
        return $null
    }
}

function Get-ListeningProcessId {
    param([int]$TargetPort)

    try {
        $connection = Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction Stop | Select-Object -First 1
        if ($null -ne $connection) {
            return [int]$connection.OwningProcess
        }
    }
    catch {
    }

    return $null
}

function Wait-ForPreview {
    param(
        [string]$TargetUrl,
        [int]$TimeoutSeconds,
        $PreviewProcess
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-StrattonAiUrl -TargetUrl $TargetUrl) {
            return $true
        }

        if ($null -ne $PreviewProcess) {
            try {
                $null = Get-Process -Id $PreviewProcess.Id -ErrorAction Stop
            }
            catch {
                return $false
            }
        }

        Start-Sleep -Milliseconds 500
    }

    return $false
}

function Ensure-NpmAvailable {
    $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($null -eq $npmCommand) {
        throw "npm.cmd was not found in PATH. Install Node.js before launching StrattonAI."
    }
    return $npmCommand.Source
}

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
$npmPath = Ensure-NpmAvailable

if ($InstallDeps -or -not (Test-Path (Join-Path $repoRoot "node_modules"))) {
    Write-Host "Installing npm dependencies..."
    & $npmPath install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed."
    }
}

if ($Rebuild -or -not (Test-Path $distIndex)) {
    Write-Host "Building StrattonAI..."
    & $npmPath run build
    if ($LASTEXITCODE -ne 0) {
        throw "npm run build failed."
    }
}

if (Test-StrattonAiUrl -TargetUrl $url) {
    Write-Host "StrattonAI is already available at $url"
    if (-not $NoBrowser) {
        Start-Process $url | Out-Null
    }
    exit 0
}

$existingProcess = Get-PreviewProcessFromPidFile -Path $pidFile
if ($null -ne $existingProcess) {
    if (Wait-ForPreview -TargetUrl $url -TimeoutSeconds 5 -PreviewProcess $existingProcess) {
        Write-Host "StrattonAI preview is already running at $url"
        if (-not $NoBrowser) {
            Start-Process $url | Out-Null
        }
        exit 0
    }

    Stop-Process -Id $existingProcess.Id -Force -ErrorAction SilentlyContinue
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}

Write-Host "Starting StrattonAI at $url"
$previewProcess = Start-Process `
    -FilePath $npmPath `
    -ArgumentList @("run", "preview", "--", "--host", $BindHost, "--port", "$Port", "--strictPort") `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru `
    -WindowStyle Hidden

Set-Content -Path $pidFile -Value $previewProcess.Id -Encoding ascii

if (-not (Wait-ForPreview -TargetUrl $url -TimeoutSeconds $WaitSeconds -PreviewProcess $previewProcess)) {
    $errorTail = ""
    if (Test-Path $stderrLog) {
        $errorTail = (Get-Content $stderrLog -Tail 20 -ErrorAction SilentlyContinue) -join [Environment]::NewLine
    }
    throw "StrattonAI preview did not become ready within $WaitSeconds seconds.`n$errorTail"
}

Start-Sleep -Milliseconds 500
$listeningProcessId = Get-ListeningProcessId -TargetPort $Port
if ($null -ne $listeningProcessId) {
    Set-Content -Path $pidFile -Value $listeningProcessId -Encoding ascii
}

Write-Host "StrattonAI is ready at $url"
if (-not $NoBrowser) {
    Start-Process $url | Out-Null
}
