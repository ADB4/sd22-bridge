#!/usr/bin/env bash
# Create (once) the Python environment used by matcheck.py and previews.py, then print its python path.
# Usage: bash setup_env.sh            -> prints e.g. /Users/me/.cache/sd-material-research/venv/bin/python
#        SDMR_VENV=/path bash setup_env.sh   (override location)
set -euo pipefail
VENV="${SDMR_VENV:-$HOME/.cache/sd-material-research/venv}"
PY="$VENV/bin/python"
if [ ! -x "$PY" ]; then
  BASE="$(command -v python3)"
  mkdir -p "$(dirname "$VENV")"
  "$BASE" -m venv "$VENV" >&2
  "$PY" -m pip install --quiet --upgrade pip >&2
fi
if ! "$PY" -c "import numpy, PIL, scipy" 2>/dev/null; then
  "$PY" -m pip install --quiet numpy pillow scipy >&2
fi
echo "$PY"
