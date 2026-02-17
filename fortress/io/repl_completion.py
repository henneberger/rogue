from __future__ import annotations

import os
import shlex
from typing import List

from fortress.models import LABORS


PANEL_NAMES = [
    "world",
    "worldgen",
    "flora",
    "geology",
    "rooms",
    "dwarves",
    "jobs",
    "stocks",
    "events",
    "factions",
    "squads",
    "justice",
    "culture",
]

ZONE_KINDS = ["farm", "recreation", "temple", "dormitory", "hospital", "pasture", "burrow"]
STOCKPILE_KINDS = ["raw", "cooked", "drink", "food", "materials", "goods", "medical", "furniture", "general"]
ALERT_KINDS = ["peace", "raid"]
FACTION_STANCES = ["allied", "neutral", "hostile"]
REVEAL_OPTS = ["off", "0", "false"]


def _split_tokens(line: str) -> List[str]:
    stripped = line.rstrip()
    if not stripped:
        return []
    trailing_space = line.endswith(" ")
    try:
        toks = shlex.split(stripped)
    except ValueError:
        toks = stripped.split()
    if trailing_space:
        toks.append("")
    return toks


def _prefix_filter(candidates: List[str], prefix: str) -> List[str]:
    out = [c for c in candidates if c.startswith(prefix)]
    out = sorted(set(out))
    return out


def _ids(rows) -> List[str]:
    return [str(r.id) for r in rows]


def _z_values(g) -> List[str]:
    return [str(z) for z in range(g.depth)]


def _xy_values(n: int) -> List[str]:
    upper = min(32, n)
    return [str(i) for i in range(upper)]


def _path_candidates(prefix: str) -> List[str]:
    base = os.path.expanduser(prefix or ".")
    dirname = os.path.dirname(base) if os.path.dirname(base) else "."
    partial = os.path.basename(base)
    out: List[str] = []
    try:
        for entry in os.listdir(dirname):
            if not entry.startswith(partial):
                continue
            full = os.path.join(dirname, entry)
            shown = os.path.join(os.path.dirname(prefix), entry) if os.path.dirname(prefix) else entry
            if os.path.isdir(full):
                shown += "/"
            out.append(shown)
    except OSError:
        return []
    return sorted(out)


