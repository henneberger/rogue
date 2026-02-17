from __future__ import annotations

import shlex

from fortress.models import LABORS, Squad, clamp


class CommandMixin:
    def handle_command(self, raw: str) -> str:
        raw = raw.strip()
        if not raw:
            return ""
        parts = shlex.split(raw)
        cmd = parts[0].lower()

        if cmd not in {"eval", "exec"}:
            self.command_log.append(raw)

        if cmd == "help":
            return help_text()
        if cmd == "render":
            if len(parts) == 2:
                return self.render(int(parts[1]))
            return self.render()
        if cmd == "status":
            return self.status()
        if cmd == "tick":
            n = int(parts[1]) if len(parts) > 1 else 1
            self.tick(n)
            return self.render()
        if cmd == "z" and len(parts) == 2:
            self.selected_z = clamp(int(parts[1]), 0, self.depth - 1)
            return f"selected z-level {self.selected_z}"
        if cmd == "add" and len(parts) >= 2 and parts[1] == "dwarf":
            name = parts[2] if len(parts) > 2 else None
            d = self.add_dwarf(name=name, z=self.selected_z)
            return f"added dwarf [{d.id}] {d.name} at ({d.x},{d.y},{d.z})"
        if cmd == "add" and len(parts) == 6 and parts[1] == "animal":
            a = self.add_animal(parts[2], int(parts[3]), int(parts[4]), int(parts[5]))
            return f"added animal [{a.id}] {a.species}"
        if cmd == "zone" and len(parts) == 7:
            zt = self.add_zone(parts[1], int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6]))
            return f"added zone [{zt.id}] {zt.kind}"
        if cmd == "stockpile" and len(parts) == 7:
            sp = self.add_stockpile(parts[1], int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6]))
            return f"added stockpile [{sp.id}] {sp.kind}"
        if cmd == "build" and len(parts) == 6 and parts[1] == "workshop":
            ws = self.queue_build_workshop(parts[2], int(parts[3]), int(parts[4]), int(parts[5]))
            return f"queued workshop [{ws.id}] {ws.kind} at ({ws.x},{ws.y},{ws.z})"
        if cmd == "order" and len(parts) == 4:
            self.order_workshop(int(parts[1]), parts[2], int(parts[3]))
            return "order queued"
        if cmd == "dig" and len(parts) == 5:
            self.queue_dig(int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]))
            return "dig job queued"
        if cmd == "set" and len(parts) == 5 and parts[1] == "need":
            d = self._find_dwarf(int(parts[2]))
            if not d:
                return "dwarf not found"
            key = parts[3]
            if key not in d.needs:
                return "unknown need"
            d.needs[key] = clamp(int(parts[4]), 0, 100)
            return f"set dwarf {d.id} need {key}={d.needs[key]}"
        if cmd == "set" and len(parts) == 4 and parts[1] == "morale":
            d = self._find_dwarf(int(parts[2]))
            if not d:
                return "dwarf not found"
            d.morale = clamp(int(parts[3]), 0, 100)
            return f"set morale {d.id}={d.morale}"
        if cmd == "set" and len(parts) == 4 and parts[1] == "stress":
            d = self._find_dwarf(int(parts[2]))
            if not d:
                return "dwarf not found"
            d.stress = clamp(int(parts[3]), 0, 100)
            return f"set stress {d.id}={d.stress}"
        if cmd == "labor" and len(parts) == 4:
            d = self._find_dwarf(int(parts[1]))
            if not d:
                return "dwarf not found"
            labor = parts[2]
            if labor not in LABORS:
                return "unknown labor"
            d.labor_priority[labor] = clamp(int(parts[3]), 0, 5)
            return f"set labor priority dwarf={d.id} {labor}={d.labor_priority[labor]}"
        if cmd in {"forbid", "allow"} and len(parts) == 3:
            d = self._find_dwarf(int(parts[1]))
            if not d:
                return "dwarf not found"
            labor = parts[2]
            if labor not in LABORS:
                return "unknown labor"
            if cmd == "forbid":
                d.allowed_labors.discard(labor)
            else:
                d.allowed_labors.add(labor)
            return f"{cmd} {labor} for dwarf {d.id}"
        if cmd == "squad" and len(parts) >= 2:
            sub = parts[1]
            if sub == "create" and len(parts) == 3:
                s = Squad(id=self.next_squad_id, name=parts[2])
                self.next_squad_id += 1
                self.squads.append(s)
                return f"created squad [{s.id}] {s.name}"
            if sub == "add" and len(parts) == 4:
                s = self._find_squad(int(parts[2]))
                d = self._find_dwarf(int(parts[3]))
                if not s or not d:
                    return "squad or dwarf not found"
                if d.id not in s.members:
                    s.members.append(d.id)
                    d.squad_id = s.id
                return f"assigned dwarf {d.id} to squad {s.id}"
        if cmd == "faction" and len(parts) == 4 and parts[1] == "stance":
            f = self._find_faction(int(parts[2]))
            if not f:
                return "faction not found"
            f.stance = parts[3]
            return "faction updated"
        if cmd == "alert" and len(parts) == 2:
            if parts[1] == "raid":
                self.world.raid_active = True
                self.world.threat_level = max(self.world.threat_level, 2)
            else:
                self.world.raid_active = False
                self.world.threat_level = 0
            return f"alert set to {parts[1]}"
        if cmd == "panel" and len(parts) == 2:
            return self.panel(parts[1])
        if cmd == "flora" and len(parts) == 5 and parts[1] == "at":
            return self.flora_at(int(parts[2]), int(parts[3]), int(parts[4]))
        if cmd == "items":
            return self.items_dump()
        if cmd == "alerts":
            return self.alerts_dump()
        if cmd == "save" and len(parts) == 2:
            self.save_json(parts[1])
            return f"saved {parts[1]}"
        if cmd == "load" and len(parts) == 2:
            ng = self.__class__.load_json(parts[1])
            self.__dict__.update(ng.__dict__)
            return f"loaded {parts[1]}"
        if cmd == "load_defs" and len(parts) == 2:
            self.load_defs(parts[1])
            return "definitions loaded"
        if cmd == "export" and len(parts) == 3 and parts[1] == "replay":
            self.export_replay(parts[2])
            return f"replay exported to {parts[2]}"
        if cmd == "run" and len(parts) == 2:
            outs = self.run_script(parts[1])
            return "\n".join(outs[-10:])
        if cmd == "eval":
            expr = raw[5:].strip()
            return repr(eval(expr, {}, {"g": self}))
        if cmd == "exec":
            stmt = raw[5:].strip()
            local = {"g": self}
            exec(stmt, {}, local)
            return "ok"
        if cmd in {"quit", "exit"}:
            raise SystemExit

        return "unknown command"


