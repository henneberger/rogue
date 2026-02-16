# Dwarf Fortress-Scale Roadmap (Console-First)

This document defines the feature scope to grow this project from a minimal prototype into a game with complexity in the same *class* as Dwarf Fortress.

Guiding constraints:
- Console-first rendering and interaction must remain supported at all times.
- Every core system must be inspectable in REPL/debug commands for tight iteration.
- Systems are built in vertical slices (playable each phase), not isolated tech spikes.

## Current State (Implemented)
- Dwarves with basic needs (`hunger`, `morale`) and simple autonomous job selection.
- Zones: `farm`, `recreation`.
- Workshop: constructible `kitchen`, cook orders.
- Resource loop: harvest -> cook -> consume.
- Idle behavior: wander/recreate.

## Target Feature Pillars
1. Living simulation with many interacting subsystems.
2. Emergent stories from AI decisions and world events.
3. Deep production chains and logistics.
4. Layered simulation (individual, colony, world).
5. Failure states and recoveries (injury, starvation, raids, collapse).

## Full Feature Inventory

### 1) World and Map Simulation
- Multi-layer map (surface + underground z-levels).
- Biomes with climate, rainfall, temperature, seasonal shifts.
- Tile materials (soil, stone, ore veins, aquifers).
- Procedural world generation with regions and history seeds.
- Fluids (water, magma) with pressure/spread rules.
- Weather events (rain, storms, drought, cold snaps).

### 2) Colony Core and Labor
- Custom labor priorities per dwarf.
- Skill levels and skill rust (use it or lose it).
- Work details/professions (miner, mason, cook, doctor, hauler).
- Job manager: recurring, one-off, conditional orders.
- Burrows and restricted work areas.
- Shift schedules and alert states.

### 3) Needs, Personality, and Social Simulation
- Expanded needs: sleep, thirst, safety, social, worship, entertainment.
- Personality traits and preferences (materials, food, values).
- Relationships: friendships, rivalries, families.
- Mood/memory system that affects behavior and performance.
- Stress breakdowns, tantrums, inspirations.
- Social events: conversations, gatherings, arguments.

### 4) Economy, Items, and Logistics
- Unified item entity system (quality, material, wear, ownership).
- Stockpiles with filters, links, and priorities.
- Hauling jobs and transport bottlenecks.
- Tool/equipment requirements for jobs.
- Trade depots, caravans, and negotiated barter.
- Value and wealth tracking (attracts events/threats).

### 5) Production and Crafting Chains
- Core workshops: carpenter, mason, craftsdwarf, smithy, kitchen, brewery, loom, leatherworks.
- Input/output recipes with byproducts.
- Fuel/energy dependencies (charcoal, coke, power later).
- Quality tiers and masterpiece outputs.
- Automation rules for production targets.
- Material science interactions (metal tiers, alloy recipes).

### 6) Agriculture, Animals, and Food Systems
- Seasonal farming and crop rotation.
- Seed economy and spoilage/perishability.
- Brewing and alcohol dependency behavior.
- Animal husbandry, breeding, grazing, shearing, milking.
- Hunting/fishing and ecosystem pressure.
- Kitchens with meal complexity and nutrition effects.

### 7) Construction and Architecture
- Digging channels, ramps, stairs, smoothing/engraving.
- Structural supports and cave-in simulation.
- Room requirements and value calculations.
- Furniture placement and room assignment.
- Defensive engineering: walls, traps, drawbridges.
- Power systems (water wheels, windmills, gear assemblies).

### 8) Health and Medicine
- Body-part model with wounds and pain.
- Disease/infection and sanitation effects.
- Medical jobs: diagnosis, suturing, setting bones, recovery.
- Hospitals with bed/supply requirements.
- Permanent injuries and prosthetic progression (long-term).

### 9) Combat and Threats
- Squad creation, training, equipment loadouts.
- Real-time simulation with pause/step tactical control.
- Siege/raid AI with goals and retreat logic.
- Traps, fortifications, chokepoints.
- Morale routing and panic cascades.
- Wildlife threats and megafauna encounters.

### 10) Factions, Diplomacy, and World Events
- Neighbor civilizations and political stances.
- Tribute/trade/war states and reputation impacts.
- Immigration waves and petition systems.
- Nobility and mandates (with penalties).
- Story events: artifacts, forgotten beasts, cults.

