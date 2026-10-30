# lz-wait-r2-dcyan: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "R2 Daily Cyan extended", type forecast and ML models, family lazarus, universe Tracker universe, asset class US equities, timeframe 1d. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources Test catalog entry/variants and md2 catalog entry/exit/strategy text. Aliases `lz_s_wait_r2_dcyan` and `lz_wait_r2_dcyan`.
- Strategy card in Test: `strategies/lazarus/lz-wait-r2-dcyan.md` (status live). Its Source row carries the family codename token, which is omitted here under the repo PII rule; the row reads: research lab frozen spec, wired on the master desk.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b24_Test_tree.txt in the run workspace, reused as the batch-start tree) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, strategies/, packages/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for this id. The code paths below are the paths named in the strategy card's Code section, verified present in the Test tree, and the named module was read and confirmed to carry this strategy's id / logic.

## What this strategy is

Buys the lab's 1D Cyan covered rule-search book picks on the tracker universe and holds 21 sessions (strategy card).

## Full algorithm

In evaluation order, from the strategy card in Test (`strategies/lazarus/lz-wait-r2-dcyan.md`) plus the accounting record:

1. Signal: a 1D-cyan-covered rule-search fire from the live lab.
2. Hold / exit plan: no stop (card), 21 sessions from the fill.
- Lane entry mechanics (strategy card in Test): buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.
- Accounting entry policy for the merged sleeve-feed alias (ALL-SLEEVES, md2 catalog text): {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}.
- Exit mechanics (strategy card): time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. The accounting exit text for the merged alias instead records the sleeve feed fire's plan (15% disaster stop / time exit) where the card records no stop; both readings are recorded here and the discrepancy is not resolved in the record.
- Sizing mechanics (strategy card): fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. The accounting graded sizing as a gap (not recorded in its consulted sources); the card values above are the Test record.
- This lane's sizing (card): $1,000 a position; K = min(20, ceil(20 x 21 / 126)) = 4.

## Files in this repo

- This package: `docs/LZ_WAIT_R2_DCYAN-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Strategy card: `strategies/lazarus/lz-wait-r2-dcyan.md`
- Code (already in Test): `sleeves/lazarus/lazarus.py` (its header describes the Lazarus runtime port carrying the non-Midna lanes of the lazarus-desk config, including the lazarus_feed WAIT lanes; the module was read and contains the intraweek and r2_dcyan lane ids), `sleeves/lazarus/vendor/lazarus/` (vendored lane package named in the card)
- Rule lines: `docs/verify/lazarus.md`
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Universe Tracker universe; asset class US equities; timeframe 1d; family lazarus.
- Position $1,000; K = min(20, ceil(20 x 21 / 126)) = 4 (card). Entry policy (accounting, merged alias): fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day.
- Cadence and state beyond the above: not in the record.

## Data inputs

- The lab's book outputs (card Data section).
- Sleeve-feed fires: sleeve_feed composer (tracker ledger + alt-data tags), shadow/paper_sleeve/live/sleeve_fires_v1.json (accounting filter record).

## Install and run

1. Clone the Test repo.
2. Take `sleeves/lazarus/lazarus.py` with the vendored lane package at `sleeves/lazarus/vendor/lazarus/` at the paths shown in Files.
3. Select the lane whose id is `lz-wait-r2-dcyan` in the Lazarus lane config the module carries; confirm its entry policy, hold and sizing match the Configuration section.
4. Wire the Data inputs so each evaluation carries the tracker fires / lab book outputs for this lane.
5. First evaluation: run one evaluation on a snapshot with no qualifying fire and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No per-sleeve test file for this id was found in Test; the rule lines are at `docs/verify/lazarus.md`. Behaviour checklist from the recorded algorithm:

- A fire is accepted only as a 1D-cyan-covered rule-search fire from the live lab; one position per symbol.
- Entry is a DAY limit at live price + 1%, capped at fire close + the lane band, from the open of the bar after the fire and inside the entry window; the fear_day policy values in Configuration hold exactly.
- Sizing is $1,000 a position with K = 4, whole shares, capped by the share of 20-day dollar volume and the lane budget/slots; sub-floor names are skipped.
- Exit is 21 sessions from the fill (card plan), executed as the recorded time-exit mechanics; no stop is taken under the card reading.
