import unittest

from fortress.engine import Game
from fortress.models import Mandate


def run_job_until_idle(game: Game, dwarf_id: int, max_steps: int = 20) -> None:
    dwarf = game._find_dwarf(dwarf_id)
    assert dwarf is not None
    for _ in range(max_steps):
        if dwarf.job is None:
            return
        game._perform_job_step(dwarf)
    raise AssertionError("job did not complete")


class EconomyIssue29Tests(unittest.TestCase):
    def test_forage_job_produces_multiple_resource_types(self) -> None:
        g = Game(rng_seed=101)
        g.items = []
        g.floras = []
        d = g.dwarves[0]
        flora = g._spawn_flora("allium_canadense", d.x, d.y, d.z, stage="flowering")
        self.assertIsNotNone(flora)
        assert flora is not None
        flora.reserved_by = d.id
        d.job = g._new_job(
            kind="gather_flora",
            labor="harvest",
            target_id=flora.id,
            destination=(flora.x, flora.y, flora.z),
            phase="to_flora",
            remaining=2,
        )

        run_job_until_idle(g, d.id)

        produced = {i.kind for i in g.items}
        self.assertIn("herb", produced)
        self.assertIn("berry", produced)
        self.assertGreater(g.economy_stats.get("foraged_herb", 0), 0)
        self.assertGreater(g.economy_stats.get("foraged_berry", 0), 0)

    def test_tree_stage_controls_chop_and_timber(self) -> None:
        g = Game(rng_seed=102)
        g.items = []
        g.floras = []
        d = g.dwarves[0]
        tree = g._spawn_flora("quercus_alba", d.x, d.y, d.z, stage="seedling")
        self.assertIsNotNone(tree)
        assert tree is not None

        self.assertFalse(g._is_tree_choppable(tree))
        tree.stage = "mature"
        self.assertTrue(g._is_tree_choppable(tree))
        self.assertEqual(g._tree_timber_yield(tree), 2)

        tree.reserved_by = d.id
        d.job = g._new_job(
            kind="chop_tree",
            labor="harvest",
            target_id=tree.id,
            destination=(tree.x, tree.y, tree.z),
            phase="to_tree",
            remaining=2,
        )
        run_job_until_idle(g, d.id)

        timber = [i for i in g.items if i.kind == "timber"]
        self.assertEqual(len(timber), 2)
        self.assertTrue(all(i.material == "oak" for i in timber))

    def test_mandate_fulfillment_and_expiry(self) -> None:
        g = Game(rng_seed=103)
        if not g.factions:
            g.add_faction("Test Guild")
        faction = g.factions[0]
        base_rep = faction.reputation
        g.mandates = []

        g.tick_count = 80
        g._spawn_item("herb", 1, 1, 0, material="test-herb", value=2)
        m1 = Mandate(
            id=1,
            issuer_faction_id=faction.id,
            kind="ecology",
            requested_item_kind="herb",
            requested_amount=1,
            due_tick=150,
            reward_reputation=5,
            reward_wealth=20,
            penalty_reputation=3,
        )
        g.mandates.append(m1)
        g._economy_tick()
        self.assertTrue(m1.fulfilled)
        self.assertEqual(faction.reputation, base_rep + 5)

        g.items = [i for i in g.items if i.kind != "rare_plant"]
        m2 = Mandate(
            id=2,
            issuer_faction_id=faction.id,
            kind="ecology",
            requested_item_kind="rare_plant",
            requested_amount=1,
            due_tick=40,
            reward_reputation=4,
            reward_wealth=12,
            penalty_reputation=4,
        )
        g.mandates.append(m2)
        g.tick_count = 200
        g._economy_tick()
        self.assertTrue(m2.failed)
        self.assertEqual(faction.reputation, base_rep + 1)

    def test_integration_soak_produces_economy_outputs(self) -> None:
        g = Game(rng_seed=13)
        g.add_zone("farm", 1, 8, 0, 6, 3)
        g.add_zone("recreation", 20, 1, 0, 5, 3)
        g.add_zone("temple", 20, 5, 0, 4, 3)
        g.add_zone("dormitory", 12, 10, 0, 6, 3)
        g.add_stockpile("raw", 8, 8, 0, 4, 3)
        g.add_stockpile("cooked", 13, 8, 0, 4, 3)
        g.add_stockpile("drink", 18, 8, 0, 4, 3)
        g.add_stockpile("materials", 1, 12, 0, 8, 3)
        g.queue_build_workshop("kitchen", 11, 7, 0)
        g.queue_build_workshop("brewery", 16, 7, 0)
        g.tick(30)
        for ws in g.workshops:
            if ws.kind == "kitchen" and ws.built:
                g.order_workshop(ws.id, "meal", 8)
            if ws.kind == "brewery" and ws.built:
                g.order_workshop(ws.id, "brew", 6)
        g.tick(420)

        forage_total = (
            g.economy_stats.get("foraged_herb", 0)
            + g.economy_stats.get("foraged_berry", 0)
            + g.economy_stats.get("foraged_fiber", 0)
            + g.economy_stats.get("foraged_rare", 0)
        )
        self.assertGreater(g.economy_stats.get("timber_harvested", 0), 0)
        self.assertGreater(forage_total, 0)
        self.assertGreater(g.economy_stats.get("cultural_goods_created", 0), 0)
        self.assertGreater(len(g.mandates), 0)
        self.assertGreater(g.economy_stats.get("mandates_fulfilled", 0) + g.economy_stats.get("mandates_failed", 0), 0)

    def test_deterministic_economy_snapshot(self) -> None:
        def snapshot(seed: int):
            g = Game(rng_seed=seed)
            g.add_zone("farm", 1, 8, 0, 6, 3)
            g.add_zone("temple", 20, 5, 0, 4, 3)
            g.tick(300)
            return (
                g.tick_count,
                g.economy_stats.get("timber_harvested", 0),
                g.economy_stats.get("foraged_herb", 0),
                g.economy_stats.get("foraged_berry", 0),
                g.economy_stats.get("cultural_goods_created", 0),
                g.economy_stats.get("mandates_fulfilled", 0),
                g.economy_stats.get("mandates_failed", 0),
                g.panel("world"),
                g.panel("flora"),
                g.panel("culture"),
            )

        self.assertEqual(snapshot(41), snapshot(41))


if __name__ == "__main__":
    unittest.main()
