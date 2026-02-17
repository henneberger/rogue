import unittest

from fortress.engine import Game


class BalancePassTests(unittest.TestCase):
    def test_supported_colony_stays_stable(self) -> None:
        g = Game(rng_seed=71)
        g.add_zone("farm", 1, 8, 0, 6, 3)
        g.add_zone("recreation", 20, 1, 0, 5, 3)
        g.add_zone("temple", 20, 5, 0, 4, 3)
        g.add_zone("dormitory", 12, 10, 0, 6, 3)
        g.add_zone("hospital", 1, 1, 0, 4, 2)
        g.add_stockpile("raw", 8, 8, 0, 4, 3)
        g.add_stockpile("cooked", 13, 8, 0, 4, 3)
        g.add_stockpile("drink", 18, 8, 0, 4, 3)
        g.add_stockpile("materials", 1, 12, 0, 8, 3)
        g.queue_build_workshop("kitchen", 11, 7, 0)
        g.queue_build_workshop("brewery", 16, 7, 0)
        g.tick(30)
        for ws in g.workshops:
            if ws.built and ws.kind == "kitchen":
                g.order_workshop(ws.id, "meal", 14)
            if ws.built and ws.kind == "brewery":
                g.order_workshop(ws.id, "brew", 12)
        g.tick(500)

        self.assertEqual(sum(1 for d in g.dwarves if d.hp > 0), len(g.dwarves))
        self.assertLessEqual(sum(d.stress for d in g.dwarves) / len(g.dwarves), 35)

    def test_disabled_food_chain_collapses(self) -> None:
        g = Game(rng_seed=97)
        g.items = [i for i in g.items if i.kind not in {"raw_food", "cooked_food", "alcohol"}]
        g.floras = []
        for d in g.dwarves:
            for labor in ("harvest", "cook", "brew"):
                d.allowed_labors.discard(labor)
        g.tick(600)

        self.assertEqual(sum(1 for d in g.dwarves if d.hp > 0), 0)
        self.assertTrue(all(d.mood == "tantrum" for d in g.dwarves))


if __name__ == "__main__":
    unittest.main()
