# INVESTANDBEFREE-DMAC — BUILD REPORT (2026-10-29)

Sleeve `investandbefree_dmac` built and installed per
INVESTANDBEFREE-DMAC-SPEC-2026-10-29.md (FROZEN), following the
grok_sr_spy / teddy_orb_spy install pattern. Edge UNPROVEN; no
backtest claimed; the live paper record is the test.

## What was built

- `sleeves/investandbefree_dmac.py` — pure core. Wilder and
  exponential MACDs (12/26/9) as separately unit-testable
  smoothers; 4H buckets aggregated in-core from 1H bars (RTH only,
  anchored to the session's first RTH bar, emitted only when a
  bucket holds exactly 4 consecutive hourly bars); alignment
  (both MACDs same side of their signals); dominance (slowest
  aligned timeframe weekly > daily > 4H, trade requires dominant
  == daily); crossover/curl triggers on the last closed daily
  bar; ATM strike at the nearest expiry >= 30 calendar days;
  10% spread gate; USD 2,000 budget with 25% slice hard cap;
  exits in order: 50% premium stop, dominant break, +100% partial
  leaving >= 1 runner (qty 1 = full exit, once per position),
  runner out on a daily MACD-E cross against or at 5 DTE, with
  the daily-layer hold (runner ignores 4H flips while daily
  alignment holds). Position state (entry premium, qty, contract
  identity, partial-done flag) uses the capitulation_options
  sleeve-state shape.
- `adapters/investandbefree_dmac.py` — plumbing adapter (grok
  pattern): daily/weekly/hourly bars via the bridge, chains and
  quotes from the established 'options' input, sleeve state from
  broker positions merged with the persisted plan in
  `dmac_state.json` beside the sleeve journal.
- `adapters3/investandbefree_dmac.py` — v3 entrypoint, INPUTS =
  bars, bars:*:1Day, bars:*:1Hour, bars:*:1Week, options,
  positions, quotes, session_fills (all bars keys already in
  producers_g4._BARS_TF_KEYS).
- `INVESTANDBEFREE-DMAC-SPEC-2026-10-29.md` — desk spec doc with
  every rule labeled extracted / inferred / recreated / deviation.
- `tests/test_investandbefree_dmac_blockers.py` — 23 blocker
  tests, gate-wired by the gate's `test_*_blockers.py` discover
  pattern (run_regression_blockers.sh itself is pattern-based
  and needed no edit). Golden expectations are independent:
  an in-test MACD implementation written from the definitions
  plus hand-embedded values, hand sizing/partial arithmetic.
- `proof/install/investandbefree_dmac.json` — install proof in
  the grok format (hashes, frozen parameters, feeding proof,
  fail-first evidence).

## Every file touched

Created: INVESTANDBEFREE-DMAC-SPEC-2026-10-29.md,
sleeves/investandbefree_dmac.py, adapters/investandbefree_dmac.py,
adapters3/investandbefree_dmac.py,
tests/test_investandbefree_dmac_blockers.py,
proof/install/investandbefree_dmac.json, this build report.
Modified: config/sleeves.json (one appended row; roster 328 ->
329), desk3/warm.py (feeding windows, below), BUGLOG_2026-10-29.md
(install entry appended), and the roster-count pins 328 -> 329 in
tests/test_deploy_blockers.py, tests/test_harden_batch1_blockers.py,
tests/test_milkman_0dte_20261027_blockers.py,
tests/test_teddy_orb_spy_blockers.py,
tests/test_grok_sr_spy_blockers.py,
tests/test_trullas_variants_blockers.py,
tests/test_przm_recreation_blockers.py (the last is the
concurrent PRZM lane's untracked file; only its roster-count
assertion changed, so the gate stays truthful at 329).
No fenced file was touched, staged, reverted, or committed: the
pre-existing dirty set (BUGLOG_2026-10-27.md, STAGE-C-PROGRESS.md,
adapters/laz8_common.py, desk3/aster_batch1.py,
desk3/dispatcher.py, desk3/netfetch.py,
tests/test_aster_batch1_blockers.py,
tests/test_edge_batch5_blockers.py, the untracked przm_*
sleeves/adapters and broker-422 test files) is byte-for-byte as
found, apart from the single named pin line above.

## Feeding proof

Observed from the desk's own warm product on disk at build time
(state/warm_bars.json, fetched 2026-10-29T15:05:50Z): SPY and QQQ
daily 346 rows each (need >= 300: FED); weekly 72 rows each (need
120: SHORT); 1Hour 359 rows each, about 51 sessions (need 120
sessions for the 4H stack: SHORT). Cure, minimal and named, in
desk3/warm.py: the weekly fetch window widens 500 -> 1000
calendar days (~143 bars) and targeted SPY/QQQ 1Hour fetches at
200 calendar days (~140 RTH sessions) join INTRADAY_FETCHES, the
same shape as the grok install's SPY 1Min widening. The widened
windows are pinned by blocker tests; the larger counts land at
the next warm cycle. Fixture drive through the real adapter path
(blocker TestAdapterDrive): a full snapshot view produces exactly
one entry intent (ATM 2026-11-28 call, qty 4 = floor(2000/500))
and dmac_state.json round-trips with the contract identity and
partial_done=false.

