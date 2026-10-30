# qr-newsconditioned121leadership: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "News-conditioned 12-1 leadership", type forecast and ML models, family quant_research. Algorithm grade PARTIAL in the accounting, gaps: entry/signal rule, exit rule and sizing not recorded in its consulted sources (Test catalog entry/variants only). Those gaps are filled in Test by the strategy card and the code below. Alias `qr_newsconditioned121leadership`; status waiting in the accounting. Card Source: a written design from the desk's agentic top-five research; the code header in Test (`sleeves/quant_research/news121.py`, read for this package) states the source branch is a design specification without code and its rules are implemented in that module as written.
- Strategy card in Test: `strategies/quant_research/qr-newsconditioned121leadership.md`.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b24_Test_tree.txt in the run workspace, reused as the batch-start tree) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, strategies/, packages/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for this id. The code paths below are the paths named in the strategy card's Code section, verified present in the Test tree, and the named module was read and confirmed to carry this strategy's id / logic.

## What this strategy is

Each month's S&P 500 12-1 momentum leaders, bought only on a fresh Tensor 1-hour swing and stopped at its invalidation (strategy card).

## Full algorithm

In evaluation order, from the strategy card in Test (`strategies/quant_research/qr-newsconditioned121leadership.md`) and the code header in Test:

1. Pool, after each month's last session: S&P 500 members with 253 daily closes, a close >= $10 and a 20-session average dollar volume >= $25M; momentum = the close 21 sessions back / the close 252 back - 1 on all-adjusted closes; positive momentum in the top 20%.
2. Rank: S = 0.65 R + 0.35 (1 + C N) / 2 with R the momentum percentile; no news model runs (C = N = 0), so names rank by momentum; the top 50 are candidates.
3. Trigger: the newest confirmed 1-hour Tensor swing is at most 3 bars and 6 hours old, confidence >= 8, not extended, its stop not yet breached and not acted on before; the daily structural screen is neither BROKEN nor UNKNOWN.
4. Order: whole shares, a DAY limit at the swing's entry x 1.03 (skipped when the ask is above it), good for 6 hours or until the close.
5. Exit: stop = the swing's invalidation, held by the engine. Refresh: at the next monthly snapshot, a name ranked below 75 or no longer eligible is sold at the market.
6. Sizing: $1,000,000 book: 0.5% of NAV at risk to the stop per entry, <= 10% of NAV a name, <= 30% a sector, <= 2% of NAV total stop risk, at most 8 names.

## Files in this repo

- This package: `docs/QR_NEWSCONDITIONED121LEADERSHIP-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Strategy card: `strategies/quant_research/qr-newsconditioned121leadership.md`
- Code (already in Test): `sleeves/quant_research/news121.py`, `sleeves/quant_research/vendor/old_desk_research/structural_screen.py`. Card Code section also names a Tensor swing module that is not in this repo (desk/sleeves/femto/ swing module); that dependency is recorded here as not in Test.
- Rule lines: `docs/verify/quant_research.md`
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Universe S&P 500 (current members); asset class US equities; timeframe 1mo ranking, 1h timing; family quant_research.
- Book $1,000,000; risk 0.5% of NAV to the stop per entry; <= 10% of NAV a name; <= 30% a sector; <= 2% of NAV total stop risk; at most 8 names; monthly snapshot after the close of each month's final regular session (code header, family job qr_news121).
- Cadence and state beyond the above: not in the record.

## Data inputs

- The S&P 500 constituent list (refreshed at each snapshot), all-adjusted daily bars (Alpaca; Yahoo without keys), the desk's canonical 1-hour Tensor feed, and split-adjusted daily bars for the screen (card Data section).

## Install and run

1. Clone the Test repo.
2. Take the code files named in Files at their Test paths, with their shared `sleeves/quant_research/common.py` dependencies.
3. Configure the book size, roster and cadence exactly as in Configuration; provide the Data inputs feeds.
4. First run: score one close on a small fixture roster and confirm the eligibility, ranking and order rules in the Verification checklist before any live-size run.

## Verification

Behaviour checklist from the recorded algorithm (rule lines at `docs/verify/quant_research.md`):

- The monthly pool requires 253 daily closes, close >= $10, 20-session average dollar volume >= $25M, and positive 12-1 momentum in the top 20%; ranking uses S = 0.65 R + 0.35 (1 + C N) / 2 with C = N = 0, and only the top 50 are candidates.
- An entry requires a confirmed 1-hour Tensor swing at most 3 bars and 6 hours old, confidence >= 8, not extended, stop unbreached and not previously acted on, and a structural screen that is neither BROKEN nor UNKNOWN.
- Orders are whole shares, DAY limit at swing entry x 1.03, skipped when the ask is above the limit, good for 6 hours or until the close.
- Sizing respects every cap in Configuration simultaneously; the exit stop is the swing's invalidation, and a name ranked below 75 or ineligible at the next snapshot is sold at the market.
