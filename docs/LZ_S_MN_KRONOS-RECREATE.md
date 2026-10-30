# lz_s_mn_kronos: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Kronos (Midna port)", type forecast and ML models, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_kronos` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- Strategy card in Test: `strategies/midna/mn-kronos-topk.md` (Kronos-base TopkDropout), whose Code section names Midna v3 `sleeves/s_mn_kronos.py`. Lane-config status text: shadow-tracked (no broker orders) in the row's status text, turned ON at cutover per its flags; the running module header records the desk-side fire-consumer design.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

ML-forecast rotation: holds the top 4 names ranked by the Kronos time-series model's forecast, rebalancing when the forecast changes with a 5-session minimum hold. The model runs upstream; the desk lane consumes its forecast fires (module header).

## Full algorithm

In evaluation order, from `sleeves/s_mn_kronos.py` `signal()` (read in full):

1. Forecast extraction `_forecast`: take fires with sleeve_id s_mn_kronos, keep those dated 0 to MAX_FIRE_AGE_DAYS 7 days before the session, take the latest date only, sort by rank when every row carries a rank, else by descending score, and take TOP_N 4 symbols. No fresh forecast rows: return no intents at all (fail closed: hold existing, no churn).
2. Exit first: a held name not in the latest top 4 exits only when sessions_held >= MIN_HOLD 5, at its full held quantity, price hint the last close, reason forecast_changed min_hold_met.
3. Entries: free slots = 4 - (held - exiting); for each top-4 symbol not held, in forecast order, skip when no bars or when xstale_refused (ENH20 cross-stale gate), size qty_for(PER_NAME $500, last close); the module header records the budget reading: hold the forecast top 4 at $500 each on a $2,000 catalog budget (the catalog's '2 slots' cell conflicts with 'top 4 names'; the named rule wins, per the header).
4. Upstream forecast (card, for the producer side): every 10 sessions the Kronos-base model reads each of 24 frozen names' last 90 sessions and samples 10 paths 10 sessions ahead (temperature 0.6, top-p 0.9, fixed seeds); score = forecast close in 10 sessions / last close - 1; a name needs 252 complete prior sessions, 20-session average dollar volume >= $10M and close >= $5. The card's TopkDropout book rule (drop the worst held name held >= 5 sessions and out of today's top 5, fill back to 4) describes the upstream books; the desk module implements the fire-consumer form above.

Accounting / lane-config wrapper (md2 catalog text, identical in the sleeves.json row): entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: Kronos topK rebalance / min hold 5", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 5, "rest": "time", "plan_overrides": []}. The lane config also records the removed desk-wide gate for these Lazarus ports: the entry policy named midna_block is the upstream red-day buy block (QQQ red AND VIX up AND the name red on the session); the master-desk ports drop that gate, the desk halt, the cross-lane held-by-account check and the shared account cash pool (`sleeves/midna/lanes.py` header) - where a section below says the gate was removed, the config row still naming the policy is the historical record, not a live gate.
- stop_pct 99.0 in the plan record is effectively no price stop; the running code has no price stop, only the forecast-change exit after the minimum hold.

## Files in this repo

- This package: `docs/LZ_S_MN_KRONOS-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Strategy card: `strategies/midna/mn-kronos-topk.md`
- Code (already in Test): `sleeves/s_mn_kronos.py`; adapters `adapters/s_mn_kronos.py`, `integration/s_mn_kronos_adapter.py`; lane row in `sleeves/lazarus/vendor/lazarus/sleeves.json`
- Dependency named by the code's imports: `sleeves/laz8_common.py` per the import line; in the Test tree that module is present at `engines/sleeves/laz8_common.py` and `engines/adapters/laz8_common.py` (the recreation must place it importable as sleeves.laz8_common).
- Rule lines: `docs/verify/midna.md`
- Nothing was vendored: every code file named here was already in Test.

## Configuration

- Sleeve id in running code: `s_mn_kronos` (canonical accounting id `lz_s_mn_kronos`). SleeveConfig cadence_s=300, state_schema {"position": "dict|None"}.
- TOP_N 4, PER_NAME $500, MIN_HOLD 5, MAX_FIRE_AGE_DAYS 7.
Lane-config sizing block (sleeves.json row): budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Note the three sizing records: lane row budget $1,000 / 1 slot (the accounting wrapper), module header $2,000 holding top 4 at $500 each (the running desk code), card Midna book slice = 95% of equity / 4 on a $100,000 book. They are not reconciled in the record; the running module's $500 per name governs the desk lane's intents.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Forecast fires carrying symbol + rank/score for sleeve_id s_mn_kronos; daily bars for held and candidate names.

## Install and run

1. Clone the Test repo.
2. Take the code files at the exact paths in Files, with the lane row for this id in `sleeves/lazarus/vendor/lazarus/sleeves.json`.
3. Configure the lane with the entry, exit and sizing values in Configuration; confirm the sleeve id in code matches the s_mn_ form of the canonical id.
4. Wire the Data inputs: the sleeve_midna fire file / Tensor-bundle fire channel and the bar / position views the code names.
5. First evaluation: run one evaluation with no qualifying fire / signal and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No dedicated test file for this sleeve was found in Test; rule lines at `docs/verify/midna.md`. Behaviour checklist:

- With no fire dated within 7 days, zero intents are emitted (no entries, no exits).
- A held name outside the latest top 4 exits only at >= 5 sessions held; before that it is held.
- Entries fill only top-4 names, $500 each via qty_for, at most 4 names held, and a stale-refused name is skipped.
- Ranking uses rank when all latest-date rows carry one, else descending score.
