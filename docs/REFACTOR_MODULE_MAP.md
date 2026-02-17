# Refactor Module Map (Issue #26)

This document maps pre-refactor responsibilities to new module locations.

## Engine Responsibilities
- `fortress/engine.py` (before):
  - `default_defs`
  - world generation (`_generate_world`)
  - core helper methods (finders, item helpers, movement, logging)
  - tick coordinator/state
- `fortress/engine.py` (after):
  - tick coordinator/state only
- `fortress/systems/defs.py`:
  - `default_defs`
- `fortress/systems/flora_catalog.py`:
  - real-species flora catalog data
- `fortress/systems/worldgen.py`:
  - `_generate_world`
- `fortress/systems/game_helpers.py`:
  - shared helpers used by systems/IO

## Jobs Responsibilities
- `fortress/systems/jobs.py` (before):
  - assignment + all execution handlers
- `fortress/systems/jobs.py` (after):
  - assignment logic + high-level job dispatch
- `fortress/systems/jobs_execution.py`:
  - haul/workshop/need execution handlers and release flow

## Compatibility
- `from fortress.engine import Game` remains unchanged.
- Existing REPL commands and panel names are unchanged.
- Save/load format remains unchanged.
