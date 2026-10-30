# qr-bracketedoptionlawtransport: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "BOLT event tilt (SPY / QQQ)", type options directional, family quant_research, style "Options-implied event tilt", universe "SPY, QQQ; SPX and NDX options as information", asset class US ETFs (SPY, QQQ), timeframe "Event windows (about 10 sessions)", creator "BOLT, from the desk's ten-strategy repair review (R10) playbook". Algorithm grade PARTIAL in the accounting, with recorded gaps: entry/signal rule, exit rule and sizing not recorded in any consulted source. Alias `qr_bracketedoptionlawtransport` (test_catalog status: entry status_counts={'blocked': 1}).
- Test catalog entry `qr-bracketedoptionlawtransport` (`docs/CATALOG.json`): status blocked, card `strategies/quant_research/qr-bracketedoptionlawtransport.md`, code list naming `sleeves/quant_research/bolt.py`, the vendor bolt directory and `sleeves/quant_research/common.py`.
- The rules the accounting lacked are held in the Test strategy card and in the code in this repo (named in Files); nothing beyond the card and that code is claimed.
- Code provenance recorded in the sleeve header: quant-research-backup at commit d170596b, path `research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/bolt` (transport_kernel.py, admission.py, PRACTICAL_PLAYBOOK.md).

## What this strategy is

BOLT (Bracketed Option-Law Transport): a $1,000,000 50/50 SPY / QQQ book that records index-option bounds around FOMC and CPI releases and tilts to 25/75 either way only once 144 of its own events have matured and a ridge forecast clears its cost and confidence tests; otherwise it holds 50/50 and keeps recording events as its training set.

## Full algorithm

From `sleeves/quant_research/bolt.py` (SID `qr_bracketedoptionlawtransport`; constants THETAS (0.005, 0.01, 0.02), RIDGE 100.0, EXIT_SESSIONS 5, OBS_SESSIONS 5, SUPPORT (80, 40, 24), COSTS_BP (15, 30, 45)) and the vendored kernel in Files:

