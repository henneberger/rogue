import unittest

from fortress.engine import Game


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

    def test_z_command_rerenders_new_level(self) -> None:
        g = Game(rng_seed=116, depth=3)
        out = g.handle_command("z 2")
        self.assertEqual(g.selected_z, 2)
        self.assertIn(" | z=2 | ", out)

    def test_tick_interrupt_flag_stops_after_current_iteration(self) -> None:
        g = Game(rng_seed=113)
        steps = {"count": 0}
        orig_update = g._update_world_time_weather

        def interrupt_after_one_step() -> None:
            orig_update()
            steps["count"] += 1
            if steps["count"] == 1:
                g.interrupt_requested = True

        g._update_world_time_weather = interrupt_after_one_step
        g.tick(1000)
        self.assertEqual(g.tick_count, 1)
        self.assertFalse(g.interrupt_requested)


if __name__ == "__main__":
    unittest.main()
