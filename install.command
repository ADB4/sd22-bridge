#!/bin/sh
# Installs the Substance Designer <-> Claude bridge on macOS.
# Double-click this file in Finder, or run it in Terminal:
#   sh install.command [--skip-claude-config | --claude-desktop]
# Options:
#   --skip-claude-config   don't touch Claude Desktop's config file
#   --claude-desktop       add the Claude Desktop entry without asking
# Written for /bin/sh (POSIX), so it runs on the bash 3.2 that macOS ships.

HERE=$(cd "$(dirname "$0")" && pwd)
HERE_REAL=$(cd "$HERE" && pwd -P)
SKIP_CONFIG=0
FORCE_CONFIG=0
for arg in "$@"; do
    case "$arg" in
        --skip-claude-config) SKIP_CONFIG=1 ;;
        --claude-desktop) FORCE_CONFIG=1 ;;
        *) echo "Unknown option: $arg"; exit 2 ;;
    esac
done

INTERACTIVE=0
[ -t 0 ] && INTERACTIVE=1

step() {
    echo ""
    echo "== $1"
}

finish() {
    # A double-clicked .command may close its window on exit: keep the output readable.
    if [ "$INTERACTIVE" = 1 ]; then
        echo ""
        printf "Press Return to close. "
        read -r _ignored
    fi
    exit "$1"
}

