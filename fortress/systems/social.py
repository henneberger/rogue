from __future__ import annotations

from typing import List, Tuple

from fortress.models import Dwarf, clamp


class SocialSystemsMixin:
    def _social_tick(self) -> None:
        active = [d for d in self.dwarves if d.hp > 0]
        if len(active) < 2:
            return
        if self.rng.random() < 0.12:
            a, b = self.rng.sample(active, 2)
            delta = 1 if self.rng.random() < 0.85 else -2
            a.relationships[b.id] = clamp(a.relationships.get(b.id, 0) + delta, -100, 100)
            b.relationships[a.id] = clamp(b.relationships.get(a.id, 0) + delta, -100, 100)
            if delta > 0:
                self._remember(a, f"Enjoyed time with {b.name}")
                self._remember(b, f"Enjoyed time with {a.name}")
            else:
                self._remember(a, f"Argued with {b.name}")
                self._remember(b, f"Argued with {a.name}")

    def _culture_tick(self) -> None:
        temple = self._find_zone("temple")
        if temple and self.rng.random() < 0.05:
            self.world.culture_points += 1
        if self.rng.random() < 0.03 and self.world.culture_points > 3:
            self._spawn_item("artifact", self.width // 2, self.height // 2, 0, quality=4, value=20)
            self.world.culture_points -= 3
            self._log("culture", "An inspired artifact was created from colony legends.", 2)
        if self.rng.random() < 0.04:
            self.world.scholarly_points += 1

    def _top_skills(self, dwarf: Dwarf) -> List[Tuple[str, int]]:
        return sorted(dwarf.skills.items(), key=lambda kv: kv[1], reverse=True)[:3]

    def _remember(self, dwarf: Dwarf, text: str) -> None:
        dwarf.memories.append(f"t{self.tick_count}:{text}")
        if len(dwarf.memories) > 20:
            dwarf.memories = dwarf.memories[-20:]
