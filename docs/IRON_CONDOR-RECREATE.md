# iron_condor: Recreation package

Provenance: Source row in strategies/femto/femto-iron-condor.md in this repo: The old Alpaca swing desk, via Femto-lean.

## What this sleeve is
This sleeve sells high-IV iron condors on a fixed 13-name high-volatility watchlist: 16-delta shorts with 5-delta wings, 30-45 days to expiry, only when IV rank is at least 50, VIX is at most 35 and no earnings are due within 45 days. It exits at half the credit, at a loss stop, at 7 DTE, or after 21 days.

## Full algorithm
Strategy (desk3/vendor/sleeves/iron_condor.py): WATCHLIST = (ARQQ, NBIS, WYFI, AEHR, POET, HIVE, SNDK, IREN, CORZ, ARM, AXTI, DGXX, VELO); RISK_FREE = 0.04; IV_RANK_MIN = 50.0; DTE window 30-45; SHORT_DELTA = 0.16; WING_DELTA = 0.05; PROFIT_TARGET_PCT = 0.50; STOP_MULT = 2.0; EXIT_DTE = 7; RISK_FRACTION = 0.01; MAX_POSITIONS = 3; EARNINGS_CLEAR_DAYS = 45; SPREAD_GATE_FRAC = 0.10; VIX_MAX = 35.0; MAX_CONTRACTS_PER_CONDOR = 25; MAX_HOLD_DAYS = 21; IV_RANK_COLD_START_MIN = 60; IV_RANK_WINDOW = 252; GATE_EXEMPT_DECISION75 = True (a net-credit sale, exempt from the red-day / chart-gate staging, recorded in every entry reason). SleeveConfig: cadence_s=300, universe=WATCHLIST, state_schema={"position": "dict|None"}, risk_pct=0.01.
Adapter (desk3/sleeves/iron_condor.py): INPUTS = ('bars:*:1Day', 'bars:VIX:1Day', 'options:chains', 'earnings', 'iv'); WARMUP_BARS = {"1Day": 30}. It fetches 60 daily bars for the watchlist, merges each symbol's options chain payload (chains / quotes dicts) into the derived extra, serves extra["vix"] as (last close, prior close, date, "cache") from VIX daily bars when not already served, derives earnings_in_days from the earnings calendar, and serves iv / iv_history from the IV ledger. After the strategy returns, the adapter fans each entry intent whose reason carries the four OCC legs out into 4 per-leg intents (put short sell_to_open, put long buy_to_open, call short sell_to_open, call long buy_to_open; intent ids suffixed -1..-4, each carrying the condor map {put_short_occ, put_long_occ, call_short_occ, call_long_occ, width, expiry}, the entry credit and the original package_id).
Entries, per watchlist symbol in order, when open condors < 3 and equity > 0 and bars exist: (1) VIX gate: extra["vix"] must be present and <= 35; absent or above fails closed for that symbol. (2) IV rank: TRUE rank = (current IV - min) / (max - min) x 100 over the last 252 stored IV readings for that symbol; fewer than 60 stored readings is a cold start and pauses entry; entry requires rank > 50 (the code tests rank <= 50 as a skip, so exactly 50 does not enter). (3) Earnings: extra["earnings_in_days"][symbol] must be present and > 45; unknown or <= 45 fails closed. (4) build_condor over extra["chains"][symbol] with spot = last daily close and the symbol's current IV: per side (put, call), among tradable contracts take the nearest expiry with 30 <= DTE <= 45; the short is the strike whose |Black-Scholes delta| (risk-free 0.04, T = DTE/365) is nearest 0.16; the wing is the strike beyond the short (below for puts, above for calls) whose |delta| is nearest 0.05. Both sides must share the same expiry, else fail closed. All four legs need two-sided quotes (bid > 0, ask >= bid) with (ask-bid)/mid <= 0.10. Net credit = short bids - long asks summed over both sides, and must be > 0. Width = the wider of the put and call wing widths; max_loss = (width - credit) x 100, must be > 0. (5) Quantity = min(int((equity x 0.01) // max_loss), 25); below 1 skips. The entry intent is on the underlying symbol with price_hint = round(spot, 2) and a reason carrying all four OCC legs and strikes, expiry, DTE, credit, max_loss, width, IV rank and the gate-exemption note; the adapter then fans it out as described above.
Exits, per held symbol (quantity taken as abs(qty), because a condor fill books negative qty): close cost = buy the shorts at ask minus sell the longs at bid from extra["quotes"]; a long wing bidding 0 is worthless, not unquotable, while a missing quote or an unpriceable short leg makes the cost uncomputable (quote-based exits then cannot fire, but the DTE and hold exits still evaluate). exit_due order: profit when credit - close_cost >= 0.50 x credit (profit_target_50pct); loss when close_cost - credit >= the stop threshold (stop_2x_premium, or with the ENH switch extra["iron_condor_enhance"]["enabled"] default ON, the smaller of 2 x credit and 0.5 x (width - credit), named stop_half_max_loss when the half-max-loss leg binds); then DTE <= 7 (dte_time_stop_7); then at least 21 bar-calendar sessions since entry_date (max_hold_21d). The exit intent is on the underlying at the last close with a reason naming the exit rule, close cost and the four leg OCCs.

