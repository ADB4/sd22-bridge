# Installs the Substance Designer <-> Claude bridge on Windows 10/11.
# Run install.bat (double-click), or:
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
# Options:
#   -SkipClaudeConfig   don't touch Claude Desktop's config file
#   -ClaudeDesktop      add the Claude Desktop entry without asking

param(
    [switch]$SkipClaudeConfig,
    [switch]$ClaudeDesktop
)

$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Step($text) {
    Write-Host ""
    Write-Host "== $text" -ForegroundColor Cyan
}

function Fail($text) {
    Write-Host ""
    Write-Host "ERROR: $text" -ForegroundColor Red
    exit 1
}

Write-Host "Substance Designer <-> Claude bridge installer"

# --------------------------------------------------------------------------
Step "1/4  Installing the Designer plugin"

$pluginSrc = Join-Path $here 'designer_plugin\sd_claude_bridge'
if (-not (Test-Path -LiteralPath $pluginSrc)) {
    Fail "Can't find $pluginSrc. Unzip the whole folder first, then run install.bat from inside it."
}

# GetFolderPath follows OneDrive/Documents redirection, same as Designer.
# Adobe installs use the Adobe folder; the Steam edition of Designer 2022 still
# uses the Allegorithmic one. Install into every one that exists.
$docs = [Environment]::GetFolderPath('MyDocuments')
$sdUserDirs = @(
    (Join-Path $docs 'Adobe\Adobe Substance 3D Designer'),
    (Join-Path $docs 'Allegorithmic\Substance Designer')
)
$targets = @($sdUserDirs | Where-Object { Test-Path -LiteralPath $_ })
if ($targets.Count -eq 0) {
    Write-Host "   Note: no Designer user folder found yet (Designer creates one on first launch). Using $($sdUserDirs[0])." -ForegroundColor Yellow
    Write-Host "   Steam edition: start Designer once, then run this installer again." -ForegroundColor Yellow
    $targets = @($sdUserDirs[0])
} elseif ((Test-Path -LiteralPath $sdUserDirs[0]) -and -not (Test-Path -LiteralPath $sdUserDirs[1])) {
    # Maybe an earlier run made the Adobe folder before Designer's first launch.
    Write-Host "   Using the Steam edition? Its folder ($($sdUserDirs[1])) appears when Designer first starts:" -ForegroundColor Yellow
    Write-Host "   start Designer once, then run this installer again." -ForegroundColor Yellow
}

foreach ($sdUserDir in $targets) {
    $pluginParent = Join-Path $sdUserDir 'python\sduserplugins'
    $pluginDest = Join-Path $pluginParent 'sd_claude_bridge'

    New-Item -ItemType Directory -Force -Path $pluginParent | Out-Null
    # tools\link_install.py may have made it a junction into a git checkout. Leave that
    # alone: Windows PowerShell's Remove-Item -Recurse would delete the checkout's files.
    # Test the link type, not the ReparsePoint attribute: OneDrive placeholders have that too.
    $existing = Get-Item -LiteralPath $pluginDest -Force -ErrorAction SilentlyContinue
    if ($existing -and ($existing.LinkType -in @('Junction', 'SymbolicLink'))) {
        if (Test-Path -LiteralPath (Join-Path $pluginDest '__init__.py')) {
            Write-Host "   Linked to a git checkout, left as is: $pluginDest"
            continue
        }
        $existing.Delete()  # deletes only the link
        Write-Host "   Removed a link to a checkout that is gone: $pluginDest"
    }
    # Never delete the source: a checkout cloned as sduserplugins\sd_claude_bridge, or an
    # sduserplugins folder that is itself a link (into a checkout, for example).
    $parentItem = Get-Item -LiteralPath $pluginParent -Force -ErrorAction SilentlyContinue
    $parentLinked = $parentItem -and ($parentItem.LinkType -in @('Junction', 'SymbolicLink'))
    if ((Test-Path -LiteralPath (Join-Path $pluginDest '.git')) -or $parentLinked) {
        Write-Host "   Left as is (a git checkout, or a linked sduserplugins folder): $pluginDest" -ForegroundColor Yellow
        continue
    }
    if (Test-Path -LiteralPath $pluginDest) {
        Remove-Item -LiteralPath $pluginDest -Recurse -Force -ErrorAction SilentlyContinue
        # Windows PowerShell can't delete OneDrive cloud files; cmd's rmdir can, and doesn't follow junctions.
        if (Test-Path -LiteralPath $pluginDest) { cmd /c rmdir /s /q "$pluginDest" 2>$null }
        # Copying onto what's left would nest the new plugin inside the old one.
        if (Test-Path -LiteralPath $pluginDest) {
            Fail "Could not remove the old plugin at $pluginDest. Quit Designer, which keeps its files open, and run install.bat again."
        }
    }
    Copy-Item -LiteralPath $pluginSrc -Destination $pluginDest -Recurse -Force -ErrorVariable copyErrors
    if ($copyErrors -or -not (Test-Path -LiteralPath (Join-Path $pluginDest '__init__.py'))) {
        Fail "Could not copy the plugin to $pluginDest (see the messages above)."
    }
    Get-ChildItem -LiteralPath $pluginDest -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force
    Write-Host "   Plugin copied to: $pluginDest"
}

# --------------------------------------------------------------------------
Step "2/4  Finding Python 3.10 or newer"

