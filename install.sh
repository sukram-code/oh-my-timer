#!/usr/bin/env bash
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/oh-my-timer"

chmod +x "$SRC/oh-my-timer.py"
mkdir -p "$(dirname "$DEST")"

if [ -L "$DEST" ] || [ -e "$DEST" ]; then
  if [ "$(readlink "$DEST" 2>/dev/null || true)" = "$SRC" ]; then
    echo "Already installed: $DEST -> $SRC"
  else
    echo "Error: $DEST already exists and is not a link to $SRC" >&2
    exit 1
  fi
else
  ln -s "$SRC" "$DEST"
  echo "Linked $DEST -> $SRC"
fi

cat <<EOF

Next steps:
  1. Add 'oh-my-timer' to the plugins list in ~/.zshrc, e.g.
       plugins=(git oh-my-timer)
  2. Reload your shell:  exec zsh
  3. Run:  timer 25m
EOF
