# aster_rec_rsi2_long_touch_a: Recreation package

Provenance: Ausar R17/R18 options research (Source row in strategies/ausar/opt-recovery.md in this repo).

## What this sleeve is
This sleeve buys a single long call on IWM, QQQ or SPY after a short-term RSI(2) dip inside a long-term uptrend, and exits on a fixed 5-session hold, or earlier if the underlying recovers 2 percent. This book is OPT_RSI2_LONG_TOUCH_A with risk fraction 0.02. It is a thin wrapper delegating to desk3/aster_b2.py.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_b2.py): book="OPT_RSI2_LONG_TOUCH_A", family="recovery", signal="RSI2", structure="long", risk=0.02, dte=(14, 21), delta=(0.5, 0.6), hold=5, max_debit_width=0.6, max_premium_spot=0.025, exit_rule="touch". Constants: FEE_PER_CONTRACT=0.65, SLICE=10000.0. max_debit_width is carried in the SPECS entry but, for structure="long", the binding debit test in _entry is the max_premium_spot test below (max_debit_width binds vertical structures).

Evaluation order in desk3/aster_b2.py::evaluate(sleeve_id, view, ctx):
1. Exits first, over positions that carry option legs (a position without legs has no exit rule here). held is sessions_held if supplied, else the count of the underlying's daily bars dated after the position's opened_at/entry_date. In order: (a) pre-expiry: if the first leg's expiry is within 1 day of the current session date (expiry - session <= 1 day), exit reason `pre_expiry_obligation_exit`; (b) planned: if held >= 5, exit reason `planned_session_exit`; (c) touch only (this sleeve): if the underlying's last daily close (else entry_spot) >= entry_spot * 1.02, exit reason `touch_two_percent_recovery_exit`. Exit intent sells the whole quantity, sell_to_close, with the legs reversed (long leg sell_to_close, any short leg buy_to_close).
2. If any exit was produced, return only exits. If any position carries legs, return no entry (one package per book).
3. Entry window: 09:35 <= ET time < 09:40 (from ctx now / view now; a timestamp without a time is treated as in-window by the code).
4. Signal scan in the fixed symbol order IWM, QQQ, SPY: require at least 200 daily bars; closes[-1] > SMA200 (mean of the last 200 closes) AND RSI(2) < 10, where RSI(2) uses the source smoothing reproduced in _rsi2 (seeded from the first 2 changes as mean gain/loss, then gain = (gain + gain_today) / 2 and loss = (loss + loss_today) / 2 per step; 50.0 if gain and loss are both 0, 100.0 if loss is 0). The first passing symbol is attempted; if its contract entry fails, the scan continues to the next symbol in the code's loop only in the sense that _entry returning None falls through to the next iteration.
5. Contract selection (_select, right="call"): contracts for the underlying with 14 <= DTE <= 21 and 0.5 <= abs(delta) <= 0.6; choose the minimum by (expiry, abs(abs(delta) - 0.55), abs(strike - spot), symbol). Structure is long, so there is one leg with ratio 1 and no wing.
6. Debit gates (_entry): debit per share = the long leg's ask; refuse if debit <= 0 or (debit * 100) / (spot * 100) > 0.025 (i.e. debit / spot > 0.025). Per-contract cash = debit * 100 + 0.65 * 1 leg. qty = int((0.02 * 10000.0) // per-contract cash), capped by the long leg's ask_size; refuse if qty < 1. Risk budget is therefore $200.
7. Mid-price limit enhancement (ENH-ASTERB2-MIDLIMIT-20261024, switch extra["enh_<sid>"] or extra["aster_b2_enh"] {"mid_limit": bool}, default ON): when the leg has a usable bid/ask mid, the entry becomes a limit order at round(mid, 2) instead of a market order and the same mid treatment applies to exits; OFF restores market orders exactly.
Entry intent: kind="entry", side="buy", buy_to_open, time_in_force="day", price_hint = spot, entry_spot = spot, exit_rule="touch", hold_sessions=5, reason naming recovery_qualified_entry, the book, the signal id `<symbol>:<session>` and the debit.

## Files in this repo
- Sleeve wrapper: `adapters3/aster_rec_rsi2_long_touch_a.py` (also `sleeves/aster_rec_rsi2_long_touch_a.py` and `integration/aster_rec_rsi2_long_touch_a_adapter.py`).
- Shared engine: `desk3/aster_b2.py` (this sleeve's SPECS entry, _rsi2, _select, _entry and evaluate).
- Existing family card: `strategies/ausar/opt-recovery.md`.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Universe: IWM, QQQ, SPY in that scan order (underlying ETFs for long calls). Timeframe: 1d bars (200 sessions) for the signal; options DTE 14-21.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0; risk fraction 0.02 of the slice as above; bp_buffer_frac=0.02.
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; params: {} (empty in the roster row; all parameters live in the engine SPECS entry above).
- Parked: false.

## Data inputs
- Inputs declared in the roster row and the adapter: bars, options, positions (INPUTS_COMMON in desk3/aster_b2.py). Producers in the engine PRODUCERS tuple: bars -> bars (freshness_sla_s 900), options_chain -> options (900), broker_readback -> positions (900).
- bars: view["bars"] keyed by `<symbol>|1Day`, `<symbol>|1D` or symbol; at least 200 daily bars per underlying for the signal.
- options: view["options"] as a list of contract rows or the producer's per-underlying dict with chains; each row carries underlying, right, expiry, strike, delta, bid, ask and ask_size. The engine header states inputs not produced by v3 producers (options chain, earnings_events) leave the sleeves UNFED, never fake-fed.
- positions: view["positions"] rows with qty, legs (symbol, underlying, expiry, ratio), sessions_held or opened_at/entry_date, entry_spot and avg_price.

## Install and run
1. Place the engine file(s) listed above in a fresh desk at their desk paths and the wrapper at `adapters3/aster_rec_rsi2_long_touch_a.py` with SLEEVE_ID = "aster_rec_rsi2_long_touch_a" (the repo also carries `sleeves/aster_rec_rsi2_long_touch_a.py` and `integration/aster_rec_rsi2_long_touch_a_adapter.py` copies).
2. Register the roster row for `aster_rec_rsi2_long_touch_a` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_rec_rsi2_long_touch_a, the cadence, session, slice and inputs stated there).
3. Wire the producers named in the Data inputs section so every evaluation snapshot carries the declared inputs, view now (or ctx now), and, where the engine uses it, ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the wrapper, which calls desk3.aster_b2.evaluate(SLEEVE_ID, view, ctx). Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the signal on fixtures: 199 bars, close at or below SMA200, and RSI(2) at or above 10 each produce no entry; the symbol order IWM then QQQ then SPY is respected.
- Check the entry window is 09:35 to 09:40 ET and that a held option package blocks any new entry.
- Check contract selection picks the minimum by (expiry, distance of abs(delta) from 0.55, distance of strike from spot, symbol) inside DTE 14-21 and delta 0.5-0.6.
- Check the debit gate at max_premium_spot=0.025 and sizing: qty equals int(0.02 * 10000 // (debit * 100 + 0.65)), capped by ask_size.
- Check exits in precedence order: pre-expiry (within 1 day), then planned at held >= 5, then touch at underlying >= entry_spot * 1.02.
- Check the mid-limit rule: with the enhancement ON and a usable mid, entry and exit are limits at round(mid, 2); with it OFF, market orders.
