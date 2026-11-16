# GROK-SR-SPY-BUILD — grok_sr_spy install report

Date: 2026-10-28. Spec: `GROK-SR-SPY-SPEC-2026-10-28.md` (FROZEN, committed with this package).
Provenance: X post by @thiccteddy, algo by Grok, installed by owner order 2026-10-28.
Edge status: **UNPROVEN. The live paper record is the test; no backtest is claimed or implied by this install.**

## Scope (InfinityBlade)

- **Surface:** new strategy `sleeves/grok_sr_spy.py`; plumbing pair `adapters/grok_sr_spy.py` + `adapters3/grok_sr_spy.py` (trullas pattern); one config row in `config/sleeves.json` (roster 314 → 315, pins updated at the source in the three pinning test files); one key added to `desk3/producers_g4._BARS_TF_KEYS` (`bars:SPY:1Min`); one tuple widened in `desk3/warm.py` (SPY 1Min fetch 10 → 18 calendar days); new tests `tests/test_grok_sr_spy_blockers.py`; proof `proof/install/grok_sr_spy.json`; BUGLOG entry in `BUGLOG_2026-10-28.md`.
- **Constraints:** the unrelated broker-422 lane's uncommitted work (adapters/laz8_common.py, desk3/aster_batch1.py, desk3/dispatcher.py, desk3/netfetch.py, BUGLOG_2026-10-27.md, STAGE-C-PROGRESS.md and its test files) was never staged, committed, reverted, stashed, or edited; commits are by explicit grok_sr_spy paths only. No Tensor engine files touched; Best Setups untouched. The owner's legal name appears nowhere in this package.
- **Outcome:** a FED, parked=false paper sleeve on SPY 1-minute SIP bars implementing the frozen spec.
- **Proof:** golden/causality/reclaim/caps blocker tests (fail-first proven on two broken variants), full desk gate GREEN (rc=0, 1328 tests discovered), config-reload activation per `desk3/run_live.py` ConfigWatcher (no restart).
- **Edges:** dispatcher executes stop/target from the sleeve's ExitRule data; the sleeve core owns the reclaim-within-3-bars exit and the 13:00 hard flat, which the dispatcher cannot express.

## What was built

SPY shares, long and short. Zone map recomputed deterministically each cycle from the prior 10 completed RTH sessions only (current session excluded; static/no-repaint by construction, no persisted zone state): fractal pivots k=5 per session, volume-at-price nodes in 0.10 bins at/above the 90th percentile of bin volume, single-linkage clustering at max gap 0.40, bands widened to the 0.40 minimum or split at the largest internal gap when wider than 0.80, scored by pivot touches + node volume share, top 6 kept.

Fade: price enters a band from outside, rejection wick beyond the far edge ≥ 50% of range, close back inside the band or beyond its near edge, volume > 1.5× the trailing 20-bar average. Breakout: this bar is the crossing (prior close at or beyond the far edge on the approach side), close beyond the far edge by ≥ 0.10, body ≥ 60% of range, volume greater than the prior bar's and ≥ 1.2× the trailing 20-bar average. Continuation holds are confirmation only; no extra entry (spec). Reclaim invalidation: a close back through the band within 3 bars after the entry fill exits (intent emitted on the reclaim bar's close, filling at the next bar open per desk convention); after 3 bars the rule lapses. Stop beyond the zone ±0.10 (fade short = band top + 0.10, breakout long = band bottom − 0.10, mirrored). Target: nearest band edge in the trade direction or 2R, whichever is closer; 2R when no band lies that way.

Bookkeeping: one open position at a time; a band that produced an exit (reclaim, hard flat, or an exit the desk executed, observed when the position disappears) is dead for the rest of the session; max 3 entries per session; entries 09:30–11:30 ET; hard flat 13:00 ET is the sleeve's own rule, so config `flat_by_close` stays false with `flatten_time_et` null (no second flatten path, trullas precedent). Sleeve state (plan, day counters, dead bands) round-trips through `state/grok_sr_spy/grok_state.json` beside the journal, via the adapter.

## Spec choices (named where the frozen spec is terse or silent)

- **Sizing (spec silent — the gap the scout flagged):** unit risk **0.25% of slice equity** per trade with a **25% notional cap** on slice equity, the desk's trullas_divergence install norm. qty = floor(min(0.0025 × equity / risk-per-share, 0.25 × equity / entry)). This choice is frozen in `proof/install/grok_sr_spy.json`.
- **Entry reference price:** the signal bar's close (signals evaluate on the close and fill at the next bar open per desk convention); stop/target and 2R are computed from that reference.
- **Breakout crossing condition:** a breakout requires the prior bar's close at or beyond the band's far edge on the approach side. Without it, any bar sitting far beyond a distant band counted as "breaking out" through it (found during build: a fade fixture bar spuriously "broke out" through a support band 3+ points below). Cured at the source; see BUGLOG_2026-10-28.md.
- **Fade evaluated before breakout across bands:** a bar that closes back inside a band it rejected at is a fade, even though that close also sits beyond a lower band's far edge.
- **Reclaim definition:** fade — a close through the band's far edge (above band top for a faded resistance short, below band bottom for a faded support long); breakout — a close back inside the band. Window: today's bar indices entry_index+1 … entry_index+3, where entry_index+1 is the fill bar.
- **Trailing volume average:** the 20 bars immediately before the signal bar, same session.
- **Volume nodes:** each bar's volume assigned to the 0.10 bin of its close; node price is the bin center.

