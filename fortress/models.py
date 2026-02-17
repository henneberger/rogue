from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import random


Coord3 = Tuple[int, int, int]


LABORS = {
    "build",
    "harvest",
    "haul",
    "cook",
    "brew",
    "mine",
    "craft",
    "medical",
    "combat",
    "recreate",
    "social",
    "worship",
    "sleep",
}

CONTAINER_CAPACITY: Dict[str, int] = {
    "chest": 8,
    "barrel": 12,
    "bin": 14,
    "crate": 16,
    "bag": 8,
}


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


@dataclass
class Zone:
    id: int
    kind: str  # farm recreation temple dormitory hospital pasture burrow
    x: int
    y: int
    z: int
    w: int
    h: int
    crop_available: int = 0
    crop_max: int = 8

    def contains(self, pos: Coord3) -> bool:
        px, py, pz = pos
        return pz == self.z and self.x <= px < self.x + self.w and self.y <= py < self.y + self.h

    def random_tile(self, rng: random.Random) -> Coord3:
        return (
            rng.randint(self.x, self.x + self.w - 1),
            rng.randint(self.y, self.y + self.h - 1),
            self.z,
        )


@dataclass
class Stockpile:
    id: int
    kind: str  # raw cooked drink materials goods medical furniture general
    x: int
    y: int
    z: int
    w: int
    h: int

    def contains(self, pos: Coord3) -> bool:
        px, py, pz = pos
        return pz == self.z and self.x <= px < self.x + self.w and self.y <= py < self.y + self.h

    def accepts(self, item_kind: str) -> bool:
        cat = item_category(item_kind)
        if self.kind == "general":
            return True
        if self.kind == "food":
            return cat in {"raw", "cooked", "drink"}
        return self.kind == cat

    @property
    def capacity(self) -> int:
        return self.w * self.h


@dataclass
class Workshop:
    id: int
    kind: str  # kitchen brewery carpenter mason craftdwarf smithy loom leatherworks
    x: int
    y: int
    z: int
    built: bool = False
    orders: Dict[str, int] = field(default_factory=dict)

    @property
    def pos(self) -> Coord3:
        return (self.x, self.y, self.z)


@dataclass
class Item:
    id: int
    kind: str
    x: int
    y: int
    z: int
    material: str = "plant"
    quality: int = 0
    value: int = 1
    perishability: int = 0  # 0 = stable, >0 spoils slower with smaller values
    age: int = 0
    owner_id: Optional[int] = None
    stockpile_id: Optional[int] = None
    carried_by: Optional[int] = None
    reserved_by: Optional[int] = None
    container_id: Optional[int] = None


@dataclass
class Job:
    id: int
    kind: str
    labor: str
    target_id: Optional[int] = None
    item_id: Optional[int] = None
    recipe: Optional[str] = None
    destination: Optional[Coord3] = None
    remaining: int = 1
    phase: str = ""
    container_id: Optional[int] = None


@dataclass
class Dwarf:
    id: int
    name: str
    x: int
    y: int
    z: int
    morale: int = 70
    stress: int = 10
    mood: str = "steady"
    hp: int = 100
    wounds: List[str] = field(default_factory=list)
    skills: Dict[str, int] = field(default_factory=dict)
    labor_priority: Dict[str, int] = field(default_factory=dict)
    allowed_labors: Set[str] = field(default_factory=lambda: set(LABORS))
    needs: Dict[str, int] = field(
        default_factory=lambda: {
            "hunger": 20,
            "thirst": 20,
            "alcohol": 20,
            "sleep": 15,
            "social": 15,
            "worship": 20,
            "entertainment": 15,
            "safety": 20,
        }
    )
    nutrition: Dict[str, int] = field(
        default_factory=lambda: {
            "protein": 30,
            "fiber": 30,
            "variety": 35,
        }
    )
    alcohol_dependency: int = 55
    withdrawal_ticks: int = 0
    religion: str = "The Forge Ancestors"
    memories: List[str] = field(default_factory=list)
    relationships: Dict[int, int] = field(default_factory=dict)
    squad_id: Optional[int] = None
    assigned_room_id: Optional[int] = None
    rested_bonus: int = 0
    job: Optional[Job] = None
    state: str = "idle"

    @property
    def pos(self) -> Coord3:
        return (self.x, self.y, self.z)

    @pos.setter
    def pos(self, value: Coord3) -> None:
        self.x, self.y, self.z = value


