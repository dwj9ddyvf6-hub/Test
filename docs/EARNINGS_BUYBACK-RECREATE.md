# earnings_buyback: Recreation package

Provenance: Source row in strategies/femto/femto-earnings-buyback.md in this repo: Quantpedia #0271 (Amini & Singal, buybacks before earnings); the old swing desk, via Femto-lean (family Femto-lean, asset equity options, timeframe 1d (hourly checks), universe 73 basket and phase names, style event drift (options)).

## What this sleeve is
This sleeve buys a defined-risk call debit spread (or a long-call fallback) 8 to 15 days before earnings on a stock that announced a buyback of at least 5 percent of its shares 15 to 30 days before the report, and holds through the event to 15 trading days after earnings. Its defined-risk structures are exempt from the desk's no-holding-through-earnings rule by the decision recorded in the module header. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/earnings_buyback.py signal(bars, slice_state, context), with entry filtering through desk3/enhance14.py in the adapter path.

## Full algorithm
Constants (sleeves/earnings_buyback.py): BUYBACK_MIN_PCT = 5.0, DTE_FLOOR = 5, MIN_STOCK_PRICE = 10.0, EXIT_TRADING_DAYS_AFTER_EARNINGS = 15, SPREAD_WIDTH_PCT = 0.10, DEBIT_RANGE = (0.30, 0.45), RISK_FRACTION = 0.005, MAX_POSITIONS = 4, MAX_SAME_SECTOR = 2, PROFIT_TARGET_FRAC = 0.50, STOP_FRAC = 0.50, SCAN_MAX_AGE_DAYS = 8, LONG_CALL_OTM_PCT = 0.02, MIN_DAYS_EXPIRY_AFTER_EARNINGS = 26 (the enhancement value; see below). CONFIG: cadence_s 300, universe (), risk_pct RISK_FRACTION.

Qualification and entries, in code order:
1. Scan freshness: scan rows arrive via extra["scan_signals"] (parsed from the latest buyback_scan file) and extra["scan_age_days"] gates freshness here fail-closed: a scan older than SCAN_MAX_AGE_DAYS = 8 days is stale and produces no entries. The card notes SEC requests stay off until a contact is set, so the scan has no fresh input until then.
2. Signal qualification (qualify_signal): an 8-K repurchase announcement of at least BUYBACK_MIN_PCT = 5 percent of shares, filed 15 to 30 calendar days before the earnings date; entry only inside T-15 to T-8 days before earnings on a fresh calendar; the stock price must be at least MIN_STOCK_PRICE = $10.
3. Capacity: at most MAX_POSITIONS = 4 positions and MAX_SAME_SECTOR = 2 per sector.
4. Expiry gate: candidate expiries are filtered to 30 to 45 DTE and must expire strictly after earnings (expiry_after_earnings); with the enhancement on (ENH-EARNINGS-BUYBACK-20261024, switch in extra, default ON) the expiry must be at least MIN_DAYS_EXPIRY_AFTER_EARNINGS = 26 days after earnings (expiry_gap_ok; the module comment derives 26 as 21 calendar days for T+15 trading days plus the 5-DTE floor).
5. Structure (build_trade, select_debit_spread first): the nearest 30 to 45 DTE expiry; long leg = the highest strike at or below spot; short leg = the first strike at or above long strike x 1.10 (SPREAD_WIDTH_PCT = 0.10); the long-leg quote gate is 10 percent spread; the debit must lie inside DEBIT_RANGE = 30 to 45 percent of the width. Fallback (select_long_call): a single call at least LONG_CALL_OTM_PCT = 2 percent out of the money with a spread gate of 15 percent per the card, expiring after earnings under the same expiry gate.
6. Sizing: RISK_FRACTION = 0.5 percent of the book in debit per trade.

Exits (exit_due, first trigger wins): EXIT_TRADING_DAYS_AFTER_EARNINGS = 15 trading days after earnings (trading_days_since_earnings); profit at +50 percent of the debit (PROFIT_TARGET_FRAC = 0.50); stop at -50 percent of the debit (STOP_FRAC = 0.50); or DTE_FLOOR = 5 days to expiry per the card's exit summary.

Position management: at most 4 positions, at most 2 per sector, held through earnings by design (the exemption above), no pyramiding.

## Files in this repo
- Sleeve module (desk sleeves/earnings_buyback.py): `sleeves/earnings_buyback.py`.
- v3 adapter (desk adapters3/earnings_buyback.py): `adapters3/earnings_buyback.py`; also present as `integration/earnings_buyback_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py; named in the audit record as a shared dependency).
- Shared entry filter in the adapter delegation path: `engines/desk3/enhance14.py` (desk source desk3/enhance14.py, vendored in this repo per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/femto/femto-earnings-buyback.md`.

## Configuration
- Universe: 73 basket and phase names (served as scan and bars keys; CONFIG universe is ()). Asset: equity options (call debit spreads, long-call fallback). Timeframe: 1d with hourly checks per the card.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk_pct 0.005 in CONFIG (0.5 percent of the book in debit per trade).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions, options, earnings, buyback_scan.

## Data inputs
- scan_signals and scan_age_days: context.extra rows parsed from the latest buyback_scan_*.json (producer: the weekday EDGAR 8-K buyback scan) and its age in days; older than 8 days fails closed.
- earnings: the earnings calendar (dates per symbol) for the T-15..T-8 window, the filing-to-earnings gap and the T+15 exit count.
- options: 30 to 45 DTE call chains with bid/ask quotes for the spread and fallback selection; bars for spot; the sector map for the 2-per-sector cap.

## Install and run
1. Place the sleeve module at sleeves/earnings_buyback.py and the adapter at adapters3/earnings_buyback.py (repo copies at the same paths). The adapter uses evaluate_ported from the snapshot glue and the shared filter at desk3/enhance14.py (repo copy at engines/desk3/enhance14.py).
2. Register the roster row for `earnings_buyback` exactly as in the Configuration section in config/sleeves.json (module adapters3.earnings_buyback).
3. Wire the producers so every snapshot carries: daily bars, the earnings calendar, call chains and quotes, this sleeve's positions, and extra scan_signals with scan_age_days from the EDGAR buyback scan.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch2_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check qualification: a buyback under 5 percent, a filing outside 15 to 30 days before earnings, an entry day outside T-15 to T-8, a stock under $10, or a scan older than 8 days each produce no entry.
- Check the structure: the long leg is the highest strike at or below spot, the short leg the first at or above long x 1.10, a debit outside 30 to 45 percent of width falls back or refuses per the module, and every expiry is strictly after earnings (at least 26 days after with the enhancement on).
- Check capacity and sizing: the 5th position or a 3rd position in one sector is refused, and debit per trade is at most 0.5 percent of the book.
- Check exits: 15 trading days after earnings, +50 percent or -50 percent on the debit, or 5 days to expiry each close the position, and the position is NOT closed by the desk earnings blackout before then.
