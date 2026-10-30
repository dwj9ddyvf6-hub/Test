# rule_1d_cyan_smallcap: Recreation package

Provenance: Source row in strategies/femto/femto-rule-1d-cyan-smallcap.md in this repo: The old Alpaca swing desk's Daily Cyan GBM and GBM-rule research on its Tensor engine replica, via Femto-lean.

## What this sleeve is
This is a small-cap rule sleeve: an external GBM rule scorer's 1-day cyan fire, filtered by the frozen rule conditions, a $5 to $10 price band, a $1M 20-day dollar-volume floor and an EDGAR market-cap ceiling, is bought at 1 percent of equity notional and held 21 sessions. The fire detection itself is a core Data product; this sleeve holds only the selection law. Sources: sleeves/rule_1d_cyan_smallcap.py and desk_sleeves/rule_1d_cyan_smallcap.py on the desk.

## Full algorithm
Constants (sleeves/rule_1d_cyan_smallcap.py): HOLD_BARS 21, LANE 1D, SIGNAL_KIND cyan, MIN_DV20 1,000,000, MCAP_THRESHOLD 9.377766990661621 (log10 market cap), NOTIONAL_FRACTION 0.01, MAX_POSITIONS 10, DISASTER_STOP 0.25, rule id V4-1D-CYAN-RAW-H21-COV-bb707043 (tier A). CONFIG: cadence_s 300, universe (), risk_pct None. Frozen CONDITIONS: feature pxn == 2, AND feature di between -10.590971183776855 and 12.556758308410648 inclusive.
Evaluation order in signal():
1. Exits first, for every booked position: when sessions since entry (delivered bar dates strictly after the entry date) reach HOLD_BARS - 1 = 20, exit the full qty, staged one session early so the core's next-session fill lands on the 21st close. There is no price stop in the source law.
2. Entries need equity above 0 and a non-empty rule_fires map. Symbols are considered in sorted order; held symbols and a book already at 10 positions are skipped.
3. Fire match: a fire for the symbol whose date equals the last bar's date and whose features pass every CONDITIONS entry (rule_pass).
4. Price band: the last close must satisfy 5.00 <= px < 10.00.
5. Liquidity: dv20 (the mean of close x volume over the last 20 sessions; 0.0 with fewer than 20 bars) must be at least 1,000,000.
6. Market cap: log_mcap for the symbol must be present, finite and at most 9.377766990661621; missing or non-numeric market cap fails closed.
7. Sizing: qty = floor(equity x 0.01 / px); qty below 1 skips, with no forced floor. Entry price is the next session close (core executes).
8. Enhancement (switch context.extra["rule_1d_cyan_smallcap_enhance"]["disaster_stop"], default ON): the entry intent also carries a disaster stop at 0.75 x entry (ExitRule stop plus stop=) alongside the time_bars 21 ExitRule; with the switch OFF the intent carries the time exit only. Paired control/treatment records ride the sleeve's enhance journal.
The v3 adapter universe is the 41-name basket (AEHR, NBIS, SKYQ, SHAZ, LITE, SOXL, WYFI, CRML, AAOI, WDC, VELO, ANF, SATL, ASPI, IREN, AG, AXTI, LASR, ARQQ, OUST, ALAB, CRDO, FCEL, HIVE, POET, SNDK, TEM, CORZ, HUT, TSEM, ARM, KEEL, FFIV, MU, CLS, TE, TTMI, CVNA, VRT, OKLO, USAR) plus the bridge CANDIDATES, roster additions and held symbols, with 21 1-day warmup bars requested; entries then pass desk3/enhance18.filter_entries.

## Files in this repo
- Strategy module (desk sleeves/rule_1d_cyan_smallcap.py): `sleeves/rule_1d_cyan_smallcap.py` in this repo (the strategy logic; CONFIG sleeve_id=rule_1d_cyan_smallcap).
- v3 adapter (desk desk_sleeves/rule_1d_cyan_smallcap.py): `integration/rule_1d_cyan_smallcap_adapter.py` in this repo; the adapter re-shapes the snapshot via the port bridge and applies the enhance18 entry filter to entries.
- Shared engine files (engines_map.json): `engines/desk3/enhance18.py` (desk desk3/enhance18.py, vendored; filter_entries) and `engines/desk3/bridge.py` (desk desk3/bridge.py, vendored; the port bridge).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=rule_1d_cyan_smallcap); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module rule_1d_cyan_smallcap; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars_1day', 'positions', 'rule_fires', 'log_mcap']; parked false. Source: muse-desk-v3/config/sleeves.json row id=rule_1d_cyan_smallcap (repo copy: engines/config/sleeves.json).

## Data inputs
Rule fires {SYM: [{date, features}]} via context.extra["rule_fires"] (the external GBM rule scorer's cyan fires, a core Data product; the sleeve never shells out to the scorer); log_mcap {SYM: float|None} via context.extra (the EDGAR public-float computation, also a Data product); daily bars for the price, dv20 and session counting; sleeve_state {SYM: {position: {entry_px, entry_date, qty}}}.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `rule_1d_cyan_smallcap` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the rule: a fire with pxn of 1 or 3, or di outside the stated inclusive band, does not pass; pxn 2 with di at either band edge passes.
- Check the filters: a close of $4.99 and of $10.00 each fail the band; dv20 below $1,000,000 fails; a missing log_mcap fails closed; log_mcap above 9.377766990661621 fails.
- Check the fire date: a passing fire dated before the last bar's date produces no entry.
- Check sizing and caps: qty equals floor(equity x 0.01 / px), a sub-1 qty skips, and the 11th position is refused.
- Check the exit staging: at 20 sessions since entry the exit is emitted; at 19 it is not.
- Check the enhancement: with the switch ON the entry carries a stop at 0.75 x entry; with it OFF it carries only the time_bars 21 rule.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
