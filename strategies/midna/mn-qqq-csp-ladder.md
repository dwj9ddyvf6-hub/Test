# QQQ cash-secured put ladder

Each week, sells three QQQ puts near 0.065 delta about 45 days out, and buys back, rolls up or rolls down by rule.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | ETF options |
| **Timeframe** | 1d (weekly layers) |
| **Universe** | QQQ listed puts |
| **Style** | Options income |
| **Status** | waiting |

## Entry

- New layer once per week: QQQ not down and VIX not up on the day, nothing challenged, a fresh chain; expiry nearest 45 days (38-52); the put with delta 0.05-0.08, nearest 0.065.

## Exit

- Severe (QQQ ≤ strike, ask ≥ 3× credit or delta ≥ 0.35): buy back. 7 days or fewer left: buy back.
- 8-21 DTE: roll up when unchallenged and the ask ≤ half the credit; roll down and out when challenged (ask ≥ 2× credit, delta ≥ 0.20 or QQQ ≤ strike).

## Sizing

- 3 contracts a layer on a $1,000,000 book; each sale must be cash-secured.

## Data

- Cboe delayed QQQ option quotes (the option-marks producer).

## Code

- **Master desk**: `sleeves/midna/ladder.py`
