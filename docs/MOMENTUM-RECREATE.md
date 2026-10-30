# momentum: Recreation package

Provenance: Source row in strategies/femto/femto-momentum.md in this repo: The old Alpaca swing desk's momentum sleeve, via Femto-lean; Midna's TypeScript desk.

## What this sleeve is
This sleeve holds the top tenth of liquid names by 126-session return: it ranks the served universe on completed daily bars, reviews every 63 sessions, and holds at most 10 names within a 30% of equity sleeve cap. A 40% drop from entry closes a position on any pass.

## Full algorithm
Wrapper (desk3/port_b5/momentum.py): SLEEVE_ID = "momentum", INPUTS = ('bars', 'positions'), CADENCE_S = 300; evaluate() runs the strategy through the port_b5 ENH2 completed-bars layer (desk3/port_b5/_enh2.py, run_enh2): with the switch ON (extra["momentum_enh2"]["completed_bars"] or extra["enh2_completed_bars"], default ON) the strategy is served a copy of the view with every bar that cannot be completed at the cycle's now trimmed (a 1Day bar dated the current ET session, or an intraday bar whose span has not closed), and the untrimmed view is also evaluated in a throwaway state dir as a shadow control whose intents are never emitted. OFF serves the untrimmed view untouched.
Adapter glue (adapters/momentum.py, run via desk3/port_b5/_ctx.py): WARMUP_BARS = {"1Day": 127}; it fetches 300 1Day bars for the candidate symbols, derives sleeve_state from positions and extra["now_hm"] from ctx.now in ET, serves extra["vix"] = (last VIX close, prior close, as-of date, "cache") from 10 VIX / ^VIX daily bars when at least 2 rows exist, and translates the strategy intents.
Strategy (sleeves/momentum.py in the desk, desk3/vendor form core.sleeve): LOOKBACK = 126; REVIEW_EVERY = 63; TOP_FRAC = 0.10; MAX_POSITIONS = 10; SLEEVE_CAP = 0.30; MIN_PRICE = 5.0; MIN_DOLLAR_VOL = 1,000,000; SKIP_SYMBOLS = {SOXL}; BREAKER_DROP = 0.40; VIX_HIGH = 32.0; VIX_SPIKE = 0.25; SPY_DROP = -0.08; FOMC_2026 = the eight 2026 FOMC date pairs listed in the file (Jan 27-28, Mar 17-18, Apr 28-29, Jun 16-17, Jul 28-29, Sep 15-16, Oct 27-28, Dec 8-9). SleeveConfig: cadence_s=300, universe=(), state_schema={"position": "dict|None", "meta.last_review_spy_date": "str|None"}, risk_pct=None.
Ranking (compute_rank) on completed bars only (bar date < session): a symbol needs at least 127 completed bars to be ranked. Eligible: not SOXL, last completed close >= $5, 20-session mean dollar volume (mean of close x volume over the last 20 completed bars) >= $1,000,000, and a valid close 126 bars back. ret126 = last close / close 126 bars back - 1. The top set is the highest ret126 names, count = min(max(1, int(eligible x 0.10)), 10), and is empty unless at least 10 names are eligible (fail closed: an empty top set rotates and buys nothing).
Exits, in code order: (1) Circuit breaker, every pass, before everything: a held name whose last bar close <= entry_px x 0.60 exits the full qty (reason "momentum breaker"). (2) Rotation: the top-set sell test runs when extra["review_due"] is true (the core supplies it from the persisted last_review_spy_date, every 63 sessions) OR, under the ENH switch (extra["momentum_enhance"]["enabled"], default ON), on every pass while anything is held; a held name outside a non-empty current top set exits the full qty at the last close, except names already breaker-exiting. OFF restores review-only rotation.
New-buy gates (new_buy_gates; buys only, never sells), any one blocks all buys: Friday with ET time >= 14:00; today is one of the last 5 December weekdays of the year; FOMC blackout (the prior weekday session and both FOMC days, for the 2026 pairs above); VIX unknown (absent tuple or close None) fails closed; VIX as-of more than 4 calendar days before today (or unparseable) is stale; VIX close > 32; VIX up more than 25% on the day (close / prior close - 1 > 0.25); SPY 20-session return <= -8% (last completed close vs the close 21 bars back) while VIX is rising. Buys also require equity > 0 and a free slot (held < 10).
Buy sizing: budget = max(0, 0.30 x equity - held book notional), where held notional sums qty x (entry_px or ref_px or last close) over held names. Targets are the top-set names not already held, up to the free slots; per-name budget = budget / number of targets; all-in price = price x (1 + cost_bps(price)) with cost tiers 10 bps at price >= 20, 25 bps at >= 5, 50 bps below 5; qty = int(per-name // all-in); below 1 takes no position. The enter intent carries price_hint = round(price, 2) and a reason naming ret126, the 20-day dollar volume and the cost tier.

## Files in this repo
- Sleeve wrapper (desk desk3/port_b5/momentum.py): `desk3/port_b5/momentum.py`.
- Strategy (desk sleeves/momentum.py): `sleeves/momentum.py`.
- Adapter glue (desk adapters/momentum.py): `adapters/momentum.py` (repo path as in the existing card's code list; the v3 run path is desk3/port_b5/_ctx.py, below).
- ENH2 completed-bars layer: `engines/desk3/port_b5/_enh2.py` (desk desk3/port_b5/_enh2.py).
- Port context runner: `engines/desk3/port_b5/_ctx.py` (desk desk3/port_b5/_ctx.py).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py`.
- Existing per-sleeve card: strategies/femto/femto-momentum.md (the old swing desk / Femto-lean variant row).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars, positions.

## Data inputs
- The wrapper's evaluate(view, ctx) runs the strategy through desk3/port_b5/_ctx.py's run (the v2 adapter body in adapters/momentum.py) and then the ENH2 completed-bars layer in desk3/port_b5/_enh2.py.
- context.extra["sleeve_state"], ["vix"] (adapter-served tuple), ["review_due"] (core-supplied from the persisted last review date), ["now_hm"], and the optional ["universe"] override (default: the bars keys). Bars are daily dicts ascending; the strategy itself treats only bars dated before the session as completed.

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `momentum` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check completed-bar law: a bar dated the current session is excluded from ranking, pricing and the breaker, both by the strategy's own last_completed filter and (with ENH2 ON) by the wrapper trim.
- Check eligibility: close $4.99, 20-day mean dollar volume $999,999, SOXL, and 126 completed bars each exclude a name; with only 9 eligible names the top set is empty and nothing is bought or rotated.
- Check ranking: ret126 uses the close 126 completed bars back, and the top count is min(max(1, int(eligible x 0.10)), 10).
- Check the breaker: a close exactly at entry x 0.60 exits; one cent above does not; the breaker fires even when every buy gate is closed.
- Check rotation: with review_due false and the ENH switch ON, a held name outside a non-empty top set still exits; with the switch OFF it holds until a due review; an empty top set sells nothing in either mode.
- Check each buy gate in isolation: Friday 14:00 ET, a last-5-December weekday, an FOMC blackout day and its prior weekday, missing VIX, VIX as-of 5 days old, VIX 33, VIX +26% on the day, and SPY -8% over 20 sessions with VIX rising.
- Check sizing: budget is 30% of equity minus held notional, split evenly over the actual targets, with the cost tier for the name's price added before flooring; a per-name budget that buys less than 1 share takes no position.
