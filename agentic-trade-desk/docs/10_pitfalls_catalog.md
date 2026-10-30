# 10 — Pitfalls catalog

Each entry: **Symptom → Cause → Fix → Guard**. IDs are stable; other documents cite them. Scenarios are generalized composites, with account and deployment details omitted. Any thresholds are illustrative, not defaults: derive them from your own risk policy, provider contract, measured workload, and instrument behavior. Order is by theme, not severity. For each pitfall you adopt, add its **guard test** to your suite *before* you consider it handled.

How to use: (1) skim headings once; (2) when designing a component, read its theme section fully; (3) when something breaks, search the symptom here before debugging from scratch.

**Severity hints**: identity, persistence, supervision, stop handling, and execution-boundary failures can create wrong orders, wrong positions, or unprotected exposure.


## A. Identity and idempotency

### P-01 — Restart re-enters already-taken signals
- **Symptom:** The same signal produced several entries in one morning, each exiting a few minutes later; every supervisor restart added another.
- **Cause:** A vendored strategy library stamped each intent id with the *pass's wall-clock time*, so a restart produced a 'new' id; the strategy's own 'episode taken' memory was not persisted by the host; the cadence timer reset on restart so a flat sleeve with a still-live trigger fired immediately.
- **Fix:** Re-key in the host from the DATA: `<sleeve>-<newest bar of the finest timeframe read>-<symbol>-<kind>-<side>`. An entry whose cid already has `entry_sent` writes one `intent_skipped` audit row and does nothing. Exit ids include the position's entry cid. Add a transitional guard: same sleeve+symbol+reason entered earlier the same session under a stamp key ⇒ taken (voided attempts excluded). Do not edit the vendored code. Annotate past duplicates with additive notes.
- **Guard:** `test_restart_does_not_reenter`: run a pass, build a fresh desk object on the same ledger, run again, assert 0 orders and one skipped row.

### P-02 — A timeout is treated as a refusal, then a second order is sent
- **Symptom:** Duplicate orders after a slow broker response.
- **Cause:** Any submit exception, including a transport timeout whose POST actually landed, re-queued the entry and the next attempt used a new id.
- **Fix:** Only HTTP 4xx (not 429) is a refusal. Transport errors and 5xx are `send_unknown`: keep the order unsettled and resolve by `GET by client_order_id` next pass (found → apply; absent → refused → retry with `attempt+1`). Look up before every POST. Keep a daily fsynced file of terminal order ids and refuse any POST of an id already on it.
- **Guard:** `FlakyBroker` that accepts then raises: exactly one order exists after two passes.

### P-03 — A refused exit is never re-sent (or counted as an active sell forever)
- **Symptom:** A position that should have been sold stayed open; the book showed an exit 'in flight' that did not exist at the broker.
- **Cause:** A refused/never-sent exit stayed in a non-final state and blocked resends; re-using its id could also drive an illegal `exiting → flat` transition.
- **Fix:** Only unsettled, non-final sells block a resend. A refused/voided exit is re-sent every pass under a new attempt id until filled. The FSM raises on illegal transitions.
- **Guard:** `RefusingBroker` for exits: resent under attempt+1 until fill; FSM illegal-transition test.

### P-04 — A refusal at the first decision slot burns the whole window
- **Symptom:** A near-close entry refused at 15:31 was never retried; the signal waited a day or expired on its last day.
- **Cause:** The 'one decision per session' mark was set before the broker answered.
- **Fix:** A refusal clears the session mark so the next pass in the window resends (`attempt+1`, bounded to e.g. 3). An *unknown input* is `wait`, not `skip`, and does not lock the session.
- **Guard:** Fake-broker lifecycle test: refuse the first, accept the second, assert one fill.

### P-77 — Manual/out-of-band orders confuse the audit
- **Symptom:** An audit failed 10 broker orders that were legitimate.
- **Cause:** Human-approved manual sells and a watchdog's stop cancels had no desk ids and were written into the book out of band; no fill triggered a backup, so the off-box copy lacked them.
- **Fix:** Manual orders use a `manual-…` prefix; the audit recognises allowed prefixes; the book-hash-differs-from-last-backup condition triggers a backup, not only fills.
- **Guard:** Audit test with a manual-prefixed order; backup-on-hash-change test.


## B. State, persistence, concurrency

### P-05 — A concurrent save overwrites adopted lots
- **Symptom:** Positions bought by the failover vanished from the book although they existed at the broker; adopted lots disappeared after the next pass.
- **Cause:** The adopter wrote the state file while the main loop held an older in-memory copy; the main loop saved last and erased the adoption.
- **Fix:** Exclusive file lock around every read-modify-write; atomic replace; **merge-back on save**: under the lock re-read the file and add any foreign-source lot the in-memory copy lacks (add-only). Foreign writers reload under the same lock. A broker-driven import repairs any that were lost.
- **Guard:** Merge test (old copy saved after adoption keeps the lot) + N-writer concurrency test.

### P-06 — A crash between POST and save leaves an order the book doesn't know
- **Symptom:** Broker had an order, the book did not; recon alert.
- **Cause:** State saved only at pass end.
- **Fix:** Intent journal: state saved **before and after** each submit; `pass_end` records the book hash; startup verifies state == last `pass_end` and alerts on a gap; the first pass resyncs by cid and reconciles.
- **Guard:** `SuicideBroker` raises SystemExit after accepting; restart; assert 1 order, book consistent.

### P-07 — Backup copy of a WAL database fails to open ('disk I/O error')
- **Symptom:** The store copy of the ledger could not be opened.
- **Cause:** The copy included the WAL header (journal-mode bytes) on a FUSE/network store.
- **Fix:** Copy via the online backup API, set `journal_mode=DELETE` for the copy, assert header bytes, run `integrity_check`; keep the live DB local.
- **Guard:** Regression test: backup then open then `integrity_check == ok`.

### P-08 — One stalled request stalls the whole pass (and misses a time exit)
- **Symptom:** A pass exceeded its decision window and delayed a time-sensitive exit.
- **Cause:** HTTP calls had only an idle socket timeout, no total deadline; the pass had no deadline.
- **Fix:** `urlopen_read` with a hard total deadline (broker 40 s); pass deadline (600 s, monotonic); side jobs 240 s; intraday warm 120 s with bounded concurrency; a due exit refreshes its own feed.
- **Guard:** `SlowBroker` sleeping past the deadline: pass ends on time, alert raised, other sleeves ran.

