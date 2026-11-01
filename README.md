# oh-my-timer

A full-screen focus countdown timer for the terminal, packaged as an oh-my-zsh plugin. It needs only Python 3 and the standard library's `curses`.

## Install

```sh
./install.sh
```

Then add `oh-my-timer` to `plugins=(...)` in `~/.zshrc` and run `exec zsh`.

## Usage

```sh
timer 25      # bare number = minutes
timer 25m
timer 90s
timer 1m30s
timer 1h
```

| Key | Action |
|---|---|
| ↑ / ↓ (or k / j) | move selection |
| Enter | confirm |
| q / Esc / Ctrl-C | quit |

Flow: **Start** → running (**Pause** / Quit) → paused (**Resume** / Quit) → time's up, which plays a beep (**Restart** / Quit).

## Tests

```sh
python3 -m unittest discover tests
```
