# lz_s_mn_hourly_1d: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Hourly 1D (Midna port)", type forecast and ML models, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_hourly_1d` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- Strategy card in Test: `strategies/midna/mn-hourly-playbook.md` (Hourly Tensor playbook; the 1D lane of the playbook). Lane code in Test: `sleeves/midna/lanes.py`, whose header documents the s_mn_hourly_1d lane in full, and `sleeves/midna/hourly.py` (the playbook engine).
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

Hourly Tensor playbook lane fed by the tracker's 1D fires: it buys first-of-setup Tensor consensus-buy fires on the daily timeframe and exits on the calibrated plan, else a 40-session time exit (lanes.py header; card).

## Full algorithm

In evaluation order:

1. Fire (card + `sleeves/midna/hourly.py` header): a gap20, first-of-setup 1H consensus-buy fire of the swing basket; a fire is decided once (seen) and skipped when its setup episode already traded, when its unit/tags match a killed rule, when it is not tradeable or not from Yahoo bars, when dv20 (mean of the last 20 close x volume) is unknown or below $1,000,000. For this lane the fires are the canonical tracker's 1D fires (sleeve_midna.hourly_fires) per `sleeves/midna/lanes.py`.
2. Entry window (lanes.py): entries on the session after the fire's daily bar, window [09:30, + 65 min], a DAY limit capped at the fire close + 5%; lane cap for 1d is 5 in the playbook engine (card sizing: $100,000 account, 20 slots of min($5,000, 1% of dv20), lane caps 1h 5 / 1d 5 / 1w 10). The Lazarus lane instead runs its own config sizing: $1,000 a position, 2 slots, $2,000 budget, dv20 >= $100,000, cap 1.0% of dv20 (sleeves.json row, quoted in Configuration); both records are kept because they describe the upstream book and the Lazarus port respectively.
3. Plan / exit: the plan rules.ts planForNewEntry gives (the tracker's calibrated stop / max bars, else 40 sessions) per lanes.py; accounting exit record: stop_pct 15.0, max_bars 40, hold_from plan, hold unit 1d, rest time. Exit in regular hours on a fresh quote at the plan stop or the time exit (close of the max_bars-th session).
Accounting / lane-config wrapper (md2 catalog text, identical in the sleeves.json row): entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: calibrated plan / time exit 40 sessions", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 15.0, "max_bars": 40, "rest": "time", "plan_overrides": []}. The lane config also records the removed desk-wide gate for these Lazarus ports: the entry policy named midna_block is the upstream red-day buy block (QQQ red AND VIX up AND the name red on the session); the master-desk ports drop that gate, the desk halt, the cross-lane held-by-account check and the shared account cash pool (`sleeves/midna/lanes.py` header) - where a section below says the gate was removed, the config row still naming the policy is the historical record, not a live gate.

## Files in this repo

- This package: `docs/LZ_S_MN_HOURLY_1D-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Strategy card: `strategies/midna/mn-hourly-playbook.md`
- Code (already in Test): `sleeves/midna/lanes.py` (MidnaLane for s_mn_hourly_1d; resolves its row from the Lazarus CONFIG), `sleeves/midna/hourly.py` (playbook engine: evaluatePass exits and considerEntries, entryWindow, timeExitAt, planForNewEntry), `sleeves/lazarus/vendor/lazarus/sleeves.json` (lane row s_mn_hourly_1d)
- Rule lines: `docs/verify/midna.md` (Hourly Tensor playbook section)
- Nothing was vendored: every code file named here was already in Test.

## Configuration

Lane-config sizing block (sleeves.json row): budget_usd 2000, max_slots 2, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Playbook book (card): $100,000 account, 20 slots of min($5,000, 1% of dv20), lane caps 1h 5 / 1d 5 / 1w 10. Research lines in the row: Midna rules.ts Hourly 1D; LANE_CAPS 1d:5 MAX_DELAY 65.
- Cadence beyond the entry window: not in the record.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- The hourly watch's inbox (tensor-watch port) per the card; daily bars for the 1D fires.

## Install and run

1. Clone the Test repo.
2. Take the code files at the exact paths in Files, with the lane row for this id in `sleeves/lazarus/vendor/lazarus/sleeves.json`.
3. Configure the lane with the entry, exit and sizing values in Configuration; confirm the sleeve id in code matches the s_mn_ form of the canonical id.
4. Wire the Data inputs: the sleeve_midna fire file / Tensor-bundle fire channel and the bar / position views the code names.
5. First evaluation: run one evaluation with no qualifying fire / signal and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No dedicated test file for this lane was found in Test; rule lines at `docs/verify/midna.md`. Behaviour checklist:

- A 1D fire that is not first-of-setup, matches a killed rule, is not tradeable, or has dv20 < $1,000,000 produces no entry.
- Entry occurs only on the session after the fire's daily bar, inside [09:30, +65 min], as a DAY limit capped at fire close + 5%.
- Lazarus-lane sizing is $1,000 a position, at most 2 slots, $2,000 budget, dv20 floor $100,000.
- Exit fires on the calibrated plan stop / max bars, defaulting to the 40-session time exit, and on no other condition.
