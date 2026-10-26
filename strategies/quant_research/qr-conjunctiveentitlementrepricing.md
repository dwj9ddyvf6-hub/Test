# CER entitlement repricing

A 49% QQQ / 49% SPY core that funds 2% stock positions when a registered project's required entitlement conditions all turn true; with no projects registered it holds the core.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | CER, from the desk's ten-strategy repair review (R10) playbook |
| **Asset** | US equities and ETFs |
| **Timeframe** | 1d (21- or 63-session hold) |
| **Universe** | QQQ, SPY and registered project issuers |
| **Style** | Event-driven (registered inputs) |
| **Status** | blocked |

## Entry

- Core: QQQ 49%, SPY 49%, cash 2%, bought once at the live quotes.
- Inputs: a hand-kept registry file of projects (1-8 required predicates, a horizon of 21 or 63 sessions, value intervals, an equity value) and their dated proofs.
- Admission at the 16:15 ET clock: every required predicate true now but not all at the prior 16:15, with a new usable true proof in between; a positive worst-case value gain; at least 100 matured episodes, 40 issuers, 10 groups and 36 months; the registered net forecast above 50 bp.
- Entry from 09:45 ET within 5 sessions of admission: sell 1% of NAV each of QQQ and SPY and buy 2% of NAV of the stock with a limit 25 bp over the ask, good for the session; at most 4 issuers, 8% in stocks, 4% per group.

## Exit

- First of: H sessions after the fill, the bid 12% under the entry, or a revoked condition (a usable false or conflicting proof); sold at the market and the QQQ / SPY shares restored.

## Sizing

- $1,000,000 book: 2% of NAV per episode in fractional shares, funded from the core.

## Data

- The registry file and live quotes.

## Code

- **Master desk**: `sleeves/quant_research/cer.py`, `sleeves/quant_research/r10.py`; not in this repo: `desk/vendor/quant_research/r10/cer/`
