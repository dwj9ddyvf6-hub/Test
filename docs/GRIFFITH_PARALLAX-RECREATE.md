# griffith-parallax - Recreation Package

Grade: PARTIAL (accounting) - code present in Test; see Files and Verification

## Provenance

- Canonical ID: `griffith-parallax`
- Canonical name: Parallax
- Aliases: griffith_parallax
- Type: other; Family: griffith; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Parallax" (also `docs/ALL-SLEEVES.md`); local census copy at research_notes/sleeve-census-20261029/accounting.json. doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Parallax" (also docs/ALL-SLEEVES.md); Test catalog entry 'griffith-parallax' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus file reads of strategies/griffith/griffith-parallax.md and sleeves/griffith/griffith.py); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for this canonical id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found in Test, so nothing was vendored.
- Accounting algorithm record: entry: []; exit: []; filters: []; parameters: {}; gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source']. Where the accounting graded PARTIAL, the algorithm below is taken from the code and the strategy card in Test, which are the truth where they go beyond the accounting.

## What this strategy is

Parallax. Universe: SCOPE universe: 550 US names; Asset: US equities; Timeframe: 1d.

Strategy card in Test (verbatim body):

Scores four entry engines (drift, dislocation, compression, reclaim) against the sector's state and the market regime and buys an opportunity of 48 or more with engine-specific brackets; a paper lane also arms strong WAITs as stop-limits above the market.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith / Ledge desk, Parallax PX_1_3_0_EXACT (conditional lane PX_1_3_0_CHALLENGER) |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | SCOPE universe: 550 US names |
| **Style** | Multi-engine swing |
| **Status** | live |

## Entry

- Decision: once a trading day before the open (else at the session's first pass), on the last completed bars, through the source's orchestrator over the universe.
- Field: each sector ETF against SPY (10-, 20- and 126-day relative strength, its 126-day percentile among the sectors, the EMA 50 slope) reads WATERFALL, TURN, TROUGH or TREND; names outside the sector map read TURN; a WATERFALL or unreadable field gives no decision.
- Regime: across the universe, the median day, the share up over 20 days, the median ATR% and the spread of 20-day returns give PANIC, REFLEXIVE_REBOUND, HIGH_VOLATILITY_DELEVERAGING, ORDERLY_RISK_ON, NARROW_RISK_ON or RANGE_BOUND; the medians of 5-, 20- and 60-day returns are the benchmark.
- Engines, 0-100 on returns over that benchmark: DRIFT (20- and 60-day residuals, 20-day path efficiency, above EMA 50, not stretched), DISLOCATION (a 5-day shock against ATR, close location, RSI < 45, MACD turning up), COMPRESSION (a low 20-day range percentile near the 20-day high), RECLAIM (yesterday under the 20-day low, today back above it in the top 45% of the range); TREND allows drift or compression, TURN dislocation, reclaim or compression, TROUGH dislocation or reclaim; the field's own engine gets +6.
- BUY: opportunity = the engine score less penalties (ATR over 4%, thin or heavy volume, a large shock, a stretch over EMA 20) ≥ 48; relative volume ≥ 2.8 is AVOID; a PANIC or HIGH_VOLATILITY_DELEVERAGING regime or a TROUGH field is WAIT.
- Orders: DRIFT, RECLAIM, DISLOCATION a GTC limit at the decision close, armed 2 days; COMPRESSION a stop-limit at the 20-day high + 0.05 ATR (limit + 0.20 ATR), armed 7 days.
- Conditional paper lane: the 8 best WAITs a run of the challenger version with an allowed engine and score ≥ 70 arm stop-limits above the close (the trigger 0.20-0.35 ATR over it by engine, or the 20-day high + 0.05 ATR for compression; the limit at least 0.10 ATR higher), armed 3 days (compression 5).
- Delivery, every regular-session pass (15 minutes): a plan is dropped when the name is held or the ask is at or under its stop and waits while an entry works on the name; otherwise it goes in as a GTC order carrying its stop-loss and take-profit.

## Exit

- Brackets: DRIFT -1.5 / +2.5 ATR, RECLAIM -1.25 / +2.25 ATR, DISLOCATION -1.5 / +2.25 ATR; COMPRESSION a stop 0.25 ATR under the compression low and a target 2.5 × the risk; the conditional lane keeps those stops with a target 2.5 × the risk.

## Sizing

- Risk 0.35% (the conditional lane 0.5%) of equity / risk per share, within the strategy's 3% risk cap less its open and armed risk; per order ≤ 35% of equity and ≤ 98% of buying power; a held name is not added to; $100,000 book.

## Data

- Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys.

## Code

- **Master desk**: `sleeves/griffith/griffith.py`, `sleeves/griffith/vendor/griffith/strategy_system.py`, `sleeves/griffith/vendor/griffith/strategy_orchestrator.py`, `sleeves/griffith/vendor/griffith/strategy_execution.py`, `sleeves/griffith/feedlib/griffith.py`; not in this repo: `desk/vendor/griffith/config.json`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)

## Notes

- The 28 universe names mapped to XLB, XLC or XLY (among them AMZN, TSLA, META and GOOGL) get no Parallax decision: those ETFs are not on the tape.
- Only the bracket exits: the source's lifecycle exits (thesis break, a 15-session time exit, breakeven, trailing) are not carried.

## Full algorithm

