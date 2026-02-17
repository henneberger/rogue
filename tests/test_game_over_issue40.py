import unittest

from fortress.engine import Game


class GameOverIssue40Tests(unittest.TestCase):
    def test_tick_command_shows_game_over_summary(self) -> None:
        g = Game(rng_seed=201)
        for dwarf in g.dwarves:
            dwarf.hp = 0

        out = g.handle_command("tick 5")

        self.assertTrue(g.game_over)
        self.assertEqual(g.tick_count, 0)
        self.assertIn("GAME OVER: No dwarves remain.", out)
        self.assertIn("Event Summary:", out)
        self.assertIn("dwarves_alive=0/", out)
        self.assertEqual(sum(1 for e in g.events if e.kind == "game_over"), 1)

    def test_game_over_triggers_once_and_stops_future_ticks(self) -> None:
        g = Game(rng_seed=202)
        for dwarf in g.dwarves[:-1]:
            dwarf.hp = 0
        survivor = g.dwarves[-1]

        def kill_survivor() -> None:
            if survivor.hp > 0:
                survivor.hp = 0
                g._log("death", f"{survivor.name} has died.", 3)

        g._update_needs_moods_stress = kill_survivor

        g.tick(3)
        self.assertEqual(g.tick_count, 1)
        self.assertTrue(g.game_over)
        self.assertEqual(sum(1 for e in g.events if e.kind == "game_over"), 1)

        g.tick(10)
        self.assertEqual(g.tick_count, 1)
        self.assertEqual(sum(1 for e in g.events if e.kind == "game_over"), 1)


if __name__ == "__main__":
    unittest.main()
