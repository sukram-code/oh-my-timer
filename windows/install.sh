#!/usr/bin/env bash
# Install oh-my-timer for Git Bash on Windows (run this from Git Bash).
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RC="$HOME/.bashrc"
MARK_BEGIN="# >>> oh-my-timer >>>"
MARK_END="# <<< oh-my-timer <<<"

# shellcheck source=oh-my-timer.bash
source "$SRC/oh-my-timer.bash"
if [ "${#_OMT_PY[@]}" -eq 0 ]; then
  echo "Error: Python 3 not found (tried: py -3, python, python3)." >&2
  echo "Install it from https://www.python.org/downloads/windows/ and re-run." >&2
  exit 1
fi
echo "Using Python: ${_OMT_PY[*]}"

if "${_OMT_PY[@]}" -c 'import curses' >/dev/null 2>&1; then
  echo "curses is available"
else
  echo "Installing windows-curses..."
  "${_OMT_PY[@]}" -m pip install --user windows-curses
fi

if [ -f "$RC" ] && grep -qF "$MARK_BEGIN" "$RC"; then
  echo "Already configured in $RC"
else
  {
    echo ""
    echo "$MARK_BEGIN"
    echo "source \"$SRC/oh-my-timer.bash\""
    echo "$MARK_END"
  } >>"$RC"
  echo "Added oh-my-timer to $RC"
fi

cat <<EOF

Next steps:
  1. Reload your shell:  source ~/.bashrc
  2. Run:  timer 25m
EOF
