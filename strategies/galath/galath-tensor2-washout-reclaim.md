# Tensor 2 washout / reclaim printer

Buys a watch-list name when the Tensor 2 replica prints a green buy on a completed hour after a washout, and sells when an hour closes red under its 21-hour EMA.

| | |
|---|---|
| **Family** | Galath / GrokBot |
| **Source** | The Galath desk's Tensor 2 replica (galath-desk src/lib/tensor/engine.ts); a recorder made a book by the owner's D32 |
| **Asset** | US equities and ETFs |
| **Timeframe** | 1h |
| **Universe** | Galath's 13-name default watch list |
| **Style** | Washout reclaim |
| **Status** | waiting |

## Entry

- Read once per completed canonical hour for each of the 13 names (SATL, SKYQ, RDW, INDI, SPY, QQQ, NVDA, MU, AAPL, AMD, TSLA, WULF, POET), once the frame holds 200 bars (the source's authority).
- Washout: within the last 9 hours, a bar's low at the 12-hour swing low with RSI(14) ≤ 42.
- Green buy, on the hour: no buy signal held and no green buy in the last 12 hours; a washout; the bar closes at or above its open; RSI(14) rising from a 9-hour trough ≤ 48 and still under 58, with the MACD histogram rising; at most 0.8 ATR(14) above EMA21; the close reclaiming EMA21 or at a reclaim or launch-pad location, never extended (over 1.2 ATR above it).
- Orders: each decision once, at the book's next pass in the session (from 5 minutes after the open): a market buy of one slot while the signal is buy and the name is not held, a market sell once it is no longer buy; a decision unsent by the close of the session after its bar lapses, and a name without a live equity quote is not bought.

## Exit

- Out when the signal ends: an hour that closes below EMA21 on a red bar (the magenta sell); sold at the book's next pass in the session. No stop of its own.

## Sizing

- An equal slot of the book's equity / 13 a name; $100,000 book.

## Data

- Yahoo 60-minute bars (the desk's canonical 1H series, a year, regular session) and daily bars (2 years); the producer job runs 2-11 minutes after each completed hour, and a read older than 90 minutes is not used.

## Code

- **Master desk**: `sleeves/galath/monitor/printer_books.py`, `sleeves/galath/monitor/galath_tensor_mon.py`, `sleeves/galath/monitor/reads.py`, `sleeves/galath/monitor.py`; not in this repo: `desk/vendor/galath_mon/src/lib/tensor/engine.ts`
- **Rule lines**: [docs/verify/galath.md](../../docs/verify/galath.md)

## Notes

- The Tensor 2 replica it runs (Galath's Tensor engine) is not published in this repo.
- A recorder until the owner's ruling D32 (2026-10-26) funded it as a paper book; its first live signal is pending.
