# TRACE residual accumulation (daily)

Buys a liquid stock whose residual volume pressure built inside a 20-session box before two closes broke above it, with 1.5 / 3 ATR barriers and a 20-session limit.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | TRACE, from the desk's ten-strategy repair review (R10) playbook, at the daily scale on the Tensor research roster |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | The Tensor research roster's liquid operating companies |
| **Style** | Residual accumulation breakout |
| **Status** | waiting |

## Entry

- Universe: the roster's operating companies with 252 daily and 72 weekly bars, a close ≥ $10 and a 60-session median dollar volume ≥ $50M.
- Path: over the last 20 sessions, returns less a ridge fit on SPY and the name's sector ETF over the 60 sessions before; daily pressure = the close's place in its range × volume / the median of the 20 prior volumes (capped ±5); q = cumulative pressure / √20, p = cumulative residual / (σ √20).
- Gate: pressure established first (q ≥ 1, |p| ≤ 0.5, the close inside the range of the 20 sessions before the window), then two closes running above that range's high within the last 3 sessions, and no close under its low since.
- Order: the next session 09:35-09:45 ET, in symbol order, a limit at the close + 0.5 ATR(14) good until 09:45; no pyramiding; 20 sessions' cooldown after an exit.

## Exit

- Barriers, every pass: the bid at or below fill - 1.5 ATR, or at or above fill + 3 ATR.
- At 09:35-09:45 ET: 20 sessions held, or a renewal failure (the last 3 closes not above the prior closing high, a negative phase contrast and negative pressure over those 3 days); sold at the market.

## Sizing

- $100,000 book: shares = min(0.25% of NAV / 1.5 ATR, 8% of NAV / price, 0.5% of the 20-day average volume, the 25% sector room, the gross room, cash), at least $1,000; at most 15 names.

## Data

- Split-adjusted daily bars (600 sessions) of the roster, SPY and the sector ETFs, read from the desk's cache after each close.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`; not in this repo: `desk/vendor/foliotend_research/trace/trace_r10.py`
- **Rule lines**: [docs/verify/quant_research.md](../../docs/verify/quant_research.md)

## Notes

- The FolioTend research code it runs is not published in this repo.
