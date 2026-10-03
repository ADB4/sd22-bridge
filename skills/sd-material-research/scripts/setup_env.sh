#!/usr/bin/env bash
# Create (once) the Python environment used by matcheck.py and previews.py, then print its python path.
# Usage: bash setup_env.sh            -> prints e.g. /Users/me/.cache/sd-material-research/venv/bin/python
#                                        (Windows, Git Bash: /c/Users/me/.cache/sd-material-research/venv/Scripts/python.exe)
#        SDMR_VENV=/path bash setup_env.sh   (override location)
# Only the path goes to stdout; venv and pip output go to stderr.
set -euo pipefail
VENV="${SDMR_VENV:-$HOME/.cache/sd-material-research/venv}"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) WINDOWS=1 ;;
  *) WINDOWS=0 ;;
esac
if [ "$WINDOWS" = 1 ] || [ -x "$VENV/Scripts/python.exe" ]; then
  PY="$VENV/Scripts/python.exe"
else
  PY="$VENV/bin/python"
fi

# Sets BASE to a command that runs a real Python 3. On Windows, prefer the py launcher, then python, and skip
# the Microsoft Store stubs in WindowsApps (they open the Store instead of running Python).
find_base() {
  local cands=() c path
  if [ "$WINDOWS" = 1 ]; then cands=("py -3" python python3); else cands=(python3); fi
  for c in "${cands[@]}"; do
    path="$(command -v "${c%% *}" 2>/dev/null)" || continue
    case "$path" in */WindowsApps/*) continue ;; esac
    read -r -a BASE <<< "$c"
    "${BASE[@]}" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 && return 0
  done
  echo "setup_env.sh: no Python 3 found (tried: ${cands[*]})" >&2
  return 1
}

if [ ! -x "$PY" ]; then
  find_base
  mkdir -p "$(dirname "$VENV")"
  "${BASE[@]}" -m venv "$VENV" >&2
  "$PY" -m pip install --quiet --upgrade pip >&2
fi
if ! "$PY" -c "import numpy, PIL, scipy, cv2" 2>/dev/null; then
  "$PY" -m pip install --quiet numpy pillow scipy opencv-python >&2
fi
echo "$PY"
