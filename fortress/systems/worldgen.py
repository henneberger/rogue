from __future__ import annotations

import random

from fortress.models import HistoricalEvent, Region


class WorldgenMixin:
    def _generate_world(self) -> None:
        world_rng = random.Random(self.rng_seed)
        adjectives = ["Crag", "Frost", "Iron", "Amber", "Moss", "Storm", "Deep", "Dawn"]
        nouns = ["Reach", "Vale", "Spine", "Basin", "Frontier", "March", "Hollow", "Strand"]
        biomes = [
            "temperate-forest",
            "arid-steppe",
            "taiga",
            "alpine",
            "river-lowlands",
            "highland-heath",
        ]
        rainfalls = ["low", "moderate", "high"]
        temps = ["cold", "mild", "warm"]
        elevations = ["lowlands", "uplands", "mountainous"]
        resource_pool = ["wood", "stone", "ore", "clay", "fiber", "wildlife", "herbs"]
        self.world.world_name = f"{world_rng.choice(adjectives)} {world_rng.choice(nouns)}"

        self.regions = []
        for rid in range(1, 7):
            region = Region(
                id=rid,
                name=f"{world_rng.choice(adjectives)} {world_rng.choice(nouns)}",
                biome=world_rng.choice(biomes),
                rainfall=world_rng.choice(rainfalls),
                temperature_band=world_rng.choice(temps),
                elevation=world_rng.choice(elevations),
                resources=sorted(world_rng.sample(resource_pool, k=3)),
            )
            self.regions.append(region)

        for idx, region in enumerate(self.regions):
            nxt = ((idx + 1) % len(self.regions)) + 1
            prv = ((idx - 1) % len(self.regions)) + 1
            region.neighbors = sorted({nxt, prv})
        for region in self.regions:
            if world_rng.random() < 0.45:
                region.neighbors = sorted(set(region.neighbors + [world_rng.randint(1, len(self.regions))]))
                region.neighbors = [rid for rid in region.neighbors if rid != region.id]

        fortress_region = next((r for r in self.regions if r.biome == "temperate-forest"), self.regions[0])
        self.world.fortress_region_id = fortress_region.id
        self.world.biome = fortress_region.biome

        civ_specs = [
            ("Mountainhome", "dwarven-hold", fortress_region.id),
            ("River Guild", "merchant-league", self.regions[1].id),
            ("Goblin Host", "warlike-tribe", self.regions[2].id),
            ("Sun Court", "kingdom", self.regions[3].id),
        ]
        civ_names = [name for name, _, _ in civ_specs]
        event_types = [
            ("trade-pact", 10, 24),
            ("border-skirmish", -28, -10),
            ("aid-treaty", 12, 20),
            ("trade-dispute", -16, -6),
            ("marriage-alliance", 14, 26),
            ("betrayal", -30, -14),
        ]

        self.world_history = []
        for year in sorted(world_rng.sample(range(-120, -4), 14)):
            actor = world_rng.choice(civ_names)
            target = world_rng.choice([name for name in civ_names if name != actor])
            ev_name, lo, hi = world_rng.choice(event_types)
            delta = world_rng.randint(lo, hi)
            text = f"{actor} and {target}: {ev_name} ({delta:+d} relation)"
            self.world_history.append(
                HistoricalEvent(
                    year=year,
                    event_type=ev_name,
                    actor=actor,
                    target=target,
                    delta_reputation=delta,
                    text=text,
                )
            )

        relation_by_civ = {name: 0 for name in civ_names}
        player_civ = "Mountainhome"
        for ev in self.world_history:
            if ev.actor == player_civ:
                relation_by_civ[ev.target] += ev.delta_reputation
            elif ev.target == player_civ:
                relation_by_civ[ev.actor] += ev.delta_reputation

        self.factions = []
        self.next_faction_id = 1
        for name, civ_type, home_region_id in civ_specs:
            score = relation_by_civ.get(name, 0)
            if name == player_civ:
                stance = "allied"
                score = max(score, 15)
            elif score >= 20:
                stance = "allied"
            elif score <= -20:
                stance = "hostile"
            else:
                stance = "neutral"
            self.add_faction(
                name=name,
                stance=stance,
                reputation=score,
                home_region_id=home_region_id,
                civ_type=civ_type,
            )
