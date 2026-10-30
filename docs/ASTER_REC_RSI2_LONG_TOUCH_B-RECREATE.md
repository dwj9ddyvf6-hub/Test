# aster_rec_rsi2_long_touch_b: Recreation package

Provenance: Source row in strategies/ausar/opt-recovery.md in this repo: Ausar R17/R18 options research (family Ausar, asset ETF options, timeframe 1d, universe IWM, QQQ, SPY, style mean reversion). The desk adapter header states Aster batch 2, engine desk3/aster_b2.py.

## What this sleeve is
This sleeve buys a single-leg long call on IWM, QQQ or SPY after an RSI2 dip in a long-term uptrend, and exits on a 2 percent recovery touch, at the 5-session planned exit, or before expiry. It is a thin adapter in adapters3/ whose evaluate(view, ctx) delegates to desk3/aster_b2.py evaluate(SLEEVE_ID, view, ctx). It implements no strategy math of its own; all rules below are the batch-2 engine rules as applied to this sleeve's own SPECS entry.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_b2.py): book="OPT_RSI2_LONG_TOUCH_B", family="recovery", signal="RSI2", structure="long", risk=0.005, dte=(14, 21), delta=(0.5, 0.6), hold=5, max_debit_width=0.45, max_premium_spot=0.015, exit_rule="touch". Constants: SLICE = 10000.0, FEE_PER_CONTRACT = 0.65. B tier, risk budget $50.00 on the $10,000 slice.

