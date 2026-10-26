# CRD capital release

A weekly optimized long book of up to 30 registered capital-release candidates; with no decision documents registered it holds cash.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | CRD, from the desk's ten-strategy repair review (R10) playbook |
| **Asset** | US equities |
| **Timeframe** | 1w decisions |
| **Universe** | Registered decision documents |
| **Style** | Optimized event book (registered inputs) |
| **Status** | waiting |

## Entry

- Inputs: a hand-kept registry file of weekly decision documents (names, sectors, clusters, the 20-session covariance, lower-mean return scenarios, each candidate's frozen evidence, ADV) and nightly monitoring evidence.
- Admission: a release flag; a residual rank of 0.60-0.95 that rose ≥ 0.20 in 20 sessions; a positive residual sum; ≥ 30 effective origins and 100 calibration dates; the increment over the rank-only forecast less 1.645 SE positive; and the forecast less 1.645 SE above the round trip + 0.2%.
- Plan: the robust log-wealth optimum over the admitted and held names (traded only on a gain above log 1.0002 or to cure a cap), in whole shares within 30 names, 5% a name, 25% a sector, 20% a cluster, 95% gross, ≥ 5% cash, ≤ 20% forecast volatility and ≤ 30% weekly turnover.
- Execution: only the session after the decision, 09:35-10:05 ET, sells listed before buys, each ≤ 0.5% of the trailing ADV; marketable limits that expire at 10:05.

## Exit

- At each session's first pass, on the previous close: a residual rank under 0.40, a conservative forecast ≤ 0, lost fundamental eligibility, a hard cap breach, an 8% drawdown from entry, or a 20% account drawdown (which sells everything); a drawdown exit pauses entries for 5 sessions; sold at the market.

## Sizing

- $1,000,000 book; whole shares; idle cash stays cash.

## Data

- The registry file and live quotes (marked at the mid).

## Code

- **Master desk**: `sleeves/quant_research/crd.py`, `sleeves/quant_research/r10.py`; not in this repo: `desk/vendor/quant_research/r10/crd/`
- **Rule lines**: [docs/verify/quant_research.md](../../docs/verify/quant_research.md)