@dataclass
class Animal:
    id: int
    species: str
    x: int
    y: int
    z: int
    hunger: int = 20
    tame: bool = True

    @property
    def pos(self) -> Coord3:
        return (self.x, self.y, self.z)


@dataclass
class Squad:
    id: int
    name: str
    members: List[int] = field(default_factory=list)
    training: int = 0


@dataclass
class Faction:
    id: int
    name: str
    stance: str = "neutral"  # allied neutral hostile
    reputation: int = 0
    home_region_id: Optional[int] = None
    civ_type: str = "kingdom"


@dataclass
class Crime:
    id: int
    tick: int
    dwarf_id: int
    kind: str
    resolved: bool = False


@dataclass
class Event:
    tick: int
    kind: str
    text: str
    severity: int = 1


@dataclass
class Region:
    id: int
    name: str
    biome: str
    rainfall: str
    temperature_band: str
    elevation: str
    resources: List[str] = field(default_factory=list)
    neighbors: List[int] = field(default_factory=list)


@dataclass
class HistoricalEvent:
    year: int
    event_type: str
    actor: str
    target: str
    delta_reputation: int
    text: str


@dataclass
class Room:
    id: int
    kind: str  # bedroom | dormitory | hall
    x: int
    y: int
    z: int
    w: int
    h: int
    value: int = 0
    bed_item_id: Optional[int] = None
    assigned_dwarf_id: Optional[int] = None

    def contains(self, pos: Coord3) -> bool:
        px, py, pz = pos
        return pz == self.z and self.x <= px < self.x + self.w and self.y <= py < self.y + self.h


@dataclass
class Flora:
    id: int
    species_id: str
    common_name: str
    scientific_name: str
    kind: str  # plant | tree
    x: int
    y: int
    z: int
    stage: str
    growth_points: int = 0
    age_ticks: int = 0
    health: int = 100
    dormant: bool = False
    stressed: bool = False
    dead: bool = False
    spread_cooldown: int = 0
    reserved_by: Optional[int] = None

    @property
    def pos(self) -> Coord3:
        return (self.x, self.y, self.z)


@dataclass
class WorldState:
    world_name: str = "Unnamed World"
    day: int = 1
    season: str = "spring"
    weather: str = "clear"
    temperature_c: int = 12
    biome: str = "temperate-forest"
    fortress_region_id: int = 1
    wealth: int = 0
    water_pressure: int = 0
    magma_pressure: int = 0
    threat_level: int = 0
    raid_active: bool = False
    scholarly_points: int = 0
    culture_points: int = 0


@dataclass
class Mandate:
    id: int
    issuer_faction_id: int
    kind: str  # ecology | timber | culture
    requested_item_kind: str
    requested_amount: int
    delivered_amount: int = 0
    due_tick: int = 0
    reward_reputation: int = 6
    reward_wealth: int = 20
    penalty_reputation: int = 5
    fulfilled: bool = False
    failed: bool = False


def item_category(kind: str) -> str:
    if kind in {"raw_food", "herb", "berry", "rare_plant"}:
        return "raw"
    if kind in {"seed"}:
        return "raw"
    if kind in {"cooked_food"}:
        return "cooked"
    if kind in {"alcohol"}:
        return "drink"
    if kind in {
        "wood",
        "stone",
        "ore",
        "fiber",
        "hide",
        "timber",
        "leather",
        "flour",
        "metal_bar",
        "mechanism",
        "ash",
        "dye",
        "paper_sheet",
    }:
        return "materials"
    if kind in {"barrel", "bin", "crate", "bag"}:
        return "materials"
    if kind in {"chest"}:
        return "furniture"
    if kind in {
        "craft_good",
        "artifact",
        "manuscript",
        "performance_record",
        "weapon",
        "armor",
        "tool",
        "gem_cut",
        "siege_part",
        "soap",
        "pottery",
        "ammo",
    }:
        return "goods"
    if kind in {"bandage", "medicine"}:
        return "medical"
    if kind in {"bed", "chair", "table"}:
        return "furniture"
    return "general"


def is_container_kind(kind: str) -> bool:
    return kind in CONTAINER_CAPACITY
