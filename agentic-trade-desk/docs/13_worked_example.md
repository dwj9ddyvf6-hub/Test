# 13 — Worked example: from nothing to a restart-safe toy desk

Goal: in ~30 minutes, build the smallest desk that demonstrates the invariants, then extend it. Everything is simulated.

## 13.1 Run the toy
```bash
python3 skeleton/examples/run_example.py
```
Expected shape of output (dates are fixtures):
```
2026-03-03 first process     orders=1 skipped=0 errors=0
2026-03-03 restarted process orders=0 skipped=1 errors=0   # same signal bar → intent_skipped, no second order
...
book (replayed from ledger): flat
chain ok: True
```
What it proves:
* the signal id is derived from the **data bar** (`bar_ts`), so reconstructing the `Desk` on the same signal does not re-enter;
* the ledger's replayed book is the position truth;
* the hash chain verifies.

The output label "restarted process" describes a simulation: this example
creates another `Desk` object inside the same Python process, sharing the
ledger. It demonstrates repeat-evaluation deduplication. An operating-system
restart, interrupted network send and supervisor recovery need their own
drills in the extension exercises below.

From the repository root, the clean-copy check runs this example and the
invariant suite with no inherited credentials and rejects network activity:

```bash
python3 agentic-trade-desk/skeleton/tools/check_onboarding.py
```

Its JSON receipt checks one entry and one exit across twelve toy passes,
zero duplicate orders on the six simulated restarts, a flat final book and
the ledger chain. See [setup Step 3](03_setup_step_by_step.md#step-3--copy-the-skeleton-and-run-its-tests)
for the copy layout and proof boundary.

## 13.2 Read the toy sleeve
`DipBuyer.entries()` returns an intent with `bar_ts = <date of the bar that triggered it>`. That single field is the difference between a restart-safe desk and a desk that re-enters on every restart (P-01).

## 13.3 Extension exercises (do them in order; each has a pass criterion)

1. **Add a second sleeve in the same lane.** Pass: lane with `max_slots=2` blocks the third entry; ledger has a `blocked(lane_full)` event (see `test_lane_cap_blocks`).
2. **Add a broker double that times out after accepting** (`FlakyBroker`). Make `Desk._execute` resolve `send_unknown` by `lookup(cid)` on the next pass. Pass: 1 order at the double after 2 passes.
3. **Add a data hub** that returns `None` for a missing mark. Pass: an exit with no mark waits and alerts (see `test_exit_without_mark_waits`).
4. **Persist state with `StateStore`** and add a foreign adopter thread. Pass: adopted lot survives the main loop's save.
5. **Add reconcile** with a pending-order tolerance. Pass: broker leading the book by the pending qty is OK, by more is an alert.
6. **Add `ensure_desk.sh`** and kill the loop with `-9`. Pass: restarted within one supervisor interval; `-STOP` the loop: TERM, KILL, restart.
7. **Add a backup + restore drill.** Pass: replayed book equals the live book.
8. **Switch one sleeve to a real paper broker with tiny size**, human yes required. Pass: full lifecycle read-back; restart mid-pass: no duplicate.

## 13.4 What the toy deliberately omits
Real calendars/holidays, partial fills, stops, corporate actions, real data, multiple accounts, failover. Each is covered by a document: `05`, `06`, `07`.

## 13.5 A minimal `sleeves.json`
```json
{
  "lanes": {
    "toy_dip": {"kind": "1d", "max_slots": 2, "budget_usd": 200, "slot_usd": 100,
                "window": {"start": "15:20", "end": "15:50"},
                "exits": {"time_sessions": 3, "hold_from": "fill", "risk_policy_id": "toy-policy-defined-for-simulation"},
                "status": "shadow"}
  },
  "mode": "shadow",
  "accounts_allowlist": []
}
```
This is a configuration contract for an extended implementation. The supplied
`run_example.py` constructs its lane directly in Python; it does not read this
JSON or implement hot reload. When adding a config loader, implement and test
the intended behavior: reload a valid configuration each pass, and report
unknown keys. A malformed or risk-invalid update must not silently loosen the
last accepted policy. Keep this exercise separate from the toy's existing
deduplication proof.
The budgets, slots, and timing in this toy are simulation fixtures, not sizing recommendations. A risk policy must be defined for the instrument and strategy before any paper order path is enabled; this example intentionally does not prescribe a stop percentage.

## 13.6 A minimal regression harness skeleton
```python
# tests/regress.py
import subprocess, sys, json
GROUPS = {"unit": ["python3","-m","unittest","discover","-s","tests"],
          "secret_scan": ["python3","tools/secret_scan.py"]}
def main():
    res = {}
    for name, cmd in GROUPS.items():
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        res[name] = "PASS" if r.returncode == 0 else "FAIL"
    # SKIP must carry a reason and is never counted as PASS
    print(json.dumps(res, indent=1)); sys.exit(1 if "FAIL" in res.values() else 0)
main()
```
Extend with: bug-log blocker existence check, tests-never-live assertion, mode/allow-list assertion, restore drill freshness.
