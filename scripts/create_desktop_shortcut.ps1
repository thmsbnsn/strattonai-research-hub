param(
    [string]$ShortcutName = "StrattonAI.lnk"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath $ShortcutName
$launcherScript = Join-Path $PSScriptRoot "start_strattonai.ps1"
$iconPath = Join-Path $repoRoot "public\\favicon.ico"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = (Get-Command powershell.exe -ErrorAction Stop).Source
$shortcut.Arguments = "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$launcherScript`""
$shortcut.WorkingDirectory = $repoRoot
$shortcut.Description = "Start StrattonAI in your default browser."
if (Test-Path $iconPath) {
    $shortcut.IconLocation = $iconPath
}
$shortcut.Save()

Write-Host "Desktop shortcut created at $shortcutPath"