### P-09 — A disk rollback / wipe removes the desk's tools and caches
- **Symptom:** After a re-provision the research venv, output folders and the restore hook were gone; every publish failed; producers failed next morning.
- **Cause:** Treating the local disk as durable; the restore hook lived in a file the rollback itself reverted.
- **Fix:** Persistent store snapshots (code, state, config, ledgers; no secrets; sha256; newest N kept); a boot hook living **in the persistent store**; boot sentinel that detects a new boot id, missing folders, broken venv; venv freeze file; restore is *keep-newer*, never deletes.
- **Guard:** Boot drill: wipe a copy, boot, assert recovery and alerts.

### P-10 — A refresh job overwrote log rows written only in the mirror
- **Symptom:** Dozens of bug-log rows vanished with no git object or backup.
- **Cause:** An ad-hoc whole-tree copy refreshed a documentation mirror over in-place edits.
- **Fix:** One refresh tool: copy git HEAD only, atomic per file, never delete, refuse (exit 2 + alert) if a mirror file matches no version git ever committed; logs live in git; a superset guard before copying a bug log.
- **Guard:** Test: mirror with an uncommitted edit ⇒ refresh refuses.

### P-11 — Restore drill fails: backup has fills but ledger lacks their records
- **Symptom:** Restored state hash differed from the snapshot ledger.
- **Cause:** The fill-triggered backup ran before that tick's fill and `book_sync` records reached the ledger.
- **Fix:** Append fill-sync records first, then back up.
- **Guard:** Drill: after a fill, backup, restore into empty dir, `identical == true`.


## C. Supervision and operations

### P-12 — The supervisor kills healthy loops after a VM pause
- **Symptom:** Ten 'heartbeat stale' restarts in a morning; some in the middle of a catch-up pass.
- **Cause:** On resume the wall clock jumped hours; heartbeat files hold wall-clock epochs; monotonic time did not move.
- **Fix:** Jump detector (wall delta − monotonic delta > ~180 s): skip the stale judgment for that check, grant a grace (~150 s), run immediate checks on resume; the loop beats at the **start** of every tick; log `suspend_detected`.
- **Guard:** Supervisor test with a mocked clock jump ⇒ no restart; real stall ⇒ restart.

### P-13 — A hung loop ignores TERM
- **Symptom:** Supervisor 'restarted' but the old process lived; two loops or a stuck lock.
- **Cause:** TERM only; no wait; no KILL; no lock wait.
- **Fix:** TERM → wait ~15 s → KILL → wait for the lock → start.
- **Guard:** Test with a child that ignores TERM.

### P-14 — The loop dies when the tool session that started it ends
- **Symptom:** Desk down shortly after an agent finished a turn.
- **Cause:** Loop was a child of the agent's shell/process group.
- **Fix:** `setsid -f nohup … </dev/null`, closed fds; lock fd closed in the child (`9>&-`).
- **Guard:** Start from a throwaway shell, end the shell, assert the loop survives.

### P-15 — The keep-alive says alive while nothing is happening
- **Symptom:** A loop stuck in a long call looked healthy because the pid existed.
- **Cause:** Liveness = pid or a heartbeat thread, not progress.
- **Fix:** Heartbeat only on real progress; keep-alive requires fresh heartbeat AND a moving progress counter; honest status in the supervisor.
- **Guard:** `keepalive_ok` truth table test.

### P-16 — Supervisor kills a long but healthy tick at its stale limit
- **Symptom:** Kill loop: the engine tick legitimately took longer than the stale limit.
- **Cause:** Heartbeat written only at the end of a tick.
- **Fix:** Progress-gated heartbeat and export *during* long ticks; stale limits sized to the longest legitimate tick.
- **Guard:** Long-tick simulation with intermediate beats.

### P-17 — A supervisor resurrects a retired desk
- **Symptom:** Two desks trading the same accounts minutes after shutdown.
- **Cause:** Only the schedulers were killed; the supervisor that restarts them kept running.
- **Fix:** Kill supervisor first, then children; tombstone entry points (`SystemExit` under `__main__`), non-executable launchers, shims pointing to the new desk; a regression check 'no old-desk process'.
- **Guard:** Check `ops:no_old_desk_process`.

### P-18 — Agent usage limit exhausted: scheduled agent runs fail, desk unsupervised
- **Symptom:** Scheduled agent runs fail, leaving supervision unavailable until deterministic recovery runs.
- **Cause:** Supervision depended on an LLM run.
- **Fix:** Deterministic script supervisor independent of agents; wake-ups quiet when healthy; usage budget and reset date tracked; cheap checks first.
- **Guard:** Chaos test: disable the agent, desk still restarts.

### P-19 — Provider quota exhaustion threatens state freshness
- **Symptom:** A standby cannot publish or read the state needed to prove it is safe to act.
- **Cause:** The design did not calculate worst-case use against the current provider plan.
- **Fix:** Bound and measure requests, write only changed state, retain a single writer, and stand down if freshness or mutual exclusion cannot be proved. Do not submit orders after a required state-sync operation fails.
- **Guard:** Simulate the actual plan limits and assert that a quota failure blocks order creation without losing position ownership.

### P-20 — Failover cancels all stops for a symbol to sell one lot
- **Symptom:** Remaining lots of the symbol unprotected.
- **Cause:** Cancel-all-then-sell.
- **Fix:** Record each cancelled stop; re-place for `held − sold` at the same price, GTC, with a foreign-stop id prefix (never the prefix the primary adopts as an exit).
- **Guard:** Sell 10 of 30 ⇒ 20 re-protected.

### P-21 — Failover buys are not in the book
- **Symptom:** Broker had positions the book lacked; the account didn't match the book.
- **Cause:** Adoption missed (overwritten by P-05 or never written).
- **Fix:** `absorb` job before each pass: adopt worker sells as exits, import buys; broker-driven import by id prefix; merge-back on save.
- **Guard:** Offline import test.

### P-22 — Daylight-saving hard-coded offsets
- **Symptom:** A bar timestamped 08:30 instead of 09:30 after the clock change.
- **Cause:** Fixed `-04:00`.
- **Fix:** tz database everywhere; grep for fixed offsets; cron in UTC shifts: calendar-check in code.
- **Guard:** DST-week tests on both sides.

### P-23 — Date confusion around midnight and off-session
- **Symptom:** A page said 'a fear day' on a green session; a close-basis point was dated the build day.
- **Cause:** Colour from one snapshot, percent from another; build date used instead of the session date.
- **Fix:** Pin the session date once per pass; derive wording from the same number that is printed; stamp every carried-forward value with its own date.
- **Guard:** Wording-vs-number test; after-midnight test.

