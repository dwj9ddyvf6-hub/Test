#!/usr/bin/env python3
"""Mechanical worker-slot cap checker (A-18, staged local form).

Implements the slot discipline from deepseek-ai/dsh-superagent-prototype
(src/policy.ts:93, src/limits.ts:6, WorkerSlots in the execution layer),
as adopted in round-4 law (worker slots plus one human slot):

- max_workers defaults to 3 and must be in the range 1 to 16; a value
  outside that range is a configuration error (exit 2), not a refusal.
- Worker slots are reserved synchronously against a single state file
  (an flock serialises the check-and-reserve, so two concurrent
  acquirers cannot both take the last slot).
- A human (owner) follow-up may exceed the worker cap by exactly one
  slot, so the owner never queues behind new launches. There is only
  one human slot: a second human reservation while one is held is
  refused, and human reservations never consume worker slots.

This tool is the invocable checker. Wiring it into the workflow
scheduler itself (acquire before every spawn, release on completion)
is a workflow-runtime change outside the adoption program's authority;
that remaining step is staged in
research_notes/adoption-implementation-20261103/staged/
A18-WORKER-SLOT-CAP-RUNTIME-INTEGRATION.md.

Usage:
  worker_slots.py status   [--state PATH] [--max-workers N]
  worker_slots.py acquire  [--state PATH] [--max-workers N] --id ID --kind worker|human
  worker_slots.py release  [--state PATH] --id ID
  worker_slots.py selftest

Exit codes: 0 ok, 2 configuration/usage error, 3 slot refused.
"""
import argparse, fcntl, json, os, sys, tempfile, time

DEFAULT_MAX_WORKERS = 3
MIN_WORKERS, MAX_WORKERS_LIMIT = 1, 16
DEFAULT_STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "worker_slots.json")


def load_state(path):
    if not os.path.exists(path):
        return {"reservations": []}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("reservations"), list):
        raise ValueError(f"corrupt slot state at {path}")
    return data


def save_state(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def with_lock(path, fn):
    """Run fn(state) -> (result, changed) holding an exclusive flock."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    lock_path = path + ".lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load_state(path)
        result, changed = fn(state)
        if changed:
            save_state(path, state)
        return result


def check_max_workers(n):
    if not (MIN_WORKERS <= n <= MAX_WORKERS_LIMIT):
        print(f"CONFIG ERROR: max_workers={n} outside range {MIN_WORKERS} to {MAX_WORKERS_LIMIT}", file=sys.stderr)
        sys.exit(2)


def counts(state):
    workers = sum(1 for r in state["reservations"] if r["kind"] == "worker")
    humans = sum(1 for r in state["reservations"] if r["kind"] == "human")
    return workers, humans


def do_acquire(state, rid, kind, max_workers):
    workers, humans = counts(state)
    if any(r["id"] == rid for r in state["reservations"]):
        return ({"ok": False, "reason": f"id {rid} already holds a slot"}, False)
    if kind == "worker" and workers >= max_workers:
        return ({"ok": False, "reason": f"worker cap reached ({workers}/{max_workers}); human slot is not available to workers"}, False)
    if kind == "human" and humans >= 1:
        return ({"ok": False, "reason": "the single human slot is already held"}, False)
    state["reservations"].append({"id": rid, "kind": kind, "reserved_at": int(time.time())})
    w, h = counts(state)
    return ({"ok": True, "id": rid, "kind": kind, "workers": w, "humans": h, "max_workers": max_workers}, True)


def do_release(state, rid):
    before = len(state["reservations"])
    state["reservations"] = [r for r in state["reservations"] if r["id"] != rid]
    if len(state["reservations"]) == before:
        return ({"ok": False, "reason": f"no reservation with id {rid}"}, False)
    return ({"ok": True, "released": rid}, True)


def selftest():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "slots.json")
        # default cap 3: three workers fit, the fourth is refused
        for i in range(3):
            res = with_lock(path, lambda s, i=i: do_acquire(s, f"w{i}", "worker", 3))
            assert res["ok"], res
        res = with_lock(path, lambda s: do_acquire(s, "w3", "worker", 3))
        assert not res["ok"], "fourth worker must be refused at cap 3"
        # human follow-up exceeds the full worker cap by exactly one
        res = with_lock(path, lambda s: do_acquire(s, "owner-1", "human", 3))
        assert res["ok"] and res["workers"] == 3 and res["humans"] == 1, res
        # a second human is refused: the plus-one is exactly one
        res = with_lock(path, lambda s: do_acquire(s, "owner-2", "human", 3))
        assert not res["ok"], "second human must be refused"
        # duplicate id refused
        res = with_lock(path, lambda s: do_acquire(s, "w0", "worker", 3))
        assert not res["ok"], "duplicate reservation id must be refused"
        # release frees a worker slot, which can then be taken
        res = with_lock(path, lambda s: do_release(s, "w0"))
        assert res["ok"], res
        res = with_lock(path, lambda s: do_acquire(s, "w3", "worker", 3))
        assert res["ok"], "released slot must be reusable"
        # releasing an unknown id reports failure, changes nothing
        res = with_lock(path, lambda s: do_release(s, "nope"))
        assert not res["ok"], res
        # config range enforced by check_max_workers via SystemExit(2)
        for bad in (0, 17):
            try:
                check_max_workers(bad)
                raise AssertionError(f"max_workers={bad} must be a config error")
            except SystemExit as e:
                assert e.code == 2, e
        print("SELFTEST PASS worker_slots: cap=3 refuses 4th worker; human exceeds cap by exactly 1; 2nd human refused; duplicate id refused; release frees a reusable slot; max_workers outside 1..16 is a config error (exit 2)")
        return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Mechanical worker-slot cap checker (A-18 staged form)")
    p.add_argument("--state", default=DEFAULT_STATE)
    p.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    a = sub.add_parser("acquire"); a.add_argument("--id", required=True); a.add_argument("--kind", choices=["worker", "human"], required=True)
    r = sub.add_parser("release"); r.add_argument("--id", required=True)
    sub.add_parser("selftest")
    args = p.parse_args(argv)
    if args.cmd == "selftest":
        return selftest()
    check_max_workers(args.max_workers)
    if args.cmd == "status":
        state = load_state(args.state)
        w, h = counts(state)
        print(json.dumps({"workers": w, "humans": h, "max_workers": args.max_workers,
                          "worker_slots_free": max(0, args.max_workers - w),
                          "human_slot_free": h == 0, "reservations": state["reservations"]}, indent=2))
        return 0
    if args.cmd == "acquire":
        res = with_lock(args.state, lambda s: do_acquire(s, args.id, args.kind, args.max_workers))
        print(json.dumps(res))
        return 0 if res["ok"] else 3
    if args.cmd == "release":
        res = with_lock(args.state, lambda s: do_release(s, args.id))
        print(json.dumps(res))
        return 0 if res["ok"] else 3
    return 2


if __name__ == "__main__":
    sys.exit(main())