Exits, evaluated first, in code order, for each held position that carries legs (a position without legs is skipped: the engine has no exit rule for a leg-less equity position):
1. Pre-expiry guard: if the first leg's expiry exists and (expiry date minus the session date) is at most 1 day, exit the full qty, reason `pre_expiry_obligation_exit`.
2. Planned session exit: otherwise, if sessions held is at least hold = 5, exit the full qty, reason `planned_session_exit`. Sessions held is the position sessions_held field when present, otherwise the count of bars for the leg underlying dated after opened_at/entry_date.
3. Touch exit (this sleeve's exit_rule is touch): otherwise, if entry_spot is present and the last bar close for the underlying is at least entry_spot x 1.02, exit the full qty, reason `touch_two_percent_recovery_exit`.
Exit intents are sell_to_close, time_in_force day, qty = absolute held qty, price_hint = the position avg_price (or None). Mid-limit enhancement (ENH-ASTERB2-MIDLIMIT-20261024, on by default; switch extra["enh_aster_rec_rsi2_long_touch_b"] or extra["aster_b2_enh"] {"mid_limit": bool}): when every leg's contract row is present in view["options"] with a computable mid (bid > 0 and ask >= bid), the exit becomes a limit order at round(package mid, 2), where the package mid sums +mid for ratio > 0 legs and -mid for ratio < 0 legs, only when that sum is positive; a paired shadow record (control = the bid/ask cross price) is stored on enhance_exp and in the journal. If any exit intent is produced, entries are not evaluated.

Entries, in code order:
1. One package per book: if any held position carries legs, return no entry.
2. Entry window: the evaluation time (ctx now, else view now) must satisfy 09:35 <= time < 09:40; a timestamp string without a "T" is treated as inside the window.
3. Signal, for each symbol in the order IWM, QQQ, SPY: read daily bars (keys `<sym>|1Day`, `<sym>|1D`, then `<sym>`); fewer than 200 bars skips the symbol. Compute SMA200 as the mean of the last 200 closes and RSI2 by the engine _rsi2 recursion: changes over all closes; gain and loss are seeded as the mean of the positive and negative parts of the first 2 changes divided by 2 in the code's summed form, then each later change updates gain = (gain + max(change, 0)) / 2 and loss = (loss + max(-change, 0)) / 2; RSI2 = 50 if gain and loss are both 0, 100 if loss is 0, else 100 - 100 / (1 + gain / loss). The symbol passes only when last close > SMA200 and RSI2 < 10.
4. Contract selection for the first passing symbol (right = call): candidates in view["options"] (a list of rows, or the live per-underlying dict with chains, normalised by the engine) with underlying = symbol, right = call, DTE between 14 and 21 inclusive, and absolute delta between 0.5 and 0.6 inclusive. The long leg is the minimum by (expiry string, absolute delta minus the band midpoint 0.55, absolute strike minus spot, symbol), where spot is the last bar close. No candidate means no entry for that symbol.
5. Caps: this is a long structure, so the premium cap applies: debit per share is the long leg ask; refuse when debit / spot > max_premium_spot = 0.015 (the code computes (debit x 100) / (spot x 100)). max_debit_width = 0.45 is recorded in the SPECS entry but is applied only to vertical structures in this engine. Debit at most 0 also refuses.
6. Sizing: per-contract cash = debit per share x 100 + 0.65 x number of legs (1 leg, so debit x 100 + 0.65). Quantity = int((risk x SLICE) // per-contract cash) = int(50.00 // per-contract cash), then capped at the long leg's ask_size. Quantity below 1 refuses.
7. Entry intent: market buy, time_in_force day, buy_to_open, symbol = the long leg's OCC symbol, price_hint = spot (the last bar close), reason naming family recovery, book OPT_RSI2_LONG_TOUCH_B and the signal id `<sym>:<session>`, with legs (ratio +1, strike, expiry, right call), entry_spot = spot, exit_rule = "touch" and hold_sessions = 5. Mid-limit enhancement (same switch as exits, on by default): when the leg mid is computable and positive, the entry becomes a limit order at round(mid per share, 2) with a paired shadow record whose control price is the ask debit.

Position management: one options package at a time, no pyramiding, no averaging, no stop-loss price rule in this engine beyond the three exit rules above.

## Files in this repo
- Sleeve adapter (desk adapters3/aster_rec_rsi2_long_touch_b.py): `adapters3/aster_rec_rsi2_long_touch_b.py`; also present as `sleeves/aster_rec_rsi2_long_touch_b.py` and `integration/aster_rec_rsi2_long_touch_b_adapter.py`.
- Shared engine: `desk3/aster_b2.py` (desk source desk3/aster_b2.py, SPECS entry for `aster_rec_rsi2_long_touch_b`).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/ausar/opt-recovery.md`.

## Configuration
- Universe: IWM, QQQ, SPY in that order. Asset: ETF call options (single-leg long). Timeframe: 1d bars for the signal; entry window 09:35 to 09:40 ET.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk fraction 0.005 in the engine SPECS entry (see the Full algorithm sizing rule).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row (all parameters live in the engine SPECS entry).
- Parked: false.
- Roster inputs: bars, options, positions.

## Data inputs
- bars: view["bars"], daily bars per symbol with t and c (the engine reads the close; exit held-counting also reads bar dates). Producer: bars, freshness SLA 900 seconds (engine PRODUCERS in desk3/aster_b2.py).
- options: view["options"], contract rows with underlying, right, expiry, delta, strike, symbol, ask, bid and ask_size (list form or the live per-underlying chains dict). Producer: options_chain, freshness SLA 900 seconds. The engine header states inputs not produced by v3 producers leave the sleeve unfed, never fake-fed.
- positions: view["positions"] rows with qty, symbol, legs, avg_price, entry_spot, sessions_held and opened_at/entry_date. Producer: broker_readback, freshness SLA 900 seconds.
- Session and clock: ctx session / view now supply the session date; ctx now / view now supply the entry-window clock.

## Install and run
1. Place the engine at desk3/aster_b2.py in the fresh desk (repo copy at the same path) and the adapter at adapters3/aster_rec_rsi2_long_touch_b.py with SLEEVE_ID = "aster_rec_rsi2_long_touch_b".
2. Register the roster row for `aster_rec_rsi2_long_touch_b` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_rec_rsi2_long_touch_b, cadence 300, session rth, $10,000 slice, inputs bars/options/positions).
3. Wire the producers so every snapshot carries daily bars for IWM, QQQ and SPY, the options chain in view["options"], and this sleeve's positions, plus view/ctx now and the session date.
4. First evaluation: call evaluate(view, ctx) on the adapter; it calls desk3.aster_b2.evaluate("aster_rec_rsi2_long_touch_b", view, ctx). Confirm a snapshot outside 09:35 to 09:40 ET, with fewer than 200 bars per symbol, or with a package already held returns no entry, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the signal on fixtures: with at least 200 daily bars, a symbol with last close at or below SMA200, or RSI2 at or above 10, produces no entry; a passing symbol produces an entry only inside 09:35 to 09:40 ET.
- Check symbol order: when both IWM and QQQ pass, the entry is on IWM; when IWM fails and QQQ passes, the entry is on QQQ.
- Check contract selection: DTE outside 14 to 21 or absolute delta outside 0.5 to 0.6 excludes a contract; among candidates the earliest expiry wins, then delta nearest 0.55, then strike nearest spot.
- Check the premium cap: a long ask with ask / spot above 0.015 produces no entry, and sizing: quantity equals int(50.00 // (ask x 100 + 0.65)), capped at ask_size.
- Check the mid-limit enhancement: with bid > 0 quotes present the entry and exit intents are limit orders at the rounded package mid; with the switch off they are market orders.
- Check exit precedence: pre-expiry (expiry within 1 day) before the 5-session planned exit, planned exit before the touch exit, the touch exit fires exactly when the last close reaches entry_spot x 1.02, and any exit suppresses entries in the same evaluation.
