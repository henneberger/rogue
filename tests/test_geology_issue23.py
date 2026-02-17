import os
import tempfile
import unittest

from fortress.engine import Game


class GeologyIssue23Tests(unittest.TestCase):
    def test_geology_generation_is_seed_deterministic(self) -> None:
        g1 = Game(rng_seed=923)
        g2 = Game(rng_seed=923)
        sig1 = sorted((d.x, d.y, d.z, d.kind, d.material, d.rarity, d.total_yield) for d in g1.geology_deposits)
        sig2 = sorted((d.x, d.y, d.z, d.kind, d.material, d.rarity, d.total_yield) for d in g2.geology_deposits)
        self.assertEqual(sig1, sig2)
        self.assertEqual(sorted(g1.geology_cavern_tiles), sorted(g2.geology_cavern_tiles))
        self.assertGreater(len(g1.geology_cavern_tiles), 0)

    def test_mining_extracts_and_depletes_deposit(self) -> None:
        g = Game(rng_seed=924)
        dep = next((d for d in g.geology_deposits if d.kind == "ore"), None)
        self.assertIsNotNone(dep)
        assert dep is not None
        total = dep.total_yield
        for _ in range(total):
            g._resolve_geology_mining(dep.x, dep.y, dep.z)
        self.assertEqual(dep.remaining_yield, 0)
        ore_items = [i for i in g.items if i.kind == "ore" and i.material == dep.material]
        self.assertEqual(len(ore_items), total)
        # After depletion, generic stone should be produced instead.
        g._resolve_geology_mining(dep.x, dep.y, dep.z)
        stone_items = [i for i in g.items if i.kind == "stone"]
        self.assertGreaterEqual(len(stone_items), 1)

    def test_cavern_breach_event_fires_once(self) -> None:
        g = Game(rng_seed=925)
        tile = next(iter(g.geology_cavern_tiles))
        x, y, z = tile
        g._resolve_geology_mining(x, y, z)
        first = g.economy_stats.get("caverns_breached", 0)
        g._resolve_geology_mining(x, y, z)
        second = g.economy_stats.get("caverns_breached", 0)
        self.assertEqual(first, 1)
        self.assertEqual(second, 1)
        self.assertIn(tile, g.geology_breached_tiles)

    def test_geology_persists_save_load(self) -> None:
        g = Game(rng_seed=926)
        dep = g.geology_deposits[0]
        g._resolve_geology_mining(dep.x, dep.y, dep.z)
        cav = next(iter(g.geology_cavern_tiles))
        g._resolve_geology_mining(cav[0], cav[1], cav[2])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
            path = tf.name
        try:
            g.save_json(path)
            loaded = Game.load_json(path)
            self.assertEqual(loaded.geology_strata, g.geology_strata)
            self.assertEqual(len(loaded.geology_deposits), len(g.geology_deposits))
            self.assertEqual(loaded.economy_stats.get("caverns_breached", 0), g.economy_stats.get("caverns_breached", 0))
            self.assertEqual(sorted(loaded.geology_breached_tiles), sorted(g.geology_breached_tiles))
        finally:
            os.unlink(path)

    def test_geology_panel_and_prospect(self) -> None:
        g = Game(rng_seed=927)
        panel = g.panel("geology")
        self.assertIn("deposits_total=", panel)
        dep = g.geology_deposits[0]
        out = g.prospect(dep.x, dep.y, dep.z)
        self.assertIn("traces", out)


if __name__ == "__main__":
    unittest.main()
