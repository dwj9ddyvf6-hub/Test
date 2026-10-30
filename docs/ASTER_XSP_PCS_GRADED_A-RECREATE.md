# aster_xsp_pcs_graded_a: Recreation package

Provenance: Milkman Trades' ATR premium spec; Ausar R17/R18 options research; the old swing desk via Femto-lean (Source row in strategies/ausar/opt-xsp-pcs.md in this repo).

## What this sleeve is
This sleeve sells a weekly XSP put credit spread on the first session of the week when the prior week's digital put price sits low in its own history. This book is the graded structure with risk 0.03 of the slice. It is a thin wrapper delegating to desk3/aster_b4.py (with helpers imported from desk3/aster_b2.py), and it lands visibly UNFED because no v3 producer supplies the XSP index-regime state yet.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_b4.py): book="OPT_XSP_GRADED_A", family="xsp_pcs", structure="graded", risk=0.03. Constants imported from desk3/aster_b2.py: FEE_PER_CONTRACT=0.65, SLICE=10000.0. Risk budget for this book is 0.03 * 10000.0 = $300.

Evaluation order in desk3/aster_b4.py::_evaluate_xsp (reached from evaluate):
1. Settlement exit first, over non-zero positions carrying legs: if the current session date >= the first leg's expiry date, return a single settle exit for the whole absolute quantity with reason naming official_PM_expiry_settle and settle=True, legs reversed (long leg sell_to_close, short leg buy_to_close), price_hint = avg_price. This is the source's only exit: there is no earlier price stop. If a legged position is held and no settlement is due, return no entry (one package per book).
2. Entry window and calendar: the calendar must mark first_session_of_week, and the ET time must satisfy 10:00 <= time < 10:05. The ET reading uses ENH-B13-XSP-ETWIN-20261024 (switch et_window under extra/ctx key aster_xsp_enh, default ON): timezone-aware stamps are converted to America/New_York before the window test; OFF restores the raw timestamp-slice reading.
3. Weekly state: view["xsp_state"]["weekly_bars"] must be non-empty, its last bar's week_end must equal the calendar's previous_session, and at least 15 weekly bars are required (the weekly ATR14 warmup).
4. Digital history: prior_digitals in xsp_state, filtered to week_end < current session and sorted by week_end, must have unique week_ends, at least 26 entries, and every value strictly between 0 and 1. The percentile window is the last 52 of those values.
5. Current digital: xsp_state["adjacent_put_symbols"] must name exactly 2 distinct contracts present in the chain, both XSP puts expiring on the calendar's weekly_pm_expiry, with no other XSP put of that expiry struck strictly between them (true adjacency). With the two strikes sorted lo < hi and their mids from the chain bid/ask, current = (mid_hi - mid_lo) / (hi - lo); refuse unless 0 < current < 1.
6. Regime gate: median and p75 are the 0.5 and 0.75 quantiles (linear interpolation, _quantile in desk3/aster_b2.py) of the last 52 prior digital values. Refuse if current >= p75; this graded-structure book has no separate median entry gate (the median only selects the strike multipliers in step 8).
7. Weekly ATR14 (_weekly_atr14): true ranges over the weekly bars (first bar skipped), seeded as the mean of the first 14 true ranges, then Wilder-smoothed atr = (atr * 13 + tr) / 14. prior_close is the last weekly bar's close. Refuse if atr <= 0 or prior_close <= 0.
8. Strike targets: calm_flag = current < median. target_short = prior_close - atr * (1.0 if calm_flag else 1.236). For this graded book target_long = prior_close - atr * (1.618 if calm_flag else 1.786).
9. Leg selection among chain XSP puts of the weekly PM expiry: short = the put minimising (abs(strike - target_short), symbol). Long candidates are puts struck below the short strike; long = the candidate minimising (abs(strike - target_long), symbol). No candidates means no entry.
10. Credit, loss and sizing: width = (short strike - long strike) * 100; credit = (short bid - long ask) * 100; refuse if credit <= 0. Max loss per package = width - credit + 2 * 0.65; refuse unless 0 < max loss < width. qty = min(int(risk budget // max loss), int(10000.0 // width), int(long leg ask_size), int(short leg bid_size)); refuse if qty < 1.
Entry intent: kind="entry", symbol = the short put's symbol, side="sell", position_intent="sell_to_open", market, day, qty as computed, entry_spot = prior_close, exit_rule="settle", expiry = the weekly PM expiry, legs = [long put ratio 1 buy_to_open, short put ratio -1 sell_to_open] with strike, expiry, right "put", underlying "XSP" and exercise_style "european" on each leg, reason naming XSP_prior_week_conditional_credit with the digital, median, p75, credit and max loss.

## Files in this repo
- Sleeve wrapper: `adapters3/aster_xsp_pcs_graded_a.py` (also `sleeves/aster_xsp_pcs_graded_a.py` and `integration/aster_xsp_pcs_graded_a_adapter.py`); the wrapper exposes INPUTS = INPUTS_XSP and PRODUCERS = PRODUCERS_XSP from the engine.
- Shared engines: `desk3/aster_b4.py` (this sleeve's SPECS entry and _evaluate_xsp) and `desk3/aster_b2.py` (imported FEE_PER_CONTRACT, SLICE, _bars, _entry, _in_window, _quantile and _sess helpers).
- Contract type: desk3/contract.py, whose repo copy is at `engines/desk3/contract.py` in engines_map.json with status gate_blocked, so that copy was not vendored by the engines pass; the desk original must be supplied from desk3/contract.py to run.
- Existing family card: `strategies/ausar/opt-xsp-pcs.md`.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Universe: XSP (mini-SPX) puts only, weekly PM expiry from the calendar. Asset: index options. Timeframe: 1w (weekly bars and weekly digitals).
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0; risk fraction 0.03 with the sizing formula in the Full algorithm section; bp_buffer_frac=0.02.
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; params: {} (empty in the roster row; all parameters live in the engine SPECS entry above).
- Parked: false.

## Data inputs
- Inputs declared in the roster row and the engine INPUTS_XSP tuple: options, positions, xsp_state. Producers in PRODUCERS_XSP: bars -> bars (freshness_sla_s 900), options_chain -> options (900), broker_readback -> positions (900), xsp_index_regime -> xsp_state (900).
- xsp_state: view["xsp_state"] with weekly_bars (rows with week_end, h, l, c; at least 15, last week_end equal to the calendar previous_session), prior_digitals (rows with week_end and value in (0, 1); at least 26 unique weeks) and adjacent_put_symbols (exactly 2 OCC symbols). The engine header states inputs not produced by v3 producers (OPRA chain, XSP index-regime state) leave the sleeves UNFED, never fake-fed.
- options: view["options"] as a list of contract rows or the producer's per-underlying dict of chains; each row carries symbol, underlying, right, expiry, strike, bid, ask, ask_size and bid_size.
- calendar: view["calendar"] with first_session_of_week, previous_session and weekly_pm_expiry.
- positions: view["positions"] rows with symbol, qty, avg_price and legs (symbol, expiry, ratio).

## Install and run
1. Place the engine file(s) listed above in a fresh desk at their desk paths and the wrapper at `adapters3/aster_xsp_pcs_graded_a.py` with SLEEVE_ID = "aster_xsp_pcs_graded_a" (the repo also carries `sleeves/aster_xsp_pcs_graded_a.py` and `integration/aster_xsp_pcs_graded_a_adapter.py` copies).
2. Register the roster row for `aster_xsp_pcs_graded_a` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_xsp_pcs_graded_a, the cadence, session, slice and inputs stated there).
3. Wire the producers named in the Data inputs section so every evaluation snapshot carries the declared inputs, view now (or ctx now), and, where the engine uses it, ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the wrapper, which calls desk3.aster_b4.evaluate(SLEEVE_ID, view, ctx). Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the calendar and clock gates: a non-first session of the week, and any ET time outside 10:00-10:05, each produce no entry; a UTC-stamped 14:00Z snapshot opens the window with the ET-window enhancement ON and not with it OFF.
- Check the state gates: fewer than 15 weekly bars, a last week_end other than the previous session, fewer than 26 unique prior digitals, a digital value outside (0, 1), and non-adjacent or wrong-expiry adjacent put symbols each produce no entry.
- Check the regime gate for this book: current >= p75 produces no entry.
- Check strike selection: the short put is nearest to prior_close - atr * (1.0 when current < median, else 1.236) and the long put is nearest to prior_close - atr * (1.618 when current < median, else 1.786) among puts below the short strike, with the weekly ATR14 Wilder calculation stated above.
- Check sizing for this book: qty equals min(int(300 // max loss), int(10000 // width), long ask_size, short bid_size), with max loss = width - credit + 1.30, and credit <= 0 produces no entry.
- Check the only exit is the settlement exit on or after the first leg's expiry, and that a held package blocks new entries.
