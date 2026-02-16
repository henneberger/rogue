from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from fortress.models import Flora, clamp


class FloraSystemsMixin:
    def _init_flora(self) -> None:
        if self.floras:
            return
        region = self._fortress_region()
        biome = region.biome if region else self.world.biome
        species_pool = self._flora_species_for_biome(biome)
        if not species_pool:
            return

        target = max(14, min(32, (self.width * self.height) // 20))
        used: Set[Tuple[int, int, int]] = set()
        attempts = target * 5
        for _ in range(attempts):
            if len(self.floras) >= target:
                break
            x = self.rng.randint(0, self.width - 1)
            y = self.rng.randint(0, self.height - 1)
            z = 0
            if (x, y, z) in used:
                continue
            used.add((x, y, z))
            if any(d.x == x and d.y == y and d.z == z for d in self.dwarves):
                continue
            if any(w.x == x and w.y == y and w.z == z for w in self.workshops):
                continue
            sp = self.rng.choice(species_pool)
            stage = sp["stages"][0]
            if self.rng.random() < 0.35:
                stage = sp["stages"][1]
            self._spawn_flora(sp["id"], x, y, z, stage=stage)

    def _spawn_flora(self, species_id: str, x: int, y: int, z: int, stage: Optional[str] = None) -> Optional[Flora]:
        sp = self._flora_species().get(species_id)
        if not sp:
            return None
        stages = sp["stages"]
        fl = Flora(
            id=self.next_flora_id,
            species_id=species_id,
            common_name=sp["common_name"],
            scientific_name=sp["scientific_name"],
            kind=sp["kind"],
            x=x,
            y=y,
            z=z,
            stage=stage if stage in stages else stages[0],
            growth_points=self.rng.randint(0, 8),
            health=self.rng.randint(75, 100),
        )
        self.next_flora_id += 1
        self.floras.append(fl)
        return fl

    def _fortress_region(self):
        return next((r for r in self.regions if r.id == self.world.fortress_region_id), None)

    def _flora_species(self) -> Dict[str, Dict[str, object]]:
        return self.defs.get("flora_species", {})

    def _flora_species_for_biome(self, biome: str) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for sp in self._flora_species().values():
            if biome in sp.get("biomes", []):
                out.append(sp)
        return out

    def _flora_stage_index(self, flora: Flora) -> int:
        stages = self._flora_species().get(flora.species_id, {}).get("stages", [])
        try:
            return stages.index(flora.stage)
        except ValueError:
            return 0

    def _flora_density_at(self, x: int, y: int, z: int, radius: int) -> int:
        count = 0
        for fl in self.floras:
            if fl.z != z or fl.dead:
                continue
            if abs(fl.x - x) <= radius and abs(fl.y - y) <= radius:
                count += 1
        return count

    def _biome_modifiers(self) -> Tuple[float, float, float]:
        region = self._fortress_region()
        rainfall = getattr(region, "rainfall", "moderate")
        temp_band = getattr(region, "temperature_band", "mild")
        elevation = getattr(region, "elevation", "uplands")

        rain_mult = {"low": 0.82, "moderate": 1.0, "high": 1.15}.get(rainfall, 1.0)
        temp_mult = {"cold": 0.9, "mild": 1.0, "warm": 1.05}.get(temp_band, 1.0)
        elev_mult = {"lowlands": 1.06, "uplands": 1.0, "mountainous": 0.88}.get(elevation, 1.0)
        return rain_mult, temp_mult, elev_mult

    def _flora_tick(self) -> None:
        if not self.floras:
            return
        biome = self.world.biome
        rain_mult, temp_mult, elev_mult = self._biome_modifiers()
        new_spawns: List[Tuple[str, int, int, int]] = []
        remove_ids: Set[int] = set()

        for fl in self.floras:
            sp = self._flora_species().get(fl.species_id)
            if not sp:
                continue
            fl.age_ticks += 1
            if fl.spread_cooldown > 0:
                fl.spread_cooldown -= 1

            stage_idx = self._flora_stage_index(fl)
            stage_count = len(sp["stages"])

            season_mod = sp["season_mod"].get(self.world.season, 1.0)
            weather_mod = sp["weather_mod"].get(self.world.weather, 1.0)
            base_growth = float(sp["base_growth"])
            growth_delta = base_growth * season_mod * weather_mod * rain_mult * temp_mult * elev_mult

            min_c = int(sp["temp_min"])
            max_c = int(sp["temp_max"])
            stress = 0
            if self.world.temperature_c < min_c:
                stress += (min_c - self.world.temperature_c) // 2 + 2
            if self.world.temperature_c > max_c:
                stress += (self.world.temperature_c - max_c) // 2 + 2
            if self.world.weather == "dry" and sp.get("dry_penalty", 0) > 0:
                stress += int(sp["dry_penalty"])
            if biome not in sp.get("biomes", []):
                stress += 4

            fl.stressed = stress > 0
            fl.dormant = season_mod < 0.35 or growth_delta <= 0.2

            if fl.dead:
                if fl.age_ticks % 40 == 0 and self.rng.random() < 0.35:
                    remove_ids.add(fl.id)
                continue

            if stress > 0:
                fl.health = clamp(fl.health - stress, 0, 100)
                growth_delta *= max(0.25, 1.0 - (stress / 22.0))
            else:
                fl.health = clamp(fl.health + 1, 0, 100)

            if fl.health <= 0:
                fl.dead = True
                fl.stage = "dead"
                self._log("flora", f"{fl.common_name} ({fl.scientific_name}) died off.", 1)
                continue

            growth_delta *= 0.55
            if stress >= 4:
                growth_delta -= 0.7
            fl.growth_points += int(round(growth_delta))
            threshold = int(sp["stage_threshold"])

            if fl.growth_points >= threshold and stage_idx < stage_count - 1:
                fl.growth_points -= threshold
                fl.stage = sp["stages"][stage_idx + 1]
                if fl.stage in {"mature", "ancient", "flowering", "seeded"} and self.rng.random() < 0.12:
                    self._log("flora", f"{fl.common_name} ({fl.scientific_name}) reached {fl.stage}.", 1)
            elif fl.growth_points <= -threshold and stage_idx > 0:
                fl.growth_points = 0
                fl.stage = sp["stages"][stage_idx - 1]

            if fl.kind == "plant" and self.world.season == "winter" and fl.stage in {"flowering", "seeded"}:
                if self.rng.random() < 0.08:
                    fl.stage = "withered"
                    fl.growth_points = 0
            if fl.kind == "plant" and fl.stage == "seeded" and self.world.season in {"autumn", "winter"}:
                if self.rng.random() < 0.05:
                    fl.stage = "withered"
                    fl.growth_points = 0
            if fl.kind == "plant" and self.world.season == "spring" and fl.stage == "withered" and fl.health >= 35:
                if self.rng.random() < 0.18:
                    fl.stage = "sprout"
                    fl.growth_points = 0

            spread_stage = int(sp["spread_stage_index"])
            if (
                self._flora_stage_index(fl) >= spread_stage
                and fl.health >= 55
                and not fl.dormant
                and fl.spread_cooldown == 0
                and len(self.floras) + len(new_spawns) < self.max_flora
            ):
                spread_chance = float(sp["spread_chance"])
                spread_chance *= 0.22
                if self.world.weather in {"rain", "storm"}:
                    spread_chance *= 1.25
                if self.world.weather == "dry":
                    spread_chance *= 0.65
                if self.rng.random() < spread_chance:
                    radius = int(sp["spread_radius"])
                    tx = clamp(fl.x + self.rng.randint(-radius, radius), 0, self.width - 1)
                    ty = clamp(fl.y + self.rng.randint(-radius, radius), 0, self.height - 1)
                    if self._flora_density_at(tx, ty, fl.z, 1) < 4:
                        new_spawns.append((fl.species_id, tx, ty, fl.z))
                        fl.spread_cooldown = int(sp["spread_cooldown"])

        if new_spawns:
            for sid, x, y, z in new_spawns:
                if len(self.floras) >= self.max_flora:
                    break
                created = self._spawn_flora(sid, x, y, z)
                if created and self.rng.random() < 0.12:
                    self._log("flora", f"New {created.common_name} ({created.scientific_name}) sprouted.", 1)

        if remove_ids:
            self.floras = [fl for fl in self.floras if fl.id not in remove_ids]

    def _flora_glyph(self, flora: Flora) -> str:
        if flora.dead or flora.stage == "dead":
            return "x"
        if flora.kind == "tree":
            tree_map = {
                "seedling": "t",
                "sapling": "y",
                "young": "T",
                "mature": "Y",
                "ancient": "A",
            }
            return tree_map.get(flora.stage, "t")
        plant_map = {
            "sprout": ",",
            "juvenile": ";",
            "mature": '"',
            "flowering": "*",
            "seeded": "+",
            "withered": ".",
        }
        return plant_map.get(flora.stage, ",")

    def flora_at(self, x: int, y: int, z: int) -> str:
        rows = [
            fl
            for fl in self.floras
            if fl.x == x and fl.y == y and fl.z == z
        ]
        if not rows:
            return "no flora at tile"
        lines = []
        for fl in rows:
            lines.append(
                f"[{fl.id}] {fl.common_name} ({fl.scientific_name}) kind={fl.kind} stage={fl.stage} hp={fl.health} dormant={fl.dormant} stressed={fl.stressed} gp={fl.growth_points}"
            )
        return "\n".join(lines)
