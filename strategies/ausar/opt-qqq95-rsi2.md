# QQQ 95% core with RSI2 options

Holds 95% of the book in QQQ and spends the 5% reserve on short-dated calls after an RSI(2) dip.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17/R18 options research (core_reserve family) |
| **Asset** | ETF + ETF options |
| **Timeframe** | 1d |
| **Universe** | QQQ core; IWM, QQQ, SPY options |
| **Style** | Core + dip overlay |
| **Status** | 2 live |

## Entry

- Buys the QQQ core once: 95% of initial capital at the ask.
- Overlay: the RSI2 recovery signal (close > SMA200, RSI(2) < 10), 09:35-09:40 ET, 14-21 DTE calls of delta 0.50-0.60.

## Exit

- Overlay: exit on the 5th session counting the entry day, or on a 2% touch of the underlying; the core is held.

## Sizing

- Overlay risk 0.5% of NAV, within the 5% premium reserve.

## Data

- SIP daily bars, OPRA quotes.

## Variants

| Book | Structure |
|---|---|
| QQQ95_RSI2_LONG | long call |
| QQQ95_RSI2_VERTICAL | call vertical |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_b2.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_options.py`
