# 03 — Setup, step by step

Follow in order. Each step ends with a **proof** — a command whose output you can paste into your build log. Do not continue past a failed proof.

> Conventions: `$DESK` is your repository root. Keys are in `~/.desk/*.env` (mode 0600), *outside* `$DESK`.

## Step 0 — Decide the perimeter (10 minutes, human)
Write `AGENTS.md` (start from `../AGENTS.md`). Explicitly list: paper only; which actions need a human yes; who may restart what; quiet windows when nothing may be restarted (e.g. the decision window before the close).
**Proof:** the file exists and the human has read it.

## Step 1 — Repository and hygiene
```bash
mkdir desk && cd desk && git init -b main
mkdir -p config engine sleeves vendor tools tests evidence/undo docs state
printf 'state/\n*.env\n*alpaca*\n*.bak_*\n.venv/\n__pycache__/\n' > .gitignore
git add -A && git commit -m "scaffold"
```
Add a **secret scanner** (`tools/secret_scan.py`: regexes for key shapes, long hex/base64 tokens, `BEGIN PRIVATE KEY`, account-id patterns) and a **pre-push hook** that runs it. **Proof:** introduce a fake key in a scratch file, confirm the hook refuses the push, remove it.

## Step 2 — Environment
```bash
python3 -m venv .venv && . .venv/bin/activate
python3 -c "import sqlite3, zoneinfo; print('ok')"
```
Pin dependencies (`pip freeze > requirements.lock`). On a recent Python some pinned scientific wheels do not exist; prefer unpinned minimal deps over compiling from source.
**Proof:** `python3 -m unittest` runs (zero tests is fine now).

## Step 3 — Copy the skeleton and run its tests
```bash
cp -r <this-repo>/agentic-trade-desk/skeleton/deskkit engine/
cp -r <this-repo>/agentic-trade-desk/skeleton/tests tests/
python3 -m unittest discover -s tests -v
```
**Proof:** 19 tests pass. Read each test name: it is a list of invariants you now own.

## Step 4 — Simulated broker, one trivial sleeve
Write one sleeve (e.g. "buy 1 share of an ETF when yesterday closed down; sell after 3 sessions"). Run passes against **ShadowBroker** with frozen fixture bars. Confirm: entry created once; re-running the pass creates nothing; a restart (new process, same ledger) creates nothing; the exit fires after 3 sessions; ledger replay equals the book.
**Proof:** a test `test_restart_does_not_reenter` (exists in skeleton) *and* one for your sleeve.

## Step 5 — Real data with freshness rules
Implement the data hub with: single fetch per pass, hard deadlines (`netguard`), freshness limits, calendar via tz database. Add fixtures from real data and tests for: stale bars → treated as missing; provider 429 → backoff honoring `Retry-After`; deadline exceeded → alert + skip, not crash.
**Proof:** unplug the network (or block the host) and run a pass: it finishes inside the pass deadline, writes alerts, no order, no traceback.

## Step 6 — Broker paper account (read-only first)
1. Create the paper account; store keys in `~/.desk/broker.env` (0600).
2. Write `tools/broker_check.py`: GET account, positions, orders. Print **names and counts only** (never keys).
3. Confirm the **account identity pin**: the account number suffix or id must match config; refuse to run otherwise. (A stale shell environment once pointed a tool at the wrong account and every call returned 401 — key *files* win over env.)
**Proof:** `broker_check.py` prints account status, position count, open-order count.

## Step 7 — Enable the order path on paper (one account, tiny size)
* Switch exactly one component to `PaperBroker` mode via an explicit config flag **and** an allow-list of accounts. The default mode is shadow.
* Send **one** order manually through the same code path (with the human's yes), observe the full lifecycle: accepted → filled → read back → book updated → reconcile OK.
* Kill the process between the persist and the send, restart: no duplicate.
* Simulate a transport timeout (fake broker that raises after accepting): the next pass finds the order by cid; no second order.
**Proof:** a captured lifecycle log and tests `SuicideBroker`, `FlakyBroker` (see `05` §5.9).

## Step 8 — Reconcile and read-back loops
* Read back non-final orders every pass (every 5 min), not hourly.
* Reconcile book vs broker with pending-order tolerance; alert on mismatch.
* Broker-driven import for desk-owned order ids the book lacks.
**Proof:** place an order out of band with the desk prefix; next pass imports it and logs an alert; book == broker.

## Step 9 — Supervision
Install `skeleton/ops/ensure_desk.sh`, start via `setsid`, test: kill -9 the loop → restarted; hang the loop (SIGSTOP) → TERM, then KILL, then restart; simulate a clock jump (`date -s` in a throwaway VM, or mock) → no needless restart.
Add the **progress-gated heartbeat** (written each tick and during long ticks, only if the loop is actually progressing).
**Proof:** a drill log for each of the three failure modes.

## Step 10 — Backups and restore drill
* Ledger + state → off-box private repo on a `state-backup` branch, additive, retried, secret-scanned, after every pass that had orders/fills and on a timer.
* **Restore drill:** restore into an empty directory, replay, compare book hash with the live book. Do it before you need it. Put the result in `evidence/restore_drill.json`.
**Proof:** the drill output with `identical: true`.

## Step 11 — Reporting
A read-only snapshot with: mode, last pass time, pass duration, orders/fills, alerts, per-sleeve status, blocked reasons, book vs broker recon status. Build the status page from the snapshot only. Add a contract test so the page cannot show a field the snapshot does not carry.

## Step 12 — Add sleeves through the pipeline (`04`)
One at a time. Never batch-import hundreds without an inventory.

## Step 13 — Failover worker (optional, after a stable week)
Deploy **in dry mode**, compare its decisions with the primary's for a few sessions, promote exits to live, then entries after a clean dry day and an explicit human yes. See `07` §7.6.

## Step 14 — Wake-up routines for agents
Create two routines: (1) a **fear-window / critical-window wake** shortly before any time-critical decision window, (2) a **trading-day heartbeat wake** every 30 minutes that *checks* and revives. Both must stay **quiet** when healthy. They run deterministic scripts first and only escalate to reasoning on an exception. Add a **boot hook** that restarts the supervisor after a machine re-provision.

## Step 15 — Go-live checklist for *paper autonomy*
Run `11_checklists.md` §11.1 (pre-open) and §11.4 (readiness drill) on three consecutive sessions without manual intervention. Only then call the desk "autonomous on paper".

## Troubleshooting quick table

| symptom | first suspect | doc |
|---|---|---|
| orders duplicated after restart | ids derived from pass time | P-01 |
| book ≠ broker by a pending amount | read-back too infrequent | P-30/31 |
| loop restarted repeatedly with "heartbeat stale" | VM pause / wall clock jump | P-12 |
| no fills for days | caps full, windows closed, market not meeting gate, or data stale — **check the reasons log first** | `07` §7.8 |
| pass takes 60+ min | a request without a total deadline | P-08 |
| exits never fire | missing inputs (next trading day, peak) or no mark | P-40/41 |
