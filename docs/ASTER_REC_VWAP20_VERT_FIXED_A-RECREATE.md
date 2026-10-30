# aster_rec_vwap20_vert_fixed_a: Recreation package

Provenance: Source row in strategies/ausar/opt-recovery.md in this repo: Ausar R17/R18 options research (family Ausar, asset ETF options, timeframe 1d, universe IWM, QQQ, SPY, style mean reversion). The desk adapter header states Aster batch 4, engine desk3/aster_b4.py (contract selection, sizing and entry reuse desk3/aster_b2.py).

## What this sleeve is
This sleeve buys a debit call vertical on IWM, QQQ or SPY after a VWAP20 recovery dip in a long-term uptrend, with a fixed exit rule and the A tier, risk budget $200.00 on the $10,000 slice sizing. It is a thin adapter in adapters3/ whose evaluate(view, ctx) delegates to desk3/aster_b4.py evaluate(SLEEVE_ID, view, ctx), which reuses the entry helper in desk3/aster_b2.py. It implements no strategy math of its own; all rules below are those engines' rules as applied to this sleeve's own SPECS entry.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_b4.py): book="OPT_VWAP20_VERTICAL_FIXED_A", family="recovery", signal="VWAP20", structure="vertical", risk=0.02, dte=(14, 21), delta=(0.5, 0.6), hold=5, max_debit_width=0.6, max_premium_spot=0.025, exit_rule="fixed". Constants reused from desk3/aster_b2.py: SLICE = 10000.0, FEE_PER_CONTRACT = 0.65. A tier, risk budget $200.00 on the $10,000 slice.

Exits, evaluated first (engine _opt_exits in desk3/aster_b4.py), in code order, for each held position that carries legs:
1. Pre-expiry guard: if the first leg's expiry exists and (expiry date minus the session date) is at most 1 day, exit the full qty, reason `pre_expiry_obligation_exit`.
2. Planned session exit: otherwise, if sessions held is at least hold = 5, exit the full qty, reason `planned_session_exit`. Sessions held is the position sessions_held field when present, otherwise the count of bars for the leg underlying dated after opened_at/entry_date.
3. No touch exit: this sleeve's exit_rule is fixed, so the touch branch in the engine does not apply.
Exit intents are sell_to_close, time_in_force day, qty = absolute held qty, price_hint = the position avg_price (or None) before the enhancement below. Exit mid-limit enhancement (ENH-B11-VWAP20VERT-EXITMID-20261024; this sleeve is in the engine ENH11_VERT tuple, on by default; switch extra["enh_aster_rec_vwap20_vert_fixed_a"] {"exit_mid_limit": bool}): when the options rows price both legs with bid > 0 and ask >= bid, the exit becomes a limit order at round(package mid, 2), price_hint becomes the rounded package mid per share, and a paired shadow record (control = the bid/ask cross price) is stored on enhance_exp and in the journal. If any exit intent is produced, entries are not evaluated.

