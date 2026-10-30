# killed-pead-price-surprise - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `killed-pead-price-surprise`
- Canonical name: PEAD price surprise
- Aliases: killed_pead_price_surprise
- Type: momentum; Family: killed; Algorithm grade in ALL-SLEEVES accounting: PARTIAL (gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source']; the accounting's entry/exit/sizing fields are empty, so the algorithm below is taken from the code in Test, which is the truth)
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "PEAD price surprise" (also `docs/ALL-SLEEVES.md`); local census copy at research_notes/sleeve-census-20261029/accounting.json. doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "PEAD price surprise" (also docs/ALL-SLEEVES.md); Test catalog entry 'killed-pead-price-surprise' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Family card in Test: `strategies/killed/killed-pead-price-surprise.md`.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus file reads of sleeves/killed/events.py, sleeves/killed/common.py, the family card, and packages/claude/master-desk-parity-tools/tools/parity/killed_pead.py); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching trullas, r19 timing hour, or killed pead path); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no matching path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path; the only pead-named file is an unrelated outside_ideas/code/pead_filters.py, which is not this strategy's code). Code was found in Test, so nothing was vendored.
- Classification evidence in the accounting: Earnings drift | Classification 2026-10-30: momentum (code evidence): Master desk sleeves/killed/events.py read: PeadPriceSurprise goes long the top price surprise quintile at the open two sessions after earnings and holds 1, 5, 10 or 20 sessions, a post earnings drift trade

## What this strategy is

PEAD price surprise. Long the top price-surprise quintile of earnings events, entered at the open two sessions after the report, in four equal holding tranches of 1, 5, 10 and 20 sessions. This is a killed (rejected) research study, forward-tested on the master desk in Test; it is not a live alpha claim.

Universe: Nasdaq earnings-calendar names; Asset class: US equities; Timeframe: 1d (event).

## Full algorithm

Evaluation order in sleeves/killed/events.py, class PeadPriceSurprise (SLEEVE_ID killed_pead_price_surprise), plan(view, st, tb):
1. Gate: f = view.extra["killed_pead"]; require f present, f["ready"] true, st["seen"] not equal to f["t"], and common.signal_day(view.now) not None (a pass of a trading session before its auction cutoff, so the signal session is the session before the pass session). Then set st["seen"] = f["t"].
2. Surprise (computed by the feed, desk/feedlib/killed_data per the class docstring): S = (P[t+1] / P[t-1] - 1) - (SPY[t+1] / SPY[t-1] - 1) on adjusted daily closes, where t is the Nasdaq calendar's event date.
3. Cohort: symbols in f["cohort"], i.e. S above the quarter's 80th percentile cut f["cut"]. Named divergence in the code: the study cut each calendar quarter's quintiles after the quarter; forward, the cut is the 80th percentile (pd.qcut's top-bin edge) of the PREVIOUS complete calendar quarter's surprises. Other named divergences: universe is Nasdaq calendar symbols listed in the NASDAQ Trader directories instead of Alpaca /v2/assets; adjusted closes are the hub's (Alpaca adjustment=all when keyed, else Yahoo's dividend-adjusted close).
4. For each cohort symbol in sorted order, for each hold h in PEAD_HOLDS = (1, 5, 10, 20): add a long tranche with notional CAPITAL / 1500 = 100000 / 1500 (about $66.67), arm "pead:<h>", enter at the open of t+2, exit at the close of entry + (h - 1) sessions (add_sessions(d, h - 1), "close"), why recorded with the event date, S, and the cut, event = f["t"].
5. Emit one signal Intent on SPY with signal_key pead:<event date> and a reason naming the cohort size, the number of events, the cut, and the quarter the cut came from.
Exit rule: each tranche exits market-on-close at the close of its hold's last session (entry session counted as day 1). There is no stop or target in the code.
Study source pinned in the code: pead/code/04_backtest.py, blob 71819ef28c26d078217585a2da603db9d65d207e, results pead/results_dev.md blob bb43e2520265a954f2782afece7c0e31f0c72784, pre-registration pead/PRE_REGISTRATION.md blob c94203dd172049213665b4fdb719feb8bf96e37d (paths under workspace/alpaca-swing-desk/desk/research/ in the source record).
NEEDS in the code: feeds [killed_pead], quotes source equity. No SCHEDULE or CADENCE override in the class (the family defaults apply; not in the record for this class beyond the code cited).

