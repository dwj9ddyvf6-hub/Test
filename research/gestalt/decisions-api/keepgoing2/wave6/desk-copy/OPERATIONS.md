# OPERATIONS — muse-desk-v3

## What runs
One process: `python3 -m desk3.run_live --dispatch`, launched detached
(setsid/nohup) from the repo root, logging to `state/runner_dispatch.log`.
Evaluate-only launch (zero orders, FakeBroker): same command without
`--dispatch`, log `state/runner_eval.log`. A 60-second cycle: producers
build ONE immutable snapshot → fed gate (UNFED sleeves excluded and
named) → worker-pool evaluation → the single Dispatcher → journals +
terminal feed. Heartbeat: `state/runner.json` (pid, cycle, mode,
last_status) rewritten every cycle.

## Paper door
Alpaca PAPER API only (`paper-api.alpaca.markets` enforced in code;
`ALPACA_ENV=live` refused at startup). Client order ids are
`v3-<sleeve>-<intent_id>`. Credentials = v2's route: key ID from
`ALPACA_KEY_ID` env else the local-alpaca-paper skill config file;
secret as the Secure Vault surrogate via dynamic_credentials
(custom.alpaca), held only in the door process. Fills count ONLY from
broker read-back (`get_order_by_client_id`), never from submit ACKs.

## State
All under `state/`: per-sleeve `state/<id>/journal.jsonl` (append-only),
`state/dispatcher.jsonl`, `state/snapshots/`, `state/scheduler.json`,
`state/terminal_feed.json` + `state/terminal.json` (freshness =
generated_at/cycle_id), `state/runner.json`. State is runtime data,
not source: it is not committed.

## Supervision (always-on, HARDEN 2026-10-25)
Two processes, neither depends on the agent layer being awake:
the runner (above, detached) and its watchdog. The watchdog runs
as a boot-enabled systemd unit —
`muse-desk-v3-watchdog.service` (canonical copy in
`desk3/systemd/`, installed at /etc/systemd/system/;
Restart=always, KillMode=process so a watchdog restart never
cgroup-kills the detached runner) — because a VM reboot kills
every userspace process together (proven 2026-10-25 02:54Z,
BUGLOG HARDEN-WD2). Manage it with `systemctl
{status|restart} muse-desk-v3-watchdog`; a hand launch
(`setsid nohup python3 -u -m desk3.watchdog --loop`) is equivalent
but is NOT reboot-proof. Status in `state/watchdog.json`, restart
journal in `state/watchdog.jsonl`, log `state/watchdog.log` (hand
launches) / journald (unit). The watchdog verifies the runner
by EFFECTS only: the runner's own heartbeat (`state/runner.json`,
written after each completed cycle) plus the pid's live
/proc cmdline. Healthy = pid alive AND heartbeat age <= 600 s
(AUDIT-CURE 2026-10-25 A-01/A-02: the 180 s grace was shorter
than the real ~275 s cycle period and caused duplicate-runner
relaunches; a live runner is never duplicated — stale-but-alive
is named, a wedged pid (>1800 s) is terminated and verified dead
before one relaunch, and the runner holds a single-instance
flock on state/runner.lock). A runner the watchdog launched is judged by its launch
record (`state/watchdog_launched.json`) for up to 900 s — its first
cycle runs the full producer warm and the heartbeat legitimately
still names the previous pid until that cycle lands (HARDEN-WD1).
Unhealthy -> one detached relaunch, mode preserved from the last
heartbeat, journaled with old/new pid + reason. Restart intensity
is capped at 3 per 600 s; beyond the cap the watchdog writes the
named DEGRADED state and stops respawning (journaled once, on the
transition). Single watchdog instance via flock on
`state/watchdog.lock`; a live runner pid is never duplicated.
Internal supervision only — no external dead-man service (retired
by the owner 2026-10-23). Checks: `python3 -m desk3.watchdog
--status` / `--once`. Blockers:
tests/test_harden_supervision_blockers.py.

## Stop
`kill $(python3 -c "import json;print(json.load(open('state/runner.json'))['pid'])")`
— verify by effects: runner.json stops advancing and the pid's
/proc/<pid>/cmdline is gone. No flatten is performed on stop; paper
positions persist at the broker.

## Recovery
Relaunch the same command. Scheduler state and dispatcher idempotency
(seen intent ids in dispatcher.jsonl + broker client-order-id dedup)
make restart safe: no intent is submitted twice. A corrupt snapshot
fails the cycle closed before any dispatch.

## Save / restore
GitHub mirror: Silicon repo, branch `muse-desk-v3`, SHA-preserving
Git-Data mirror (`.scratch-femto-mirror/mirror_v3_branch.py`), route
registered in `~/workspace/backup/restorability_check.py`
(GITLINK_ROUTES). Restore = read the branch objects back (mirror
summary + ref read-back) into a fresh clone and run
`./run_regression_blockers.sh` there.

## Reconcile (A15)
At session start the first reconcile records the broker's current
positions as the pre-v3 baseline (state/reconcile_baseline.json) —
the legacy book predates v3 and is never attributed to a sleeve.
Every cycle then reconciles journal-derived positions/cash (from
dispatcher fill events) against broker read-back BEFORE dispatch;
the roll carries the reconcile status. A named discrepancy halts new
entries for the affected sleeve(s) only (exits pass); a cash
discrepancy is named and halts entries desk-wide (cash_halt).

## State save (A16)
Source: Silicon branch muse-desk-v3 (above). State: Silicon branch
muse-desk-v3-state holds state_snapshot.tar.gz + manifest.json
(per-file sha256 + journal line counts) pushed by the cure-2 drill
script; restore = reconstruct source from the mirror branch, unpack
the state snapshot into state/, run the gate.

## Known open items (named, not hidden)
- CURE3 (2026-10-24): bars are now REAL (desk3/warm.py, Alpaca SIP
  1Day+1Hour for the 155-symbol union, cached state/warm_bars.json);
  positions read back from the paper account in dispatch mode. Still
  UNFED by name: 115 sleeves whose other declared inputs (options,
  kraken, tensor, fires, quotes, earnings…) have no producer yet;
  23 parked; 18 FED evaluate each cycle — and now emit real intents
  on warm bars (evaluate-only fills vs FakeBroker observed).
- The runner currently runs EVALUATE-ONLY (pid in state/runner.json)
  so no weekend paper orders are placed from stale Friday bars.
  Re-enable `--dispatch` only for the supervised RTH session — that
  session's first paper fill, read back from the broker, is the
  remaining A9 proof. Reconcile runs in dispatch mode only (CURE3-4).
  A9-FLIP-20261025: the Monday 2026-10-26 re-enable is AUTOMATIC —
  the watchdog's desired_mode() returns dispatch from Mon 09:25 ET
  (FLIP_AT) and flips/relaunches the runner in dispatch mode itself,
  then writes the first-fill broker read-back to
  state/a9_first_fill.json. The manual relaunch above is now only
  the fallback for a degraded watchdog.
