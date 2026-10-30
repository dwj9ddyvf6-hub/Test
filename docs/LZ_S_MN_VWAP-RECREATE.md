# lz_s_mn_vwap: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna VWAP (Midna port)", type trend following, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_vwap` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- Strategy card in Test: `strategies/midna/mn-ema4-vwap.md`, whose Notes state the v3 reading plainly: Midna v3's s_mn_vwap trades the price crossing a 20-session VWAP, one slot. The card's fuller EMA4 form (master desk) is recorded as a distinct reading in the algorithm section. Running module in Test: `sleeves/s_mn_vwap.py`, read in full.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

Trend lane: buys when price crosses above the 20-session rolling VWAP and exits when price crosses back below it, one position at a time (running v3 module).

## Full algorithm

In evaluation order, from `sleeves/s_mn_vwap.py` `signal()` (read in full):

1. Rolling VWAP `rolling_vwap`: over the trailing WINDOW 20 sessions ending at bar i, sum(typical price x volume) / sum(volume), typical price = (high + low + close) / 3 on daily bars; returns None when fewer than 20 bars or any bar in the window has volume <= 0.
2. Cross `_cross` on the last two closed bars: up when close[-2] <= VWAP[-2] and close[-1] > VWAP[-1]; down when close[-2] >= VWAP[-2] and close[-1] < VWAP[-1]; needs at least 21 bars.
3. Exit first: a held name with a down cross exits the full held quantity at the last close, reason price_cross_below_vwap20. If any exit fired or anything is held, return with no entries.
4. Entry: scan symbols in sorted order; the first name with an up cross that is not stale-refused (xstale_refused, ENH20) enters with qty_for(SLOT_BUDGET $1,000, last close), one slot, reason price_cross_above_vwap20.
5. Distinct master-desk reading (card, NOT the v3 lane): EMA(4) crosses above the 20-session VWAP while that VWAP is above its value 5 sessions earlier, alphabetical, up to 4 names, exit on the cross back or a 3 x ATR(14) chandelier under the peak, unit = min(floor(1% of equity / ATR14), floor(cash / price)); code `sleeves/midna/board.py` + `sleeves/midna/vendor/midna/board_signals.py`.

Accounting / lane-config wrapper (md2 catalog text, identical in the sleeves.json row): entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: VWAP down exit", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time", "plan_overrides": []}. The lane config also records the removed desk-wide gate for these Lazarus ports: the entry policy named midna_block is the upstream red-day buy block (QQQ red AND VIX up AND the name red on the session); the master-desk ports drop that gate, the desk halt, the cross-lane held-by-account check and the shared account cash pool (`sleeves/midna/lanes.py` header) - where a section below says the gate was removed, the config row still naming the policy is the historical record, not a live gate.

## Files in this repo

- This package: `docs/LZ_S_MN_VWAP-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Strategy card: `strategies/midna/mn-ema4-vwap.md`
- Code (already in Test): `sleeves/s_mn_vwap.py`; adapters `adapters/s_mn_vwap.py`, `integration/s_mn_vwap_adapter.py`; lane row in `sleeves/lazarus/vendor/lazarus/sleeves.json`
- Dependency: `sleeves/laz8_common.py` import; present in the tree at `engines/sleeves/laz8_common.py` and `engines/adapters/laz8_common.py`.
- Rule lines: `docs/verify/midna.md` (Midna v3 reading row cites sleeves/s_mn_vwap.py)
- Nothing was vendored: every code file named here was already in Test.

## Configuration

- Sleeve id in running code: `s_mn_vwap`. SleeveConfig cadence_s=300, state_schema {"position": "dict|None"}. SLOT_BUDGET $1,000, WINDOW 20, 1 slot in the running module.
Lane-config sizing block (sleeves.json row): budget_usd 2000, max_slots 2, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Completed daily bars with high, low, close and volume for the swing basket; at least 21 bars per name for a cross.

## Install and run

1. Clone the Test repo.
2. Take the code files at the exact paths in Files, with the lane row for this id in `sleeves/lazarus/vendor/lazarus/sleeves.json`.
3. Configure the lane with the entry, exit and sizing values in Configuration; confirm the sleeve id in code matches the s_mn_ form of the canonical id.
4. Wire the Data inputs: the sleeve_midna fire file / Tensor-bundle fire channel and the bar / position views the code names.
5. First evaluation: run one evaluation with no qualifying fire / signal and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No dedicated test file for this sleeve was found in Test; rule lines at `docs/verify/midna.md`. Behaviour checklist:

- VWAP is the 20-session rolling typical-price VWAP; a window containing a zero-volume bar yields no VWAP and no cross.
- A held name exits exactly on the down cross of the last two closed bars; while anything is held, no entry is emitted.
- The first sorted-order up-cross name that is not stale-refused enters at $1,000 via qty_for.
