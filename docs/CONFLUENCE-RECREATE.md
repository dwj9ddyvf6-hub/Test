# confluence: Recreation package

Provenance: Source row in strategies/femto/femto-confluence.md in this repo: The old Alpaca swing desk, via Femto-lean (family Femto-lean, asset US equities, timeframe 1w, universe the weekly M2 qualifier list, style weekly signal, confluence).

## What this sleeve is
This sleeve is the confluence twin of the beaten-down machinery: each week it buys the M2 qualifiers on which at least 2 of the 9 frozen HOLD9 confluence rules fire, ranked by rule count, and holds 91 days. It shares the frozen HOLD9 set, the Decision #92 new-buy gates and the exit-due law with beatendown; only the selection law differs. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/confluence.py signal(bars, slice_state, context), with entry filtering through desk3/enhance14.py in the adapter path recorded in the audit chain.

## Full algorithm
Frozen constants (sleeves/confluence.py): SELECT_MIN_COUNT = 2, CUT_LAM = 0.17647058823529413, MAX_POSITIONS = 10, HOLD_DAYS = 91, SLEEVE_CAP = 0.30, COST_BPS_SIDE = 0.00255 (25.5 bps per side). CONFIG: cadence_s 300, universe (), risk_pct None. HOLD9 is the frozen 9-rule set R1 to R9 scored by score_rules over each qualifier's feature dict; HOLD9_NAMES = R1..R9.

Selection and entries, in code order:
1. Population: context.extra qualifiers rows {symbol, close, feat} from the weekly M2 qualifier file (written after Friday's close). Unlike beatendown there is NO beaten-down price cut in this sleeve's selection law.
2. Selection count: effective_count counts the fired rules, with the enhancement applied (ENH-CONFLUENCE-20261024, on by default; switch extra["confluence_improve"] {"avwap_pair_one": bool}): when both R5 and R6 (the anchored-VWAP pair) fire they contribute at most 1 to the count (both names still appear in intent reasons); OFF restores the raw count exactly. Qualifiers with an effective count of at least SELECT_MIN_COUNT = 2 are selected, ranked by count, most first. Paired records go to extra["confluence_exp_journal"]["records"] when served.
3. New-buy gates (new_buy_gates, shared Decision #92 law): entries wait on the last 5 sessions of the year, on FOMC days and the session before (FOMC_2026 table in the module, overridable via extra fomc_dates), and on unknown or stale VIX (extra vix). A slot sold that morning can be refilled (per the card).
4. Timing and sizing: buys are Monday entries from 10:00 ET at a fresh mid; the budget is SLEEVE_CAP = 30 percent of equity less held and working notional, split over the week's selected names; whole shares at mid + 25.5 bps, at least 1 share when the split affords it; at most MAX_POSITIONS = 10 positions.

Exits: exit_due is the shared law: a position is due when its exit_due_date (entry plus HOLD_DAYS = 91 days, 13 weeks) is reached, and a position with a missing exit_due_date is due at once. Due positions are sold in the Monday fill at a fresh mid. There is no price stop in this module.

Position management: at most 10 positions, sleeve notional capped at 30 percent of equity including working orders, no pyramiding rule beyond the weekly selection above.

## Files in this repo
- Sleeve module (desk sleeves/confluence.py): `sleeves/confluence.py`.
- v3 adapter (desk adapters3/confluence.py): `adapters3/confluence.py`; also present as `integration/confluence_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py; named in the audit record as a shared dependency).
- Shared entry filter in the adapter delegation path: `engines/desk3/enhance14.py` (desk source desk3/enhance14.py, vendored in this repo per engines_map.json).
- Twin machinery source: `sleeves/beatendown.py` (the sibling sleeve sharing the HOLD9 set, gates and exit law).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/femto/femto-confluence.md`.

## Configuration
- Universe: the weekly M2 qualifier list (no fixed symbol list in CONFIG; universe ()). Asset: US equities. Timeframe: 1w signal; Monday entries and exits.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the module's executed law is the 30 percent sleeve cap over account equity described above.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions.

## Data inputs
- qualifiers: context.extra["qualifiers"] rows with symbol, close and the feature dict the HOLD9 rules score; producer: the weekly M2 qualifier file, written after Friday's close.
- vix: context.extra["vix"] (close, prev, asof_iso, source) or None; unknown or stale VIX waits entries.
- fomc_dates: optional context.extra override of the module's FOMC_2026 table.
- sleeve_state: context.extra["sleeve_state"] {symbol: {"position": {entry_px, entry_date, exit_due_date, qty}}}; bars supply exit price hints only.

## Install and run
1. Place the sleeve module at sleeves/confluence.py and the adapter at adapters3/confluence.py (repo copies at the same paths). The adapter path also places the shared filter at desk3/enhance14.py (repo copy at engines/desk3/enhance14.py).
2. Register the roster row for `confluence` exactly as in the Configuration section in config/sleeves.json (module adapters3.confluence).
3. Wire the producers so every snapshot carries: daily bars (exit hints), this sleeve's positions and sleeve_state, and extra qualifiers, vix, and fomc_dates when overriding.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch1_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check selection: a qualifier with an effective count of 1 is not selected and one with 2 or more is, ranked by count; a qualifier firing only R5 and R6 counts once with the enhancement on and twice with it off.
- Check that no beaten-down cut applies: a qualifier above 0.80 x its 52-week high with 2 or more effective rules is still selected by this sleeve.
- Check the gates and sizing: the year-end, FOMC and VIX gates each produce no buys; held plus working notional never exceeds 30 percent of equity and the 11th position is refused.
- Check the exit: a position is sold on the Monday fill once 91 days have passed, and a missing exit_due_date makes it due immediately.
