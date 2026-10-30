# aster_rec_vwap20_long_fixed_a: Recreation package

Provenance: Source row in strategies/ausar/opt-recovery.md in this repo: Ausar R17/R18 options research (family Ausar, asset ETF options, timeframe 1d, universe IWM, QQQ, SPY, style mean reversion). The desk adapter header states Aster batch 3, engine desk3/aster_batch3.py.

## What this sleeve is
This sleeve buys a single-leg long call on IWM, QQQ or SPY after a VWAP20 recovery dip in a long-term uptrend, with a fixed exit rule and the A tier, risk budget $200.00 on the $10,000 slice sizing. It is a thin adapter in adapters3/ whose evaluate(view, ctx) delegates to desk3/aster_batch3.py evaluate(SLEEVE_ID, view, ctx). It implements no strategy math of its own; all rules below are the batch-3 engine rules as applied to this sleeve's own book.

## Full algorithm
This sleeve's book and SPECS entry (desk3/aster_batch3.py): book="OPT_VWAP20_LONG_FIXED_A", family="recovery", signal="VWAP20", structure="long", exit_rule="fixed", risk_fraction=0.02, max_debit_width=0.6, max_premium_spot=0.025, dte=(14, 21), delta=(0.5, 0.6), hold_sessions=5. Slice constant SLICE_USD = 10000.0. A tier, risk budget $200.00 on the $10,000 slice.

Exits, evaluated first (engine _exit_intents), for each held position carrying legs in its metadata or directly, with qty > 0:
1. European style only: if the first leg's exercise_style is european and the calendar session is at or after expiry and the expiry close time is known and now is at or after it, the exit is due as a settlement, reason `official_PM_expiry`, action settle (no price is computed).
2. Otherwise the planned exit is computed first: due when the session-exit test for the metadata exit_session (falling back to the leg expiry) passes, where that test is true on any date after the exit session, and on the exit session itself from 5 minutes before that session's option close (the close must be known from the calendar, otherwise the test raises and due stays false); reason `planned_session_exit`. The exit session stored at entry is the 5th session counting the entry session as session 1 (see the entry rule below).
3. Pre-expiry guard: if the previous session before expiry (from the calendar previous_session_by_date, or the metadata expiry_exit_session) passes the same session-exit test at 15 minutes before its close, the exit is due with reason `pre_expiry_obligation_exit`, overriding the planned reason.
4. Verified assignment alert: if the exercise/assignment check for the leg underlying has assignment_alert true, verified exactly True, a source_sha256 present, and received_at at or before now, the exit is due, reason `assignment_risk_exit_or_lifecycle_obligation`.
5. No touch exit: this sleeve's exit_rule is fixed, so the touch rule in the engine does not apply.
A due non-settlement exit is priced from current OPRA quotes: each leg quote must be fresh (feed opra, at most 10 seconds old), displayed size on the closing side must be at least the held qty, and leg quote market times must span at most 2 seconds; if any of that fails the due exit emits nothing in this engine (no fake price). The closing package price pays bid for ratio > 0 legs and ask for ratio < 0 legs, times ratio x 100. Exit intents are sell_to_close, time_in_force day, full qty, price_hint = the rounded closing package price, exit_action close (or settle). Mid-limit enhancement (ENH-ASTERB3-MIDLIMIT-20261024, recovery family only, on by default; switch extra["enh_aster_rec_vwap20_long_fixed_a"] or extra["aster_b3_enh"] {"mid_limit": bool}): when every leg has a quote with ask >= bid > 0, the exit becomes a limit order at round(mid package price / 100, 2) when that mid price is positive, with a paired shadow record. If any exit intent is produced, entries are not evaluated.

