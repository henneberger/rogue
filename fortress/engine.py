from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import random

from fortress.io.commands import CommandMixin, help_text
from fortress.io.persistence import PersistenceMixin
from fortress.io.render import RenderMixin
from fortress.models import (
    Animal,
    Coord3,
    Crime,
    Dwarf,
    Event,
    Faction,
    Flora,
    HistoricalEvent,
    Item,
    Job,
    LABORS,
    Region,
    Room,
    Squad,
    Stockpile,
    WorldState,
    Workshop,
    Zone,
    clamp,
)
from fortress.systems.jobs import JobSystemsMixin
from fortress.systems.justice import JusticeSystemsMixin
from fortress.systems.needs import NeedsSystemsMixin
from fortress.systems.social import SocialSystemsMixin
from fortress.systems.world import WorldSystemsMixin
from fortress.systems.architecture import ArchitectureSystemsMixin
from fortress.systems.flora import FloraSystemsMixin


@dataclass
class Game(
    CommandMixin,
    PersistenceMixin,
    RenderMixin,
    ArchitectureSystemsMixin,
    FloraSystemsMixin,
    JobSystemsMixin,
    JusticeSystemsMixin,
    NeedsSystemsMixin,
    SocialSystemsMixin,
    WorldSystemsMixin,
):
    width: int = 32
    height: int = 16
    depth: int = 3
    rng_seed: int = 7
    tick_count: int = 0
    selected_z: int = 0
    next_zone_id: int = 1
    next_stockpile_id: int = 1
    next_workshop_id: int = 1
    next_item_id: int = 1
    next_dwarf_id: int = 1
    next_animal_id: int = 1
    next_squad_id: int = 1
    next_faction_id: int = 1
    next_job_id: int = 1
    next_crime_id: int = 1
    next_room_id: int = 1
    next_flora_id: int = 1
    max_flora: int = 80
    zones: List[Zone] = field(default_factory=list)
    stockpiles: List[Stockpile] = field(default_factory=list)
    workshops: List[Workshop] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    dwarves: List[Dwarf] = field(default_factory=list)
    animals: List[Animal] = field(default_factory=list)
    squads: List[Squad] = field(default_factory=list)
    factions: List[Faction] = field(default_factory=list)
    regions: List[Region] = field(default_factory=list)
    world_history: List[HistoricalEvent] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    floras: List[Flora] = field(default_factory=list)
    crimes: List[Crime] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    jobs: List[Job] = field(default_factory=list)
    world: WorldState = field(default_factory=WorldState)
    command_log: List[str] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    defs: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.rng_seed)
        self.defs = self.default_defs()
        self._generate_world()
        if not self.dwarves:
            self.add_dwarf("Urist", 2, 2, 0)
            self.add_dwarf("Domas", 4, 2, 0)
            self.add_dwarf("Mistem", 3, 4, 0)
        if not self.animals:
            self.add_animal("goat", 6, 3, 0)
        for _ in range(4):
            self._spawn_item("raw_food", 1, 1, 0, material="plump-helmet", perishability=120, value=2)
        self._spawn_item("cooked_food", 1, 2, 0, material="stew", perishability=180, value=4)
        self._spawn_item("wood", 2, 1, 0, material="oak", value=2)
        self._spawn_item("stone", 2, 2, 0, material="granite", value=1)
        self._spawn_item("ore", 2, 3, 0, material="hematite", value=3)
        self._spawn_item("fiber", 2, 4, 0, material="pig-tail", value=2)
        self._spawn_item("hide", 2, 5, 0, material="goat-hide", value=2)
        self._init_flora()
        self._refresh_rooms_and_assignments()

    @staticmethod
    def default_defs() -> Dict[str, Any]:
        return {
            "recipes": {
                "kitchen": {"meal": {"inputs": {"raw_food": 1}, "outputs": {"cooked_food": 1}, "time": 4, "value_bonus": 3}},
                "brewery": {"brew": {"inputs": {"raw_food": 1}, "outputs": {"alcohol": 1}, "time": 4, "value_bonus": 2}},
                "carpenter": {"bed": {"inputs": {"wood": 1}, "outputs": {"bed": 1}, "time": 5, "value_bonus": 5}},
                "mason": {"block": {"inputs": {"stone": 1}, "outputs": {"craft_good": 1}, "time": 3, "value_bonus": 2}},
                "craftdwarf": {"trinket": {"inputs": {"stone": 1}, "outputs": {"craft_good": 1}, "time": 3, "value_bonus": 3}},
                "smithy": {"tool": {"inputs": {"ore": 1}, "outputs": {"craft_good": 1}, "time": 6, "value_bonus": 6}},
                "loom": {"cloth": {"inputs": {"fiber": 1}, "outputs": {"craft_good": 1}, "time": 4, "value_bonus": 4}},
                "leatherworks": {
                    "leather_gear": {"inputs": {"hide": 1}, "outputs": {"craft_good": 1}, "time": 4, "value_bonus": 4}
                },
            },
            "creatures": {"goat": {"graze": 1}, "boar": {"graze": 1}},
            "materials": ["oak", "granite", "hematite", "pig-tail", "goat-hide", "plump-helmet"],
            "flora_species": {
                "quercus_alba": {
                    "id": "quercus_alba",
                    "common_name": "White oak",
                    "scientific_name": "Quercus alba",
                    "kind": "tree",
                    "biomes": ["temperate-forest"],
                    "stages": ["seedling", "sapling", "young", "mature", "ancient"],
                    "stage_threshold": 26,
                    "base_growth": 1.0,
                    "spread_stage_index": 3,
                    "spread_radius": 3,
                    "spread_chance": 0.035,
                    "spread_cooldown": 22,
                    "temp_min": -8,
                    "temp_max": 30,
                    "dry_penalty": 1,
                    "season_mod": {"spring": 1.3, "summer": 1.15, "autumn": 0.75, "winter": 0.28},
                    "weather_mod": {"clear": 1.0, "rain": 1.12, "storm": 0.92, "dry": 0.7, "fog": 0.95},
                },
                "betula_papyrifera": {
                    "id": "betula_papyrifera",
                    "common_name": "Paper birch",
                    "scientific_name": "Betula papyrifera",
                    "kind": "tree",
                    "biomes": ["temperate-forest"],
                    "stages": ["seedling", "sapling", "young", "mature", "ancient"],
                    "stage_threshold": 22,
                    "base_growth": 1.15,
                    "spread_stage_index": 2,
                    "spread_radius": 3,
                    "spread_chance": 0.05,
                    "spread_cooldown": 18,
                    "temp_min": -12,
                    "temp_max": 29,
                    "dry_penalty": 2,
                    "season_mod": {"spring": 1.4, "summer": 1.2, "autumn": 0.8, "winter": 0.24},
                    "weather_mod": {"clear": 1.0, "rain": 1.18, "storm": 0.94, "dry": 0.6, "fog": 1.0},
                },
                "vaccinium_corymbosum": {
                    "id": "vaccinium_corymbosum",
                    "common_name": "Highbush blueberry",
                    "scientific_name": "Vaccinium corymbosum",
                    "kind": "plant",
                    "biomes": ["temperate-forest", "river-lowlands"],
                    "stages": ["sprout", "juvenile", "mature", "flowering", "seeded"],
                    "stage_threshold": 16,
                    "base_growth": 1.35,
                    "spread_stage_index": 3,
                    "spread_radius": 2,
                    "spread_chance": 0.07,
                    "spread_cooldown": 14,
                    "temp_min": -4,
                    "temp_max": 31,
                    "dry_penalty": 2,
                    "season_mod": {"spring": 1.5, "summer": 1.25, "autumn": 0.95, "winter": 0.18},
                    "weather_mod": {"clear": 1.0, "rain": 1.22, "storm": 0.85, "dry": 0.62, "fog": 0.97},
                },
                "allium_canadense": {
                    "id": "allium_canadense",
                    "common_name": "Wild onion",
                    "scientific_name": "Allium canadense",
                    "kind": "plant",
                    "biomes": ["temperate-forest", "river-lowlands", "highland-heath"],
                    "stages": ["sprout", "juvenile", "mature", "flowering", "seeded"],
                    "stage_threshold": 14,
                    "base_growth": 1.45,
                    "spread_stage_index": 2,
                    "spread_radius": 2,
                    "spread_chance": 0.08,
                    "spread_cooldown": 12,
                    "temp_min": -6,
                    "temp_max": 32,
                    "dry_penalty": 1,
                    "season_mod": {"spring": 1.55, "summer": 1.1, "autumn": 0.82, "winter": 0.2},
                    "weather_mod": {"clear": 1.0, "rain": 1.16, "storm": 0.9, "dry": 0.72, "fog": 1.0},
                },
                "picea_mariana": {
                    "id": "picea_mariana",
                    "common_name": "Black spruce",
                    "scientific_name": "Picea mariana",
                    "kind": "tree",
                    "biomes": ["taiga"],
                    "stages": ["seedling", "sapling", "young", "mature", "ancient"],
                    "stage_threshold": 27,
                    "base_growth": 0.9,
                    "spread_stage_index": 3,
                    "spread_radius": 2,
                    "spread_chance": 0.03,
                    "spread_cooldown": 24,
                    "temp_min": -22,
                    "temp_max": 24,
                    "dry_penalty": 2,
                    "season_mod": {"spring": 1.1, "summer": 1.0, "autumn": 0.72, "winter": 0.38},
                    "weather_mod": {"clear": 1.0, "rain": 1.08, "storm": 0.9, "dry": 0.7, "fog": 1.02},
                },
                "pinus_sylvestris": {
                    "id": "pinus_sylvestris",
                    "common_name": "Scots pine",
                    "scientific_name": "Pinus sylvestris",
                    "kind": "tree",
                    "biomes": ["taiga", "highland-heath"],
                    "stages": ["seedling", "sapling", "young", "mature", "ancient"],
                    "stage_threshold": 24,
                    "base_growth": 1.0,
                    "spread_stage_index": 3,
                    "spread_radius": 3,
                    "spread_chance": 0.04,
                    "spread_cooldown": 20,
                    "temp_min": -18,
                    "temp_max": 27,
                    "dry_penalty": 1,
                    "season_mod": {"spring": 1.2, "summer": 1.1, "autumn": 0.8, "winter": 0.36},
                    "weather_mod": {"clear": 1.0, "rain": 1.08, "storm": 0.92, "dry": 0.75, "fog": 1.0},
                },
                "cladonia_rangiferina": {
                    "id": "cladonia_rangiferina",
                    "common_name": "Reindeer lichen",
                    "scientific_name": "Cladonia rangiferina",
                    "kind": "plant",
                    "biomes": ["taiga", "alpine"],
                    "stages": ["sprout", "juvenile", "mature", "seeded", "withered"],
                    "stage_threshold": 20,
                    "base_growth": 0.78,
                    "spread_stage_index": 2,
                    "spread_radius": 1,
                    "spread_chance": 0.05,
                    "spread_cooldown": 16,
                    "temp_min": -26,
                    "temp_max": 20,
                    "dry_penalty": 0,
                    "season_mod": {"spring": 1.05, "summer": 1.0, "autumn": 0.88, "winter": 0.65},
                    "weather_mod": {"clear": 1.0, "rain": 1.0, "storm": 0.95, "dry": 0.92, "fog": 1.1},
                },
                "pteridium_aquilinum": {
                    "id": "pteridium_aquilinum",
                    "common_name": "Bracken fern",
                    "scientific_name": "Pteridium aquilinum",
                    "kind": "plant",
                    "biomes": ["taiga", "temperate-forest"],
                    "stages": ["sprout", "juvenile", "mature", "flowering", "withered"],
                    "stage_threshold": 15,
                    "base_growth": 1.2,
                    "spread_stage_index": 2,
                    "spread_radius": 2,
                    "spread_chance": 0.055,
                    "spread_cooldown": 13,
                    "temp_min": -10,
                    "temp_max": 28,
                    "dry_penalty": 2,
                    "season_mod": {"spring": 1.45, "summer": 1.22, "autumn": 0.72, "winter": 0.18},
                    "weather_mod": {"clear": 1.0, "rain": 1.2, "storm": 0.9, "dry": 0.62, "fog": 1.04},
                },
                "artemisia_tridentata": {
                    "id": "artemisia_tridentata",
                    "common_name": "Big sagebrush",
                    "scientific_name": "Artemisia tridentata",
                    "kind": "plant",
                    "biomes": ["arid-steppe"],
                    "stages": ["sprout", "juvenile", "mature", "seeded", "withered"],
                    "stage_threshold": 19,
                    "base_growth": 0.95,
                    "spread_stage_index": 2,
                    "spread_radius": 2,
                    "spread_chance": 0.045,
                    "spread_cooldown": 15,
                    "temp_min": -8,
                    "temp_max": 35,
                    "dry_penalty": 0,
                    "season_mod": {"spring": 1.2, "summer": 1.0, "autumn": 0.9, "winter": 0.4},
                    "weather_mod": {"clear": 1.0, "rain": 1.08, "storm": 0.95, "dry": 0.95, "fog": 0.92},
                },
                "bouteloua_gracilis": {
                    "id": "bouteloua_gracilis",
                    "common_name": "Blue grama",
                    "scientific_name": "Bouteloua gracilis",
                    "kind": "plant",
                    "biomes": ["arid-steppe", "highland-heath"],
                    "stages": ["sprout", "juvenile", "mature", "seeded", "withered"],
                    "stage_threshold": 13,
                    "base_growth": 1.15,
                    "spread_stage_index": 2,
                    "spread_radius": 2,
                    "spread_chance": 0.09,
                    "spread_cooldown": 10,
                    "temp_min": -6,
                    "temp_max": 36,
                    "dry_penalty": 1,
                    "season_mod": {"spring": 1.35, "summer": 1.25, "autumn": 0.86, "winter": 0.25},
                    "weather_mod": {"clear": 1.0, "rain": 1.35, "storm": 1.05, "dry": 0.78, "fog": 0.95},
                },
                "opuntia_humifusa": {
                    "id": "opuntia_humifusa",
                    "common_name": "Prickly pear",
                    "scientific_name": "Opuntia humifusa",
                    "kind": "plant",
                    "biomes": ["arid-steppe"],
                    "stages": ["sprout", "juvenile", "mature", "flowering", "seeded"],
                    "stage_threshold": 20,
                    "base_growth": 0.88,
                    "spread_stage_index": 3,
                    "spread_radius": 1,
                    "spread_chance": 0.03,
                    "spread_cooldown": 18,
                    "temp_min": -4,
                    "temp_max": 38,
                    "dry_penalty": 0,
                    "season_mod": {"spring": 1.0, "summer": 1.15, "autumn": 0.85, "winter": 0.3},
                    "weather_mod": {"clear": 1.0, "rain": 1.05, "storm": 0.9, "dry": 1.0, "fog": 0.85},
                },
                "vachellia_tortilis": {
                    "id": "vachellia_tortilis",
                    "common_name": "Acacia",
                    "scientific_name": "Vachellia tortilis",
                    "kind": "tree",
                    "biomes": ["arid-steppe"],
                    "stages": ["seedling", "sapling", "young", "mature", "ancient"],
                    "stage_threshold": 25,
                    "base_growth": 0.82,
                    "spread_stage_index": 3,
                    "spread_radius": 2,
                    "spread_chance": 0.028,
                    "spread_cooldown": 25,
                    "temp_min": -2,
                    "temp_max": 39,
                    "dry_penalty": 0,
                    "season_mod": {"spring": 1.0, "summer": 1.1, "autumn": 0.86, "winter": 0.32},
                    "weather_mod": {"clear": 1.0, "rain": 1.15, "storm": 1.0, "dry": 0.95, "fog": 0.82},
                },
                "pinus_mugo": {
                    "id": "pinus_mugo",
                    "common_name": "Dwarf mountain pine",
                    "scientific_name": "Pinus mugo",
                    "kind": "tree",
                    "biomes": ["alpine", "highland-heath"],
                    "stages": ["seedling", "sapling", "young", "mature", "ancient"],
                    "stage_threshold": 26,
                    "base_growth": 0.85,
                    "spread_stage_index": 3,
                    "spread_radius": 2,
                    "spread_chance": 0.03,
                    "spread_cooldown": 22,
                    "temp_min": -20,
                    "temp_max": 22,
                    "dry_penalty": 1,
                    "season_mod": {"spring": 1.05, "summer": 1.0, "autumn": 0.85, "winter": 0.45},
                    "weather_mod": {"clear": 1.0, "rain": 1.05, "storm": 0.9, "dry": 0.8, "fog": 1.02},
                },
                "myosotis_alpestris": {
                    "id": "myosotis_alpestris",
                    "common_name": "Alpine forget-me-not",
                    "scientific_name": "Myosotis alpestris",
                    "kind": "plant",
                    "biomes": ["alpine", "highland-heath"],
                    "stages": ["sprout", "juvenile", "mature", "flowering", "seeded"],
                    "stage_threshold": 15,
                    "base_growth": 1.05,
                    "spread_stage_index": 3,
                    "spread_radius": 1,
                    "spread_chance": 0.06,
                    "spread_cooldown": 13,
                    "temp_min": -16,
                    "temp_max": 19,
                    "dry_penalty": 2,
                    "season_mod": {"spring": 1.3, "summer": 1.1, "autumn": 0.72, "winter": 0.22},
                    "weather_mod": {"clear": 1.0, "rain": 1.1, "storm": 0.82, "dry": 0.6, "fog": 1.05},
                },
                "leontopodium_nivale": {
                    "id": "leontopodium_nivale",
                    "common_name": "Edelweiss",
                    "scientific_name": "Leontopodium nivale",
                    "kind": "plant",
                    "biomes": ["alpine"],
                    "stages": ["sprout", "juvenile", "mature", "flowering", "withered"],
                    "stage_threshold": 18,
                    "base_growth": 0.86,
                    "spread_stage_index": 2,
                    "spread_radius": 1,
                    "spread_chance": 0.036,
                    "spread_cooldown": 16,
                    "temp_min": -18,
                    "temp_max": 17,
                    "dry_penalty": 1,
                    "season_mod": {"spring": 1.2, "summer": 1.0, "autumn": 0.75, "winter": 0.32},
                    "weather_mod": {"clear": 1.0, "rain": 1.08, "storm": 0.82, "dry": 0.74, "fog": 1.0},
                },
                "sphagnum_spp": {
                    "id": "sphagnum_spp",
                    "common_name": "Sphagnum moss",
                    "scientific_name": "Sphagnum spp.",
                    "kind": "plant",
                    "biomes": ["alpine", "river-lowlands", "taiga"],
                    "stages": ["sprout", "juvenile", "mature", "seeded", "withered"],
                    "stage_threshold": 17,
                    "base_growth": 1.1,
                    "spread_stage_index": 2,
                    "spread_radius": 1,
                    "spread_chance": 0.072,
                    "spread_cooldown": 12,
                    "temp_min": -14,
                    "temp_max": 24,
                    "dry_penalty": 3,
                    "season_mod": {"spring": 1.3, "summer": 1.1, "autumn": 0.9, "winter": 0.34},
                    "weather_mod": {"clear": 1.0, "rain": 1.28, "storm": 1.08, "dry": 0.5, "fog": 1.12},
                },
                "salix_nigra": {
                    "id": "salix_nigra",
                    "common_name": "Black willow",
                    "scientific_name": "Salix nigra",
                    "kind": "tree",
                    "biomes": ["river-lowlands"],
                    "stages": ["seedling", "sapling", "young", "mature", "ancient"],
                    "stage_threshold": 21,
                    "base_growth": 1.22,
                    "spread_stage_index": 2,
                    "spread_radius": 3,
                    "spread_chance": 0.065,
                    "spread_cooldown": 16,
                    "temp_min": -8,
                    "temp_max": 31,
                    "dry_penalty": 3,
                    "season_mod": {"spring": 1.5, "summer": 1.25, "autumn": 0.9, "winter": 0.22},
                    "weather_mod": {"clear": 1.0, "rain": 1.33, "storm": 1.05, "dry": 0.48, "fog": 1.08},
                },
                "populus_deltoides": {
                    "id": "populus_deltoides",
                    "common_name": "Eastern cottonwood",
                    "scientific_name": "Populus deltoides",
                    "kind": "tree",
                    "biomes": ["river-lowlands"],
                    "stages": ["seedling", "sapling", "young", "mature", "ancient"],
                    "stage_threshold": 20,
                    "base_growth": 1.28,
                    "spread_stage_index": 2,
                    "spread_radius": 3,
                    "spread_chance": 0.07,
                    "spread_cooldown": 15,
                    "temp_min": -7,
                    "temp_max": 32,
                    "dry_penalty": 3,
                    "season_mod": {"spring": 1.52, "summer": 1.3, "autumn": 0.9, "winter": 0.2},
                    "weather_mod": {"clear": 1.0, "rain": 1.35, "storm": 1.0, "dry": 0.45, "fog": 1.05},
                },
                "phragmites_australis": {
                    "id": "phragmites_australis",
                    "common_name": "Common reed",
                    "scientific_name": "Phragmites australis",
                    "kind": "plant",
                    "biomes": ["river-lowlands"],
                    "stages": ["sprout", "juvenile", "mature", "flowering", "seeded"],
                    "stage_threshold": 12,
                    "base_growth": 1.35,
                    "spread_stage_index": 2,
                    "spread_radius": 2,
                    "spread_chance": 0.1,
                    "spread_cooldown": 9,
                    "temp_min": -5,
                    "temp_max": 33,
                    "dry_penalty": 4,
                    "season_mod": {"spring": 1.5, "summer": 1.32, "autumn": 0.9, "winter": 0.16},
                    "weather_mod": {"clear": 1.0, "rain": 1.4, "storm": 1.15, "dry": 0.4, "fog": 1.1},
                },
                "typha_latifolia": {
                    "id": "typha_latifolia",
                    "common_name": "Cattail",
                    "scientific_name": "Typha latifolia",
                    "kind": "plant",
                    "biomes": ["river-lowlands"],
                    "stages": ["sprout", "juvenile", "mature", "seeded", "withered"],
                    "stage_threshold": 13,
                    "base_growth": 1.3,
                    "spread_stage_index": 2,
                    "spread_radius": 2,
                    "spread_chance": 0.085,
                    "spread_cooldown": 10,
                    "temp_min": -6,
                    "temp_max": 31,
                    "dry_penalty": 4,
                    "season_mod": {"spring": 1.45, "summer": 1.25, "autumn": 0.9, "winter": 0.18},
                    "weather_mod": {"clear": 1.0, "rain": 1.32, "storm": 1.12, "dry": 0.42, "fog": 1.08},
                },
            },
        }

    @property
    def raw_food(self) -> int:
        return sum(1 for i in self.items if i.kind == "raw_food")

    @property
    def cooked_food(self) -> int:
        return sum(1 for i in self.items if i.kind == "cooked_food")

    @property
    def drinks(self) -> int:
        return sum(1 for i in self.items if i.kind == "alcohol")

    def add_dwarf(self, name: Optional[str] = None, x: Optional[int] = None, y: Optional[int] = None, z: int = 0) -> Dwarf:
        name = name or f"Dwarf{self.next_dwarf_id}"
        x = x if x is not None else self.rng.randint(1, self.width - 2)
        y = y if y is not None else self.rng.randint(1, self.height - 2)
        self._validate_point(x, y, z)
        d = Dwarf(id=self.next_dwarf_id, name=name, x=x, y=y, z=z)
        d.alcohol_dependency = self.rng.randint(35, 85)
        d.needs["alcohol"] = max(10, min(90, d.alcohol_dependency - 20))
        for labor in LABORS:
            d.labor_priority.setdefault(labor, 3)
            d.skills.setdefault(labor, 0)
        self.next_dwarf_id += 1
        self.dwarves.append(d)
        for other in self.dwarves:
            if other.id != d.id:
                d.relationships[other.id] = 0
                other.relationships[d.id] = 0
        return d

    def add_animal(self, species: str, x: int, y: int, z: int) -> Animal:
        self._validate_point(x, y, z)
        a = Animal(id=self.next_animal_id, species=species, x=x, y=y, z=z)
        self.next_animal_id += 1
        self.animals.append(a)
        return a

    def add_faction(
        self,
        name: str,
        stance: str = "neutral",
        reputation: int = 0,
        home_region_id: Optional[int] = None,
        civ_type: str = "kingdom",
    ) -> Faction:
        f = Faction(
            id=self.next_faction_id,
            name=name,
            stance=stance,
            reputation=reputation,
            home_region_id=home_region_id,
            civ_type=civ_type,
        )
        self.next_faction_id += 1
        self.factions.append(f)
        return f

    def _generate_world(self) -> None:
        world_rng = random.Random(self.rng_seed)
        adjectives = ["Crag", "Frost", "Iron", "Amber", "Moss", "Storm", "Deep", "Dawn"]
        nouns = ["Reach", "Vale", "Spine", "Basin", "Frontier", "March", "Hollow", "Strand"]
        biomes = [
            "temperate-forest",
            "arid-steppe",
            "taiga",
            "alpine",
            "river-lowlands",
            "highland-heath",
        ]
        rainfalls = ["low", "moderate", "high"]
        temps = ["cold", "mild", "warm"]
        elevations = ["lowlands", "uplands", "mountainous"]
        resource_pool = ["wood", "stone", "ore", "clay", "fiber", "wildlife", "herbs"]
        self.world.world_name = f"{world_rng.choice(adjectives)} {world_rng.choice(nouns)}"

        self.regions = []
        for rid in range(1, 7):
            region = Region(
                id=rid,
                name=f"{world_rng.choice(adjectives)} {world_rng.choice(nouns)}",
                biome=world_rng.choice(biomes),
                rainfall=world_rng.choice(rainfalls),
                temperature_band=world_rng.choice(temps),
                elevation=world_rng.choice(elevations),
                resources=sorted(world_rng.sample(resource_pool, k=3)),
            )
            self.regions.append(region)

        for idx, region in enumerate(self.regions):
            nxt = ((idx + 1) % len(self.regions)) + 1
            prv = ((idx - 1) % len(self.regions)) + 1
            region.neighbors = sorted({nxt, prv})
        for region in self.regions:
            if world_rng.random() < 0.45:
                region.neighbors = sorted(set(region.neighbors + [world_rng.randint(1, len(self.regions))]))
                region.neighbors = [rid for rid in region.neighbors if rid != region.id]

        fortress_region = next((r for r in self.regions if r.biome == "temperate-forest"), self.regions[0])
        self.world.fortress_region_id = fortress_region.id
        self.world.biome = fortress_region.biome

        civ_specs = [
            ("Mountainhome", "dwarven-hold", fortress_region.id),
            ("River Guild", "merchant-league", self.regions[1].id),
            ("Goblin Host", "warlike-tribe", self.regions[2].id),
            ("Sun Court", "kingdom", self.regions[3].id),
        ]
        civ_names = [name for name, _, _ in civ_specs]
        event_types = [
            ("trade-pact", 10, 24),
            ("border-skirmish", -28, -10),
            ("aid-treaty", 12, 20),
            ("trade-dispute", -16, -6),
            ("marriage-alliance", 14, 26),
            ("betrayal", -30, -14),
        ]

        self.world_history = []
        for year in sorted(world_rng.sample(range(-120, -4), 14)):
            actor = world_rng.choice(civ_names)
            target = world_rng.choice([name for name in civ_names if name != actor])
            ev_name, lo, hi = world_rng.choice(event_types)
            delta = world_rng.randint(lo, hi)
            text = f"{actor} and {target}: {ev_name} ({delta:+d} relation)"
            self.world_history.append(
                HistoricalEvent(
                    year=year,
                    event_type=ev_name,
                    actor=actor,
                    target=target,
                    delta_reputation=delta,
                    text=text,
                )
            )

        relation_by_civ = {name: 0 for name in civ_names}
        player_civ = "Mountainhome"
        for ev in self.world_history:
            if ev.actor == player_civ:
                relation_by_civ[ev.target] += ev.delta_reputation
            elif ev.target == player_civ:
                relation_by_civ[ev.actor] += ev.delta_reputation

        self.factions = []
        self.next_faction_id = 1
        for name, civ_type, home_region_id in civ_specs:
            score = relation_by_civ.get(name, 0)
            if name == player_civ:
                stance = "allied"
                score = max(score, 15)
            elif score >= 20:
                stance = "allied"
            elif score <= -20:
                stance = "hostile"
            else:
                stance = "neutral"
            self.add_faction(
                name=name,
                stance=stance,
                reputation=score,
                home_region_id=home_region_id,
                civ_type=civ_type,
            )

    def add_zone(self, kind: str, x: int, y: int, z: int, w: int, h: int) -> Zone:
        if kind not in {"farm", "recreation", "temple", "dormitory", "hospital", "pasture", "burrow"}:
            raise ValueError("unknown zone kind")
        self._validate_rect(x, y, z, w, h)
        zt = Zone(id=self.next_zone_id, kind=kind, x=x, y=y, z=z, w=w, h=h)
        self.next_zone_id += 1
        if kind == "farm":
            zt.crop_available = 3
        self.zones.append(zt)
        return zt

    def add_stockpile(self, kind: str, x: int, y: int, z: int, w: int, h: int) -> Stockpile:
        if kind not in {"raw", "cooked", "drink", "materials", "goods", "medical", "furniture", "general"}:
            raise ValueError("unknown stockpile kind")
        self._validate_rect(x, y, z, w, h)
        sp = Stockpile(id=self.next_stockpile_id, kind=kind, x=x, y=y, z=z, w=w, h=h)
        self.next_stockpile_id += 1
        self.stockpiles.append(sp)
        return sp

    def queue_build_workshop(self, kind: str, x: int, y: int, z: int) -> Workshop:
        if kind not in {"kitchen", "brewery", "carpenter", "mason", "craftdwarf", "smithy", "loom", "leatherworks"}:
            raise ValueError("unsupported workshop kind")
        self._validate_point(x, y, z)
        ws = Workshop(id=self.next_workshop_id, kind=kind, x=x, y=y, z=z)
        self.next_workshop_id += 1
        self.workshops.append(ws)
        self.jobs.append(self._new_job(kind="build_workshop", labor="build", target_id=ws.id, remaining=6, destination=ws.pos))
        return ws

    def order_workshop(self, workshop_id: int, recipe: str, amount: int) -> None:
        ws = self._find_workshop(workshop_id)
        if not ws or not ws.built:
            raise ValueError("workshop not built")
        recipes = self.defs.get("recipes", {}).get(ws.kind, {})
        if recipe not in recipes:
            raise ValueError(f"recipe not available for {ws.kind}")
        if amount <= 0:
            raise ValueError("amount must be > 0")
        ws.orders[recipe] = ws.orders.get(recipe, 0) + amount

    def queue_dig(self, x: int, y: int, from_z: int, to_z: int) -> None:
        self._validate_point(x, y, from_z)
        self._validate_point(x, y, to_z)
        self.jobs.append(self._new_job(kind="dig_stairs", labor="mine", destination=(x, y, from_z), remaining=6, target_id=to_z))

    def tick(self, n: int = 1) -> None:
        for _ in range(n):
            self.tick_count += 1
            self._update_world_time_weather()
            self._grow_farms_and_ecosystems()
            self._update_threats_and_factions()
            self._update_needs_moods_stress()
            for dwarf in self.dwarves:
                if dwarf.hp <= 0:
                    continue
                if dwarf.job is None:
                    dwarf.job = self._assign_job(dwarf)
                self._perform_job_step(dwarf)
            self._social_tick()
            self._justice_tick()
            self._culture_tick()
            self._animal_tick()
            self._fluid_tick()
            self._item_tick()
            self._flora_tick()
            self._sync_carried_items()
            self._refresh_rooms_and_assignments()
            self.world.wealth = sum(i.value + i.quality for i in self.items)

    # Shared helpers for subsystems.
    def _find_zone(self, kind: str, z: Optional[int] = None) -> Optional[Zone]:
        return next((zz for zz in self.zones if zz.kind == kind and (z is None or zz.z == z)), None)

    def _find_workshop(self, workshop_id: Optional[int]) -> Optional[Workshop]:
        if workshop_id is None:
            return None
        return next((w for w in self.workshops if w.id == workshop_id), None)

    def _find_stockpile(self, stockpile_id: Optional[int]) -> Optional[Stockpile]:
        if stockpile_id is None:
            return None
        return next((s for s in self.stockpiles if s.id == stockpile_id), None)

    def _find_dwarf(self, dwarf_id: int) -> Optional[Dwarf]:
        return next((d for d in self.dwarves if d.id == dwarf_id), None)

    def _find_squad(self, squad_id: Optional[int]) -> Optional[Squad]:
        if squad_id is None:
            return None
        return next((s for s in self.squads if s.id == squad_id), None)

    def _find_faction(self, faction_id: int) -> Optional[Faction]:
        return next((f for f in self.factions if f.id == faction_id), None)

    def _find_item(self, kind: str) -> Optional[Item]:
        return next((i for i in self.items if i.kind == kind and i.reserved_by is None and i.carried_by is None), None)

    def _find_item_by_id(self, item_id: Optional[int]) -> Optional[Item]:
        if item_id is None:
            return None
        return next((i for i in self.items if i.id == item_id), None)

    def _find_farm_with_crops(self, z: Optional[int] = None) -> Optional[Zone]:
        return next((f for f in self.zones if f.kind == "farm" and f.crop_available > 0 and (z is None or f.z == z)), None)

    def _find_ordered_workshop_for_dwarf(self, dwarf: Dwarf) -> Tuple[Optional[Workshop], Optional[str]]:
        candidates = [
            w
            for w in self.workshops
            if w.built and w.z == dwarf.z and any(count > 0 for count in w.orders.values())
        ]
        if not candidates:
            return None, None
        scored: List[Tuple[int, Workshop]] = []
        for ws in candidates:
            labor = self._labor_for_workshop(ws.kind)
            if not self._labor_allowed(dwarf, labor):
                continue
            scored.append((dwarf.labor_priority.get(labor, 3), ws))
        if not scored:
            return None, None
        scored.sort(key=lambda t: t[0], reverse=True)
        for _, ws in scored:
            recipe = next((r for r, c in ws.orders.items() if c > 0), None)
            if recipe:
                ws.orders[recipe] -= 1
                return ws, recipe
        return None, None

    def _find_haul_candidate(self) -> Tuple[Optional[Item], Optional[Stockpile]]:
        for item in self.items:
            if item.reserved_by is not None or item.carried_by is not None:
                continue
            if item.stockpile_id is not None:
                continue
            stock = self._find_stockpile_for_item(item)
            if stock:
                return item, stock
        return None, None

    def _find_stockpile_for_item(self, item: Item) -> Optional[Stockpile]:
        for sp in self.stockpiles:
            if sp.accepts(item.kind) and self._stockpile_free_slots(sp) > 0 and sp.z == item.z:
                return sp
        return None

    def _stockpile_used_slots(self, stockpile: Stockpile) -> int:
        return sum(1 for i in self.items if i.stockpile_id == stockpile.id)

    def _stockpile_free_slots(self, stockpile: Stockpile) -> int:
        return stockpile.capacity - self._stockpile_used_slots(stockpile)

    def _choose_stockpile_drop_tile(self, stockpile: Stockpile) -> Coord3:
        best = (stockpile.x, stockpile.y, stockpile.z)
        best_load = 10**9
        for yy in range(stockpile.y, stockpile.y + stockpile.h):
            for xx in range(stockpile.x, stockpile.x + stockpile.w):
                load = sum(
                    1
                    for i in self.items
                    if i.stockpile_id == stockpile.id and i.x == xx and i.y == yy and i.z == stockpile.z
                )
                if load < best_load:
                    best_load = load
                    best = (xx, yy, stockpile.z)
        return best

    def _step_move_toward(self, dwarf: Dwarf, destination: Optional[Coord3]) -> None:
        if destination is None:
            if self.rng.random() < 0.5:
                nx = clamp(dwarf.x + self.rng.choice([-1, 0, 1]), 0, self.width - 1)
                ny = clamp(dwarf.y + self.rng.choice([-1, 0, 1]), 0, self.height - 1)
                dwarf.pos = (nx, ny, dwarf.z)
            return
        tx, ty, tz = destination
        if dwarf.z != tz:
            dwarf.z += 1 if tz > dwarf.z else -1
            return
        dx = 0 if tx == dwarf.x else (1 if tx > dwarf.x else -1)
        dy = 0 if ty == dwarf.y else (1 if ty > dwarf.y else -1)
        dwarf.pos = (clamp(dwarf.x + dx, 0, self.width - 1), clamp(dwarf.y + dy, 0, self.height - 1), dwarf.z)

    def _item_pos(self, item: Item) -> Coord3:
        if item.carried_by is not None:
            d = self._find_dwarf(item.carried_by)
            if d:
                return d.pos
        return (item.x, item.y, item.z)

    def _spawn_item(
        self,
        kind: str,
        x: int,
        y: int,
        z: int,
        material: str = "generic",
        quality: int = 0,
        value: int = 1,
        perishability: int = 0,
    ) -> Item:
        it = Item(
            id=self.next_item_id,
            kind=kind,
            x=x,
            y=y,
            z=z,
            material=material,
            quality=quality,
            value=value,
            perishability=perishability,
        )
        self.next_item_id += 1
        self.items.append(it)
        return it

    def _consume_item(self, item_id: int) -> None:
        self.items = [i for i in self.items if i.id != item_id]

    def _sync_carried_items(self) -> None:
        for i in self.items:
            if i.carried_by is None:
                continue
            d = self._find_dwarf(i.carried_by)
            if d:
                i.x, i.y, i.z = d.x, d.y, d.z

    def _log(self, kind: str, text: str, severity: int) -> None:
        e = Event(tick=self.tick_count, kind=kind, text=text, severity=severity)
        self.events.append(e)
        if len(self.events) > 400:
            self.events = self.events[-400:]
        if severity >= 2:
            self.alerts.append(f"t{self.tick_count} [{kind}] {text}")
            if len(self.alerts) > 200:
                self.alerts = self.alerts[-200:]

    def _validate_point(self, x: int, y: int, z: int) -> None:
        if not self._in_bounds(x, y, z):
            raise ValueError("point out of bounds")

    def _validate_rect(self, x: int, y: int, z: int, w: int, h: int) -> None:
        if w <= 0 or h <= 0:
            raise ValueError("w and h must be positive")
        if not (self._in_bounds(x, y, z) and self._in_bounds(x + w - 1, y + h - 1, z)):
            raise ValueError("rect out of bounds")

    def _in_bounds(self, x: int, y: int, z: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth

    def _effective_perishability(self, item: Item) -> int:
        if item.perishability <= 0:
            return 0
        effective = item.perishability
        sp = self._find_stockpile(item.stockpile_id)
        if sp:
            if sp.kind in {"raw", "cooked", "drink"}:
                effective = int(effective * 1.7)
            elif sp.kind == "general":
                effective = int(effective * 1.25)
            else:
                effective = int(effective * 1.1)
        else:
            effective = int(effective * 0.82)
            if self.world.weather in {"rain", "storm"}:
                effective = int(effective * 0.85)
            if self.world.temperature_c >= 24:
                effective = int(effective * 0.90)
        return max(1, effective)

    def _apply_nutrition_from_item(self, dwarf: Dwarf, item: Item) -> None:
        material = (item.material or "").lower()
        protein_gain = 8
        fiber_gain = 6
        variety_gain = 4
        if any(token in material for token in {"fish", "meat", "goat", "boar"}):
            protein_gain += 14
        if any(token in material for token in {"plump", "mushroom", "herb", "leaf"}):
            fiber_gain += 12
        if item.kind == "cooked_food":
            variety_gain += 8
        if item.quality >= 2:
            variety_gain += 5
        dwarf.nutrition["protein"] = clamp(dwarf.nutrition["protein"] - protein_gain, 0, 100)
        dwarf.nutrition["fiber"] = clamp(dwarf.nutrition["fiber"] - fiber_gain, 0, 100)
        dwarf.nutrition["variety"] = clamp(dwarf.nutrition["variety"] - variety_gain, 0, 100)


__all__ = ["Game", "help_text"]
