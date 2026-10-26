# Opening gamma puts

After a hot final two hours, buys short-dated puts when the next morning's first 5-minute bar is red and breaks its low; flat by 10:00 ET.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R18 opening-reversal research (R5 events) |
| **Asset** | Equity options |
| **Timeframe** | 5m |
| **Universe** | 42-name R5 list |
| **Style** | Opening reversal |
| **Status** | 2 waiting |

## Entry

- Prior afternoon: the last-two-hours return ≥ the 80th percentile of its trailing 252 sessions (at least 126).
- Today: the first 5-minute bar closes down and price breaks below its low; buys 09:35-09:45 ET.
- Puts, delta 0.50-0.65: A 0-2 DTE, B 7-14 DTE.

## Exit

- Sells at 10:00 ET the same day.

## Sizing

- Risk 2% (A) or 0.5% (B) of NAV / debit; premium ≤ 2.5% / 1.5% of spot.

## Data

- 30-minute bars for the R5 statistic; the first 5-minute bar; OPRA quotes.

## Variants

| Book | DTE | Risk |
|---|---|---|
| A | 0-2 | 2% |
| B | 7-14 | 0.5% |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch1.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_options.py`, `desk/sleeves/families/ausar_options.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)
