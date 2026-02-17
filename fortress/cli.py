from __future__ import annotations

import os
import sys
try:
    import termios
    import tty
except ImportError:  # pragma: no cover
    termios = None
    tty = None

from fortress.engine import Game
from fortress.io.repl_completion import complete


def _redraw(prompt: str, buf: list[str], cursor: int) -> None:
    text = "".join(buf)
    sys.stdout.write("\r\x1b[2K" + prompt + text)
    back = len(text) - cursor
    if back > 0:
        sys.stdout.write(f"\x1b[{back}D")
    sys.stdout.flush()


def _common_prefix(values: list[str]) -> str:
    if not values:
        return ""
    prefix = values[0]
    for v in values[1:]:
        i = 0
        lim = min(len(prefix), len(v))
        while i < lim and prefix[i] == v[i]:
            i += 1
        prefix = prefix[:i]
        if not prefix:
            break
    return prefix


def _read_command(g: Game, prompt: str) -> str | None:
    # Fallback for non-TTY environments.
    if not sys.stdin.isatty() or termios is None or tty is None:
        try:
            return input(prompt)
        except EOFError:
            return None

    history = g.command_log
    hidx = len(history)
    buf: list[str] = []
    cursor = 0
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        tty.setraw(fd)
        while True:
            ch = os.read(fd, 1).decode("utf-8", errors="ignore")
            if not ch:
                return None
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buf)
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x04":
                # Ctrl-D behaves like EOF on empty buffer.
                if not buf:
                    return None
                continue

            if ch == "\x7f":  # backspace
                if cursor > 0:
                    del buf[cursor - 1]
                    cursor -= 1
                    _redraw(prompt, buf, cursor)
                continue

            if ch == "\t":  # tab completion
                line = "".join(buf)
                start = line.rfind(" ", 0, cursor) + 1
                text = line[start:cursor]
                cands = complete(g, line, text)
                if not cands:
                    continue
                if len(cands) == 1:
                    repl = cands[0]
                    buf[start:cursor] = list(repl)
                    cursor = start + len(repl)
                    if cursor == len(buf) and not repl.endswith("/"):
                        buf.insert(cursor, " ")
                        cursor += 1
                    _redraw(prompt, buf, cursor)
                else:
                    pref = _common_prefix(cands)
                    if pref and pref != text:
                        buf[start:cursor] = list(pref)
                        cursor = start + len(pref)
                        _redraw(prompt, buf, cursor)
                    sys.stdout.write("\n" + "  ".join(cands[:24]) + ("\n... more" if len(cands) > 24 else "") + "\n")
                    _redraw(prompt, buf, cursor)
                continue

            if ch == "\x1b":  # escape sequence (arrows, etc.)
                nxt = os.read(fd, 1).decode("utf-8", errors="ignore")
                if nxt != "[":
                    continue
                code = os.read(fd, 1).decode("utf-8", errors="ignore")
                if code == "A":  # up
                    if hidx > 0:
                        hidx -= 1
                        buf = list(history[hidx])
                        cursor = len(buf)
                        _redraw(prompt, buf, cursor)
                elif code == "B":  # down
                    if hidx < len(history) - 1:
                        hidx += 1
                        buf = list(history[hidx])
                    else:
                        hidx = len(history)
                        buf = []
                    cursor = len(buf)
                    _redraw(prompt, buf, cursor)
                elif code == "C":  # right
                    if cursor < len(buf):
                        cursor += 1
                        _redraw(prompt, buf, cursor)
                elif code == "D":  # left
                    if cursor > 0:
                        cursor -= 1
                        _redraw(prompt, buf, cursor)
                elif code == "3":
                    # Delete key sends ESC [ 3 ~
                    _ = os.read(fd, 1)
                    if cursor < len(buf):
                        del buf[cursor]
                        _redraw(prompt, buf, cursor)
                continue

            if ch.isprintable():
                # Immediate hotkeys on empty input.
                if not buf and cursor == 0 and ch in {".", "<", ">"}:
                    sys.stdout.write(ch + "\n")
                    sys.stdout.flush()
                    return ch
                buf.insert(cursor, ch)
                cursor += 1
                _redraw(prompt, buf, cursor)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def repl() -> None:
    g = Game()
    print("DF-like Console Colony Prototype")
    print("Type 'help' for commands.")
    print(g.render())

    while True:
        try:
            raw = _read_command(g, "\n> ")
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return

        if raw is None:
            print("bye")
            return
        raw = raw.strip()
        if not raw:
            continue

        try:
            out = g.handle_command(raw)
            if out:
                print(out)
        except SystemExit:
            print("bye")
            return
        except Exception as e:
            print(f"error: {e}")
