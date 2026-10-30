# killed-pead-spillover-scalp - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `killed-pead-spillover-scalp`
- Canonical name: Earnings-day overnight scalp
- Aliases: killed_pead_spillover_scalp
- Type: momentum; Family: killed; Algorithm grade in ALL-SLEEVES accounting: PARTIAL (gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source']; the accounting's entry/exit/sizing fields are empty, so the algorithm below is taken from the code in Test, which is the truth)
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Earnings-day overnight scalp" (also `docs/ALL-SLEEVES.md`); local census copy at research_notes/sleeve-census-20261029/accounting.json. doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Earnings-day overnight scalp" (also docs/ALL-SLEEVES.md); Test catalog entry 'killed-pead-spillover-scalp' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Family card in Test: `strategies/killed/killed-pead-spillover-scalp.md`.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus file reads of sleeves/killed/events.py, sleeves/killed/common.py, the family card, and packages/claude/master-desk-parity-tools/tools/parity/killed_pead.py); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching trullas, r19 timing hour, or killed pead path); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no matching path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path; the only pead-named file is an unrelated outside_ideas/code/pead_filters.py, which is not this strategy's code). Code was found in Test, so nothing was vendored.
- Classification evidence in the accounting: Earnings overnight | Classification 2026-10-30: momentum (code evidence): Master desk sleeves/killed/events.py read: PeadSpilloverScalp buys at the earnings day close when the day return net of cost is positive and sells at the next open, riding overnight continuation

## What this strategy is

Earnings-day overnight scalp. On a stock's earnings day, buy the close when the day's return net of cost is positive, and sell at the next session's open. This is a killed (rejected) research study, forward-tested on the master desk in Test; it is not a live alpha claim.

Universe: Nasdaq earnings-calendar names; Asset class: US equities; Timeframe: 1d (overnight).

## Full algorithm

