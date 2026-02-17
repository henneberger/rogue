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

        for fl in self.floras:
            if fl.z != z or not self._in_bounds(fl.x, fl.y, z):
                continue
            grid[fl.y][fl.x] = self._flora_glyph(fl)

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
                "timber": "L",
                "herb": "h",
                "berry": "b",
                "rare_plant": "r",
                "manuscript": "M",
                "performance_record": "P",
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
            f"food raw={self.raw_food} cooked={self.cooked_food} drink={self.drinks} flora={len(self.floras)} wealth={self.world.wealth} raid={self.world.raid_active}",
            'Legend: D dwarf, a animal, workshops (lower=construction upper=built), f/r/t/d/h/p/b zones, stockpiles s c q m g u + S, flora , ; " * + t y T Y A x, items R C A W O E F H B * L h b r M P',
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
            nutrition = ",".join(f"{k[:2]}={v}" for k, v in d.nutrition.items())
            room_value = self._dwarf_room_value(d.id)
            lines.append(
                f"  [{d.id}] {d.name} ({d.x},{d.y},{d.z}) hp={d.hp} morale={d.morale} stress={d.stress} mood={d.mood} state={state} room={d.assigned_room_id} room_value={room_value} rested_bonus={d.rested_bonus} dep={d.alcohol_dependency} wd={d.withdrawal_ticks} needs[{needs}] nutrition[{nutrition}]"
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
        lines.append(f"Rooms: {len(self.rooms)}")
        lines.append(f"Flora: {len(self.floras)}")
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
            active_mandates = [m for m in self.mandates if not m.fulfilled and not m.failed]
            timber_materials: Dict[str, int] = {}
            for item in self.items:
                if item.kind != "timber":
                    continue
                timber_materials[item.material] = timber_materials.get(item.material, 0) + 1
            timber_top = ", ".join(
                f"{mat}={count}" for mat, count in sorted(timber_materials.items(), key=lambda kv: kv[1], reverse=True)[:4]
            )
            timber_top = timber_top or "none"
            rep_gain = self.economy_stats.get("mandate_reputation_gained", 0)
            rep_loss = self.economy_stats.get("mandate_reputation_lost", 0)
            return (
                f"world={self.world.world_name} fortress_region={self.world.fortress_region_id}\n"
                f"day={self.world.day} season={self.world.season} weather={self.world.weather} temp={self.world.temperature_c}C\n"
                f"biome={self.world.biome} wealth={self.world.wealth}\n"
                f"water_pressure={self.world.water_pressure} magma_pressure={self.world.magma_pressure}\n"
                f"raid_active={self.world.raid_active} threat={self.world.threat_level}\n"
                f"regions={len(self.regions)} history_events={len(self.world_history)}\n"
                f"timber_harvested={self.economy_stats.get('timber_harvested', 0)} forage_total={self.economy_stats.get('foraged_herb', 0) + self.economy_stats.get('foraged_berry', 0) + self.economy_stats.get('foraged_fiber', 0) + self.economy_stats.get('foraged_rare', 0)} active_mandates={len(active_mandates)}\n"
                f"timber_species={timber_top}\n"
                f"mandate_trade_impact=wealth+{self.economy_stats.get('mandate_wealth_earned', 0)} rep+{rep_gain} rep-{rep_loss}"
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
            lines = [
                f"culture_points={self.world.culture_points} scholarly_points={self.world.scholarly_points}",
                f"cultural_goods_created={self.economy_stats.get('cultural_goods_created', 0)}",
                "Mandates:",
            ]
            mandates = sorted(
                self.mandates,
                key=lambda m: (m.fulfilled or m.failed, m.due_tick),
            )[:12]
            if mandates:
                for m in mandates:
                    status = "fulfilled" if m.fulfilled else ("failed" if m.failed else "active")
                    issuer = self._find_faction(m.issuer_faction_id)
                    issuer_name = issuer.name if issuer else f"Faction#{m.issuer_faction_id}"
                    lines.append(
                        f"  [{m.id}] {status} issuer={issuer_name} kind={m.kind} item={m.requested_item_kind} progress={m.delivered_amount}/{m.requested_amount} due=t{m.due_tick}"
                    )
            else:
                lines.append("  none")
            return "\n".join(lines)
        if name == "dwarves":
            lines = []
            for d in self.dwarves:
                rel = sorted(d.relationships.items(), key=lambda kv: kv[1], reverse=True)[:3]
                lines.append(
                    f"[{d.id}] {d.name} room={d.assigned_room_id} room_value={self._dwarf_room_value(d.id)} rested_bonus={d.rested_bonus} dep={d.alcohol_dependency} wd={d.withdrawal_ticks} nutrition={d.nutrition} skill_top={self._top_skills(d)} rel_top={rel} memories={d.memories[-2:]}"
                )
            return "\n".join(lines)
        if name == "flora":
            if not self.floras:
                return "no flora"
            stage_counts: Dict[str, int] = {}
            species_counts: Dict[str, int] = {}
            timber_species: Dict[str, int] = {}
            stress = 0
            dormant = 0
            dead = 0
            for fl in self.floras:
                stage_counts[fl.stage] = stage_counts.get(fl.stage, 0) + 1
                label = f"{fl.common_name} ({fl.scientific_name})"
                species_counts[label] = species_counts.get(label, 0) + 1
                stress += 1 if fl.stressed else 0
                dormant += 1 if fl.dormant else 0
                dead += 1 if fl.dead else 0
            for item in self.items:
                if item.kind != "timber":
                    continue
                timber_species[item.material] = timber_species.get(item.material, 0) + 1
            lines = [
                f"Flora Summary: total={len(self.floras)} stressed={stress} dormant={dormant} dead={dead}",
                "Stages: " + ", ".join(f"{k}={v}" for k, v in sorted(stage_counts.items())),
                "Yields: "
                + ", ".join(
                    [
                        f"herb={self.economy_stats.get('foraged_herb', 0)}",
                        f"berry={self.economy_stats.get('foraged_berry', 0)}",
                        f"fiber={self.economy_stats.get('foraged_fiber', 0)}",
                        f"rare={self.economy_stats.get('foraged_rare', 0)}",
                        f"timber={self.economy_stats.get('timber_harvested', 0)}",
                    ]
                ),
                (
                    "Timber species (stock): "
                    + ", ".join(f"{mat}={count}" for mat, count in sorted(timber_species.items(), key=lambda kv: kv[1], reverse=True)[:4])
                )
                if timber_species
                else "Timber species (stock): none",
                "Species (top 12):",
            ]
            for label, count in sorted(species_counts.items(), key=lambda kv: kv[1], reverse=True)[:12]:
                lines.append(f"  {label}: {count}")
            lines.append("Recent flora events:")
            flora_events = [e for e in self.events if e.kind == "flora"][-8:]
            if flora_events:
                for e in flora_events:
                    lines.append(f"  t{e.tick} {e.text}")
            else:
                lines.append("  none")
            return "\n".join(lines)
        if name == "rooms":
            lines = ["Rooms:"]
            for room in sorted(self.rooms, key=lambda r: (r.value, r.id), reverse=True):
                lines.append(
                    f"[{room.id}] {room.kind} ({room.x},{room.y},{room.z},{room.w},{room.h}) value={room.value} bed={room.bed_item_id} assigned={room.assigned_dwarf_id}"
                )
            return "\n".join(lines) if len(lines) > 1 else "no rooms"
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
