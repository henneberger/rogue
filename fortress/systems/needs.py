from __future__ import annotations

from fortress.models import clamp


class NeedsSystemsMixin:
    def _update_needs_moods_stress(self) -> None:
        for d in self.dwarves:
            if d.hp <= 0:
                continue
            if d.rested_bonus > 0:
                d.rested_bonus -= 1
            if self.tick_count % 2 == 0:
                d.needs["hunger"] = clamp(d.needs["hunger"] + 1, 0, 100)
                d.needs["thirst"] = clamp(d.needs["thirst"] + 1, 0, 100)
            if self.tick_count % 4 == 0:
                alcohol_pressure = max(0, d.alcohol_dependency // 45)
                d.needs["alcohol"] = clamp(d.needs["alcohol"] + alcohol_pressure, 0, 100)
                d.needs["sleep"] = clamp(d.needs["sleep"] + 1, 0, 100)
            if self.tick_count % 5 == 0:
                d.needs["social"] = clamp(d.needs["social"] + 1, 0, 100)
                d.needs["worship"] = clamp(d.needs["worship"] + 1, 0, 100)
                d.needs["entertainment"] = clamp(d.needs["entertainment"] + 1, 0, 100)
            if self.tick_count % 4 == 0:
                d.nutrition["protein"] = clamp(d.nutrition["protein"] + 1, 0, 100)
                d.nutrition["fiber"] = clamp(d.nutrition["fiber"] + 1, 0, 100)
                d.nutrition["variety"] = clamp(d.nutrition["variety"] + 1, 0, 100)
            if self.world.raid_active:
                if self.tick_count % 2 == 0:
                    d.needs["safety"] = clamp(d.needs["safety"] + 1, 0, 100)
            else:
                d.needs["safety"] = clamp(d.needs["safety"] - 1, 0, 100)

            avg_nutrition_pressure = sum(d.nutrition.values()) / len(d.nutrition)
            if avg_nutrition_pressure >= 85 and self.tick_count % 3 == 0:
                d.stress = clamp(d.stress + 1, 0, 100)
                d.morale = clamp(d.morale - 1, 0, 100)

            if d.alcohol_dependency >= 45 and self.drinks == 0 and d.needs["alcohol"] >= 85:
                d.withdrawal_ticks += 1
                if self.tick_count % 3 == 0:
                    d.stress = clamp(d.stress + max(1, d.alcohol_dependency // 65), 0, 100)
                if d.withdrawal_ticks % 10 == 0:
                    d.morale = clamp(d.morale - 1, 0, 100)
                if d.withdrawal_ticks in {1, 20, 50}:
                    self._log("withdrawal", f"{d.name} is suffering alcohol withdrawal.", 2)
            else:
                d.withdrawal_ticks = 0

            critical_need_keys = ("hunger", "thirst", "sleep", "safety")
            high_needs = sum(1 for key in critical_need_keys if d.needs.get(key, 0) >= 90)
            if high_needs == 0:
                d.stress = clamp(d.stress - 1, 0, 100)
            else:
                d.stress = clamp(d.stress + high_needs - (1 if d.morale > 60 else 0), 0, 100)
            if d.stress >= 96 and d.mood != "tantrum":
                d.mood = "tantrum"
                self._log("mood", f"{d.name} is having a tantrum.", 2)
                if self.items and self.rng.random() < 0.1:
                    non_essentials = [i for i in self.items if i.kind not in {"raw_food", "cooked_food", "alcohol", "seed"}]
                    pool = non_essentials if non_essentials else self.items
                    lost = self.rng.choice(pool)
                    self._consume_item(lost.id)
                    self._record_crime(d.id, "vandalism")
                    self._log("justice", f"{d.name} destroyed property in a tantrum.", 2)
            elif d.stress <= 25 and d.mood in {"tantrum", "disturbed"}:
                d.mood = "steady"
            elif d.stress >= 75 and d.mood == "steady":
                d.mood = "disturbed"
            elif d.stress < 20 and self.rng.random() < 0.03:
                d.mood = "inspired"
                self._log("mood", f"{d.name} feels inspired.", 1)

            if d.hp <= 0:
                self._log("death", f"{d.name} has died.", 3)
