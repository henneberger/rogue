from __future__ import annotations

from fortress.models import Crime, clamp


class JusticeSystemsMixin:
    def _justice_tick(self) -> None:
        unresolved = [c for c in self.crimes if not c.resolved]
        if unresolved and self.rng.random() < 0.2:
            case = unresolved[0]
            case.resolved = True
            self._log("justice", f"Crime {case.kind} by dwarf #{case.dwarf_id} was resolved.", 1)

        for d in self.dwarves:
            if d.hp <= 0:
                continue
            if d.needs["hunger"] > 95 and self.raw_food + self.cooked_food > 0 and self.rng.random() < 0.08:
                self._record_crime(d.id, "food_theft")
                meal = self._find_item(kind="cooked_food") or self._find_item(kind="raw_food")
                if meal:
                    self._consume_item(meal.id)
                d.needs["hunger"] = clamp(d.needs["hunger"] - 30, 0, 100)
                d.stress = clamp(d.stress - 5, 0, 100)
                self._log("justice", f"{d.name} stole food due to desperation.", 2)

    def _record_crime(self, dwarf_id: int, kind: str) -> None:
        c = Crime(id=self.next_crime_id, tick=self.tick_count, dwarf_id=dwarf_id, kind=kind)
        self.next_crime_id += 1
        self.crimes.append(c)