### P-24 — Detached jobs fail silently
- **Symptom:** A nightly job failed or timed out and nothing alerted.
- **Cause:** Fire-and-forget Popen.
- **Fix:** Keep the handle; poll each tick; write `job{rc,secs}`; non-zero → alert; rc None after a loop restart is recorded as 'started before restart'.
- **Guard:** Job that exits 3 produces an alert.

### P-25 — Same-tick job race installs stale data over fresh
- **Symptom:** A rebuild installed fresh files, then a feed sync overwrote them with stale ones 11 s later.
- **Cause:** The 'is the feed running?' check ran before the feed was started in that tick.
- **Fix:** Check at run time after earlier same-tick jobs started; a deferred job stays due; local builds are first-class files with receipts and the install picks the newest valid.
- **Guard:** Same-tick ordering test.

### P-26 — The decision pass is late because a producer ran in front of it
- **Symptom:** A pass started minutes late, pushing the decision window's retries past the cutoff.
- **Cause:** Synchronous data sync before the pass.
- **Fix:** Pass runs on time on data on disk; producer detached with a cap that ends ≥ 5 min before the window cut; one follow-up pass when it finishes; due pass before publish/backup jobs.
- **Guard:** Slow-producer test: pass starts on schedule.

### P-27 — `set -o pipefail` makes a status check lie
- **Symptom:** A script printed 'a pass is running' while idle; nothing applied.
- **Cause:** `tac | rg -m1 | rg -q` → SIGPIPE rc 141 → pipeline failure.
- **Fix:** Read ledgers without pipes in a small tool with explicit exit codes.
- **Guard:** Tool test: idle rc 0, running rc 3.


## D. Execution details

### P-28 — Sub-penny prices, rate limits and tick sizes
- **Symptom:** Broker rejections (HTTP 422); retries too eager on 429.
- **Cause:** `str(float)` as a price; fixed backoff.
- **Fix:** Tick-round (≥ $1 → 2 dp, < $1 → 4 dp), buys down/sells up; honour `Retry-After`/reset (≤ 10 s); GET retries only.
- **Guard:** Tick rounding tests; 429 test.

### P-29 — Rounding lifts a buy limit above its cap
- **Symptom:** Limit 62.48 vs cap 62.475.
- **Cause:** Round-half-up.
- **Fix:** When rounding exceeds a binding cap, floor to the cent.
- **Guard:** Property test across random prices.

### P-30 — Non-final states treated as final; infrequent read-back
- **Symptom:** Lost fills; positions shown queued/zero for an hour; reconcile flapping.
- **Cause:** `done_for_day`/`stopped`/`suspended` in the FINAL set; read-back hourly.
- **Fix:** FINAL = filled/canceled/expired/rejected/replaced only; read back non-final orders every pass; write `book_sync` with new hash.
- **Guard:** State classification table test; read-back cadence test.

### P-31 — Partial fills and late entry fills
- **Symptom:** Shares at the broker with the position closed; alerts forever.
- **Cause:** Exit sold the filled part; the entry then filled more.
- **Fix:** Book the filled part; late entry fill on a closed position reopens it; next due pass sells the remainder; cancelled/expired with partial fill books the filled part.
- **Guard:** Partial-fill lifecycle tests.

### P-32 — Auction-only orders (open/close) expire unfilled on a paper broker
- **Symptom:** Most opening/closing auction orders expired unfilled or partly filled at tiny share-of-volume.
- **Cause:** Paper broker's handling of auction orders, not liquidity.
- **Fix:** Avoid auction order types or prove them with a run before relying; use limit orders with caps.
- **Guard:** Order-type allow-list test.

### P-33 — No price means no trade (or a guessed price)
- **Symptom:** Thin names had no recent print; decisions waited forever; exits 'due but no price'.
- **Cause:** Single-source quote with a strict age limit.
- **Fix:** Quote chain with alerts on every fallback; exit waits and alerts; never guess; entries wait.
- **Guard:** Chain order test; exit-wait test.

### P-34 — A delayed feed makes a gate permanently unknown
- **Symptom:** A whole family of sleeves could never buy.
- **Cause:** The provider's actual delay was at or beyond the configured freshness tolerance.
- **Fix:** Measure feed delay and entitlement; define which observations the rule can use. If the required input is not fresh enough, report it unavailable instead of silently loosening the gate.
- **Guard:** Feed-age tests on both sides of the documented freshness boundary.

### P-35 — Entry sizing disagrees with the committed price cap
- **Symptom:** An entry is smaller than expected or breaches its reserved budget after limit-price rounding.
- **Cause:** Sizing used one reference price while the order used another, or rounding was applied after the cap check.
- **Fix:** Size from the price actually committed, use the instrument's authoritative tick schedule, and re-check the cap after rounding.
- **Guard:** Boundary tests around price ticks and the configured budget cap.

### P-36 — Overlapping sells rejected by the broker
- **Symptom:** Exit failed because a stop already covered the shares.
- **Cause:** Stop orders and exit orders overlapped.
- **Fix:** Cancel *and confirm* overlapping stops before any desk sell; defer the sell if not confirmed; foreign stops respected.
- **Guard:** Fake broker rejecting overlaps.

### P-37 — Disaster stop only lives in desk passes / evaluated one pass late
- **Symptom:** A sleeping machine left a position without the protection required by its documented risk policy, or an exit was evaluated after its trigger.
- **Cause:** No broker-side stops; the 'stop refused' flag was set after exits ran.
- **Fix:** Broker GTC stops per lot; same-pass evaluation for lots without a live stop; refused-stop fallback; coverage check; exempt list explicit.
- **Guard:** No-lot-held-past-threshold regression check.

### P-38 — Stop judged on a stale weekly bar
- **Symptom:** A weekly sleeve's stop used a bar up to a week old.
- **Cause:** Used the last *closed weekly* bar.
- **Fix:** Judge stops on the freshest closed daily bar (or live mark).
- **Guard:** Stale-bar test.

### P-39 — Time exit counted from the planned bar, not the fill
- **Symptom:** Positions exited early/late versus the research hold.
- **Cause:** Fills landed up to days after the planned entry bar.
- **Fix:** `hold_from=fill`; never earlier than the plan's date; re-date new fills; label.
- **Guard:** Hold-from-fill test.

### P-40 — Exits that can never fire
- **Symptom:** Signal-exit sleeves held positions indefinitely.
- **Cause:** The host didn't pass the inputs the exit needs (next trading day, peak since entry), or max_bars was 0.
- **Fix:** Wire the inputs; exit audit asserts a terminating route per sleeve.
- **Guard:** `exit_audit`: every sleeve terminates.

