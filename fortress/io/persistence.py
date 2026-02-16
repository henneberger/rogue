from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List
import json

from fortress.models import (
    Animal,
    Crime,
    Dwarf,
    Event,
    Faction,
    HistoricalEvent,
    Item,
    Job,
    Region,
    Room,
    Squad,
    Stockpile,
    WorldState,
    Workshop,
    Zone,
)


class PersistenceMixin:
    def save_json(self, path: str) -> None:
        payload = {
            "meta": {"rng_seed": self.rng_seed, "tick": self.tick_count, "selected_z": self.selected_z},
            "world": asdict(self.world),
            "zones": [asdict(z) for z in self.zones],
            "stockpiles": [asdict(s) for s in self.stockpiles],
            "workshops": [asdict(w) for w in self.workshops],
            "items": [asdict(i) for i in self.items],
            "dwarves": [
                {
                    **asdict(d),
                    "allowed_labors": sorted(list(d.allowed_labors)),
                }
                for d in self.dwarves
            ],
            "animals": [asdict(a) for a in self.animals],
            "squads": [asdict(s) for s in self.squads],
            "factions": [asdict(f) for f in self.factions],
            "regions": [asdict(r) for r in self.regions],
            "world_history": [asdict(h) for h in self.world_history],
            "rooms": [asdict(r) for r in self.rooms],
            "crimes": [asdict(c) for c in self.crimes],
            "events": [asdict(e) for e in self.events],
            "jobs": [asdict(j) for j in self.jobs],
            "counters": {
                "next_zone_id": self.next_zone_id,
                "next_stockpile_id": self.next_stockpile_id,
                "next_workshop_id": self.next_workshop_id,
                "next_item_id": self.next_item_id,
                "next_dwarf_id": self.next_dwarf_id,
                "next_animal_id": self.next_animal_id,
                "next_squad_id": self.next_squad_id,
                "next_faction_id": self.next_faction_id,
                "next_job_id": self.next_job_id,
                "next_crime_id": self.next_crime_id,
                "next_room_id": self.next_room_id,
            },
            "command_log": self.command_log,
            "defs": self.defs,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    @classmethod
    def load_json(cls, path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        g = cls(rng_seed=data["meta"]["rng_seed"])
        g.tick_count = data["meta"]["tick"]
        g.selected_z = data["meta"].get("selected_z", 0)
        g.world = WorldState(**data["world"])
        g.zones = [Zone(**z) for z in data["zones"]]
        g.stockpiles = [Stockpile(**s) for s in data["stockpiles"]]
        g.workshops = [Workshop(**w) for w in data["workshops"]]
        g.items = [Item(**i) for i in data["items"]]
        g.dwarves = []
        for dd in data["dwarves"]:
            dd["allowed_labors"] = set(dd.get("allowed_labors", []))
            needs = dd.get("needs", {})
            needs.setdefault("hunger", 20)
            needs.setdefault("thirst", 20)
            needs.setdefault("alcohol", 20)
            needs.setdefault("sleep", 15)
            needs.setdefault("social", 15)
            needs.setdefault("worship", 20)
            needs.setdefault("entertainment", 15)
            needs.setdefault("safety", 20)
            dd["needs"] = needs
            nutrition = dd.get("nutrition", {})
            nutrition.setdefault("protein", 30)
            nutrition.setdefault("fiber", 30)
            nutrition.setdefault("variety", 35)
            dd["nutrition"] = nutrition
            dd.setdefault("alcohol_dependency", 55)
            dd.setdefault("withdrawal_ticks", 0)
            if isinstance(dd.get("job"), dict):
                dd["job"] = Job(**dd["job"])
            rel = dd.get("relationships", {})
            if isinstance(rel, dict):
                dd["relationships"] = {int(k): int(v) for k, v in rel.items()}
            g.dwarves.append(Dwarf(**dd))
        g.animals = [Animal(**a) for a in data["animals"]]
        g.squads = [Squad(**s) for s in data["squads"]]
        g.factions = [Faction(**f) for f in data["factions"]]
        g.regions = [Region(**r) for r in data.get("regions", [])]
        g.world_history = [HistoricalEvent(**h) for h in data.get("world_history", [])]
        g.rooms = [Room(**r) for r in data.get("rooms", [])]
        g.crimes = [Crime(**c) for c in data["crimes"]]
        g.events = [Event(**e) for e in data["events"]]
        g.jobs = [Job(**j) for j in data["jobs"]]
        counters = data["counters"]
        g.next_zone_id = counters["next_zone_id"]
        g.next_stockpile_id = counters["next_stockpile_id"]
        g.next_workshop_id = counters["next_workshop_id"]
        g.next_item_id = counters["next_item_id"]
        g.next_dwarf_id = counters["next_dwarf_id"]
        g.next_animal_id = counters["next_animal_id"]
        g.next_squad_id = counters["next_squad_id"]
        g.next_faction_id = counters["next_faction_id"]
        g.next_job_id = counters["next_job_id"]
        g.next_crime_id = counters["next_crime_id"]
        g.next_room_id = counters.get("next_room_id", 1)
        g.command_log = data.get("command_log", [])
        g.defs = data.get("defs", g.default_defs())
        g._refresh_rooms_and_assignments()
        return g

    def load_defs(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            patch = json.load(f)
        self.defs = deep_merge(self.defs, patch)

    def export_replay(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for line in self.command_log:
                f.write(line + "\n")

    def run_script(self, path: str) -> List[str]:
        outputs: List[str] = []
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                out = self.handle_command(line)
                if out:
                    outputs.append(out)
        return outputs


def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out