def complete(g, line_buffer: str, text: str) -> List[str]:
    tokens = _split_tokens(line_buffer)
    if not tokens:
        return _prefix_filter(
            [
                ".",
                "<",
                ">",
                "help",
                "render",
                "status",
                "tick",
                "z",
                "add",
                "zone",
                "stockpile",
                "build",
                "order",
                "dig",
                "set",
                "labor",
                "forbid",
                "allow",
                "squad",
                "faction",
                "alert",
                "panel",
                "reveal",
                "flora",
                "prospect",
                "items",
                "alerts",
                "save",
                "load",
                "load_defs",
                "export",
                "run",
                "eval",
                "exec",
                "quit",
                "exit",
            ],
            text,
        )

    cmd = tokens[0]
    argi = len(tokens) - 1

    if argi == 0:
        return _prefix_filter(
            [
                ".",
                "<",
                ">",
                "help",
                "render",
                "status",
                "tick",
                "z",
                "add",
                "zone",
                "stockpile",
                "build",
                "order",
                "dig",
                "set",
                "labor",
                "forbid",
                "allow",
                "squad",
                "faction",
                "alert",
                "panel",
                "reveal",
                "flora",
                "prospect",
                "items",
                "alerts",
                "save",
                "load",
                "load_defs",
                "export",
                "run",
                "eval",
                "exec",
                "quit",
                "exit",
            ],
            text,
        )

    if cmd == "render":
        if argi == 1:
            return _prefix_filter(["geology"] + _z_values(g), text)
        if tokens[1] == "geology" and argi == 2:
            return _prefix_filter(_z_values(g), text)
        return []
    if cmd == "tick":
        return _prefix_filter(["1", "5", "10", "25", "50", "100"], text)
    if cmd == "z":
        return _prefix_filter(_z_values(g), text)
    if cmd == "add":
        if argi == 1:
            return _prefix_filter(["dwarf", "animal"], text)
        if tokens[1] == "animal":
            if argi == 2:
                return _prefix_filter(sorted(g.defs.get("creatures", {}).keys()), text)
            if argi in {3, 4}:
                return _prefix_filter(_xy_values(g.width if argi == 3 else g.height), text)
            if argi == 5:
                return _prefix_filter(_z_values(g), text)
        return []
    if cmd == "zone":
        if argi == 1:
            return _prefix_filter(ZONE_KINDS, text)
        if argi in {2, 3, 5, 6}:
            return _prefix_filter(_xy_values(g.width if argi in {2, 5} else g.height), text)
        if argi == 4:
            return _prefix_filter(_z_values(g), text)
        return []
    if cmd == "stockpile":
        if argi == 1:
            return _prefix_filter(STOCKPILE_KINDS, text)
        if argi in {2, 3, 5, 6}:
            return _prefix_filter(_xy_values(g.width if argi in {2, 5} else g.height), text)
        if argi == 4:
            return _prefix_filter(_z_values(g), text)
        return []
    if cmd == "build":
        if argi == 1:
            return _prefix_filter(["workshop"], text)
        if argi == 2 and tokens[1] == "workshop":
            return _prefix_filter(sorted(g.defs.get("recipes", {}).keys()), text)
        if argi in {3, 4} and tokens[1] == "workshop":
            return _prefix_filter(_xy_values(g.width if argi == 3 else g.height), text)
        if argi == 5 and tokens[1] == "workshop":
            return _prefix_filter(_z_values(g), text)
        return []
    if cmd == "order":
        if argi == 1:
            return _prefix_filter(_ids(g.workshops), text)
        if argi == 2:
            try:
                wsid = int(tokens[1])
            except ValueError:
                return []
            ws = next((w for w in g.workshops if w.id == wsid), None)
            if not ws:
                return []
            return _prefix_filter(sorted(g.defs.get("recipes", {}).get(ws.kind, {}).keys()), text)
        if argi == 3:
            return _prefix_filter(["1", "2", "5", "10", "20"], text)
        return []
    if cmd == "dig":
        if argi in {1, 2}:
            return _prefix_filter(_xy_values(g.width if argi == 1 else g.height), text)
        if argi in {3, 4}:
            return _prefix_filter(_z_values(g), text)
        return []
    if cmd == "set":
        if argi == 1:
            return _prefix_filter(["need", "morale", "stress"], text)
        if tokens[1] == "need":
            if argi == 2:
                return _prefix_filter(_ids(g.dwarves), text)
            if argi == 3:
                keys = sorted(next(iter(g.dwarves)).needs.keys()) if g.dwarves else []
                return _prefix_filter(keys, text)
            if argi == 4:
                return _prefix_filter(["0", "10", "25", "50", "75", "100"], text)
        if tokens[1] in {"morale", "stress"}:
            if argi == 2:
                return _prefix_filter(_ids(g.dwarves), text)
            if argi == 3:
                return _prefix_filter(["0", "10", "25", "50", "75", "100"], text)
        return []
    if cmd == "labor":
        if argi == 1:
            return _prefix_filter(_ids(g.dwarves), text)
        if argi == 2:
            return _prefix_filter(sorted(LABORS), text)
        if argi == 3:
            return _prefix_filter(["0", "1", "2", "3", "4", "5"], text)
        return []
    if cmd in {"forbid", "allow"}:
        if argi == 1:
            return _prefix_filter(_ids(g.dwarves), text)
        if argi == 2:
            return _prefix_filter(sorted(LABORS), text)
        return []
    if cmd == "squad":
        if argi == 1:
            return _prefix_filter(["create", "add"], text)
        if tokens[1] == "add":
            if argi == 2:
                return _prefix_filter(_ids(g.squads), text)
            if argi == 3:
                return _prefix_filter(_ids(g.dwarves), text)
        return []
    if cmd == "faction":
        if argi == 1:
            return _prefix_filter(["stance"], text)
        if argi == 2 and tokens[1] == "stance":
            return _prefix_filter(_ids(g.factions), text)
        if argi == 3 and tokens[1] == "stance":
            return _prefix_filter(FACTION_STANCES, text)
        return []
    if cmd == "alert" and argi == 1:
        return _prefix_filter(ALERT_KINDS, text)
    if cmd == "panel" and argi == 1:
        return _prefix_filter(PANEL_NAMES, text)
    if cmd == "reveal":
        if argi == 1:
            return _prefix_filter(["geology"], text)
        if argi == 2 and tokens[1] == "geology":
            return _prefix_filter(REVEAL_OPTS, text)
        return []
    if cmd == "flora" and argi == 1:
        return _prefix_filter(["at"], text)
    if cmd == "flora" and len(tokens) > 1 and tokens[1] == "at":
        if argi in {2, 3}:
            return _prefix_filter(_xy_values(g.width if argi == 2 else g.height), text)
        if argi == 4:
            return _prefix_filter(_z_values(g), text)
        return []
    if cmd == "prospect":
        if argi in {1, 2}:
            return _prefix_filter(_xy_values(g.width if argi == 1 else g.height), text)
        if argi == 3:
            return _prefix_filter(_z_values(g), text)
        return []
    if cmd in {"save", "load", "run", "load_defs"} and argi == 1:
        return _prefix_filter(_path_candidates(text), text)
    if cmd == "export":
        if argi == 1:
            return _prefix_filter(["replay"], text)
        if argi == 2 and tokens[1] == "replay":
            return _prefix_filter(_path_candidates(text), text)
        return []
    return []
