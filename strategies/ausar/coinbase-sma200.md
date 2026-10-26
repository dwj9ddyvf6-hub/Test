# Coinbase SMA200 crypto trend

Holds ETH, or BTC and ETH half and half, while each closes above its 200-day average; otherwise cash.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R14/R15 Coinbase research |
| **Asset** | Crypto spot |
| **Timeframe** | 1d |
| **Universe** | BTC-USD, ETH-USD (Coinbase) |
| **Style** | Trend filter |
| **Status** | 2 live |

## Entry

- Gate: the latest completed UTC daily close strictly above the 200-day SMA (inclusive).
- Rebalances 00:00-00:05 UTC to post-fee targets, once per day, with every market qualified.

## Exit

- A symbol whose gate turns off is sold in full at the bid, at any time.

## Sizing

- Weights: ETH_SMA200 0/1, BTC_ETH_SMA200 0.5/0.5 of post-fee NAV; 0.2% fee per side; lot floors.

## Data

- Coinbase daily candles (200), products and quotes.

## Variants

| Book | BTC | ETH |
|---|---|---|
| ETH_SMA200 | 0 | 1 |
| BTC_ETH_SMA200 | 0.5 | 0.5 |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch1.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_native/prospective_native.py`, `desk/sleeves/families/coinbase_sma200.py`
