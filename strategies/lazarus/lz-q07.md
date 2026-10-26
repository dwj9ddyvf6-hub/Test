# Q07 Tensor alt-data confluence cells

Buys weekly Tensor fires (Cyan, Green or Swing) that also pass a cell of alt-data filters, and holds 52 or 78 weeks.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath research lab (Q07 confluence cells), run by Lazarus |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Tracker universe by PIT SEC band |
| **Style** | Tensor signal + alt data |
| **Status** | 52 blocked |

## Entry

- Cell = lane × hold × band × tags, e.g. `Q07-w_cyan-H52-small-cheap5+wiki_cov`; a fire trades only when every tag of its cell is true (a missing input is no fire).
- Tags: tierA (unified tier A), deep70 (60-week depth ≥ 70), cheap5 (close < $5), mom6 (126-day return ≥ the frozen 67th percentile), stress_vix20 (VIX ≥ 20), wiki_cov / wiki_low / wiki_spike2 (Wikipedia attention), insider2, ats_z1 (FINRA ATS z ≥ 1), gamma_low.
- Index lanes trade the union of their cells: `lz_q07_wiki` (the wiki cells), `lz_q07_ins2` (the insider cells).
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit 52 or 78 weeks.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position, mostly 1 slot per cell; the index lanes take the paper-test K = min(20, ⌈20 × H / 126⌉).
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- Tracker weekly fires, the w_swing feed, and the alt-data nightlies (Wikipedia, insider, FINRA, options market). Off since 2026-10-19, so these lanes are blocked.

## Variants

| Dimension | Values |
|---|---|
| Lane | w_cyan (`c`) · w_green (`g`) · w_swing (`s`) |
| Hold | 52 · 78 weeks |
| Band | micro (`mi`) · small (`sm`) · mid/large (`ml`) |
| Tags | tierA, deep70, cheap5, mom6, vix20, wcov, wlow, wspike2, ins2, ats_z1, glow |
| Also | `lz_1wsw_stress`: w_swing cheap5 + deep70 + VIX ≥ 20, all bands, 52 weeks |

Rows: 52 on the master desk, 50 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
- **Midna v3 (Q07)**: `desk3/lazarus_q07.py`, `desk3/q07_engine.py`, `sleeves/lazarus/s_q07w_*.py`. The `sleeves/lazarus/s_q07w_*` files call `laz_sleeves._common`, which is not in this repo

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
- Midna v3 reads its own filter proxies: deep70 as close ≤ 70% of the 252-session high, wlow as under 1,000 Wikipedia views, mom6 as any positive 126-day return, ins2 as 2+ insider buys.
