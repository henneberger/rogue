from __future__ import annotations

from fortress.models import clamp


class NeedsSystemsMixin:
    def _update_needs_moods_stress(self) -> None:
        for d in self.dwarves:
            if d.hp <= 0:
                continue
            d.needs["hunger"] = clamp(d.needs["hunger"] + 2, 0, 100)
            d.needs["thirst"] = clamp(d.needs["thirst"] + 2, 0, 100)
            d.needs["sleep"] = clamp(d.needs["sleep"] + 1, 0, 100)
            d.needs["social"] = clamp(d.needs["social"] + 1, 0, 100)
            d.needs["worship"] = clamp(d.needs["worship"] + 1, 0, 100)
            d.needs["entertainment"] = clamp(d.needs["entertainment"] + 1, 0, 100)
            if self.world.raid_active:
                d.needs["safety"] = clamp(d.needs["safety"] + 2, 0, 100)
            else:
                d.needs["safety"] = clamp(d.needs["safety"] - 1, 0, 100)

            high_needs = sum(1 for v in d.needs.values() if v >= 80)
            d.stress = clamp(d.stress + high_needs - (1 if d.morale > 70 else 0), 0, 100)
            if d.stress >= 90 and d.mood != "tantrum":
                d.mood = "tantrum"
                self._log("mood", f"{d.name} is having a tantrum.", 2)
                if self.items and self.rng.random() < 0.3:
                    lost = self.rng.choice(self.items)
                    self._consume_item(lost.id)
                    self._record_crime(d.id, "vandalism")
                    self._log("justice", f"{d.name} destroyed property in a tantrum.", 2)
            elif d.stress <= 25 and d.mood in {"tantrum", "disturbed"}:
                d.mood = "steady"
            elif d.stress >= 65 and d.mood == "steady":
                d.mood = "disturbed"
            elif d.stress < 20 and self.rng.random() < 0.03:
                d.mood = "inspired"
                self._log("mood", f"{d.name} feels inspired.", 1)

            if d.hp <= 0:
                self._log("death", f"{d.name} has died.", 3)

