from __future__ import annotations

import os
import re
import select
import signal
import sys
try:
    import termios
    import tty
except ImportError:  # pragma: no cover
    termios = None
    tty = None

from fortress.engine import Game


_CSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _redraw(prompt: str, buf: list[str], cursor: int) -> None:
    text = "".join(buf)
    sys.stdout.write("\r\x1b[2K" + prompt + text)
    back = len(text) - cursor
    if back > 0:
        sys.stdout.write(f"\x1b[{back}D")
    sys.stdout.flush()


def _drain_ready_input(fd: int) -> str:
    chunks: list[str] = []
    while True:
        ready, _, _ = select.select([fd], [], [], 0)
        if not ready:
            break
        chunk = os.read(fd, 4096).decode("utf-8", errors="ignore")
        if not chunk:
            break
        chunks.append(chunk)
    return "".join(chunks)


def _enqueue_pasted_lines(g: Game, raw_text: str) -> None:
    if not raw_text:
        return
    # Strip CSI controls (e.g., bracketed paste wrappers) and normalize line endings.
    cleaned = _CSI_RE.sub("", raw_text).replace("\r\n", "\n").replace("\r", "\n")
    parts = cleaned.split("\n")
    existing = getattr(g, "_repl_pending_lines", [])
    existing.extend(parts[:-1])
    setattr(g, "_repl_pending_lines", existing)
    setattr(g, "_repl_prefill", parts[-1])


def _read_command(g: Game, prompt: str) -> str | None:
    pending = getattr(g, "_repl_pending_lines", [])
    if pending:
        line = pending.pop(0)
        setattr(g, "_repl_pending_lines", pending)
        return line

    # Fallback for non-TTY environments.
    if not sys.stdin.isatty() or termios is None or tty is None:
        try:
            return input(prompt)
        except EOFError:
            return None

    history = g.command_log
    hidx = len(history)
    prefill = getattr(g, "_repl_prefill", "")
    setattr(g, "_repl_prefill", "")
    buf: list[str] = list(prefill)
    cursor = len(buf)
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    if prefill:
        _redraw(prompt, buf, cursor)
    else:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    try:
        tty.setraw(fd)
        while True:
            ch = os.read(fd, 1).decode("utf-8", errors="ignore")
            if not ch:
                return None
            if ch in ("\r", "\n"):
                line = "".join(buf)
                _enqueue_pasted_lines(g, _drain_ready_input(fd))
                sys.stdout.write("\n")
                sys.stdout.flush()
                return line
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

            if ch == "\x1b":  # escape sequence (arrows, bracketed paste controls, etc.)
                nxt = os.read(fd, 1).decode("utf-8", errors="ignore")
                if nxt != "[":
                    continue
                seq = ""
                while True:
                    b = os.read(fd, 1).decode("utf-8", errors="ignore")
                    if not b:
                        break
                    seq += b
                    if 0x40 <= ord(b) <= 0x7E:
                        break
                if seq == "A":  # up
                    if hidx > 0:
                        hidx -= 1
                        buf = list(history[hidx])
                        cursor = len(buf)
                        _redraw(prompt, buf, cursor)
                elif seq == "B":  # down
                    if hidx < len(history) - 1:
                        hidx += 1
                        buf = list(history[hidx])
                    else:
                        hidx = len(history)
                        buf = []
                    cursor = len(buf)
                    _redraw(prompt, buf, cursor)
                elif seq == "C":  # right
                    if cursor < len(buf):
                        cursor += 1
                        _redraw(prompt, buf, cursor)
                elif seq == "D":  # left
                    if cursor > 0:
                        cursor -= 1
                        _redraw(prompt, buf, cursor)
                elif seq == "3~":
                    # Delete key sends ESC [ 3 ~.
                    if cursor < len(buf):
                        del buf[cursor]
                        _redraw(prompt, buf, cursor)
                continue

            if ch.isprintable():
                buf.insert(cursor, ch)
                cursor += 1
                _redraw(prompt, buf, cursor)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def repl() -> None:
    g = Game()
    sigint_state = {
        "pending_exit": False,
        "running": False,
        "show_idle_hint": False,
        "show_interrupt_hint": False,
        "exit_requested": False,
    }

    previous_sigint = signal.getsignal(signal.SIGINT)

    def _handle_sigint(_signum: int, _frame) -> None:
        if sigint_state["pending_exit"]:
            sigint_state["exit_requested"] = True
            if sigint_state["running"]:
                g.interrupt_requested = True
            return
        sigint_state["pending_exit"] = True
        if sigint_state["running"]:
            g.interrupt_requested = True
            sigint_state["show_interrupt_hint"] = True
        else:
            sigint_state["show_idle_hint"] = True

    signal.signal(signal.SIGINT, _handle_sigint)

    print("DF-like Console Colony Prototype")
    print("Type 'help' for commands.")
    print(g.render())

    try:
        while True:
            if sigint_state["exit_requested"]:
                print("\nbye")
                return
            if sigint_state["show_interrupt_hint"]:
                print("\ninterrupt requested (press Ctrl-C again to exit)")
                sigint_state["show_interrupt_hint"] = False
            if sigint_state["show_idle_hint"]:
                print("\npress Ctrl-C again to exit")
                sigint_state["show_idle_hint"] = False

            try:
                print()
                raw = _read_command(g, "> ")
            except (EOFError, KeyboardInterrupt):
                if sigint_state["pending_exit"]:
                    print("\nbye")
                    return
                sigint_state["pending_exit"] = True
                print("\npress Ctrl-C again to exit")
                continue

            if raw is None:
                print("bye")
                return
            raw = raw.strip()
            if not raw:
                continue

            sigint_state["pending_exit"] = False
            sigint_state["running"] = True
            try:
                out = g.handle_command(raw)
                if out:
                    print(out)
            except SystemExit:
                print("bye")
                return
            except KeyboardInterrupt:
                # Fallback if platform/runtime still raises KeyboardInterrupt while running.
                if sigint_state["pending_exit"]:
                    print("\nbye")
                    return
                sigint_state["pending_exit"] = True
                g.interrupt_requested = True
                print("\ninterrupt requested (press Ctrl-C again to exit)")
            except Exception as e:
                print(f"error: {e}")
            finally:
                sigint_state["running"] = False
    finally:
        signal.signal(signal.SIGINT, previous_sigint)
