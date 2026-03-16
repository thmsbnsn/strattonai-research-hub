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
$stateFile = Join-Path $runtimeDir "preview.state.json"
$distIndex = Join-Path $repoRoot "dist\\index.html"

function Test-StrattonAiUrl {
    param([string]$TargetUrl)

    try {
        $response = Invoke-WebRequest -Uri $TargetUrl -TimeoutSec 2 -UseBasicParsing
        if ($response.Content -match "<title>\s*StrattonAI" -or $response.Content -match "Quantitative Market Research") {
            return $true
        }
    }
    catch {
    }

    return $false
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

function Save-PreviewState {
    param(
        [string]$Path,
        [int]$ProcessId,
        [int]$TargetPort,
        [string]$TargetUrl
    )

    $payload = @{
        pid = $ProcessId
        port = $TargetPort
        url = $TargetUrl
        updatedAt = (Get-Date).ToUniversalTime().ToString("o")
    } | ConvertTo-Json
    Set-Content -Path $Path -Value $payload -Encoding utf8
}

function Open-StrattonAiInBrowser {
    param([string]$TargetUrl)

    $launchNonce = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $separator = if ($TargetUrl.Contains("?")) { "&" } else { "?" }
    $launchUrl = "$TargetUrl$separator" + "launch=$launchNonce"
    Start-Process $launchUrl | Out-Null
}

function Get-NewestProjectWriteTimeUtc {
    $pathsToCheck = @(
        (Join-Path $repoRoot "src"),
        (Join-Path $repoRoot "public"),
        (Join-Path $repoRoot "index.html"),
        (Join-Path $repoRoot "package.json"),
        (Join-Path $repoRoot "vite.config.ts")
    )

    $latest = [datetime]::MinValue
    foreach ($path in $pathsToCheck) {
        if (-not (Test-Path $path)) {
            continue
        }

        if ((Get-Item $path) -is [System.IO.DirectoryInfo]) {
            $items = Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue
        }
        else {
            $items = @(Get-Item $path)
        }

        foreach ($item in $items) {
            if ($item.LastWriteTimeUtc -gt $latest) {
                $latest = $item.LastWriteTimeUtc
            }
        }
    }

    return $latest
}

function Test-BuildRequired {
    if (-not (Test-Path $distIndex)) {
        return $true
    }

    $distWriteTime = (Get-Item $distIndex).LastWriteTimeUtc
    $projectWriteTime = Get-NewestProjectWriteTimeUtc
    return $projectWriteTime -gt $distWriteTime
}

function Resolve-LaunchTarget {
    param(
        [string]$BindAddress,
        [int]$PreferredPort
    )

    for ($candidatePort = $PreferredPort; $candidatePort -lt ($PreferredPort + 25); $candidatePort++) {
        $candidateUrl = "http://$BindAddress`:$candidatePort/"
        $listeningProcessId = Get-ListeningProcessId -TargetPort $candidatePort
        if ($null -eq $listeningProcessId) {
            return @{
                Port = $candidatePort
                Url = $candidateUrl
                Existing = $false
            }
        }

        if (Test-StrattonAiUrl -TargetUrl $candidateUrl) {
            return @{
                Port = $candidatePort
                Url = $candidateUrl
                Existing = $true
            }
        }
    }

    throw "Could not find an available launch port for StrattonAI starting at $PreferredPort."
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
$buildRequired = $Rebuild -or (Test-BuildRequired)

if ($InstallDeps -or -not (Test-Path (Join-Path $repoRoot "node_modules"))) {
    Write-Host "Installing npm dependencies..."
    & $npmPath install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed."
    }
    $buildRequired = $true
}

if ($buildRequired) {
    Write-Host "Building StrattonAI..."
    & $npmPath run build
    if ($LASTEXITCODE -ne 0) {
        throw "npm run build failed."
    }
}

$previewState = Get-PreviewState -Path $stateFile
if ($null -ne $previewState -and $previewState.url -and (Test-StrattonAiUrl -TargetUrl $previewState.url)) {
    Write-Host "StrattonAI is already available at $($previewState.url)"
    if (-not $NoBrowser) {
        Open-StrattonAiInBrowser -TargetUrl $previewState.url
    }
    exit 0
}

$existingProcess = Get-PreviewProcessFromPidFile -Path $pidFile
if ($null -ne $existingProcess) {
    $existingUrl = if ($null -ne $previewState -and $previewState.url) { $previewState.url } else { "http://$BindHost`:$Port/" }
    if (Wait-ForPreview -TargetUrl $existingUrl -TimeoutSeconds 5 -PreviewProcess $existingProcess) {
        Write-Host "StrattonAI preview is already running at $existingUrl"
        if (-not $NoBrowser) {
            Open-StrattonAiInBrowser -TargetUrl $existingUrl
        }
        exit 0
    }

    Stop-Process -Id $existingProcess.Id -Force -ErrorAction SilentlyContinue
    Remove-Item $pidFile -ErrorAction SilentlyContinue
    Remove-Item $stateFile -ErrorAction SilentlyContinue
}

$launchTarget = Resolve-LaunchTarget -BindAddress $BindHost -PreferredPort $Port
if ($launchTarget.Existing) {
    Save-PreviewState -Path $stateFile -ProcessId ([int](Get-ListeningProcessId -TargetPort $launchTarget.Port)) -TargetPort $launchTarget.Port -TargetUrl $launchTarget.Url
    Write-Host "StrattonAI is already running at $($launchTarget.Url)"
    if (-not $NoBrowser) {
        Open-StrattonAiInBrowser -TargetUrl $launchTarget.Url
    }
    exit 0
}

Write-Host "Starting StrattonAI at $($launchTarget.Url)"
$previewProcess = Start-Process `
    -FilePath $npmPath `
    -ArgumentList @("run", "preview", "--", "--host", $BindHost, "--port", "$($launchTarget.Port)", "--strictPort") `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru `
    -WindowStyle Hidden

Set-Content -Path $pidFile -Value $previewProcess.Id -Encoding ascii
Save-PreviewState -Path $stateFile -ProcessId $previewProcess.Id -TargetPort $launchTarget.Port -TargetUrl $launchTarget.Url

if (-not (Wait-ForPreview -TargetUrl $launchTarget.Url -TimeoutSeconds $WaitSeconds -PreviewProcess $previewProcess)) {
    $errorTail = ""
    if (Test-Path $stderrLog) {
        $errorTail = (Get-Content $stderrLog -Tail 20 -ErrorAction SilentlyContinue) -join [Environment]::NewLine
    }
    throw "StrattonAI preview did not become ready within $WaitSeconds seconds.`n$errorTail"
}

Start-Sleep -Milliseconds 500
$listeningProcessId = Get-ListeningProcessId -TargetPort $launchTarget.Port
if ($null -ne $listeningProcessId) {
    Set-Content -Path $pidFile -Value $listeningProcessId -Encoding ascii
    Save-PreviewState -Path $stateFile -ProcessId $listeningProcessId -TargetPort $launchTarget.Port -TargetUrl $launchTarget.Url
}

Write-Host "StrattonAI is ready at $($launchTarget.Url)"
if (-not $NoBrowser) {
    Open-StrattonAiInBrowser -TargetUrl $launchTarget.Url
}
