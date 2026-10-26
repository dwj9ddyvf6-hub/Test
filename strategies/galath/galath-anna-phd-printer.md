# Anna PhD location printer

Holds a census name while the PhD replay of Anna's printer says buy on daily bars: in on a cyan or green print, out on a red or magenta print or a close back under the 200-day EMA.

| | |
|---|---|
| **Family** | Galath / GrokBot |
| **Source** | The Galath desk's gospel PhD replay of Anna's printer (galath-desk-backup scripts/anna-phd-replay.mjs); a recorder made a book by the owner's D32 |
| **Asset** | US equities and ETFs |
| **Timeframe** | 1d |
| **Universe** | Anna's labeled census: 115 names |
| **Style** | Printer signal (seven votes + location) |
| **Status** | waiting |

## Entry

- Votes on each completed daily bar: Stoch RSI K over D, Aroon up over down, +DI over -DI, OBV's 5-bar slope, squeeze momentum, EMA8 over EMA21, WaveTrend 1 over 2; the buy gate needs all seven readable, at least 5 bullish and 4 more than bearish.
- Prints: a UT Bot buy flip through the gate is cyan; an EMA 8/21 cross up within 6 bars of a UT buy flip, through the gate, is green; a UT sell flip is red; an EMA 8/21 cross down within 6 bars of a UT sell flip is magenta.
- Location re-prints: a red or magenta print deep under EMA200 (the close at most 65% of it) with at least 5 bullish votes turns cyan; an EMA200 reclaim inside the band, a confirmed gold warning, a launch-pad sequence and a support bounce print cyan; a failed euphoria or an extended failure prints magenta.
- Read after each close by the producer job (the replay under Node over the census names); the session's decision trades at the book's first pass of the next session.
- Orders: each decision once, at the book's next pass in the session (from 5 minutes after the open): a market buy of one slot while the signal is buy and the name is not held, a market sell once it is no longer buy; a decision unsent by the close of the session after its bar lapses, and a name without a live equity quote is not bought.

## Exit

- Out when the signal turns sell: a red or magenta print, or, while long, a close crossing below EMA200. No stop of its own.

## Sizing

- An equal slot of the book's equity / 115 a name; $100,000 book.

## Data

- Yahoo daily bars (2 years; Nasdaq or Cboe while Yahoo refuses), completed sessions only.

## Code

- **Master desk**: `sleeves/galath/monitor/printer_books.py`, `sleeves/galath/monitor/galath_phd_mon.py`, `sleeves/galath/monitor/reads.py`, `sleeves/galath/monitor.py`; not in this repo: `desk/vendor/galath_gospel/scripts/anna-phd-replay.mjs`
- **Rule lines**: [docs/verify/galath.md](../../docs/verify/galath.md)

## Notes

- The census holds the S&P 500 index (^GSPC); with no equity quote it is never bought.
- The PhD replay it runs is not published in this repo.
- A recorder until the owner's ruling D32 (2026-10-26) funded it as a paper book; its first live signal is pending.
