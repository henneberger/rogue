from __future__ import annotations

from fortress.engine import Game


def repl() -> None:
    g = Game()
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