## Files in this repo
- Sleeve module (desk desk3/sleeves/iron_condor.py): `desk3/sleeves/iron_condor.py`.
- Strategy (desk desk3/vendor/sleeves/iron_condor.py, byte-identical vendored copy loaded by load_strategy): `sleeves/iron_condor.py`.
- Shared bridge: `engines/desk3/port4_bridge.py` (desk desk3/port4_bridge.py).
- Snapshot context: `engines/desk3/port4_context.py` (desk desk3/port4_context.py: evaluate_via and load_strategy).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from core.sleeve).
- Existing per-sleeve card: strategies/femto/femto-iron-condor.md.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars:*:1Day, bars:VIX:1Day, options:chains, earnings, iv.

## Data inputs
- The adapter's evaluate(view, ctx) runs through desk3/port4_context.evaluate_via, which serves the snapshot inputs declared in the module INPUTS tuple into an old-style context; the strategy then reads context.extra, context.equity, context.session and context.now.
- Bars are fetched through the port4 bridge from the snapshot bar cache at the sizes stated per sleeve in the Full algorithm section; positions arrive as the snapshot positions, from which the bridge derives held quantities and sleeve_state.
- context.extra["chains"] {symbol: {"put": [contracts], "call": [contracts]}} with {symbol, strike, expiration}; ["quotes"] {OCC: {bid, ask}}; ["iv"] {symbol: current IV}; ["iv_history"] {symbol: [stored readings]}; ["earnings_in_days"] {symbol: int or None}; ["vix"]; ["sleeve_state"] — all served by the adapter as stated in the Full algorithm section. Spot is the last daily close (60 bars fetched).

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `iron_condor` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the entry gates in isolation: VIX absent and VIX 36 each block; IV history of 59 readings blocks (cold start); rank exactly 50 blocks and 51 passes the gate; earnings_in_days of 45 blocks, 46 passes, and missing blocks.
- Check construction: shorts are the strikes nearest |delta| 0.16 and wings nearest 0.05 beyond them on the nearest 30-45 DTE expiry; mismatched put/call expiries, a leg spread above 10% of mid, and credit <= 0 each fail closed.
- Check max loss uses the wider wing: max_loss = (max(put width, call width) - credit) x 100, and quantity = min(int(equity x 0.01 // max_loss), 25).
- Check the adapter fan-out: one strategy entry becomes exactly 4 leg intents with position intents sell/buy/sell/buy in put-short, put-long, call-short, call-long order, all carrying the same condor map, credit and package_id.
- Check exit precedence: profit target before the loss stop, the loss stop before the 7-DTE stop, and the 7-DTE stop before the 21-session hold; with the ENH switch ON a credit of at least width/3 stops at half the max loss per share instead of 2 x credit.
- Check a held condor whose long wing bids 0 still computes a close cost, while a missing short-leg quote blocks only the quote-based exits.
