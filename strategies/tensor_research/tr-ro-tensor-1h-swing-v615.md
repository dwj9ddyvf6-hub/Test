# Tensor 1H Swing (v615)

Buys a stock when a completed hourly Tensor green arrow confirms a black-square setup within 3 bars, and sells at the close of hour 20; the winner census sells in thirds at hours 10, 20 and 30.

| | |
|---|---|
| **Family** | Tensor research |
| **Source** | FolioTend v615 Tensor Swing (full-universe study) and its corrected 10 / 20 / 30-bar winner census, as forward-test books |
| **Asset** | US equities |
| **Timeframe** | 1h |
| **Universe** | 1,838-name genome roster |
| **Style** | Swing confirmation |
| **Status** | 2 live |

## Entry

- Setup, a black square: an hourly bar with no primary marker, ≥ 5 of 7 bullish votes, the fast state bullish and the slow not; confirmation, a green arrow (≥ 5 bullish votes, ≥ 4 more than bearish) on the current completed hour within 3 bars of the setup; one episode per setup bar.
- Fired once per notification episode; the census book splits each episode into three equal sub-lots.
- Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
- Entry: the next hour's open, a market order within that hour; skipped once it has passed.

## Exit

- Exit: the close of hour 20 (market-on-close when it ends a session). The census book's sub-lots close at hours 10, 20 and 30.

## Sizing

- One equal slot per event: the $100,000 book / (1,838 names × 1 timeframe) = about $54 (a third of it per census sub-lot); skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.

## Data

- Completed regular-session hourly bars (1 year) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Variants

| Book | Exit | Row |
|---|---|---|
| 1H Swing | one lot, at the close of hour 20 | `ro_tensor_1h_swing_v615` |
| Winner census | three equal sub-lots, at the closes of hours 10, 20 and 30 | `ro_winner_census_10_20_30` |

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`; not in this repo: `desk/vendor/foliotend_research/v615/lib/tensor-swing-signals.mjs`, `desk/vendor/foliotend_research/v615/lib/tensor-swing-notification.mjs`, `desk/vendor/foliotend_research/v615/lib/tensor-enrichment-signals.mjs`
- **Rule lines**: [docs/verify/tensor_research.md](../../docs/verify/tensor_research.md)

## Notes

- The Tensor engine and the FolioTend research code these rules run are not published in this repo.
