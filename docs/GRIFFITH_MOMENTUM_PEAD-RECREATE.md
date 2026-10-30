# griffith-momentum-pead: Recreation package

## Provenance

- Canonical id: `griffith-momentum-pead`; canonical name: Momentum plus earnings drift; aliases: griffith_momentum_pead.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type momentum, family griffith, style evidence 'Earnings drift + momentum', universe SCOPE stocks (ETF basket excluded), asset US equities, timeframe 1d (20-session hold), creator 'Griffith R4 tournament registration MOMENTUM_PEAD_COMBINATION_1_0_0, on Nasdaq's public earnings calendar'. Algorithm grade PARTIAL; gaps: entry/signal, exit and sizing not recorded in any consulted source. Those gaps are closed by the strategy card and code in Test cited below, which are the truth.
- Test catalog entry: `docs/CATALOG.json` entry 'griffith-momentum-pead' (status blocked: 1; card strategies/griffith/griffith-momentum-pead.md; master desk rows griffith_momentum_pead; code list as in Files).
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4609 entries, plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21337 entries; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47379 entries; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7855 entries; no path named for this id). Desk source /home/hatch/workspace/muse-desk-v3 was also read for the v3 engines named below. Code was found in Test, so nothing was vendored.

## What this strategy is

Buys a SCOPE stock that beats its consensus EPS while in a liquid momentum uptrend at the first open after the report and holds it 20 sessions, in equal weight (strategy card in Test, verbatim in substance).

## Full algorithm

Evaluation order in `sleeves/griffith/event_research.py` (class EarningsDrift, SPECS maps griffith_momentum_pead to MOMENTUM_PEAD_COMBINATION_1_0_0; HORIZON=20):
1. Universe: `universe()` = tape symbols from the Griffith tape feed excluding the vendored R4 lab ETF_BASKET (ETFs report no earnings).
2. Events: feed griffith_earnings_events (`sleeves/griffith/feedlib/griffith_earnings.py`): Nasdaq's public earnings calendar for the universe (reported EPS, consensus, release time), refreshed once per session at the open when in regular hours; known_events as of the pass.
3. Liquid-momentum SETUP set: for each symbol with bars, the vendored `strategy_tournament.evaluate_daily_candidate('LIQUID_MOMENTUM_TREND_1_0_0', raw_rows)` must return status SETUP on its last completed daily bar. That pure function requires at least 253 completed bars; trend = close > SMA200 and SMA50 > SMA200; 12-1 momentum = closes[-22]/closes[-253]-1 > 0; adv20 = mean of close x volume over the last 20 bars >= $20,000,000; passed = trend and momentum > 0 and adv20 >= 20M.
4. Trigger (`trigger()`): take the symbol's latest public report row; surprise_fraction = (actual - consensus) / |consensus|; a zero or missing consensus, or a surprise <= 0, produces no trigger. For this spec a trigger also requires the symbol to be in the SETUP set from step 3.
5. Entry session (`entry_session()`): a pre-market report on a trading day trades at that session's open; every other report trades at the next trading day's open. A name already active or held is skipped; one event per name at a time.
6. Book / sizing: the R4 lab equal-weight calendar-time portfolio: at each session's first pass, every active event whose age is under the horizon is targeted at weight 1/N (N = number of such active names) of the book; the card records a $100,000 book in equal calendar-time weights. Target intents carry price_hint = ask or last quote, order window 3600 s, and are emitted only when every target name has an ask or last quote; re-targeting is stamped once per day.
7. Exit: when minutes to close <= 25 and a held name's session count (trading days between entry and today + 1) >= 20, emit a market-on-close exit (type market, tif cls, window 3600 s). No price stop and no early target are in the code for this spec.
8. State: active events (entry session, event date, eps, consensus, seen flag) are pruned when a name is no longer held and was seen, or when its age exceeds the horizon.
Named divergences recorded in the engine header: Nasdaq's public calendar replaces the Alpha Vantage EARNINGS lane; history pages carry no release time, so a history day's reports count from the next open; entries are at the open after the event is public.

## Files in this repo

- This package: `docs/GRIFFITH_MOMENTUM_PEAD-RECREATE.md`
- Code (already in Test; nothing vendored): `sleeves/griffith/event_research.py` (EarningsDrift, SPECS, trigger, entry_session), `sleeves/griffith/vendor/griffith/strategy_tournament.py` (CANDIDATES registration lines 37-40 and evaluate_daily_candidate lines 54-73), `sleeves/griffith/feedlib/griffith_earnings.py`, `sleeves/griffith/feedlib/griffith.py`
- Strategy card: `strategies/griffith/griffith-momentum-pead.md`; rule lines: `docs/verify/griffith.md`
- Catalog / accounting: `docs/CATALOG.json`, `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

- Registration: MOMENTUM_PEAD_COMBINATION_1_0_0, rule 'liquid_momentum_trend_and_positive_pead', horizonSessions 20.
- SleeveConfig in code: family event_research, cadence_s 300, schedule rth, params spec=MOMENTUM_PEAD_COMBINATION_1_0_0, horizon_sessions 20, prior_quarters 8 (the prior-quarters constant belongs to the sibling SUE spec and is not used by this spec's trigger).
- Book: $100,000 per the card, equal calendar-time weights 1/N. Universe, asset, timeframe as in Provenance.

## Data inputs

- Nasdaq archived earnings calendar pages and live quotes (card); Alpaca IEX raw daily bars of the SCOPE universe (last 550 sessions per the card) and Yahoo daily bars, via the Griffith tape feed in `sleeves/griffith/feedlib/griffith.py`.
- Quotes: equity quotes (ask / last) for target pricing.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Confirm the files in Files in this repo are present; the sleeve entry point is `sleeves/griffith/event_research.py` `sleeves()` returning EarningsDrift('griffith_momentum_pead', 'MOMENTUM_PEAD_COMBINATION_1_0_0').
3. Wire the griffith_earnings_events feed and the Griffith tape feed, plus equity quotes, in the form the code expects.
4. Register the sleeve with cadence 300 s, rth schedule, and the Configuration above.
5. Run one evaluation on fixture data and confirm the Verification checks before any live use.

## Verification

No dedicated test file for this exact id was found in the Test tree. Behaviour checklist from the code:
- A report with surprise <= 0, zero consensus, or a name not SETUP under the liquid-momentum rule (close/SMA, 12-1 momentum, adv20) produces no entry.
- A pre-market report enters that session; any other report enters the next session; a held or already-active name is not re-entered.
- With N active events, each target weight is exactly 1/N, re-targeted at the session's first pass.
- A held position exits market-on-close in the last 25 minutes of its 20th session (entry session counts as 1), and no earlier price move exits it.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
