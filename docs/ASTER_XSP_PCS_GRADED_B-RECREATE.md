# aster_xsp_pcs_graded_b: Recreation package

Provenance: Source row in strategies/ausar/opt-xsp-pcs.md in this repo: Milkman Trades' ATR premium spec; Ausar R17/R18 options research; the old swing desk via Femto-lean (family Ausar, asset index options, timeframe 1w, universe XSP (mini-SPX), style options income). The desk adapter header states Aster batch 4, engine desk3/aster_b4.py.

## What this sleeve is
This sleeve sells a weekly XSP put credit spread whose strikes are set from the prior week's close and weekly ATR14, gated by a prior-week digital regime statistic. It is a thin adapter in adapters3/ whose evaluate(view, ctx) delegates to desk3/aster_b4.py evaluate(SLEEVE_ID, view, ctx). It implements no strategy math of its own; all rules below are the batch-4 engine rules as applied to this sleeve's own SPECS entry.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_b4.py): book="OPT_XSP_GRADED_B", family="xsp_pcs", structure="graded", risk=0.01. Constants imported from desk3/aster_b2.py: SLICE = 10000.0, FEE_PER_CONTRACT = 0.65. Risk budget = 0.01 x 10000.0 = $100.00.

Exit, evaluated first: the source's ONLY exit is European cash settlement at the weekly PM expiry. For each held position carrying legs, if the session date is at or after the first leg's expiry, emit one settle exit: full qty, market, sell_to_close, settle = True, reason official_PM_expiry_settle. No earlier price stop exists in the source. If any position carries legs and no settle is due, entries are not evaluated (one package per book).

