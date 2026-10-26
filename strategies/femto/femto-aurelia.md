# Aurelia Nasdaq + gold allocation

Holds Nasdaq (QQQ + TQQQ, up to 3×; 4× in APEX C1) and gold (GLD) at trend-times-volatility targets, rebalanced market-on-close when a target moves 0.20.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk paper desk), via Femto-lean; also APEX round 3 C1 (the AURELIA pair) |
| **Asset** | US ETFs (incl. 3× leveraged) |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, GLD, BIL |
| **Style** | Trend × volatility targeting |
| **Status** | 2 live |

## Entry

- Per asset (Nasdaq-100 total return, gold futures): unit = trend score (the share of 6 votes: above the 50/100/200-day SMA, positive 63/126/252-day return) × min(cap, 20% / the HAR volatility forecast).
- The units are averaged and scaled to 35% portfolio volatility (at most 3×), capped per asset (Nasdaq 4, gold 3) and at 6× in total; Femto-lean then cuts the Nasdaq target to 3×.
- Band: a held target changes only when the signal moves 0.20, or goes flat.
- Posture (Femto-lean): VIX ≥ 25 or a Nasdaq day ≤ -5% caps Nasdaq at 1×; VIX ≥ 40 or ≤ -8% caps it at 0.5×; gold is not cut. APEX C1 has no posture cut.

## Exit

- Positions follow the targets: market-on-close orders on a later session, sent until 15 minutes before the close (APEX C1: the next session, until 20 minutes before).

## Sizing

- Femto-lean: Nasdaq = QQQ + 3 × TQQQ within 100% of NAV; gold = GLD one for one; capital used ≤ 180% (both scaled together); idle weight ≥ 2% in BIL; a $500,000 margin book.
- APEX C1: Nasdaq as QQQ / TQQQ, gold in GLD, idle capital in BIL; above the book's capital a margin debit at 7.75% a year; shares = floor(weight × equity / the last close); a $100,000 book.

## Data

- Yahoo daily history of ^NDX, QQQ, GC=F and ^VIX.
- APEX C1: QQQ's adjusted returns and gold futures (GC=F), with ^IRX for T-bills.

## Variants

| Book | Posture cuts | Nasdaq cap | Capital | Rows |
|---|---|---|---|---|
| Femto-lean (master desk) | yes | 3× | ≤ 180% of a $500,000 book | `femto_aurelia_ndx` |
| Midna v3 | yes | 3× | account equity | `aurelia_ndx`, `aurelia_gold` |
| APEX C1 (master desk) | no | 4×, 6× in total | a $100,000 book, margin debit above it | `apex_c1_aurelia_pair` |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk**: `sleeves/femto/aurelia_ndx.py`, `sleeves/femto/vendor/aurelia/prism.py`, `sleeves/femto/vendor/aurelia/features.py`, `sleeves/femto/vendor/aurelia/allocate.py`, `sleeves/femto/vendor/aurelia/session.py`, `sleeves/femto/vendor/aurelia/plan.py`, `sleeves/femto/vendor/aurelia/judgment.py`, `sleeves/femto/feedlib/aurelia.py`
- **Midna v3**: `sleeves/aurelia_ndx.py`. Nasdaq legs; sizes off account equity
- **Midna v3 (gold)**: `sleeves/aurelia_gold.py`. The GLD leg
- **Master desk (APEX C1)**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/round3.py`, `sleeves/apex/vendor/apex/inventions.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- The master desk runs both Aurelia legs as one book (`femto_aurelia_ndx`); Midna v3 keeps two (`aurelia_ndx`, `aurelia_gold`).
- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): rebalance only on the first evaluation of each session.