1. Book: 50% SPY, 50% QQQ by default, bought at the first pass and left to drift; long only, no leverage, no cash target. Rebalance only when the target weights change; sizing weight x NAV at the ask, fractional shares (the card; the code sizes through `common.target_shares` / `common.rebalance`, sells before buys in effect through the rebalance helper). Sleeve cadence 300 s, RTH.
2. Events: FOMC statements (14:00 ET, the desk's FOMC list) and CPI releases (BLS schedule, 08:30 ET per the code's events()). An event is skipped when another FOMC, CPI or Employment Situation release falls strictly between 15:45 ET of its observation session and 09:35 ET of its exit session. Observation session = the 5th trading session before the event; exit session = the 5th trading session after it.
3. Snapshots: at 15:45 ET (the code accepts 15:45 <= time < 15:55) on the observation session and on the session before it, for SPX (SPXW) and NDX (NDXP): the bracketing expiries are the latest expiry strictly before the event and the earliest strictly after it, each after the snapshot and within 4 sessions of the event. Each expiry's forward is its put-call-parity forward (the strike where call and put mids are closest). Usable calls: two-sided, relative spread <= 20%, strikes within +/-10% of the forward, at least 9 strikes per expiry, thinned to strikes at least 0.5% apart, at most 41, normalised by the forward; the state grid adds outer states 0.5 and 2.0.
4. Bounds: for theta = 0.5%, 1% and 2%, the vendored `transport_kernel.quote_bounds` bounds the net up-crossing payoff (from at or below the forward to theta above it, less the reverse) over martingale laws inside the quote boxes: L, U per index, expiry pair and theta. An infeasible / blocked law records the event index as blocked and yields no features for it.
5. Features (36): per index and theta: L, U, U - L and their changes since the prior snapshot. Missing any component yields no features (no tilt).
6. Labels: each recorded event's label is the QQQ - SPY return between its frozen entry clocks (09:35 of the session after the observation session) and its exit clock (09:35 of the exit session), tilted or not.
7. Model and admission (`decide_tilt`): matured events in time order split oldest-first into training (all but the last 64), calibration (40) and development (24); fewer than 80 training events fails the vendored `admission.physical_admission` support check and the book holds 50/50. The ridge (penalty 100, train-only standardisation, unpenalised intercept) is fitted on the training events and calibrated on the calibration residuals; forecast f for the new event; lower bound lcb = f - 1.645 x std(calibration residuals) / sqrt(n_cal). Incremental benefit per cost scenario c in (15, 30, 45) bp: 0.25 x |f| - 2 x c / 10000 x 0.25 must clear the admission gate (the card states the same test as: every cost scenario leaving 0.25 x (|forecast| - 2 x cost) above 0.5%, and for a positive forecast its 95% lower bound above zero; signs must agree). A drawdown of 25% or more from the recorded peak NAV disables the tilt.
8. Tilt: a positive forecast holds 25% SPY / 75% QQQ, a negative one 75% / 25%, from 09:35 of the session after the observation session; one event at a time (no stacking while an event is active).
9. Exit: back to 50/50 at 09:35 ET of the 5th session after the event; the exit prices are recorded for the label whether or not the event was tilted.
10. Execution in the code: rebalances go through the common helper from the first pass at or after 09:35, sells before buys (the card's marketable limits 1% through the quote, each good for 30 minutes, are the master-desk execution terms; the code's named divergence 5 records market orders on the desk's quotes). Named divergences 1-4 in the sleeve header stand: SPXW / NDXP cash-index options from CBOE delayed quotes replace CME E-mini options and futures; BLS schedules plus the desk FOMC list are the calendar; the strike grid is thinned as in step 3; training events accumulate from the sleeve's own snapshots only.

## Files in this repo

- This doc: `docs/QR_BRACKETEDOPTIONLAWTRANSPORT-RECREATE.md`
- Strategy card: `strategies/quant_research/qr-bracketedoptionlawtransport.md`; catalog: `docs/CATALOG.json` (entry qr-bracketedoptionlawtransport); rule lines: `docs/verify/quant_research.md`.
- Sleeve code (already in Test): `sleeves/quant_research/bolt.py` (the Bolt sleeve, calendar job, snapshot / features / ridge / decide_tilt logic) and `sleeves/quant_research/common.py` (nav, target_shares, rebalance, sessions_between).
- Vendored kernel already in Test: `sleeves/quant_research/vendor/quant_research/r10/bolt/admission.py` (byte-identical to the quant-research-backup original at the path in Provenance; verified by hash this pass).
- Vendored into Test by this package: `engines/universe/qr-bracketedoptionlawtransport/transport_kernel.py`, byte-identical to the original in dwj9ddyvf6-hub/quant-research-backup at `research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/bolt/code/transport_kernel.py` (sha256 52633208db1a4986a512f5804e69c62e3c6cf424f1e79d9af12fa803e6dd301b). The card's Code row listed the vendor bolt directory as not in this repo; the kernel was missing from Test's vendored bolt folder (which holds only admission.py) and is now supplied at the engines/universe path above. In the master-desk layout the sleeve imports it as `vendor.quant_research.r10.bolt.transport_kernel` beside admission.py.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`.
- Code search: Silicon and Midna trees were searched for bolt / transport code; no matching file was found there. The kernel original was located in quant-research-backup as above (its tree listing is truncated by GitHub, so the file was confirmed by direct fetch).

## Configuration

- Sleeve id: `qr_bracketedoptionlawtransport`; family quant_research; capital $1,000,000; cadence 300 seconds; schedule rth.
- Universe (traded): SPY, QQQ. Information: SPX (SPXW) and NDX (NDXP) option chains, 0-12 days.
- Params (from the SleeveConfig): default weights SPY 0.5 / QQQ 0.5; tilts [0.25, 0.75] and [0.75, 0.25]; thetas [0.005, 0.01, 0.02]; ridge 100; exit_sessions 5; support [80, 40, 24]; margin_bp 50; cost_scenarios_bp [15, 30, 45]; drawdown_disable 0.25.
- Needs: feeds qr_macro_cal (the BLS calendar job) and qr_bolt_chains; equity quotes for SPY and QQQ.
- State schema: snaps, events, active, target, peak, log.

## Data inputs

- SPX and NDX option chains (0-12 days) on the snapshot passes, with spot levels.
- The BLS CPI and Employment Situation schedules (fetched each weekday morning by the qr_macro_cal job; a failed fetch keeps the last snapshot) and the desk's FOMC list.
- SPY / QQQ quotes and the book's NAV / positions for the rebalance and the drawdown peak.

## Install and run

1. Clone the Test repo.
2. Place `sleeves/quant_research/bolt.py` and `sleeves/quant_research/common.py` at their repo paths, the vendored `admission.py` at its vendored path above, and the vendored `transport_kernel.py` from `engines/universe/qr-bracketedoptionlawtransport/` beside it in the runtime's vendor layout (`vendor/quant_research/r10/bolt/`), so the sleeve's kernel import resolves.
3. Register the sleeve (class Bolt, `sleeves()` returns it) with the Configuration values above.
4. Wire the feeds: qr_macro_cal (calendar cache), qr_bolt_chains (chains and spots on snapshot passes only, gated by `snapshot_due`), and SPY / QQQ equity quotes.
5. Call the sleeve's `signal(view)` every 300 seconds in RTH; snapshots are taken only on the 15:45 passes, tilts are decided at 09:35 of the entry session, and the restore fires at 09:35 of the exit session.
6. Verify against the Verification checklist before any live use. The accounting and catalog record this strategy as blocked; the tilt cannot fire until 144 of its own events have matured.

## Verification

No dedicated test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- With fewer than 80 matured training events (or 40 calibration / 24 development), or with any feature missing, or at a drawdown of 25% or more, the target stays 50/50 and the event is still recorded with its features and outcome.
- A colliding event (another FOMC, CPI or jobs release inside the observation-to-exit window) is skipped entirely.
- A snapshot with fewer than 9 usable strikes on either bracketing expiry, or an infeasible bound, yields no features for that index.
- An admitted positive forecast tilts to 25% SPY / 75% QQQ and a negative one to 75% / 25%, from 09:35 of the session after the observation session, restoring 50/50 at 09:35 of the 5th session after the event; a second event cannot stack while one is active.
- The vendored transport_kernel.py in this repo hashes to the quant-research-backup original named in Files.