### P-41 — Time exit never executed because the mark window was too narrow
- **Symptom:** Overnight holds of intraday positions.
- **Cause:** Intraday feed refreshed only in a short window; stale cache rejected after 30 min.
- **Fix:** A due exit refreshes the feed itself; window covers the session; late exits labelled.
- **Guard:** Due-exit-without-mark test.


## E. Caps, budgets, windows

### P-42 — A slot consumed by a signal that was only looked at
- **Symptom:** Valid in-window fires blocked behind out-of-window ones.
- **Cause:** Slot taken at decision time rather than order time.
- **Fix:** Slot taken by an order; released on refusal.
- **Guard:** Lane lifecycle test.

### P-43 — Queued entries never end
- **Symptom:** A lane stayed full with 'queued' ghosts.
- **Cause:** No deadline; re-adopted every pass.
- **Fix:** Entry deadlines and final-skip end the entry and release the slot.
- **Guard:** Synthetic queued entry with a 16:00 deadline.

### P-44 — Lane budgets exceed what the account can hold overnight
- **Symptom:** On heavy days orders were rejected for buying power.
- **Cause:** Intraday margin multiple used for sizing.
- **Fix:** Size to overnight capacity or measure/alert the overshoot; handle `insufficient_bp` as a clean refusal.
- **Guard:** Budget-vs-capacity check.

### P-45 — Pending entries count as $0
- **Symptom:** A lane over-committed within one session.
- **Cause:** Budget tally used the fill price.
- **Fix:** Pending entries counted at their limit.
- **Guard:** Budget test.

### P-46 — Off-by-one on the last day of a signal window
- **Symptom:** Fires waiting for a specific market condition were lost exactly on their last valid day.
- **Cause:** Every producer keeps fires younger than N−1 sessions; the book entry was created only at order time.
- **Fix:** Remember fires seen until decided (or 20 days).
- **Guard:** Last-day lifecycle test.

### P-47 — Concentration invisible
- **Symptom:** Seven sleeves bought one name in one pass.
- **Cause:** No cross-sleeve view.
- **Fix:** Alert (never shrink) when ≥ 3 books or > threshold dollars in one pass.
- **Guard:** Replay test.

### P-48 — Blocked-by-cap mistaken for a bug (or hidden behind it)
- **Symptom:** Hundreds of 'blocked' lines; no one knew if fewer fills were expected.
- **Cause:** No audit of occupancy vs caps.
- **Fix:** Daily cap audit: open + queued vs max; caps equal last intended; label by-design only with a recorded decision; counts of unique blocked fires per lane.
- **Guard:** Cap-audit evidence file.

### P-49 — Sleeve count inflated
- **Symptom:** Headline count included blocked/merged/duplicate rows.
- **Cause:** Config rows summed with catalog rows.
- **Fix:** Separate running/shadow/blocked/merged/off; count distinct.
- **Guard:** Inventory consistency test.


## F. Data and caches

### P-50 — Bar cache lives for the process / grows without bound
- **Symptom:** New data invisible after a nightly refresh; later, memory grew every refresh.
- **Cause:** Cache key without version; then a key per version.
- **Fix:** Key by file mtime; replace the old frame; one frame per symbol/interval.
- **Guard:** Cache tests: sees refresh; bounded size.

### P-51 — Missing data is read as a signal (or as evidence of absence)
- **Symptom:** A stale feed produced trades or suppressed exits.
- **Cause:** No 'unknown' state.
- **Fix:** `Missing(reason)`; stale bars (> N days) are missing; skip + alert.
- **Guard:** Stale-bars test.

### P-52 — Upstream producer silently stopped
- **Symptom:** A feed file frozen for days; sleeves read it as current.
- **Cause:** No age check; owner's scheduler had been retired.
- **Fix:** Age check + alert; run the owner's pinned generator locally with a sha receipt; install the newest valid.
- **Guard:** Feed-age alert test.

### P-53 — Data source blocked by region or terms
- **Symptom:** A needed data endpoint returned region errors.
- **Cause:** Provider geo-blocks.
- **Fix:** Do **not** route around it. Validate a legitimate substitute against the original archive (agreement %) and block the sleeves if it is not faithful; ask the human.
- **Guard:** Agreement-check evidence.

### P-54 — Provisional/invalid bars drop out of the vendor parser
- **Symptom:** Some names had no latest daily bar; fires a session late.
- **Cause:** Vendor parser rejects bars with impossible OHLC; overlay only ran for null closes.
- **Fix:** Treat parser-invalid bars as missing and fill from the alternate feed using the parser's own validity rule.
- **Guard:** Overlay test.

### P-55 — Cache freshness judged by mtime after a restore
- **Symptom:** Yesterday's bars looked fresh after a restore reset mtimes.
- **Cause:** mtime-only freshness.
- **Fix:** Also require the cached last bar to be today's session after the close.
- **Guard:** Post-restore freshness test.

### P-56 — Environment/keys do not persist across reboot
- **Symptom:** Crypto data blocked after a reboot.
- **Cause:** Key only in a shell env.
- **Fix:** Boot hook heals the env from a `0600` file (presence check only).
- **Guard:** Boot drill.

### P-57 — Tools use a stale shell environment instead of the key file
- **Symptom:** 401 on every call; no orders, no recon, no equity row.
- **Cause:** Env had old values; file had new.
- **Fix:** Key files win; supervisor sources the file unconditionally.
- **Guard:** Key-file-wins test.


## G. Fidelity, research and testing

### P-58 — A ported rule is inverted
- **Symptom:** A group of sleeves would have bought on the wrong days; no order had been sent yet.
- **Cause:** Misread the original's boolean.
- **Fix:** Exact port + randomized parity vs the original on thousands of cases incl. flat/None.
- **Guard:** randomized parity test (thousands of random cases including flat/None inputs).

### P-59 — Ported rules missing fill-time risk blocks
- **Symptom:** A port applied the entry gate but not the origin's shock/freeze/event-day blocks.
- **Cause:** Only part of the origin read.
- **Fix:** Per-sleeve logic diff against the pinned origin; port blocks exactly.
- **Guard:** Logic-diff matrix.

### P-60 — Research gates that only control false positives
- **Symptom:** Real narrow edges could never pass; 'it's random' conclusions.
- **Cause:** Multiplicative gates; p-value floor × thousands of cells; tiny holdouts; median-based tests on tail strategies.
- **Fix:** Planted-edge power checks; correct within the hypothesis family; choose statistics matching the claim; pre-register.
- **Guard:** Power table in research evidence.

