from __future__ import annotations

from typing import Optional, Tuple

from fortress.models import Coord3, Dwarf, Event, Faction, Flora, Item, Squad, Stockpile, Workshop, Zone, clamp


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
