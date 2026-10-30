# apex-o9-omega: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX O9: OMEGA", type options directional, family apex, style "Trend x volatility + options overlays", universe "QQQ, TQQQ, BIL; QQQ listed options", asset class US ETFs and ETF options, timeframe 1d (monthly options), creator "APEX research desk (Cursor2), options study O9". Algorithm grade PARTIAL in the accounting, with recorded gaps: entry/signal rule, exit rule and sizing not recorded in any consulted source. Alias `apex_o9_omega` (test_catalog status: entry apex-o9-omega status_counts={'live': 1}).
- Test catalog entry `apex-o9-omega` (`docs/CATALOG.json`): status live, card `strategies/apex/apex-o9-omega.md`, code list naming the files in Files below.
- The rules the accounting lacked are held in the Test strategy card and in the code in this repo (named in Files); nothing beyond the card and that code is claimed.

## What this strategy is

APEX-50F Nasdaq exposure (the six-vote trend score times a walk-forward HAR volatility forecast, traded in QQQ / TQQQ with BIL for idle capital) plus all three APEX options overlays on the whole book's NAV: PHOENIX calls, the CHOP iron condor and the FEAR put spread. Book $1,000,000.

## Full algorithm

From the card `strategies/apex/apex-o9-omega.md` and the code: sleeve row `apex_o9_omega` in `sleeves/apex/apex_options.py` runs `O.overlay(x, s, c, t, ("phoenix", "chop", "fear"))` from `sleeves/apex/vendor/apex/opt_strategies.py` on an APEX-50F core (tags phx, chop, fear). Inputs are read at t-1. Evaluation order in the vendored `overlay` decide(): phoenix, then chop, then fear; the core plan is the APEX-50F plan (`live["plans"]["apex50f"]`).

1. Signals (vendored `build_inputs`): trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days; dd252 = level / rolling 252-day max of level - 1; vol30 = the 30-day implied vol (VXN surface); vol30_p80 = its rolling 252-day 80th percentile; hi10_prior = the prior 10-day high of the level (level shifted 1, rolling 10 max); month_start = first session of a month.
2. Core: APEX-50F Nasdaq exposure with its 0.20 band, in QQQ / TQQQ; a trend score of 0 holds only T-bills (BIL). The core trades market-on-close on the equity less the options' value.
3. PHOENIX (`_phoenix`): if phx legs are held, close the tag when the first leg's expiry is 30 days or less away, and return. Otherwise, using t-1 values (all must be finite): if dd252 <= -0.15 AND vol30 >= vol30_p80 AND level >= hi10_prior, open at-the-money calls (K = spot at t) at the expiry nearest 91 days (minimum 60), sized 0.05 x NAV / call price units; one position at a time (no new open while legs are held). If the quoted price is 0 or less, no open.
4. CHOP (`_chop`): only at a month start and only with no chop legs held. Trend votes T6 = round(trend[t-1] x 6) must be 2, 3 or 4. Expiry = the next monthly expiry at least 15 days out. With T = years to that expiry, sig = ATM implied vol at that expiry, w = sig x sqrt(T), units = NAV / spot: sell the call at spot x exp(+1w) and the put at spot x exp(-1w), buy the call wing at spot x exp(+2w) and the put wing at spot x exp(-2w), each leg NAV / spot shares (an iron condor). Held to expiry (no early exit rule in the code).
5. FEAR (`_fear`): only at a month start and only with no fear legs held. Using t-1 values: if vol30 >= vol30_p80 AND round(trend x 6) <= 2, at the expiry nearest 61 days (minimum 45): sell the 90% put (K = 0.90 x spot) and buy the 80% put (K = 0.80 x spot), each NAV / spot shares. Held to expiry.
6. Execution (sleeve header, `sleeves/apex/apex_options.py`): options decide once a session in the last 45 minutes (15:15-15:45 ET per the card; sleeve schedule `rth&close-45:close-15`, cadence 600 s), on the listed QQQ monthly and the strike nearest the model's, in whole contracts (a decision under one contract is skipped); a structure opened in one decision is one multi-leg package; single contracts are marketable limits. If the options cannot decide (no context, an error, an OPT-03 impossible-inputs refusal), the core still goes to its plan from the daily decision, net of the options held at their marks, in the window's second half.
7. No stop: exposure follows the target (card).

