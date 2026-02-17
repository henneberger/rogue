from __future__ import annotations

from typing import Dict, Optional


class RenderMixin:
    def render_geology(self, z: Optional[int] = None) -> str:
        z = self.selected_z if z is None else z
        grid = [["#" for _ in range(self.width)] for _ in range(self.height)]
        reveal = self.debug_reveal_all_geology

        for x, y, cz in self.geology_cavern_tiles:
            if cz != z or not self._in_bounds(x, y, z):
                continue
            if reveal or (x, y, z) in self.geology_breached_tiles:
                grid[y][x] = "!" if (x, y, z) in self.geology_breached_tiles else "~"

        for dep in self.geology_deposits:
            if dep.z != z or not self._in_bounds(dep.x, dep.y, z):
                continue
            visible = reveal or dep.discovered
            if dep.remaining_yield <= 0:
                ch = "x" if visible else "#"
            elif not visible:
                ch = "#"
            elif dep.kind == "ore":
                ch = "E"
            else:
                ch = "J"
            grid[dep.y][dep.x] = ch

        for d in self.dwarves:
            if d.z == z and d.hp > 0 and self._in_bounds(d.x, d.y, z):
                grid[d.y][d.x] = "D"

        stratum = self.geology_strata.get(z, "unknown")
        lines = [
            f"Geology Overlay | z={z} stratum={stratum} reveal_all={self.debug_reveal_all_geology}",
            "Legend: # hidden rock, E discovered ore, J discovered gem, ~ cavern, ! breached cavern, x depleted, D dwarf",
        ]
        lines.extend("".join(row) for row in grid)
        return "\n".join(lines)

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
                "food": "k",
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
                "gem": "J",
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
                "chest": "X",
                "barrel": "U",
                "bin": "N",
                "crate": "Q",
                "bag": "G",
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
            'Legend: D dwarf, a animal, workshops (lower=construction upper=built), f/r/t/d/h/p/b zones, stockpiles s c q k m g u + S, flora , ; " * + t y T Y A x, items R C A W O E J F H B * L h b r M P X U N Q G',
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
            loose_counts: Dict[str, int] = {}
            contained_counts: Dict[str, int] = {}
            for i in self.items:
                counts[i.kind] = counts.get(i.kind, 0) + 1
                if i.container_id is None:
                    loose_counts[i.kind] = loose_counts.get(i.kind, 0) + 1
                else:
                    contained_counts[i.kind] = contained_counts.get(i.kind, 0) + 1
            lines = []
            for k in sorted(counts.keys()):
                lines.append(
                    f"{k}: total={counts[k]} loose={loose_counts.get(k, 0)} contained={contained_counts.get(k, 0)}"
                )
            lines.append("Containers:")
            for i in sorted(self.items, key=lambda x: x.id):
                if i.kind not in {"chest", "barrel", "bin", "crate", "bag"}:
                    continue
                used = sum(1 for x in self.items if x.container_id == i.id)
                lines.append(
                    f"  [{i.id}] {i.kind} stockpile={i.stockpile_id} load={used} mat={i.material}"
                )
            return "\n".join(lines)
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
        if name == "geology":
            discovered = [d for d in self.geology_deposits if d.discovered]
            remaining = [d for d in self.geology_deposits if d.remaining_yield > 0]
            ore_keys = sorted(k for k in self.economy_stats if k.startswith("geology_extracted_ore_"))
            gem_keys = sorted(k for k in self.economy_stats if k.startswith("geology_extracted_gem_"))
            depth_keys = sorted(k for k in self.economy_stats if k.startswith("geology_depth_") and k.endswith("_extracted"))
            lines = [
                "Geology:",
                "  strata=" + ", ".join(f"z{z}:{name}" for z, name in sorted(self.geology_strata.items())),
                f"  deposits_total={len(self.geology_deposits)} discovered={len(discovered)} remaining={len(remaining)}",
                f"  caverns_tiles={len(self.geology_cavern_tiles)} breached={len(self.geology_breached_tiles)}",
            ]
            if ore_keys:
                lines.append("  extracted_ore=" + ", ".join(f"{k.replace('geology_extracted_ore_', '')}:{self.economy_stats[k]}" for k in ore_keys))
            else:
                lines.append("  extracted_ore=none")
            if gem_keys:
                lines.append("  extracted_gem=" + ", ".join(f"{k.replace('geology_extracted_gem_', '')}:{self.economy_stats[k]}" for k in gem_keys))
            else:
                lines.append("  extracted_gem=none")
            if depth_keys:
                lines.append("  depth_activity=" + ", ".join(f"z{k.split('_')[2]}:{self.economy_stats[k]}" for k in depth_keys))
            if discovered:
                lines.append("  known_deposits:")
                for d in sorted(discovered, key=lambda dep: (dep.z, dep.id))[:10]:
                    lines.append(
                        f"    [{d.id}] {d.kind} {d.material} rarity={d.rarity} at ({d.x},{d.y},{d.z}) rem={d.remaining_yield}/{d.total_yield}"
                    )
            return "\n".join(lines)
        return "unknown panel"

    def prospect(self, x: int, y: int, z: int) -> str:
        self._validate_point(x, y, z)
        dep = next((d for d in self.geology_deposits if d.x == x and d.y == y and d.z == z), None)
        if dep and dep.remaining_yield > 0:
            status = "known" if dep.discovered else "faint"
            return f"prospect ({x},{y},{z}): {status} traces of {dep.material} ({dep.kind}, {dep.rarity})"
        if (x, y, z) in self.geology_cavern_tiles:
            return f"prospect ({x},{y},{z}): hollow resonance detected (cavern)"
        return f"prospect ({x},{y},{z}): no notable signs"

    def items_dump(self) -> str:
        lines = []
        for i in self.items:
            x, y, z = self._item_pos(i)
            lines.append(
                f"[{i.id}] {i.kind} ({x},{y},{z}) mat={i.material} q={i.quality} v={i.value} age={i.age}/{i.perishability} stock={i.stockpile_id} container={i.container_id} carried={i.carried_by} reserved={i.reserved_by}"
            )
        return "\n".join(lines)

    def alerts_dump(self) -> str:
        return "\n".join(self.alerts[-20:]) or "no alerts"