Shared tranche machinery (sleeves/killed/common.py, in Test): CAPITAL = 100000.0. A sleeve writes each trade into its state as a tranche (symbol, direction, entry moment, exit moment) when its rule fires; the ledger then drives orders: an "open" entry trades at the first pass of the entry session (marketable, until 11 minutes before the close); a "close" entry is market-on-close routed inside the auction window 30 to 11 minutes before the close (MOC_OPEN_MIN 30.0, MOC_CUTOFF_MIN 11.0); a "close" exit is market-on-close on the exit session (an exit session already past exits at the next pass); an "open" exit trades at the first pass of the exit session. Tranches of the same symbol net exactly as the study's trades do. Per-tranche P&L uses the tranche's recorded entry and exit reference prices; engine fills carry the real prices. Named common divergences in the code: fills are engine children, not the study's open/close prints; a tranche the book did not fill is re-traded at the next pass; per-trade costs are the engine's fills and fees, not the study's flat bp charge.

## Files in this repo

- Strategy code: `sleeves/killed/events.py` (in Test; the class named in the Full algorithm section)
- Shared family machinery: `sleeves/killed/common.py` (in Test; tranche ledger, CAPITAL, session and market-on-close helpers)
- Family registry: `sleeves/killed/killed_studies.py` (in Test)
- Feed builder: `sleeves/killed/feedlib/killed_data.py` (in Test); master-desk mirror at `packages/claude/master-desk-sleeve-port-library/desk/sleeves/killed/events.py` and `packages/claude/master-desk-sleeve-port-library/desk/sleeves/killed/common.py`
- Family card: `strategies/killed/killed-pead-price-surprise.md` (in Test)
- Parity test: `packages/claude/master-desk-parity-tools/tools/parity/killed_pead.py` (in Test)
- Rule lines: `docs/verify/killed.md` (in Test)

## Configuration

No row for this sleeve id in config/sleeves.json in Test (searched; the killed family runs on the master desk in Test, not the v3 roster). In-code configuration: SLEEVE_ID killed_pead_price_surprise; PARAMS {holds: [1, 5, 10, 20], entry: open of t+2, cohort: S above the quarter's 80th percentile, notional_per_tranche: CAPITAL/1500, removed_gates: []}; NEEDS {feeds: [killed_pead], quotes: {source: equity}}; family capital CAPITAL = 100000.0 in sleeves/killed/common.py.

## Data inputs

Nasdaq earnings calendar (event dates), NASDAQ Trader listings (universe), and daily adjusted bars of the event names and SPY (feed killed_pead in view.extra, built by desk/feedlib/killed_data pead_job per the events.py header; in Test at sleeves/killed/feedlib/killed_data.py); equity quotes.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and confirm the files listed in "Files in this repo" are present at the stated paths (the master-desk layout under packages/claude/master-desk-sleeve-port-library/ shows the desk-relative paths: desk/sleeves/killed/events.py and desk/sleeves/killed/common.py).
2. Place events.py and common.py with the rest of the killed family (killed_studies.py and the family contract, calendar, and util modules they import) so the class imports resolve.
3. Wire the feed named in Data inputs so view.extra carries the feed dict at evaluation time, and wire equity quotes.
4. Register the sleeve with the master-desk cycle under its SLEEVE_ID with the schedule and cadence stated in Configuration where the code states them; the tranche ledger in common.py drives the entry and exit orders at the moments stated in the Full algorithm section.
5. Run one evaluation on a fixture feed that satisfies the entry rule and confirm the tranches match the Verification checks before enabling live dispatch.

## Verification

- Parity test in this repo: packages/claude/master-desk-parity-tools/tools/parity/killed_pead.py runs the vendored study pead/code/04_backtest.py on synthetic cases and compares, per event, S against killed_data.surprise, top-quintile membership against killed_data.q80, and every hold's return against this sleeve's tranches (entered at t+2, exited at the close of entry + n - 1) priced on the same bars. Note the parity doc's own caveat: the sleeve uses the previous quarter's cut, a named divergence from the study's same-quarter cut.
- Fixture check: a cohort symbol produces exactly four tranches, one per hold 1, 5, 10, 20, each of notional 100000/1500, entering at the open of t+2 and exiting at the close of entry + hold - 1 sessions.
- Cut check: a symbol with S at or below the previous complete quarter's 80th percentile cut is not in the cohort and produces no tranches.
- Repeat check: a second feed with the same f["t"] produces no new tranches (st["seen"] guard).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
