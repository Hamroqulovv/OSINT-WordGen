#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wordgen/ui.py — Matrix / hacker themed terminal UI for OSINT WordGen.

Everything visual lives here:
  * a green "digital rain" intro animation
  * a glitch-reveal ASCII banner (pyfiglet)
  * a fake boot sequence + typing effect
  * ACCESS GRANTED / DENIED screens
  * themed panels, rules, progress bars, tables (via `rich`)

Animations are automatically disabled when output is not a TTY (e.g. piped
into a file) or when the caller passes --no-animation, so the tool stays
scriptable.
"""
from __future__ import annotations

import random
import shutil
import sys
import time
from typing import Iterable, List, Sequence, Tuple

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# --------------------------------------------------------------------------
# Branding
# --------------------------------------------------------------------------
BIG_WORD = "WORDGEN"
VERSION = "v2.0"
AUTHOR = "@Hamroqulovv"

# --------------------------------------------------------------------------
# Green "hacker" theme
# --------------------------------------------------------------------------
THEME = Theme(
    {
        "hx.head": "#d6ffd6",          # near-white green (rain head)
        "hx.bright": "bold #39ff14",   # neon green (accents / titles)
        "hx.green": "#33e033",
        "hx.mid": "#22bb22",
        "hx.dim": "#128a12",
        "hx.dark": "#0a5a0a",
        "hx.ok": "bold #39ff14",
        "hx.warn": "bold #ffcc00",     # warnings must stay readable
        "hx.err": "bold #ff3b3b",      # errors must stand out
        "hx.prompt": "bold #39ff14",
        "hx.label": "#57d957",
        "hx.value": "bold #d6ffd6",
    }
)

console = Console(theme=THEME, highlight=False)

# Raw ANSI palette (used for the frame-based animations)
_HEAD = "\033[38;5;231m"
_BRIGHT = "\033[1;38;5;46m"
_GREEN = "\033[38;5;40m"
_MID = "\033[38;5;34m"
_DIM = "\033[38;5;28m"
_DARK = "\033[38;5;22m"
_RESET = "\033[0m"

_RAIN_STYLE = {0: _DARK, 1: _HEAD, 2: _BRIGHT, 3: _GREEN, 4: _DIM}

_ANIM = True


# --------------------------------------------------------------------------
# Low-level helpers
# --------------------------------------------------------------------------
def set_animations(enabled: bool) -> None:
    """Enable/disable frame animations globally (CLI --no-animation)."""
    global _ANIM
    _ANIM = bool(enabled)


def _is_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def animations_on() -> bool:
    return _ANIM and _is_tty()


def _raw(s: str) -> None:
    sys.stdout.write(s)
    sys.stdout.flush()


def _term_size() -> Tuple[int, int]:
    size = shutil.get_terminal_size(fallback=(80, 24))
    return max(size.columns, 20), max(size.lines, 10)


def _hide_cursor() -> None:
    _raw("\033[?25l")


def _show_cursor() -> None:
    _raw("\033[?25h")


def clear() -> None:
    _raw("\033[2J\033[3J\033[H")


# --------------------------------------------------------------------------
# Digital rain intro
# --------------------------------------------------------------------------
_RAIN_CHARS = "01" + "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆ" + "日ﾊﾋﾌﾍﾎ" + "<>/\\|=+*#%&$@?abcdef0123456789"


def matrix_rain(duration: float = 1.6, fps: int = 22) -> None:
    """Classic falling-green-code intro. Safe on small/large terminals."""
    if not animations_on():
        return
    cols, rows = _term_size()
    rows = min(rows - 1, 24)
    cols = min(cols, 140)
    trail = 7
    drops = [random.randint(-rows, 0) for _ in range(cols)]
    speeds = [random.choice([1, 1, 1, 2]) for _ in range(cols)]
    frame_delay = 1.0 / max(fps, 1)

    _hide_cursor()
    _raw("\033[2J")
    end = time.time() + duration
    try:
        while time.time() < end:
            grid = [[" "] * cols for _ in range(rows)]
            styl = [[0] * cols for _ in range(rows)]
            for c in range(cols):
                head = drops[c]
                for t in range(trail):
                    y = head - t
                    if 0 <= y < rows:
                        grid[y][c] = random.choice(_RAIN_CHARS)
                        if t == 0:
                            styl[y][c] = 1
                        elif t == 1:
                            styl[y][c] = 2
                        elif t < trail // 2:
                            styl[y][c] = 3
                        else:
                            styl[y][c] = 4
                drops[c] += speeds[c]
                if drops[c] - trail > rows:
                    drops[c] = random.randint(-rows // 2, 0)
            out: List[str] = ["\033[H"]
            for y in range(rows):
                cur = -1
                row_buf: List[str] = []
                for c in range(cols):
                    s = styl[y][c]
                    if s != cur:
                        row_buf.append(_RAIN_STYLE[s])
                        cur = s
                    row_buf.append(grid[y][c])
                out.append("".join(row_buf) + _RESET)
                if y < rows - 1:
                    out.append("\n")
            _raw("".join(out))
            time.sleep(frame_delay)
    except KeyboardInterrupt:
        pass
    finally:
        _raw(_RESET)
        clear()
        _show_cursor()


# --------------------------------------------------------------------------
# ASCII banner with glitch reveal
# --------------------------------------------------------------------------
_FONTS = ["ansi_shadow", "slant", "standard", "small", "digital"]


def _figlet(text: str) -> str:
    from pyfiglet import Figlet

    cols, _ = _term_size()
    fallback = None
    for name in _FONTS:
        try:
            art = Figlet(font=name, width=max(cols, 40)).renderText(text)
        except Exception:
            continue
        width = max((len(line) for line in art.splitlines()), default=0)
        if fallback is None:
            fallback = art.rstrip("\n")
        if width <= cols - 1:
            return art.rstrip("\n")
    return fallback if fallback is not None else text


_GLITCH_CHARS = "01#%&$@*<>/\\|=+ﾊﾋﾌ▓▒░"


def _glitch_reveal(art: str, frames: int = 7, delay: float = 0.055) -> None:
    lines = art.split("\n")
    height = len(lines)
    for f in range(frames):
        frac = 1.0 - (f + 1) / frames
        buf: List[str] = []
        for line in lines:
            chars = []
            for ch in line:
                if ch != " " and random.random() < frac:
                    chars.append(random.choice(_GLITCH_CHARS))
                else:
                    chars.append(ch)
            buf.append("".join(chars))
        _raw(_BRIGHT + "\n".join(buf) + _RESET + "\n")
        time.sleep(delay)
        if f < frames - 1:
            _raw(f"\033[{height}A")


def show_banner() -> None:
    art = _figlet(BIG_WORD)
    if animations_on():
        _glitch_reveal(art)
    else:
        console.print(Text(art, style="hx.bright"))
    console.print(f"  H A M R O Q U L O V   ·   OSINT WordGen  {VERSION}", style="hx.green")
    console.print("  Smart OSINT-based password wordlist generator", style="hx.mid")
    console.print(f"  Authorized security testing only  ·  by {AUTHOR}", style="hx.dim")
    console.print()


# --------------------------------------------------------------------------
# Typing effect + fake boot sequence
# --------------------------------------------------------------------------
def type_line(text: str, style: str = "hx.green", delay: float = 0.010) -> None:
    """Print a line with a typewriter effect (falls back to instant print)."""
    if not animations_on():
        console.print(text, style=style)
        return
    for ch in text:
        console.print(ch, style=style, end="")
        time.sleep(delay)
    console.print()


def boot_sequence(steps: Sequence[str]) -> None:
    for step in steps:
        if animations_on():
            _raw(f"{_DIM}  [*] {_RESET}{_GREEN}{step}{_RESET}")
            time.sleep(0.14)
            _raw(f"{_BRIGHT}   [ OK ]{_RESET}\n")
            time.sleep(0.05)
        else:
            console.print(f"  [*] {step}   [ OK ]", style="hx.mid")
    console.print()


# --------------------------------------------------------------------------
# Section rules / panels
# --------------------------------------------------------------------------
def section(title: str) -> None:
    console.print()
    console.rule(f"[hx.bright]▎ {title}", style="hx.dark", align="left")


def info_panel(body: str, title: str = "", style: str = "hx.mid") -> None:
    console.print(
        Panel(body, title=title, title_align="left", border_style="hx.dim",
              style=style, box=box.ROUNDED, padding=(0, 2))
    )


def disclaimer(text: str) -> None:
    console.print(
        Panel(
            Text(text, style="hx.warn"),
            title="[hx.warn]⚠  LEGAL NOTICE",
            title_align="left",
            border_style="hx.warn",
            box=box.HEAVY,
            padding=(1, 2),
        )
    )


# --------------------------------------------------------------------------
# Authorization screens
# --------------------------------------------------------------------------
def access_granted() -> None:
    if animations_on():
        _raw(f"{_DIM}  >> validating authorization")
        for _ in range(6):
            _raw(f"{_GREEN}.{_RESET}")
            time.sleep(0.09)
        _raw("\n")
    console.print(
        Panel(
            Align.center("[hx.ok]✓   A C C E S S   G R A N T E D   ✓"),
            border_style="hx.ok",
            box=box.DOUBLE,
            padding=(0, 6),
        )
    )
    console.print()


def access_denied() -> None:
    console.print(
        Panel(
            Align.center("[hx.err]✗   A C C E S S   D E N I E D   ✗"),
            border_style="hx.err",
            box=box.DOUBLE,
            padding=(0, 6),
        )
    )


# --------------------------------------------------------------------------
# Prompts
# --------------------------------------------------------------------------
def ask(label: str) -> str:
    try:
        return console.input(f"[hx.prompt]  {label}[/] ")
    except EOFError:
        return ""


# --------------------------------------------------------------------------
# Progress bar
# --------------------------------------------------------------------------
def make_progress() -> Progress:
    return Progress(
        SpinnerColumn(spinner_name="line", style="hx.bright"),
        TextColumn("[hx.mid]{task.description}"),
        BarColumn(
            bar_width=None,
            style="hx.dark",
            complete_style="hx.bright",
            finished_style="hx.ok",
            pulse_style="hx.green",
        ),
        MofNCompleteColumn(),
        TextColumn("[hx.dim]{task.fields[rate]}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )


# --------------------------------------------------------------------------
# Target profile + summary + samples
# --------------------------------------------------------------------------
def target_profile(fields: Sequence[Tuple[str, str]]) -> None:
    if not fields:
        return
    table = Table(box=box.SIMPLE, show_header=False, expand=False, pad_edge=False)
    table.add_column(style="hx.label", justify="right", no_wrap=True)
    table.add_column(style="hx.value")
    for name, value in fields:
        table.add_row(f"{name}", value)
    console.print(
        Panel(table, title="[hx.bright]▸ TARGET PROFILE", title_align="left",
              border_style="hx.dim", box=box.ROUNDED, padding=(0, 1))
    )


def summary(rows: Sequence[Tuple[str, str]]) -> None:
    table = Table(box=box.SIMPLE, show_header=False, expand=False, pad_edge=False)
    table.add_column(style="hx.label", justify="right", no_wrap=True)
    table.add_column(style="hx.value")
    for name, value in rows:
        table.add_row(f"{name}", value)
    console.print(
        Panel(table, title="[hx.ok]✔ GENERATION COMPLETE", title_align="left",
              border_style="hx.ok", box=box.DOUBLE, padding=(0, 1))
    )


def _strength_bar(score: int) -> Text:
    filled = "█" * score + "░" * (5 - score)
    style = {0: "hx.err", 1: "hx.err", 2: "hx.warn", 3: "hx.green", 4: "hx.ok", 5: "hx.ok"}[score]
    return Text(filled, style=style)


def sample_table(samples: Sequence[Tuple[str, int, str]]) -> None:
    """samples = list of (password, score0-5, label)."""
    if not samples:
        return
    table = Table(
        title="[hx.bright]▸ SAMPLE CANDIDATES",
        title_justify="left",
        box=box.MINIMAL_DOUBLE_HEAD,
        border_style="hx.dim",
        header_style="hx.mid",
        expand=False,
    )
    table.add_column("#", style="hx.dim", justify="right", no_wrap=True)
    table.add_column("candidate", style="hx.value")
    table.add_column("len", style="hx.mid", justify="right")
    table.add_column("strength", justify="left")
    table.add_column("", style="hx.label")
    for i, (pw, score, label) in enumerate(samples, 1):
        table.add_row(str(i), pw, str(len(pw)), _strength_bar(score), label)
    console.print(table)


def rule_char_note() -> None:
    console.print()


# --------------------------------------------------------------------------
# Message helpers
# --------------------------------------------------------------------------
def ok(msg: str) -> None:
    console.print(f"  [hx.ok]✓[/] {msg}", style="hx.green")


def warn(msg: str) -> None:
    console.print(f"  [hx.warn]![/] {msg}", style="hx.warn")


def err(msg: str) -> None:
    console.print(f"  [hx.err]✗[/] {msg}", style="hx.err")


def info(msg: str) -> None:
    console.print(f"  [hx.dim]›[/] {msg}", style="hx.mid")
