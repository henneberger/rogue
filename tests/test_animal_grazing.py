import unittest

from fortress.engine import Game


class AnimalGrazingTests(unittest.TestCase):
    def test_surface_animals_do_not_starve_outside_pasture(self) -> None:
        g = Game(rng_seed=501)
        g.animals = []
        goat = g.add_animal("goat", 10, 10, 0)
        goat.hunger = 90
        g.rng.random = lambda: 1.0  # no movement, no extra graze bonus
        for _ in range(200):
            g._animal_tick()
        self.assertLess(goat.hunger, 95)
        self.assertEqual(len([a for a in g.animals if a.species == "goat"]), 1)

    def test_underground_animals_can_still_starve_without_pasture(self) -> None:
        g = Game(rng_seed=502, depth=3)
        g.animals = []
        goat = g.add_animal("goat", 10, 10, 1)
        goat.hunger = 94
        g.rng.random = lambda: 1.0
        g._animal_tick()
        self.assertEqual(goat.hunger, 40)
        self.assertTrue(any("died of neglect" in e.text for e in g.events if e.kind == "animal"))


if __name__ == "__main__":
    unittest.main()