Evaluation order in sleeves/killed/events.py, class PeadSpilloverScalp (SLEEVE_ID killed_pead_spillover_scalp), plan(view, st, tb):
1. Gate: plan only inside the market-on-close window (common.in_moc_window: regular session, 11 to 30 minutes to the close) and only once per session day (st["day"] guard).
2. Feed: f = view.extra["killed_spillover"]; require f present and f["t"] equal to today. Priced events are the events in f["events"] with both a last price and a previous close; if events exist but none are priced, return nothing (the job has not priced today's events yet).
3. For each priced symbol in sorted order: px = a fresh live last price (common.fresh_last, quote at most 900 s old) or the feed's last; r = px / prev_close - 1.0 - SPILL_COST, with SPILL_COST = 0.0015 (0.15%).
4. Entry rule: if r > SPILL_FILT, with SPILL_FILT = 0.0001 (+0.01%), add a long tranche: notional CAPITAL / 250 = 100000 / 250 = $400, arm "spill", enter at the close of day t (market-on-close), exit at the open of the next session (add_sessions(d, 1), "open"), why recorded as the r_prev_net value, event = t.
5. Emit one signal Intent on SPY with signal_key spill:<date> and a reason counting how many of the priced earnings events passed.
Exit rule: the tranche exit above, the next session's open. There is no stop, target, or other exit in the code.
Study source pinned in the code: pead/v1_spillover_dev_2026-10-02.py, blob 42331b228ec47d4d3f6bbf58e16da35e12bf25fe, with its pre-registration pead/v1_spillover_prereg_2026-10-02.md, blob 9926c2587a58a87274cf2a37c46f1f0d306dcca9 (paths under workspace/alpaca-swing-desk/desk/research/ in the source record).
Schedule and cadence in the code: SCHEDULE = "open+0:open+30,close-35:close-11", CADENCE = 120. NEEDS = feeds [killed_spillover], quotes source equity.
Named divergences in the code: c_t is the live price the spillover job reads 15:28-15:40 ET (the order is the market-on-close, the study's c_t); c_{t-1} is the previous session's daily close; universe is Nasdaq calendar symbols listed in the NASDAQ Trader directories instead of Alpaca /v2/assets.

Shared tranche machinery (sleeves/killed/common.py, in Test): CAPITAL = 100000.0. A sleeve writes each trade into its state as a tranche (symbol, direction, entry moment, exit moment) when its rule fires; the ledger then drives orders: an "open" entry trades at the first pass of the entry session (marketable, until 11 minutes before the close); a "close" entry is market-on-close routed inside the auction window 30 to 11 minutes before the close (MOC_OPEN_MIN 30.0, MOC_CUTOFF_MIN 11.0); a "close" exit is market-on-close on the exit session (an exit session already past exits at the next pass); an "open" exit trades at the first pass of the exit session. Tranches of the same symbol net exactly as the study's trades do. Per-tranche P&L uses the tranche's recorded entry and exit reference prices; engine fills carry the real prices. Named common divergences in the code: fills are engine children, not the study's open/close prints; a tranche the book did not fill is re-traded at the next pass; per-trade costs are the engine's fills and fees, not the study's flat bp charge.

## Files in this repo

- Strategy code: `sleeves/killed/events.py` (in Test; the class named in the Full algorithm section)
- Shared family machinery: `sleeves/killed/common.py` (in Test; tranche ledger, CAPITAL, session and market-on-close helpers)
- Family registry: `sleeves/killed/killed_studies.py` (in Test)
- Feed builder: `sleeves/killed/feedlib/killed_data.py` (in Test); master-desk mirror at `packages/claude/master-desk-sleeve-port-library/desk/sleeves/killed/events.py` and `packages/claude/master-desk-sleeve-port-library/desk/sleeves/killed/common.py`
- Family card: `strategies/killed/killed-pead-spillover-scalp.md` (in Test)
- Parity test: `packages/claude/master-desk-parity-tools/tools/parity/killed_pead.py` (in Test)
- Rule lines: `docs/verify/killed.md` (in Test)

## Configuration

No row for this sleeve id in config/sleeves.json in Test (searched; the killed family runs on the master desk in Test, not the v3 roster). In-code configuration: SLEEVE_ID killed_pead_spillover_scalp; SCHEDULE open+0:open+30,close-35:close-11; CADENCE 120; PARAMS {filter: c_t/c_{t-1} - 1 - 0.0015 > 0.0001, entry: close of t (market-on-close), exit: open of t+1, notional: CAPITAL/250 = $400, removed_gates: []}; NEEDS {feeds: [killed_spillover], quotes: {source: equity}}; family capital CAPITAL = 100000.0 in sleeves/killed/common.py.

## Data inputs

Nasdaq earnings calendar for the day's events (feed killed_spillover in view.extra, built by desk/feedlib/killed_data spillover_job per the events.py header; in Test at sleeves/killed/feedlib/killed_data.py); each event's live last price (read 15:28-15:40 ET in the code's divergence note; the family card records live quotes 15:27-15:41 ET) and the previous session's daily close; live equity quotes for fresh_last.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and confirm the files listed in "Files in this repo" are present at the stated paths (the master-desk layout under packages/claude/master-desk-sleeve-port-library/ shows the desk-relative paths: desk/sleeves/killed/events.py and desk/sleeves/killed/common.py).
2. Place events.py and common.py with the rest of the killed family (killed_studies.py and the family contract, calendar, and util modules they import) so the class imports resolve.
3. Wire the feed named in Data inputs so view.extra carries the feed dict at evaluation time, and wire equity quotes.
4. Register the sleeve with the master-desk cycle under its SLEEVE_ID with the schedule and cadence stated in Configuration where the code states them; the tranche ledger in common.py drives the entry and exit orders at the moments stated in the Full algorithm section.
5. Run one evaluation on a fixture feed that satisfies the entry rule and confirm the tranches match the Verification checks before enabling live dispatch.

## Verification

- Parity test in this repo: packages/claude/master-desk-parity-tools/tools/parity/killed_pead.py runs the vendored spillover study code on synthetic cases and compares its per-event cohort exactly with this sleeve's rule (buy the event-day close when c_t / c_{t-1} - 1 - 0.0015 > 0.0001, sell the next open).
- Fixture check: an event with px / prev_close - 1 - 0.0015 exactly at or below 0.0001 produces no tranche; one above produces exactly one $400 long tranche entering at that day's close and exiting at the next session's open.
- Window check: a pass outside the 30-to-11-minutes-before-close window, or a second pass the same day, produces no new tranches.
- Unpriced check: events present with no priced event produces no tranches and does not consume the day guard in a way that blocks a later priced pass (the code returns before setting st["day"] only when events exist and none are priced; read the code for the exact guard order).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
