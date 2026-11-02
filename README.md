# oh-my-timer

A full-screen focus countdown timer for the terminal. It needs Python 3 and `curses`.

There are two self-contained variants:

| Folder | Platform | Shell integration |
|---|---|---|
| [`macos/`](macos) | macOS | oh-my-zsh plugin |
| [`windows/`](windows) | Windows, Git Bash in Windows Terminal | function sourced from `~/.bashrc` |

## Install

### macOS (oh-my-zsh)

```sh
./macos/install.sh
```

Then add `oh-my-timer` to `plugins=(...)` in `~/.zshrc` and run `exec zsh`.

> Upgrading from the old single-folder layout? Re-run `./macos/install.sh` once. It repoints the plugin symlink to `macos/`.

### Windows (Git Bash + Windows Terminal)

Requires Python 3 from [python.org](https://www.python.org/downloads/windows/). In Git Bash, run:

```sh
./windows/install.sh
source ~/.bashrc
```

The installer finds Python (`py -3`, `python` or `python3`). If curses is missing, it installs [`windows-curses`](https://pypi.org/project/windows-curses/) with `pip --user`. It also adds a `source` line to `~/.bashrc`. If you run it in plain mintty Git Bash rather than Windows Terminal, the timer goes through `winpty` automatically.

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

Flow: **Start** → running (**Pause** / Quit) → paused (**Resume** / Quit) → time's up, which plays a sound (**Restart** / Quit).

## Tests

```sh
python3 -m unittest discover macos/tests     # macOS
py -m unittest discover windows/tests        # Windows
```
