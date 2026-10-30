# leaps_momentum: Recreation package

Provenance: Source row in strategies/femto/femto-leaps-momentum.md in this repo: The old Alpaca swing desk, via Femto-lean.

## What this sleeve is
This sleeve mirrors the momentum sleeve's live book with deep in-the-money LEAPS calls (a poor man's covered call): one LEAPS position per momentum name, plus a short ~25-delta monthly call sold against each LEAPS. It exits a LEAPS when its name rotates out of the momentum book, at 60 DTE, or at a 30% premium loss.

## Full algorithm
Strategy (desk3/vendor/sleeves/leaps_momentum.py): MIN_DTE = 365; LEAPS_DTE_FLOOR = 60; LEAPS_STOP_FRAC = 0.30; PMCC_SHORT_DELTA = 0.25; PMCC DTE window 25-38; PMCC_ROLL_DTE = 21; PMCC_TEST_FRAC = 0.03; SPREAD_GATE_FRAC = 0.05; MAX_POSITIONS = 8; LEAPS_NOTIONAL_CAP = 0.05; MOMENTUM_BOOK_MAX_AGE_DAYS = 7; LEAPS_STRIKE_FRAC = 0.80. SleeveConfig: cadence_s=300, universe=(), state_schema={"position": "dict|None", "pmcc_short": "dict|None"}, risk_pct=0.05.
Adapter (desk3/sleeves/leaps_momentum.py): INPUTS = ('bars:*:1Day', 'options:chains', 'positions', 'journal:momentum'); WARMUP_BARS = {"1Day": 31}. It fetches 60 daily bars for the candidate symbols, derives sleeve_state, reads the momentum sleeve's own journal (the sibling momentum/journal.jsonl) for its open book {symbol: {qty}} and the age in days of its newest fill, serving them as extra["momentum_book"] and ["momentum_book_age_days"], merges each symbol's options chain (chains / quotes) into extra, and after translation fixes sides: an entry whose reason names pmcc_short is a sell, an exit whose reason names pmcc_roll is a buy.
Book freshness: the book is fresh only when it is present, its age is readable, and age <= 7 days; a stale or unreadable book blocks entries AND disables rotation exits (the fossil must not fire exits).
LEAPS exits (leaps_exit_due, in this order) for a held position with qty > 0: (1) the symbol is not in a fresh momentum book (momentum_rotation_out); (2) DTE to the position's expiry <= 60 (dte_floor_60); (3) the mid from extra["quotes"] for the position's OCC is <= entry_premium x 0.70 (stop_minus30pct). The exit intent is on the underlying at the last daily close.
PMCC management for a held LEAPS with no exit due: if a pmcc_short record exists, roll it (an exit intent for the short) when its expiry is <= 21 DTE away or spot >= short strike x 0.97 (pmcc_roll_dte_21 / pmcc_tested_within_3pct), and do nothing else that pass. If no short exists and spot > 0, select a new short: realized vol = the annualized standard deviation of log returns over the last 31 closes (needs at least 21 closes, all positive); target = max(spot x (1 + 0.67 x vol x sqrt(30/365)), (LEAPS strike + LEAPS entry premium) x 1.02); from the nearest expiry in 25-38 DTE take the first strike >= target whose quote passes the two-sided 5% gate (bid > 0, ask > 0, ask >= bid, (ask-bid)/mid <= 0.05); emit an enter intent for the same qty as the LEAPS at the spot price_hint, reason naming pmcc_short, the OCC, strike, expiry, DTE and bid. An orphaned pmcc_short with no LEAPS position is closed with an exit intent on first evaluation (orphaned_short_close).
Entries (mirror a fresh book only; equity > 0 and open positions < 8 required): for each momentum-book symbol not held, with momentum qty and spot > 0: find the LEAPS contract: the nearest expiry >= 365 DTE; strikes ordered nearest to 0.80 x spot; with the ENH strike-walk switch (extra["leaps_momentum_enhance"]["enabled"], default ON) walk those strikes nearest-first and take the first passing the 5% quote gate, with the switch OFF only the single nearest strike is tried. Contracts = int(momentum shares // 100), capped at int((equity x 0.05) / (ask x 100)); below 1 contract skips (no 1-contract floor). Emit an enter intent on the underlying, qty_hint = contracts, price_hint = round(spot, 2), reason naming the OCC, strike, expiry, ask, momentum qty and the strike rule nearest(0.80*spot) with min_dte=365.

## Files in this repo
- Sleeve module (desk desk3/sleeves/leaps_momentum.py): `desk3/sleeves/leaps_momentum.py`.
- Strategy (desk desk3/vendor/sleeves/leaps_momentum.py, byte-identical vendored copy loaded by load_strategy): `sleeves/leaps_momentum.py`.
- Shared bridge: `engines/desk3/port4_bridge.py` (desk desk3/port4_bridge.py).
- Snapshot context: `engines/desk3/port4_context.py` (desk desk3/port4_context.py: evaluate_via and load_strategy).
- Journal runtime used by the adapter to serve and file leader_last_event records: `engines/desk3/vendor/runtime/journal.py` (desk desk3/vendor/runtime/journal.py).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from core.sleeve).
- Existing per-sleeve card: strategies/femto/femto-leaps-momentum.md.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars:*:1Day, options:chains, positions, journal:momentum.

## Data inputs
- The adapter's evaluate(view, ctx) runs through desk3/port4_context.evaluate_via, which serves the snapshot inputs declared in the module INPUTS tuple into an old-style context; the strategy then reads context.extra, context.equity, context.session and context.now.
- Bars are fetched through the port4 bridge from the snapshot bar cache at the sizes stated per sleeve in the Full algorithm section; positions arrive as the snapshot positions, from which the bridge derives held quantities and sleeve_state.
- context.extra["momentum_book"] and ["momentum_book_age_days"] from the momentum sleeve's journal (adapter-served, above); ["chains"] {symbol: [call contracts]} and ["quotes"] {OCC: {bid, ask}} merged from the options product; ["sleeve_state"] including each symbol's pmcc_short record. Daily bars (60 fetched) give spot and the 30-day realized-vol closes.

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `leaps_momentum` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check book freshness: age 7 days exactly is fresh, 8 days and an unreadable age are stale; a stale book produces no entries and no rotation exits, while the 60-DTE and 30% premium exits still evaluate.
- Check LEAPS selection: the expiry is the nearest at >= 365 DTE and, with the walk ON, the first strike nearest 0.80 x spot that passes the 5% quote gate is taken (a failing nearest strike falls through to the next), while with the walk OFF a failing nearest strike yields no entry.
- Check sizing: 250 momentum shares and ask 10.00 on equity 100,000 give min(2, int(5000 / 1000)) = 2 contracts; 99 shares give 0 and no entry.
- Check exit precedence: rotation out before the 60-DTE floor before the 30% premium stop (mid exactly 0.70 x entry premium fires).
- Check the PMCC target: it is never below (LEAPS strike + entry premium) x 1.02, the short is the first strike >= target in the nearest 25-38 DTE expiry, and rolls fire at 21 DTE or when spot reaches 97% of the short strike.
- Check an orphaned short (pmcc_short record, no LEAPS position) is closed on the first evaluation.