Evaluation order (sleeves/griffith/griffith.py Parallax sleeve over the vendored strategy_system / strategy_orchestrator / strategy_execution):
1. Decision: once a trading day before the open (else at the session's first pass), on the last completed daily bars, through the source orchestrator over the 550-name SCOPE universe.
2. Sector field: each sector ETF against SPY (10-, 20- and 126-day relative strength, its 126-day percentile among sectors, EMA 50 slope) reads WATERFALL, TURN, TROUGH or TREND; names outside the sector map read TURN; a WATERFALL or unreadable field gives no decision. The 28 universe names mapped to XLB, XLC or XLY get no decision (those ETFs are not on the tape).
3. Regime: across the universe, the median day, the share up over 20 days, the median ATR% and the spread of 20-day returns give PANIC, REFLEXIVE_REBOUND, HIGH_VOLATILITY_DELEVERAGING, ORDERLY_RISK_ON, NARROW_RISK_ON or RANGE_BOUND; medians of 5-, 20- and 60-day returns are the benchmark.
4. Engines scored 0-100 on returns over that benchmark: DRIFT (20- and 60-day residuals, 20-day path efficiency, above EMA 50, not stretched), DISLOCATION (a 5-day shock against ATR, close location, RSI < 45, MACD turning up), COMPRESSION (a low 20-day range percentile near the 20-day high), RECLAIM (yesterday under the 20-day low, today back above it in the top 45% of the range). Allowed engines by field: TREND allows drift or compression, TURN dislocation, reclaim or compression, TROUGH dislocation or reclaim; the field's own engine gets +6.
5. BUY gate: opportunity = engine score less penalties (ATR over 4%, thin or heavy volume, a large shock, a stretch over EMA 20) >= 48; relative volume >= 2.8 is AVOID; a PANIC or HIGH_VOLATILITY_DELEVERAGING regime or a TROUGH field is WAIT.
6. Orders: DRIFT, RECLAIM, DISLOCATION a GTC limit at the decision close, armed 2 days; COMPRESSION a stop-limit at the 20-day high + 0.05 ATR (limit + 0.20 ATR), armed 7 days.
7. Conditional paper lane (challenger PX_1_3_0_CHALLENGER): the 8 best WAITs with an allowed engine and score >= 70 arm stop-limits above the close (trigger 0.20-0.35 ATR over it by engine, or the 20-day high + 0.05 ATR for compression; limit at least 0.10 ATR higher), armed 3 days (compression 5).
8. Delivery, every regular-session pass (15 minutes): a plan is dropped when the name is held or the ask is at or under its stop, and waits while an entry works on the name; otherwise it goes in as a GTC order carrying its stop-loss and take-profit.
Exit: brackets only. DRIFT -1.5 / +2.5 ATR, RECLAIM -1.25 / +2.25 ATR, DISLOCATION -1.5 / +2.25 ATR; COMPRESSION a stop 0.25 ATR under the compression low and a target 2.5 x the risk; the conditional lane keeps those stops with a target 2.5 x the risk. The source's lifecycle exits (thesis break, 15-session time exit, breakeven, trailing) are not carried.
Sizing: risk 0.35% (conditional lane 0.5%) of equity / risk per share, within the strategy's 3% risk cap less open and armed risk; per order <= 35% of equity and <= 98% of buying power; a held name is not added to; $100,000 book.

## Files in this repo

- Strategy card: `strategies/griffith/griffith-parallax.md` (in Test)
- Sleeve: `sleeves/griffith/griffith.py` (in Test)
- Vendored source: `sleeves/griffith/vendor/griffith/strategy_system.py`, `sleeves/griffith/vendor/griffith/strategy_orchestrator.py`, `sleeves/griffith/vendor/griffith/strategy_execution.py` (in Test)
- Feed: `sleeves/griffith/feedlib/griffith.py` (in Test)

## Configuration

- Strategy version: PX_1_3_0_EXACT; conditional lane PX_1_3_0_CHALLENGER. Book $100,000. Universe: SCOPE 550 US names.
- Own parameters: opportunity >= 48, relative volume >= 2.8 = AVOID, field engine bonus +6, risk 0.35% (lane 0.5%), strategy risk cap 3%, per-order caps 35% of equity / 98% of buying power, arm 2 days (compression 7; lane 3, compression 5).
- Source config file desk/vendor/griffith/config.json: not in the record (not present in Test).

## Data inputs

Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys. Sector ETFs and SPY for the field read.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and confirm the files listed in "Files in this repo" are present at the stated paths.
2. Confirm the configuration in the Configuration section against the code constants and, where one exists, the config/sleeves.json row.
3. Wire the data inputs named in Data inputs so the sleeve receives them at evaluation time in the form the code expects.
4. Register / enable the sleeve in the host desk exactly as its code entry point expects (see the strategy card Code section).
5. Run one evaluation on fixture data and confirm the emitted behaviour matches the Verification checks before enabling live dispatch.

## Verification

No per-sleeve test file for this canonical strategy is present in the repo tree. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Field check: a WATERFALL or unreadable sector field produces no decision; names mapped to XLB, XLC or XLY produce no decision.
- Engine-gate check: opportunity < 48, relative volume >= 2.8, a PANIC or HIGH_VOLATILITY_DELEVERAGING regime each block a buy (WAIT / AVOID as coded).
- Order check: DRIFT / RECLAIM / DISLOCATION plans are GTC limits at the decision close armed 2 days; COMPRESSION is a stop-limit at 20-day high + 0.05 ATR with limit + 0.20 ATR, armed 7 days.
- Bracket check: per-engine ATR brackets exactly as in the Full algorithm; sizing never exceeds 0.35% risk, the 3% strategy cap, 35% of equity, or 98% of buying power.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