### P-61 — Fill price semantics wrong
- **Symptom:** Fills at the signal bar's close rather than next open.
- **Cause:** Generic mark = last closed bar.
- **Fix:** Per-sleeve fill rule; test it; corrections as notes.
- **Guard:** Fill-price test per sleeve family.

### P-62 — Tests send orders or rewrite live inputs
- **Symptom:** Risk of real orders from tests; torn live files.
- **Cause:** Tests ran against live paths/mode.
- **Fix:** Shadow/fake broker only; tests run on copies; assert mode.
- **Guard:** `safety:tests_never_live`.

### P-63 — Tests import the production checkout
- **Symptom:** A branch's tests ran main's code.
- **Cause:** Hard-coded absolute path.
- **Fix:** Import relative to the test's own checkout.
- **Guard:** Path assertion.

### P-64 — Fixtures hard-code live data
- **Symptom:** Suite fails with no product fault.
- **Cause:** Ticker/fire that stopped existing.
- **Fix:** Synthetic fixtures; match by id.
- **Guard:** Fixture lint.

### P-65 — Memory pressure / OOM
- **Symptom:** The operating system kills a worker after memory use grows beyond available capacity.
- **Cause:** Unbounded caches, long-lived workers with native memory.
- **Fix:** Resident cap with recycle; bounded worker batches; log OOM count at starts.
- **Guard:** Memory soak test.

### P-66 — Disk filled by temporary directories
- **Symptom:** Accumulated temporary profiles or caches exhaust available disk space.
- **Cause:** No cleanup on exit.
- **Fix:** Remove in exit handlers; periodic safe cleaner (idle, not open).
- **Guard:** Disk check in sentinel.

### P-67 — Guard hole: named blocker never executed
- **Symptom:** Failing tests unnoticed for days.
- **Cause:** Bug-log named a test file the harness didn't run.
- **Fix:** `every_row_has_live_blocker`; harness executes every named blocker.
- **Guard:** Meta-test.

### P-68 — Restored-mode and permissions lost
- **Symptom:** Frozen specs became writable; scripts non-executable.
- **Cause:** Restore wrote bytes only.
- **Fix:** Re-apply 0444/0755 after restore.
- **Guard:** Mode test.


## H. Reporting

### P-69 — P&L numbers don't reconcile
- **Symptom:** Unrealized was a plug; realized + unrealized ≠ total by cents.
- **Cause:** Fill-rounding residual leaked into one term; panels on different bases.
- **Fix:** One headline; others derive; realized = sum of closed list; unrealized = sum of rows.
- **Guard:** Reconcile test.

### P-70 — Carried-forward value stamped with today's date
- **Symptom:** A volatility value from the prior session labelled today.
- **Cause:** Date taken from the latest build, not from the data.
- **Fix:** Use the date of the data actually used.
- **Guard:** As-of test.

### P-71 — Narrative contradicts the numbers
- **Symptom:** Wording said a down day on an up day; typos after name stripping; false 'no session today'.
- **Cause:** Templates and independent sources.
- **Fix:** Derive words from the same value printed; run sanitizer twice; validate sentences against canonical data.
- **Guard:** Wording guard tests.

### P-72 — Public page leaks internals
- **Symptom:** Internal names, stop percentages, research stats on a public page.
- **Cause:** No scrub/deny-list.
- **Fix:** `public_clean` layer + contract tests + deny-list.
- **Guard:** Leak test.


## I. Multi-agent and process

### P-73 — Two agents edit the same file
- **Symptom:** Lost edits; gate failures from in-flight work.
- **Cause:** No claims.
- **Fix:** COORDINATION log with claims, backups, 3-way merge, quiet windows.
- **Guard:** Process rule.

### P-74 — 'Done' without proof
- **Symptom:** Fix reported complete; local commit not pushed; tests not run on final artifact.
- **Cause:** Optimism.
- **Fix:** GREEN only with evidence on the final artifact; verify remote refs.
- **Guard:** Receipt template.

### P-75 — Vendored code edited
- **Symptom:** Pins broke; parity lost.
- **Cause:** Convenience fixes.
- **Fix:** Never edit vendor; shim outside; manifest check at startup.
- **Guard:** Manifest check.

### P-76 — Asking permission for repairs the human already delegated
- **Symptom:** Repeated human frustration.
- **Cause:** Over-caution.
- **Fix:** Perimeter list; ask only for authority/material choice.
- **Guard:** AGENTS.md review.

## J. Order ids, ownership and exits (added from archive review)

### P-78 — Order ids collide with themselves after a fill plus a quantity change
- **Symptom:** A burst of broker 422 duplicate-id rejections in one morning.
- **Cause:** The id was minted from the *signal* alone; after a partial fill and a changed quantity the same id was used for a different order.
- **Fix:** Mint ids from the signal **and the fill state** (cumulative filled qty / attempt counter). Test: fill, change qty, resend → new id, no collision.
- **Guard:** Id-collision test with partial fill followed by a resize.

### P-79 — A human/operator order and a sleeve exit reach for the same shares
- **Symptom:** The sleeve's exit ate broker rejections ('held for orders') because an operator's resting trim held every share.
- **Cause:** No shared view of which shares are already committed to open orders.
- **Fix:** One **reservation ledger per account+symbol** shared by every sleeve and every operator order: count open, partial and cancel-pending sells against available shares; reconcile broker positions/open orders immediately before dispatch; after a submit timeout keep the reservation as UNKNOWN until reconciled; recompute after fill/cancel races; one fenced writer owns dispatch. The desk stands down (named reason) rather than provoking a broker rejection. Consider giving an operator lane its own virtual book.
- **Guard:** Race fixture: operator trim + sleeve exit on one position ⇒ no broker rejection, one sell wins, the other logs `stand_down`.

### P-80 — Partial first fill, then a price jump, exceeds the intended stop risk
- **Symptom:** A stop sized for the planned entry price risked more than intended.
- **Cause:** Stop computed before the fill and not re-pinned.
- **Fix:** Pin the stop to the **actual first fill** and cancel the unfilled remainder before later fill boundaries; keep stop and quote units comparable across splits.
- **Guard:** Partial-fill-then-gap test asserting risk ≤ limit.

### P-81 — An unrelated data failure delays a healthy held-position exit
- **Symptom:** A position's exit waited because a different instrument's feed failed.
- **Cause:** Exit assessment shared the entry path's all-or-nothing data census.
- **Fix:** Held-symbol exits use **their own causal data source**; only *new entries* require the complete census. Test across disable/halt/restart.
- **Guard:** Break an unrelated feed ⇒ held exit still evaluates.

