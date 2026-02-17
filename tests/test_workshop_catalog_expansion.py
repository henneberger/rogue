import unittest

from fortress.engine import Game


WORKSHOP_KINDS = [
    "kitchen",
    "kitchen_advanced",
    "brewery",
    "carpenter",
    "mason",
    "craftdwarf",
    "smithy",
    "loom",
    "leatherworks",
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


class WorkshopCatalogExpansionTests(unittest.TestCase):
    def test_all_workshops_have_recipes_and_accept_orders(self) -> None:
        g = Game(rng_seed=451)
        for idx, kind in enumerate(WORKSHOP_KINDS):
            ws = g.queue_build_workshop(kind, 1 + (idx % 12), 1 + (idx // 12), 0)
            ws.built = True
            recipes = g.defs.get("recipes", {}).get(kind, {})
            self.assertTrue(recipes, f"missing recipes for workshop '{kind}'")
            recipe_name = next(iter(recipes.keys()))
            g.order_workshop(ws.id, recipe_name, 1)
            self.assertEqual(ws.orders.get(recipe_name), 1)


if __name__ == "__main__":
    unittest.main()