### 11) Justice, Law, and Governance
- Crime simulation (theft, assault, vandalism).
- Investigation and witness systems.
- Courts, punishments, prisons.
- Edicts and colony policies.

### 12) Knowledge, Religion, and Culture
- Deities, temples, and religious preferences.
- Art generation tied to historical events.
- Libraries, writing, and scholarship progression.
- Performance/poetry/music systems and venue needs.

### 13) UI/UX and Tooling (Console-First)
- Multi-panel console views (map, alerts, jobs, dwarves, stocks).
- Configurable hotkeys and command macros.
- Search/filter for dwarves, items, jobs, buildings.
- Timeline/event log with drill-down detail.
- Deterministic replay mode from seeds + command logs.

### 14) Save/Load and Debug Infrastructure
- Versioned save format with migration support.
- Snapshot inspector for any tick.
- Command scripting for automated simulation tests.
- Debug overlays (pathing cost, room value, fluid pressure).
- Metrics export (JSON/CSV) for balancing.

### 15) Modding and Data-Driven Content
- Data-defined materials, creatures, workshops, recipes.
- External content packs loaded at startup.
- Validation tools for mod schemas.
- Script hooks for events and AI behaviors.

## Phase Plan (Execution Order)

### Phase 1: Strong Fortress Loop (near-term)
Goal: turn current prototype into a robust management game.
- Implement stockpiles + hauling.
- Add bedrooms/dormitory + sleep need.
- Add brewery + alcohol production/consumption.
- Expand farm mechanics (seasons + seeds).
- Add carpenter/mason workshops and furniture chain.
- Add labor priorities and simple scheduler UI.

Exit criteria:
- A 1-year colony sim can run without manual micromanagement.
- Failure modes include starvation, exhaustion, morale collapse.

### Phase 2: Structural Depth
Goal: deep base-building and logistics strategy.
- Multi-z-level map and mining.
- Stone/wood industries with quality outputs.
- Room value and assignment system.
- Burrows/work zones and traffic restrictions.
- Fluids v1 (water only).

Exit criteria:
- Players can design meaningful fortress layouts and logistics networks.

### Phase 3: Society and Events
Goal: emergent stories from social simulation.
- Personality, memories, relationships.
- Immigration and faction-driven events.
- Justice/prison systems.
- Stress events and mood spirals.

Exit criteria:
- Colonies produce distinct social outcomes under similar maps.

### Phase 4: Combat and Survival Pressure
Goal: external pressure drives strategic defense.
- Militia, equipment, training loops.
- Raids/sieges and tactical alerts.
- Traps/fortifications.
- Health/medical pipeline.

Exit criteria:
- Military and medicine become core, not optional.

### Phase 5: World Simulation and Long-Run Complexity
Goal: fortress embedded in a living world.
- Worldgen with neighboring civs/history.
- Diplomacy/trade/war states.
- Advanced creatures and rare events.
- Culture/religion/scholarship systems.

Exit criteria:
- Multi-year forts produce unique world-connected narratives.

## Engineering Architecture Targets
- ECS-style or data-oriented entity storage for scale.
- Tick pipeline with explicit phases (needs -> jobs -> movement -> actions -> events).
- Deterministic simulation under fixed seed.
- Pathfinding service with cache/invalidation.
- Event bus for decoupled subsystem interactions.
- Data-driven definitions for recipes, materials, creatures.

## Testing and Verification Strategy
- Unit tests for deterministic subsystem rules.
- Simulation tests for production chains and starvation edge cases.
- Long-run soak tests (10k+ ticks) for deadlocks/perf regressions.
- Golden-output replay tests for deterministic behavior.

## Immediate Next Build Backlog (Recommended)
1. Introduce `Item` + `Stockpile` system and refactor food into item entities.
2. Add `bed` workshop/furniture and sleep need.
3. Implement labor priorities and per-dwarf allowed/disallowed work.
4. Add simple event log panel and filters.
5. Add save/load (JSON) and deterministic replay command log.

## Definition of “DF-like Complexity” for This Project
- 10+ interconnected core subsystems (needs, labor, logistics, industry, society, combat, health, diplomacy, world events, justice).
- 100+ entity types across creatures/items/buildings/materials/jobs.
- Emergent failure/success states not explicitly scripted.
- Long-duration colonies with diverging histories under different seeds and player decisions.