Entries, in code order:
1. One package per book: if any held position carries legs, return no entry.
2. Entry window (desk3/aster_b2.py _in_window): the evaluation time (ctx now, else view now) must satisfy 09:35 <= time < 09:40; a timestamp string without a "T" is treated as inside the window.
3. VWAP20 signal, for each symbol in the order IWM, QQQ, SPY: read daily bars (keys `<sym>|1Day`, `<sym>|1D`, then `<sym>`); fewer than 200 bars fails the symbol. SMA200 is the mean of the last 200 closes. VWAP20 is the volume-weighted average of typical price (H+L+C)/3 over the last 20 bars; non-positive total volume in those 20 bars fails. The symbol passes only when last close > SMA200 and last close <= VWAP20 x 0.98. There is no previous-session or completed-bar validation in this engine's signal function beyond the bar count.
4. Contract selection via desk3/aster_b2.py _entry and _select, for the first passing symbol (right = call): candidates in view["options"] (a list of rows, or the live per-underlying dict with chains, normalised by the engine) with underlying = symbol, right = call, DTE between 14 and 21 inclusive, and absolute delta between 0.5 and 0.6 inclusive. The long leg is the minimum by (expiry string, absolute delta minus the band midpoint 0.55, absolute strike minus spot, symbol), where spot is the last bar close. The vertical wing is a same-expiry call with strike above the long strike, chosen as the minimum by (absolute strike minus spot x 1.02, symbol). No candidate or no wing means no entry.
5. Caps: debit per share is the long leg ask minus the wing bid. Refuse when debit is at most 0, or when debit / width > max_debit_width = 0.6, where width = absolute long minus wing strike difference. max_premium_spot = 0.025 is recorded in the SPECS entry but is applied only to long (non-vertical) structures in the reused entry helper.
6. Sizing (reused helper): per-contract cash = debit per share x 100 + 0.65 x number of legs (2 legs, so debit x 100 + 1.30). Quantity = int((risk x SLICE) // per-contract cash) = int(200.00 // per-contract cash), then capped at the minimum displayed size across the legs (ask_size for the long leg, bid_size for the short wing). Quantity below 1 refuses.
7. Entry intent: market buy, time_in_force day, buy_to_open, symbol = the long leg's OCC symbol, price_hint = spot, reason naming family recovery, book OPT_VWAP20_VERTICAL_FIXED_A and the signal id `<sym>:<session>`, with legs (long ratio +1 buy_to_open, wing ratio -1 sell_to_open, strikes, expiry, right call), entry_spot = spot, exit_rule = "fixed" and hold_sessions = 5. Mid-limit enhancement from the reused helper (ENH-ASTERB2-MIDLIMIT-20261024, on by default; switch extra["enh_aster_rec_vwap20_vert_fixed_a"] or extra["aster_b2_enh"] {"mid_limit": bool}): when every leg mid is computable (bid > 0 and ask >= bid) and the package mid is positive, the entry becomes a limit order at round(package mid, 2) with a paired shadow record whose control price is the ask/bid debit.

Position management: one options package at a time, no pyramiding, no averaging, and no price stop in these engines beyond the exit rules above. The batch-4 engine header states inputs not produced by v3 producers leave the sleeves unfed, never fake-fed.

## Files in this repo
- Sleeve adapter (desk adapters3/aster_rec_vwap20_vert_fixed_a.py): `adapters3/aster_rec_vwap20_vert_fixed_a.py`; also present as `sleeves/aster_rec_vwap20_vert_fixed_a.py` and `integration/aster_rec_vwap20_vert_fixed_a_adapter.py`.
- Shared engines: `desk3/aster_b4.py` (desk source desk3/aster_b4.py, SPECS entry for `aster_rec_vwap20_vert_fixed_a`) and `desk3/aster_b2.py` (reused contract selection, sizing and entry helper).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/ausar/opt-recovery.md`.

## Configuration
- Universe: IWM, QQQ, SPY in that order. Asset: ETF call options (debit vertical). Timeframe: 1d bars for the signal; entry window 09:35 to 09:40 ET.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk fraction 0.02 in the engine SPECS entry (see the Full algorithm sizing rule).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row (all parameters live in the engine SPECS entry).
- Parked: false.
- Roster inputs: bars, options, positions.

## Data inputs
- bars: view["bars"], daily bars per symbol with t, o, h, l, c, v. Producer: bars, freshness SLA 900 seconds (engine PRODUCERS in desk3/aster_b4.py).
- options: view["options"], contract rows with underlying, right, expiry, delta, strike, symbol, ask, bid, ask_size and bid_size (list form or the live per-underlying chains dict). Producer: options_chain, freshness SLA 900 seconds.
- positions: view["positions"] rows with qty, symbol, legs, avg_price, entry_spot, sessions_held and opened_at/entry_date. Producer: broker_readback, freshness SLA 900 seconds.
- Session and clock: ctx session / view now supply the session date; ctx now / view now supply the entry-window clock.

## Install and run
1. Place the engines at desk3/aster_b4.py and desk3/aster_b2.py in the fresh desk (repo copies at the same paths) and the adapter at adapters3/aster_rec_vwap20_vert_fixed_a.py with SLEEVE_ID = "aster_rec_vwap20_vert_fixed_a".
2. Register the roster row for `aster_rec_vwap20_vert_fixed_a` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_rec_vwap20_vert_fixed_a, cadence 300, session rth, $10,000 slice, inputs bars/options/positions).
3. Wire the producers so every snapshot carries daily bars for IWM, QQQ and SPY, the options chain in view["options"], and this sleeve's positions, plus view/ctx now and the session date.
4. First evaluation: call evaluate(view, ctx) on the adapter; it calls desk3.aster_b4.evaluate("aster_rec_vwap20_vert_fixed_a", view, ctx). Confirm a snapshot outside 09:35 to 09:40 ET, with fewer than 200 bars per symbol, or with a package already held returns no entry, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the VWAP20 signal on fixtures: with at least 200 daily bars, last close at or below SMA200, last close above 0.98 x VWAP20, or non-positive 20-bar volume each produce no entry; a passing symbol produces an entry only inside 09:35 to 09:40 ET.
- Check symbol order: when both IWM and QQQ pass, the entry is on IWM; when IWM fails and QQQ passes, the entry is on QQQ.
- Check contract selection: DTE outside 14 to 21 or absolute delta outside 0.5 to 0.6 excludes a contract; the long leg is earliest expiry, then delta nearest 0.55, then strike nearest spot; the wing is the same-expiry call above the long strike nearest spot x 1.02, and a missing wing produces no entry.
- Check the debit cap: package debit / width above 0.6 produces no entry, and sizing: quantity equals int(200.00 // (debit x 100 + 1.30)), capped at the minimum displayed leg size.
- Check the enhancements: with valid bid/ask quotes the entry is a limit order at the package mid (batch-2 mid-limit, on by default) and the exit is a limit order at the package mid (batch-11 exit mid-limit, on by default); with either switch off the corresponding intent is a market order.
- Check exit precedence: pre-expiry (expiry within 1 day) before the 5-session planned exit, and there is no touch exit for this fixed book; any exit suppresses entries in the same evaluation.
