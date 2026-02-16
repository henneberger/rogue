# DF-like Console Colony Prototype

Console-first colony simulation with an introspectable REPL and deterministic seed-driven tick loop.

Roadmap: `/Users/henneberger/game2/docs/ROADMAP_DF_COMPLEXITY.md`
Coverage status: `/Users/henneberger/game2/docs/ROADMAP_COVERAGE_STATUS.md`

## Code Layout

- `/Users/henneberger/game2/game.py`: launcher entrypoint.
- `/Users/henneberger/game2/fortress/models.py`: entities, dataclasses, constants/helpers.
- `/Users/henneberger/game2/fortress/engine.py`: `Game` state + tick coordinator + shared helpers.
- `/Users/henneberger/game2/fortress/cli.py`: interactive REPL loop.
- `/Users/henneberger/game2/fortress/systems/`: simulation subsystems (`jobs`, `world`, `needs`, `social`, `justice`).
- `/Users/henneberger/game2/fortress/io/`: REPL command dispatch, rendering/panels, save/load/replay.

## Run

```bash
python3 /Users/henneberger/game2/game.py
```

## Quick Start

```text
zone farm 1 8 0 6 3
zone recreation 20 1 0 5 3
zone temple 20 5 0 4 3
zone dormitory 12 10 0 6 3
zone hospital 1 1 0 4 2
zone pasture 24 10 0 5 4
stockpile raw 8 8 0 4 3
stockpile cooked 13 8 0 4 3
stockpile drink 18 8 0 4 3
stockpile materials 1 12 0 8 3
build workshop kitchen 11 7 0
build workshop brewery 16 7 0
build workshop carpenter 21 7 0
tick 20
order 1 meal 4
order 2 brew 3
order 3 bed 2
tick 25
status
panel events
```

## Core Features

- Multi-z-level world with weather, seasons, and raid pressure.
- Dwarves with multi-need simulation (`hunger`, `thirst`, `sleep`, `social`, `worship`, `entertainment`, `safety`), stress, moods, skills, labor priorities, and allowed/forbidden labors.
- Zones: `farm`, `recreation`, `temple`, `dormitory`, `hospital`, `pasture`, `burrow`.
- Workshops: `kitchen`, `brewery`, `carpenter`, `mason`, `craftdwarf`, `smithy`, `loom`, `leatherworks` with recipe orders.
- Item/entity simulation with materials, quality, value, perishability, ownership/reservation/carried state.
- Food sim v2: nutrition pressure, storage-sensitive spoilage, and alcohol dependency effects.
- Stockpiles with typed acceptance and hauling jobs.
- Social memory and relationship updates.
- Justice events and crime records.
- Squads, raid alerts, basic defense/training loop, injury/recovery.
- Culture/scholarship points and occasional artifact creation.
- Room detection/valuation and dwarf room assignment with quality effects.
- Biome-aware flora simulation with real species (scientific names), growth stages, stress, dormancy, and spreading.
- Save/load, replay export, scripted command execution, data-definition loading (`load_defs`).

## REPL Commands

- `help`
- `render [z]`
- `status`
- `tick [n]`
- `z <level>`
- `add dwarf [name]`
- `add animal <species> <x> <y> <z>`
- `zone <kind> <x> <y> <z> <w> <h>`
- `stockpile <kind> <x> <y> <z> <w> <h>`
- `build workshop <kind> <x> <y> <z>`
- `order <workshop_id> <recipe> <amount>`
- `dig <x> <y> <from_z> <to_z>`
- `set need <dwarf_id> <need> <value>`
- `set morale <dwarf_id> <value>`
- `set stress <dwarf_id> <value>`
- `labor <dwarf_id> <labor> <0..5>`
- `forbid <dwarf_id> <labor>` / `allow <dwarf_id> <labor>`
- `squad create <name>`
- `squad add <squad_id> <dwarf_id>`
- `faction stance <faction_id> <allied|neutral|hostile>`
- `alert <peace|raid>`
- `panel <world|worldgen|flora|rooms|dwarves|jobs|stocks|events|factions|squads|justice|culture>`
- `flora at <x> <y> <z>`
- `items`
- `alerts`
- `save <path>` / `load <path>`
- `load_defs <path>`
- `export replay <path>`
- `run <script_path>`
- `eval <python-expression>`
- `exec <python-statement>`
- `quit`

## Introspection Examples

```text
eval g.world
eval [(d.id, d.mood, d.stress, d.needs) for d in g.dwarves]
panel jobs
panel stocks
panel flora
flora at 10 5 0
items
exec g.tick(50)
```
