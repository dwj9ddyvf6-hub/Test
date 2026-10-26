# Earnings-drift (PEAD) put options

After a weak earnings reaction, buys puts or put spreads three sessions later to ride the drift.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17/R18 options research |
| **Asset** | Equity options |
| **Timeframe** | 1d |
| **Universe** | Names with published earnings |
| **Style** | Event drift |
| **Status** | 3 live · 1 waiting |

## Entry

- Surprise = the stock's return minus SPY's from the session before to the session after the event.
- Trades when the surprise is at or below the 20th percentile of at least 200 prior events (prior four quarters), price ≥ $5, 20-day dollar volume ≥ $1M.
- Enters on event day + 3 sessions, 09:35-09:40 ET: puts with 21-35 DTE, delta 0.50-0.65; verticals sell the strike nearest spot × 0.95.

## Exit

- Planned exit on the 10th session counting the entry day; pre-expiry exit the session before expiry.

## Sizing

- Risk = min(NAV × 2% (A) or 0.5% (B), the 5% reserve, cash) / package debit.

## Data

- Earnings calendar with first-publication times; SIP daily bars of the stock and SPY.

## Variants

| Parameter | Values |
|---|---|
| Structure | long put · put vertical |
| Risk | A 2% · B 0.5% |

Rows: 4 on the master desk, 4 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_b2.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_options.py`, `desk/feedlib/ausar_pead.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)
