# APEX C7: COUNCIL

A fixed mix: 55% GESTALT × APEX on the Nasdaq, 25% a gold trend sleeve and 20% Variance Value options on T-bills; a variant adds 10% Bitcoin.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), round 3 C7 and the invention report's Council |
| **Asset** | US ETFs, ETF options and Bitcoin |
| **Timeframe** | 1d (monthly options) |
| **Universe** | QQQ, TQQQ, GLD, BIL, BTC/USD; QQQ listed options |
| **Style** | Multi-strategy mix |
| **Status** | 2 live |

## Entry

- Nasdaq book: N6, ½ × (APEX-50F target + GESTALT leverage), with the 0.20 band.
- Gold book: gold futures' trend score × min(2, 20% / HAR volatility), 0.20 band, held as GLD.
- Options book: the Variance Value rule (as O6) on its share of the book.
- Bitcoin variant: 10% at Bitcoin's trend score × min(1, 20% / HAR volatility), 0.20 band; the other books keep C7's proportions on the remaining 90%.

## Exit

- No stops: each book follows its target; option structures are held to expiry.

## Sizing

- Fixed shares of equity, the options book's T-bills = its share less its options' value.
- Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits.
- Exposure books market-on-close; Bitcoin in the last 10 minutes of the equity session; a $1,000,000 book.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), GC=F, BTC-USD, ^TNX, ^VIX, ^SOX and SMH; recomputed after each close.
- The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Variants

| Row | Nasdaq (N6) | Gold | Bitcoin | Variance Value |
|---|---|---|---|---|
| `apex_c7_council` | 55% | 25% | none | 20% |
| `apex_council_btc` | 49.5% | 22.5% | 10% | 18% |

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_book.py`, `sleeves/apex/vendor/apex/round3.py`, `sleeves/apex/vendor/apex/inventions.py`, `sleeves/apex/vendor/apex/opt_strategies.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
- **Rule lines**: [docs/verify/apex.md](../../docs/verify/apex.md)

## Notes

- The Bitcoin variant follows the invention report's Council; its "Bitcoin capped at 10% of risk" was never coded by the source, so the desk takes N4's Bitcoin sleeve on 10% of the book.
