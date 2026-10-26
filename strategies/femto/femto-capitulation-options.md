# Capitulation reversal calls (0-7 DTE)

On the hourly capitulation signal, buys a call 2% out of the money expiring within a week.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | Equity options |
| **Timeframe** | 1h · 1d filters |
| **Universe** | 41-name old-desk basket |
| **Style** | Mean reversion (options) |
| **Status** | waiting |

## Entry

- The capitulation signal (hourly RSI(14) < 20 volume climax into the 200-day EMA, daily ATR > 5%), while the desk fear composite is ≥ 55.
- Contract: the nearest expiry 0-7 days out, the first strike ≥ spot × 1.02; ask > 0 and spread ≤ 15% of mid; a DAY limit at the ask; at most 5 live.
- Scans hourly at :31 in the session.

## Exit

- Premium +75%, 1 day to expiry, or the stock 3% under its entry price; sold with a DAY limit at the bid; no stop.

## Sizing

- Premium ≤ 0.10% of the book a trade.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Daily (260) and hourly bars, the desk's 0-7 DTE call chains and quotes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/capitulation_options.py`, `desk/sleeves/femto/capitulation.py`
- **Midna v3**: `sleeves/capitulation_options.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds the 3-day pre-earnings veto, and an Edge-IMPROVE change (2026-10-24, on by default): expiries 2+ days out.
