# Tensor LEAPS calls

Expresses each R19 G4 Tensor buy as a long-dated call and exits on the G4 trade's own deadline.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17/R18 options research |
| **Asset** | Equity options |
| **Timeframe** | 1w |
| **Universe** | R19 G4 signals |
| **Style** | Value recovery (options) |
| **Status** | 2 blocked |

## Entry

- On a qualified G4 event's entry session: calls with 540-720 DTE, delta 0.60-0.80.

## Exit

- Exits at the G4 trade's saved 52-week deadline or its state exit.

## Sizing

- Risk 2% (A) or 0.5% (B) of NAV / debit; premium ≤ 50% of spot.

## Data

- The R19 G4 event bridge; OPRA quotes.

## Variants

| Book | Risk |
|---|---|
| A | 2% |
| B | 0.5% |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch3.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_options.py`
