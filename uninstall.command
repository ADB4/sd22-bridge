#!/bin/sh
# Removes the Substance Designer <-> Claude bridge from macOS.
# Double-click this file in Finder, or run it in Terminal: sh uninstall.command

INTERACTIVE=0
[ -t 0 ] && INTERACTIVE=1

if [ "$(uname -s)" != "Darwin" ]; then
    echo "This uninstaller is for macOS. On Windows, run uninstall.bat."
    exit 1
fi

APP_DIR="$HOME/Library/Application Support/sd-claude-bridge"
HERE_REAL=$(cd "$(dirname "$0")" && pwd -P)

# True when $1 is the folder this script runs from, or inside it, after resolving links.
# Used to never delete the source (a checkout cloned or linked at the plugin path).
inside_here() {
    real=$(cd "$1" 2>/dev/null && pwd -P) || return 1
    case "$real/" in
        "$HERE_REAL"/*) return 0 ;;
    esac
    return 1
}
VPY="$APP_DIR/venv/bin/python"

echo "Removing the Claude Desktop config entry..."
if [ -x "$VPY" ] && [ -f "$APP_DIR/configure_claude.py" ]; then
    "$VPY" "$APP_DIR/configure_claude.py" --remove
else
    echo "   Python environment not found; remove 'substance-designer' from"
    echo "   ~/Library/Application Support/Claude/claude_desktop_config.json by hand if present."
fi

TMP_ROOT=${TMPDIR:-/tmp}
for p in \
    "$HOME/Documents/Adobe/Adobe Substance 3D Designer/python/sduserplugins/sd_claude_bridge" \
    "$HOME/Documents/Allegorithmic/Substance Designer/python/sduserplugins/sd_claude_bridge" \
    "$APP_DIR" \
    "$HOME/.sd_claude_bridge" \
    "${TMP_ROOT%/}/sd_claude_bridge"; do
    if [ -e "$p" ] || [ -L "$p" ]; then  # -L: also a link whose checkout is gone
        if [ ! -L "$p" ] && { [ -e "$p/.git" ] || inside_here "$p"; }; then
            echo "   Left as is (a git checkout, or the folder this uninstaller runs from): $p"
            continue
        fi
        rm -rf "$p" 2>/dev/null
        if [ -e "$p" ] || [ -L "$p" ]; then
            echo "   Could not fully remove $p (quit Designer and Claude, then try again)."
        else
            echo "   Removed $p"
        fi
    fi
done

# tools/link_install.py links the skill into this folder; without the bridge it would keep loading.
SKILL_LINK="$HOME/.claude/skills/sd-material-research"
if [ -L "$SKILL_LINK" ] && inside_here "$SKILL_LINK"; then
    rm -f "$SKILL_LINK" && echo "   Removed $SKILL_LINK"
fi

echo ""
echo "If you registered it with Claude Code, also run:"
echo "   claude mcp remove --scope user substance-designer"
echo ""
echo "Done. Restart Designer and Claude."

if [ "$INTERACTIVE" = 1 ]; then
    echo ""
    printf "Press Return to close. "
    read -r _ignored
fi
