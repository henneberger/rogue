from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import random

from fortress.io.commands import CommandMixin, help_text
from fortress.io.persistence import PersistenceMixin
from fortress.io.render import RenderMixin
from fortress.models import (
    Animal,
    Crime,
    Dwarf,
    Event,
    Faction,
    Flora,
    HistoricalEvent,
    Item,
    Job,
    LABORS,
    Mandate,
    Region,
    Room,
    Squad,
    Stockpile,
    WorldState,
    Workshop,
    Zone,
)
from fortress.systems.jobs import JobSystemsMixin
from fortress.systems.justice import JusticeSystemsMixin
from fortress.systems.needs import NeedsSystemsMixin
from fortress.systems.social import SocialSystemsMixin
from fortress.systems.world import WorldSystemsMixin
from fortress.systems.architecture import ArchitectureSystemsMixin
from fortress.systems.flora import FloraSystemsMixin
from fortress.systems.defs import DefsMixin
from fortress.systems.worldgen import WorldgenMixin
from fortress.systems.game_helpers import GameHelpersMixin


@dataclass
class Game(
    CommandMixin,
    PersistenceMixin,
    RenderMixin,
    DefsMixin,
    WorldgenMixin,
    GameHelpersMixin,
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
    next_mandate_id: int = 1
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
    mandates: List[Mandate] = field(default_factory=list)
    crimes: List[Crime] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    jobs: List[Job] = field(default_factory=list)
    world: WorldState = field(default_factory=WorldState)
    command_log: List[str] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    economy_stats: Dict[str, int] = field(
        default_factory=lambda: {
            "foraged_herb": 0,
            "foraged_berry": 0,
            "foraged_fiber": 0,
            "foraged_rare": 0,
            "timber_harvested": 0,
            "trees_felled_recent": 0,
            "cultural_goods_created": 0,
            "mandates_fulfilled": 0,
            "mandates_failed": 0,
            "mandate_wealth_earned": 0,
            "mandate_reputation_gained": 0,
            "mandate_reputation_lost": 0,
        }
    )
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
        if kind not in {"raw", "cooked", "drink", "food", "materials", "goods", "medical", "furniture", "general"}:
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
            self._economy_tick()
            self._sync_carried_items()
            self._refresh_rooms_and_assignments()
            self.world.wealth = sum(i.value + i.quality for i in self.items)

__all__ = ["Game", "help_text"]