def help_text() -> str:
    return (
        "Commands:\n"
        "  help\n"
        "  render [z]\n"
        "  status\n"
        "  tick [n]\n"
        "  z <level>\n"
        "  add dwarf [name]\n"
        "  add animal <species> <x> <y> <z>\n"
        "  zone <kind> <x> <y> <z> <w> <h>\n"
        "    kinds: farm recreation temple dormitory hospital pasture burrow\n"
        "  stockpile <kind> <x> <y> <z> <w> <h>\n"
        "    kinds: raw cooked drink food materials goods medical furniture general\n"
        "  build workshop <kind> <x> <y> <z>\n"
        "    kinds: kitchen kitchen_advanced brewery carpenter mason craftdwarf smithy loom leatherworks butcher tanner farmer mill quern furnace weaponsmith armorsmith blacksmith jeweler siege mechanic ashery dyer soapmaker potter bowyer fletcher paper scribe apothecary doctor\n"
        "  order <workshop_id> <recipe> <amount>\n"
        "  dig <x> <y> <from_z> <to_z>\n"
        "  set need <dwarf_id> <need> <value>\n"
        "  set morale <dwarf_id> <value>\n"
        "  set stress <dwarf_id> <value>\n"
        "  labor <dwarf_id> <labor> <0..5>\n"
        "  forbid <dwarf_id> <labor> | allow <dwarf_id> <labor>\n"
        "  squad create <name>\n"
        "  squad add <squad_id> <dwarf_id>\n"
        "  faction stance <faction_id> <allied|neutral|hostile>\n"
        "  alert <peace|raid>\n"
        "  panel <world|worldgen|flora|rooms|dwarves|jobs|stocks|events|factions|squads|justice|culture>\n"
        "  flora at <x> <y> <z>\n"
        "  items\n"
        "  alerts\n"
        "  save <path> | load <path>\n"
        "  load_defs <path>\n"
        "  export replay <path>\n"
        "  run <script_path>\n"
        "  eval <python_expr>\n"
        "  exec <python_stmt>\n"
        "  quit\n"
    )
