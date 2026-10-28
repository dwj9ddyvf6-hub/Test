# TEDDY-ORB-SPY-BUILD — teddy_orb_spy install report

Date: 2026-10-28. Spec: `TEDDY-ORB-SPY-SPEC-2026-10-28.md` (FROZEN, committed with this package).
Provenance: X post by @ThiccTeddy, strategy from his posted video, installed by owner order 2026-10-28.
Edge status: **UNPROVEN. The live paper record is the test; no backtest is claimed or implied by this install.**

## Scope (InfinityBlade)

- **Surface:** new strategy `sleeves/teddy_orb_spy.py`; plumbing pair `adapters/teddy_orb_spy.py` + `adapters3/teddy_orb_spy.py` (grok/trullas pattern); one config row in `config/sleeves.json` (roster 315 → 316, pins updated at the source in the four pinning test files); new tests `tests/test_teddy_orb_spy_blockers.py`; proof `proof/install/teddy_orb_spy.json`; BUGLOG entry in `BUGLOG_2026-10-28.md`. No producer edits, no warm-window edits: the 5-minute route reuses the grok_sr_spy install's `bars:SPY:1Min` key.
- **Constraints:** serialization honored: this sleeve landed AFTER grok_sr_spy (committed at HEAD e8f46b3, roster verified 315 before the config edit; pins re-read at edit time and moved from their actual values). The unrelated broker-422 lane's uncommitted work (adapters/laz8_common.py, desk3/aster_batch1.py, desk3/dispatcher.py, desk3/netfetch.py, BUGLOG_2026-10-27.md, STAGE-C-PROGRESS.md and its test files) was never staged, committed, reverted, stashed, or edited; commits are by explicit teddy_orb_spy paths only. No Tensor engine files touched; Best Setups untouched. The owner's legal name appears nowhere in this package (scanned: 0 hits in every package file).
- **Outcome:** a FED, parked=false paper sleeve on SPY implementing the frozen opening-range breakout spec.
- **Proof:** golden/causality/invalidation/caps blocker tests (fail-first proven on two broken variants), full desk gate GREEN (rc=0, 1346 tests discovered), config-reload activation per `desk3/run_live.py` ConfigWatcher (no restart).
- **Edges:** dispatcher executes stop/target from the sleeve's ExitRule data; the sleeve core owns the close-back-inside invalidation exit and the 14:00 hard flat, which the dispatcher cannot express.

## What was built

SPY shares, long and short. Opening range from the first six 5-minute RTH bars (09:30-10:00 ET), fixed at 10:00 ET and never repainting. A breakout qualifies only when a 5-minute bar closes through the range edge with volume at least 1.5x the mean volume of the six opening-range bars, and only by 12:00 ET. After a qualified breakout the sleeve waits for a pullback of 1 to 6 bars: counter-move closes toward the broken edge, no close back inside the range, every pullback bar's volume below the breakout bar's volume. Entry triggers on the first bar after the pullback that closes beyond the pullback's extreme in the breakout direction with volume greater than the last pullback bar; the intent is emitted on that bar's close and fills at the next bar open per desk convention. If no entry triggers within the 6-bar pullback window plus 6 further bars, the setup expires. Any close back inside the range after the breakout kills the setup before entry or exits the trade after entry. Stop sits just inside the broken edge (OR high − 0.10 long, OR low + 0.10 short); target is the measured move (OR height projected from the broken edge) or 2R from entry, whichever is closer. One position at a time; one qualified breakout per direction per day (an invalidated, expired, or completed direction is dead; the opposite direction may still qualify once); no entries after 12:30 ET; hard flat 14:00 ET is the sleeve's own rule, so config `flat_by_close` stays false with `flatten_time_et` null (no second flatten path, trullas/grok precedent).

The day's setup sequence is replayed deterministically from today's completed 5-minute bars on every cycle, so no setup state needs to persist; only the open-trade plan and dead directions round-trip through `state/teddy_orb_spy/teddy_state.json` beside the journal, via the adapter.

## Spec choices (named where the frozen spec is terse or silent)

- **30-minute opening range:** the named choice in the frozen spec (the video does not state the opening period length): the six 5-minute bars 09:30-10:00 ET.
- **Volume thresholds:** breakout at least 1.5x the mean opening-range bar volume (frozen spec); pullback bars each strictly below the breakout bar's volume; trigger bar strictly above the last pullback bar's volume. A pullback bar at or above the breakout volume kills the setup for that direction (that pullback is not the lower-volume pullback the rule requires); this is the anti-churn reading, stated here and in the core docstring.
- **Pullback bar definition (spec terse):** a bar whose close retraces toward the broken edge versus the prior bar's close (down-close for a long breakout, up-close for a short). The pullback extreme is the highest high (long) or lowest low (short) across the pullback bars.
- **Entry window:** breakouts by 12:00 ET, entry triggers by 12:30 ET (the trigger bar must start before 12:30), hard flat 14:00 ET.
- **Sizing (spec silent):** unit risk **0.25% of slice equity** per trade with a **25% notional cap** on slice equity, the desk's trullas_divergence / grok_sr_spy install norm. qty = floor(min(0.0025 × equity / risk-per-share, 0.25 × equity / entry)). Frozen in `proof/install/teddy_orb_spy.json`.
- **Entry reference price:** the trigger bar's close (signals evaluate on the close and fill at the next bar open per desk convention); stop/target and 2R are computed from that reference.

