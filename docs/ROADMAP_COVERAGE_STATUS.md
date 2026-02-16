# Roadmap Coverage Status

This file tracks baseline implementation coverage of `/Users/henneberger/game2/docs/ROADMAP_DF_COMPLEXITY.md`.

Status legend:
- `Baseline`: Implemented in minimal/early form in current code.
- `Deepen`: Implemented but needs substantial depth to match late-game DF complexity.
- `Missing`: Not yet implemented.

## 1) World and Map Simulation
- Multi-z-level map: `Baseline`
- Biome/season/weather/temperature: `Baseline`
- Materialized tiles, ore veins, aquifers: `Deepen`
- Fluid pressure model (water/magma): `Baseline`
- Regional worldgen/history: `Missing`

## 2) Colony Core and Labor
- Labor priorities and allow/forbid: `Baseline`
- Skills and progression: `Baseline`
- Job manager with orders: `Baseline`
- Burrows/restricted zones: `Baseline` (zone kind exists, behavior needs depth)
- Schedules/alerts: `Baseline`

## 3) Needs, Personality, Social
- Expanded needs and stress/mood: `Baseline`
- Personality/preferences: `Deepen`
- Relationships and memories: `Baseline`
- Tantrums/inspiration: `Baseline`

## 4) Economy, Items, Logistics
- Item entity model (material/quality/value/perishability): `Baseline`
- Typed stockpiles and hauling: `Baseline`
- Ownership/tool constraints: `Deepen`
- Wealth and trade presence: `Baseline`

## 5) Production and Crafting Chains
- Multiple workshops and recipes: `Baseline`
- Input/output chain processing: `Baseline`
- Quality/value output scaling: `Baseline`
- Fuel/power/material science depth: `Missing`

## 6) Agriculture, Animals, Food
- Farm growth/harvest with seed output: `Baseline`
- Brewing and drink consumption: `Baseline`
- Animal simulation/pasture/breeding events: `Baseline`
- Full spoilage/nutrition ecology: `Deepen`

## 7) Construction and Architecture
- Workshop construction jobs: `Baseline`
- Digging jobs across z-levels: `Baseline`
- Rooms/furniture assignment and structural simulation: `Deepen`

## 8) Health and Medicine
- HP, wounds, hospital recovery jobs: `Baseline`
- Detailed body-part simulation/disease/surgery: `Missing`

## 9) Combat and Threats
- Raid state, militia squads, training, injuries: `Baseline`
- Tactical combat depth and equipment granularity: `Deepen`

## 10) Factions, Diplomacy, Events
- Factions with stance/reputation: `Baseline`
- Caravan/event hooks: `Baseline`
- Diplomacy depth and petition/nobility complexity: `Deepen`

## 11) Justice, Law, Governance
- Crime records and resolution loop: `Baseline`
- Policy/edict/court depth: `Deepen`

## 12) Knowledge, Religion, Culture
- Worship needs + temple zone: `Baseline`
- Scholarship/culture points and artifact events: `Baseline`
- Libraries/writing/performance systems: `Deepen`

## 13) UI/UX and Tooling (Console-first)
- Multi-panel console views: `Baseline`
- Alerts/event log and filters by panel: `Baseline`
- Macro/search UX depth: `Deepen`

## 14) Save/Load and Debug Infrastructure
- Save/load JSON: `Baseline`
- Replay export + script run: `Baseline`
- Deterministic seed/tick with eval/exec introspection: `Baseline`
- Full migration/golden replay framework: `Deepen`

## 15) Modding and Data-driven Content
- Data-driven recipe/creature/material defs + `load_defs`: `Baseline`
- External packs/schema validation/hook APIs: `Deepen`

## Immediate Deepening Priorities
1. Deterministic command replay loader and golden regression tests.
2. Stronger production constraints (tool/fuel stations, routing, ownership, reservations).
3. Combat/health depth (body parts, equipment, medical workflow details).
4. True worldgen with regional map and civ history.
5. Data schema validation for mod packs.
