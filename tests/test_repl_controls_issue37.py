import unittest

from fortress.engine import Game
from fortress.io.repl_completion import complete


class ReplControlsIssue37Tests(unittest.TestCase):
    def test_shortcut_dot_ticks_one_step(self) -> None:
        g = Game(rng_seed=111)
        start_tick = g.tick_count
        out = g.handle_command(".")
        self.assertEqual(g.tick_count, start_tick + 1)
        self.assertIn("Tick", out)

    def test_shortcut_angle_brackets_change_z(self) -> None:
        g = Game(rng_seed=112, depth=3)
        g.selected_z = 1
        g.handle_command(">")
        self.assertEqual(g.selected_z, 2)
        g.handle_command(">")
        self.assertEqual(g.selected_z, 2)  # bounded
        g.handle_command("<")
        self.assertEqual(g.selected_z, 1)
        g.handle_command("<")
        g.handle_command("<")
        self.assertEqual(g.selected_z, 0)  # bounded

    def test_completion_suggests_panel_names(self) -> None:
        g = Game(rng_seed=113)
        cands = complete(g, "panel ", "")
        self.assertIn("geology", cands)
        self.assertIn("jobs", cands)
        self.assertIn("stocks", cands)

    def test_completion_order_recipe_is_argument_aware(self) -> None:
        g = Game(rng_seed=114)
        ws = g.queue_build_workshop("carpenter", 4, 4, 0)
        ws.built = True
        cands_ids = complete(g, "order ", "")
        self.assertIn(str(ws.id), cands_ids)
        cands_recipe = complete(g, f"order {ws.id} ", "")
        self.assertIn("bed", cands_recipe)
        self.assertIn("barrel", cands_recipe)
        self.assertNotIn("meal", cands_recipe)

    def test_completion_build_workshop_and_stockpile(self) -> None:
        g = Game(rng_seed=115)
        ws_kinds = complete(g, "build workshop ", "")
        self.assertIn("kitchen", ws_kinds)
        self.assertIn("doctor", ws_kinds)
        pile_kinds = complete(g, "stockpile ", "")
        self.assertIn("food", pile_kinds)
        self.assertIn("materials", pile_kinds)


if __name__ == "__main__":
    unittest.main()
