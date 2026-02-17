import unittest

from fortress.engine import Game


class WorkshopDepthChainTests(unittest.TestCase):
    def test_planned_workshop_chains_produce_outputs(self) -> None:
        g = Game(rng_seed=777)
        g.floras = []
        g.items = []

        workshop_kinds = [
            "kitchen_advanced",
            "butcher",
            "tanner",
            "farmer",
            "mill",
            "quern",
            "furnace",
            "weaponsmith",
            "armorsmith",
            "blacksmith",
            "jeweler",
            "siege",
            "mechanic",
            "ashery",
            "dyer",
            "soapmaker",
            "potter",
            "bowyer",
            "fletcher",
            "paper",
            "scribe",
            "apothecary",
            "doctor",
        ]

        for idx, kind in enumerate(workshop_kinds):
            ws = g.queue_build_workshop(kind, 1 + (idx % 10), 1 + (idx // 10), 0)
            ws.built = True
        g.jobs = []

        # Add workers for throughput.
        for i in range(6):
            g.add_dwarf(f"Worker{i+1}", x=2 + i, y=10, z=0)
        for d in g.dwarves:
            d.needs["hunger"] = 5
            d.needs["thirst"] = 5
            d.needs["sleep"] = 5
            d.stress = 0

        # Seed base resources that drive all chains.
        for _ in range(30):
            g._spawn_item("ore", 2, 2, 0, material="hematite", value=3)
            g._spawn_item("wood", 2, 2, 0, material="oak", value=2)
            g._spawn_item("stone", 2, 2, 0, material="granite", value=1)
        for _ in range(48):
            g._spawn_item("hide", 2, 2, 0, material="goat-hide", value=2)
            g._spawn_item("fiber", 2, 2, 0, material="pig-tail", value=2)
            g._spawn_item("herb", 2, 2, 0, material="allium-herb", value=2, perishability=120)
            g._spawn_item("raw_food", 2, 2, 0, material="plump-helmet", value=2, perishability=140)
        for _ in range(18):
            g._spawn_item("timber", 2, 2, 0, material="oak", value=3)
            g._spawn_item("alcohol", 2, 2, 0, material="ale", value=2, perishability=150)
            g._spawn_item("seed", 2, 2, 0, material="plump-helmet-spawn", value=1)

        g.tick(700)

        kinds = {i.kind for i in g.items}
        expected = {
            "weapon",
            "armor",
            "tool",
            "medicine",
            "bandage",
            "mechanism",
            "soap",
            "pottery",
            "ammo",
            "manuscript",
            "siege_part",
        }
        missing = expected - kinds
        self.assertFalse(missing, f"expected produced outputs missing: {sorted(missing)}")
        produced_expected = {
            "produced_metal_bar",
            "produced_ash",
            "produced_flour",
            "produced_leather",
            "produced_gem_cut",
            "produced_paper_sheet",
        }
        missing_produced = {k for k in produced_expected if g.economy_stats.get(k, 0) <= 0}
        self.assertFalse(missing_produced, f"expected produced counters missing: {sorted(missing_produced)}")


if __name__ == "__main__":
    unittest.main()
