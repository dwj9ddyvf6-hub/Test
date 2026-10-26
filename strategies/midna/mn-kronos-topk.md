# Kronos-base TopkDropout

Every ten sessions ranks 24 frozen names by the Kronos-base ten-session price forecast and holds the top 4, replacing at most one.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk; also Kronos-base (shiyu-coder/Kronos; NeoQuasar/Kronos-base weights), reconstructed in the desk's six-strategy study |
| **Asset** | US equities |
| **Timeframe** | 1d (10-session cycle) |
| **Universe** | 24 frozen names |
| **Style** | Model forecast · TopkDropout |
| **Status** | 2 live |

## Entry

- Score = the forecast close in 10 sessions / the last close - 1, rebuilt every 10 sessions.
- Quant research book: from 2024-07-01, after every 10th session's close, the released Kronos-base model reads each name's last 90 sessions and samples 10 paths 10 sessions ahead (temperature 0.6, top-p 0.9, fixed seeds); the score uses their mean. A name also needs 252 complete prior sessions, a 20-session average dollar volume ≥ $10M and a close ≥ $5.
- TopkDropout: drop the worst held name held ≥ 5 sessions and out of today's top 5, then fill back to 4.

## Exit

- Sold when dropped from the targets.

## Sizing

- Midna book: slice = 95% of equity / 4 on its own $100,000 book; whole shares at last ± 0.1%.
- Quant research book: $1,000,000; buys share 95% of the cash left after sales (net of 15 bp, buys grossed up 15 bp) equally; every trade ≤ 1% of the name's 20-session dollar volume; fractional shares; marketable limits 1% through the quote, good for 30 minutes, sells first.

## Data

- Kronos-base forecasts on daily bars.
- Quant research book: split-adjusted daily bars of the 24 names; the pinned Kronos-base weights, verified by hash and run by a separate interpreter with torch.

## Variants

| Book | Book size | Sizing | Orders | Rows |
|---|---|---|---|---|
| Midna (her v3 desk and the master desk's port) | $100,000 | 95% of equity / 4, whole shares | at last ± 0.1% | `midna_kronos_topk`, `s_mn_kronos` |
| Quant research reconstruction | $1,000,000 | 95% of the cash after sales, 1% ADV caps, fractional | marketable limits, 30 minutes | `qr_kronosbasezeroshotustransfer` |

Rows: 2 on the master desk, 1 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `sleeves/s_mn_kronos.py`. Consumes forecast fires from an upstream producer not in this repo
- **Master desk** (not in this repo): `desk/sleeves/midna/kronos.py`
- **Master desk (quant research)**: `sleeves/quant_research/dropout_book.py`, `sleeves/quant_research/sixai.py`, `sleeves/quant_research/common.py`; not in this repo: `desk/sleeves/quant_research/kronos.py`, `desk/sleeves/quant_research/kronos_runner.py`

## Notes

- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
- The Kronos model code and weights it runs keep their upstream license and are not copied here.
