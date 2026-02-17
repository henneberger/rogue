from __future__ import annotations

from fortress.models import Dwarf, Job, clamp


class JobExecutionMixin:
    def _perform_haul_step(self, dwarf: Dwarf, job: Job) -> None:
        item = self._find_item_by_id(job.item_id)
        stock = self._find_stockpile(job.target_id)
        dwarf.state = "haul"
        if not item or not stock:
            self._release_job_item(dwarf, job)
            dwarf.job = None
            dwarf.state = "idle"
            return

        if job.phase == "to_item":
            job.destination = self._item_pos(item)
            self._step_move_toward(dwarf, job.destination)
            if dwarf.pos == self._item_pos(item):
                item.carried_by = dwarf.id
                item.stockpile_id = None
                job.phase = "to_stockpile"
                job.destination = self._choose_stockpile_drop_tile(stock)
            return

        if job.phase == "to_stockpile":
            if self._stockpile_free_slots(stock) <= 0:
                item.carried_by = None
                item.reserved_by = None
                item.x, item.y, item.z = dwarf.x, dwarf.y, dwarf.z
                dwarf.job = None
                dwarf.state = "idle"
                return
            self._step_move_toward(dwarf, job.destination)
            if dwarf.pos == job.destination:
                item.carried_by = None
                item.reserved_by = None
                item.x, item.y, item.z = dwarf.x, dwarf.y, dwarf.z
                item.stockpile_id = stock.id
                self._gain_skill(dwarf, "haul", 1)
                dwarf.job = None
                dwarf.state = "idle"

    def _perform_workshop_task_step(self, dwarf: Dwarf, job: Job) -> None:
        ws = self._find_workshop(job.target_id)
        if not ws or not ws.built:
            self._release_job_item(dwarf, job)
            dwarf.job = None
            dwarf.state = "idle"
            return

        recipe = job.recipe or ""
        spec = self.defs.get("recipes", {}).get(ws.kind, {}).get(recipe)
        if not spec:
            dwarf.job = None
            dwarf.state = "idle"
            return

        dwarf.state = f"{ws.kind}:{recipe}"
        primary = self._find_item_by_id(job.item_id)

        if job.phase == "to_input" and primary:
            job.destination = self._item_pos(primary)
            self._step_move_toward(dwarf, job.destination)
            if dwarf.pos == self._item_pos(primary):
                primary.carried_by = dwarf.id
                primary.stockpile_id = None
                job.phase = "to_workshop"
                job.destination = ws.pos
            return

        if job.phase == "to_workshop":
            self._step_move_toward(dwarf, ws.pos)
            if dwarf.pos == ws.pos:
                job.phase = "crafting"
                job.remaining = spec.get("time", 4)
            return

        if job.phase == "crafting":
            job.remaining -= 1
            if dwarf.rested_bonus > 0 and self.rng.random() < 0.20:
                job.remaining -= 1
            if job.remaining > 0:
                return
            # Consume required inputs.
            for input_kind, qty in spec.get("inputs", {}).items():
                for _ in range(qty):
                    found = next(
                        (i for i in self.items if i.kind == input_kind and (i.reserved_by in {None, dwarf.id})),
                        None,
                    )
                    if found:
                        self._consume_item(found.id)
            # Produce outputs.
            for output_kind, qty in spec.get("outputs", {}).items():
                for _ in range(qty):
                    quality = clamp(dwarf.skills.get(job.labor, 0) // 15, 0, 5)
                    val = 1 + spec.get("value_bonus", 1) + quality
                    perish = 150 if output_kind in {"cooked_food", "raw_food", "alcohol"} else 0
                    self._spawn_item(output_kind, ws.x, ws.y, ws.z, quality=quality, value=val, perishability=perish)
            self._gain_skill(dwarf, job.labor, 1)
            dwarf.needs["entertainment"] = clamp(dwarf.needs["entertainment"] - 4, 0, 100)
            dwarf.job = None
            dwarf.state = "idle"

    def _perform_need_job_step(self, dwarf: Dwarf, job: Job) -> None:
        dwarf.state = job.kind
        item = self._find_item_by_id(job.item_id)

        if job.kind in {"eat", "drink"}:
            if not item:
                dwarf.job = None
                dwarf.state = "idle"
                return
            if job.phase == "to_item":
                job.destination = self._item_pos(item)
                self._step_move_toward(dwarf, job.destination)
                if dwarf.pos == self._item_pos(item):
                    item.carried_by = dwarf.id
                    item.stockpile_id = None
                    job.phase = "using"
                    job.remaining = 2
                return
            if job.phase == "using":
                job.remaining -= 1
                if job.remaining > 0:
                    return
                self._apply_nutrition_from_item(dwarf, item)
                self._consume_item(item.id)
                if job.kind == "eat":
                    dwarf.needs["hunger"] = clamp(dwarf.needs["hunger"] - 65, 0, 100)
                    dwarf.morale = clamp(dwarf.morale + 4, 0, 100)
                else:
                    dwarf.needs["thirst"] = clamp(dwarf.needs["thirst"] - 70, 0, 100)
                    dwarf.morale = clamp(dwarf.morale + 3, 0, 100)
                    dwarf.needs["alcohol"] = clamp(
                        dwarf.needs["alcohol"] - (45 + max(0, dwarf.alcohol_dependency // 3)),
                        0,
                        100,
                    )
                    dwarf.withdrawal_ticks = 0
                dwarf.stress = clamp(dwarf.stress - 5, 0, 100)
                dwarf.job = None
                dwarf.state = "idle"
                return

        if job.kind == "sleep":
            if job.phase == "to_bed" and item:
                job.destination = self._item_pos(item)
                self._step_move_toward(dwarf, job.destination)
                if dwarf.pos == self._item_pos(item):
                    job.phase = "sleeping"
                    job.remaining = 5
                return
            if job.phase == "sleeping":
                job.remaining -= 1
                if job.remaining > 0:
                    return
                room_value = self._dwarf_room_value(dwarf.id)
                morale_gain = min(12, 5 + room_value // 25)
                stress_recovery = min(18, 8 + room_value // 20)
                dwarf.needs["sleep"] = clamp(dwarf.needs["sleep"] - 70, 0, 100)
                dwarf.stress = clamp(dwarf.stress - stress_recovery, 0, 100)
                dwarf.morale = clamp(dwarf.morale + morale_gain, 0, 100)
                dwarf.rested_bonus = max(dwarf.rested_bonus, min(80, room_value))
                dwarf.job = None
                dwarf.state = "idle"

    def _release_job_item(self, dwarf: Dwarf, job: Job) -> None:
        item = self._find_item_by_id(job.item_id)
        if item and item.reserved_by == dwarf.id:
            item.reserved_by = None
            if item.carried_by == dwarf.id:
                item.carried_by = None
                item.x, item.y, item.z = dwarf.pos

