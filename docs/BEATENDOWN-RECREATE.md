# beatendown: Recreation package

Provenance: Source row in strategies/femto/femto-beatendown.md in this repo: The old Alpaca swing desk, via Femto-lean (family Femto-lean, asset US equities, timeframe 1w, universe the weekly M2 qualifier list, style weekly signal, value).

## What this sleeve is
This sleeve buys the weekly M2 qualifiers that closed at least 20 percent under their trailing 52-week high, ranks them by how many of the 9 frozen HOLD9 confluence rules fire, buys on Monday and holds 91 days. The qualifier and feature pipeline arrives as a core Data product; the sleeve module itself holds the frozen selection, gate and exit law. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/beatendown.py signal(bars, slice_state, context), with entry filtering through desk3/enhance14.py in the adapter path recorded in the audit chain.

## Full algorithm
Frozen constants (sleeves/beatendown.py): BEAT_LO52_CUT = 0.80, CUT_LAM = 0.17647058823529413, MAX_POSITIONS = 10, HOLD_DAYS = 91, SLEEVE_CAP = 0.30, COST_BPS_SIDE = 0.00255 (25.5 bps per side). CONFIG: cadence_s 300, universe (), risk_pct None. HOLD9 is the frozen 9-rule set R1 to R9, each a 3-feature confluence scored by score_rules over the qualifier feature dict.

Selection and entries, in code order:
1. Population: context.extra qualifiers rows {symbol, close, wcloses, feat} from the weekly M2 qualifier file (written after Friday's close). is_beaten_down keeps only rows whose signal-week close is at most 0.80 x the trailing 52-week high computed from weekly closes. There is NO rule-count minimum in the frozen law: the HOLD9 count is the ranker, highest count first.
2. Enhancement (ENH-BEATENDOWN-20261024, on by default; switch extra["beatendown_improve"] {"hold9_min_one": bool}): a candidate with HOLD9 count 0 is skipped; OFF restores the frozen rule exactly, and control decisions are shadow-scored as paired records to extra["beatendown_exp_journal"]["records"] when served.
3. New-buy gates (new_buy_gates, Decision #92 law ported verbatim in the module): entries wait on the last 5 sessions of the year, on FOMC days and the session before (FOMC_2026 table in the module, overridable via extra fomc_dates), and on unknown or stale VIX (extra vix is (close, prev, asof_iso, source) or None). The desk fear composite must be at least 55; it fails open per the card (the core supplies the composite; the module header states the risk_gate desk-halt leg is core Risk's).
4. Timing and price: buys are Monday entries from 10:20 ET at a fresh mid (the fill law in the module's intent construction); the cost model adds 25.5 bps per side (mid + 25.5 bps for sizing).
5. Sizing: the budget is SLEEVE_CAP = 30 percent of equity less held and working notional, split over the week's selected names; whole shares, at least 1 share when the split affords it; at most MAX_POSITIONS = 10 positions.

Exits: exit_due is ported verbatim: a position is due when its exit_due_date (entry plus HOLD_DAYS = 91 days, 13 weeks) is reached, and a position with a MISSING exit_due_date is due at once (the 2026-10-12 fix: never held forever). Due positions are sold in the Monday fill at a fresh mid. There is no price stop in this module.

Position management: at most 10 positions, sleeve notional capped at 30 percent of equity including working orders, no pyramiding rule beyond the weekly selection above.

## Files in this repo
- Sleeve module (desk sleeves/beatendown.py): `sleeves/beatendown.py`.
- v3 adapter (desk adapters3/beatendown.py): `adapters3/beatendown.py`; also present as `integration/beatendown_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py; named in the audit record as a shared dependency).
- Shared entry filter in the adapter delegation path: `engines/desk3/enhance14.py` (desk source desk3/enhance14.py, vendored in this repo per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/femto/femto-beatendown.md`.

## Configuration
- Universe: the weekly M2 qualifier list (no fixed symbol list in CONFIG; universe ()). Asset: US equities. Timeframe: 1w signal; Monday entries and exits.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the module's executed law is the 30 percent sleeve cap over account equity described above (the card's per-sleeve $100,000 book note is the old-desk basis; the v3 roster slice governs registration).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions.

## Data inputs
- qualifiers: context.extra["qualifiers"] rows with symbol, close, weekly closes and the feature dict the HOLD9 rules score; producer: the weekly M2 qualifier file (the old desk's Tensor Anna weekly replica with its feature blocks), written after Friday's close.
- vix: context.extra["vix"] (close, prev, asof_iso, source) or None; unknown or stale VIX waits entries.
- fomc_dates: optional context.extra override of the module's FOMC_2026 table; the desk fear composite (at least 55 to buy) is supplied by core.
- sleeve_state: context.extra["sleeve_state"] {symbol: {"position": {entry_px, entry_date, exit_due_date, qty}}}; bars supply exit price hints only.

## Install and run
1. Place the sleeve module at sleeves/beatendown.py and the adapter at adapters3/beatendown.py (repo copies at the same paths). The adapter path also places the shared filter at desk3/enhance14.py (repo copy at engines/desk3/enhance14.py).
2. Register the roster row for `beatendown` exactly as in the Configuration section in config/sleeves.json (module adapters3.beatendown).
3. Wire the producers so every snapshot carries: daily bars (exit hints), this sleeve's positions and sleeve_state, and extra qualifiers, vix, fomc_dates when overriding, and the fear composite.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch1_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check selection: a qualifier closing above 0.80 x its 52-week high is excluded; qualifiers are ranked by HOLD9 count descending, and with the enhancement on a count-0 qualifier is skipped while with it off it ranks normally.
- Check the gates: the last 5 sessions of the year, an FOMC day or the session before it, missing or stale VIX, or a fear composite under 55 each produce no buys.
- Check sizing: total held plus working notional never exceeds 30 percent of equity, the budget splits over the selected names at mid + 25.5 bps in whole shares, and the 11th position is refused.
- Check the exit: a position is sold on the Monday fill once 91 days have passed, and a position whose exit_due_date is missing is due immediately.
