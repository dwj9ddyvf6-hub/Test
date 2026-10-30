# lz_s_mn_hourly: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Hourly (Midna port)", type forecast and ML models, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_hourly` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- Strategy card in Test: `strategies/midna/mn-hourly-playbook.md`, whose Code section names Midna v3 `sleeves/lazarus/s_mn_hourly.py` and notes it calls laz_sleeves._common, which is not in this repo (dependency gap recorded in Files). Running module read in full; master-desk engine in Test: `sleeves/midna/hourly.py`.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

Hourly Tensor lane: buys hourly Tensor consensus-buy fires under the frozen playbook, with a 15% disaster stop or a 60-bar time exit, 12 slots at $1,000 in the v3 module (module header).

## Full algorithm

In evaluation order:

1. v3 module `sleeves/lazarus/s_mn_hourly.py`: SLEEVE_ID s_mn_hourly, INPUTS (bars_1hour, positions, midna_signals); evaluate() delegates to mn_hourly_evaluate(view, ctx, SLEEVE_ID, stop=True, slots=12) from laz_sleeves._common. Header record: Tensor hourly signal (Midna rules); 15% stop or 60-bar time exit; 12 slots x $1,000; source status Live; the signal arrives via the desk Tensor-bundle hourly product (ledger substitution LAZ-B7: the research-archive midna_fires file is unreachable from this box).
2. Playbook engine `sleeves/midna/hourly.py` (the master-desk port the card names; header read in full): fires are the hourly watch's inbox: a gap20, first-of-setup 1H consensus-buy fire of the swing basket (unit 1h-basket, max 60 bars); a fire is decided once (seen) and skipped when its setup episode already traded, when its unit/tags match a killed rule (KILLED), when it is not tradeable or not from Yahoo bars, when a 1H fire is not the first of its gap20 episode, when its entry deadline passed, or when dv20 is unknown or below $1,000,000.
3. Entry (hourly.py header): inside the window [the next bar's open, + 30 min] for 1H, best rank first (meta decile x 1e6 + score, then symbol); 1H entries only in regular hours; a held name is skipped; a full lane (or 20 open) waits inside the window; a fresh quote (<= 15 min old, <= 1 min ahead) whose last is within the lane's limit band over the fire close (1H 3%) else it waits; slot = min($5,000, 1% of dv20) on the $100,000 playbook book with lane cap 1h 5; cash below 90% of the slot skips; qty = floor(min(slot, cash) / paper price). The v3 lane's own config sizing is the sleeves.json block in Configuration ($1,000 a position, 2 slots, $2,000 budget in the wrapper row; the module header says 12 slots x $1,000 - recorded as found, not reconciled).
4. Plan / exit (hourly.py header): 1h-basket plan: the plan's stop (last <= entry x (1 - stop%)) or the time exit (the close of the 60th hourly bar from the entry bar) at the bid, in regular hours on a fresh quote. Accounting exit record: disaster stop 15%, time exit 60 bars, hold_from plan, hold unit 1h.

Accounting / lane-config wrapper (md2 catalog text, identical in the sleeves.json row): entry policy {"policy": "midna_block", "max_delay_minutes": 30, "limit_band_pct": 3.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: disaster stop 15% / time exit 60 bars", "hold_from": "plan", "hold_unit_kind": "1h", "stop_pct": 15.0, "max_bars": 60, "rest": "time", "plan_overrides": []}. The lane config also records the removed desk-wide gate for these Lazarus ports: the entry policy named midna_block is the upstream red-day buy block (QQQ red AND VIX up AND the name red on the session); the master-desk ports drop that gate, the desk halt, the cross-lane held-by-account check and the shared account cash pool (`sleeves/midna/lanes.py` header) - where a section below says the gate was removed, the config row still naming the policy is the historical record, not a live gate.

## Files in this repo

- This package: `docs/LZ_S_MN_HOURLY-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Strategy card: `strategies/midna/mn-hourly-playbook.md`
- Code (already in Test): `sleeves/lazarus/s_mn_hourly.py` (also `integration/s_mn_hourly_adapter.py`), `sleeves/midna/hourly.py` (playbook engine), `sleeves/midna/lanes.py`; lane row in `sleeves/lazarus/vendor/lazarus/sleeves.json`
- Dependency gap (card + module import): `laz_sleeves._common` (mn_hourly_evaluate) is not in this repo; the recreation must supply / locate that module from the desk engine before the v3 module can run. Recorded as a gap, not reconstructed.
- Rule lines: `docs/verify/midna.md` (Hourly Tensor playbook section)
- Nothing was vendored: every code file named here was already in Test.

## Configuration

- v3 module: slots 12 at $1,000 (header), stop=True, inputs bars_1hour / positions / midna_signals. Playbook book (card): $100,000, 20 slots of min($5,000, 1% of dv20), lane caps 1h 5 / 1d 5 / 1w 10.
Lane-config sizing block (sleeves.json row): budget_usd 2000, max_slots 2, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Hourly bars (1h), the Tensor-bundle hourly product / hourly watch inbox, fresh quotes, positions.

## Install and run

1. Clone the Test repo.
2. Take the code files at the exact paths in Files, with the lane row for this id in `sleeves/lazarus/vendor/lazarus/sleeves.json`.
3. Configure the lane with the entry, exit and sizing values in Configuration; confirm the sleeve id in code matches the s_mn_ form of the canonical id.
4. Wire the Data inputs: the sleeve_midna fire file / Tensor-bundle fire channel and the bar / position views the code names.
5. First evaluation: run one evaluation with no qualifying fire / signal and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No dedicated test file for this lane was found in Test; rule lines at `docs/verify/midna.md`. Behaviour checklist:

- A fire that is not first-of-setup / gap20-first, matches a killed rule, is not tradeable, is stale past its deadline, or has dv20 < $1,000,000 produces no entry.
- Entries occur only inside [next bar open, +30 min], in regular hours, within 3% of the fire close on a fresh quote.
- A held position exits when last <= entry x (1 - 15%) or at the close of the 60th hourly bar from the entry bar.
- The v3 module delegates with stop=True and slots=12; without laz_sleeves._common it cannot run (dependency gap in Files).
