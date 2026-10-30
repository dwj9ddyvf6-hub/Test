# lz_s_mn_moonshot: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Moonshot (Midna port)", type other, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_moonshot` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- Strategy card in Test: `strategies/lazarus/lz-moonshot.md` (Moonshot weekly lane), whose Variants table names the Midna book form `s_mn_moonshot` (Midna v3): 1W buy-cyan fires <= 10 days old, 60-week depth >= 70.35, hold 78 weeks (v3: 390 sessions), up to 10 open on the upstream book. Its Source row carries the family codename token, which is omitted here under the repo PII rule. Running module in Test: `sleeves/s_mn_moonshot.py`.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

Lottery / deep-reset lane: enters only on a fresh upstream moonshot pick fire and holds it with no stop for 78 weeks (390 sessions) (module header).

## Full algorithm

In evaluation order, from `sleeves/s_mn_moonshot.py` `signal()` (read in full):

1. Exit first: a held name exits at its full held quantity when sessions_held >= HOLD_SESSIONS 390 (78 weeks x 5), reason hold_complete_78_weeks no_stop. There is no price stop.
2. If anything is held (and no exit fired), return: one position at a time in this module.
3. Entry: `_fresh_fire` scans fires with sleeve_id s_mn_moonshot dated 0 to MAX_FIRE_AGE_DAYS 7 days before the session and takes the newest; absent, stale or malformed fires fail closed (no intent). Skip when the pick has no bars or is stale-refused (xstale_refused, ENH20). Enter qty_for(BUDGET $1,000, last close), reason records the fire date and weight=1pct (the header: the $1,000 slot IS the 1%-weight pick on the test book; catalog rule: entry 'Midna moonshot pick at 1% weight').
4. Upstream pick record (card variants table, Midna book): a weekly buy-cyan fire with close <= $14.94 and 60-week depth >= 70.35, <= 10 days old, not seen before; the pick generation itself is upstream and not in this repo's desk module.

Accounting / lane-config wrapper (md2 catalog text, identical in the sleeves.json row): entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: no stop / time exit 78 weeks", "hold_from": "plan", "hold_unit_kind": "1w", "stop_pct": 99.0, "max_bars": 78, "rest": "time", "plan_overrides": []}. The lane config also records the removed desk-wide gate for these Lazarus ports: the entry policy named midna_block is the upstream red-day buy block (QQQ red AND VIX up AND the name red on the session); the master-desk ports drop that gate, the desk halt, the cross-lane held-by-account check and the shared account cash pool (`sleeves/midna/lanes.py` header) - where a section below says the gate was removed, the config row still naming the policy is the historical record, not a live gate.

## Files in this repo

- This package: `docs/LZ_S_MN_MOONSHOT-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Strategy card: `strategies/lazarus/lz-moonshot.md`
- Code (already in Test): `sleeves/s_mn_moonshot.py`; adapters `adapters/s_mn_moonshot.py`, `integration/s_mn_moonshot_adapter.py`; lane row in `sleeves/lazarus/vendor/lazarus/sleeves.json`
- Dependency: `sleeves/laz8_common.py` import; present in the tree at `engines/sleeves/laz8_common.py` and `engines/adapters/laz8_common.py`.
- Rule lines: `docs/verify/lazarus.md` (per the card)
- Nothing was vendored: every code file named here was already in Test.

## Configuration

- Sleeve id in running code: `s_mn_moonshot`. SleeveConfig cadence_s=300, state_schema {"position": "dict|None"}. BUDGET $1,000, HOLD_SESSIONS 390, MAX_FIRE_AGE_DAYS 7.
Lane-config sizing block (sleeves.json row): budget_usd 2000, max_slots 2, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Upstream pick fires for sleeve_id s_mn_moonshot; daily bars for the picked name.

## Install and run

1. Clone the Test repo.
2. Take the code files at the exact paths in Files, with the lane row for this id in `sleeves/lazarus/vendor/lazarus/sleeves.json`.
3. Configure the lane with the entry, exit and sizing values in Configuration; confirm the sleeve id in code matches the s_mn_ form of the canonical id.
4. Wire the Data inputs: the sleeve_midna fire file / Tensor-bundle fire channel and the bar / position views the code names.
5. First evaluation: run one evaluation with no qualifying fire / signal and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No dedicated test file for this sleeve was found in Test; rule lines at `docs/verify/lazarus.md`. Behaviour checklist:

- No fire, a fire older than 7 days, or a malformed fire produces no intent.
- A held position never exits before 390 sessions held and always exits at 390, with no stop exit at any loss.
- Entry quantity is qty_for($1,000, last close) for the newest fresh pick only, and a stale-refused pick is skipped.
