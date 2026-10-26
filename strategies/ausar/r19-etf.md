# R19 ETF books: momentum leader rotation

Holds the strongest of 14 ETFs by 126-session return and rotates monthly. Fixed-weight QQQ, SPY, SMH and QLD books run beside it as controls.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17/R18 ETF research, frozen as the R19 ETF books |
| **Asset** | US ETFs |
| **Timeframe** | 1d, monthly rebalance |
| **Universe** | QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY; QLD for the 2x controls |
| **Style** | Momentum rotation |
| **Status** | 12 live · 14 waiting |

## Entry

- Score: log(close / close 126 sessions earlier) on total-return closes. A fund needs 252 sessions of history to be eligible.
- LEADER1 holds the top score. EXSMH1 excludes SMH. CORE25 holds 25% leader and 75% QQQ. DRIFT1 keeps the incumbent's shares when it leads again.
- INTERVAL policies score on Alpaca and Yahoo. They take the fund whose lower score beats every other fund's upper score, else the incumbent if it can still lead, else QQQ.
- Trades 09:35-09:40 ET on the month's first session, on the prior month's last close, retrying for up to 5 sessions.

## Exit

- Each month sells what left the target before it buys. Buy-and-hold books never sell. No stops.

## Sizing

- Target shares = floor(weight × gross × NAV / ask). Gross is 0.98 in cash (C098), 1.5 on margin with a 10%/yr debit (M150), or 1.0 (C100).
- Buys wait for settled cash and the displayed ask size; 15 bps per side.

## Data

- Daily total-return closes (Alpaca; Yahoo too for INTERVAL); IEX quotes.

## Variants

| Book | Rule | Gross |
|---|---|---|
| LEADER1 · DRIFT1 · CORE25 · EXSMH1 | momentum leader policies | C098 · M150 |
| INTERVAL1 · INTERVAL_DRIFT1 · INTERVAL_CORE25 | two-provider interval versions | C098 · M150 |
| QQQ_MONTHLY · SPY_MONTHLY | 100% one fund, rebalanced monthly | C098 · M150 |
| SMH_HOLD | buy once and hold | C098 · M150 |
| QQQ_HOLD_FULL · SPY_HOLD_FULL · QLD_ONLY · QQQ_QLD_50_50 | buy and hold, or monthly (QLD) | C100 |

Rows: 26 on the master desk, 27 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_etf.py`, `desk3/aster_etf_b9.py`, `desk3/aster_batch8.py`, `desk3/aster_batch11.py`, `sleeves/free_etf.py`. `free_etf` executes R19 books handed to it on one $100,000 budget
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_etf.py`, `desk/sleeves/families/r19_etf.py`

## Notes

- Midna v3 sizes whole shares off the last close of its $10,000 slice. By default it lets a missed 09:35 monthly rebalance run later the same session (09:40-15:55 ET). `free_etf` ranks by return per unit of volatility by default.
