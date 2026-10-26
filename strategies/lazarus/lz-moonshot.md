# Moonshot weekly lane

Buys cheap, deeply drawn-down weekly Cyan fires with $1,000 each, no stop, and holds them a year or more.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath research (MOONSHOT_FROZEN_SPEC v1.0), run by Lazarus; Midna's moonshot book |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Tracker universe · Midna's swing basket |
| **Style** | Value recovery |
| **Status** | 1 live · 1 waiting |

## Entry

- Signal: a tracker 1W Cyan or Green fire with close ≤ $14.94, 60-week depth ≥ 70, dv20 ≥ $1M; tier A first on ties.
- Midna's book: a weekly buy-cyan fire with close ≤ $14.94 and 60-week depth ≥ 70.35, ≤ 10 days old, not seen before; fewer than 10 open.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit 52 weeks.
- Midna's book: closes at the first regular-hours print after its 78th week; no stop.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position, 2 slots, $2,581. Midna's book: floor(min(cash, $1,000) / price).
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- Tracker ledger fires and ue_tag values.
- Midna's book: the hourly watch's weekly moonshot fires.

## Variants

| Variant | Fires | 60-week depth | Hold | Open at once |
|---|---|---|---|---|
| Lazarus lane (`lz_moonshot`; Midna v3 `s_moonshot`) | 1W Cyan or Green | ≥ 70 | 52 weeks | 2 |
| Midna's book (`midna_w_cyan_moonshot`; Midna v3 `s_mn_moonshot`) | 1W buy-cyan, ≤ 10 days old | ≥ 70.35 | 78 weeks (v3: 390 sessions) | 10 |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
- **Master desk (Midna's book)**: `sleeves/midna/shadow.py`
- **Midna v3 (`s_mn_moonshot`)**: `sleeves/s_mn_moonshot.py`. Consumes upstream fires; no stop, 390 sessions
- **Rule lines**: [docs/verify/lazarus.md](../../docs/verify/lazarus.md)

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
