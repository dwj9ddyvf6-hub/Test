# ASTER_ETF_QLD_BUY_HOLD RECREATE

Provenance: Ausar R17/R18 ETF research, frozen as the R19 ETF books (Source row in strategies/ausar/r19-etf.md, the existing repo doc for this sleeve).

## What this sleeve is

This is a monthly Aster R19 ETF sleeve in the v3 desk. It is a thin adapter wrapper: the sleeve module sets SLEEVE_ID to "aster_etf_qld_buy_hold" and delegates evaluate(view, ctx) to desk3/aster_etf.py. Its own policy is QLD_ONLY_BUY_HOLD with gross target 1.0.

## Full algorithm

Config params are empty for this sleeve in config/sleeves.json; its policy, frequency, gross and weights come only from desk3/aster_etf.py SPECS.

Sleeve-specific rules: Frequency guard: BUY_HOLD. If any position exists, emit nothing forever (no exit and no rebalance by design). Only a flat book proceeds. Weights: QLD 100%. Target is therefore the initial allocation only.

Equity basis: see step 2 of the common evaluation order below; gross is applied to that equity, not to cash plus held value separately.

Evaluation order in desk3/aster_etf.py evaluate():
1. Time gate: now is read from view['now'], ctx['now'], or ctx['session']. Aware timestamps are converted to America/New_York (ENH-ETWIN, default ON via extra['aster_etf_enh']['et_window']); naive timestamps are read as ET. Emit nothing outside 09:35-09:40 ET, except that a MONTHLY sleeve with a due rebalance may use the same-session catch-up window 09:40-15:55 ET (ENH-B5-CATCHUP, default ON via extra['aster_etf_enh']['catchup']). If now cannot be parsed, emit nothing.
2. Equity basis: equity = extra['account_value'] or extra['net_value'] or slice capital_usd or 10000.0. Note the config slice is 10000.0 capital and 10000.0 cash.
3. Positions: view['positions'] with non-zero qty, keyed by symbol.
4. Frequency guard for this sleeve (see sleeve-specific rules below).
5. Target weights for this sleeve (see sleeve-specific rules below). For a target leg, price is the last close of its bars ('<symbol>|1Day', '<symbol>|1D', or bare symbol key). If any target price is <= 0, refuse the whole rebalance and emit nothing.
6. Target shares: int(gross x equity x weight / price), floored to whole shares.
7. Sells first: for each held symbol in sorted order, if held > target (target 0 for non-target symbols), emit a sell intent for held minus target; kind is exit if target is 0 else rebalance, side sell, position_intent sell_to_close, order_type market, time_in_force day, price_hint = last close or position average price.
8. Buys: for each target symbol in sorted order, if target > held, emit a buy intent for target minus held (kind entry, side buy, position_intent buy_to_open, order_type market, time_in_force day, price_hint = last close). If the catch-up path served, each intent reason is suffixed with the catch-up experiment id and an enhance_exp record is attached.
No price stop and no price target exist in this engine. Source-book cost_bps 15 is accounting in the source book, not an order field (engine docstring).

Exit rules are the sell and rebalance rules in the steps above. There is no separate stop, target, trailing, or time-based exit in the engine, except the BUY_HOLD / monthly guards stated for this sleeve where applicable.

## Files in this repo

- Sleeve module: sleeves/aster_etf_qld_buy_hold.py (also adapters3/aster_etf_qld_buy_hold.py in the desk layout; the repo mirrors the adapter as integration/aster_etf_qld_buy_hold_adapter.py)
- Adapter: integration/aster_etf_qld_buy_hold_adapter.py (desk path adapters3/aster_etf_qld_buy_hold.py)
- Engine: desk3/aster_etf.py
- Config: config/sleeves.json (also engines/config/sleeves.json) containing the row for aster_etf_qld_buy_hold
- Existing family doc: strategies/ausar/r19-etf.md
- Existing per-sleeve algorithm doc: docs/ASTER_ETF_QLD_BUY_HOLD-ALGORITHM.md (where present in the tree)

