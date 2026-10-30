# s_cl_vmr_qqq: Recreation package

Provenance: Source row in strategies/lazarus/cl-vmr-qqq.md in this repo: Family Lazarus; Source ChartsLector (his VIX Mood Ring), via Lazarus; Asset US ETF; Timeframe 1d; Universe QQQ; Style Fear rebound; Status waiting. The same doc notes the v3 module uses VIX at or below 35 alone, not the composite, and the per-sleeve algorithm doc docs/S_CL_VMR_QQQ-ALGORITHM.md states it was derived from the sleeve code on 2026-10-29 (no author spec on file).

## What this sleeve is
This sleeve buys QQQ for a 5-session fear rebound whenever the VIX reading is at or below 35, in a single $1,000 slot. It is v3-native in laz_sleeves/s_cl_vmr_qqq.py and reads the VIX scalar directly from the snapshot, not the Mood Ring composite described in the plan doc. Sources: laz_sleeves/s_cl_vmr_qqq.py and laz_sleeves/_common.py on the desk.

## Full algorithm
Evaluation order in laz_sleeves/s_cl_vmr_qqq.py evaluate(view, ctx) (SLOT_USD 1000.0, HOLD_SESSIONS 5, VIX_MAX 35.0, 1 slot):

1. Session: the session date is read from view now; no parseable session date emits nothing.
2. Held position first: when sessions held, counted as QQQ daily bars dated strictly after the position's opened_at, reach 5, exit the full held qty at the last QQQ close, reason cl_vmr_time5. No stop is implemented.
3. Entry gate: any held position, or missing QQQ daily bars, returns with only any exits.
4. VIX gate: the VIX reading is view vix as a scalar float; a missing reading, a non-scalar payload (which fails closed with no reading, per the CURE2-2 guard in the code) or a reading above 35.0 emits no entry.
5. Stale-bar gate (ENH19, on by default; extra s_cl_vmr_qqq_enh19 stale_gate): refuse the entry when the last QQQ bar is more than 4 calendar days before the session (_bar_stale); exits are never gated, and a refused entry is journalled as refuse_stale_bar against the shadow-faithful enter.
6. Sizing and intent: qty = int(1000.0 // last QQQ close) (_qty_for); qty at or below 0 emits nothing. The entry intent is a market, day, buy priced (hint) at the last close, reason cl_vmr_vix_le35.

## Files in this repo
- Sleeve module: laz_sleeves/s_cl_vmr_qqq.py (the strategy logic; v3-native, evaluate(view, ctx)); also copied in this repo at sleeves/lazarus/s_cl_vmr_qqq.py and integration/s_cl_vmr_qqq_adapter.py.
- Shared engine file: laz_sleeves/_common.py (desk laz_sleeves/_common.py; the helpers _bars, _positions, _session, _intent, _qty_for and the ENH19 helpers this module imports). NOTE: engines_map.json records engines/laz_sleeves/_common.py as gate_blocked, so this shared file is not present in this repo; a recreation must supply the same helper definitions from a fresh desk.
- Existing strategy doc: strategies/lazarus/cl-vmr-qqq.md.
- Config: engines/config/sleeves.json (row id=s_cl_vmr_qqq).
- Per-sleeve algorithm doc: docs/S_CL_VMR_QQQ-ALGORITHM.md.

## Configuration
Module laz_sleeves.s_cl_vmr_qqq; cadence_s 86400; session rth; slice capital_usd 1000.0, cash_usd 1000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars_1day, positions, vix]; parked false. Source: muse-desk-v3/config/sleeves.json row id=s_cl_vmr_qqq. The module's own constants are 1 slot x $1,000, matching the $1,000 slice.

## Data inputs
QQQ daily bars in view bars under key QQQ|1Day ([{t,o,h,l,c,v} ascending]); the VIX scalar in view vix (the ^VIX close from the sanctioned Yahoo price-only route named in the _common header); positions filtered to this sleeve; the session date from view now. No data is fetched during evaluation.

## Install and run
1. Place the sleeve module at laz_sleeves/s_cl_vmr_qqq.py (also copied in this repo at laz_sleeves/s_cl_vmr_qqq.py, sleeves/lazarus/s_cl_vmr_qqq.py and integration/s_cl_vmr_qqq_adapter.py) and supply the shared helper module laz_sleeves/_common.py: engines_map.json records engines/laz_sleeves/_common.py as gate_blocked, so that one shared file is NOT in this repo and a recreation must supply the same helper definitions (the functions named in Files in this repo) from a fresh desk.
2. Register the config row for `s_cl_vmr_qqq` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides (params {}).
3. Wire the producers named in Data inputs so bars, positions and the sleeve's third input arrive in the snapshot view in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the module's evaluate(view, ctx), which reads the session date from view now and emits v3 intent dicts directly (no separate adapter delegation).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A (entry): no held position, fresh QQQ bars and a scalar VIX at or below 35.0 produce one market buy of int(1000.0 // last QQQ close) shares with reason cl_vmr_vix_le35. Fixture B: a VIX above 35.0, a non-scalar VIX payload, or a last QQQ bar more than 4 calendar days before the session (enhancement on) each produce no entry. Fixture C (exit): a position with 5 bars after its open date produces one full exit with reason cl_vmr_time5.

- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated partial quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