# True when $1 is the folder this script runs from, or inside it, after resolving links.
# Used to never delete the source (a checkout cloned or linked at the plugin path).
inside_here() {
    real=$(cd "$1" 2>/dev/null && pwd -P) || return 1
    case "$real/" in
        "$HERE_REAL"/*) return 0 ;;
    esac
    return 1
}

fail() {
    echo ""
    echo "ERROR: $1"
    finish 1
}

echo "Substance Designer <-> Claude bridge installer (macOS)"

if [ "$(uname -s)" != "Darwin" ]; then
    echo "This installer is for macOS. On Windows, run install.bat."
    exit 1
fi

# --------------------------------------------------------------------------
step "1/4  Installing the Designer plugin"

PLUGIN_SRC="$HERE/designer_plugin/sd_claude_bridge"
[ -d "$PLUGIN_SRC" ] || fail "Can't find $PLUGIN_SRC. Unzip the whole folder first, then run install.command from inside it."

# Adobe installs use the Adobe folder; the Steam edition uses the Allegorithmic one.
# Install into every one that exists.
ADOBE_DIR="$HOME/Documents/Adobe/Adobe Substance 3D Designer"
STEAM_DIR="$HOME/Documents/Allegorithmic/Substance Designer"
TARGETS=""
for d in "$ADOBE_DIR" "$STEAM_DIR"; do
    [ -d "$d" ] && TARGETS="$TARGETS
$d"
done
if [ -z "$TARGETS" ]; then
    # Designer creates its Documents folder on first launch. Guess the edition from its
    # settings folder, else assume the Adobe one.
    if [ -d "$HOME/Library/Application Support/Allegorithmic/Substance Designer" ] &&
       [ ! -d "$HOME/Library/Application Support/Adobe/Adobe Substance 3D Designer" ]; then
        TARGETS="$STEAM_DIR"
    else
        TARGETS="$ADOBE_DIR"
    fi
    echo "   Note: no Designer user folder found yet (Designer creates one on first launch)."
    echo "   Using: $TARGETS"
    echo "   If the plugin doesn't load, start Designer once, quit it, and run this installer again."
elif [ -d "$ADOBE_DIR" ] && [ ! -d "$STEAM_DIR" ]; then
    # Maybe an earlier run made the Adobe folder before Designer's first launch.
    echo "   Using the Steam edition? Its folder ($STEAM_DIR) appears when Designer first starts:"
    echo "   start Designer once, then run this installer again."
fi

OLD_IFS=$IFS
IFS='
'
set -f  # split on newlines only, no globbing
for d in $TARGETS; do
    [ -n "$d" ] || continue
    dest="$d/python/sduserplugins/sd_claude_bridge"
    if ! mkdir -p "$d/python/sduserplugins" 2>/dev/null; then
        IFS=$OLD_IFS
        fail "Could not write to $d.
       If macOS asked whether Terminal may access your Documents folder, allow it:
       System Settings > Privacy & Security > Files and Folders > Terminal > Documents Folder.
       Then run this installer again."
    fi
    if [ -L "$dest" ]; then
        if [ -e "$dest" ]; then
            # tools/link_install.py pointed it at a git checkout; a copy would undo that.
            echo "   Linked to a git checkout, left as is: $dest"
            continue
        fi
        rm -f "$dest"
        echo "   Removed a link to a checkout that is gone: $dest"
    fi
    if [ -e "$dest/.git" ] || inside_here "$dest"; then
        echo "   Left as is (a git checkout, or the folder this installer runs from): $dest"
        continue
    fi
    rm -rf "$dest"
    if ! cp -R "$PLUGIN_SRC" "$dest"; then
        IFS=$OLD_IFS
        fail "Could not copy the plugin to $dest (see the message above)."
    fi
    find "$dest" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null
    echo "   Plugin copied to: $dest"
done
set +f
IFS=$OLD_IFS

# --------------------------------------------------------------------------
step "2/4  Finding Python 3.10 or newer"

PY=""
for name in python3.12 python3.13 python3.11 python3.10 python3.14 python3; do
    for cand in "$(command -v "$name" 2>/dev/null)" \
                "/opt/homebrew/bin/$name" "/usr/local/bin/$name" \
                "/Library/Frameworks/Python.framework/Versions/Current/bin/$name"; do
        [ -n "$cand" ] && [ -x "$cand" ] || continue
        # /usr/bin/python3 is Apple's 3.9 (or a stub that pops up the Xcode tools installer).
        [ "$cand" = "/usr/bin/python3" ] && continue
        ok=$("$cand" -c 'import sys; print(sys.version_info >= (3, 10))' 2>/dev/null)
        if [ "$ok" = "True" ]; then
            PY="$cand"
            break 2
        fi
    done
done

if [ -z "$PY" ]; then
    fail "Python 3.10 or newer was not found.
       Install it from https://www.python.org/downloads/macos/ (the macOS 64-bit universal2
       installer), or with Homebrew: brew install python@3.12. Then run this installer again."
fi
echo "   Using: $PY ($("$PY" -c 'import platform; print(platform.python_version())'))"

# --------------------------------------------------------------------------
step "3/4  Installing the MCP server"

APP_DIR="$HOME/Library/Application Support/sd-claude-bridge"
mkdir -p "$APP_DIR" || fail "Could not create $APP_DIR"
for f in "$HERE"/mcp_server/*; do
    [ -f "$f" ] || continue
    t="$APP_DIR/$(basename "$f")"
    if [ -L "$t" ]; then
        if [ -e "$t" ]; then
            echo "   Linked to a git checkout, left as is: $t"
            continue
        fi
        rm -f "$t"  # its checkout is gone; cp would write through the link
    fi
    cp -f "$f" "$APP_DIR/"
done

VENV="$APP_DIR/venv"
VPY="$VENV/bin/python"

# Rebuild the venv if it's broken (e.g. the Python it was made from was removed, or
# Homebrew moved it to a new minor version).
if [ -d "$VENV" ] && ! "$VPY" -c 'pass' 2>/dev/null; then
    echo "   Existing virtual environment is broken; recreating it."
    rm -rf "$VENV"
fi
if [ ! -d "$VENV" ]; then
    "$PY" -m venv "$VENV" || fail "Could not create the virtual environment in $VENV"
fi

"$VPY" -m pip install --disable-pip-version-check -q --upgrade pip >/dev/null 2>&1
if ! "$VPY" -m pip install --disable-pip-version-check -q -r "$APP_DIR/requirements.txt"; then
    fail "pip install failed (see the messages above). Check your internet connection and run this installer again."
fi

SERVER="$APP_DIR/sd_designer_mcp.py"
"$VPY" "$SERVER" --check || fail "The MCP server failed its self-check (see the messages above)."
echo "   Installed to: $APP_DIR"

# --------------------------------------------------------------------------
step "4/4  Connecting Claude"

configure=0
if [ "$SKIP_CONFIG" = 1 ]; then
    configure=0
elif [ "$FORCE_CONFIG" = 1 ]; then
    configure=1
elif [ "$INTERACTIVE" = 1 ]; then
    printf "   Add 'substance-designer' to Claude Desktop's config now? [Y/n] "
    read -r answer
    case "$answer" in
        ""|[Yy]*) configure=1 ;;
        *) echo "   Skipped. See 'Manual setup' in README.md." ;;
    esac
else
    echo "   Not asked (no terminal). Re-run with --claude-desktop to add the Claude Desktop entry."
fi
if [ "$configure" = 1 ]; then
    "$VPY" "$APP_DIR/configure_claude.py" ||
        echo "   Config was not updated automatically; follow 'Manual setup' in README.md."
fi

echo ""
echo "   Claude Code users can register it with:"
echo "   claude mcp add --scope user substance-designer -- \"$VPY\" \"$SERVER\""

echo ""
echo "Done."
echo "Next:"
echo "  1. Start (or restart) Substance Designer. Windows > Console should show:"
echo "       [Claude bridge] v1.0.0 listening on 127.0.0.1:9881"
echo "  2. Quit Claude completely (Cmd+Q, or Claude > Quit Claude in the menu bar) and open it again."
echo "  3. Open a graph in Designer and ask Claude: 'Check the Designer connection.'"
finish 0
