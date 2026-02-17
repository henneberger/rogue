from __future__ import annotations

try:
    import readline
except ImportError:  # pragma: no cover
    readline = None

from fortress.engine import Game
from fortress.io.repl_completion import complete


def _install_readline(g: Game) -> None:
    if readline is None:
        return
    readline.set_history_length(1000)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \t\n")

    def _completer(text: str, state: int):
        line = readline.get_line_buffer()
        options = complete(g, line, text)
        if state < len(options):
            return options[state]
        return None

    readline.set_completer(_completer)


def repl() -> None:
    g = Game()
    _install_readline(g)
    print("DF-like Console Colony Prototype")
    print("Type 'help' for commands.")
    print(g.render())

    while True:
        try:
            raw = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return

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
