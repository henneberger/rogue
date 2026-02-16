from __future__ import annotations

from typing import Any, List, Optional

from fortress.models import Dwarf, Job, clamp


class JobSystemsMixin:
    def _assign_job(self, dwarf: Dwarf) -> Job:
        # Critical needs first.
        if dwarf.needs["hunger"] >= 70:
            meal = self._find_item(kind="cooked_food")
            if not meal and dwarf.needs["hunger"] >= 90:
                meal = self._find_item(kind="raw_food")
            if meal:
                meal.reserved_by = dwarf.id
                return self._new_job(kind="eat", labor="cook", item_id=meal.id, destination=self._item_pos(meal), phase="to_item")

        if dwarf.needs["alcohol"] >= 60 or dwarf.needs["thirst"] >= 70:
            drink = self._find_item(kind="alcohol")
            if drink:
                drink.reserved_by = dwarf.id
                return self._new_job(kind="drink", labor="brew", item_id=drink.id, destination=self._item_pos(drink), phase="to_item")

        if dwarf.needs["sleep"] >= 75 and self._find_zone("dormitory"):
            bed = self._assigned_bed_for_dwarf(dwarf.id)
            if bed and bed.reserved_by is None:
                bed.reserved_by = dwarf.id
                return self._new_job(kind="sleep", labor="sleep", item_id=bed.id, destination=self._item_pos(bed), phase="to_bed", remaining=5)
            bed = self._find_item(kind="bed")
            if bed and bed.reserved_by is None:
                bed.reserved_by = dwarf.id
                return self._new_job(kind="sleep", labor="sleep", item_id=bed.id, destination=self._item_pos(bed), phase="to_bed", remaining=5)
            dorm = self._find_zone("dormitory")
            if dorm:
                return self._new_job(kind="sleep", labor="sleep", destination=dorm.random_tile(self.rng), phase="sleeping", remaining=5)

        # Hospital / medical.
        if dwarf.hp < 60 and self._find_zone("hospital") and self._labor_allowed(dwarf, "medical"):
            return self._new_job(kind="recover", labor="medical", destination=self._find_zone("hospital").random_tile(self.rng), remaining=4)

        # Combat response.
        if self.world.raid_active and dwarf.squad_id and self._labor_allowed(dwarf, "combat"):
            return self._new_job(kind="defend", labor="combat", destination=(self.width - 2, self.height // 2, dwarf.z), remaining=4)

        # Global queued jobs.
        build_job = self._pop_global_job_for_labor(dwarf, "build")
        if build_job:
            return build_job
        mine_job = self._pop_global_job_for_labor(dwarf, "mine")
        if mine_job:
            return mine_job

        # Workshop production jobs.
        ws, recipe = self._find_ordered_workshop_for_dwarf(dwarf)
        if ws and recipe:
            spec = self.defs["recipes"][ws.kind][recipe]
            consumed: List[int] = []
            for kind, qty in spec["inputs"].items():
                for _ in range(qty):
                    it = self._find_item(kind=kind)
                    if not it:
                        for cid in consumed:
                            found = self._find_item_by_id(cid)
                            if found:
                                found.reserved_by = None
                        ws.orders[recipe] += 1
                        break
                    it.reserved_by = dwarf.id
                    consumed.append(it.id)
                else:
                    continue
                break
            else:
                primary_item = consumed[0] if consumed else None
                return self._new_job(
                    kind="workshop_task",
                    labor=self._labor_for_workshop(ws.kind),
                    target_id=ws.id,
                    item_id=primary_item,
                    recipe=recipe,
                    destination=self._item_pos(self._find_item_by_id(primary_item)) if primary_item else ws.pos,
                    phase="to_input" if primary_item else "to_workshop",
                    remaining=spec.get("time", 4),
                )

        # Farming and gathering.
        if self._labor_allowed(dwarf, "harvest"):
            farm = self._find_farm_with_crops(z=dwarf.z)
            if farm:
                farm.crop_available -= 1
                return self._new_job(kind="harvest", labor="harvest", target_id=farm.id, destination=farm.random_tile(self.rng), remaining=3)

        # Hauling.
        if self._labor_allowed(dwarf, "haul"):
            item, stock = self._find_haul_candidate()
            if item and stock:
                item.reserved_by = dwarf.id
                return self._new_job(kind="haul", labor="haul", item_id=item.id, target_id=stock.id, destination=self._item_pos(item), phase="to_item")

        # Recreation, social, worship.
        if dwarf.needs["entertainment"] >= 50 and self._find_zone("recreation", dwarf.z):
            rec = self._find_zone("recreation", dwarf.z)
            return self._new_job(kind="recreate", labor="recreate", destination=rec.random_tile(self.rng), remaining=3)
        if dwarf.needs["social"] >= 50:
            peer = next((p for p in self.dwarves if p.id != dwarf.id and p.z == dwarf.z and p.hp > 0), None)
            if peer:
                return self._new_job(kind="socialize", labor="social", target_id=peer.id, destination=peer.pos, remaining=2)
        if dwarf.needs["worship"] >= 50 and self._find_zone("temple", dwarf.z):
            temple = self._find_zone("temple", dwarf.z)
            return self._new_job(kind="worship", labor="worship", destination=temple.random_tile(self.rng), remaining=3)

        # Combat training when idle.
        if dwarf.squad_id and self._labor_allowed(dwarf, "combat") and self.rng.random() < 0.2:
            return self._new_job(kind="train", labor="combat", destination=dwarf.pos, remaining=3)

        return self._new_job(kind="wander", labor="recreate", remaining=2)

    def _perform_job_step(self, dwarf: Dwarf) -> None:
        job = dwarf.job
        if job is None:
            dwarf.state = "idle"
            return

        if not self._labor_allowed(dwarf, job.labor):
            self._release_job_item(dwarf, job)
            dwarf.job = None
            dwarf.state = "idle"
            return

        if job.kind == "haul":
            self._perform_haul_step(dwarf, job)
            return
        if job.kind == "workshop_task":
            self._perform_workshop_task_step(dwarf, job)
            return
        if job.kind in {"eat", "drink", "sleep"}:
            self._perform_need_job_step(dwarf, job)
            return

        self._step_move_toward(dwarf, job.destination)
        job.remaining -= 1
        dwarf.state = job.kind
        if job.remaining > 0:
            return

        if job.kind == "build_workshop":
            ws = self._find_workshop(job.target_id)
            if ws:
                ws.built = True
                self._gain_skill(dwarf, "build", 1)
        elif job.kind == "dig_stairs":
            to_z = job.target_id if job.target_id is not None else dwarf.z
            dwarf.z = clamp(to_z, 0, self.depth - 1)
            self._gain_skill(dwarf, "mine", 1)
            self._spawn_item("stone", dwarf.x, dwarf.y, dwarf.z, material="granite", value=1)
            self._log("mining", f"A stairway was dug at ({dwarf.x},{dwarf.y}) to z={dwarf.z}", 1)
        elif job.kind == "harvest":
            self._spawn_item("raw_food", dwarf.x, dwarf.y, dwarf.z, material="plump-helmet", perishability=130, value=2)
            self._spawn_item("seed", dwarf.x, dwarf.y, dwarf.z, material="plump-helmet-spawn", value=1)
            if self.rng.random() < 0.25:
                self._spawn_item("fiber", dwarf.x, dwarf.y, dwarf.z, material="pig-tail", value=2)
            self._gain_skill(dwarf, "harvest", 1)
        elif job.kind == "recover":
            dwarf.hp = clamp(dwarf.hp + 10, 0, 100)
            if dwarf.wounds and self.rng.random() < 0.6:
                dwarf.wounds.pop(0)
            dwarf.stress = clamp(dwarf.stress - 5, 0, 100)
        elif job.kind == "defend":
            self._gain_skill(dwarf, "combat", 1)
            dwarf.needs["safety"] = clamp(dwarf.needs["safety"] - 8, 0, 100)
        elif job.kind == "train":
            squad = self._find_squad(dwarf.squad_id)
            if squad:
                squad.training = clamp(squad.training + 1, 0, 200)
        elif job.kind == "recreate":
            dwarf.needs["entertainment"] = clamp(dwarf.needs["entertainment"] - 25, 0, 100)
            dwarf.morale = clamp(dwarf.morale + 6, 0, 100)
            dwarf.stress = clamp(dwarf.stress - 4, 0, 100)
        elif job.kind == "socialize":
            peer = next((p for p in self.dwarves if p.id == job.target_id), None)
            if peer:
                dwarf.needs["social"] = clamp(dwarf.needs["social"] - 25, 0, 100)
                dwarf.relationships[peer.id] = clamp(dwarf.relationships.get(peer.id, 0) + 2, -100, 100)
                peer.relationships[dwarf.id] = clamp(peer.relationships.get(dwarf.id, 0) + 2, -100, 100)
                self._remember(dwarf, f"Shared a conversation with {peer.name}")
        elif job.kind == "worship":
            dwarf.needs["worship"] = clamp(dwarf.needs["worship"] - 30, 0, 100)
            dwarf.morale = clamp(dwarf.morale + 3, 0, 100)
            self.world.culture_points += 1
        elif job.kind == "wander":
            dwarf.morale = clamp(dwarf.morale + 1, 0, 100)

        dwarf.job = None
        dwarf.state = "idle"

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

    def _pop_global_job_for_labor(self, dwarf: Dwarf, labor: str) -> Optional[Job]:
        if not self._labor_allowed(dwarf, labor):
            return None
        candidates = [j for j in self.jobs if j.labor == labor]
        if not candidates:
            return None
        candidates.sort(key=lambda j: j.id)
        job = candidates[0]
        self.jobs.remove(job)
        return job

    def _new_job(self, **kwargs: Any) -> Job:
        j = Job(id=self.next_job_id, **kwargs)
        self.next_job_id += 1
        return j

    def _labor_allowed(self, dwarf: Dwarf, labor: str) -> bool:
        return labor in dwarf.allowed_labors and dwarf.labor_priority.get(labor, 3) > 0

    def _labor_for_workshop(self, workshop_kind: str) -> str:
        return {
            "kitchen": "cook",
            "brewery": "brew",
            "carpenter": "craft",
            "mason": "craft",
            "craftdwarf": "craft",
            "smithy": "craft",
            "loom": "craft",
            "leatherworks": "craft",
        }.get(workshop_kind, "craft")

    def _gain_skill(self, dwarf: Dwarf, labor: str, amount: int) -> None:
        dwarf.skills[labor] = dwarf.skills.get(labor, 0) + amount