### P-82 — A transient failure at the admission guard becomes a permanent denial
- **Symptom:** A signal was never admitted because one check failed once.
- **Cause:** The guard recorded a final denial on a retryable error.
- **Fix:** Defer and retry the same verified binding inside the real window; only final reasons are final.
- **Guard:** Fail-once-then-pass test.

### P-83 — Background data reads consume a protected decision window
- **Symptom:** An entry deadline was missed while a broad refresh ran.
- **Cause:** Unrelated acquisition ran concurrently with the critical window.
- **Fix:** Defer unrelated acquisition around protected windows; required fills and held exits keep priority.
- **Guard:** Window test with a slow background read.

### P-84 — A dependent buy executes although its paired sale missed
- **Symptom:** A rotation bought the replacement while still holding the donor.
- **Cause:** Buy and sell treated as independent intents.
- **Fix:** Store targets; the buy waits until the sale has a quote/fill. Model dependencies explicitly.
- **Guard:** Missed-sale test ⇒ no replacement buy.

### P-85 — Sub-minimum remainders ('dust') after exits
- **Symptom:** Tiny residual quantities no order can close.
- **Cause:** Partial exits and lot increments ignored venue minimums.
- **Fix:** Prevent creating sub-minimum remainders (round the exit up/down by policy); keep residuals **visible** — no fake close, no inventory top-up, no silent deletion; define an allowed resolve policy.
- **Guard:** Exit-sizing test across lot increments.

### P-86 — Cash availability uses the exchange calendar instead of the settlement calendar
- **Symptom:** Simulated sale cash was reusable a day too early over a settlement holiday.
- **Cause:** Exchange sessions ≠ securities settlement days; settlement cycle (T+2→T+1) changed over time; a generic federal-holiday calendar differs from the clearinghouse's.
- **Fix:** Use the official settlement calendar and cycle by date; **fail closed** for years without data; keep old release rows, bind policy version to new ones; re-run research with the corrected calendar and keep the rejected outputs labelled rejected.
- **Guard:** Dated fixtures around a settlement holiday.

### P-87 — A cost is applied twice
- **Symptom:** P&L disagreed with cash: a haircut was in the fill price and subtracted again.
- **Cause:** Two layers each applied the same cost.
- **Fix:** P&L = (sell − entry average) × shares with costs applied in exactly one place; reconcile cash against P&L.
- **Guard:** Round-trip accounting identity test.


## K. State truth, recorders and protection (added from archive review)

### P-88 — A risk number downstream of a cache trips a breaker on fiction
- **Symptom:** An exposure circuit-breaker tripped at a phantom 177% when the real figure was ~130%.
- **Cause:** The exposure ledger held a ghost position the broker did not, and missed real positions because the broker→ledger sync hadn't run; short legs were skipped entirely.
- **Fix:** Every risk metric is computed from **broker truth** (or reconciled to it every pass); shorts and legs count; stale caches are labelled stale. Prefer 'lock the symbol and alert' over a global breaker.
- **Guard:** Phantom-position test: ledger ghost + missing broker rows ⇒ metric uses broker.

### P-89 — Some writers bypass the recorder
- **Symptom:** The replay proof was clean, yet reconciling against the broker found most of a day's fills had no ledger row.
- **Cause:** Live loops recorded fills around the filing path, so the replay never saw them: 'evidence at the actual writer' was missing.
- **Fix:** All fill recording goes through one door; add a **bypass blocker** (test that any direct write fails); reconcile ledger vs broker *by fills* daily, not just positions.
- **Guard:** Fill-count reconciliation vs broker.

### P-90 — Protection verified in the desk's own state, not at the broker
- **Symptom:** Stops existed in state but not at the broker (or vice versa).
- **Cause:** The check read internal records.
- **Fix:** Verify protective orders **at the broker** (list open stops per lot, coverage %, refused lots) and treat foreign stops explicitly.
- **Guard:** Coverage check against a fake broker.

### P-91 — Adopted/legacy positions owned by nobody
- **Symptom:** Positions inherited from a retired desk were neither managed nor protected, or got managed by the wrong sleeve.
- **Cause:** No explicit ownership baseline.
- **Fix:** Record a baseline: either adopt (owner sleeve, exit rules, stops) or declare 'owned by no writer; never managed'. Reconcile guards that baseline.
- **Guard:** Baseline ownership test.

### P-92 — Per-fire block reasons are not kept
- **Symptom:** A once-per-signal sleeve sat in cash and nobody could tell whether the market gate, the name or an unknown colour was the reason.
- **Cause:** Decisions logged without the reason or expiry.
- **Fix:** Persist reason, inputs, and expiry per fire (append-only reasons log).
- **Guard:** Reasons-log completeness test.

### P-93 — A stale response overwrites a newer good read
- **Symptom:** An error banner or old price replaced a newer good value.
- **Cause:** Late failed poll won the race.
- **Fix:** Responses carry a sequence/timestamp; ignore any response older than the last accepted.
- **Guard:** Out-of-order response test.

### P-94 — A forecast dated before the book existed is treated as fresh
- **Symptom:** The next forecast never started.
- **Cause:** Freshness compared to 'now', not to the book's birth/last-used date.
- **Fix:** Compare against the last consumed signal date and the book birth.
- **Guard:** Dated-fixture test.

### P-95 — The wrong 'previous close' makes a red day look green
- **Symptom:** A gate waited on a day the rule allowed.
- **Cause:** A multi-day chart's `previousClose` field was the start of the chart range, not yesterday.
- **Fix:** Derive previous close from the daily series by session date; never from range metadata.
- **Guard:** Fixture where chart metadata disagrees with the daily series.


## L. Operations, platform and agents (added from archive review)

### P-96 — A bulk backup sync wipes a shared agent inbox
- **Symptom:** A shared dead-drop file was deleted three times in one evening.
- **Cause:** The sync mirrored the working tree, including a directory other agents write to.
- **Fix:** Exclude shared channels from sync; additive-only pushes; pre-push hooks refuse deletions and ref deletes; the sync aborts on any staged deletion; restore from git history.
- **Guard:** Guard test: staged deletion ⇒ abort.

