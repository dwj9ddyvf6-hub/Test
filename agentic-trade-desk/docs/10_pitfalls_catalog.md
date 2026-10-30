# 10 — Pitfalls catalog

Each entry: **Symptom → Cause → Fix → Guard**. IDs are stable; other documents cite them. Every item happened in a real desk. Order is by theme, not severity. For each pitfall you adopt, add its **guard test** to your suite *before* you consider it handled.

How to use: (1) skim headings once; (2) when designing a component, read its theme section fully; (3) when something breaks, search the symptom here before debugging from scratch.

**Severity hints**: P-01, P-02, P-05, P-06, P-12, P-17, P-37, P-58 each risked wrong orders, wrong positions, or unprotected exposure.


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
- **Symptom:** A pass took 66 minutes; a 12:00 time exit never executed; the position was held overnight.
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

### P-16 — Supervisor kills a long but healthy tick every 900 seconds
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
- **Symptom:** Several wake runs failed with usage errors; the desk was down for ~2 hours until a script recovered it.
- **Cause:** Supervision depended on an LLM run.
- **Fix:** Deterministic script supervisor independent of agents; wake-ups quiet when healthy; usage budget and reset date tracked; cheap checks first.
- **Guard:** Chaos test: disable the agent, desk still restarts.

### P-19 — Free-tier quota exhausted mid-morning
- **Symptom:** Failover heartbeat writes would have failed from ~08:30 and the standby would trade beside a live primary.
- **Cause:** Design wrote every 90 s (+ cron writes) ≈ 2,100/day vs 1,000/day.
- **Fix:** Throttle heartbeat (≥ 4 min), write the book only on change (hash metadata), 1 write/cron, write-probe before any live order, stand down on failure; compute worst-case writes per day in a test.
- **Guard:** KV budget simulation test: writes/day < quota, fail-closed 0 orders.

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
- **Cause:** The index-volatility feed was 15 minutes delayed; the freshness limit was 15 minutes.
- **Fix:** Measure feed delay; set the limit above it; use any print from *today's* session for a prior-close comparison; only a previous-session print is unknown.
- **Guard:** Feed-age test with a 15.3-minute-old print.

### P-35 — Entries consistently one share short
- **Symptom:** Every entry got 1 fewer share than the slot allowed.
- **Cause:** Sizing at last price, then the 'never above reserved dollars' rule cut it because the limit had a 1% buffer.
- **Fix:** With no reservation price, size at the limit actually committed.
- **Guard:** Sizing test with a $1,000 slot.

### P-36 — Overlapping sells rejected by the broker
- **Symptom:** Exit failed because a stop already covered the shares.
- **Cause:** Stop orders and exit orders overlapped.
- **Fix:** Cancel *and confirm* overlapping stops before any desk sell; defer the sell if not confirmed; foreign stops respected.
- **Guard:** Fake broker rejecting overlaps.

### P-37 — Disaster stop only lives in desk passes / evaluated one pass late
- **Symptom:** A sleeping machine left positions unprotected; a lot sold a pass after crossing -15%.
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
- **Symptom:** Kernel killed 5–6 GB processes; loop restarts.
- **Cause:** Unbounded caches, long-lived workers with native memory.
- **Fix:** Resident cap with recycle; bounded worker batches; log OOM count at starts.
- **Guard:** Memory soak test.

### P-66 — Disk filled by temp directories
- **Symptom:** 8 GB of headless-browser profile dirs.
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


---
*77 entries (P-77 sits with theme A).* Add yours: when a new failure class appears, add an entry with the next free id and a guard test.