function Get-PyVersion($exe, $extra) {
    $pyArgs = @()
    if ($extra) { $pyArgs += $extra }
    # No double quotes in the code: Windows PowerShell 5.1 mangles them for native commands.
    $pyArgs += @('-c', 'import sys; print(sys.version_info[0], sys.version_info[1])')
    try {
        $out = & $exe @pyArgs 2>$null
    } catch {
        return $null
    }
    if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
    return ($out | Select-Object -First 1).ToString().Trim()
}

$candidates = @(
    @{ Exe = 'py';      Extra = @('-3.12') },
    @{ Exe = 'py';      Extra = @('-3.13') },
    @{ Exe = 'py';      Extra = @('-3.11') },
    @{ Exe = 'py';      Extra = @('-3.10') },
    @{ Exe = 'py';      Extra = @('-3') },
    @{ Exe = 'python';  Extra = @() },
    @{ Exe = 'python3'; Extra = @() }
)

$py = $null
foreach ($c in $candidates) {
    if (-not (Get-Command $c.Exe -ErrorAction SilentlyContinue)) { continue }
    $v = Get-PyVersion $c.Exe $c.Extra
    if (-not $v) { continue }
    $parts = $v -split '\s+'
    if ($parts.Count -lt 2) { continue }
    if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 10) {
        $py = $c
        $py.Version = "$($parts[0]).$($parts[1])"
        break
    }
}

if (-not $py) {
    Fail ("Python 3.10 or newer was not found.`n" +
          "       Install it from https://www.python.org/downloads/windows/ (64-bit installer,`n" +
          "       tick 'Add python.exe to PATH'), then run install.bat again.")
}
Write-Host "   Using: $($py.Exe) $($py.Extra -join ' ')  (Python $($py.Version))"

# --------------------------------------------------------------------------
Step "3/4  Installing the MCP server"

$installDir = Join-Path $env:LOCALAPPDATA 'sd-claude-bridge'
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
foreach ($f in Get-ChildItem -LiteralPath (Join-Path $here 'mcp_server') -File) {
    $dest = Join-Path $installDir $f.Name
    $existing = Get-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue
    if ($existing -and ($existing.LinkType -eq 'SymbolicLink')) {
        $target = [string]($existing.Target | Select-Object -First 1)
        if ($target -and (Test-Path -LiteralPath $target)) {
            Write-Host "   Linked to a git checkout, left as is: $dest"
            continue
        }
        $existing.Delete()  # its checkout is gone: copy the file instead
    }
    Copy-Item -Force -LiteralPath $f.FullName -Destination $dest -ErrorVariable copyErrors
    if ($copyErrors) {
        Fail "Could not copy $($f.Name) to $installDir (see the messages above)."
    }
}

$venv = Join-Path $installDir 'venv'
$vpy = Join-Path $venv 'Scripts\python.exe'

# Rebuild the venv if it's broken (e.g. the Python it was made from was removed).
if (Test-Path -LiteralPath $vpy) {
    & $vpy -c 'pass' 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   Existing virtual environment is broken; recreating it." -ForegroundColor Yellow
        Remove-Item -LiteralPath $venv -Recurse -Force -ErrorAction SilentlyContinue
        if (Test-Path -LiteralPath $venv) {
            Fail "Could not remove the broken virtual environment in $venv. Quit Claude Desktop, which runs the server from it, and run install.bat again."
        }
    }
}
if (-not (Test-Path -LiteralPath $vpy)) {
    $pyExe = $py.Exe
    $venvArgs = @()
    if ($py.Extra) { $venvArgs += $py.Extra }
    $venvArgs += @('-m', 'venv', $venv)
    & $pyExe @venvArgs
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $vpy)) {
        Fail "Could not create the virtual environment in $venv"
    }
}

& $vpy -m pip install --disable-pip-version-check --upgrade pip | Out-Null
& $vpy -m pip install --disable-pip-version-check -r (Join-Path $installDir 'requirements.txt')
if ($LASTEXITCODE -ne 0) {
    Fail "pip install failed (see the messages above). Check your internet connection and run install.bat again."
}

$server = Join-Path $installDir 'sd_designer_mcp.py'
& $vpy $server --check
if ($LASTEXITCODE -ne 0) {
    Fail "The MCP server failed its self-check (see the messages above)."
}
Write-Host "   Installed to: $installDir"

# --------------------------------------------------------------------------
Step "4/4  Connecting Claude"

$configure = $false
if ($SkipClaudeConfig) {
    $configure = $false
} elseif ($ClaudeDesktop) {
    $configure = $true
} elseif (-not [Console]::IsInputRedirected) {
    $answer = Read-Host "   Add 'substance-designer' to Claude Desktop's config now? [Y/n]"
    if ($answer -eq '' -or $answer -match '^[Yy]') {
        $configure = $true
    } else {
        Write-Host "   Skipped. See 'Manual setup' in README.md."
    }
} else {
    # Input from a pipe (a script, Claude Code): Read-Host would wait for an answer that never comes.
    Write-Host "   Not asked (no console input). Run install.ps1 -ClaudeDesktop to add the Claude Desktop entry."
}
if ($configure) {
    & $vpy (Join-Path $installDir 'configure_claude.py')
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   Config was not updated automatically; follow 'Manual setup' in README.md." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "   Claude Code users can register it with:"
Write-Host "   claude mcp add --scope user substance-designer -- `"$vpy`" `"$server`""

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Next:"
Write-Host "  1. Start (or restart) Substance Designer. Windows > Console should show:"
Write-Host "       [Claude bridge] v1.0.0 listening on 127.0.0.1:9881"
Write-Host "  2. Quit Claude Desktop completely (right-click the tray icon > Quit) and open it again."
Write-Host "  3. Open a graph in Designer and ask Claude: 'Check the Designer connection.'"
