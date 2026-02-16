from __future__ import annotations

from typing import List, Optional, Set

from fortress.models import Room


class ArchitectureSystemsMixin:
    def _refresh_rooms_and_assignments(self) -> None:
        rooms: List[Room] = []
        room_id = 1

        for zone in self.zones:
            if zone.kind not in {"dormitory", "recreation"}:
                continue

            zone_items = [
                i
                for i in self.items
                if i.z == zone.z and zone.x <= i.x < zone.x + zone.w and zone.y <= i.y < zone.y + zone.h and i.carried_by is None
            ]
            beds = [i for i in zone_items if i.kind == "bed"]

            if zone.kind == "dormitory" and beds:
                for bed in beds:
                    value = self._room_value_from_items([i for i in zone_items if i.x == bed.x and i.y == bed.y], zone.kind)
                    value += 10
                    rooms.append(
                        Room(
                            id=room_id,
                            kind="bedroom",
                            x=bed.x,
                            y=bed.y,
                            z=zone.z,
                            w=1,
                            h=1,
                            value=value,
                            bed_item_id=bed.id,
                        )
                    )
                    room_id += 1
            else:
                value = self._room_value_from_items(zone_items, zone.kind)
                rooms.append(
                    Room(
                        id=room_id,
                        kind="dormitory" if zone.kind == "dormitory" else "hall",
                        x=zone.x,
                        y=zone.y,
                        z=zone.z,
                        w=zone.w,
                        h=zone.h,
                        value=value,
                    )
                )
                room_id += 1

        prev_assignment = {d.id: d.assigned_room_id for d in self.dwarves if d.assigned_room_id is not None}
        self.rooms = rooms
        self.next_room_id = room_id

        assigned_rooms: Set[int] = set()
        for dwarf in self.dwarves:
            dwarf.assigned_room_id = None

        for dwarf in self.dwarves:
            previous = prev_assignment.get(dwarf.id)
            if previous is None:
                continue
            room = next((r for r in self.rooms if r.id == previous), None)
            if room and room.assigned_dwarf_id is None and room.kind == "bedroom":
                room.assigned_dwarf_id = dwarf.id
                dwarf.assigned_room_id = room.id
                assigned_rooms.add(room.id)

        free_bedrooms = [r for r in self.rooms if r.kind == "bedroom" and r.id not in assigned_rooms]
        free_bedrooms.sort(key=lambda r: r.value, reverse=True)
        unassigned = [d for d in self.dwarves if d.assigned_room_id is None]
        for dwarf, room in zip(unassigned, free_bedrooms):
            room.assigned_dwarf_id = dwarf.id
            dwarf.assigned_room_id = room.id
            assigned_rooms.add(room.id)

        fallback = next((r for r in sorted(self.rooms, key=lambda rr: rr.value, reverse=True) if r.kind in {"dormitory", "hall"}), None)
        if fallback:
            for dwarf in self.dwarves:
                if dwarf.assigned_room_id is None:
                    dwarf.assigned_room_id = fallback.id

    def _room_value_from_items(self, items: List[object], zone_kind: str) -> int:
        base = 12 if zone_kind == "dormitory" else 8
        value = base
        for item in items:
            quality = getattr(item, "quality", 0)
            item_value = getattr(item, "value", 1)
            kind = getattr(item, "kind", "")
            bonus = item_value + (quality * 2)
            if kind in {"artifact"}:
                bonus += 12
            if kind in {"bed", "chair", "table"}:
                bonus += 4
            value += bonus
        return value

    def _find_room(self, room_id: Optional[int]) -> Optional[Room]:
        if room_id is None:
            return None
        return next((r for r in self.rooms if r.id == room_id), None)

    def _assigned_bed_for_dwarf(self, dwarf_id: int):
        dwarf = self._find_dwarf(dwarf_id)
        if not dwarf:
            return None
        room = self._find_room(dwarf.assigned_room_id)
        if not room or room.bed_item_id is None:
            return None
        return self._find_item_by_id(room.bed_item_id)

    def _dwarf_room_value(self, dwarf_id: int) -> int:
        dwarf = self._find_dwarf(dwarf_id)
        if not dwarf:
            return 0
        room = self._find_room(dwarf.assigned_room_id)
        if not room:
            return 0
        return room.value
