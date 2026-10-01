# Removes the Substance Designer <-> Claude bridge.
# Run uninstall.bat, or: powershell -NoProfile -ExecutionPolicy Bypass -File uninstall.ps1

$ErrorActionPreference = 'Continue'

$installDir = Join-Path $env:LOCALAPPDATA 'sd-claude-bridge'
$vpy = Join-Path $installDir 'venv\Scripts\python.exe'
$cfgScript = Join-Path $installDir 'configure_claude.py'

Write-Host "Removing the Claude Desktop config entry..."
if ((Test-Path $vpy) -and (Test-Path $cfgScript)) {
    & $vpy $cfgScript --remove
} else {
    Write-Host "   Python environment not found; remove 'substance-designer' from claude_desktop_config.json by hand if present."
}

$docs = [Environment]::GetFolderPath('MyDocuments')
# Adobe installs and the Steam edition keep user plugins in different folders.
$pluginDests = @(
    (Join-Path $docs 'Adobe\Adobe Substance 3D Designer\python\sduserplugins\sd_claude_bridge'),
    (Join-Path $docs 'Allegorithmic\Substance Designer\python\sduserplugins\sd_claude_bridge')
)
$sessionDir = Join-Path $env:USERPROFILE '.sd_claude_bridge'
$previewDir = Join-Path $env:TEMP 'sd_claude_bridge'

foreach ($p in ($pluginDests + @($installDir, $sessionDir, $previewDir))) {
    if (Test-Path $p) {
        Remove-Item -Recurse -Force $p -ErrorAction SilentlyContinue
        if (Test-Path $p) {
            Write-Host "   Could not fully remove $p (close Designer / Claude Desktop and try again)." -ForegroundColor Yellow
        } else {
            Write-Host "   Removed $p"
        }
    }
}

Write-Host ""
Write-Host "Done. Restart Designer and Claude Desktop." -ForegroundColor Green
