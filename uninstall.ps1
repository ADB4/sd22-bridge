# Removes the Substance Designer <-> Claude bridge.
# Run uninstall.bat, or: powershell -NoProfile -ExecutionPolicy Bypass -File uninstall.ps1

$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

$installDir = Join-Path $env:LOCALAPPDATA 'sd-claude-bridge'
$vpy = Join-Path $installDir 'venv\Scripts\python.exe'
$cfgScript = Join-Path $installDir 'configure_claude.py'

Write-Host "Removing the Claude Desktop config entry..."
if ((Test-Path -LiteralPath $vpy) -and (Test-Path -LiteralPath $cfgScript)) {
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

function Remove-LinksIn($dir) {
    # Links made by tools\link_install.py point into a git checkout. Delete only the link:
    # Windows PowerShell's Remove-Item -Recurse follows a junction and empties its target.
    # The link type, not the ReparsePoint attribute: OneDrive placeholders have that too.
    Get-ChildItem -LiteralPath $dir -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.LinkType -in @('Junction', 'SymbolicLink') } |
        ForEach-Object { $_.Delete() }
}

function Test-InCheckout($path) {
    # A git checkout cloned at the path, or a path whose parent folder is a link (into a checkout,
    # for example): never delete those.
    if (Test-Path -LiteralPath (Join-Path $path '.git')) { return $true }
    $parent = Get-Item -LiteralPath (Split-Path -Parent $path) -Force -ErrorAction SilentlyContinue
    return [bool]($parent -and ($parent.LinkType -in @('Junction', 'SymbolicLink')))
}

foreach ($p in ($pluginDests + @($installDir, $sessionDir, $previewDir))) {
    $item = Get-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue
    if ($item) {
        if ($item.LinkType -in @('Junction', 'SymbolicLink')) {
            $item.Delete()
        } elseif (($pluginDests -contains $p) -and (Test-InCheckout $p)) {
            Write-Host "   Left as is (a git checkout, or inside a linked folder): $p" -ForegroundColor Yellow
            continue
        } else {
            Remove-LinksIn $p
            Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue
            # Windows PowerShell can't delete OneDrive cloud files; cmd's rmdir can, and doesn't follow junctions.
            if (Test-Path -LiteralPath $p) { cmd /c rmdir /s /q "$p" 2>$null }
        }
        if (Test-Path -LiteralPath $p) {
            Write-Host "   Could not fully remove $p (close Designer / Claude Desktop and try again)." -ForegroundColor Yellow
        } else {
            Write-Host "   Removed $p"
        }
    }
}

# tools\link_install.py links the skill into this folder; without the bridge it would keep loading.
$skillLink = Join-Path $env:USERPROFILE '.claude\skills\sd-material-research'
$skill = Get-Item -LiteralPath $skillLink -Force -ErrorAction SilentlyContinue
if ($skill -and ($skill.LinkType -in @('Junction', 'SymbolicLink'))) {
    $target = [string]($skill.Target | Select-Object -First 1)
    if ($target.StartsWith('\??\')) { $target = $target.Substring(4) }
    $inside = [IO.Path]::GetFullPath($here).TrimEnd('\') + '\'
    if ($target -and [IO.Path]::GetFullPath($target).StartsWith($inside, [StringComparison]::OrdinalIgnoreCase)) {
        $skill.Delete()
        Write-Host "   Removed $skillLink"
    }
}

Write-Host ""
Write-Host "Done. Restart Designer and Claude Desktop." -ForegroundColor Green