## Files in this repo

- This doc: `docs/APEX_O9_OMEGA-RECREATE.md`
- Strategy card: `strategies/apex/apex-o9-omega.md`; catalog: `docs/CATALOG.json` (entry apex-o9-omega); rule lines: `docs/verify/apex.md`.
- Sleeve code (already in Test): `sleeves/apex/apex_options.py` (row apex_o9_omega, OptionRow / OptionBook machinery) and `sleeves/apex/apex.py` (ApexOptionSleeve base, CAPITAL 1,000,000, OPTION_SCHEDULE / OPTION_CADENCE above).
- Vendored strategy code that runs the overlay logic: `sleeves/apex/vendor/apex/opt_strategies.py` (overlay, _phoenix, _chop, _fear, build_inputs) and `sleeves/apex/vendor/apex/strategies.py` (compute_signals, apex_target, APEX_50F).
- Feeds: `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_book.py`; features dependency named by the card: `sleeves/femto/vendor/aurelia/features.py`.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`.
- Code search: Silicon, quant-research-backup and Midna trees were searched for this sleeve id; the running code was found in Test only (Silicon holds unrelated APEX-vendor teardown research, not this sleeve).

## Configuration

- Sleeve id: `apex_o9_omega`; family apex_options; capital $1,000,000.
- Universe: QQQ, TQQQ, BIL; QQQ listed options. Timeframe: daily (1d), monthly options.
- Schedule `rth&close-45:close-15`; cadence 600 seconds; feeds apex and apex_live.
- Dividend assumption in the model surface: 0.55% (card and sleeve header). State: the frozen per-session options decision and the core plan are held in sleeve state (see apex.py / apex_options.py).

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.
- The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend (all per the card).

## Install and run

1. Clone the Test repo.
2. Place the Files above at their repo paths, preserving the `sleeves/apex/`, `sleeves/apex/feedlib/`, `sleeves/apex/vendor/apex/` and `sleeves/femto/vendor/aurelia/` layout so the relative imports in apex.py / apex_options.py resolve.
3. Register the sleeve through `sleeves/apex/apex_options.py` `sleeves()` (row apex_o9_omega, tags phx/chop/fear, core apex50f) with capital $1,000,000, the option schedule and 600-second cadence above.
4. Wire the apex and apex_live feeds: daily histories and plans (apex50f), plus the live option context (signals through the last finished session, today's QQQ price, T-bill rate, month start, surface, listed chain).
5. Call the sleeve's `signal(view)` on cadence during the option window; the options decision freezes once per session and the core trades market-on-close on equity less options value.
6. Verify against the Verification checklist before any live use.

## Verification

The vendored opt_strategies.py header records that `tests/test_apex.py` re-hashes its excerpt blocks in the source desk; no test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- PHOENIX opens only when all three t-1 conditions hold together (dd252 <= -0.15, vol30 >= its 252-day 80th percentile, level >= prior 10-day high), at the expiry nearest 91 days (at least 60), for 5% of NAV of premium units, and closes when 30 days or less remain.
- CHOP opens only at a month start with trend votes 2, 3 or 4, as a four-leg condor at +/-1 and +/-2 sigma-sqrt(T) strikes, NAV / spot shares a leg, next monthly expiry at least 15 days out; FEAR opens only at a month start with vol30 at or above its 80th percentile and trend votes at most 2, as a short 90% / long 80% put spread at the expiry nearest 61 days (at least 45).
- Neither CHOP nor FEAR re-opens while its legs are held, and both are held to expiry; a trend score of 0 leaves the core in BIL only.
- A decision under one whole listed contract is skipped, and an options-context failure still trades the core to its APEX-50F plan in the window's second half.
