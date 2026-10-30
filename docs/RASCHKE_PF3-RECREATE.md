# raschke_pf3: Recreation package

Provenance: Source row in strategies/muse/muse-raschke-pf3.md in this repo: Linda Raschke's PF3 momentum method, as designed into an algorithm by Grok (for ES 5-minute futures).

## What this sleeve is
This sleeve expresses a 5-minute momentum-slope method in SPY shares, long and short: when the ROC2, fast and slow slope lines all rise it goes long, and when all fall it goes short, entering at the first bar of an alignment cluster with a 0.75 ATR stop and a 1.5 ATR target. It is forward-testing only and claims no backtest result. Sources: sleeves/raschke_pf3.py (repo copy at sleeves/muse/sleeves/raschke_pf3.py) and desk3/port_b5/raschke_pf3.py on the desk.

## Full algorithm
Method math (sleeves/raschke_pf3.py): ROC2 = C - C[2]; Fast = SMA(C,3) - SMA(C,10); Slow = SMA(Fast,16). Long when all three slopes are strictly up (each line above its prior value), short when all are strictly down; a zero slope is not aligned. Constants: SYM SPY, STOP_MULT 0.75 (stop 0.75 x ATR(14)), TARGET_MULT 1.5, MAX_HOLD_BARS 10, RISK_PCT 0.005, ADX_THRESHOLD 20.0, WARMUP_BARS 26 (28 with the trend filter on), FLAT_BEFORE_CLOSE_MIN 5, CUTOFF_BEFORE_CLOSE_MIN 10, BAR_SECONDS 300. CONFIG: cadence_s 60, universe (SPY,). Bars are completed RTH 5-minute SIP bars only, continuous across sessions; premarket bars never enter the math.
Evaluation order in signal():
1. Position management first, never trapped behind warmup or any entry block. Exit precedence: flat (at close minus 5 minutes, and a carried overnight position exits on the session's first pass) > stop > target > slope-reverse (the first completed bar after the entry bar where any slope is no longer aligned with the position) > time (10 bars held). Stop and target are in-signal completed-bar-close evaluations frozen at signal time off the entry anchor; they are never broker resting stops.
2. Calendar: a non-trading day produces no entry.
3. Entry proof: entries need the gpf3_journal door or the session fills fallback; with neither, entries stand down. In fills-only mode, any entry fill this session consumes the (unnamed) cluster and no further entry is proven.
4. Warmup fail-closed: fewer than 26 completed bars (28 with the filter on) is blocked_warmup.
5. Signal: the latest completed bar must be the FIRST bar of an alignment cluster and must belong to this session (no backfill of a missed cluster). A cluster already in the journal's consumed_clusters stands down (one entry attempt per cluster, consumed on emission); opposite clusters may follow immediately.
6. Cutoffs: no entry when the signal bar closes after close minus 10 minutes, or at or after close minus 5 minutes. Short entries stand down when the desk declares SPY not shortable.
7. Trend filter (switch extra gpf3_trend_filter, default OFF): when ON, Wilder ADX(14) at the signal bar must be strictly above 20.
8. Sizing: qty = floor(0.005 x slice equity / (0.75 x ATR(14))); a zero quantity is recorded in the journal as a sizing rejection and no trade is emitted. Entry is a market intent with price_hint = the signal-bar close (the anchor); stop and target are frozen off that anchor.

## Files in this repo
- Strategy module (desk sleeves/raschke_pf3.py, the strategy logic; CONFIG sleeve_id=raschke_pf3): the desk module path is sleeves/raschke_pf3.py.
- v3 wrapper (desk desk3/port_b5/raschke_pf3.py): `desk3/port_b5/raschke_pf3.py` in this repo (also copied at sleeves/raschke_pf3.py); its evaluate(view, ctx) delegates through the shared context runner.
- v3 adapter / integration copy: `integration/raschke_pf3_adapter.py`.
- Shared engine files (engines_map.json): `engines/desk3/port_b5/_ctx.py` (desk desk3/port_b5/_ctx.py, vendored).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Shared files used by the strategy: `sleeves/muse/core/data.py` and `sleeves/muse/core/early_close.py` (desk core/data.py, core/early_close.py; the shared early-close table).
- Full strategy copy in this repo: `sleeves/muse/sleeves/raschke_pf3.py`.
- Test in this repo: tests/test_raschke_rre_event_feed_blockers.py covers the sibling RRE sleeve's event feed only, not this sleeve.
- Config: engines/config/sleeves.json (row id=raschke_pf3); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module desk3.port_b5.raschke_pf3; cadence_s 60; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars', 'positions', 'journal']; parked false. Source: muse-desk-v3/config/sleeves.json row id=raschke_pf3 (repo copy: engines/config/sleeves.json).

## Data inputs
Completed RTH 5-minute SIP bars for SPY via context.extra["bars_5m_long"] (the shared long 5-minute SIP door); session_fills via context.extra (entry-proof fallback); the gpf3_journal served in context.extra or slice_state; slice equity for sizing; the market record's spy_shortable flag via context.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `raschke_pf3` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check alignment: any one slope flat or opposed produces no signal; all three strictly up signals long and all three strictly down signals short.
- Check warmup: 25 completed bars is blocked_warmup (27 with the trend filter on); 26 (28) proceeds.
- Check cluster law: a bar that is the second bar of a cluster produces no entry, a consumed cluster is never re-entered, and a cluster that began in a prior session is not backfilled.
- Check exits and precedence: on a fixture position, flat-at-close-minus-5 beats stop, stop beats target, target beats slope-reverse, slope-reverse beats the 10-bar time exit.
- Check sizing: qty equals floor(0.005 x equity / (0.75 x ATR)); an ATR large enough to make qty 0 records a sizing rejection and emits nothing.
- Check the trend filter: with it ON, ADX of exactly 20 blocks the entry; 20.01 passes that gate.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
