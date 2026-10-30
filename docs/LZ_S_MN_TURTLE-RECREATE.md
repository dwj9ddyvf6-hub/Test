# lz_s_mn_turtle: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Turtle (Midna port)", type breakout, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_turtle` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- Strategy card in Test: `strategies/midna/mn-turtle.md` (Turtle System 1), whose Code section names only master-desk code: `sleeves/midna/board.py`, `sleeves/midna/vendor/midna/board_signals.py`, `sleeves/midna/common.py` - all present in Test, with rule lines in `docs/verify/midna.md` citing exact board.py / board_signals.py line ranges for every rule below. No module named s_mn_turtle exists in any searched repo (the only turtle-named sleeve module in Test is the distinct options form, sleeves/s_mn_opt_turtle.py); the lane's running logic is the board code plus its sleeves.json lane row, recorded as found.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

Turtle System 1 breakout lane: buys 20- or 55-day closing breakouts with Turtle unit sizing and pyramiding, exits on a 2N stop or a 10-day low (card).

## Full algorithm

In evaluation order, from the card and the verify rule lines (code: `sleeves/midna/board.py`, `sleeves/midna/vendor/midna/board_signals.py`):

1. Entry signal (board_signals.py:120-165; board.py:184-206): a close above the prior 20-day (or 55-day) high, new today; at most 4 names, alphabetical (BOARD_MAX_NAMES=4 per the lane row's research line).
2. Skip rule (board.py:194-202): a 20-day breakout right after a winning exit is skipped once; the 55-day one is taken.
3. Pyramiding (board.py:159-171): add a unit at each +0.5N over the last add, up to 4 units. N = ATR(20).
4. Exits (board.py:114-133, 144-157, 225-247): stop at entry - 2N (raised with adds), on any regular-hours print; signal exit on a close under the prior 10-day low. The accounting exit record names the same plan: 'turtle ATR stop / exit10', stop_pct 99.0 (no percentage stop), max_bars 0.
5. Sizing (board.py:34-37, 48-54): unit = min(floor(1% of equity / N), floor(cash / price)), BOARD_RISK=0.01 per the lane row's research line. The Lazarus lane wrapper sizing is the sleeves.json block in Configuration ($1,000 a position, 2 slots, $2,000 budget); the two records describe the upstream book and the port respectively.

Accounting / lane-config wrapper (md2 catalog text, identical in the sleeves.json row): entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: turtle ATR stop / exit10", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time", "plan_overrides": []}. The lane config also records the removed desk-wide gate for these Lazarus ports: the entry policy named midna_block is the upstream red-day buy block (QQQ red AND VIX up AND the name red on the session); the master-desk ports drop that gate, the desk halt, the cross-lane held-by-account check and the shared account cash pool (`sleeves/midna/lanes.py` header) - where a section below says the gate was removed, the config row still naming the policy is the historical record, not a live gate.

## Files in this repo

- This package: `docs/LZ_S_MN_TURTLE-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Strategy card: `strategies/midna/mn-turtle.md`
- Code (already in Test): `sleeves/midna/board.py`, `sleeves/midna/vendor/midna/board_signals.py`, `sleeves/midna/common.py`; lane row in `sleeves/lazarus/vendor/lazarus/sleeves.json`
- Rule lines: `docs/verify/midna.md` (Turtle System 1 section)
- Nothing was vendored: every code file named here was already in Test.

## Configuration

- Universe: Midna's swing basket (card); asset US equities; timeframe 1d. Unit risk 1% of equity / ATR(20); max 4 names; up to 4 units per name.
Lane-config sizing block (sleeves.json row): budget_usd 2000, max_slots 2, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Research line in the row: Midna board.ts turtle enter20/enter55 BOARD_MAX_NAMES=4 BOARD_RISK=0.01.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Completed daily bars of the swing basket (card Data).

## Install and run

1. Clone the Test repo.
2. Take the code files at the exact paths in Files, with the lane row for this id in `sleeves/lazarus/vendor/lazarus/sleeves.json`.
3. Configure the lane with the entry, exit and sizing values in Configuration; confirm the sleeve id in code matches the s_mn_ form of the canonical id.
4. Wire the Data inputs: the sleeve_midna fire file / Tensor-bundle fire channel and the bar / position views the code names.
5. First evaluation: run one evaluation with no qualifying fire / signal and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No dedicated test file for this lane was found in Test; rule lines at `docs/verify/midna.md`. Behaviour checklist:

- Entry only on a close above the prior 20- or 55-day high that is new today, at most 4 names in alphabetical order.
- A 20-day breakout immediately after a winning exit is skipped once; a 55-day breakout in the same situation is taken.
- Units add at each +0.5N to at most 4 units, sized min(floor(1% of equity / ATR20), floor(cash / price)).
- Exit on any regular-hours print at or under entry - 2N (as raised by adds), or on a close under the prior 10-day low.