Entries, in code order (engine _evaluate_xsp):
1. Calendar and window: view calendar first_session_of_week must be truthy and the evaluation time in ET must satisfy 10:00 <= time < 10:05. Entry-window clock (ENH-B13-XSP-ETWIN-20261024, on by default; switch extra["aster_xsp_enh"] et_window): timezone-aware stamps are converted to ET before the test; naive stamps keep the raw ET reading, and a paired shadow record of both readings is journaled.
2. Weekly bars: view xsp_state weekly_bars must be present, its last row's week_end must equal the calendar previous_session, and there must be at least 15 weekly bars.
3. Prior digitals: xsp_state prior_digitals with week_end before the session, sorted by week_end, must have at least 26 distinct week_ends (no duplicates) and every value strictly between 0 and 1.
4. Current digital: xsp_state adjacent_put_symbols must be exactly 2 distinct symbols present in the options chain, both XSP puts expiring on the calendar weekly_pm_expiry, with no other XSP put for that expiry struck strictly between them (adjacency). With lo/hi their strikes in ascending order and mids from bid/ask, current = (mid of the higher strike minus mid of the lower strike) / (hi - lo); refuse unless 0 < current < 1.
5. Regime gate: vals are the last 52 prior digital values; median = the 0.5 quantile and p75 = the 0.75 quantile by the engine _quantile. Refuse when current >= p75 (reason class XSP_conditional_regime_skip). The additional median skip applies only to the calm structure, not to this graded sleeve. calm regime for strike distances means current < median.
6. ATR: _weekly_atr14 over the weekly bars: true ranges from bar 2 onward, Wilder ATR14 seeded as the mean of the first 14 true ranges then atr = (atr x 13 + tr) / 14; priorclose is the last weekly close. Refuse when atr <= 0 or priorclose <= 0.
7. Strike targets (graded): target_short = priorclose - atr x (1.0 if calm else 1.236); target_long = priorclose - atr x (1.618 if calm else 1.786). Among XSP puts for the weekly PM expiry, the short leg is the nearest strike to target_short; the long leg is the nearest strike to target_long among puts struck below the short strike (the exactly-5-points rule applies only to calm). No puts or no long candidate means no entry.
8. Credit and loss: width = (short strike - long strike) x 100; credit = (short bid - long ask) x 100; refuse when credit <= 0. Max loss per package = width - credit + 2 x 0.65; refuse unless 0 < max loss < width.
9. Sizing: qty = min(int(100.00 // max loss), int(10000.0 // width), int(long ask_size), int(short bid_size)); qty below 1 refuses (XSP_package_unaffordable).
10. Entry intent: sell_to_open, market, day, qty as computed, symbol = the short leg's OCC symbol, price_hint = None, entry_spot = priorclose, exit_rule = "settle", expiry = the weekly PM expiry, legs: long put ratio +1 (buy_to_open) and short put ratio -1 (sell_to_open), both european, with the reason naming book OPT_XSP_GRADED_B, digital, median, p75, credit and max loss.

Position management: one package at a time, no pyramiding, no averaging, and no price stop beyond the settlement exit above.

## Files in this repo
- Sleeve adapter (desk adapters3/aster_xsp_pcs_graded_b.py): `adapters3/aster_xsp_pcs_graded_b.py`; also present as `sleeves/aster_xsp_pcs_graded_b.py` and `integration/aster_xsp_pcs_graded_b_adapter.py`.
- Shared engine: `desk3/aster_b4.py` (desk source desk3/aster_b4.py, SPECS entry for `aster_xsp_pcs_graded_b`); it imports SLICE, FEE_PER_CONTRACT and helpers from `desk3/aster_b2.py`.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/ausar/opt-xsp-pcs.md`. Existing per-sleeve algorithm doc: `docs/ASTER_XSP_PCS_GRADED_B-ALGORITHM.md`.

## Configuration
- Universe: XSP (mini-SPX) weekly puts only. Asset: index options (put credit spread). Timeframe: 1w (weekly bars and weekly PM expiry); entry window 10:00 to 10:05 ET on the first session of the week.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk fraction 0.01 in the engine SPECS entry (see the Full algorithm sizing rule).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row (all parameters live in the engine SPECS entry).
- Parked: false.
- Roster inputs: options, positions, xsp_state.

## Data inputs
- options: view["options"], XSP put contract rows with underlying, right, expiry, strike, symbol, bid, ask, bid_size and ask_size (list form or the live per-underlying chains dict). Producer: options_chain, freshness SLA 900 seconds (engine PRODUCERS_XSP in desk3/aster_b4.py).
- positions: view["positions"] rows with qty, symbol, legs and avg_price. Producer: broker_readback, freshness SLA 900 seconds.
- xsp_state: view["xsp_state"] with weekly_bars (h, l, c, week_end), prior_digitals (week_end, value) and adjacent_put_symbols. Producer: xsp_index_regime, freshness SLA 900 seconds. The engine header states inputs not produced by v3 producers (OPRA chain, XSP index-regime state) leave the sleeve unfed, never fake-fed.
- calendar: view["calendar"] with first_session_of_week, previous_session and weekly_pm_expiry; ctx now / view now supply the entry-window clock.

## Install and run
1. Place the engines at desk3/aster_b4.py and desk3/aster_b2.py in the fresh desk (repo copies at the same paths) and the adapter at adapters3/aster_xsp_pcs_graded_b.py with SLEEVE_ID = "aster_xsp_pcs_graded_b".
2. Register the roster row for `aster_xsp_pcs_graded_b` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_xsp_pcs_graded_b, cadence 300, session rth, $10,000 slice, inputs options/positions/xsp_state).
3. Wire the producers so every snapshot carries the XSP put chain in view["options"], this sleeve's positions, view["xsp_state"] (weekly bars, prior digitals, adjacent put symbols), view["calendar"], and view/ctx now.
4. First evaluation: call evaluate(view, ctx) on the adapter; it calls desk3.aster_b4.evaluate("aster_xsp_pcs_graded_b", view, ctx). Confirm a snapshot that is not the first session of the week, outside 10:00 to 10:05 ET, with fewer than 15 weekly bars or fewer than 26 prior digitals returns no entry, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the window and calendar gates: no entry when first_session_of_week is false, or at 09:59 ET or 10:05 ET; an entry is possible only at 10:00 to 10:04 ET, and a UTC-stamped 14:00Z stamp opens the window with the enhancement on.
- Check the regime gate: current digital at or above the 75th percentile of the last 52 prior digitals produces no entry; the same value below the median uses the 1.0 / 1.618 ATR distances, and at or above the median uses 1.236 / 1.786.
- Check adjacency and history: non-adjacent adjacent_put_symbols, a duplicate prior-digital week, fewer than 26 digitals, or a digital value outside (0, 1) each produce no entry.
- Check strike choice, credit and sizing: the short and long legs are the puts nearest the two targets, credit must be positive, max loss must satisfy 0 < max loss < width, and quantity equals min(int(100.00 // max loss), int(10000.0 // width), long ask_size, short bid_size).
- Check the exit: a held package emits nothing before its expiry session and exactly one settle exit on or after it, and any held package suppresses entries.