## The 5-minute route actually used (route (b): aggregation in the core)

The frozen spec allows either a native SPY 5Min key or deterministic aggregation. The scout verified the literal key `bars:SPY:5Min` is NOT in `desk3/producers_g4._BARS_TF_KEYS`, so claiming a native 5Min producer would have invented one. Route (b) was chosen: zero producer edits, reusing the grok_sr_spy install's proven `bars:SPY:1Min` key. The v2 adapter requests `bars_old(ctx, "SPY", "1Min", 2000)` (over two full calendar days of SPY 1Min rows including extended hours; the strategy needs only the current session and session-filters in the core). The pure core aggregates: buckets anchored at 09:30 ET, o=first, h=max, l=min, c=last, v=sum, and a bucket is emitted only when all 5 constituent minutes are present, so the forming bucket never appears and never repaints.

Equivalence was re-proven at build time against the desk's native 5Min product on the on-disk warm cache (fetched 2026-10-28T16:38:36Z, SPY|1Min 6818 rows): aggregating the 2026-10-27 RTH 1-minute bars (390) yields exactly 78 5-minute bars with **0 OHLCV mismatches** versus native SPY|5Min. Aggregation loses nothing versus the native product. Volume is Alpaca SIP end to end (the warm path hardcodes feed=sip); Yahoo volume is not used anywhere.

## Tests

`tests/test_teddy_orb_spy_blockers.py` — **18 tests, all passing**, gate-wired automatically by the gate's `test_*_blockers.py` discover pattern (no edit to run_regression_blockers.sh; that discovery is the wiring mechanism, trullas/grok precedent).

- **Aggregation and range:** the 1-minute fixtures rebuild the scripted 5-minute bars exactly; an incomplete trailing bucket (3 of 5 minutes) is dropped; the opening range is the hand-worked high 102.0 / low 98.5 / mean volume 1000 from the six scripted bars; wild post-10:00 bars never move it.
- **Qualification:** a high-volume breakout (2000 vs the 1500 threshold) qualifies as a pending setup but does not enter; the same close-through on volume 1400 must NOT qualify and the full pullback/trigger tail after it produces no entry.
- **Golden entries:** long entry 103.2, stop 101.90, target 105.5 (measured move closer than 2R at 105.8), qty 19; short entry 97.2, stop 98.60, target 95.0, qty 17 — all computed independently in the test from the fixture constants, checked to the cent.
- **Invalidation:** a pullback bar closing back inside the range kills the setup before entry (a later strong bar cannot revive that direction); a post-entry close inside exits the full position and records the direction dead; a higher-volume pullback (2500 vs breakout 2000) produces no entry.
- **Flat and cutoff:** the 14:00 ET hard flat exits an open position; a trigger completing at 12:30 ET produces no entry.
- **Causality:** mutating future bars never changes the entry; truncating the series never changes an earlier decision.
- **Adapter parity:** the adapters3 drive on the golden long series (live snapshot shape) emits the identical entry and persists `teddy_state.json`.
- **Wiring:** roster is exactly 316 with exactly one teddy_orb_spy row and no duplicate ids; the config row shape mirrors trullas/grok; `adapters3.teddy_orb_spy.INPUTS` equals the config row inputs; `bars:SPY:1Min` is in `_BARS_TF_KEYS`.

**Fail-first proof:** two deliberately broken variants were run against the suite: (1) `BREAKOUT_VOL_MULT` 1.5 → 0.0 — the low-volume qualification test **fails** (a spurious entry is emitted); (2) the close-inside predicate `_inside()` forced False — 2 of the 3 invalidation tests **fail**. The restored module was hash-verified (sha256 541bb19b…) and passes 18/18. Variants were scratch edits, reverted and hash-verified, not committed.

## Gate

GREEN: `./run_regression_blockers.sh` on the install working tree — exit code **0**, **1346 tests** in the `test_*_blockers.py` discover (1328 at the grok_sr_spy install + this install's 18; count by loader enumeration; the run includes the unrelated broker-422 lane's uncommitted test files, which also passed — nothing of that lane was absorbed or fixed by this install). Roster pins 315 → 316 were updated at the source in `tests/test_deploy_blockers.py`, `tests/test_harden_batch1_blockers.py`, `tests/test_milkman_0dte_20261027_blockers.py`, and `tests/test_grok_sr_spy_blockers.py` (the fourth pin lives in the grok install's own wiring test).

## Activation state

Per-cycle config reload, no restart: `desk3/run_live.py` ConfigWatcher hashes `config/sleeves.json` each cycle and rebuilds the Desk before the next 60 s cycle on change. The sleeve is FED on all six declared inputs. First live-cycle FED/read-back evidence belongs to the next desk cycle after this commit and is not claimed here.

**Edge status: UNPROVEN.** No backtest was run or is claimed. The live paper record is the test.
