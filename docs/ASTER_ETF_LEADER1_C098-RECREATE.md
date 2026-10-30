# ASTER_ETF_LEADER1_C098 RECREATE

Provenance: Ausar R17/R18 ETF research, frozen as the R19 ETF books (Source row in strategies/ausar/r19-etf.md, the existing repo doc for this sleeve).

## What this sleeve is

This is a monthly Aster R19 ETF sleeve in the v3 desk. It is a thin adapter wrapper: the sleeve module sets SLEEVE_ID to "aster_etf_leader1_c098" and delegates evaluate(view, ctx) to desk3/aster_etf_b9.py. Its own policy is LEADER1 with gross target 0.98.

## Full algorithm

Engine SPECS source_id: R19_ETF_LEADER1_C098 (desk3/aster_etf_b9.py SPECS and config/sleeves.json params).

Sleeve-specific rules: LEADER1 selection: select the highest-scoring eligible symbol (126-session log return, at least 252 sessions, ties alphabetical). No symbol is excluded. Weights: 100% to the selected symbol.

NAV basis: ENH-NAVBASE does NOT apply to this sleeve (the engine explicitly keeps aster_etf_leader1_c098 on the legacy basis): NAV = slice cash (default 10000.0) plus held value at last close.

Evaluation order in desk3/aster_etf_b9.py evaluate():
1. Execution window: if a clock time is known, emit nothing outside 09:35-09:40 America/New_York. Aware timestamps are converted to ET, naive timestamps are read as ET, and a date-only or midnight stamp is ungated. If no time is supplied, the window check passes.
2. Build the primary bars map from view['bars'], keyed '<symbol>|1Day', '<symbol>|1D', or the bare symbol, for the universe. If the map is empty, emit nothing.
3. Score: for each symbol with at least 252 sessions and all closes in the last 252 sessions positive, score = log(close[-1] / close[-127]) (126-session log return). Symbols below 252 sessions are ineligible.
4. Selection for this sleeve's policy (see sleeve-specific rules below). Ties for non-interval policies break alphabetically (lowest symbol among highest scores).
5. Monthly guard: signal_month is the latest bar month (max last-bar date, first 7 characters). If positions exist and every held position carries signal_month equal to that month, emit nothing (this month's signal is already completed).
6. Incumbent (where needed): a position flagged incumbent or selected, otherwise the holding with the largest held value at last close (fallback average price).
7. Prices: last close for each held or target symbol, falling back to bars last close, then to the position average price. If any needed price is <= 0, emit nothing.
8. Desired shares: floor(weight x gross x NAV / price) for each symbol in held union target, whole shares, never capped inside the sleeve. The dispatcher buying-power check governs execution for gross above 1.0.
9. Sell-then-settle: if any holding is above its desired shares, emit ONLY sell intents on this evaluation (kind exit, side sell, qty held minus desired, order_type market, time_in_force day, position_intent sell_to_close), and return. Buys follow on a later evaluation.
10. Otherwise emit buy intents for desired minus held where positive (kind entry, side buy, order_type market, time_in_force day, position_intent buy_to_open, price_hint = last close). Intent id format: '<sleeve>-<signal_month>-<stamp last 4>-<n>-<symbol>-<side>'.
No price stop and no price target exist in this engine. The designed exit is the next monthly selection reducing or replacing a holding.

Exit rules are the sell and rebalance rules in the steps above. There is no separate stop, target, trailing, or time-based exit in the engine, except the BUY_HOLD / monthly guards stated for this sleeve where applicable.

## Files in this repo

- Sleeve module: sleeves/aster_etf_leader1_c098.py (also adapters3/aster_etf_leader1_c098.py in the desk layout; the repo mirrors the adapter as integration/aster_etf_leader1_c098_adapter.py)
- Adapter: integration/aster_etf_leader1_c098_adapter.py (desk path adapters3/aster_etf_leader1_c098.py)
- Engine: desk3/aster_etf_b9.py
- Config: config/sleeves.json (also engines/config/sleeves.json) containing the row for aster_etf_leader1_c098
- Existing family doc: strategies/ausar/r19-etf.md
- Existing per-sleeve algorithm doc: docs/ASTER_ETF_LEADER1_C098-ALGORITHM.md (where present in the tree)

## Configuration

- Universe: QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY
- Timeframe: 1d bars (daily), monthly selection / rebalance for this sleeve
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0, gross_target 0.98, bp_buffer_frac 0.02
- Cadence: cadence_s 300, session rth
- Parked: false (parked false in config/sleeves.json)
- flat_by_close: false, flatten_time_et: null
- Module: adapters3.aster_etf_leader1_c098
- Inputs (config row): bars, positions

## Data inputs

Primary bars: daily histories for the universe, keyed '<symbol>|1Day', '<symbol>|1D', or bare symbol; the engine uses closes (field c) and last-bar timestamps (field t). Positions: held qty, symbol, average price, and where supplied incumbent/selected flags and signal_month.
Producers: bars producer (outputs bars, freshness_sla_s 900) and broker_readback producer (outputs positions, freshness_sla_s 900), as declared in desk3/aster_etf_b9.py PRODUCERS.
Freshness is as stated in the producer declarations above. Absent or stale bars produce no intents in the engine (empty bars map or missing target price returns an empty list).

## Install and run

1. Place the engine file at desk3/aster_etf_b9.py and the sleeve wrapper at sleeves/aster_etf_leader1_c098.py and adapters3/aster_etf_leader1_c098.py (repo adapter copy at integration/aster_etf_leader1_c098_adapter.py), preserving the delegation: the wrapper imports evaluate, and for b9 sleeves inputs_for and PRODUCERS, from the engine and calls it with SLEEVE_ID "aster_etf_leader1_c098".
2. Add or verify the config row in config/sleeves.json exactly as in the Configuration section (id, module adapters3.aster_etf_leader1_c098, inputs, slice, cadence_s 300, session rth, parked false, and params where the desk row carries them).
3. Wire the producers named in Data inputs so view contains bars, positions at evaluation time.
4. Register the sleeve with the desk cycle so evaluate(view, ctx) is called on the 300 s cadence in the rth session; the engine itself enforces the 09:35-09:40 ET window (and, for b10 MONTHLY sleeves, the same-session catch-up).
5. First evaluation: run one evaluation on a flat book inside the window with at least 252 daily bars per eligible symbol and confirm the emitted intents match the Verification checks before enabling live dispatch.

## Verification

No per-sleeve test file for this v3 sleeve is present in the repo tree (audit record: no tests/test_aster_* for these sleeves). Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Window check: an evaluation at 09:36 ET inside the window can emit; an evaluation at 09:41 ET emits nothing (for a b10 MONTHLY sleeve, a due rebalance may instead emit in the 09:40-15:55 ET catch-up with the catch-up marker).
- Eligibility check: a symbol with 251 bars is never scored or selected; a symbol with 252 bars and score log(close[-1]/close[-127]) is.
- Selection check: with fixture closes giving a known highest 126-session log return, the selected symbol, weights, and (for interval sleeves) robust / incumbent / QQQ fallback match the sleeve-specific rules above exactly.
- Sizing check: desired shares equal floor(weight x 0.98 x NAV-or-equity / price) on the NAV / equity basis stated above, whole shares only.
- Sell-first check: a holding above target produces only sell intents on that evaluation (b9) or sells before buys in the returned list (b10); a holding at target produces no intent for that symbol.
- Monthly guard check: holdings already stamped with the current signal month (b9) or current entry month (b10) produce no rebalance.
- Missing-data check: empty bars, missing bars_secondary for an interval sleeve, or a non-positive target price produces an empty intent list, never a guessed trade.
