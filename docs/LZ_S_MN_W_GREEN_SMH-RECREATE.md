# lz_s_mn_w_green_smh: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna W green calm SMH (Midna port)", type trend following, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_w_green_smh` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- Running engine in Test: `desk3/lazarus_midna.py` (Lazarus Midna fire-consumer engine, batch 9), whose SPECS dict carries this lane verbatim: family green, tf 1W, hold_sessions 126, stop None, gate smh_calm, budget 1000.0. Adapter in Test: `adapters3/s_mn_w_green_smh.py` (also `sleeves/s_mn_w_green_smh.py`, `integration/s_mn_w_green_smh_adapter.py`). Existing Test docs for the s_mn_ form: `docs/S_MN_W_GREEN_SMH-ALGORITHM.md`, `docs/S_MN_W_GREEN_SMH-RECREATE.md`.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

Weekly Green Tensor fire lane gated on a calm SMH: buys a green-family weekly fire when SMH's 20-session move is within 5%, holds 126 sessions, no stop (engine SPECS + gate code).

## Full algorithm

In evaluation order, from `desk3/lazarus_midna.py` `evaluate()` for sleeve_id s_mn_w_green_smh (read in full):

1. Exits first, for each open position: if the spec stop applies (this lane's stop is None, so no stop exit) or age >= hold_sessions 126, exit the full quantity at the last close (reason time label 126_sessions, age counted from the position's sessions_held fields or entry date against the bars). If any exit is emitted, return.
2. One slot: if any position is open, return [].
3. Fires: read from view midna_fires / fires / extra, or the Tensor bundle (view tensor / tensor_bundle, including its sleeves dict). No fires: return [] (fail closed).
4. Fire filters: the fire's sleeve_id, when present, must equal s_mn_w_green_smh; its family/kind/signal text must contain 'green'; its timeframe, when present, must match the spec tf 1W (1W / W / WEEK / WEEKLY accepted); its date, when present, must be 0 to 10 days before the session.
5. Cross-stale gate (ENH20, on by default): refuse when the symbol's last bar lags the universe's latest bar by more than 4 days (journaled).
6. Price (ENH19, on by default): gate and size off the fresh last close when bars exist, else the fire price; a price <= 0 skips the fire.
7. Gate smh_calm: an explicit extra smh_calm flag, when present, must be truthy; otherwise compute from SMH bars: with at least 21 bars, r = SMH close[-1] / close[-21] - 1 and the fire is refused when |r| > 0.05; with fewer than 21 bars and no explicit flag, the fire is refused.
8. Size: qty = int(budget $1,000 // price); qty < 1 skips. Emit one market entry intent (DAY, buy_to_open, price hint the chosen price) and stop (first qualifying fire only).

Accounting / lane-config wrapper (md2 catalog text, identical in the sleeves.json row): entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: no stop / time exit 126 sessions", "hold_from": "fill", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 126, "rest": "time", "plan_overrides": []}. The lane config also records the removed desk-wide gate for these Lazarus ports: the entry policy named midna_block is the upstream red-day buy block (QQQ red AND VIX up AND the name red on the session); the master-desk ports drop that gate, the desk halt, the cross-lane held-by-account check and the shared account cash pool (`sleeves/midna/lanes.py` header) - where a section below says the gate was removed, the config row still naming the policy is the historical record, not a live gate.
- Note the wrapper order record (capped_limit_day) vs the engine's emitted intent (market, DAY): recorded as found in each source.

## Files in this repo

- This package: `docs/LZ_S_MN_W_GREEN_SMH-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code (already in Test): `desk3/lazarus_midna.py` (SPECS + evaluate), adapter `adapters3/s_mn_w_green_smh.py` (also `sleeves/s_mn_w_green_smh.py`, `integration/s_mn_w_green_smh_adapter.py`); lane row in `sleeves/lazarus/vendor/lazarus/sleeves.json`
- Existing s_mn_ docs: `docs/S_MN_W_GREEN_SMH-ALGORITHM.md`, `docs/S_MN_W_GREEN_SMH-RECREATE.md`
- Producers declared by the engine: tensor_bundle (freshness SLA 86400s), bars (900s), broker_readback positions (900s); engine INPUTS (tensor, bars, positions)
- Nothing was vendored: every code file named here was already in Test.

## Configuration

- Engine spec: family green, tf 1W, hold_sessions 126, stop None, gate smh_calm, budget $1,000. Max 1 position (engine returns after exits while any position is open).
Lane-config sizing block (sleeves.json row): budget_usd 2000, max_slots 2, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- The lane row's $2,000 / 2 slots is the wrapper config; the running engine's budget is $1,000 with one open position. Recorded as found. Research line in the row: Midna forward.ts FORWARD_SPECS id=w-green-smh ruleId=V4-1W-GREEN-TAIL-H126-ALL-fb459d4f FORWARD_NAV=20000 FORWARD_SLOTS=6.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Tensor-bundle / midna fires, daily and weekly bars for candidate symbols and for SMH, and the broker position readback (engine INPUTS).

## Install and run

1. Clone the Test repo.
2. Take the code files at the exact paths in Files, with the lane row for this id in `sleeves/lazarus/vendor/lazarus/sleeves.json`.
3. Configure the lane with the entry, exit and sizing values in Configuration; confirm the sleeve id in code matches the s_mn_ form of the canonical id.
4. Wire the Data inputs: the sleeve_midna fire file / Tensor-bundle fire channel and the bar / position views the code names.
5. First evaluation: run one evaluation with no qualifying fire / signal and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No dedicated test file for this lane was found in Test. Behaviour checklist from the engine code:

- With no fires, or a fire whose family is not green or timeframe is not weekly, no intent is emitted.
- A fire is refused when SMH's 20-session return exceeds 5% in either direction (or SMH bars are under 21 with no explicit calm flag).
- A held position exits at 126 sessions held and never on a price stop.
- Entry quantity is int($1,000 // fresh close); only the first qualifying fire enters, and only while flat.
