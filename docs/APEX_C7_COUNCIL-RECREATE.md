# apex-c7-council - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `apex-c7-council`
- Canonical name: APEX C7: COUNCIL
- Aliases: apex_c7_council, apex_council_btc
- Type: other; Family: apex; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "APEX C7: COUNCIL" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "APEX C7: COUNCIL" (also docs/ALL-SLEEVES.md); Test catalog entry 'apex-c7-council' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start, 4,430 entries; plus file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,441 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Where the accounting graded PARTIAL, those gaps are gaps of the accounting's consulted sources only; the Test strategy card and code cited below are the fuller record used here, and any remaining gap is marked 'not in the record' in place.

## What this strategy is

APEX C7: COUNCIL. Universe in accounting: QQQ, TQQQ, GLD, BIL, BTC/USD; QQQ listed options. Asset class in accounting: US ETFs, ETF options and Bitcoin. Timeframe in accounting: 1d (monthly options). Creator in accounting: APEX research desk (Cursor2), round 3 C7 and the invention report's Council.

## Full algorithm

From the card (`strategies/apex/apex-c7-council.md`) and the rule lines in `docs/verify/apex.md`, in evaluation order. This canonical strategy groups two running rows (variants in the accounting):

- Row `apex_c7_council`: Nasdaq (N6) 55%, Gold 25%, Bitcoin none, Variance Value 20%.
- Row `apex_council_btc`: Nasdaq (N6) 49.5%, Gold 22.5%, Bitcoin 10%, Variance Value 18%.

Books:
1. Nasdaq book: N6, 1/2 x (APEX-50F target + GESTALT leverage), with the 0.20 band. (Rule lines: `sleeves/apex/feedlib/apex_rules.py:364-369,376-380`; `sleeves/apex/vendor/apex/inventions.py:248-251`.)
2. Gold book: gold futures' trend score x min(2, 20% / HAR volatility), 0.20 band, held as GLD. (Rule lines: `sleeves/apex/vendor/apex/round3.py:212-221`; `sleeves/apex/feedlib/apex_rules.py:372-373`.)
3. Options book: the Variance Value rule (as O6) on its share of the book. (Rule lines: `sleeves/apex/vendor/apex/opt_strategies.py:198-218`; `sleeves/apex/apex.py:586-588`.)
4. Bitcoin variant only: 10% at Bitcoin's trend score x min(1, 20% / HAR volatility), 0.20 band; the other books keep C7's proportions on the remaining 90%. (Rule lines: `sleeves/apex/feedlib/apex_rules.py:383-399`.) Named divergence recorded in the card and in `sleeves/apex/apex.py:53-56`: the invention report's 'Bitcoin capped at 10% of risk' was never coded by the source, so the desk takes the N4 Bitcoin sleeve on 10% of the book.

Exit: No stops: each book follows its target; option structures are held to expiry.

Sizing: Fixed shares of equity, the options book's T-bills = its share less its options' value. Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. Exposure books market-on-close; Bitcoin in the last 10 minutes of the equity session; a $1,000,000 book.

Common APEX core (from the other APEX cards and `sleeves/apex/vendor/apex/strategies.py`): trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. APEX-50F target = trend score x min(4, 50% / volatility). Decided on the last finished session; execution mapping per `sleeves/apex/apex.py` header: market-on-close in the next session; Nasdaq exposure up to 1x is QQQ, 1-3x is QQQ + TQQQ with QQQ + 3 x TQQQ = L, above 3x TQQQ alone at L / 3 on margin; idle capital in BIL unless the rule names another idle asset; shares = floor(weight x book equity / last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This recreation doc: `docs/APEX_C7_COUNCIL-RECREATE.md`
- Strategy card: `strategies/apex/apex-c7-council.md`
- Running code (already in Test): `sleeves/apex/apex.py` (rows `apex_c7_council` and `apex_council_btc`, both in VV_ROWS so they run as VVSleeve; TITLES maps them to 'C7 COUNCIL' and 'Council with Bitcoin'; book $1,000,000 for option-carrying C7/Council per the module header), `sleeves/apex/apex_options.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex_book.py`
- Vendored source (already in Test): `sleeves/apex/vendor/apex/round3.py`, `sleeves/apex/vendor/apex/inventions.py`, `sleeves/apex/vendor/apex/opt_strategies.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/apex/vendor/apex/engine.py`, `sleeves/apex/vendor/apex/sim.py`, `sleeves/apex/vendor/apex/series.py`, `sleeves/apex/vendor/apex/surface.py`, `sleeves/femto/vendor/aurelia/features.py`
- Rule lines: `docs/verify/apex.md` (APEX C7: COUNCIL section). Tests in Test: `tests/test_apex.py` re-hashes every vendored excerpt block.
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

- Universe: QQQ, TQQQ, GLD, BIL, BTC/USD; QQQ listed options. Timeframe: 1d (monthly options). Book: $1,000,000 (option-carrying C7/Council book per `sleeves/apex/apex.py` header).
- Variant shares: see the two rows in the Full algorithm. Cadence / schedule: per `sleeves/apex/apex.py`: CADENCE 1800 s, SCHEDULE "rth&close-400:close-20" for exposure books; OPTION_SCHEDULE "rth&close-45:close-15", OPTION_CADENCE 600 s for option decisions; decisions computed by the apex_decisions job after each close (weekday 16:20-23:59 ET, 1800 s).

## Data inputs

Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), GC=F, BTC-USD, ^TNX, ^VIX, ^SOX and SMH; recomputed after each close. The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. (Per the card.)

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc, the strategy card / family card named in Files, and `docs/ALL-SLEEVES.json` for the accounting record.
3. Use the code files listed in Files as the runnable logic, preserving their exact delegation and parameter values.
4. Supply the data inputs named above in the shape the code expects.
5. Run on the cadence and in the window stated in Configuration / Full algorithm; exits / rebalances are evaluated in the order the algorithm states.
6. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- Tests in Test: `tests/test_apex.py` (vendored excerpt re-hash).
- The Nasdaq book target is 1/2 x (APEX-50F target + GESTALT leverage) on its stated share (55% base row, 49.5% Bitcoin row), moved only on a 0.20 band change or to 0 as the common core states.
- The gold book is trend score x min(2, 20% / HAR volatility) on its stated share, held as GLD; the Bitcoin row, where present, is trend score x min(1, 20% / HAR volatility) on 10%.
- Option structures are held to expiry, are whole contracts only (under one skipped), and decide only in 15:15-15:45 ET.
- No stop is ever emitted.
