# Kraken basis repair (ADA / LINK)

When the 4-hour perpetual-over-spot basis is positive and two standard deviations above its 180-bar mean with positive funding, buys spot and shorts the perpetual until the basis is back at the mean.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk) Kraken research books, via Femto-lean |
| **Asset** | Crypto spot + perpetual |
| **Timeframe** | 4h |
| **Universe** | ADA, LINK (Kraken) |
| **Style** | Basis arbitrage |
| **Status** | 2 waiting |

## Entry

- Basis on aligned completed 4h spot and perpetual candles; needs 181 consecutive bars.
- Fires when the signal bar's basis > 0 and > the prior 180-bar mean + 2 sd, and the latest known funding (rate and relative rate) is positive.
- Package: buy 1 token spot at the ask and short 1 contract at the bid, once per signal candle, both quoted and uncrossed; no overlapping package.

## Exit

- Unwinds both legs when the basis is back at or below the entry mean, or 42 completed 4h candles after the signal; a leg left alone is closed.

## Sizing

- 1 token a leg, each within 10% of a $100,000 budget.

## Data

- Kraken public 4h spot and perpetual candles, funding prints and the instrument list.

## Variants

| Coin | Rows |
|---|---|
| ADA | `femto_free_kraken_ada_basis`; Midna v3 `free_kraken_ada_basis` |
| LINK | `femto_free_kraken_link_basis`; Midna v3 `free_kraken_link_basis` |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/free_kraken_ada_basis.py`, `desk/sleeves/femto/free_kraken_link_basis.py`, `desk/vendor/aurelia/kraken.py`
- **Midna v3**: `sleeves/free_kraken_ada_basis.py`
- **Midna v3 (LINK)**: `sleeves/free_kraken_link_basis.py`
