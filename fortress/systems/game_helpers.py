from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from fortress.models import (
    CONTAINER_CAPACITY,
    Coord3,
    Dwarf,
    Event,
    Faction,
    Flora,
    GeologyDeposit,
    Item,
    Squad,
    Stockpile,
    Workshop,
    Zone,
    clamp,
    is_container_kind,
)


class GameHelpersMixin:
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

    def _find_flora_by_id(self, flora_id: Optional[int]) -> Optional[Flora]:
        if flora_id is None:
            return None
        return next((fl for fl in self.floras if fl.id == flora_id), None)

    def _find_geology_deposit_at(self, x: int, y: int, z: int) -> Optional[GeologyDeposit]:
        return next(
            (
                dep
                for dep in self.geology_deposits
                if dep.x == x and dep.y == y and dep.z == z and dep.remaining_yield > 0
            ),
            None,
        )

    def _resolve_geology_mining(self, x: int, y: int, z: int, miner: Optional[Dwarf] = None) -> None:
        dep = self._find_geology_deposit_at(x, y, z)
        if dep:
            if not dep.discovered:
                dep.discovered = True
                self.economy_stats["geology_discoveries"] = self.economy_stats.get("geology_discoveries", 0) + 1
                self._log("geology", f"Discovered {dep.material} {dep.kind} deposit ({dep.rarity}) at ({x},{y},{z}).", 2)
            dep.remaining_yield = max(0, dep.remaining_yield - 1)
            if dep.kind == "ore":
                ore_meta = self.defs.get("geology_ores", {}).get(dep.material, {})
                value = int(ore_meta.get("value", 4))
                self._spawn_item("ore", x, y, z, material=dep.material, value=value)
                key = f"geology_extracted_ore_{dep.material}"
                self.economy_stats[key] = self.economy_stats.get(key, 0) + 1
            else:
                gem_meta = self.defs.get("geology_gems", {}).get(dep.material, {})
                value = int(gem_meta.get("value", 10))
                self._spawn_item("gem", x, y, z, material=dep.material, value=value)
                key = f"geology_extracted_gem_{dep.material}"
                self.economy_stats[key] = self.economy_stats.get(key, 0) + 1
            depth_key = f"geology_depth_{z}_extracted"
            self.economy_stats[depth_key] = self.economy_stats.get(depth_key, 0) + 1
            if dep.remaining_yield == 0:
                self._log("geology", f"{dep.material} deposit at ({x},{y},{z}) is depleted.", 1)
        else:
            self._spawn_item("stone", x, y, z, material="granite", value=1)

        tile = (x, y, z)
        if tile in self.geology_cavern_tiles and tile not in self.geology_breached_tiles:
            self.geology_breached_tiles.add(tile)
            self.economy_stats["caverns_breached"] = self.economy_stats.get("caverns_breached", 0) + 1
            self._log("geology", f"Cavern breach at ({x},{y},{z})! Strange echoes from below...", 3)
            for d in self.dwarves:
                d.needs["safety"] = clamp(d.needs["safety"] + 12, 0, 100)
            if self.rng.random() < 0.35:
                self.world.raid_active = True
                self.world.threat_level = max(self.world.threat_level, 1)
                self._log("geology", "Cavern wildlife has stirred and threatens the outpost.", 2)

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
        scored.sort(key=lambda t: (t[0], -sum(t[1].orders.values())), reverse=True)
        ordered = [ws for _, ws in scored]
        if ordered:
            start = self.workshop_dispatch_cursor % len(ordered)
            ordered = ordered[start:] + ordered[:start]
            self.workshop_dispatch_cursor = (self.workshop_dispatch_cursor + 1) % max(1, len(self.workshops))
        for ws in ordered:
            recipe = next((r for r, c in ws.orders.items() if c > 0), None)
            if recipe:
                ws.orders[recipe] -= 1
                return ws, recipe
        return None, None

    def _find_haul_candidate(self) -> Tuple[Optional[Item], Optional[Stockpile], Optional[Item]]:
        for item in self.items:
            if item.reserved_by is not None or item.carried_by is not None:
                continue
            if item.stockpile_id is not None:
                continue
            if item.container_id is not None:
                continue
            stock, container = self._find_stockpile_for_item(item)
            if stock:
                return item, stock, container
        return None, None, None

    def _find_stockpile_for_item(self, item: Item) -> Tuple[Optional[Stockpile], Optional[Item]]:
        if is_container_kind(item.kind):
            stock_targets = [
                sp
                for sp in self.stockpiles
                if sp.z == item.z and item.kind in self._stockpile_container_policy(sp.kind) and self._stockpile_free_slots(sp) > 0
            ]
            if stock_targets:
                stock_targets.sort(key=lambda sp: self._stockpile_used_slots(sp))
                return stock_targets[0], None
        best: Optional[Tuple[int, Stockpile, Optional[Item]]] = None
        for sp in self.stockpiles:
            if not sp.accepts(item.kind) or sp.z != item.z:
                continue
            container = self._find_compatible_container(sp, item.kind)
            if container:
                load = self._container_load(container)
                if best is None or load < best[0]:
                    best = (load, sp, container)
                continue
            if self._stockpile_free_slots(sp) > 0:
                load = self._stockpile_used_slots(sp)
                if best is None or load < best[0]:
                    best = (load, sp, None)
                continue
            self._request_container_for_stockpile(sp, item.kind)
        if best:
            return best[1], best[2]
        return None, None

    def _stockpile_container_policy(self, stockpile_kind: str) -> List[str]:
        policy: Dict[str, List[str]] = {
            "raw": ["bag", "barrel"],
            "cooked": ["barrel"],
            "drink": ["barrel"],
            "food": ["barrel", "bag"],
            "materials": ["bin", "crate", "bag"],
            "goods": ["bin", "chest", "crate"],
            "furniture": ["crate", "chest"],
            "medical": ["bag", "barrel", "bin"],
            "general": ["crate", "bin", "barrel", "bag", "chest"],
        }
        return policy.get(stockpile_kind, [])

    def _container_accepts_item(self, container_kind: str, item_kind: str, stockpile_kind: str) -> bool:
        if container_kind not in self._stockpile_container_policy(stockpile_kind):
            return False
        if item_kind in {"chest", "barrel", "bin", "crate", "bag"}:
            return False
        if container_kind == "bag":
            return item_kind in {"seed", "herb", "berry", "raw_food", "fiber", "medicine", "rare_plant"}
        if container_kind == "barrel":
            return item_kind in {"raw_food", "cooked_food", "alcohol", "herb", "berry", "medicine"}
        if container_kind == "bin":
            return item_kind in {"craft_good", "artifact", "manuscript", "performance_record", "fiber", "hide", "ore", "stone", "timber", "wood"}
        if container_kind == "crate":
            return item_kind not in {"alcohol"}
        if container_kind == "chest":
            return item_kind in {"craft_good", "artifact", "manuscript", "performance_record", "bed", "chair", "table"}
        return False

    def _container_load(self, container: Item) -> int:
        return sum(1 for i in self.items if i.container_id == container.id)

    def _container_free_capacity(self, container: Item) -> int:
        cap = CONTAINER_CAPACITY.get(container.kind, 0)
        return max(0, cap - self._container_load(container))

    def _find_compatible_container(self, stockpile: Stockpile, item_kind: str) -> Optional[Item]:
        candidates: List[Item] = []
        for item in self.items:
            if item.stockpile_id != stockpile.id or item.container_id is not None:
                continue
            if not is_container_kind(item.kind):
                continue
            if item.reserved_by is not None:
                continue
            if not self._container_accepts_item(item.kind, item_kind, stockpile.kind):
                continue
            if self._container_free_capacity(item) <= 0:
                continue
            candidates.append(item)
        if not candidates:
            return None
        candidates.sort(key=lambda c: (self._container_load(c), c.id))
        return candidates[0]

    def _request_container_for_stockpile(self, stockpile: Stockpile, item_kind: str) -> None:
        if self.tick_count % 20 != 0:
            return
        container_order = {
            "raw": ("carpenter", "barrel"),
            "cooked": ("carpenter", "barrel"),
            "drink": ("carpenter", "barrel"),
            "food": ("carpenter", "barrel"),
            "materials": ("carpenter", "bin"),
            "goods": ("carpenter", "chest"),
            "furniture": ("carpenter", "crate"),
            "medical": ("loom", "bag"),
            "general": ("carpenter", "crate"),
        }.get(stockpile.kind)
        if not container_order:
            return
        ws_kind, recipe = container_order
        ws = next((w for w in self.workshops if w.kind == ws_kind and w.built and w.z == stockpile.z), None)
        if not ws:
            return
        if ws.orders.get(recipe, 0) >= 2:
            return
        ws.orders[recipe] = ws.orders.get(recipe, 0) + 1
        self._log("logistics", f"Queued {recipe} for stockpile #{stockpile.id} ({stockpile.kind}).", 1)

    def _stockpile_loose_item_count(self, stockpile: Stockpile) -> int:
        return sum(
            1
            for i in self.items
            if i.stockpile_id == stockpile.id and i.container_id is None and not is_container_kind(i.kind)
        )

    def _stockpile_used_slots(self, stockpile: Stockpile) -> int:
        return sum(1 for i in self.items if i.stockpile_id == stockpile.id and i.container_id is None)

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
                    if i.stockpile_id == stockpile.id and i.container_id is None and i.x == xx and i.y == yy and i.z == stockpile.z
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
        remove_ids = {item_id}
        contained = {i.id for i in self.items if i.container_id == item_id}
        remove_ids |= contained
        self.items = [i for i in self.items if i.id not in remove_ids]

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
        if item.container_id is not None:
            return 0

        organic_kinds = {
            "raw_food",
            "cooked_food",
            "alcohol",
            "herb",
            "berry",
            "fiber",
            "hide",
            "leather",
            "timber",
            "wood",
            "seed",
            "flour",
        }
        is_organic = item.kind in organic_kinds
        if not is_organic and item.perishability <= 0:
            return 0

        x, y, z = self._item_pos(item)
        sheltered = z > 0 or any(room.contains((x, y, z)) for room in self.rooms)
        if is_organic and sheltered:
            return 0

        effective = item.perishability if item.perishability > 0 else 220
        if self.world.weather in {"rain", "storm"}:
            effective = int(effective * 0.78)
        if self.world.temperature_c >= 24:
            effective = int(effective * 0.85)
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
