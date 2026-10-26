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
| **Status** | 3 live |

## Entry

- Gate: the latest completed UTC daily close strictly above the 200-day SMA (inclusive).
- Rebalances 00:00-00:05 UTC to post-fee targets, once per day, with every market qualified.

## Exit

- A symbol whose gate turns off is sold in full at the bid, at any time.
- Aurelia forward: sells the whole holding at the bid on a daily close below the SMA200, on the master desk (the owner's decision Q41, 2026-10-26) as in Midna v3.

## Sizing

- Weights: ETH_SMA200 0/1, BTC_ETH_SMA200 0.5/0.5 of post-fee NAV; 0.2% fee per side; lot floors.
- Aurelia forward: when flat and the close is above the SMA200, 0.01 BTC at the ask once per UTC day (00:00-00:05) once 200 consecutive completed days exist and the quote is ≤ 30 s old; each order ≤ 10% of a $100,000 budget.

## Data

- Coinbase daily candles (200), products and quotes.

## Variants

| Book | Rows | Holds | Gate and exit |
|---|---|---|---|
| ETH_SMA200 | `ausar_eth_sma200_coinbase`; Midna v3 `aster_native_eth_sma200` | ETH | close vs the 200-day SMA |
| BTC_ETH_SMA200 | `ausar_btc_eth_sma200_coinbase`; Midna v3 `aster_native_btc_eth_sma200` | BTC and ETH, half each | close vs the 200-day SMA |
| Aurelia forward FWD_COINBASE_SMA200_V1 | `femto_fwd_coinbase_sma200`; Midna v3 `fwd_coinbase_sma200` | 0.01 BTC a day | in on a close above, out on a close below the SMA200 (master desk since 2026-10-26, and Midna v3) |

Rows: 3 on the master desk, 3 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch1.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_native/prospective_native.py`, `desk/sleeves/families/coinbase_sma200.py`
- **Master desk (Aurelia forward)** (not in this repo): `desk/sleeves/femto/fwd_coinbase_sma200.py`, `desk/vendor/aurelia/coinbase_schedule.py`
- **Midna v3 (Aurelia forward)**: `sleeves/fwd_coinbase_sma200.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)

## Notes

- The Aurelia forward copies its source exactly: no SMA200 test and no exit, so it buys 0.01 BTC on every executable day. Midna v3 adds the SMA200 entry and exit (an owner-approved design).
