# em_1587: Recreation package

Provenance: Source row in strategies/muse/muse-em-1587.md in this repo: Azrael's 15.87 Rule, reverse-engineered from his worksheet (family Muse, asset SPY options (0DTE), timeframe 5m, universe SPY (QQQ confirms), style expected-move levels).

## What this sleeve is
This sleeve draws the day's expected-move map from the prior VIX close divided by 15.87, then trades same-day SPY options: in the calm regime it fades a wall touch toward the magnet, and in the confirm and fast regimes it buys a confirmed SPY and QQQ break of the opening box. Everything is flat by 11:30 ET and there is at most one setup per session. The strategy module sleeves/em_1587.py binds the reconstruction parameters in the shared core sleeves/muse/core/em_1587.py, and the v3 adapter delegates through the snapshot glue with entry filtering through desk3/enhance14.py in the adapter path.

## Full algorithm
Module constants (sleeves/em_1587.py): SYM = "SPY", CONFIRM_SYM = "QQQ", BUDGET_PCT = 0.04 (premium budget per entry), EXPIRY_DTE = 0 (SPY 0DTE), QUOTE_STALE_S = 60.0, SPREAD_MAX_FRAC = 0.05, ENTRY_FRESH_S = 1800.0 (one-shot signal freshness, 30 minutes), ROOM_MIN_ANCHOR = the core ROOM_MIN_SPX divided by SPX_SCALE (= 0.8 SPY points), AGREE_TOL_ANCHOR = the core AGREE_TOL_SPX divided by SPX_SCALE (= 0.5). CONFIG: cadence_s 60, universe ("SPY", "QQQ"), risk_pct 0.04. SPX is read as SPY: the map is drawn in SPY prices and SPX points convert at 10 to 1.

The map, before the open (in the core, per the module header): EM percent = prior ^VIX close / 15.87; EM points = EM percent x prior SPY close, rounded to 0.1 point BEFORE lines are drawn. Five lines: prior close plus/minus EM (walls), plus/minus EM/2 (shelves), and the prior close itself (magnet). Regime from the same VIX close: under 15 FADE; 15 to 18.5 CONFIRM; above 18.5 FAST (never fade, half size). The three biggest open-interest strikes above and below price are cross-checked against the map and logged; they never gate.

Entries, in code order (signal closes 09:50 to 11:05 ET only, acted on within ENTRY_FRESH_S = 30 minutes, at most one setup position per session):
1. Break setup (CONFIRM and FAST regimes): SPY and QQQ each close beyond their own 09:30 to 09:50 box (the first-20-minute box) on the SAME completed 5-minute bar, each by at least 0.05 x that ticker's EM; each box must be no wider than 0.2 x its EM; room to the next map line must exceed 0.8 points and be at least 1R (R = the signal close to the box edge). Direction follows the break (calls above, puts below, in SPY 0DTE).
2. Fade setup (FADE regime only): the first bar whose range reaches a wall: long from the lower wall, short (puts) from the upper wall, toward the magnet; a bar touching both walls stands down.
3. Contract: today's SPY expiry (0DTE), the strike nearest spot; its quote must be two-sided, at most QUOTE_STALE_S = 60 seconds old, with spread at most SPREAD_MAX_FRAC = 5 percent of mid; the entry is a limit at the mid.
4. Sizing: BUDGET_PCT = 4 percent of the $10,000 slice in premium (half in the FAST regime), whole contracts, at least 1; the card adds that no entry may cost more than the slice's free cash.

Exits, in code order:
1. Position from an earlier day: sold at once.
2. Break positions: out when a bar reaches the next map line (target checked first), or on a 5-minute close back inside the SPY box.
3. Fade positions: out at the magnet, or on a 5-minute close beyond the wall by EM/2 (stop checked first).
4. Hard flat at 11:30 ET: a mid limit, the bid from 11:25, market from 11:28.

Position management: at most one setup position per session, no pyramiding, hard flat at 11:30 ET every day.

## Files in this repo
- Sleeve module (desk sleeves/em_1587.py): `sleeves/em_1587.py`.
- v3 adapter (desk adapters3/em_1587.py): `adapters3/em_1587.py`; also present as `integration/em_1587_adapter.py`.
- Shared engine core bound by the sleeve: `sleeves/muse/core/em_1587.py` (desk source core/em_1587.py), with `sleeves/muse/core/sleeve.py`, `sleeves/muse/core/data.py` and `sleeves/muse/core/early_close.py` (the audit record's engine_files_needed for this sleeve).
- Shared entry filter in the adapter delegation path: `engines/desk3/enhance14.py` (desk source desk3/enhance14.py, vendored in this repo per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/muse/muse-em-1587.md`.

## Configuration
- Universe: SPY (traded) with QQQ as the confirmation symbol. Asset: SPY 0DTE options. Timeframe: 5m bars; entries 09:50 to 11:05 ET; hard flat 11:30 ET.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk_pct 0.04 in CONFIG (4 percent of the slice in premium, half in the FAST regime).
- Cadence: 60 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions, options, extra.

## Data inputs
- bars: SPY and QQQ 5-minute bars (4,000 per the card) for the boxes, breaks and exits.
- VIX: the prior ^VIX close (Yahoo daily per the card) for EM percent and the regime.
- options: the SPY 0DTE chain with quotes (two-sided, at most 60 seconds old) and per-strike open interest (logged context only, never a gate).

## Install and run
1. Place the sleeve module at sleeves/em_1587.py, the core at sleeves/muse/core/em_1587.py with its sibling core files (sleeve.py, data.py, early_close.py), and the adapter at adapters3/em_1587.py (repo copies at the same paths). The adapter uses evaluate_ported from the snapshot glue and the shared filter at desk3/enhance14.py (repo copy at engines/desk3/enhance14.py).
2. Register the roster row for `em_1587` exactly as in the Configuration section in config/sleeves.json (module adapters3.em_1587, cadence 60, session rth, $10,000 slice, inputs bars/positions/options/extra).
3. Wire the producers so every snapshot carries SPY and QQQ 5-minute bars, the prior ^VIX close, the SPY 0DTE chain with quotes and open interest, and this sleeve's positions.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot before 09:50 ET, with a signal older than 30 minutes, or with a position already held today returns no new entry, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch2_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check the map: with prior close C and prior VIX V, EM points equal round(C x V / 15.87 / 100, 1) as computed by the core's rounding rule, walls at C plus/minus EM, shelves at C plus/minus EM/2, magnet at C; VIX under 15 gives FADE, 15 to 18.5 CONFIRM, above 18.5 FAST.
- Check the break: SPY and QQQ must break their own 09:30 to 09:50 boxes on the same 5-minute bar by at least 0.05 x EM, each box at most 0.2 x EM wide, with room over 0.8 points and at least 1R; a single-ticker break produces no entry, and no fade is taken in FAST.
- Check the fade and contract gates: in FADE only a first wall touch trades (both walls touched stands down); a quote older than 60 seconds or wider than 5 percent of mid, a non-0DTE expiry, or a second setup in the session each produce no entry; premium is 4 percent of the slice (2 percent in FAST).
- Check exits: a break position exits at the next line before the box re-entry check, a fade position exits on the beyond-wall stop before the magnet check, any earlier-day position is sold at once, and every position is flat by 11:30 ET (bid from 11:25, market from 11:28).
