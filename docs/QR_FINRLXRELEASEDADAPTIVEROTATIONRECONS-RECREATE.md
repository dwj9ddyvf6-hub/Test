# qr-finrlxreleasedadaptiverotationrecons: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "FinRL-X adaptive rotation", type market timing and rotation, family quant_research, style "Regime-gated group rotation", universe "21 stocks and ETFs in three groups, plus SPY and QQQ", asset class US equities and ETFs, timeframe "1w", creator "FinRL-X adaptive rotation (AI4Finance Foundation, FinRL-Trading), reconstructed in the desk's six-strategy study". Algorithm grade PARTIAL, gaps entry/exit/sizing in the accounting; the algorithm below is from the Test card and the wrapper code in this repo.
- Test catalog entry `qr-finrlxreleasedadaptiverotationrecons`: card `strategies/quant_research/qr-finrlxreleasedadaptiverotationrecons.md`, status live: 1.
- Alias: `qr_finrlxreleasedadaptiverotationrecons`.
- INCOMPLETE-CODE: the wrapper `sleeves/quant_research/finrlx.py` is in Test, but the upstream engine it imports (`desk/vendor/quant_research/finrlx/`, 17 files plus `AdaptiveRotationConf_v1.2.1.yaml`) is NOT in Test and was not found in Silicon, quant-research-backup or Midna. The card itself notes: 'not in this repo: desk/vendor/quant_research/finrlx/' and 'The released FinRL-X code it runs keeps its upstream license and is not copied here.' This package therefore does not pass the recreation bar on code.
- Code search (this package): fresh trees at batch start for Test (sleeves/, strategies/, packages/, adapters/, adapters3/, desk3/, integration/), Silicon, quant-research-backup and Midna were searched for the canonical id, its aliases and family terms. 

## What this strategy is

Each week splits a regime-set budget over the two strongest of three asset groups (growth tech, real assets, defensive), three names each, with a five-fund fallback.

## Full algorithm

From `strategies/quant_research/qr-finrlxreleasedadaptiverotationrecons.md` and `sleeves/quant_research/finrlx.py`, in evaluation order:

1. Decision: once a week on the completed Friday close, using the released FinRL-X engine and its v1.2.1 config (SPY standing in for the S&P 500, with Yahoo's VIX), traded from the next session. Wrapper code: decision on the last Friday before the session, cadence 300s, schedule rth, $1,000,000 capital, stream `native_cash`.
2. Budget: a point each for SPY under its 26-week average, a 13-week drawdown >= 10% and a VIX robust z-score (3 years) >= 3; 0 points invests 100%, 1 point 85%, 2-3 points 70%; 70% too when SPY or QQQ fell >= 3% over 3 sessions, or when the VIX z-score is >= 3 and its change's >= 3.5.
3. Groups: growth tech (AAPL, MSFT, NVDA, META, AMZN, GOOGL, TSLA), real assets (XOM, CVX, COP, FCX, BHP, GLD, SLV) and defensive (TLT, IEF, XLU, XLV, IAU, SHY, UUP), ranked by 12-week information ratio against QQQ; the best two that beat QQQ over those 12 weeks are active. Note the wrapper docstring records the upstream builder as 'at most two groups, two names each' while the card records the engine taking the top 3 of each group and the config's two-names-per-group cap as not read; both statements are in the record and are not reconciled here.
4. Names: in each active group, the 3 with the highest robust z-score of their latest weekly return over the group's (against the last 12 weeks); the budget splits equally over the groups, then over their names.
5. Exception: a picked name with a z-score >= 3.5 and a positive 12-week return above 1.5 x QQQ's gets 1.5 x its weight; the total is capped at 100%.
6. Fallback: with no active group, SPY, QQQ, IAU, XLU and XLV share the budget equally.
7. Orders (card): marketable limits 1% through the quote, each good for 30 minutes; sells first, buys once no sell is outstanding. Wrapper divergence recorded in its docstring: the rebalance trades at the market from the first pass of the session after the decision Friday, sized on the live quote and the sleeve's NAV; sells first and buys follow on the next pass once no sell is outstanding.
8. Exit: names outside the new week's allocation are sold at that rebalance; holdings drift between Fridays.
9. Sizing: $1,000,000 book: each weight x NAV at the ask, fractional shares; the unallocated budget stays in cash.
10. Recorded non-actions on the card: the config's daily stops (-5%, -10% trailing) never act (the engine is given no positions); only each Friday's own readings count (the 10-day fast risk-off hold and the 4-week persistence exception never act).

## Files in this repo

- This doc: `docs/QR_FINRLXRELEASEDADAPTIVEROTATIONRECONS-RECREATE.md`
- Strategy card: `strategies/quant_research/qr-finrlxreleasedadaptiverotationrecons.md`
- Code in Test (wrapper only): `sleeves/quant_research/finrlx.py`, `sleeves/quant_research/common.py`
- Code NOT in Test (and not found in any searched GitHub repo): the vendored upstream engine under `desk/vendor/quant_research/finrlx/` (17 files, config `AdaptiveRotationConf_v1.2.1.yaml`)
- Rule lines: `docs/verify/quant_research.md` (named on the card)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: 21 stocks and ETFs in three groups, plus SPY and QQQ (23 tradables in the wrapper). Timeframe: 1w. Book: $1,000,000.
- Config: `AdaptiveRotationConf_v1.2.1.yaml (unchanged)`, stream `native_cash`, decision completed Friday close, execution next session open, drift until next decision. History start in wrapper: 2016-01-01, 2900 daily bars requested.
- State schema in wrapper: decided, target, weights, log.

## Data inputs

- Split-adjusted daily bars (Alpaca; Yahoo without keys) of the 23 tradables from 2016, and Yahoo's daily VIX.

## Install and run

1. Clone the Test repo.
2. Read this doc and the strategy card named in Files.
3. Open the code files listed in Files and locate this strategy's sleeve / row.
4. Provide the data inputs listed below.
4a. STOP: obtain the upstream FinRL-X engine and its v1.2.1 config from its upstream source before running; it is not in this repo, so a recreation from this repo alone cannot run the engine. Do not substitute a reimplementation and present it as the original.
5. Run as described in Configuration / Full algorithm and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- The budget percentages follow the point count and the two extra 70% conditions in step 2 exactly.
- Only groups beating QQQ over 12 weeks can be active, at most two groups, with the fallback in step 6 when none is active.
- Names outside the new allocation are sold at the rebalance; no intraweek trade occurs.
- A recreation must also reproduce the recorded non-actions in step 10.
