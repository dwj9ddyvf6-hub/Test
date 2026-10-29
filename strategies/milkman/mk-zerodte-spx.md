# Milkman 0DTE (SPX)

Buys SPX 0DTE premium in the direction of Milkman's authored intraday lanes, picking the contract nearest 0.40 delta from fresh two-sided quotes. Parked and inert at install: the SPX 0DTE chain route is not proven on this desk.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades' 0DTE SPX method, from his 2026-10-21 answers and the authored Femto-lean sleeve (milkman-0dte branch), installed 2026-10-27 |
| **Asset** | SPX index options (0DTE, root SPXW) |
| **Timeframe** | Intraday |
| **Universe** | SPX |
| **Style** | Long premium day trading |
| **Status** | Midna's desk only; parked, waiting on the SPX 0DTE chain and greeks route |

## Entry

- Long premium only: a long lane buys a call, a short lane buys a put.
- Contract: today's expiry, the contract whose absolute delta is nearest 0.40 among fresh (at most 180 s) two-sided quotes at most 20% wide; bought at the quoted ask. No model price anywhere.
- ESMON and OPX4 lanes are not expressed.
- Inert until the SPX 0DTE chain is proven by the desk probe record; never a fallback to SPY options or to a model.

## Exit

- Sold at the quoted bid; no entry in the last 30 minutes; hard flat 15 minutes before the close.
- Daily stop: session P&L reaching -$10,000 (Milkman's own figure) flattens everything and blocks entries for the rest of the session.

## Sizing

- $2,500 premium per trade in whole contracts (one contract if it costs up to 1.5 budgets); at most 4 open at once.

## Data

- SPX 0DTE chain with greeks (not yet served on this desk; that is the parked reason).

## Code

- **Midna v3**: `sleeves/milkman_0dte.py`, `desk3/milkman_0dte/` (vendored authored package and probe)

## Notes

- Catalog provenance: muse-desk-v3 commit bc4fd4421a06268f481713283d9f07e9221e995c, config/sleeves.json row mk_zerodte_spx (parked), added 2026-10-29 to close the catalog diff of that date.
