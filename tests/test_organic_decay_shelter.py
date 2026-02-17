import unittest

from fortress.engine import Game


class OrganicDecayShelterTests(unittest.TestCase):
    def test_outdoor_organic_item_decays(self) -> None:
        g = Game(rng_seed=210)
        item = g._spawn_item("raw_food", 6, 6, 0, material="wild-herb", perishability=100, value=1)
        item.age = 120
        g.rng.random = lambda: 0.0
        g._item_tick()
        self.assertIsNone(g._find_item_by_id(item.id))

    def test_room_covered_organic_item_does_not_decay(self) -> None:
        g = Game(rng_seed=211)
        g.add_zone("recreation", 5, 5, 0, 3, 3)
        g._refresh_rooms_and_assignments()
        item = g._spawn_item("raw_food", 6, 6, 0, material="wild-herb", perishability=100, value=1)
        item.age = 120
        g.rng.random = lambda: 0.0
        g._item_tick()
        self.assertIsNotNone(g._find_item_by_id(item.id))

    def test_underground_organic_item_does_not_decay(self) -> None:
        g = Game(rng_seed=212, depth=3)
        item = g._spawn_item("raw_food", 6, 6, 1, material="plump-helmet", perishability=100, value=1)
        item.age = 120
        g.rng.random = lambda: 0.0
        g._item_tick()
        self.assertIsNotNone(g._find_item_by_id(item.id))

    def test_contained_organic_item_does_not_decay(self) -> None:
        g = Game(rng_seed=213)
        barrel = g._spawn_item("barrel", 6, 6, 0, material="oak", value=2)
        item = g._spawn_item("raw_food", 6, 6, 0, material="wild-berry", perishability=100, value=1)
        item.container_id = barrel.id
        item.age = 999
        g.rng.random = lambda: 0.0
        g._item_tick()
        self.assertIsNotNone(g._find_item_by_id(item.id))


if __name__ == "__main__":
    unittest.main()
