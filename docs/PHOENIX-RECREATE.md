# phoenix: Recreation package

Provenance: Source row in strategies/femto/femto-phoenix.md in this repo: The old Alpaca swing desk, via Femto-lean.

## What this sleeve is
This is a daily breakout equity sleeve over a fixed 19-name universe: a strict 20-day closing-high breakout made while SPY's trailing 60-day return is not positive becomes a pending signal, and the sleeve enters on the first red day within the next 5 sessions, holding 20 trading days. Entries are evaluated only on the first pass at or after 15:55 ET. Sources: sleeves/phoenix.py and desk3/port_b5/phoenix.py on the desk.

## Full algorithm
Constants (sleeves/phoenix.py): UNIVERSE (MU, WDC, ANF, CLS, FFIV, AAOI, AXTI, SOXL, AEHR, FCEL, TTMI, SIMO, VICR, AG, SILJ, SPY, QQQ, NVDA, AAPL), REGIME_PROXY SPY, WARMUP_BARS 60, LOOKBACK 20, ENTRY_WINDOW 5, HOLD_DAYS 20, DISASTER_STOP 0.25, RISK_FRACTION 0.0025, MAX_POSITIONS 8, SLEEVE_NOTIONAL_CAP 0.25, EARNINGS_STALE_DAYS 8, BLACKOUT_DAYS_BEFORE 3, COST_BPS 0.0005. CONFIG: cadence_s 300, universe = UNIVERSE.
Evaluation order in signal(): symbols with fewer than 61 bars are skipped fail-closed. Evaluation (entries and due exits) runs only in the window from 15:55 to 20:00 ET; the math bars always exclude today's forming session.
1. Signal (closed bars only, recomputed every pass and merged with persisted pending signals): close[t] strictly above max(close[t-20..t-1]) (ties do not count), AND trailing-60-session SPY return at t (SPY close[t] / close[t-60] - 1) <= 0, AND signal-bar volume > 0.
2. Exit first inside the window: a held position exits at the close of the 20th trading day after the entry bar (a dead exit session defers to the next available close; an entry bar absent from the bars fails safe toward exiting as soon as possible). The exit needs a forming bar with volume. The 25 percent disaster stop below the entry fill is carried as ExitRule data.
3. Entry gate chain, in order: no existing position or pending entry; broker book readable (broker_qty None fails closed; a nonzero broker qty not claimed by another sleeve blocks as an orphan, a co-held name does not burn the signal); an active pending signal exists and its date is in the bars; window day (bars since the signal + 1) is within 1..5; entries not auto-paused (3 disaster-stop hits in the trailing 20 closed trades pause entries until explicitly resumed); a forming bar exists for today.
4. Red test: the forming day must be red (close below its own open). Amendment (switch context.extra["phoenix_improve"]["armb_day5_fallback"], default ON): on window day 5 only, a gate-clean signal with no red day falls through and enters at the day-5 forming close; days 1 to 4 are unchanged.
5. Remaining gates after the red test, in code order: the earnings veto (entries vetoed from 3 days before through the earnings date; a stale or missing calendar, or a symbol absent from it, fails closed); de-overlap (an entry day on or before the last exit day is skipped); fewer than 8 open positions; sizing qty from the 0.25 percent risk budget on the 25 percent stop distance (a 1.0 percent notional target, with a 1-share minimum whose overshoot is flagged); and sleeve notional after the entry at most 25 percent of equity.

## Files in this repo
- Strategy module (desk sleeves/phoenix.py, the strategy logic; CONFIG sleeve_id=phoenix): the desk module path is sleeves/phoenix.py.
- v3 wrapper (desk desk3/port_b5/phoenix.py): `desk3/port_b5/phoenix.py` in this repo (also copied at sleeves/phoenix.py); its evaluate(view, ctx) delegates through the shared context runner.
- v3 adapter / integration copy: `integration/phoenix_adapter.py`.
- Shared engine files (engines_map.json): `engines/desk3/port_b5/_ctx.py` (desk desk3/port_b5/_ctx.py, vendored).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=phoenix); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module desk3.port_b5.phoenix; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars', 'positions', 'earnings']; parked false. Source: muse-desk-v3/config/sleeves.json row id=phoenix (repo copy: engines/config/sleeves.json).

## Data inputs
Daily bars for the universe plus SPY (the regime proxy); context.extra: sleeve_state {SYM: {pending_signals, pending_entry, position, last_exit_date}}, meta {closed_trades, entries_paused_by_disaster_rule}, forming {SYM: {o, c, v}} for today's session, earnings {SYM: date|None} with earnings_fresh, broker_qty {SYM: qty} (None means unreadable), and foreign_holders {SYM: [sleeve, ...]}.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `phoenix` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the signal: a close equal to the prior 20-day maximum does not signal (strict), a positive SPY 60-day return at the signal bar does not signal, and zero signal-bar volume does not signal.
- Check the entry window: entry occurs on the first red forming day within days 1 to 5; with the day-5 fallback OFF, a signal with no red day in the window is skipped; with it ON, day 5 enters at the forming close.
- Check fail-closed gates: broker_qty None, a stale earnings calendar, and a symbol missing from the calendar each produce no entry.
- Check the exit: a position exits on the 20th trading day after entry, and a missing forming bar defers the exit to the next available close.
- Check caps: the 9th concurrent position and an entry that would take sleeve notional above 25 percent of equity are refused.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
