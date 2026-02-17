from __future__ import annotations

from typing import Set

from fortress.models import clamp


class WorldSystemsMixin:
    def _update_world_time_weather(self) -> None:
        if self.tick_count % 20 == 0:
            self.world.day += 1
        if self.world.day % 30 == 1 and self.tick_count % 20 == 0:
            seasons = ["spring", "summer", "autumn", "winter"]
            idx = seasons.index(self.world.season)
            self.world.season = seasons[(idx + 1) % len(seasons)]
            self._log("season", f"Season changed to {self.world.season}", 1)
            if self.world.season in {"spring", "autumn"}:
                self._caravan_arrival()
        weather_choices = ["clear", "rain", "storm", "dry", "fog"]
        if self.rng.random() < 0.08:
            self.world.weather = self.rng.choice(weather_choices)
            self._log("weather", f"Weather is now {self.world.weather}", 1)
        base_temp = {"winter": 0, "spring": 10, "summer": 24, "autumn": 12}[self.world.season]
        if self.world.weather == "storm":
            base_temp -= 2
        if self.world.weather == "dry":
            base_temp += 4
        self.world.temperature_c = base_temp + self.rng.randint(-2, 2)

    def _grow_farms_and_ecosystems(self) -> None:
        season_bonus = 0.35 if self.world.season in {"spring", "summer"} else 0.20
        for z in self.zones:
            if z.kind == "farm":
                if z.crop_available < z.crop_max and self.rng.random() < season_bonus:
                    z.crop_available += 1
            if z.kind == "pasture" and self.rng.random() < 0.015:
                self.add_animal("goat", z.x, z.y, z.z)
                self._log("animal", "A goat kid was born in the pasture.", 1)

    def _update_threats_and_factions(self) -> None:
        if self.tick_count < 300:
            return
        hostile = next((f for f in self.factions if f.stance == "hostile"), None)
        raid_chance = 0.0006 + (self.world.wealth / 120000)
        if hostile and not self.world.raid_active and self.rng.random() < raid_chance:
            self.world.raid_active = True
            self.world.threat_level = self.rng.randint(1, 4)
            self._log("raid", f"Raid detected: threat level {self.world.threat_level}", 3)
        if self.world.raid_active:
            total_training = sum(s.training for s in self.squads)
            militia = sum(len(s.members) for s in self.squads)
            defense = total_training + militia * 2
            if defense > self.world.threat_level * 10 and self.rng.random() < 0.2:
                self.world.raid_active = False
                self.world.threat_level = 0
                self._log("raid", "Raid repelled.", 2)
                for f in self.factions:
                    if f.stance == "hostile":
                        f.reputation -= 2
            elif self.rng.random() < 0.01:
                victim = self.rng.choice(self.dwarves)
                if victim.hp > 0:
                    victim.wounds.append("bruised")
                    victim.hp = max(5, victim.hp - self.rng.randint(4, 12))
                    victim.needs["safety"] = clamp(victim.needs["safety"] + 20, 0, 100)
                    self._log("combat", f"{victim.name} was injured during a skirmish.", 2)
            elif self.rng.random() < 0.03:
                self.world.raid_active = False
                self.world.threat_level = 0
                self._log("raid", "Raiders dispersed before a full assault.", 1)

    def _animal_tick(self) -> None:
        pasture = self._find_zone("pasture")
        for a in self.animals:
            a.hunger = clamp(a.hunger + 2, 0, 100)
            if pasture and a.z == pasture.z:
                a.hunger = clamp(a.hunger - 3, 0, 100)
            if self.rng.random() < 0.3:
                nx = clamp(a.x + self.rng.choice([-1, 0, 1]), 0, self.width - 1)
                ny = clamp(a.y + self.rng.choice([-1, 0, 1]), 0, self.height - 1)
                a.x, a.y = nx, ny
            if a.hunger >= 95:
                self._spawn_item("hide", a.x, a.y, a.z, material=f"{a.species}-hide", value=2)
                self._log("animal", f"A {a.species} died of neglect.", 2)
                a.hunger = 40

    def _fluid_tick(self) -> None:
        if self.world.weather in {"rain", "storm"}:
            self.world.water_pressure = clamp(self.world.water_pressure + 1, 0, 100)
        else:
            self.world.water_pressure = clamp(self.world.water_pressure - 1, 0, 100)
        if self.selected_z == self.depth - 1 and self.rng.random() < 0.02:
            self.world.magma_pressure = clamp(self.world.magma_pressure + 2, 0, 100)

    def _item_tick(self) -> None:
        remove_ids: Set[int] = set()
        for item in self.items:
            item.age += 1
            effective_perishability = self._effective_perishability(item)
            if effective_perishability > 0 and item.age > effective_perishability:
                if self.rng.random() < 0.15:
                    remove_ids.add(item.id)
        if remove_ids:
            self.items = [i for i in self.items if i.id not in remove_ids]
            self._log("spoilage", f"{len(remove_ids)} perishable item(s) spoiled.", 1)

    def _caravan_arrival(self) -> None:
        self._log("trade", "A caravan arrived with trade goods.", 1)
        self._spawn_item("wood", self.width - 3, 2, 0, material="oak", value=2)
        self._spawn_item("medicine", self.width - 3, 3, 0, material="herbs", value=4)
        friendly = next((f for f in self.factions if f.name == "River Guild"), None)
        if friendly:
            friendly.reputation += 1
