from __future__ import annotations

import random

from fortress.models import GeologyDeposit, HistoricalEvent, Region


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

    def _generate_geology(self) -> None:
        geo_rng = random.Random(self.rng_seed + 1009)
        self.geology_deposits = []
        self.geology_strata = {}
        self.geology_cavern_tiles = set()
        self.geology_breached_tiles = set()
        next_dep_id = 1

        # Depth-biased strata: shallow sedimentary, deep igneous/metamorphic.
        for z in range(self.depth):
            if z <= max(0, self.depth // 3 - 1):
                self.geology_strata[z] = "sedimentary-shale"
            elif z >= max(1, self.depth - 1):
                self.geology_strata[z] = "igneous-basalt"
            else:
                self.geology_strata[z] = "metamorphic-schist"

        region = next((r for r in self.regions if r.id == self.world.fortress_region_id), None)
        elev = getattr(region, "elevation", "uplands")
        ore_bias = {"lowlands": 0.85, "uplands": 1.0, "mountainous": 1.3}.get(elev, 1.0)
        biome = self.world.biome
        gem_bias = 1.2 if biome in {"alpine", "highland-heath"} else 1.0

        ores = self.defs.get("geology_ores", {})
        gems = self.defs.get("geology_gems", {})

        used = set()
        area = self.width * self.height
        deposit_target = max(8, int((area * max(1, self.depth - 1)) / 32))
        deposit_target = int(deposit_target * ore_bias)
        deposit_target = min(deposit_target, 48)

        deep_min_z = 1 if self.depth > 1 else 0

        def pick_free_pos(min_z: int = deep_min_z):
            for _ in range(80):
                x = geo_rng.randint(0, self.width - 1)
                y = geo_rng.randint(0, self.height - 1)
                z = geo_rng.randint(min_z, self.depth - 1)
                if (x, y, z) in used:
                    continue
                used.add((x, y, z))
                return x, y, z
            return None

        ore_count = int(deposit_target * 0.72)
        gem_count = max(3, int(deposit_target * 0.28 * gem_bias))

        for _ in range(ore_count):
            pos = pick_free_pos(min_z=deep_min_z)
            if not pos:
                break
            x, y, z = pos
            eligible = [
                (mat, meta)
                for mat, meta in ores.items()
                if int(meta.get("min_depth", 1)) <= z <= int(meta.get("max_depth", self.depth - 1))
            ]
            if not eligible:
                continue
            mat, meta = geo_rng.choice(eligible)
            rarity = str(meta.get("rarity", "common"))
            base = {"common": (3, 6), "uncommon": (2, 4), "rare": (1, 3)}.get(rarity, (2, 4))
            total = geo_rng.randint(base[0], base[1])
            self.geology_deposits.append(
                GeologyDeposit(
                    id=next_dep_id,
                    x=x,
                    y=y,
                    z=z,
                    kind="ore",
                    material=mat,
                    rarity=rarity,
                    total_yield=total,
                    remaining_yield=total,
                )
            )
            next_dep_id += 1

        for _ in range(gem_count):
            pos = pick_free_pos(min_z=deep_min_z)
            if not pos:
                break
            x, y, z = pos
            # Gem pockets are depth-biased toward deeper levels.
            if geo_rng.random() < 0.6:
                z = self.depth - 1
            eligible = [
                (mat, meta)
                for mat, meta in gems.items()
                if int(meta.get("min_depth", 1)) <= z <= int(meta.get("max_depth", self.depth - 1))
            ]
            if not eligible:
                continue
            mat, meta = geo_rng.choice(eligible)
            rarity = str(meta.get("rarity", "common"))
            base = {"common": (1, 2), "uncommon": (1, 2), "rare": (1, 1)}.get(rarity, (1, 2))
            total = geo_rng.randint(base[0], base[1])
            self.geology_deposits.append(
                GeologyDeposit(
                    id=next_dep_id,
                    x=x,
                    y=y,
                    z=z,
                    kind="gem",
                    material=mat,
                    rarity=rarity,
                    total_yield=total,
                    remaining_yield=total,
                )
            )
            next_dep_id += 1

        # Cavern regions: contiguous open pockets on deeper bands.
        cavern_z = self.depth - 1
        for _ in range(2):
            cx = geo_rng.randint(3, max(3, self.width - 4))
            cy = geo_rng.randint(3, max(3, self.height - 4))
            radius = geo_rng.randint(2, 4)
            for yy in range(max(0, cy - radius), min(self.height, cy + radius + 1)):
                for xx in range(max(0, cx - radius), min(self.width, cx + radius + 1)):
                    if abs(xx - cx) + abs(yy - cy) <= radius + geo_rng.randint(0, 1):
                        self.geology_cavern_tiles.add((xx, yy, cavern_z))
