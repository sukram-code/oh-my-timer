# oh-my-timer: full-screen focus countdown timer
# Usage: timer 25m | timer 90s | timer 1m30s | timer 25

_OMT_DIR="${0:A:h}"

timer() {
  python3 "$_OMT_DIR/oh-my-timer.py" "$@"
}
