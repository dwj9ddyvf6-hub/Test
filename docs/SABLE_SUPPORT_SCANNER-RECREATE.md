# sable-support-scanner: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Support scanner (5-minute)", type mean reversion, family sable, style "Support bounce", universe "Sable catalog: 488 stocks", asset class US equities, timeframe 5m, creator "Sable / Autopilot desk, the legacy completed-bar support scanner". Algorithm grade PARTIAL in the accounting, with gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card, which is a consulted source in this repo (see Files).
- Test catalog entry `sable-support-scanner` (`docs/CATALOG.json`): status live (1), card `strategies/sable/sable-support-scanner.md`, master-desk row `sable_support_scanner`.
- Alias: `sable_support_scanner`.

## What this strategy is

Buys a stock holding its completed 5-minute swing support, not stretched and with momentum intact. It is a support-bounce scanner over the 488-stock Sable catalog, evaluated on completed regular-hours 5-minute bars.

## Full algorithm

Evaluation order, from `strategies/sable/sable-support-scanner.md` (the card) and the code in Files:

1. Deep list construction: held names, the last scan's buy-side names, SPY / QQQ / IWM, then the best spark screen scores (near the 52-week or day low, down on the day) up to 36 names.
2. Per-name quote: from the last 5 sessions' completed regular-hours 5-minute bars compute support = the 64-bar low, ATR(14), RSI(14), the 12 / 26 EMA gap, VWAP; with the spark's 52-week range.
3. SETUP (buy) condition: price >= 99.5% of support and <= 1.6 ATR above it, RSI 38-68, EMA gap >= -0.15, below 88% of the 52-week range; stocks only.
4. Hands: the first 6 buy-side rows, SETUPs first by score (improving momentum, a tight range, volume and the lowest 30% of the 52-week range add points).
5. Entry execution: buy each SETUP hand not held, not sold in the last 8 hours, while under 6 positions (working buys count), in the regular session; free slots fill in the catalog's order. Orders: marketable limits (1% through the quote), good for an hour; a working buy is cancelled once its name leaves the hands.
6. Exit, checked every 5 minutes: stop at fill - 1.6 x ATR, target at fill + 2.8 x ATR (5-minute ATR(14), at least 1.5% of the fill: -2.4% / +4.2% at that floor). Breakeven at +1R: once the stop is moved to the entry price, it stays there.
7. Time stop: after 15 days if the position is not in profit.
8. Notes recorded on the card: no earnings filter (the 5-minute quotes carry no earnings flag); Tensor reads are not supplied, so the source's Tensor SELL veto and score badges are off.

Gaps: the accounting graded this PARTIAL because its own consulted sources held no entry/exit/sizing text; the card in this repo does hold them, as above. Anything beyond the card and code is not in the record.

## Files in this repo

- This doc: `docs/SABLE_SUPPORT_SCANNER-RECREATE.md`
- Strategy card: `strategies/sable/sable-support-scanner.md`
- Code (already in Test, master-desk paths): `sleeves/sable/sable.py`, `sleeves/sable/desk_scanner.py`, `sleeves/sable/runtime.py`; also `sleeves/sable/location_first.py`, `sleeves/sable/feedlib/yahoo_spark.py`, `sleeves/sable/jsport.py`, `sleeves/sable/vendor/sable/catalog.mjs`, `sleeves/sable/vendor/sable/universe.ts`
- Rule lines: `docs/verify/sable.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Searched for code outside Test: Silicon, quant-research-backup and Midna trees were searched for sable scanner code; no distinct original was found there (Silicon hits were unrelated REA artifacts). The code above in Test is the home used.

## Configuration

- Universe: Sable catalog, 488 stocks. Timeframe: 5m, completed regular-hours bars, last 5 sessions.
- Book: $100,000 (per card sizing). Max positions: 6. Deep list cap: 36 names.
- Cadence / state: not in the record beyond the 5-minute exit check and the 8-hour sold-name cooldown.

## Data inputs

- Yahoo spark quotes (5-minute closes, day and 52-week range) and Yahoo 5-minute bars (last 5 sessions).

## Install and run

1. Clone the Test repo.
2. Read `strategies/sable/sable-support-scanner.md` and `docs/verify/sable.md`.
3. Open `sleeves/sable/sable.py`, `sleeves/sable/desk_scanner.py` and `sleeves/sable/runtime.py`; these are the runnable scanner/runtime modules.
4. Provide Yahoo spark and 5-minute bar data for the 488-stock catalog in `sleeves/sable/vendor/sable/`.
5. Run the runtime/scanner on a 5-minute cadence in the regular session and verify behaviour against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- A name at 99.0% of its 64-bar support is not a SETUP; a name at 100% of support, 1.0 ATR above it, RSI 50, EMA gap 0, at 80% of its 52-week range is a SETUP.
- No buy when 6 positions (including working buys) are held, or when the name was sold within 8 hours.
- Stop and target for a fill are exactly fill - 1.6 ATR and fill + 2.8 ATR, with ATR floored at 1.5% of fill.
- A position not in profit after 15 days is exited by the time stop.
