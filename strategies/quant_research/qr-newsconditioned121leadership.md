# News-conditioned 12-1 leadership

Each month's S&P 500 12-1 momentum leaders, bought only on a fresh Tensor 1-hour swing and stopped at its invalidation.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | News-conditioned 12-1 leadership, a written design from the desk's agentic top-five research |
| **Asset** | US equities |
| **Timeframe** | 1mo ranking · 1h timing |
| **Universe** | S&P 500 (current members) |
| **Style** | Momentum + Tensor timing |
| **Status** | waiting |

## Entry

- Pool, after each month's last session: S&P 500 members with 253 daily closes, a close ≥ $10 and a 20-session average dollar volume ≥ $25M; momentum = the close 21 sessions back / the close 252 back - 1 on all-adjusted closes; positive momentum in the top 20%.
- Rank: S = 0.65 R + 0.35 (1 + C N) / 2 with R the momentum percentile; no news model runs (C = N = 0), so names rank by momentum; the top 50 are candidates.
- Trigger: the newest confirmed 1-hour Tensor swing is at most 3 bars and 6 hours old, confidence ≥ 8, not extended, its stop not yet breached and not acted on before; the daily structural screen is neither BROKEN nor UNKNOWN.
- Order: whole shares, a DAY limit at the swing's entry × 1.03 (skipped when the ask is above it), good for 6 hours or until the close.

## Exit

- Stop: the swing's invalidation, held by the engine.
- Refresh: at the next monthly snapshot, a name ranked below 75 or no longer eligible is sold at the market.

## Sizing

- $1,000,000 book: 0.5% of NAV at risk to the stop per entry, ≤ 10% of NAV a name, ≤ 30% a sector, ≤ 2% of NAV total stop risk, at most 8 names.

## Data

- The S&P 500 constituent list (refreshed at each snapshot), all-adjusted daily bars (Alpaca; Yahoo without keys), the desk's canonical 1-hour Tensor feed, and split-adjusted daily bars for the screen.

## Code

- **Master desk**: `sleeves/quant_research/news121.py`, `sleeves/quant_research/vendor/old_desk_research/structural_screen.py`; not in this repo: `desk/sleeves/femto/tensor_swing.py`
- **Rule lines**: [docs/verify/quant_research.md](../../docs/verify/quant_research.md)
