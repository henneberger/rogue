import unittest

from fortress.cli import _enqueue_pasted_lines, _read_command
from fortress.engine import Game


class CliPasteQueueTests(unittest.TestCase):
    def test_enqueue_multiline_paste_sets_pending_lines(self) -> None:
        g = Game(rng_seed=201)
        _enqueue_pasted_lines(g, "zone farm 1 8 0 6 3\nstatus\n")
        self.assertEqual(getattr(g, "_repl_pending_lines"), ["zone farm 1 8 0 6 3", "status"])
        self.assertEqual(getattr(g, "_repl_prefill"), "")

    def test_enqueue_partial_last_line_prefills_next_prompt(self) -> None:
        g = Game(rng_seed=202)
        _enqueue_pasted_lines(g, "zone farm 1 8 0 6 3\nstatus")
        self.assertEqual(getattr(g, "_repl_pending_lines"), ["zone farm 1 8 0 6 3"])
        self.assertEqual(getattr(g, "_repl_prefill"), "status")

    def test_read_command_consumes_pending_before_reading_tty(self) -> None:
        g = Game(rng_seed=203)
        setattr(g, "_repl_pending_lines", ["tick 1", "status"])
        self.assertEqual(_read_command(g, "> "), "tick 1")
        self.assertEqual(_read_command(g, "> "), "status")
        self.assertEqual(getattr(g, "_repl_pending_lines"), [])


if __name__ == "__main__":
    unittest.main()
