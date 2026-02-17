from __future__ import annotations

from typing import Any, Dict

from fortress.systems.flora_catalog import FLORA_SPECIES

class DefsMixin:
    @staticmethod
    def default_defs() -> Dict[str, Any]:
        return {
            "recipes": {
                "kitchen": {"meal": {"inputs": {"raw_food": 1}, "outputs": {"cooked_food": 1}, "time": 4, "value_bonus": 3}},
                "kitchen_advanced": {
                    "preserves": {"inputs": {"raw_food": 1, "alcohol": 1}, "outputs": {"cooked_food": 2}, "time": 6, "value_bonus": 5},
                    "stew": {"inputs": {"raw_food": 2}, "outputs": {"cooked_food": 2}, "time": 6, "value_bonus": 4},
                },
                "brewery": {"brew": {"inputs": {"raw_food": 1}, "outputs": {"alcohol": 1}, "time": 4, "value_bonus": 2}},
                "carpenter": {
                    "bed": {"inputs": {"wood": 1}, "outputs": {"bed": 1}, "time": 5, "value_bonus": 5},
                    "chest": {"inputs": {"wood": 1}, "outputs": {"chest": 1}, "time": 5, "value_bonus": 4},
                    "barrel": {"inputs": {"wood": 1}, "outputs": {"barrel": 1}, "time": 4, "value_bonus": 3},
                    "bin": {"inputs": {"timber": 1}, "outputs": {"bin": 1}, "time": 5, "value_bonus": 4},
                    "crate": {"inputs": {"timber": 1}, "outputs": {"crate": 1}, "time": 5, "value_bonus": 4},
                },
                "mason": {"block": {"inputs": {"stone": 1}, "outputs": {"craft_good": 1}, "time": 3, "value_bonus": 2}},
                "craftdwarf": {"trinket": {"inputs": {"stone": 1}, "outputs": {"craft_good": 1}, "time": 3, "value_bonus": 3}},
                "smithy": {"tool": {"inputs": {"ore": 1}, "outputs": {"craft_good": 1}, "time": 6, "value_bonus": 6}},
                "butcher": {
                    "dress_carcass": {"inputs": {"hide": 1}, "outputs": {"raw_food": 2, "seed": 1}, "time": 4, "value_bonus": 2}
                },
                "tanner": {
                    "cure_hide": {"inputs": {"hide": 1}, "outputs": {"leather": 1}, "time": 4, "value_bonus": 3}
                },
                "farmer": {
                    "thresh_crop": {"inputs": {"seed": 1}, "outputs": {"raw_food": 2, "seed": 1}, "time": 4, "value_bonus": 2}
                },
                "mill": {
                    "grind_flour": {"inputs": {"raw_food": 1}, "outputs": {"flour": 1}, "time": 4, "value_bonus": 2}
                },
                "quern": {
                    "make_gruel": {"inputs": {"flour": 1}, "outputs": {"raw_food": 1}, "time": 3, "value_bonus": 2}
                },
                "furnace": {
                    "smelt_bar": {"inputs": {"ore": 1, "wood": 1}, "outputs": {"metal_bar": 1}, "time": 7, "value_bonus": 4}
                },
                "weaponsmith": {
                    "forge_weapon": {"inputs": {"metal_bar": 1}, "outputs": {"weapon": 1}, "time": 7, "value_bonus": 7}
                },
                "armorsmith": {
                    "forge_armor": {"inputs": {"metal_bar": 1}, "outputs": {"armor": 1}, "time": 7, "value_bonus": 7}
                },
                "blacksmith": {
                    "forge_tool": {"inputs": {"metal_bar": 1}, "outputs": {"tool": 1}, "time": 6, "value_bonus": 6}
                },
                "jeweler": {
                    "cut_gem": {"inputs": {"ore": 1}, "outputs": {"gem_cut": 1}, "time": 5, "value_bonus": 5},
                    "set_jewel": {"inputs": {"gem_cut": 1}, "outputs": {"craft_good": 1}, "time": 4, "value_bonus": 6},
                },
                "siege": {
                    "build_siege_part": {"inputs": {"timber": 1, "wood": 1}, "outputs": {"siege_part": 1}, "time": 8, "value_bonus": 7}
                },
                "mechanic": {
                    "make_mechanism": {"inputs": {"stone": 1}, "outputs": {"mechanism": 1}, "time": 4, "value_bonus": 4}
                },
                "ashery": {
                    "make_ash": {"inputs": {"wood": 1}, "outputs": {"ash": 1}, "time": 4, "value_bonus": 3}
                },
                "dyer": {
                    "make_dye": {"inputs": {"herb": 1}, "outputs": {"dye": 1}, "time": 4, "value_bonus": 3}
                },
                "soapmaker": {
                    "make_soap": {"inputs": {"ash": 1, "hide": 1}, "outputs": {"soap": 1}, "time": 5, "value_bonus": 5}
                },
                "potter": {
                    "fire_pottery": {"inputs": {"stone": 1}, "outputs": {"pottery": 1}, "time": 4, "value_bonus": 4}
                },
                "bowyer": {
                    "make_bow": {"inputs": {"wood": 1}, "outputs": {"weapon": 1}, "time": 5, "value_bonus": 5}
                },
                "fletcher": {
                    "make_bolts": {"inputs": {"wood": 1}, "outputs": {"ammo": 2}, "time": 4, "value_bonus": 3}
                },
                "paper": {
                    "press_paper": {"inputs": {"fiber": 1}, "outputs": {"paper_sheet": 1}, "time": 4, "value_bonus": 3}
                },
                "scribe": {
                    "copy_text": {"inputs": {"paper_sheet": 1}, "outputs": {"manuscript": 1}, "time": 5, "value_bonus": 5}
                },
                "apothecary": {
                    "compound_medicine": {"inputs": {"herb": 1}, "outputs": {"medicine": 1}, "time": 4, "value_bonus": 4}
                },
                "doctor": {
                    "prepare_bandage": {"inputs": {"fiber": 1}, "outputs": {"bandage": 1}, "time": 3, "value_bonus": 3}
                },
                "loom": {
                    "cloth": {"inputs": {"fiber": 1}, "outputs": {"craft_good": 1}, "time": 4, "value_bonus": 4},
                    "bag": {"inputs": {"fiber": 1}, "outputs": {"bag": 1}, "time": 4, "value_bonus": 3},
                },
                "leatherworks": {
                    "leather_gear": {"inputs": {"hide": 1}, "outputs": {"craft_good": 1}, "time": 4, "value_bonus": 4},
                    "bag": {"inputs": {"hide": 1}, "outputs": {"bag": 1}, "time": 4, "value_bonus": 3},
                },
            },
            "creatures": {"goat": {"graze": 1}, "boar": {"graze": 1}},
            "materials": ["oak", "granite", "hematite", "pig-tail", "goat-hide", "plump-helmet"],
            "geology_ores": {
                "hematite": {"rarity": "common", "value": 4, "min_depth": 1, "max_depth": 2},
                "magnetite": {"rarity": "uncommon", "value": 5, "min_depth": 1, "max_depth": 2},
                "cassiterite": {"rarity": "rare", "value": 7, "min_depth": 2, "max_depth": 2},
            },
            "geology_gems": {
                "quartz": {"rarity": "common", "value": 8, "min_depth": 1, "max_depth": 2},
                "garnet": {"rarity": "uncommon", "value": 10, "min_depth": 2, "max_depth": 2},
                "emerald": {"rarity": "rare", "value": 14, "min_depth": 2, "max_depth": 2},
            },
            "flora_species": FLORA_SPECIES,
        }