## The sleeve is FED (lookback evidence)

The zone map needs the prior 10 RTH sessions (3,900 RTH bars). Measured through the desk's own data path before build (scout, 2026-10-28 ~15:58Z, Alpaca SIP): at the then-current warm window (`desk3/warm.py` SPY 1Min = 10 calendar days) only **7** complete prior RTH sessions were servable — the sleeve would have been silently underfed. Cure, both halves applied:

1. `desk3/warm.py` `INTRADAY_FETCHES`: only the `("SPY", "1Min", 10)` entry widened to **18 calendar days**, proven to serve 12 complete prior RTH sessions (the prior 10 = exactly 3,900 bars, plus buffer). Backward-compatible: every existing SPY 1Min consumer slices `[-n:]`, so extra history changes no existing sleeve's input. QQQ and all other tuples untouched.
2. `adapters/grok_sr_spy.py` requests `bars_old(ctx, "SPY", "1Min", 12000)`: the 18-day warm map holds ~11,261 SPY|1Min rows; a trullas-style N=4000 would have truncated the lookback to ~4 sessions.

Producer key `bars:SPY:1Min` added to `desk3/producers_g4._BARS_TF_KEYS` (the BarsProjection is generic over the warm map and already serves the key; blocker-tested).

## Tests

`tests/test_grok_sr_spy_blockers.py` — **18 tests, all passing**, gate-wired automatically by the gate's `test_*_blockers.py` discover pattern (no edit to run_regression_blockers.sh; that discovery is the wiring mechanism, trullas precedent).

- **Golden zones:** hand-worked clustering from a synthetic pivot/volume prior session (bands [97.80, 98.20], [99.85, 100.25], [101.80, 102.20], each score 1.0) and a largest-internal-gap split fixture (width 0.98 cluster split at the 0.38 gap into two 0.40-minimum bands).
- **Golden fade:** rejection at the resistance band: entry 101.90, stop 102.30, target 101.10 (2R closer than the next band edge at distance 1.65), qty 24 — all computed independently in the test, checked to the cent. A low-volume twin bar produces no entry.
- **Golden breakout:** decisive close through resistance: entry 102.50, stop 101.70, target 104.10 (2R, no band above), qty 24. A non-expanding-volume twin produces no entry.
- **Reclaim:** close back above the faded band on the 2nd bar after the fill bar exits the full position, kills the band, and records it dead; the same close on the 4th bar after the fill bar does **not** exit. Hard flat at 13:00 ET exits.
- **Caps:** 3-entries/day cap blocks; no entries at/after 11:30 ET.
- **Causality:** zones identical when built with or without today's (wild) bars; mutating future bars never changes the entry; truncating the series never changes an earlier decision.
- **Adapter parity:** the adapters3 drive on the golden fade series (live snapshot shape) emits the identical entry and persists `grok_state.json`.
- **Wiring:** roster is exactly 315 with exactly one grok_sr_spy row and no duplicate ids; config row shape mirrors trullas; `adapters3.grok_sr_spy.INPUTS` equals the config row inputs; `bars:SPY:1Min` is in `_BARS_TF_KEYS` and served by BarsProjection; `("SPY", "1Min", 18)` is in `INTRADAY_FETCHES`.

**Fail-first proof:** two deliberately broken variants were run against the suite: (1) zones including the current session (`d <= session`) — the causality test **fails**; (2) `FADE_VOL_MULT` 1.5 → 0.0 — the volume-confirmation test **fails**. The restored module passes 18/18. Variants were scratch edits, reverted and hash-verified, not committed.

## Gate

GREEN: `./run_regression_blockers.sh` on the install working tree — exit code **0**, **1328 tests** in the `test_*_blockers.py` discover (count includes the unrelated broker-422 lane's uncommitted test files, which also passed; nothing of that lane was absorbed or fixed by this install). Roster pins 314 → 315 were updated at the source in `tests/test_deploy_blockers.py`, `tests/test_harden_batch1_blockers.py`, and `tests/test_milkman_0dte_20261027_blockers.py` as part of this install.

## Activation state

Per-cycle config reload, no restart: `desk3/run_live.py` ConfigWatcher hashes `config/sleeves.json` each cycle and rebuilds the Desk before the next 60 s cycle on change. The sleeve is FED on all six declared inputs. First live-cycle FED/read-back evidence belongs to the next desk cycle after this commit and is not claimed here.

**Edge status: UNPROVEN.** No backtest was run or is claimed. The live paper record is the test.
