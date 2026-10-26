# Index-ETF recovery options (RSI2 / VWAP20)

Buys calls or call spreads on IWM, QQQ or SPY after a short-term dip in a long-term uptrend.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17/R18 options research |
| **Asset** | ETF options |
| **Timeframe** | 1d |
| **Universe** | IWM, QQQ, SPY |
| **Style** | Mean reversion |
| **Status** | 8 live · 8 waiting |

## Entry

- Close > SMA200 and either RSI(2) < 10 (RSI2 books) or close ≤ 0.98 × the 20-day typical-price VWAP (VWAP20 books), on the prior session.
- Enters 09:35-09:40 ET on the first passing symbol in IWM, QQQ, SPY order; one package at a time.
- Call with 14-21 days to expiry and delta 0.50-0.60; vertical books sell the strike nearest spot × 1.02.

## Exit

- Planned exit on the 5th session counting the entry day, 5 minutes before the close; pre-expiry exit the session before expiry.
- touch books also exit when the underlying bid reaches entry spot × 1.02.

## Sizing

- Risk = min(NAV × 2% (A) or 0.5% (B), 5% of capital minus open risk, cash) / package debit, capped by displayed size.
- Debit caps: vertical ≤ 60% / 45% of width; long ≤ 2.5% / 1.5% of spot.

## Data

- SIP daily bars (200 sessions), OPRA option quotes and greeks.

## Variants

| Parameter | Values |
|---|---|
| Signal | RSI2 · VWAP20 |
| Structure | long call · vertical |
| Exit | fixed · touch |
| Risk | A 2% · B 0.5% |

Rows: 16 on the master desk, 16 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_b2.py`, `desk3/aster_b4.py`, `desk3/aster_batch3.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_options.py`, `desk/sleeves/families/ausar_options.py`