Entries, in code order:
1. One package per book: if any position carrying legs exists (the engine _positions filter), return no entry.
2. Market-open gate: extra market_open, when present, must be exactly True; absent means open.
3. Entry window: now in ET must satisfy 09:35 <= time < 09:40.
4. Signal, for each symbol in UNIVERSE = (IWM, QQQ, SPY) in order: read daily bars (keys `<sym>`, `<sym>|1Day`, `<sym>|1d`, `<sym>|1D`). recovery_signal requires at least 200 rows and uses the last 200; it raises (and the symbol is skipped) when any row has usable_after after now, complete not exactly True, duplicate or non-chronological sessions, invalid OHLCV (not 0 < low <= close <= high, or volume < 0), or a non-finite value. SMA200 is the mean of the 200 closes. VWAP20 arm: value = the 20-session VWAP of typical price (H+L+C)/3 over the last 20 rows, volume-weighted (zero total volume in those 20 rows raises and fails the symbol); the signal passes only when last close > SMA200 and last close <= value x 0.98. When the calendar previous_session is present, the signal session (the last row's session) must equal it, otherwise the symbol is skipped.
5. Contract selection for the first passing symbol that yields an intent (calls only): spot is the midpoint of a fresh underlying quote (feed sip, at most 5 seconds old, symbol matching). Chain rows for the symbol with right = call, DTE between 14 and 21 inclusive, absolute delta between 0.5 and 0.6 inclusive, and greeks at most 10 seconds old (greeks_market_at <= greeks_received_at <= now) are candidates. The long leg is the minimum by (expiry, absolute delta minus the band midpoint 0.55, absolute strike minus spot, symbol).
6. Package pricing and caps: opening package price (per package, x 100) pays ask for ratio > 0 legs and bid for ratio < 0 legs, from OPRA quotes fresh to 10 seconds with leg market times spanning at most 2 seconds. Long cap: refuse when package debit / (spot x 100) > max_premium_spot = 0.025. max_debit_width = 0.6 is recorded in the book but is applied only to vertical structures in this engine.
7. Fees: the fee total is the snapshot fee schedule per_contract_per_fill (from extra option_fees or options fees) times the number of legs when that schedule is present; otherwise the fallback is package debit x 0.0015 in total. Per-package cost = debit + fees.
8. Sizing: risk = min(slice equity x risk_fraction, slice equity x 0.05 minus outstanding max loss, slice cash), where slice equity and cash come from view slice capital_usd / cash_usd (each falling back to 10000.0) and outstanding max loss sums metadata max_loss_per_package x qty over held leg positions. Quantity = floor(risk / per-package cost), then capped by displayed size on every leg (ask_size for ratio > 0, bid_size for ratio < 0). Quantity below 1 refuses.
9. Entry intent: a package symbol `PKG:` plus the first 24 hex characters of the SHA-256 of the book, signal id and leg symbols; market buy, time_in_force day, buy_to_open, full computed qty, price_hint = the package debit, legs and metadata (rule_id = book, risk_budget, entry_spot = spot, entry_session, exit_session = the 5th session from the calendar future_sessions list whose first entry must be the entry session, expiry_exit_session, held_sessions = 5, exit_rule = "fixed", signal_id = `<book>:<sym>:<signal_session>`, per_leg_fee, max_loss_per_package = per-package cost). Mid-limit enhancement (same switch as exits, on by default, recovery family): when leg quote mids are computable, the entry becomes a limit order at round(mid package debit / 100, 2) when positive, with a paired shadow record.

Position management: one options package at a time, no pyramiding, no averaging, and no price stop in this engine beyond the exit rules above. The engine header states no v3 producer emits OPRA chains yet, so in the live registry these sleeves are unfed by name, never fed invented data.

## Files in this repo
- Sleeve adapter (desk adapters3/aster_rec_vwap20_long_fixed_a.py): `adapters3/aster_rec_vwap20_long_fixed_a.py`; also present as `sleeves/aster_rec_vwap20_long_fixed_a.py` and `integration/aster_rec_vwap20_long_fixed_a_adapter.py`.
- Shared engine: `desk3/aster_batch3.py` (desk source desk3/aster_batch3.py, SPECS entry for `aster_rec_vwap20_long_fixed_a`).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/ausar/opt-recovery.md`.

## Configuration
- Universe: IWM, QQQ, SPY in that order. Asset: ETF call options (long). Timeframe: 1d bars for the signal; entry window 09:35 to 09:40 ET.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk fraction 0.02 in the engine book (see the Full algorithm sizing rule).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row (all parameters live in the engine book).
- Parked: false.
- Roster inputs: bars, options_chain, quotes, positions.

## Data inputs
- bars: view["bars"], at least 200 completed daily sessions per symbol with session, usable_after, complete, o, h, l, c, v. Producer: bars, freshness SLA 3600 seconds (engine PRODUCERS in desk3/aster_batch3.py).
- options_chain and options_quotes: view["options_chain"] keyed by symbol (chain rows with right, expiry, delta, strike, symbol and greeks timestamps) and view["options_quotes"] keyed by OCC symbol (bid, ask, sizes, feed opra, market_at, received_at). Producer: options_chain, freshness SLA 900 seconds.
- quotes: view["quotes"] keyed by underlying symbol (bid, ask, feed sip, market_at, received_at) for spot and, where applicable, the touch test. Producer: quotes, freshness SLA 60 seconds.
- positions: view["positions"] rows with symbol, qty and legs (directly or in metadata, with entry_spot, exit_session, expiry_exit_session and max_loss_per_package in metadata). Producer: broker_readback, freshness SLA 900 seconds.
- Calendar and extras: view calendar (previous_session, future_sessions, option_close_by_date, previous_session_by_date, session) and view extra (market_open, option_fees, exercise_checks or assignment_alerts).

## Install and run
1. Place the engine at desk3/aster_batch3.py in the fresh desk (repo copy at the same path) and the adapter at adapters3/aster_rec_vwap20_long_fixed_a.py with SLEEVE_ID = "aster_rec_vwap20_long_fixed_a".
2. Register the roster row for `aster_rec_vwap20_long_fixed_a` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_rec_vwap20_long_fixed_a, cadence 300, session rth, $10,000 slice, inputs bars/options_chain/quotes/positions).
3. Wire the producers so every snapshot carries at least 200 completed daily bars per universe symbol, the OPRA options chain and quotes, underlying SIP quotes, positions, a calendar with previous and future sessions, and a timezone-aware now.
4. First evaluation: call evaluate(view, ctx) on the adapter; it calls desk3.aster_batch3.evaluate("aster_rec_vwap20_long_fixed_a", view, ctx). Confirm a snapshot outside 09:35 to 09:40 ET, with incomplete bars, a signal session other than the previous session, or a package already held returns no entry, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check bar validation: fewer than 200 rows, an incomplete or not-yet-usable bar, duplicate sessions, or invalid OHLCV each produce no entry for that symbol.
- Check the VWAP20 signal: last close at or below SMA200 fails; last close above 0.98 x VWAP20 fails, and zero volume in the last 20 sessions fails; a signal session other than the calendar previous session is skipped.
- Check symbol order and the one-package rule: the first passing symbol in IWM, QQQ, SPY order wins, and any held leg package blocks all entries.
- Check contract selection: greeks older than 10 seconds, DTE outside 14 to 21, or absolute delta outside 0.5 to 0.6 excludes a contract; earliest expiry wins, then delta nearest 0.55, then strike nearest spot.
- Check caps and sizing: package debit / (spot x 100) above 0.025 produces no entry; quantity equals floor(min(equity x 0.02, equity x 0.05 minus outstanding, cash) / (debit + fees)), capped by displayed size on every leg.
- Check exits: the planned exit is due from 5 minutes before the close of the 5th session counting entry as session 1; the pre-expiry guard fires 15 minutes before the close of the session before expiry; an unpriceable due exit emits nothing; there is no touch exit for this fixed book; the mid-limit enhancement converts priced entries and exits to limit orders at the package mid when its switch is on.
