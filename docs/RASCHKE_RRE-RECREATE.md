# raschke_rre: Recreation package

Provenance: Source row in strategies/muse/muse-raschke-rre.md in this repo: Astra's RRE Adaptive Desk v0.2.0, on Linda Raschke's methods.

## What this sleeve is
This sleeve is a thin desk wrapper over a complete routed research engine for SPY on 5-minute bars: two lanes advance on every bar, but only a routed RRE2 candidate (FIRST_CROSS / FAILED_BREAK) may become an entry, while RRE1 candidates are journaled as baseline only and never trade. Exits run first in every pass, and a macro-release calendar gates entries by session. Sources: sleeves/raschke_rre.py, the core/raschke_rre engine package, and desk_sleeves/raschke_rre.py on the desk.

## Full algorithm
Constants (sleeves/raschke_rre.py): SYM SPY, SERIES_ID SPY-5m-RTH-SIP-v1, CALENDAR_VERSION desk-rth-earlyclose-v1, MAX_QUOTE_AGE_S 5.0, COOLDOWN_S 900, HOLD_S 1800, PRIOR_FEED_SESSIONS 40. CONFIG: cadence_s 60, universe (SPY,). The wrapper contains no strategy math: the brain is the core/raschke_rre package (raschke_core, raschke_engine, awareness, router) plus the adapted admission module.
Evaluation order in signal():
1. Event gates first: (event_coverage_known, events_clear) resolve from the macro-release calendar in context.extra["macro_events"] (FOMC decision, CPI and Employment Situation release dates). Coverage is known only inside the calendar's committed window; a listed release date is a session blackout; anything absent or malformed stays (False, False), fail closed.
2. Thesis reconciliation: one SPY thesis at a time; the journal's active_thesis holds the slot from entry-intent emission until terminal flat reconciliation proven by the served position/fill records (an expired unfilled intent releases it). Cooldown is 900 wall-clock seconds after that proven-flat pass.
3. Exits first, always, in this precedence: quote-triggered stop, quote-triggered target, the 1800-second hold deadline from the first actual fill (the intent creation time is the provisional fallback, journaled), and flatten at session close minus 300 seconds. A due exit with no fresh executable quote is journaled exit_due_unpriced and never priced synthetically. Exits are never trapped behind warmup or the event block.
4. Bar bundle: current plus prior sessions from the 5-minute SIP door; frozen PriorSessionReference objects are built per session (complete only when the prior session's bars cover its full grid). Up to 40 prior sessions are fed to a fresh router so its context and baseline are built by the engine's own machinery.
5. Warmup (required elements only): a complete frozen prior-session reference, and core feature readiness (features exist with a known previous state; the PF3 arm gate is at generation bar_count >= 27). The 20-session same-slot baseline is optional context: ratios stay None and nothing blocks on it.
6. Feeding: this session's completed bars are fed exactly once (journal watermark), harvesting routed and vetoed candidates per bar; DATA_BLOCK and SHOCK_PAUSE vetoes are journaled VETOED and never offered to admission.
7. Admission and disposition: pending routed candidates pass the admission pins: the virtual slice equity is the single capital bound; max_risk_age 60 s; spread caps 0.10 / 0.01; depth participation 0.5; adverse-gap 0.2 x ATR; crossing caps $20 / 0.2; costs (.01, .01, .01, 2); allowed feeds (sip, iex). Quote sizes of 0/0 mean depth unknown: a non-binding depth record is substituted and journaled. Shorts fail closed: with no borrow-verification door, borrow_verified is False and admission rejects SHORT_NOT_EXPRESSIBLE. Only a routed RRE2 candidate (FIRST_CROSS / FAILED_BREAK) may become a desk entry intent; a routed RRE1 candidate is journaled BASELINE_ONLY and never trades.

## Files in this repo
- Strategy wrapper (desk sleeves/raschke_rre.py): `sleeves/raschke_rre.py` in this repo.
- v3 adapter (desk desk_sleeves/raschke_rre.py): `integration/raschke_rre_adapter.py` in this repo; it serves 5-minute SPY bars (2000 requested), sleeve_state, session_fills, latest_quote and macro_events into context.extra, and persists the rre_journal in the sleeve's own state directory.
- Engine package (desk core/raschke_rre/): `sleeves/muse/core/raschke_rre/__init__.py`, `sleeves/muse/core/raschke_rre/admission.py`, `sleeves/muse/core/raschke_rre/awareness.py`, `sleeves/muse/core/raschke_rre/raschke_core.py`, `sleeves/muse/core/raschke_rre/raschke_engine.py`, `sleeves/muse/core/raschke_rre/router.py`.
- Shared files: `sleeves/muse/core/sleeve.py`, `sleeves/muse/core/data.py`, `sleeves/muse/core/early_close.py` (desk core/sleeve.py, core/data.py, core/early_close.py).
- Test in this repo: tests/test_raschke_rre_event_feed_blockers.py (the event-feed blocker).
- Config: engines/config/sleeves.json (row id=raschke_rre); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module raschke_rre; cadence_s 60; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars_5min', 'positions', 'session_fills', 'latest_quotes', 'macro_events']; parked false. Source: muse-desk-v3/config/sleeves.json row id=raschke_rre (repo copy: engines/config/sleeves.json).

## Data inputs
SPY 5-minute SIP bars (current and prior sessions) via context.extra["bars_5m_long"]; latest quotes via context.extra (the IEX latest-quote door; maximum quote age 5.0 s for exit pricing); session fills and positions via context.extra / slice_state; the macro-release calendar via context.extra["macro_events"] (producer desk3/macro_calendar.py data); the rre_journal served back through the adapter's persisted state.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `raschke_rre` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the event seam: a session listed in the macro calendar produces no entry; a session outside the calendar's coverage window also produces no entry (fail closed), with the absence named in the stamp.
- Check exits first: a held position past its 1800-second hold deadline exits even on a warmup-blocked or event-blocked pass; a due exit with no fresh quote is journaled unpriced and emits no synthetic price.
- Check warmup: an incomplete prior-session reference blocks entries (blocked_warmup) but not exits; a missing 20-session baseline does not block.
- Check routing: an RRE1 candidate is journaled BASELINE_ONLY and emits no intent; only an RRE2 FIRST_CROSS or FAILED_BREAK candidate can reach admission.
- Check the thesis law: a second entry is refused while a thesis is active, and the 900-second cooldown runs only from the proven-flat pass.
- Check shorts: a short candidate is rejected at admission as not expressible.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