## Configuration

- Universe: QLD only as a target; the b10 engine basket constant is still the 14-symbol list, but this sleeve's fixed weights use only QLD
- Timeframe: 1d bars (daily), monthly selection / rebalance for this sleeve (frequency BUY_HOLD)
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0, gross_target 1.0, bp_buffer_frac 0.02
- Cadence: cadence_s 300, session rth
- Parked: false (parked false in config/sleeves.json)
- flat_by_close: false, flatten_time_et: null
- Module: adapters3.aster_etf_qld_buy_hold
- Inputs (config row): bars, positions, quotes

## Data inputs

Bars: daily histories keyed '<symbol>|1Day', '<symbol>|1D', or bare symbol; the engine uses the last close and, for LEADER1, close[-127]. Positions: held qty, symbol, average price, and entry_date or opened_at for the monthly guard. Quotes are a declared input (freshness 60 s) though target pricing in evaluate() uses bar closes.
Producers: bars producer (outputs bars, freshness_sla_s 900), broker_readback producer (outputs positions, freshness_sla_s 900), and quotes producer (outputs quotes, freshness_sla_s 60), as declared in desk3/aster_etf.py PRODUCERS. The evaluate() logic itself reads bars and positions (and ctx/view extras); quotes are a declared input of the sleeve.
Freshness is as stated in the producer declarations above. Absent or stale bars produce no intents in the engine (empty bars map or missing target price returns an empty list).

## Install and run

1. Place the engine file at desk3/aster_etf.py and the sleeve wrapper at sleeves/aster_etf_qld_buy_hold.py and adapters3/aster_etf_qld_buy_hold.py (repo adapter copy at integration/aster_etf_qld_buy_hold_adapter.py), preserving the delegation: the wrapper imports evaluate, and for b9 sleeves inputs_for and PRODUCERS, from the engine and calls it with SLEEVE_ID "aster_etf_qld_buy_hold".
2. Add or verify the config row in config/sleeves.json exactly as in the Configuration section (id, module adapters3.aster_etf_qld_buy_hold, inputs, slice, cadence_s 300, session rth, parked false, and params where the desk row carries them).
3. Wire the producers named in Data inputs so view contains bars, positions, and quotes as a declared input at evaluation time.
4. Register the sleeve with the desk cycle so evaluate(view, ctx) is called on the 300 s cadence in the rth session; the engine itself enforces the 09:35-09:40 ET window (and, for b10 MONTHLY sleeves, the same-session catch-up).
5. First evaluation: run one evaluation on a flat book inside the window with at least 252 daily bars per eligible symbol and confirm the emitted intents match the Verification checks before enabling live dispatch.

## Verification

No per-sleeve test file for this v3 sleeve is present in the repo tree (audit record: no tests/test_aster_* for these sleeves). Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Window check: an evaluation at 09:36 ET inside the window can emit; an evaluation at 09:41 ET emits nothing (for a b10 MONTHLY sleeve, a due rebalance may instead emit in the 09:40-15:55 ET catch-up with the catch-up marker).
- Eligibility check: a symbol with 251 bars is never scored or selected; a symbol with 252 bars and score log(close[-1]/close[-127]) is.
- Selection check: with fixture closes giving a known highest 126-session log return, the selected symbol, weights, and (for interval sleeves) robust / incumbent / QQQ fallback match the sleeve-specific rules above exactly.
- Sizing check: desired shares equal floor(weight x 1.0 x NAV-or-equity / price) on the NAV / equity basis stated above, whole shares only.
- Sell-first check: a holding above target produces only sell intents on that evaluation (b9) or sells before buys in the returned list (b10); a holding at target produces no intent for that symbol.
- Monthly guard check: holdings already stamped with the current signal month (b9) or current entry month (b10) produce no rebalance.
- Missing-data check: empty bars, missing bars_secondary for an interval sleeve, or a non-positive target price produces an empty intent list, never a guessed trade.
