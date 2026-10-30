# s_cl_qm_small: Recreation package

Provenance: Source row in strategies/lazarus/cl-qm-small.md in this repo: Family Lazarus; Source ChartsLector (his Qullamaggie TradingView screen), via Lazarus; Asset US equities; Timeframe 1d; Universe Tracker universe, small band ($300M-$2B); Style Breakout; Status live. The same doc notes the v3 module is a simpler reading of the screen (a 20-day high breakout, close at or below 1.25 x SMA20, the small-cap tag and the QQQ-down rule), and the module header records Source status Live.

## What this sleeve is
This sleeve buys small-cap breakout leaders directly from daily bars: a name tagged small in the alt data that closes over its prior 20-session high without stretching past 1.25 times its 20-session average, on a QQQ-down day. It is v3-native in laz_sleeves/s_cl_qm_small.py and does not consume fires. Sources: laz_sleeves/s_cl_qm_small.py and laz_sleeves/_common.py on the desk.

## Full algorithm
Evaluation order in laz_sleeves/s_cl_qm_small.py evaluate(view, ctx) (SLOTS 8, SLOT_USD 1000.0, HOLD_SESSIONS 90):

1. Session: the session date is read from view now; no parseable session date emits nothing.
2. Held positions first (positions filtered to this sleeve_id by the _common _positions helper, nonzero qty only): when the count of the symbol's daily bars dated strictly after opened_at reaches 90, exit the full held qty at the last close, reason cl_qm_time90. No stop is implemented.
3. Entry gate: entries stop when held positions reach 8, and entries require the QQQ-down house rule (_qqq_down: at least 2 QQQ daily bars and the last QQQ close below the prior close); otherwise the call returns with only any exits.
4. Candidates, in sorted bars-map key order, for each key ending |1Day except QQQ|1Day, skipping held symbols: the alt_data entry for the symbol must carry mcap_band == "small"; at least 21 daily bars are required.
5. Breakout test on the last bar: last close >= $5.0; last close strictly above the prior 20-session high (max high over bars[-21:-1]); and last close at or below 1.25 * SMA20, where SMA20 is the mean of closes over bars[-21:-1].
6. Sizing and intent: qty = int(1000.0 // last close) (_qty_for); qty at or below 0 skips. The entry intent is a market, day, buy priced (hint) at the last close, reason cl_qm_breakout.
7. Slot-count cure (ENH19, on by default; extra s_cl_qm_small_enh19 slot_guard): entries already emitted in this pass count toward the 8 slots, so the pass breaks once held plus emitted entries reach 8 and journals the overflow as the shadow-faithful overflow; OFF restores the pre-change fixed-held-count test.

## Files in this repo
- Sleeve module: laz_sleeves/s_cl_qm_small.py (the strategy logic; v3-native, evaluate(view, ctx)); also copied in this repo at sleeves/lazarus/s_cl_qm_small.py and integration/s_cl_qm_small_adapter.py.
- Shared engine file: laz_sleeves/_common.py (desk laz_sleeves/_common.py; the helpers _bars, _positions, _session, _intent, _qty_for and the ENH19 helpers this module imports). NOTE: engines_map.json records engines/laz_sleeves/_common.py as gate_blocked, so this shared file is not present in this repo; a recreation must supply the same helper definitions from a fresh desk.
- Existing strategy doc: strategies/lazarus/cl-qm-small.md.
- Config: engines/config/sleeves.json (row id=s_cl_qm_small).

## Configuration
Module laz_sleeves.s_cl_qm_small; cadence_s 86400; session rth; slice capital_usd 8000.0, cash_usd 8000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars_1day, positions, alt_data]; parked false. Source: muse-desk-v3/config/sleeves.json row id=s_cl_qm_small. The module's own constants are 8 slots x $1,000, matching the $8,000 slice.

## Data inputs
Daily bars in view bars as {SYM|1Day: [{t,o,h,l,c,v} ascending]} for the candidate universe plus QQQ (for the QQQ-down rule); positions filtered to this sleeve; alt_data {SYM: {mcap_band, ...}} from the alt-data producer (the tracker/PIT shares band product; the module reads only mcap_band); the session date from view now. No fires and no data fetched during evaluation.

## Install and run
1. Place the sleeve module at laz_sleeves/s_cl_qm_small.py (also copied in this repo at laz_sleeves/s_cl_qm_small.py, sleeves/lazarus/s_cl_qm_small.py and integration/s_cl_qm_small_adapter.py) and supply the shared helper module laz_sleeves/_common.py: engines_map.json records engines/laz_sleeves/_common.py as gate_blocked, so that one shared file is NOT in this repo and a recreation must supply the same helper definitions (the functions named in Files in this repo) from a fresh desk.
2. Register the config row for `s_cl_qm_small` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides (params {}).
3. Wire the producers named in Data inputs so bars, positions and the sleeve's third input arrive in the snapshot view in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the module's evaluate(view, ctx), which reads the session date from view now and emits v3 intent dicts directly (no separate adapter delegation).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A (entry): on a QQQ-down session, a small-tagged name with 21 or more bars closing at or above $5, strictly over its prior 20-session high and at or below 1.25 x its 20-session close average, produces one market buy of int(1000.0 // close) shares with reason cl_qm_breakout. Fixture B: the same name on a QQQ-up session, or with mcap_band not small, produces no entry. Fixture C (exit): a position with 90 bars after its open date produces one full exit with reason cl_qm_time90.

- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated partial quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