## Gate result

Full gate: `desk/run_regression_blockers.sh` exit code 0 on the final tree; unittest discover reported "Ran 1401 tests, OK" (the pre-install tree ran 1378; +23 new blockers = 1401, matching exactly). The new blocker file alone: 23/23 OK. Fail-first: QUOTE_GATE_FRAC and PREMIUM_STOP_FRAC mutations each failed their targeted test and were restored byte-identical (a stale .pyc produced by the same-second restore was cleared and the pass re-proven).

## Deviations

- The vendor's event-calendar gate items are NOT implemented in
  v1 (index ETFs have no earnings; no macro calendar producer is
  wired for this sleeve). Named in the desk spec doc.
- No ladder fallback entries; no overbought/oversold runner exit.
  Both named in the desk spec doc.
- Recreated defaults frozen, per the source SPEC: 12/26/9
  periods, ATM strike, 30-day expiry bound, 50% premium stop,
  USD 2,000 budget / 25% cap, 10% spread gate, exact
  alignment/dominance/curl step forms, 5-DTE runner bound.

## Real-frames evaluation (independent verification, 2026-10-29)

Verifier: independent phase, not the builder. Method: real bars
fetched fresh through the desk's own data path (desk3/warm.py
fetch_all, Alpaca SIP, paper credentials route) at 2026-10-29
~16:0xZ, and a real options chain fetched through the desk's own
options producer (desk3/producers.build_options_payload, Alpaca
contracts + indicative snapshots, fetched 2026-10-29). The
installed adapters3.investandbefree_dmac.evaluate path was then
driven day by day, fresh state per session, as of 16:05 ET on
each session, with bars truncated to CLOSED bars only for that
session (daily bars dated <= session; weekly bars whose week had
ended before the session's week; hourly bars dated <= session).
Options chain in the view: the live 2026-10-29 chain (SPY 4,322
quotable rows, QQQ 4,008), because the desk path serves no
historical OPRA quotes; contract selection therefore ran on real
current quotes, and the ask/qty printed for a historical session
are the 2026-10-29 quote basis for that same OCC, NOT the
session-day premium (named limitation of this evaluation).

### Bars actually delivered per timeframe per symbol (fresh fetch)

- SPY: 1Day 346 rows (2025-06-16 to 2026-10-29), 1Week 143 rows
  (2024-02-05 to 2026-10-26), 1Hour 2,232 rows (2026-04-13 to
  2026-10-29). QQQ: identical counts and ranges.
- The widened warm windows are proven by this fetch: weekly
  72 -> 143 rows, hourly 359 -> 2,232 rows versus the on-disk
  warm product from build time (fetched 2026-10-29T15:05:50Z:
  1Day 346, 1Week 72, 1Hour 359 per symbol).
- Per driven session the adapter received, per symbol: daily
  341 to 345 rows, weekly (closed weeks only) 141 to 142 rows,
  hourly 2,160 to 2,224 rows, aggregating in-core to 135 to 139
  complete RTH 4H bars.

### Alignment census (closed bars, fresh-data windows)

Last 15 closed sessions (2026-10-08 to 2026-10-28), both symbols,
computed with the sleeve's own evaluate_timeframes on the fresh
windows:

- Bullish zone 2026-10-08 to 2026-10-14: daily +1 for both
  symbols; weekly +1 for QQQ from 2026-10-12 (SPY weekly
  unaligned: its two weekly MACDs disagree); 4H +1 except QQQ
  4H unaligned 10-12 to 10-14. Dominant = daily (SPY) / weekly
  (QQQ, +1, agreeing with daily). No trigger on any of these
  days (no MACD-E crossover, no curl on the last daily bar).
- 2026-10-15: daily unaligned for both (transition day); SPY
  dominant falls to 4H (-1) with daily unaligned = no trade;
  QQQ weekly +1 alone = no trade.
- Bearish zone 2026-10-16 to 2026-10-28: daily -1 for both
  symbols every session; 4H -1 every session; weekly unaligned
  until 2026-10-26, then weekly -1 for both, so dominant =
  weekly (-1) 10-26 to 10-28, agreeing with daily. Triggers:
  SPY curl (bearish) on 2026-10-22 and 2026-10-23 only; QQQ no
  trigger on any session in the window.

### Signals through the installed adapter path (fresh state per session)

- 2026-10-22 SPY: ENTRY, bearish curl, dominant=daily (-1).
  Buy to open SPY261127P00764000 (SPY put, strike 764, expiry
  2026-11-27, the nearest listed expiry >= 30 calendar days:
  2026-11-20 is only 29 days out). Qty 2 =
  floor(2000 / (8.53 x 100)) = 2, also the 25% cap floor.
  Entry premium basis: ask 8.53, the 2026-10-29 indicative ask
  for this OCC (see limitation above). dmac_state.json
  round-tripped with direction -1, qty 2, partial_done=false.
- 2026-10-23 SPY: ENTRY (fresh-state scan), bearish curl,
  dominant=daily (-1). Buy to open SPY261127P00760000 (strike
  760, expiry 2026-11-27), qty 2, ask basis 7.52 (2026-10-29
  quote basis, same limitation). Note: in sequential live
  running the 2026-10-22 position would already be open, so
  the one-position-per-underlying rule would suppress this as
  a second entry; it is listed because this scan drives each
  session with fresh state to surface every trigger day.
- 2026-10-26, 2026-10-27, 2026-10-28: ZERO intents for both
  symbols, explained by the census above: full bearish
  alignment (weekly = daily = 4H = -1 from 10-26) but no
  crossover and no curl on those daily bars.
- QQQ: zero intents on all five driven sessions (daily -1
  aligned from 10-16 but no trigger in the window).

### Verification verdict on this evaluation

The pipeline is FED and the drive is clean: the sleeve emits
exactly where the frozen rules say it should on real frames
(two SPY bearish-curl entries, nothing else), and zero-signal
sessions are explained by the alignment/trigger census, not by
missing data. One rule-fidelity failure was found elsewhere in
the verification (live-path forming bars, see the verification
feedback): this evaluation deliberately truncated to closed
bars, which the installed live path itself does not do.

## Repair: closed-bars-only + alignment-loss exit (2026-10-29)

The independent verifier failed the install on two findings;
both are cured at the source, in this sleeve's own files only
(`BUGLOG_2026-10-29.md` entry
INVESTANDBEFREE-DMAC-CLOSEDBARS-20261029):

- FAILURE 1 (blocking): closed-bars-only was violated at the
  real execution boundary. signal() consumed bars[-1]
  unconditionally and the adapter stripped nothing, while the
  desk path serves the forming daily bar (that day's intraday
  print), the unfinished current weekly bar, and the
  in-progress hourly bar; with cadence_s=3600 in RTH the live
  sleeve would have evaluated entries/exits on forming bars on
  every timeframe, including 4H buckets built from a forming
  hour. Cure: `closed_bars(bars, timeframe, now)` in the core
  keeps a bar only once its period has ended as of
  Context.now (1Hour: start + 3600s; 1Day: the next ET midnight
  after the bar's ET session date; 1Week: the next Monday
  00:00 ET after the bar's Monday-anchored ET week; no readable
  timestamp = dropped, unprovable). signal() filters the daily,
  weekly and 1Hour inputs through it before any MACD or 4H
  aggregation, and the adapter applies the same filter at the
  desk boundary, so the cure holds at both layers.
- FAILURE 2 (secondary): _manage's dominant-break branch
  required dominant_dir not-None and the runner daily-break
  branch required daily not-None, so a complete loss of
  alignment on every timeframe (dominant_dir None) produced no
  exit. Both branches now treat None as a break: pre-partial,
  any dominant_dir != direction exits; for the runner, any
  daily != direction exits. Opposite-direction flips behave
  exactly as before.

Blockers (gate-wired, same file): 5 new tests.
TestClosedBarsOnly covers the period-end arithmetic for all
three timeframes, a core entry drive whose intent (reason and
qty) is byte-identical with crash-priced forming daily and
weekly bars appended, and an adapter drive at a mid-session
timestamp (2026-10-29 12:00 ET) with forming bars appended to
the snapshot, still emitting exactly the one closed-bar entry.
TestAlignmentLossExits covers total alignment loss (flat
closes on every timeframe) exiting both an open position
(dominant_alignment_break) and a runner
(daily_alignment_break_runner). Fail-first: all 5 failed on
the pre-cure code; in the adapter drive the pre-cure code
emitted the opposite-direction put (SPY261128P00239000) off
the forming daily bar, which is the verifier's failure in
miniature. The fixture helper `_bars` was retimestamped to
end at the last closed bar (2026-10-28) relative to the
fixtures' mid-session now; NO golden expectation changed:
every closes series, sizing, strike, expiry and reason
expectation is exactly as installed. Blocker file: 28/28 OK.

Gate after the repair: `run_regression_blockers.sh` exit
code 0 on the final tree; unittest discover reported "Ran 1406 tests"
(1401 at install + 5 new blockers, matching exactly), the
single error in one manual non-gate discover rerun being the
isolated-tree test recursively copying a hand-made in-repo
temp dir from that rerun itself, absent under the gate's own
temp handling. The install proof
(proof/install/investandbefree_dmac.json) was refreshed with
the new file hashes, the repair record and the 1406 count.
