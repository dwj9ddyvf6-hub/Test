# 07 — Reliability and operations

A trading desk that is correct but down is a failure; one that is up but silently wrong is worse. This document covers keeping it up *and* knowing when it isn't.

## 7.1 Failure model (design for all of these)

| failure | example from history | defence |
|---|---|---|
| process crash | OOM kill of a large process | supervisor, restart-safe ids, crash tests |
| hung process | a loop ignoring TERM | TERM → wait → KILL |
| slow request | a call without a total deadline stalled a pass beyond a time-sensitive decision | per-request total deadline, per-pass deadline, per-job limits |
| VM pause / snapshot-restore | wall clock +hours, monotonic unchanged; healthy loops "stale" | jump detector + grace, monotonic timeouts |
| disk rollback / wipe | caches, venv and output folders vanished after a re-provision | off-box backup, boot hook, boot sentinel, venv freeze |
| provider outage / block | index feed delayed; a funding data source geo-blocked | skip+alert, validated substitutes only, never circumvent |
| rate limit / quota | a provider limit prevents state synchronization | use current published limits, bound writes, and stand down if required state cannot be synchronized |
| agent unavailable | usage limit exhausted; scheduled agent runs failed | deterministic supervisor independent of agents; quiet routines; usage budget |
| human unavailable | nobody awake at the decision window | pre-authorized repairs; failover |
| platform surprise | sandbox idled and paused the VM when no agent turn was active | keep activity from a scheduled wake-up; design for pauses |

## 7.2 Timeouts everywhere

```text
request   : total deadline (e.g. broker 40 s, data 25 s), plus socket timeout
pass      : monotonic deadline (e.g. 600 s) – abort remaining sleeves, alert, finish cleanly
side jobs : own limits (e.g. 240 s); intraday warm 120 s
nightly   : generous but monotonic (e.g. 6 h); verify completion record; retry ONCE
supervisor: stale limits ~ 2× longest legitimate tick (e.g. 900 s main loop, 600 s engine)
```
* Use **monotonic** limits for long detached jobs. A wall-clock `timeout 2h` counted pauses on some platforms and not on others; a nightly job once "ran 2h46m" only because of pauses. Provide `ops/mono_timeout.py`.
* After a limit hits, **verify** the job's completion record in the ledger; if absent, relaunch exactly once (never a duplicate while one runs).
* Detached jobs' exit codes are **read back** (`rc`, `secs` written to the ledger; non-zero → alert). Fire-and-forget jobs failed silently for days before this was added.

## 7.3 Scheduling

* **Align** passes to bar closes (e.g. :00:20, :05:20). A late wake runs at the next boundary (catch-up once).
* **Pass before same-tick jobs** (publish, backup). A slow publish at 15:40 carried the 15:42 decision pass past the cut-off once.
* **Guaranteed pass** inside any critical window: if the last pass is older than N minutes and the window is open, run one now.
* **Detach slow producers** (tracker/research/data refresh): the pass runs on the data on disk; when the producer finishes, one follow-up pass picks up new fires. A still-running producer is alerted, never doubled.
* **Job ordering races**: check "is the other job still running?" at *run time*, after earlier same-tick jobs started; a deferred job stays due and runs on the first free tick. (A rebuild installed fresh files, then a feed sync overwrote them with stale ones 11 seconds later.)
* Shell scripts using `set -o pipefail`: `producer | rg -m1 … | rg -q …` can fail with SIGPIPE (rc 141) and print a false "a pass is running". Read ledgers without pipes (`tools/pass_state.py`).
* **Quiet windows**: no restarts of the loop in the minutes before and during decision windows, or within 3 minutes of a pass, unless it is already dead.
* Config is hot-reloaded every pass; unknown job names → alert ("restart the loop"), never an exception.

## 7.4 Supervision

Requirements for the supervisor (`skeleton/ops/ensure_desk.sh`):

1. **Single instance** via `flock`; two supervisors never start two loops. A bash subshell that kept the lock after launching the loop (so a replacement supervisor exited and nothing watched) is the classic bug: close the lock fd (`9>&-`) in the child and launch with `setsid -f`.
2. **Detach** the loop from the starting session/process group; close inherited fds. A loop that is a child of an agent tool session dies when the session is reaped.
3. **TERM → wait ~15 s → KILL.** Then wait for the loop lock to release before starting (lock wait), or two loops run briefly.
4. **Honest keep-alive**: "alive" = heartbeat fresh **and** progress counter moving, not just a pid. The loop writes the heartbeat at the **start** of every tick and during long ticks (progress-gated), so a legitimately long tick (a 900 s engine tick) is not killed as stale. The heartbeat is *not* written by a thread that keeps going while the main work is hung.
5. **Resume awareness**: compare the wall-clock delta with the monotonic delta between checks; a jump > ~180 s means "the machine was paused". Skip the stale judgment for that check, grant a grace (e.g. 150 s) and run immediate checks on resume.
6. **Death forensics**: on every start, log heartbeat age, uptime, and the kernel OOM-kill count so the next death is attributable.
7. **Memory cap with recycling** for long-lived workers (restart above a threshold, e.g. 4.5 GB RSS), logged.
8. **Boot sentinel**: on a new boot id, check watched output folders, the venv, backup presence, and the loop; restart via the supervisor (never inside a quiet window); alert on missing folders.
9. **Retire safely**: when replacing a desk, kill every scheduler *and the supervisor that would resurrect them*; tombstone entry points.

