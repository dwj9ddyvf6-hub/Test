# griffith-tensor-phenotype-experiment: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor phenotype experiment (HIGH_BREAK_4)", type "forecast and ML models", family "griffith", style evidence "Tensor phenotype, bracketed", universe "Tensor research roster: 1,838 US names", asset class "US equities", timeframe "1d · 1w", creator/source "Griffith Tensor experimental paper lane (TENSOR_EXPERIMENTAL_1_1_0)". Algorithm grade PARTIAL (sources: Test catalog entry/variants); the accounting records no entry, exit or sizing rules and lists the gaps: entry/signal rule not in the record, exit rule not in the record, sizing not in the record. The rules below therefore come from the strategy card and the code/spec files in Test named in Files, not from the accounting.
- Test catalog entry `griffith-tensor-phenotype-experiment` in `docs/CATALOG.json` (card and code list as in Files).
- One catalog-listed file, `desk/vendor/griffith/config.json`, is marked 'not in this repo' on the card and was not found in the fresh Test tree; the traded path (tensor_research, griffith.py, strategy_execution.py) is in Test. Its absence is recorded here and in Files rather than filled in.
- Searched at batch start (fresh trees, 2026-10-30 run): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and family terms. No code for this id was found in Silicon, quant-research-backup or Midna (except the Anna replica traces noted where applicable); the code named below is already in Test.

## What this strategy is

An experimental paper lane (TENSOR_EXPERIMENTAL_1_1_0) that sends each frozen-phenotype prediction through a bracket path: a buy up to 0.1 ATR over the event high, a stop 2 ATR under its close, and a target 10% (daily) or 25% (weekly) higher. $100,000 book.

## Full algorithm

From the card `strategies/griffith/griffith-tensor-phenotype-experiment.md`, in evaluation order:

1. Predictions: the frozen v4 phenotype events, at most 25 a cycle, oldest first, each once.
2. Plan: trigger = the event bar's high; ceiling = trigger + 0.10 ATR(14); stop = its close - 2 ATR(14); target = the ceiling x 1.10 (daily) or x 1.25 (weekly).
3. Order construction: the planner prices on the live ask (or last trade) when the pass has one, else just under the trigger, so a name below the event high gets a stop-limit at the high, capped at the ceiling, and waits for the break; armed 7 days (daily) or 28 days (weekly). Card history note: until 2026-10-26 the ceiling itself was passed as the price, so every plan read as already crossed and bought at once below the high (owner decision Q51 fixed it).
4. Delivery, every regular-session pass (15 minutes): a plan is dropped when the name is held or the ask is at or under its stop, and waits while an entry works on the name; otherwise it goes in as a GTC order carrying its stop-loss and take-profit.
5. Exit: the plan's bracket only (stop and target). Card notes, preserved: the HIGH_BREAK_4 rule's wait for a break of the event high is lost in this path; the decision's horizon (26 / 130 sessions) is recorded, not enforced.
6. Sizing: risk 1% of equity / risk per share, within the strategy's 3% risk cap less its open and armed risk; per order <= 35% of equity and <= 98% of buying power; a held name is not added to; $100,000 book.

## Files in this repo

- This doc: `docs/GRIFFITH_TENSOR_PHENOTYPE_EXPERIMENT-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-tensor-phenotype-experiment.md`
- Rule lines: `docs/verify/griffith.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/griffith.py`, `sleeves/griffith/vendor/griffith/strategy_execution.py`
- NOT in Test: `desk/vendor/griffith/config.json` (catalog lists it; the card marks it not in this repo; not found in the fresh Test tree)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: Tensor research roster, 1,838 US names. Timeframes: 1d and 1w. Book: $100,000.
- Cycle cap: 25 predictions, oldest first, each once. Pass cadence: every 15 minutes in the regular session. Armed life: 7 days (daily) / 28 days (weekly).
- Bracket: trigger event high; ceiling +0.10 ATR(14); stop close - 2 ATR(14); target ceiling x1.10 daily / x1.25 weekly.
- Risk: 1% of equity per order by risk per share; 3% total risk cap net of open/armed risk; per-order caps 35% of equity and 98% of buying power.
- State: per-plan trigger/ceiling/stop/target, armed expiry, and open/armed risk totals.

## Data inputs

Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698; live ask/last trade for planner pricing (card).

## Install and run

1. Clone the Test repo.
2. Read this doc, the strategy card named in Files, and the accounting entry for `griffith-tensor-phenotype-experiment` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/griffith/griffith.py` and `sleeves/griffith/vendor/griffith/strategy_execution.py` with the frozen-phenotype event feed from `sleeves/tensor_research/tensor_research.py`; confirm the bracket formulas, the 25-per-cycle cap and the risk caps match Configuration. Note the missing `desk/vendor/griffith/config.json` recorded in Files before running.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- At most 25 predictions are planned per cycle, oldest first, and each event is planned once.
- Plan prices satisfy: ceiling = event high + 0.10 ATR(14); stop = event close - 2 ATR(14); target = ceiling x 1.10 (daily) or x 1.25 (weekly).
- A plan for a held name, or with the ask at or under its stop, is dropped; a plan waits while an entry works on the name.
- Orders are GTC with both bracket legs, armed 7 days (daily) or 28 days (weekly), and no horizon exit is enforced.
- Position size never risks more than 1% of equity, total risk stays within the 3% cap, and no order exceeds 35% of equity or 98% of buying power.
