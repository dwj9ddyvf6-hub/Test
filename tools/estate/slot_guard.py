#!/usr/bin/env python3
"""Owner routing with authorization retained, plus the worker-slot cap
with a plus-one human slot (T-53, mechanized).

Two mechanisms that were TACIT (no executable check existed):
  1. Slots: worker slots are capped and reserved BEFORE work starts.
     During the owner's active hours one slot always remains free; a
     follow-up from the owner may use it by exceeding the worker cap by
     exactly one. A second human-slot use, or any worker reservation
     past the cap, is refused.
  2. Owner routing: a follow-up on work that already has a live owner
     (tracked item, goal, workflow, open thread) routes straight to that
     owner without re-triage, BUT the sender and authorization check
     still runs on the bypass every time. An unauthorized sender is
     refused even when an owner exists; the source system's
     no-sender-check subscription delivery is expressly rejected.
State is a JSON file of reservations; the guard is the check, callers
reserve through it before starting work.

Usage: slot_guard.py selftest
Library: SlotGuard(state_path, worker_cap=4); route_followup(...)
"""
import json, os, sys, tempfile

class SlotError(Exception):
    pass

class SlotGuard:
    def __init__(self, state_path, worker_cap=4):
        self.path = state_path
        self.worker_cap = worker_cap
        self.state = {"workers": [], "human_slot_used_by": None}
        if os.path.isfile(state_path):
            self.state = json.load(open(state_path, encoding="utf-8"))

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.state, f)
        os.replace(tmp, self.path)

    def reserve_worker(self, job_id):
        if job_id in self.state["workers"]:
            return True  # idempotent re-reserve of the same job
        if len(self.state["workers"]) >= self.worker_cap:
            raise SlotError(
                f"worker cap {self.worker_cap} reached; the remaining slot is the human slot, workers may not use it")
        self.state["workers"].append(job_id)
        self._save()
        return True

    def reserve_human(self, request_id):
        if self.state["human_slot_used_by"] not in (None, request_id):
            raise SlotError("human slot already in use: owner follow-ups may exceed the cap by exactly one, not two")
        self.state["human_slot_used_by"] = request_id
        self._save()
        return True

    def release(self, job_id):
        if job_id in self.state["workers"]:
            self.state["workers"].remove(job_id)
        if self.state["human_slot_used_by"] == job_id:
            self.state["human_slot_used_by"] = None
        self._save()
        return True

def route_followup(owner, sender_authorized):
    """Route to the live owner without re-triage, authorization retained."""
    if not sender_authorized:
        return {"routed": False, "reason": "authorization check failed on the bypass: refused even though an owner exists"}
    if not owner:
        return {"routed": False, "reason": "no live owner: normal triage applies"}
    return {"routed": True, "owner": owner, "reason": "routed to live owner, authorization checked"}

def selftest():
    with tempfile.TemporaryDirectory() as td:
        g = SlotGuard(os.path.join(td, "slots.json"), worker_cap=2)
        assert g.reserve_worker("w1") and g.reserve_worker("w2")
        try:
            g.reserve_worker("w3"); raise SystemExit("third worker must be refused at cap")
        except SlotError:
            pass
        assert g.reserve_human("owner-ask-1")
        try:
            g.reserve_human("owner-ask-2"); raise SystemExit("second human-slot use must be refused")
        except SlotError:
            pass
        g.release("w1")
        assert g.reserve_worker("w3"), "released slot must be reservable"
        assert route_followup("desk-lane", True)["routed"]
        assert not route_followup("desk-lane", False)["routed"], "unauthorized sender must be refused on the bypass"
        assert not route_followup(None, True)["routed"]
        print("SELFTEST PASS slot_guard: worker cap enforced, human slot exceeds by exactly one, release frees a slot, owner routing requires authorization every time")
    return 0

if __name__ == "__main__":
    raise SystemExit(selftest() if len(sys.argv) > 1 and sys.argv[1] == "selftest" else print(__doc__))
