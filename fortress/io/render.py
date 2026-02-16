from __future__ import annotations

from typing import Dict, Optional


class RenderMixin:
    def render(self, z: Optional[int] = None) -> str:
        z = self.selected_z if z is None else z
        grid = [["." for _ in range(self.width)] for _ in range(self.height)]

        for zone in self.zones:
            if zone.z != z:
                continue
            ch = {
                "farm": "f",
                "recreation": "r",
                "temple": "t",
                "dormitory": "d",
                "hospital": "h",
                "pasture": "p",
                "burrow": "b",
            }.get(zone.kind, "z")
            for yy in range(zone.y, zone.y + zone.h):
                for xx in range(zone.x, zone.x + zone.w):
                    if self._in_bounds(xx, yy, z):
                        grid[yy][xx] = ch

        for sp in self.stockpiles:
            if sp.z != z:
                continue
            ch = {
                "raw": "s",
                "cooked": "c",
                "drink": "q",
                "materials": "m",
                "goods": "g",
                "furniture": "u",
                "medical": "+",
                "general": "S",
            }.get(sp.kind, "S")
            for yy in range(sp.y, sp.y + sp.h):
                for xx in range(sp.x, sp.x + sp.w):
                    if self._in_bounds(xx, yy, z):
                        grid[yy][xx] = ch

        for ws in self.workshops:
            if ws.z != z:
                continue
            ch = ws.kind[0].upper() if ws.built else ws.kind[0]
            if self._in_bounds(ws.x, ws.y, z):
                grid[ws.y][ws.x] = ch

        for item in self.items:
            ix, iy, iz = self._item_pos(item)
            if iz != z or not self._in_bounds(ix, iy, iz):
                continue
            ch = {
                "raw_food": "R",
                "cooked_food": "C",
                "alcohol": "A",
                "wood": "W",
                "stone": "O",
                "ore": "E",
                "fiber": "F",
                "hide": "H",
                "bed": "B",
                "artifact": "*",
            }.get(item.kind, "i")
            grid[iy][ix] = ch

        for a in self.animals:
            if a.z == z and self._in_bounds(a.x, a.y, z):
                grid[a.y][a.x] = "a"

        for d in self.dwarves:
            if d.z == z and d.hp > 0 and self._in_bounds(d.x, d.y, z):
                grid[d.y][d.x] = "D"

        lines = [
            f"Tick {self.tick_count} | z={z} | day={self.world.day} {self.world.season} | weather={self.world.weather} temp={self.world.temperature_c}C",
            f"food raw={self.raw_food} cooked={self.cooked_food} drink={self.drinks} wealth={self.world.wealth} raid={self.world.raid_active}",
            "Legend: D dwarf, a animal, workshops (lower=construction upper=built), f/r/t/d/h/p/b zones, stockpiles s c q m g u + S, items R C A W O E F H B *",
        ]
        lines.extend("".join(row) for row in grid)
        return "\n".join(lines)

    def status(self) -> str:
        alive = [d for d in self.dwarves if d.hp > 0]
        lines = [
            f"Tick {self.tick_count} day={self.world.day} season={self.world.season} weather={self.world.weather} temp={self.world.temperature_c}C z={self.selected_z}",
            f"World: {self.world.world_name} region={self.world.fortress_region_id}",
            f"Resources: raw={self.raw_food} cooked={self.cooked_food} drink={self.drinks} items={len(self.items)} wealth={self.world.wealth}",
            f"Threat: raid_active={self.world.raid_active} level={self.world.threat_level} squads={len(self.squads)}",
            f"Population: dwarves={len(alive)}/{len(self.dwarves)} animals={len(self.animals)}",
            f"Knowledge: scholarly={self.world.scholarly_points} culture={self.world.culture_points}",
            "Dwarves:",
        ]
        for d in self.dwarves:
            state = d.job.kind if d.job else "idle"
            needs = ",".join(f"{k[:2]}={v}" for k, v in d.needs.items())
            lines.append(
                f"  [{d.id}] {d.name} ({d.x},{d.y},{d.z}) hp={d.hp} morale={d.morale} stress={d.stress} mood={d.mood} state={state} needs[{needs}]"
            )
        lines.append("Workshops:")
        for ws in self.workshops:
            lines.append(f"  [{ws.id}] {ws.kind} ({ws.x},{ws.y},{ws.z}) built={ws.built} orders={ws.orders}")
        lines.append("Zones:")
        for z in self.zones:
            extra = f" crop={z.crop_available}/{z.crop_max}" if z.kind == "farm" else ""
            lines.append(f"  [{z.id}] {z.kind} ({z.x},{z.y},{z.z},{z.w},{z.h}){extra}")
        lines.append("Stockpiles:")
        for sp in self.stockpiles:
            lines.append(
                f"  [{sp.id}] {sp.kind} ({sp.x},{sp.y},{sp.z},{sp.w},{sp.h}) used={self._stockpile_used_slots(sp)}/{sp.capacity}"
            )
        lines.append("Factions:")
        for f in self.factions:
            lines.append(
                f"  [{f.id}] {f.name} stance={f.stance} rep={f.reputation} home_region={f.home_region_id} type={f.civ_type}"
            )
        unresolved = len([c for c in self.crimes if not c.resolved])
        lines.append(f"Justice: crimes={len(self.crimes)} unresolved={unresolved}")
        return "\n".join(lines)

    def panel(self, name: str) -> str:
        name = name.lower()
        if name == "world":
            return (
                f"world={self.world.world_name} fortress_region={self.world.fortress_region_id}\n"
                f"day={self.world.day} season={self.world.season} weather={self.world.weather} temp={self.world.temperature_c}C\n"
                f"biome={self.world.biome} wealth={self.world.wealth}\n"
                f"water_pressure={self.world.water_pressure} magma_pressure={self.world.magma_pressure}\n"
                f"raid_active={self.world.raid_active} threat={self.world.threat_level}\n"
                f"regions={len(self.regions)} history_events={len(self.world_history)}"
            )
        if name == "worldgen":
            lines = [
                f"World: {self.world.world_name} (seed={self.rng_seed})",
                f"Fortress Region: {self.world.fortress_region_id}",
                "Regions:",
            ]
            for region in self.regions:
                lines.append(
                    f"  [{region.id}] {region.name} biome={region.biome} rain={region.rainfall} temp={region.temperature_band} elev={region.elevation} neighbors={region.neighbors} resources={region.resources}"
                )
            lines.append("Historical Events:")
            for ev in self.world_history[-10:]:
                lines.append(
                    f"  y{ev.year}: {ev.actor} -> {ev.target} {ev.event_type} ({ev.delta_reputation:+d})"
                )
            return "\n".join(lines)
        if name == "jobs":
            lines = ["Global queued jobs:"]
            for j in self.jobs:
                lines.append(f"[{j.id}] {j.kind} labor={j.labor} target={j.target_id} rem={j.remaining}")
            lines.append("Assigned jobs:")
            for d in self.dwarves:
                if d.job:
                    lines.append(f"D{d.id} -> [{d.job.id}] {d.job.kind} phase={d.job.phase} rem={d.job.remaining}")
            return "\n".join(lines)
        if name == "stocks":
            counts: Dict[str, int] = {}
            for i in self.items:
                counts[i.kind] = counts.get(i.kind, 0) + 1
            return "\n".join(f"{k}: {v}" for k, v in sorted(counts.items()))
        if name == "events":
            return "\n".join(f"t{e.tick} [{e.kind}] sev={e.severity} {e.text}" for e in self.events[-20:])
        if name == "factions":
            return "\n".join(
                f"[{f.id}] {f.name}: {f.stance} rep={f.reputation} home_region={f.home_region_id} type={f.civ_type}"
                for f in self.factions
            )
        if name == "squads":
            return "\n".join(f"[{s.id}] {s.name}: members={s.members} training={s.training}" for s in self.squads) or "no squads"
        if name == "justice":
            return "\n".join(
                f"[{c.id}] t{c.tick} dwarf={c.dwarf_id} {c.kind} resolved={c.resolved}" for c in self.crimes[-20:]
            ) or "no crimes"
        if name == "culture":
            return f"culture_points={self.world.culture_points} scholarly_points={self.world.scholarly_points}"
        if name == "dwarves":
            lines = []
            for d in self.dwarves:
                rel = sorted(d.relationships.items(), key=lambda kv: kv[1], reverse=True)[:3]
                lines.append(f"[{d.id}] {d.name} skill_top={self._top_skills(d)} rel_top={rel} memories={d.memories[-2:]}")
            return "\n".join(lines)
        return "unknown panel"

    def items_dump(self) -> str:
        lines = []
        for i in self.items:
            x, y, z = self._item_pos(i)
            lines.append(
                f"[{i.id}] {i.kind} ({x},{y},{z}) mat={i.material} q={i.quality} v={i.value} age={i.age}/{i.perishability} stock={i.stockpile_id} carried={i.carried_by} reserved={i.reserved_by}"
            )
        return "\n".join(lines)

    def alerts_dump(self) -> str:
        return "\n".join(self.alerts[-20:]) or "no alerts"
