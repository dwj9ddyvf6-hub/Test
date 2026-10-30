# aster_pead_vertical_b - RECREATE

Provenance: Ausar R17/R18 options research (Source row of the existing Test doc `strategies/ausar/opt-pead.md`); v3 engine header in `desk3/aster_b2.py` describes the port as a faithful port of the archive r19_options PEAD evaluate paths and books in options_rules.json.

## What this sleeve is

This sleeve trades post-earnings drift in equity options after a weak earnings reaction, buying a put structure three sessions after the event. This specific variant is `aster_pead_vertical_b` (book `OPT_PEAD_VERTICAL_B`), a vertical put with risk fraction 0.005. It runs in the regular trading hours session on a 300 second cadence with a $10,000 slice.

## Full algorithm

Sleeve SPECS entry in `desk3/aster_b2.py` (exact values for this sleeve): `book="OPT_PEAD_VERTICAL_B", family="pead", structure="vertical", risk=0.005, dte=(21, 35), delta=(0.5, 0.65), hold=10, max_debit_width=0.45, max_premium_spot=0.02, exit_rule="fixed"`. Fee assumption in the engine: `FEE_PER_CONTRACT = 0.65` dollars per contract per leg, `SLICE = 10000.0`.

Evaluation order in `desk3/aster_b2.py::evaluate` (called via the adapter):

1. Exits first (see Exit rules). If any exit intent is produced, return only exits.
2. If any open position carries option legs, return no entry (one package per book, source rule).
3. Entry window: the timestamp in `ctx.now` / `view.now` must satisfy 09:35 <= time < 09:40 ET (`_in_window`). Enhancement ENH-B5-PEAD-CATCHUP-20261024 (default ON, switch `extra["enh_<sleeve>"]` or `extra["aster_b2_enh"]` `{"pead_catchup": bool}`): on the entry session only, a qualified event may still enter the same session in 09:40 <= time < 15:55; all other gates are unchanged. With the switch OFF, the window-only rule is restored exactly.
4. PEAD event loop: iterate `earnings_events` sorted by `(entry_session, symbol)`. Consider only events whose `entry_session` equals the current session date (`_sess`, from `ctx.session` or `view.now`). That session is event day + 3 sessions in the producer-built event (existing card and engine header).
5. Threshold: use the event's `threshold` if present; otherwise compute the 20th percentile (`_quantile(..., 0.2)`) of `prior_surprises` only if at least 200 prior surprises are present. Skip the event if no threshold can be formed.
6. Qualification: `surprise <= threshold` AND `spot_at_signal >= 5` AND `mean20_dollar_volume >= 1000000`. Surprise is defined in the existing card as the stock return minus SPY return from the session before to the session after the event.
7. On the first qualifying event, call `_entry` with right = `put` and spot = `spot_at_signal`, and return that single entry intent if `_entry` produces one.

Contract selection in `_entry` / `_select` (this sleeve's SPECS values applied):

- Candidates: option contracts with `underlying == event symbol`, `right == "put"`, DTE in 21 to 35 days inclusive, and absolute delta in 0.50 to 0.65 inclusive.
- Long leg: the candidate minimising `(expiry, | |delta| - 0.575 |, |strike - spot|, symbol)`, where 0.575 is the midpoint of the 0.50 to 0.65 delta band. Ratio +1.
- Structure is `vertical` (long put plus short wing put). Wing selection: same underlying, right and expiry as the long leg; strike beyond the long strike in the put direction (strike < long strike) and not equal to it; the wing minimising `(|strike - spot * 0.95|, symbol)`. Ratio -1. If no wing exists, no entry.
- Debit check for a vertical: `debit_ps = long ask - short bid`. Reject if `debit_ps <= 0`, if width `|long strike - wing strike| <= 0`, or if `debit_ps / width > MAX_DEBIT_WIDTH` for this sleeve (see below).

Sizing in `_entry`:

- Per-contract cash debit `per = debit_ps * 100 + 0.65 * number_of_legs`.
- Risk budget = `risk * SLICE` = 0.005 * 10000 = $50. Quantity `qty = floor(risk_budget / per)`, then capped by the minimum displayed size across the legs (`ask_size` for a long-ratio leg, `bid_size` for a short-ratio leg). Reject if `qty < 1`. max_debit_width applies to the vertical check; max_premium_spot is recorded in SPECS but the code applies it only to long structures.
- Entry intent: `kind="entry"`, side buy, `position_intent="buy_to_open"` for the long leg (and `sell_to_open` for a vertical wing), `time_in_force="day"`, `entry_spot` = spot, `exit_rule="fixed"`, `hold_sessions=10`. Price: market by default, changed by the engine enhancement below.

Mid-price limit enhancement (ENH-ASTERB2-MIDLIMIT-20261024, in `desk3/aster_b2.py`, default ON; switch `extra["enh_<sleeve>"]` or `extra["aster_b2_enh"]` `{"mid_limit": bool}`): if every leg has bid > 0 and ask >= bid, the entry (and a corresponding exit) becomes a limit order at the package mid (long mids added, short mids subtracted), rounded to 2 decimals, when that mid is > 0, with a paired shadow record of the market-cross price. With the switch OFF, the original market order is restored.

Exit rules (evaluated first, in this order, for each open position that carries option legs; positions without legs are skipped in this engine):

1. Pre-expiry guard: if `(expiry date - current session date).days <= 1`, exit with reason `pre_expiry_obligation_exit`.
2. Planned session exit: otherwise, if sessions held >= 10 (`hold`), exit with reason `planned_session_exit`. Sessions held is `sessions_held` if supplied, otherwise the count of bars for the leg underlying with a date after the position entry date.
3. No touch exit for this sleeve: `exit_rule="fixed"`, so the 2 percent touch rule in the engine does not apply.
- Exit intent: side sell, `position_intent="sell_to_close"` for a long-ratio leg and `buy_to_close` for a short-ratio leg, quantity = absolute position quantity, `time_in_force="day"`, subject to the mid-limit enhancement above.

## Files in this repo

- Sleeve adapter (repo copies of the desk adapter): `adapters3/aster_pead_vertical_b.py`, `sleeves/aster_pead_vertical_b.py`, and `integration/aster_pead_vertical_b_adapter.py`. The desk original is `adapters3/aster_pead_vertical_b.py` in the desk tree, a thin wrapper that sets `SLEEVE_ID="aster_pead_vertical_b"` and delegates to `desk3.aster_b2.evaluate`.
- Shared engine that runs the logic: `desk3/aster_b2.py` (contains the SPECS row for this sleeve, `_select`, `_entry`, and `evaluate`).
- Existing family card: `strategies/ausar/opt-pead.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_pead_vertical_b`).

