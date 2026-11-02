# oh-my-timer (Windows / Git Bash): full-screen focus countdown timer
# Usage: timer 25m | timer 90s | timer 1m30s | timer 25
# Source this file from ~/.bashrc (windows/install.sh does it for you).

_OMT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Pick a working Python 3 once. `-c` rejects the Microsoft Store "python" stub.
_omt_find_python() {
  _OMT_PY=()
  local candidate
  for candidate in "py -3" "python" "python3"; do
    # shellcheck disable=SC2086  # intentional word splitting of "py -3"
    if command -v ${candidate%% *} >/dev/null 2>&1 &&
       $candidate -c 'import sys; sys.exit(sys.version_info < (3, 7))' >/dev/null 2>&1; then
      read -r -a _OMT_PY <<<"$candidate"
      return 0
    fi
  done
  return 1
}
_omt_find_python

timer() {
  if [ "${#_OMT_PY[@]}" -eq 0 ]; then
    echo "timer: Python 3 not found (tried: py -3, python, python3)" >&2
    return 1
  fi
  # Windows Terminal (WT_SESSION set) gives native console apps a real console;
  # plain mintty needs winpty for curses to work.
  if [ -z "${WT_SESSION:-}" ] && command -v winpty >/dev/null 2>&1; then
    winpty "${_OMT_PY[@]}" "$_OMT_DIR/oh-my-timer.py" "$@"
  else
    "${_OMT_PY[@]}" "$_OMT_DIR/oh-my-timer.py" "$@"
  fi
}
