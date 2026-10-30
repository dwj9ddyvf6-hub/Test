# po10_qqq: Recreation package

Provenance: Source row in strategies/muse/muse-po10-qqq.md in this repo: Milkman Trades' PO10 extreme algo (NQ, August 2026 thread), translated to QQQ shares.

## What this sleeve is
This sleeve translates a Nasdaq futures Phase Oscillator extreme system into QQQ shares: the first completed 10-minute PO close beyond plus or minus 100 inside the 09:30 to 11:00 ET entry window opens a long or short QQQ position, which exits on the opposite cross or flat at 15:59 ET. It has no stop and no target by design; the exit rule is the whole risk model. Sources: sleeves/po10_qqq.py (repo copy at sleeves/muse/sleeves/po10_qqq.py) and desk3/port_b5/po10_qqq.py on the desk.

## Full algorithm
Constants (sleeves/po10_qqq.py): SYM QQQ, PO_THRESHOLD 100.0 (strict: beyond, never at), WINDOW_START 09:30 ET, WINDOW_END 11:00 ET (a close at 11:00 does not enter), FLAT_T 15:59 ET, MNQ_COUNT 2, MNQ_USD_PER_POINT 2.0 (so USD_PER_NQ_POINT 4.00), NQ_QQQ_MULTIPLIER 41.0, ENTRY_FRESH_S 1800, QUOTE_STALE_S 60. CONFIG: cadence_s 60, universe (QQQ,). Indicator math comes from core/saty_bars and core/saty_indicators run on QQQ 10-minute bars over the extended session 04:00 to 20:00 ET, aggregated from 5-minute SIP bars; only completed 10-minute bars are read.
Evaluation order in signal():
1. Non-trading day: no action. Missing series: blocked_data (a held position still gets its blocked-exit path, step 3). Empty series: blocked_warmup.
2. Held position first (broker truth; never adds): exit when an opposite PO cross prints on a completed 10-minute bar after the fill (opposite_cross), else at or after 15:59 ET (eod_flat). A long sells to close at the bid, a short buys to close at the ask (quote door, 60-second staleness convention; the last close is the fallback reference, and an unpriced exit emits nothing). An overnight residual is flagged and is exited by the same rules, and by the blocked-exit path even when the series is missing.
3. Entries: one entry per session, proven from the session's own fill rows; when session_fills is unavailable, entries fail closed (blocked_no_fills_proof) while exits are unaffected. Any buy_to_open or sell_to_open fill today means no further entry.
4. Signal: first_signal is the first completed 10-minute close of the session whose close time falls in [09:30, 11:00) ET with PO beyond +100 (long) or below -100 (short), whether the cross itself printed in-window or earlier.
5. Freshness: the signal must be at most 1800 seconds old (and not more than 60 seconds in the future), else it is spent and never backfilled.
6. Sizing: shares = round(4.00 x NQ level / QQQ price), where the NQ level is approximated as QQQ price x 41.0; the reference price is a fresh quote when available, else the last series close. Zero shares skips.
7. Entry intent: a marketable limit at the ask for a long (buy_to_open) or the bid for a short (sell_to_open). Intent stop and target are never set.

## Files in this repo
- Strategy module (desk sleeves/po10_qqq.py, the strategy logic; CONFIG sleeve_id=po10_qqq): the desk module path is sleeves/po10_qqq.py.
- v3 wrapper (desk desk3/port_b5/po10_qqq.py): `desk3/port_b5/po10_qqq.py` in this repo (also copied at sleeves/po10_qqq.py); its evaluate(view, ctx) delegates through the shared context runner.
- v3 adapter / integration copy: `integration/po10_qqq_adapter.py`.
- Shared engine files (engines_map.json): `engines/desk3/port_b5/_ctx.py` (desk desk3/port_b5/_ctx.py, vendored).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Shared indicator / bar files used by the strategy: `sleeves/muse/core/saty_bars.py`, `sleeves/muse/core/saty_indicators.py` and `sleeves/muse/core/early_close.py` (desk core/saty_bars.py, core/saty_indicators.py, core/early_close.py).
- Full strategy copy in this repo: `sleeves/muse/sleeves/po10_qqq.py`.
- Config: engines/config/sleeves.json (row id=po10_qqq); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module desk3.port_b5.po10_qqq; cadence_s 60; session rth; slice capital_usd 125000.0, cash_usd 125000.0; bp_buffer_frac 0.02; flat_by_close true; flatten_time_et 15:55; params {}; inputs ['bars', 'positions', 'quotes', 'session_fills']; parked false. Source: muse-desk-v3/config/sleeves.json row id=po10_qqq (repo copy: engines/config/sleeves.json).

## Data inputs
QQQ 5-minute SIP bars (aggregated to completed 10-minute bars over 04:00 to 20:00 ET) via the desk's bar door in context.extra; latest quotes (IEX convention, 60-second staleness) via context.extra; sleeve_state {QQQ: {position}} from the broker record; session_fills (the session's own fill rows) via context.extra. No bars means no signal: the sleeve stands down and never guesses.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `po10_qqq` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the threshold: a PO close of exactly +100 or -100 produces no signal; +100.01 signals long and -100.01 signals short.
- Check the window: a first beyond-threshold close at 11:00 ET does not enter; one at 10:50 ET does, subject to freshness.
- Check freshness: a signal first seen more than 1800 seconds after its close is spent and produces no entry.
- Check one-entry-per-session: with a buy_to_open fill already in session_fills, no second entry is emitted; with session_fills missing, entries are blocked but a held position still exits at 15:59 ET.
- Check exits: an opposite cross exits before 15:59 ET; absent a cross, the position is flat at 15:59 ET; no intent ever carries a stop or target.
- Check sizing: shares equal round(4.00 x (QQQ x 41.0) / QQQ) for the fixture reference price.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
