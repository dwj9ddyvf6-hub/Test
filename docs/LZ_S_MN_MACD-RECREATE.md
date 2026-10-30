# lz_s_mn_macd: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna MACD (Midna port)", type momentum, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_macd` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- Strategy card in Test: `strategies/midna/mn-macd-cci.md`, whose Notes state the v3 reading plainly: Midna v3's s_mn_macd trades a plain MACD(12, 26, 9) cross with one slot, no CCI filter or chandelier. The card's fuller MACD-CCI form (master desk) is recorded as a distinct reading in the algorithm section, not merged into the v3 lane.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

Momentum lane: buys a daily MACD cross up and exits on the cross down, one position at a time (running v3 module).

## Full algorithm

In evaluation order, from `sleeves/s_mn_macd.py` `signal()` (read in full):

1. MACD: fast EMA(12) and slow EMA(26) on daily closes; line = fast - slow; signal = EMA(9) of the line; histogram = line - signal (`macd_hist`). A name needs at least MIN_BARS 35 bars.
2. Exit first: for each held name, if hist[-2] >= 0 and hist[-1] < 0 (cross down on the last two closed bars), exit the full held quantity at the last close. If any exit is emitted, or anything is held, return with no entries.
3. Entry: scan symbols in sorted order; a cross up is hist[-2] <= 0 and hist[-1] > 0; skip stale-refused names (xstale_refused, ENH20); keep the strongest histogram (ties deterministic by symbol order); enter that one name with qty_for(SLOT_BUDGET $1,000, last close), one slot.
4. Distinct master-desk reading (card `strategies/midna/mn-macd-cci.md`, NOT the v3 lane): MACD cross up gated by CCI(20) > 100, ranked by CCI, up to 4 names, exit on cross down or price under peak since entry - 3 x ATR(14), unit = min(floor(1% of equity / ATR14), floor(cash / price)); its code is `sleeves/midna/board.py` + `sleeves/midna/vendor/midna/board_signals.py`.

Accounting / lane-config wrapper (md2 catalog text, identical in the sleeves.json row): entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: MACD down exit", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time", "plan_overrides": []}. The lane config also records the removed desk-wide gate for these Lazarus ports: the entry policy named midna_block is the upstream red-day buy block (QQQ red AND VIX up AND the name red on the session); the master-desk ports drop that gate, the desk halt, the cross-lane held-by-account check and the shared account cash pool (`sleeves/midna/lanes.py` header) - where a section below says the gate was removed, the config row still naming the policy is the historical record, not a live gate.

## Files in this repo

- This package: `docs/LZ_S_MN_MACD-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Strategy card: `strategies/midna/mn-macd-cci.md`
- Code (already in Test): `sleeves/s_mn_macd.py`; adapters `adapters/s_mn_macd.py`, `integration/s_mn_macd_adapter.py`; lane row in `sleeves/lazarus/vendor/lazarus/sleeves.json`
- Dependency: `sleeves/laz8_common.py` import; present in the tree at `engines/sleeves/laz8_common.py` and `engines/adapters/laz8_common.py`.
- Rule lines: `docs/verify/midna.md` (MACD-CCI section, Midna v3 reading row cites sleeves/s_mn_macd.py)
- Nothing was vendored: every code file named here was already in Test.

## Configuration

- Sleeve id in running code: `s_mn_macd`. SleeveConfig cadence_s=300, state_schema {"position": "dict|None"}. SLOT_BUDGET $1,000, MIN_BARS 35, MACD(12,26,9), 1 slot in the running module.
Lane-config sizing block (sleeves.json row): budget_usd 2000, max_slots 2, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- The lane row's 2 slots / $2,000 is the wrapper config; the running module enforces one position at a time. Recorded as found; not reconciled in the record.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Completed daily bars (closes) for the swing basket; at least 35 bars per name for any signal.

## Install and run

1. Clone the Test repo.
2. Take the code files at the exact paths in Files, with the lane row for this id in `sleeves/lazarus/vendor/lazarus/sleeves.json`.
3. Configure the lane with the entry, exit and sizing values in Configuration; confirm the sleeve id in code matches the s_mn_ form of the canonical id.
4. Wire the Data inputs: the sleeve_midna fire file / Tensor-bundle fire channel and the bar / position views the code names.
5. First evaluation: run one evaluation with no qualifying fire / signal and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No dedicated test file for this sleeve was found in Test; rule lines at `docs/verify/midna.md`. Behaviour checklist:

- A held name exits exactly when the histogram crosses from >= 0 to < 0 on the last two closed bars.
- With any position held, no new entry is emitted.
- Among same-session cross-ups, the strongest histogram wins; symbol order breaks ties; stale names are skipped.
- A name with fewer than 35 bars produces no intent.