## 7.5 Monitoring philosophy

| do | don't |
|---|---|
| alerts with a key and a dedupe window | one alert per pass |
| severity levels; a digest for humans | page for every warn |
| read-only diagnostics; explicit deterministic gates own safety transitions | monitors with hidden order side effects |
| record *recovery* (`RECOVERED` lines) | leave stale alert lines looking current |
| test the alert path (a failing publish raises one alert after N consecutive failures) | assume it works |
| a check that names a missing blocker fails | blockers named in a log row but never run |

Health signals: last pass age; pass duration; heartbeat age; progress counter; orders/fills today; unreconciled count; blocked reasons by count; data freshness by feed; backup age; restore-drill age; job rc history; memory; disk and temporary-file growth.

### 7.5.1 Safety states and stop behavior

Separate alert severity from authority to change the order path. A warning can remain informational; a critical invariant failure must trigger its documented deterministic control. At minimum, define these states:

| state | new entries | existing orders and positions | recovery |
|---|---|---|---|
| `RUNNING` | allowed only after all gates pass | normal ownership, reconciliation, and exits | normal checks |
| `SLEEVE_DEGRADED` | blocked for the affected sleeve | preserve ownership; other sleeves continue if shared inputs and controls remain healthy | repair and revalidate that sleeve |
| `ENTRY_PAUSED` | blocked desk-wide | reconcile orders and positions; apply the predeclared policy to unfilled entry orders; preserve exits and protective orders | clear the named blocker and require the configured approval/checks |
| `EMERGENCY_STOP` | automated order creation blocked | apply the tested policy to queued and working orders; preserve position records and broker-native protection unless the policy explicitly directs otherwise; no blind liquidation | explicit operator-controlled recovery after reconciliation and integrity checks |

Examples that should block new exposure include stale or incomplete decision data, an account-identity mismatch, corrupt or unavailable durable state, an unexplained broker/book difference, unknown order submission outcome, duplicate-order detection, risk-cap breach, or a shared broker/data outage. A local sleeve defect should not stop unrelated sleeves if their inputs, account, risk controller, and order path are demonstrably independent.

An exit is not automatically safe just because it reduces nominal position size: it still needs a valid instrument, account, quantity, order identity, price policy, and broker route. If those cannot be verified, retain ownership, prevent new exposure, preserve any already-working protective order, alert, and follow the named contingency runbook. Never retry an unknown submission with a new client id before reading back the original id. Recovery must be explicit, logged, and idempotent.

## 7.6 Failover worker (standby in the cloud)

Why: a primary on a pausable machine can be unavailable during a decision window. A separate standby may support continuity, but it adds another state writer and order-capable process; prove mutual exclusion, state freshness, and recovery before granting it any order authority.

Build order:
1. **Dry** mode: reads broker (GET only), reads primary's exported book + heartbeat, computes what it *would* do, records it. Compare with the primary's decisions for several sessions.
2. **Heartbeat lock**: the primary posts book + heartbeat every few minutes; the worker stands down while it is fresh (e.g. < 10 min). Write the heartbeat only when it is *making progress*.
3. **Exits live** first: time/target/stop/signal exits for known lots, with the primary's cid scheme.
4. **Entries live** only after a clean dry day and a human yes, from a **session plan** exported by the primary (windows, caps, cash, slot counts, price caps, risk blocks) with a session date the worker verifies.
5. **Quota discipline**: calculate worst-case reads, writes, CPU, and subrequests against the provider's current plan and leave headroom. Write state only when it changes, keep a single writer, and make the standby stand down if it cannot prove fresh state or mutual exclusion.
6. **Resource limits**: measure the actual workload, including cold starts and worst-case state size. Know what the service does when its execution or storage budget is exhausted.
7. **Stop handling**: record each cancelled stop and re-place for `held − sold`; ids with a foreign-stop prefix; never the prefix the primary adopts as an exit.
8. **Adoption**: the primary absorbs the worker's fills before each pass (`absorb` job): sells become that lot's exit; buys are imported; a broker-driven import covers the case where the worker's own book write failed.
9. **DST**: cron expressions in UTC shift by an hour twice a year; calendar-check inside the worker too.
10. **Watchdog backstop** (e.g. a CI schedule) that kicks the worker if the market is open and the worker's own cron is stale; quiet unless a genuine error.

