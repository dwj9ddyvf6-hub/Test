# QQQ weekly put ladder

Sells three far out-of-the-money QQQ puts about 45 days out once a week, and rolls or buys back each layer by rule.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | A public options campaign, run by Aurelia (Agentic-Trading-Desk), via Femto-lean; Midna's variant |
| **Asset** | ETF options |
| **Timeframe** | 1d (weekly layers) |
| **Universe** | QQQ listed puts |
| **Style** | Options income |
| **Status** | 2 waiting |

## Entry

- A new layer at most once per ISO week: the 38-52 DTE put with delta 0.05-0.08, nearest 45 DTE, then delta 0.05, then the tightest spread; bid ≥ $0.05, spread ≤ max($0.10, 25% of mid), strike below spot, not in an expiration already held.
- Blocked when the posture is not normal (VIX ≥ 25 or a Nasdaq day ≤ -5% is cautious; VIX ≥ 40 or ≤ -8% stands down), QQQ is down over 5 sessions, a put is challenged, 12 contracts are open, a layer was sold this week, or the cash does not secure it.
- Midna's variant: a new layer once per ISO week when QQQ is not down and VIX not up on the day, nothing is challenged and the chain is fresh; nearest 45 days (38-52); delta 0.05-0.08, nearest 0.065.

## Exit

- ≤ 5 DTE: bought back.
- ≤ 21 DTE: rolled up in the same expiration when the posture is normal, the put is not challenged, QQQ is above the entry spot and the ask ≤ half the credit; a challenged put (|delta| ≥ 0.20 or spot ≤ strike × 1.03) rolls out and down to the band put at or below its strike unless standing down, else is bought back.
- Midna's variant: bought back when severe (QQQ ≤ strike, ask ≥ 3× credit or delta ≥ 0.35) or at ≤ 7 DTE; 8-21 DTE rolls up (ask ≤ half the credit) or down and out when challenged (ask ≥ 2× credit, delta ≥ 0.20 or QQQ ≤ strike).

## Sizing

- 3 contracts a layer, at most 12 open; each secured by (strike - bid) × 100 × 3 of the book's cash; sales at the bid, buy-backs at the ask, day limits; a $1,000,000 book.
- Midna's variant: 3 contracts a layer on a $1,000,000 book; each sale cash-secured.

## Data

- The desk's QQQ put chain with deltas (0-52 DTE), the live QQQ quote, QQQ daily closes, and the Aurelia tape (VIX, Nasdaq day) for the posture.
- Midna's variant: Cboe delayed QQQ option quotes (the option-marks producer).

## Variants

| Variant | Rows | Target delta | Bought back | Cap | New-layer gate |
|---|---|---|---|---|---|
| Aurelia campaign (Femto-lean) | `femto_qqq_put_ladder`; Midna v3 `qqq_put_ladder` | 0.05 | ≤ 5 DTE, or challenged with no roll | 12 contracts | posture normal, QQQ not down over 5 sessions |
| Midna TypeScript | `midna_qqq_csp_ladder` | 0.065 | ≤ 7 DTE, or severe | cash-secured | QQQ not down and VIX not up on the day |

Rows: 2 on the master desk, 1 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk**: `sleeves/femto/qqq_put_ladder.py`, `sleeves/femto/vendor/aurelia/put_ladder.py`, `sleeves/femto/vendor/aurelia/judgment.py`
- **Master desk (Midna's variant)**: `sleeves/midna/ladder.py`
- **Midna v3**: `sleeves/qqq_put_ladder.py`. A wrapper only; the strategy file is not in this repo
