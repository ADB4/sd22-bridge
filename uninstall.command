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
    if [ -e "$p" ]; then
        rm -rf "$p" 2>/dev/null
        if [ -e "$p" ]; then
            echo "   Could not fully remove $p (quit Designer and Claude, then try again)."
        else
            echo "   Removed $p"
        fi
    fi
done

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
