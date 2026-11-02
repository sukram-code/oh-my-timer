#!/usr/bin/env python3
"""oh-my-timer: a full-screen focus countdown timer for the terminal."""

import argparse
import curses
import math
import re
import shutil
import subprocess
import sys
import time

# --------------------------------------------------------------------------- #
# Duration parsing
# --------------------------------------------------------------------------- #

_DURATION_RE = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$")


def parse_duration(text):
    """Parse '25', '90s', '25m', '1m30s', '1h5m' into seconds.

    A bare integer means minutes. Raises ValueError on invalid or zero input.
    """
    text = (text or "").strip().lower()
    if not text:
        raise ValueError("empty duration")
    if text.isdigit():
        seconds = int(text) * 60
    else:
        match = _DURATION_RE.match(text)
        if not match or not any(match.groups()):
            raise ValueError(f"invalid duration: {text!r}")
        h, m, s = (int(g) if g else 0 for g in match.groups())
        seconds = h * 3600 + m * 60 + s
    if seconds <= 0:
        raise ValueError("duration must be greater than zero")
    return seconds


def format_time(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# --------------------------------------------------------------------------- #
# Big block font
# --------------------------------------------------------------------------- #

FONT = {
    "0": ["#####", "#   #", "#   #", "#   #", "#####"],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", " ### "],
    "2": ["#####", "    #", "#####", "#    ", "#####"],
    "3": ["#####", "    #", " ####", "    #", "#####"],
    "4": ["#   #", "#   #", "#####", "    #", "    #"],
    "5": ["#####", "#    ", "#####", "    #", "#####"],
    "6": ["#####", "#    ", "#####", "#   #", "#####"],
    "7": ["#####", "    #", "   # ", "  #  ", "  #  "],
    "8": ["#####", "#   #", "#####", "#   #", "#####"],
    "9": ["#####", "#   #", "#####", "    #", "#####"],
    ":": [" ", "#", " ", "#", " "],
}
FONT_HEIGHT = 5
GLYPH_GAP = 1


def big_rows(text):
    """Return the unscaled rows (strings of '#' and ' ') for text."""
    rows = [""] * FONT_HEIGHT
    for i, ch in enumerate(text):
        glyph = FONT[ch]
        for r in range(FONT_HEIGHT):
            rows[r] += (" " * GLYPH_GAP if i else "") + glyph[r]
    return rows


# --------------------------------------------------------------------------- #
# Timer state machine
# --------------------------------------------------------------------------- #

READY, RUNNING, PAUSED, DONE = "READY", "RUNNING", "PAUSED", "DONE"

MENUS = {
    READY: ["Start", "Quit"],
    RUNNING: ["Pause", "Quit"],
    PAUSED: ["Resume", "Quit"],
    DONE: ["Restart", "Quit"],
}


class Timer:
    def __init__(self, total):
        self.total = total
        self.state = READY
        self.remaining = float(total)
        self.end_at = None
        self.selected = 0

    def _set_state(self, state):
        self.state = state
        self.selected = 0

    def now_remaining(self):
        if self.state == RUNNING:
            return max(0.0, self.end_at - time.monotonic())
        return self.remaining

    def start(self):
        self.remaining = float(self.total)
        self.end_at = time.monotonic() + self.remaining
        self._set_state(RUNNING)

    def pause(self):
        self.remaining = self.now_remaining()
        self._set_state(PAUSED)

    def resume(self):
        self.end_at = time.monotonic() + self.remaining
        self._set_state(RUNNING)

    def tick(self):
        """Advance; return True if the timer just finished."""
        if self.state == RUNNING and self.now_remaining() <= 0:
            self.remaining = 0.0
            self._set_state(DONE)
            return True
        return False

    def menu(self):
        return MENUS[self.state]

    def move(self, delta):
        self.selected = (self.selected + delta) % len(self.menu())

    def activate(self):
        """Run the selected action; return False if the app should quit."""
        item = self.menu()[self.selected]
        if item == "Quit":
            return False
        if item in ("Start", "Restart"):
            self.start()
        elif item == "Pause":
            self.pause()
        elif item == "Resume":
            self.resume()
        return True


# --------------------------------------------------------------------------- #
# Sound
# --------------------------------------------------------------------------- #

SOUND = "/System/Library/Sounds/Glass.aiff"


def beep():
    try:
        curses.beep()
    except curses.error:
        pass
    if shutil.which("afplay"):
        try:
            subprocess.Popen(
                ["afplay", SOUND],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

PAIR_PAUSED, PAIR_DONE, PAIR_DIM = 1, 2, 3


def safe_addstr(win, y, x, text, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    text = text[: max(0, w - x - (1 if y == h - 1 else 0))]
    if not text:
        return
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


def draw(stdscr, timer, colors):
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    remaining = timer.now_remaining()
    text = format_time(math.ceil(remaining))

    label = {PAUSED: "PAUSED", DONE: "Time's up!"}.get(timer.state, "")
    clock_attr = curses.A_BOLD
    if colors and timer.state == PAUSED:
        clock_attr |= curses.color_pair(PAIR_PAUSED)
    elif colors and timer.state == DONE:
        clock_attr |= curses.color_pair(PAIR_DONE)

    menu = timer.menu()
    # space below clock: blank, label, blank, menu items
    below = 3 + len(menu)

    rows = big_rows(text)
    base_w = len(rows[0])
    scale = 0
    for s in (4, 3, 2, 1):
        # horizontal scale doubled so glyphs look roughly square
        if base_w * s * 2 <= w - 4 and FONT_HEIGHT * s + below + 2 <= h:
            scale = s
            break

    if scale:
        sx, sy = scale * 2, scale
        clock_h = FONT_HEIGHT * sy
        block_h = clock_h + below
        top = max(0, (h - block_h) // 2)
        left = (w - base_w * sx) // 2
        for r, row in enumerate(rows):
            line = "".join(("█" if c == "#" else " ") * sx for c in row)
            for k in range(sy):
                safe_addstr(stdscr, top + r * sy + k, left, line, clock_attr)
        y = top + clock_h + 1
    else:
        block_h = 1 + below
        top = max(0, (h - block_h) // 2)
        safe_addstr(stdscr, top, (w - len(text)) // 2, text, clock_attr)
        y = top + 1

    if label:
        safe_addstr(stdscr, y, (w - len(label)) // 2, label, clock_attr)
    y += 2

    item_w = max(len(m) for m in menu) + 4
    for i, item in enumerate(menu):
        if i == timer.selected:
            s = f"▶ {item}".ljust(item_w)
            attr = curses.A_REVERSE | curses.A_BOLD
        else:
            s = f"  {item}".ljust(item_w)
            attr = curses.color_pair(PAIR_DIM) if colors else curses.A_NORMAL
        safe_addstr(stdscr, y + i, (w - item_w) // 2, s, attr)

    hint = "↑/↓ select · Enter confirm · q quit"
    safe_addstr(stdscr, h - 1, (w - len(hint)) // 2, hint,
                curses.color_pair(PAIR_DIM) if colors else curses.A_DIM)

    stdscr.refresh()


ESC_IGNORED = -2


def read_key(stdscr):
    """getch() that decodes raw ESC [ A/B and ESC O A/B arrow sequences.

    A lone Esc is returned as 27; any other escape sequence is swallowed.
    """
    key = stdscr.getch()
    if key != 27:
        return key
    stdscr.nodelay(True)
    try:
        seq = []
        while True:
            k = stdscr.getch()
            if k == -1:
                break
            seq.append(k)
    finally:
        stdscr.nodelay(False)
        stdscr.timeout(100)
    if not seq:
        return 27
    if len(seq) >= 2 and seq[0] in (ord("["), ord("O")):
        return {ord("A"): curses.KEY_UP, ord("B"): curses.KEY_DOWN}.get(seq[1], ESC_IGNORED)
    return ESC_IGNORED


def run(stdscr, total):
    curses.set_escdelay(25)
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.keypad(True)
    stdscr.timeout(100)

    colors = False
    if curses.has_colors():
        try:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(PAIR_PAUSED, curses.COLOR_YELLOW, -1)
            curses.init_pair(PAIR_DONE, curses.COLOR_GREEN, -1)
            curses.init_pair(PAIR_DIM, 8 if curses.COLORS > 8 else curses.COLOR_WHITE, -1)
            colors = True
        except curses.error:
            colors = False

    timer = Timer(total)
    while True:
        if timer.tick():
            beep()
        draw(stdscr, timer, colors)

        key = read_key(stdscr)
        if key == -1:
            continue
        if key == curses.KEY_RESIZE:
            stdscr.clear()
        elif key in (curses.KEY_UP, ord("k")):
            timer.move(-1)
        elif key in (curses.KEY_DOWN, ord("j")):
            timer.move(1)
        elif key in (curses.KEY_ENTER, 10, 13):
            if not timer.activate():
                return
        elif key in (ord("q"), ord("Q"), 27):
            return


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="timer",
        description="Full-screen focus countdown timer.",
        epilog="Examples: timer 25   timer 25m   timer 90s   timer 1m30s   timer 1h",
    )
    parser.add_argument(
        "duration",
        help="duration like 90s, 25m, 1m30s, 1h (a bare number means minutes)",
    )
    args = parser.parse_args(argv)
    try:
        total = parse_duration(args.duration)
    except ValueError as exc:
        parser.print_usage(sys.stderr)
        print(f"timer: error: {exc}", file=sys.stderr)
        return 2

    try:
        curses.wrapper(run, total)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
