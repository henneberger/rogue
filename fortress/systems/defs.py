from __future__ import annotations

from typing import Any, Dict

from fortress.systems.flora_catalog import FLORA_SPECIES

class DefsMixin:
    @staticmethod
    def default_defs() -> Dict[str, Any]:
        return {
            "recipes": {
                "kitchen": {"meal": {"inputs": {"raw_food": 1}, "outputs": {"cooked_food": 1}, "time": 4, "value_bonus": 3}},
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
            "flora_species": FLORA_SPECIES,
        }