## 7.7 Backups (recap; details in `06`, `12`)
Additive, off-box, retried with bounded backoff, and secret-scanned. Verify the resulting backup by hash and restore checks; never force an overwrite after an ambiguous failure.

## 7.8 "Why isn't it trading?" runbook (answer with data in under five minutes)

1. Is the loop alive and **progressing**? (heartbeat age, last `pass_end`)
2. Is the market open and is any entry **window** open? Read the day's reasons log, grouped by reason.
3. Are lanes **full**? (open + queued vs `max_slots`; caps equal the last intended values?)
4. Is the **market gate** met? (e.g. "only on index-down days": was the index down today?)
5. Is **data** fresh for the sleeve's feed? (producer file age, bar freshness, provider status)
6. Are there **refusals** (insufficient buying power, bad price, halted)? 
7. Is the **mode** `shadow` rather than `paper`?
8. Did a **restart** leave sleeves in a "taken" state (keys already seen)?
9. Did a **failover** buy instead (and adopt)? 
Report the *specific* finding, not "market conditions". A run of "no fills" can be correct because no signal fired, or can reveal a misconfigured window, stale input, full capacity, or rejected order. Use per-decision reasons and provider/order receipts to distinguish them before changing a rule or limit.

## 7.9 Agent-side reliability

* **Routines**: (1) a window wake shortly before critical decisions; (2) a periodic trading-day wake (e.g. every 30 min during market hours) that checks heartbeats, revives via the deterministic boot script, and stays *silent* when healthy. Provide a weekend/holiday variant.
* **Usage limits**: an exhausted plan limit took three scheduled agent runs down in one afternoon and the desk was unsupervised until a script-based supervisor recovered it. Keep the supervisor free of any agent dependency; track limit reset times; make wake-ups cheap.
* **Platform pause**: if the host pauses the VM when no agent turn is active, in-box heartbeats do not count as activity. The wake-up routine *is* the keep-alive. Schedule it to cover the critical window. Don't try to "outsmart" the platform; build the failover.
* **Session ownership**: any process started in a tool session may be killed with it. Always `setsid`.
* **Handoffs**: a new agent should be able to resume from files alone: RUNBOOK, last evidence, open items list, quiet windows.

## 7.10 Operations checklist
See `11_checklists.md`.


## Addendum — platform, supervision and diagnostics (from the archive review)

- **Everything on the box can vanish.** Put the schedule or a dead-man's switch **off the box**: an external routine that runs the idempotent start script several times per weekday and pages on a missing heartbeat. Detaching a process is not host-reset recovery (P-99). A dead worker must leave enough on disk for the next one to converge to the truth; a pass that died mid-run and one that never started should look the same — idempotent passes and the broker read-back sort it out.
- **'Slot done' only on success; retry = the next tight tick (+5 min), not in-band retry.** Verify before retrying (look for partial effects), submit idempotently, and add a **post-window verifier** that confirms the intended end state — the retry makes it likely, the verifier makes it *known*. Derive 'what's new' from durable state (ledger diff), not 'what happened in the last N minutes', so a missed poll is harmless.
- **Time:** use a wall-clock cadence for *when* to run and monotonic time for *how long*; after a reboot ask 'am I inside my window right now?' rather than 'did I run at T' (P-105). Keep external cron windows wide around DST.
- **Supervisor child exits:** record exit **code and signal** separately, pid/start identity, who requested the stop, last progress and memory; capped exponential backoff; detect alive-but-stalled via heartbeat + birth + exact lease ownership and terminate only your own child (P-98). Liveness by effects (pid + cmdline + heartbeat age ≤ 3× cycle) (P-100).
- **Persist gates and plans** (cadence, prefetch) — fresh-process-per-pass designs lose memory (P-101). Inventory producers→consumers→schedule; name any **UNFED** input (P-102).
- **Never-delete list and gated restores** (P-97): ledgers, outcomes, journals, hidden state are never wiped; only rebuildable caches. Gate bulk restores on free disk and keep them out of market hours; `gc.auto=0` on backup clones. Exclude shared inboxes from sync (P-96).
- **Starved host runbook** (P-109): provider web console → `cat /proc/pressure/{cpu,memory,io}`, `free -m`, `vmstat 1 5`, `ps -eo pid,ppid,comm,%cpu,%mem,rss --sort=-rss | head`, per-cgroup usage, kernel OOM log; stop/renice only the dominant **non-trading** process; reconcile positions/orders before any restart.
- **Measure before optimising** (P-106): cgroup quotas can hide behind a parent's accounting; add read-only no-op checks before rewriting caches; prove byte-identical decisions after a speed-up.
- **Agent programs:** small fenced, resumable steps; commit early; never re-run completed work (P-107). A chat-pasted secret is leaked: rotate (P-108).
