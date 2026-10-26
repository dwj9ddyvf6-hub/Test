# Leaders Rest v1.1 on daily buy-greens

Each fresh daily Tensor buy-green that Leaders Rest calls a SETUP (a leader resting off its high) is bought with a GTC limit bracketed at -1.6 / +2.8 ATR.

| | |
|---|---|
| **Family** | Tensor research |
| **Source** | Griffith's Leaders Rest (LR_1_1_0_CORRECTED) on FolioTend's Deep Reset / Leaders Rest wrapper |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 1,838-name genome roster |
| **Style** | Pullback in a leader |
| **Status** | live |

## Entry

- Candidates: names with a fresh daily buy-green (funds excluded), each run through Leaders Rest v1.1 on its daily history with SPY's.
- Leader: ≥ 253 sessions; price ≥ $10 or 20-day dollar volume ≥ $20M; within 25% of the 52-week high; EMA 50 rising over 10 sessions; 12-1 momentum above SPY's; price above EMA 50 (or above EMA 21 with EMA 50 rising); SPY not below a falling EMA 50, and SPY's 12-1 momentum not under -4% while SPY is under its EMA 200 or its EMA 50 is falling.
- SETUP: resting (3-12% under the 20-day high, or the last 15 days' range ≤ 60% of the prior 20 days' with 2-18% off the 52-week high) and RSI(14) 48-68.
- Order: a GTC buy limit at the decision's close, armed 5 days; dropped when the name is held or the ask is at or under the stop.

## Exit

- Bracket: stop at the limit - 1.6 ATR, target at the limit + 2.8 ATR (ATR(14), at least 1.5% of price).

## Sizing

- 0.5% of equity at risk / 1.6 ATR, within a 3% strategy risk cap less open and armed risk; per order ≤ 35% of equity and ≤ 98% of buying power.

## Data

- Completed regular-session daily bars (2 years) of the roster and SPY, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/griffith/griffith.py`, `sleeves/griffith/vendor/griffith/strategy_system.py`, `sleeves/griffith/vendor/griffith/strategy_execution.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`; not in this repo: `desk/vendor/griffith/config.json`

## Notes

- The Doorway Deep Reset lens is computed beside each decision and never traded.
- The Tensor engine and the FolioTend research code these rules run are not published in this repo.