### P-97 — Cleanup/restore destroys irreplaceable files or fills the disk
- **Symptom:** A health sentinel froze the desk over 'missing' files that had been deliberately moved off-box; a restore of ~17k files plus a garbage-collect collapsed free space to ~300 MB.
- **Cause:** No explicit never-delete list; manifests treated every missing file as damage; no disk gate.
- **Fix:** A written **never-delete list** (ledgers, outcomes, journals, hidden state); only rebuildable caches are fair game; the backup manifest excludes deliberately archived folders; restores are gated on free space and blocked during market hours; `gc.auto=0` on backup clones.
- **Guard:** Sentinel test: archived folder missing ⇒ no freeze.

### P-98 — A child exits with 'null' and nobody knows why
- **Symptom:** 'Loop exited null' twice with no stack.
- **Cause:** Only the exit code was recorded.
- **Fix:** Record **code and signal separately**, pid/start identity, whether the supervisor requested the stop, the last progress marker, memory at the last heartbeat, and OOM evidence. Null code + null signal with no error event often means an external SIGKILL (the OOM killer) or a dead IPC channel.
- **Guard:** Supervisor fixtures: SIGABRT, SIGKILL, timeout.

### P-99 — Detaching a process is mistaken for host-reset recovery
- **Symptom:** After a host reset nothing restarted the desk — including the on-box supervisor.
- **Cause:** Everything lived on the box.
- **Fix:** Put the schedule/dead-man's switch **off the box** (external routine or pinger that fires the idempotent start script several times a day and alerts when no heartbeat arrives).
- **Guard:** Boot drill.

### P-100 — Liveness judged by process name
- **Symptom:** A wrong process matched; a dead desk looked alive.
- **Cause:** Name matching.
- **Fix:** Liveness by *effects*: pid alive AND cmdline matches AND heartbeat age ≤ 3× the cycle.
- **Guard:** Impostor-process test.

### P-101 — Cadence or prefetch state lives in process memory
- **Symptom:** A cadence gate reset on every pass (each pass is a fresh process); two deploys emptied the prefetch plans.
- **Cause:** State kept in memory.
- **Fix:** Persist gates, plans and cursors on disk (atomic).
- **Guard:** Restart test.

### P-102 — A producer exists but is never scheduled
- **Symptom:** Every consumer reported a data gap.
- **Cause:** Nobody wired the producer into a schedule.
- **Fix:** Inventory producers → consumers → schedule; an alert for any declared input with no producer ('UNFED by name'), never a silent abstention.
- **Guard:** Inventory check.

### P-103 — A sleeve that never traded can never fire
- **Symptom:** A premium-selling sleeve's entry required 14 bars while its window served 12.
- **Cause:** Never exercised end-to-end.
- **Fix:** **Dead-sleeve audit**: for each sleeve inject a synthetic fire / run on real history and prove at least one entry and one exit are *reachable*; sleeves never seen to trade are listed first in every audit.
- **Guard:** Reachability test per sleeve.

### P-104 — Tests stub libraries the production host does not have
- **Symptom:** A sleeve failed every pass at runtime although tests passed.
- **Cause:** Tests stubbed two libraries loaded at decision time.
- **Fix:** A test walks the runtime's imports and fails on any module the host environment lacks.
- **Guard:** Import-walker test.

### P-105 — Timer semantics: monotonic sleep stalls across suspends; sparse cron misses runs
- **Symptom:** Snapshots were missing for hours; only 1 of ~20 scheduled runs fired.
- **Cause:** `sleep 900` uses a clock that does not advance during a pause; a 20-minute external cron fires rarely on a pausable platform.
- **Fix:** Use **wall-clock cadence for 'when to run'** (60 s tick comparing to the last-run time) and **monotonic time for 'how long it may take'**; raise external trigger frequency (e.g. every 5 minutes) and widen UTC windows around DST.
- **Guard:** Cadence test with a mocked pause.

### P-106 — Hidden resource limits and wasted work
- **Symptom:** A job ran at a fraction of expected speed; warm runs rewrote a large cache for nothing.
- **Cause:** A parent cgroup quota was invisible to the child's accounting; no 'already compact' check.
- **Fix:** Measure the whole path stage by stage; read cgroup limits; add read-only no-op checks before rewriting caches; bound LRUs; compare decision bytes before/after any speed-up.
- **Guard:** Before/after identical-output test.

### P-107 — Long monolithic agent tasks die on the agent's own time limit
- **Symptom:** A multi-hour agent program timed out twice.
- **Cause:** One huge step.
- **Fix:** Small fenced steps, commit early, completed work never re-run, resumable via a manifest.
- **Guard:** Resume-after-kill drill.

### P-108 — A secret is pasted into a chat
- **Symptom:** A token appeared in a conversation.
- **Cause:** Convenience.
- **Fix:** Treat as leaked: **revoke/rotate** immediately ('not committed' is not safety); use credential helpers or secret stores instead.
- **Guard:** Process rule.

### P-109 — The host is starved and SSH accepts but never shows a banner
- **Symptom:** Could not log in during a memory/CPU crunch.
- **Cause:** A ballooning non-trading process plus swap thrash.
- **Fix:** Use the provider's web console; read `/proc/pressure/{cpu,memory,io}`, `free`, `ps --sort=-rss`, per-cgroup usage and the kernel OOM log; stop or renice only the dominant **non-trading** process; never restart before a fresh broker reconciliation.
- **Guard:** Runbook entry.

### P-110 — A history mirror crawls because it re-censuses everything
- **Symptom:** A mirror took far too long and lost progress on a dropped connection.
- **Cause:** Per-object checks each pass; no retries.
- **Fix:** Range-limited census, transport retries, and the host's recursive tree API (mind documented size caps; never trust a truncated response).
- **Guard:** Timing test.


## M. Research, data and measurement (added from archive review)

### P-111 — Survivors-only fundamentals and universes create look-ahead
- **Symptom:** Rules based on filings could only fire on names that survived; a model learned that missing filings meant 'later delisted'.
- **Cause:** Data fetched only for currently listed names.
- **Fix:** Point-in-time universes including delisted names; cover rates reported separately; models never see features whose *missingness* encodes the future; score covered-universe rules against controls built from the same covered universe.
- **Guard:** Missingness-leak test.

### P-112 — Clipping and one benchmark hide (or fake) edge
- **Symptom:** Top-1% clipping removed the big winners a tail strategy exists to catch; the only benchmark was an average stock that leans small and volatile.
- **Cause:** Measurement choices.
- **Fix:** Don't clip the tail you claim to harvest; compare against **matched controls** (same volatility/size) and against the *same conditions without the signal*; multiple horizons.
- **Guard:** Matched-control report.

