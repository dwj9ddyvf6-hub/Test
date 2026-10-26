# Tensor edge v0.1 (G1 / G2 / C1)

Buys a break of the signal bar's high after a qualifying daily green ignition, weekly green emergence or weekly cyan re-acceleration, stopped at the signal bar's low and held until the frame's next sell.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith Tensor edge research (griffith-tensor-edge/0.1.0), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1d · 1w |
| **Universe** | Tensor research roster: 1,838 US names |
| **Style** | Tensor signal breakout |
| **Status** | live |

## Entry

- G1, a daily buy-green: above a rising EMA 200, a 20/60-bar range ratio ≤ 0.75, a 20-bar breakout, under 15% over EMA 21, and an up-volume share ≥ 50% or a rising OBV or A/D line.
- G2, a weekly buy-green: a long base (range ratio ≤ 0.75 or ≥ 30% under the 52-week high), the 13-week return above SPY's (or the 13-week relative strength above the 26-week), 4-week volume ≥ the 20-week, under 15% over EMA 21.
- C1, a weekly buy-cyan: 13- and 26-week returns above SPY's, a 13-week return of 25-60%, RSI 55-72, an up-volume share ≥ 55%, the 4-week range ≤ 75% of the 13-week; none when exhausted (RSI ≥ 75, a 13-week return ≥ 100%, or an extension warning).
- Entry: a buy-stop at the signal bar's high, resting through the next bar (session or week).
- Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it.

## Exit

- Stop: the bid at or under the signal bar's low, at the market.
- The next session's open after the frame's completed sell-red / sell-magenta.

## Sizing

- One slot per event: the $100,000 book / (1,838 names × 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; the desk's own fees.

## Data

- Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_edge_strategy_spec.json`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)
