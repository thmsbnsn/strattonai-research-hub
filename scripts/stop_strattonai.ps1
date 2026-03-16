param(
    [int]$Port = 4173
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot ".strattonai-runtime"
$pidFile = Join-Path $runtimeDir "preview.pid"
$stopped = $false

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

if (Test-Path $pidFile) {
    $rawPid = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($rawPid) {
        $stopped = Stop-ProcessTreeByIdIfRunning -ProcessId ([int]$rawPid)
    }
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}

if (-not $stopped) {
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        if ($null -ne $connection -and $connection.OwningProcess) {
            $stopped = Stop-ProcessTreeByIdIfRunning -ProcessId $connection.OwningProcess
        }
    }
    catch {
    }
}

if ($stopped) {
    $null = Wait-ForPortToClose -TargetPort $Port
    Write-Host "Stopped StrattonAI preview server."
}
else {
    Write-Host "No running StrattonAI preview server was found."
}
