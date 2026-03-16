param(
    [int]$Port = 4173
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot ".strattonai-runtime"
$pidFile = Join-Path $runtimeDir "preview.pid"
$stateFile = Join-Path $runtimeDir "preview.state.json"
$stopped = $false
$resolvedPort = $Port

function Test-PortListening {
    param([int]$TargetPort)

    try {
        $connection = Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction Stop | Select-Object -First 1
        return $null -ne $connection
    }
    catch {
        return $false
    }
}

function Stop-ProcessTreeByIdIfRunning {
    param([int]$ProcessId)

    try {
        $null = Get-Process -Id $ProcessId -ErrorAction Stop
        $null = & taskkill.exe /PID $ProcessId /T /F 2>$null
        return $true
    }
    catch {
        return $false
    }
}

function Wait-ForPortToClose {
    param(
        [int]$TargetPort,
        [int]$TimeoutSeconds = 10
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (-not (Test-PortListening -TargetPort $TargetPort)) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }

    return -not (Test-PortListening -TargetPort $TargetPort)
}

function Get-PreviewState {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return $null
    }

    try {
        return Get-Content $Path -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        Remove-Item $Path -ErrorAction SilentlyContinue
        return $null
    }
}

$previewState = Get-PreviewState -Path $stateFile
if ($null -ne $previewState -and $previewState.port) {
    $resolvedPort = [int]$previewState.port
}

if (Test-Path $pidFile) {
    $rawPid = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($rawPid) {
        $stopped = Stop-ProcessTreeByIdIfRunning -ProcessId ([int]$rawPid)
    }
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}
Remove-Item $stateFile -ErrorAction SilentlyContinue

if (-not $stopped) {
    try {
        $connection = Get-NetTCPConnection -LocalPort $resolvedPort -State Listen -ErrorAction Stop | Select-Object -First 1
        if ($null -ne $connection -and $connection.OwningProcess) {
            $stopped = Stop-ProcessTreeByIdIfRunning -ProcessId $connection.OwningProcess
        }
    }
    catch {
    }
}

if ($stopped) {
    $null = Wait-ForPortToClose -TargetPort $resolvedPort
    Write-Host "Stopped StrattonAI preview server."
}
else {
    Write-Host "No running StrattonAI preview server was found."
}
