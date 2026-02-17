import os
import tempfile
import unittest

from fortress.engine import Game


def run_job_until_idle(game: Game, dwarf_id: int, max_steps: int = 40) -> None:
    dwarf = game._find_dwarf(dwarf_id)
    assert dwarf is not None
    for _ in range(max_steps):
        if dwarf.job is None:
            return
        game._perform_job_step(dwarf)
    raise AssertionError("job did not complete")


class ContainerStorageIssue33Tests(unittest.TestCase):
    def test_container_recipes_exist(self) -> None:
        g = Game(rng_seed=301)
        carpenter = g.defs["recipes"]["carpenter"]
        loom = g.defs["recipes"]["loom"]
        self.assertTrue({"chest", "barrel", "bin", "crate"}.issubset(set(carpenter.keys())))
        self.assertIn("bag", loom)

    def test_seed_hauling_uses_bag_in_raw_stockpile(self) -> None:
        g = Game(rng_seed=302)
        g.items = []
        sp = g.add_stockpile("raw", 5, 5, 0, 1, 1)
        bag = g._spawn_item("bag", 5, 5, 0, material="cloth", value=3)
        bag.stockpile_id = sp.id
        seed = g._spawn_item("seed", 1, 1, 0, material="plump-helmet-spawn", value=1)

        item, stock, container = g._find_haul_candidate()
        self.assertEqual(item.id if item else None, seed.id)
        self.assertEqual(stock.id if stock else None, sp.id)
        self.assertEqual(container.id if container else None, bag.id)

        d = g.dwarves[0]
        seed.reserved_by = d.id
        bag.reserved_by = d.id
        d.job = g._new_job(
            kind="haul",
            labor="haul",
            item_id=seed.id,
            target_id=sp.id,
            container_id=bag.id,
            destination=(seed.x, seed.y, seed.z),
            phase="to_item",
        )
        run_job_until_idle(g, d.id)

        self.assertEqual(seed.stockpile_id, sp.id)
        self.assertEqual(seed.container_id, bag.id)

    def test_alcohol_hauling_uses_barrel_in_drink_stockpile(self) -> None:
        g = Game(rng_seed=303)
        g.items = []
        sp = g.add_stockpile("drink", 6, 5, 0, 1, 1)
        barrel = g._spawn_item("barrel", 6, 5, 0, material="oak", value=3)
        barrel.stockpile_id = sp.id
        booze = g._spawn_item("alcohol", 1, 1, 0, material="ale", value=2, perishability=150)

        item, stock, container = g._find_haul_candidate()
        self.assertEqual(item.id if item else None, booze.id)
        self.assertEqual(stock.id if stock else None, sp.id)
        self.assertEqual(container.id if container else None, barrel.id)

    def test_container_items_route_to_policy_stockpiles(self) -> None:
        g = Game(rng_seed=304)
        g.items = []
        raw_sp = g.add_stockpile("raw", 4, 4, 0, 2, 2)
        furn_sp = g.add_stockpile("furniture", 10, 4, 0, 2, 2)
        chest = g._spawn_item("chest", 1, 1, 0, material="oak", value=4)
        barrel = g._spawn_item("barrel", 2, 1, 0, material="oak", value=3)

        i1, s1, c1 = g._find_haul_candidate()
        self.assertEqual(i1.id if i1 else None, chest.id)
        self.assertEqual(s1.id if s1 else None, furn_sp.id)
        self.assertIsNone(c1)

        chest.reserved_by = 999
        i2, s2, c2 = g._find_haul_candidate()
        self.assertEqual(i2.id if i2 else None, barrel.id)
        self.assertEqual(s2.id if s2 else None, raw_sp.id)
        self.assertIsNone(c2)

    def test_save_load_preserves_container_links(self) -> None:
        g = Game(rng_seed=305)
        g.items = []
        sp = g.add_stockpile("raw", 5, 5, 0, 1, 1)
        bag = g._spawn_item("bag", 5, 5, 0, material="cloth", value=3)
        bag.stockpile_id = sp.id
        seed = g._spawn_item("seed", 5, 5, 0, material="spawn", value=1)
        seed.stockpile_id = sp.id
        seed.container_id = bag.id

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
            path = tf.name
        try:
            g.save_json(path)
            loaded = Game.load_json(path)
            loaded_seed = next(i for i in loaded.items if i.kind == "seed")
            loaded_bag = next(i for i in loaded.items if i.kind == "bag")
            self.assertEqual(loaded_seed.container_id, loaded_bag.id)
            self.assertEqual(loaded_seed.stockpile_id, loaded_bag.stockpile_id)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
