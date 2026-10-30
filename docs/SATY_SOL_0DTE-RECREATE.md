# saty_sol_0dte: Recreation package

Provenance: Sol (ChatGPT), autonomous engine design v1.0 of the Saty / Milkman Trades day system (Source row in strategies/muse/muse-saty-sol.md in this repo).

## What this sleeve is
This sleeve is an independent second implementation of the Saty day system on SPY options, kept for a head-to-head comparison: it does NOT import the other desk implementation's later corrections (confluence gate, $10,000 stop, partials, runners all stay out). Its active profile is SPY_ZERO_DTE_BOOK_V1. Sources: desk sleeves/saty_sol_0dte.py (constants F_TRIGGER=0.236, F_GATE=0.382, F_TARGET=0.618, MAX_ADVERSE_ATR=0.03, PO_EXTREME=61.8, SPREAD_GATE=0.05, PREMIUM_FRACTION=0.005, DAILY_LOSS_FRACTION=0.01, FEES_PER_CONTRACT=0.0, MULTIPLIER=100, ENTRY_START 09:35, ENTRY_END 14:30, MIN_MINUTES_TO_CLOSE=90, LIQ_MINUTES_BEFORE_CLOSE=10, QUOTE_STALE_S=60.0, ENTRY_FRESH_S=120.0; CONFIG cadence_s=60, universe=(SPY,), risk_pct=0.005) and strategies/muse/muse-saty-sol.md in this repo.

## Full algorithm
Two policies trade, in desk sleeves/saty_sol_0dte.py signal(). The coordinate is x = d*(S-C0)/A0, where C0 is the frozen prior-day close, A0 its ATR, S the current price and d the trade direction.
1. GG_TOUCH_RAW_V1 (both directions): a direction arms only when the session opens with x < 0.382; the FIRST crossing of 0.382 (by a 1-minute close or the live quote mid) consumes the episode for the session, even outside the entry window, rejected, unaffordable or unfilled; a start already beyond 0.382 is not a crossing (no gap entries). Entry requires the mark still inside the kernel band [0.382, 0.382+0.03 ATR], the 0.618 target not already achieved, a resolved contract and a valid quote. The completed-1h Phase Oscillator tag is recorded on every Golden Gate event (aligned d*PO >= 61.8, opposing <= -61.8) and never gates; the BILBO_FILTER, RIBBON_FILTER and NQ_CONFIRM experiments are disabled.
2. TRIGGER_3M_CALL_V1 (bullish only; the put mirror is disabled): the session must open inside the full -0.236..+0.236 band; the first completed 3-minute close above +0.236 whose preceding same-session 3-minute close was at or below the trigger (first bar: the session open mark) is the signal, consumed even outside the window. Entry must remain above the trigger, below +0.382, and within 0.03 ATR above the confirming close.
3. Arbitration and windows: each event is acted on only by the first pass that sees it (within ENTRY_FRESH_S=120 seconds), then spent; new entries 09:35-14:30 ET and at least 90 minutes before the actual session close; one position or working entry at a time, Golden Gate first.
4. Contract: today's expiry only: the nearest eligible expiry is today's, then the nearest strike to the signal coordinate (spot), tie-break relative spread then contract id; a session with NO same-day SPY expiry listed is no trade and a later expiry is NEVER substituted, even when it is the only chain available (this refusal is the variant's core law, its sole deviation from the sibling sleeve); strike nearest the spot; the quote two-sided with spread at or below 5 percent of mid and at most 60 seconds old; a limit at the ask.
5. Sizing: session premium budget = 0.5 percent of the $10,000 slice (PREMIUM_FRACTION=0.005, i.e. $50) less premium already spent today; contracts = floor(budget / (100 x ask)), which can be 0 (no trade). A 1 percent daily loss (DAILY_LOSS_FRACTION=0.01; fills plus the open position at the bid) halts new entries for the session.
6. Exits (limits at the bid; mandatory liquidation begins 10 minutes before the close (market with no quote), and the roster row also flattens at 15:55 ET; a position from an earlier session is sold at once; no partials, no runners): Golden Gate: all out at the first mark x >= 0.618 after fill, or on a 10-minute close with x < 0.236 (strict: equality does not breach) whose bar end is strictly after the first fill, whichever comes first (a tie is invalidation). Trigger: all out at the first mark at or above +0.382, or on a 3-minute close below +0.236 ending strictly after the first fill.

## Files in this repo
- Sleeve module: sleeves/saty_sol_0dte.py (strategy logic, CONFIG and all constants above).
- v3 adapter: adapters3/saty_sol_0dte.py (SLEEVE_ID=saty_sol_0dte; evaluate(view, ctx) rebuilds the v2 SleeveContext via adapters3/_snapshot_ctx and delegates to adapters/saty_sol_0dte.py; the _snapshot_ctx glue itself is not in this repo at its canonical path, as the audit record notes).
- Adapter mirror: integration/saty_sol_0dte_adapter.py in this repo.
- Shared Saty core files (desk core/, under sleeves/muse/ on the desk): sleeves/muse/core/sleeve.py (BaseSleeve, Intent, SleeveConfig), sleeves/muse/core/data.py, sleeves/muse/core/early_close.py (shared EARLY_CLOSES table), sleeves/muse/core/saty_bars.py, sleeves/muse/core/saty_indicators.py, sleeves/muse/core/saty_primitives.py, sleeves/muse/core/saty_reference.py.
- Config: engines/config/sleeves.json (row id=saty_sol_0dte), also at config/sleeves.json.
- Existing strategy doc (shared with the sibling variant, with a Variants table): strategies/muse/muse-saty-sol.md.

## Configuration
Module adapters3.saty_sol_0dte; cadence_s 60; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close true; flatten_time_et 15:55; params {}; inputs [bars, quotes, options, session_fills]; parked false. Universe: SPY options; timeframes 1m, 3m, 10m (and the completed 1h Phase Oscillator as a recorded tag). Source: muse-desk-v3/config/sleeves.json row id=saty_sol_0dte.

## Data inputs
Inputs are bars, quotes, options and session_fills. The existing doc's Data section names: SPY 5-minute bars (about 22,000) and 1-minute bars (1,200), IEX quotes, the SPY option chain and quotes, and the sleeve's own fills (fills feed the spent-premium and daily-loss reads).

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/desk3/enhance26.py is desk3/enhance26.py on a fresh desk; a sleeves/muse/core/ path is the same path on a fresh desk).
2. Register the config row for `saty_sol_0dte` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/saty_sol_0dte.py, whose evaluate(view, ctx) delegates to the sleeve module sleeves/saty_sol_0dte.py signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture opening with x < 0.382 followed by a first cross of 0.382 with the mark inside [0.382, 0.412] and the 0.618 target not yet printed: exactly one buy_to_open entry, contracts = floor(remaining $50 session budget / (100 x ask)); a second cross in the same session emits nothing.
- Fixture with a session that opens already beyond 0.382: no Golden Gate entry (no gap entries).
- Fixture with a held Golden Gate position and a mark at x >= 0.618: a full sell_to_close exit at the bid; with a 10-minute close at x < 0.236 after the fill: the same full exit.
- Fixture where the daily loss reaches 1 percent of the slice: no new entries for the session.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