### P-113 — Too few null draws and selection among many books
- **Symptom:** Five random draws could not reject anything (min p ≈ 0.17); one winner among 24 tried books.
- **Cause:** Weak null; hidden multiplicity.
- **Fix:** Many null draws; report the number of books/variants tried; deflated Sharpe; freeze the design before reading holdout/fresh results.
- **Guard:** Null-draw count assertion.

### P-114 — A ranking rule is credited for what the basket did
- **Symptom:** A momentum rule looked great on micro-caps, where random same-width books did better.
- **Cause:** No random-basket control.
- **Fix:** Compare the rule to random books of the same width drawn from the same eligible names; check where ranking adds least.
- **Guard:** Random-basket control.

### P-115 — Indicators that describe the past
- **Symptom:** Signals fired after the move; post-entry excess was ~0.
- **Cause:** The signal day itself was already an outperformance day.
- **Fix:** Measure excess **after entry**, not including the signal bar; test timing separately from selection.
- **Guard:** Post-entry excess table.

### P-116 — Provisional vs completed candles and auction inclusion
- **Symptom:** Signals evaluated post-close used a point quote that predated the closing auction; some hourly/daily frames errored while others quarantined the same tail.
- **Cause:** A quote is not a candle; a completed bar's volume includes the auction; post-market rows can carry prices with zero volume; pre/post-market rows can sit off the grid.
- **Fix:** A `candle_complete` flag; usable-at = max(completed, observed, fetched); label provisional decisions and log provisional-vs-completed disagreements; quarantine non-native tail rows consistently across frames; use one canonical volume source for volume rules; never backfill a label with the next morning's revision.
- **Guard:** Pre-close cached body fixture; early-close short bucket fixture.

### P-117 — Fabricated or mismatched symbols and mixed-start series
- **Symptom:** Requested tickers 404'd; two ETFs existed only at the end of the sample.
- **Cause:** Universe file contained non-provider symbols.
- **Fix:** Data census before any test: loaded / failed / short-history; exclude or label.
- **Guard:** Census report.

### P-118 — A 'self-improving' desk rewriting rules from n≈0
- **Symptom:** Learning loops changed nothing because forward closes were zero — or would have overfit to a week.
- **Cause:** Learning without evidence thresholds.
- **Fix:** Gate learning on forward sample size; run alternatives in **shadow books** beside the live rule; promotions need pre-registered evidence; the learner records excursions without editing rules.
- **Guard:** Promotion-gate test.

### P-119 — Publication artifacts contradict each other
- **Symptom:** A sealed publication contradicted the cards it sealed; the board was empty on its first live day.
- **Cause:** No cross-check between summary and members.
- **Fix:** Cross-checks on every publish artifact (counts, sets, dates) before it goes out.
- **Guard:** Publish contract test.

### P-120 — Retroactive unit changes in corporate-action data
- **Symptom:** Distributions normalised for later splits inflated cash fivefold when combined with historical quantities.
- **Cause:** Unit/basis mismatch.
- **Fix:** Reconcile per-share units to a primary source; carry the adjustment basis with every value.
- **Guard:** Unit-basis fixture.


## N. Observability, services and governance (added from the companion guide)

### P-121 — One green badge for everything
- **Symptom:** A dashboard said 'healthy' with a stale provider.
- **Cause:** Process, input, account and strategy readiness were merged.
- **Fix:** Display **process, input freshness, account reconciliation, strategy readiness** separately; none says anything about expected returns.
- **Guard:** UI contract test.

### P-122 — Health checks that repair
- **Symptom:** A diagnostic restarted or rebuilt production.
- **Cause:** Probe and repair shared one entry point.
- **Fix:** Health endpoints are read-only; repairs are explicitly named actions with logs.
- **Guard:** Probe side-effect test.

### P-123 — Alert delivery conflated with alert creation
- **Symptom:** A notification arrived but the dashboard lacked the event (or vice versa).
- **Cause:** One 'sent' flag.
- **Fix:** Record created / enqueued / submitted / delivered / displayed / acknowledged separately; dedupe by stable event id; mark late, provisional or corrected signals.
- **Guard:** Outbox lifecycle test.

### P-124 — Agreeing agents are not independent evidence
- **Symptom:** Several agents endorsed a bad trade.
- **Cause:** Shared data, model, prompts or anchoring.
- **Fix:** Structured outputs with source-backed claims, counterevidence and missing inputs; deterministic policy gates; models never parsed into orders.
- **Guard:** Schema validation test.

### P-125 — A card or snapshot is mistaken for a running system
- **Symptom:** A repository 'contained a strategy' but lacked engine, data or config.
- **Cause:** Catalog ≠ runtime.
- **Fix:** Trace card → source → config → adapter → tests → runtime owner; mark each link present/absent/historical/synthetic/unverified.
- **Guard:** Trace table.

### P-126 — Risk-policy rollback erases a newer decision
- **Symptom:** An automatic rollback reverted a later operator change.
- **Cause:** Rollback by value instead of by version.
- **Fix:** Compare-and-swap on the policy hash; automatic rollback applies only to the approved trial.
- **Guard:** CAS test.

### P-127 — Disabling a sleeve deletes ownership and exit obligations
- **Symptom:** A position had no safe exit after its sleeve was paused.
- **Cause:** Entry permission and position ownership were one flag.
- **Fix:** Separate 'may open new positions' from 'owns and must service existing positions'.
- **Guard:** Disable-then-exit test.

### P-128 — Silent feed fallback
- **Symptom:** Numbers changed meaning after a provider switched.
- **Cause:** Automatic substitution.
- **Fix:** Provider, feed, delay and price basis are explicit and visible; a fallback is an alert and a labelled state.
- **Guard:** Fallback-label test.

### P-129 — Zero volume vs no trade vs omitted bar vs closed vs unknown
- **Symptom:** 'No signal' hid five different situations.
- **Cause:** Collapsed states.
- **Fix:** Reason-coded coverage states (FRESH/STALE/INCOMPLETE/UNAVAILABLE/UNENTITLED/INVALID/BLOCKED) and distinct 'no signal' reasons.
- **Guard:** State-table test.

### P-130 — Multi-user claims without tenant isolation
- **Symptom:** 'Everyone gets their own instance' with shared in-memory state.
- **Cause:** Assumed isolation.
- **Fix:** Tenant-bound state, quotas, concurrency limits, queue backpressure, and isolation tests; load capacity and isolation are proven separately.
- **Guard:** Cross-tenant access test.


---
*130 entries (P-77 sits with theme A; P-78–P-120 added from the archive review of inter-agent notes and original research logs; P-121–P-130 from the companion guide).* Add yours: when a new failure class appears, add an entry with the next free id and a guard test.
