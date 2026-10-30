# ausar_g_ABSORPTION_LINKUSDT_4H: Recreation Package

Package grade: INCOMPLETE-CODE. The algorithm text on file is reproduced below in full, but the genuine (original) code that ran this book was not located in any searched GitHub repo, so this package does not claim a faithful recreation. A v3 port of the same rules exists in this repo under a different canonical id (see Files).

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Four-hour confirmed absorption · LINKUSDT", type mean reversion, family confirmed_absorption. Sole alias `ausar_g_ABSORPTION_LINKUSDT_4H`, recorded installed, source md2_catalog. Algorithm grade PARTIAL; recorded gap: "sizing not recorded in any consulted source".
- Test strategy card: `strategies/ausar/crypto-absorption.md` ("Crypto confirmed absorption (4h)"), whose "Original books (ENJ, LINK)" rows describe this book: buy at the ask within 300 s of the confirmation bar's close; sell at the bid from 16 h after the confirmation bar's close; sizing 100% of book cash including the 10 bps fee, floored to the lot, capped by the displayed ask size. The accounting's sizing gap is therefore a gap of the accounting pass for the entry/exit text it consulted; the card's sizing is recorded here as the best evidence on file.
- The `ausar_g_` prefix marks the genuine-hosted record in the md2 catalog (the posted original code), distinct from the v3 port canonical id `ABSORPTION_LINKUSDT_4H` in the same accounting.

## What this strategy is

A 4-hour confirmed-absorption mean-reversion book on LINKUSDT (Binance spot): after a high-volume down bar (the shock bar), buy the immediately following bar that confirms by closing back above the shock bar's midpoint, and sell 16 hours after the confirmation bar completes. No stop, no pyramiding.

## Full algorithm

Everything the record holds, in evaluation order (accounting entry/exit text, with the card's original-book execution and sizing):

1. Shock bar (a completed UTC 4h bar): volume > 2 x its current-inclusive EMA(volume, 20), close < open, and close < its current-inclusive EMA(close, 50). The EMAs include the bar and seed at the first bar (card).
2. Confirmation: the immediately following completed UTC 4h bar closes > open and close > (shock high + shock low) / 2; no confirmation volume or EMA filter (accounting). The card adds a warmup: confirmation counts only after at least 300 completed bars.
3. Entry (original book): buy at the ask within 300 s of the confirmation bar's close (card).
4. Exit: sell at the first eligible observed bid at or after 16 hours from the confirmation bar's completion; partial exits retain that original deadline (accounting). No stop, no pyramiding (card).
5. Sizing (card, original books): 100% of book cash including the 10 bps fee, floored to the lot, capped by the displayed ask size. The accounting consulted sources did not record sizing; that gap is noted in Provenance.

## Files in this repo

- This package: `docs/AUSAR_G_ABSORPTION_LINKUSDT_4H-RECREATE.md`
- Strategy card: `strategies/ausar/crypto-absorption.md`
- Code-derived algorithm doc for the v3 port: `docs/ASTER_ABS_LINK_4H-ALGORITHM.md`
- NOT this book's genuine code, but the v3 port of the same rules in this repo (canonical id `ABSORPTION_LINKUSDT_4H`): `sleeves/aster_abs_link_4h.py` (wrapper), `adapters3/aster_abs_link_4h.py`, `integration/aster_abs_link_4h_adapter.py`, shared engine `desk3/aster_batch1.py` (kind "absorption"; $10,000 slice, cadence 14400 s, session 24h, 300-bar warmup, 16 h exit from confirmation completion, plus a default-on one-bar catch-up enhancement described in the card's Notes).
- Genuine code search record: the full file trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were searched for absorption paths at package build time. Test holds only the v3 port and the R19 funding-filter books listed on the card; no absorption module exists in the Silicon, quant-research-backup or Midna trees searched. The card names the original master-desk code (`desk/vendor/ausar_ctx/strategies/absorption/signals.py`, `desk/sleeves/families/absorption.py`) in a repo that is not among the searched GitHub repos. Nothing was vendored for this package.

## Configuration

- Universe: LINKUSDT (accounting universe/asset class/timeframe "not recorded in consulted sources"; the card records Crypto spot, 4h, universe ADAUSDT/ENJUSDT/LINKUSDT for the family with original books on ENJ and LINK only).
- Sizing: 100% of book cash including the 10 bps fee, floored to the lot, capped by displayed ask size (card).
- Cadence/session/state for the genuine-hosted book: not in the record.

## Data inputs

Binance spot 4h klines, book ticker and last trade (card). Accounting filter text: "data: posted Ausar runtime inputs".

## Install and run

This package cannot be installed as a faithful recreation of the genuine-hosted book, because its original code is not present in any searched GitHub repo:

1. Recovery would require the original absorption code named on the card (`desk/vendor/ausar_ctx/strategies/absorption/signals.py` and `desk/sleeves/families/absorption.py` on the master desk), which is not in Test, Silicon, quant-research-backup, or Midna as searched.
2. The closest runnable relative in this repo is the v3 port `sleeves/aster_abs_link_4h.py` with engine `desk3/aster_batch1.py`; running it recreates the sibling canonical id `ABSORPTION_LINKUSDT_4H`, not this genuine-hosted book, and must not be reported as this strategy running.

## Verification

No tests for this genuine-hosted book exist in Test. Behavior checklist from the recorded algorithm (for use once the genuine code is recovered):

- A completed 4h bar with volume above 2 x EMA20(volume), close below open and below EMA50(close), followed immediately by a bar closing above its open and above the shock midpoint, produces one buy at the ask within 300 s of the confirmation close (after the 300-bar warmup).
- The position is sold at the first eligible bid at or after confirmation completion + 16 h; a partial exit does not move the deadline.
- No stop exit and no second (pyramided) entry occur for the same shock.