## Configuration

- Sleeve id: `aster_pead_vertical_b`; module: `adapters3.aster_pead_vertical_b` (roster row in desk `config/sleeves.json`).
- Universe: names with published earnings (existing card); in code, whatever symbols arrive in `earnings_events` and pass the qualification gates. Asset: equity options, puts.
- Timeframe: 1d (existing card; daily bars and the producer-built earnings event). Session: `rth`. Cadence: 300 seconds (`cadence_s=300`).
- Sizing / slice: $10,000 capital and $10,000 cash (`slice.capital_usd=10000.0, cash_usd=10000.0`); `bp_buffer_frac=0.02`; risk fraction 0.005 of the slice as above.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false (`parked=false`).

## Data inputs

Inputs declared in the roster row: `bars`, `options`, `positions`, `earnings_events`. Adapter inputs are `INPUTS_COMMON + ("earnings_events",)` where `INPUTS_COMMON = ("bars", "options", "positions")`.

Producers declared in `desk3/aster_b2.py` (`PRODUCERS_PEAD`): `bars` (outputs `bars`, freshness SLA 900 s), `options_chain` (outputs `options`, 900 s), `broker_readback` (outputs `positions`, 900 s), and `earnings_events` (outputs `earnings_events`, 86400 s). The existing card lists the underlying data as an earnings calendar with first-publication times and SIP daily bars of the stock and SPY. The engine header notes that inputs not produced leave the sleeve unfed in the registry and are never fake-fed.

## Install and run

1. Place `desk3/aster_b2.py` in a fresh desk under `desk3/`, and place the adapter file as `adapters3/aster_pead_vertical_b.py` (copy any of the repo copies listed above; they are the same wrapper).
2. Register the roster row for `aster_pead_vertical_b` from `config/sleeves.json` (module `adapters3.aster_pead_vertical_b`, cadence 300, session rth, $10,000 slice, inputs bars/options/positions/earnings_events, parked false) in the desk config.
3. Wire the four producers above so the evaluation view contains `bars`, `options` (contract rows with underlying, right, expiry, delta, strike, bid, ask and displayed sizes, or the per-underlying dict shape normalised by `_contracts`), `positions`, and `earnings_events` (each event with entry_session, surprise or prior_surprises, spot_at_signal, mean20_dollar_volume, symbol and event_id), plus `now` / session context.
4. First evaluation: call `adapters3.aster_pead_vertical_b.evaluate(view, ctx)`; it delegates to `desk3.aster_b2.evaluate("aster_pead_vertical_b", view, ctx)`. Run it on the 300 second cadence in RTH; the first qualifying check is an exit scan, then the 09:35 to 09:40 ET entry window (with the same-session catchup described above).

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist, each check derived from the algorithm above:

- Check that a position with legs expiring within 1 day exits with `pre_expiry_obligation_exit` before any entry is considered, and a position held 10 sessions exits with `planned_session_exit`.
- Check that no entry occurs outside 09:35 to 09:40 ET unless the PEAD catchup switch is ON and the time is 09:40 to 15:55 on the entry session; with catchup OFF, no entry occurs after 09:40.
- Check that an event with fewer than 200 prior surprises and no supplied threshold is skipped, an event with surprise above the 20th percentile threshold is skipped, and events with spot below $5 or mean 20 day dollar volume below $1,000,000 are skipped.
- Check that contract selection respects DTE 21 to 35 and absolute delta 0.50 to 0.65, and for a vertical that the wing is the strike nearest spot times 0.95 beyond the long put.
- Check sizing: quantity equals floor(50 / (debit times 100 plus $0.65 per leg)), capped by displayed size, and the debit gates (max_debit_width applies to the vertical check; max_premium_spot is recorded in SPECS but the code applies it only to long structures.) reject an over-limit package.
- Check that a second open package blocks any new entry (one package per book).
