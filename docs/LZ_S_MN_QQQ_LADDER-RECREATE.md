# lz_s_mn_qqq_ladder: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna QQQ Ladder (Midna port)", type other, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_qqq_ladder` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- Lane-config state for this row is 'shadow' with status text: shadow-tracked (no broker orders): QQQ options ladder; the test desk is stocks-only, paper-tracked from option-marks/ladder. Its entry policy is midna_none (the only lane in this batch without the buy block). Running ladder code in Test: `sleeves/midna/ladder.py` (sleeve_id midna_qqq_csp_ladder), read in full.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

Cash-secured QQQ put ladder, shadow-tracked on the stocks-only desk: sells band puts in weekly layers and manages them by buy-back, roll-up and roll-down rules; the lane itself places no broker orders (config state shadow; module header).

## Full algorithm

In evaluation order, from `sleeves/midna/ladder.py` (header summary of the ported source, verified against the module):

1. Book: its own $1,000,000 (LADDER_NAV = 1,000,000.0); LADDER_QTY = 3 contracts a layer; sales at the bid, buy-backs at the ask (per contract x 100). Session: regular hours from 10:00 ET.
2. Severe check first: spot (QQQ last, else the chain's) <= strike, ask >= 3x the sale credit, or live put delta >= 0.35: buy back (needs today's fresh chain and the cash for it).
3. Near expiry: anything with 7 days or fewer left is bought back.
4. Roll up (8..21 DTE, not rolled before, not challenged): QQQ above the sale's spot (quote and chain within 2%) and the put's ask <= half its credit: buy back and sell the band put (delta 0.05..0.08, nearest 0.065, lower strike on a tie) above it in the same expiration whose bid >= that ask, when the cash still secures it.
5. Roll down (8..21 DTE, challenged: ask >= 2x credit, delta >= 0.20, or QQQ <= strike, but not severe): buy back and sell the band put below the strike in the later expiration nearest 45 days (38..52) whose bid >= half the old credit, when the cash still secures it.
6. New layer, once per ISO week: QQQ not down on the day and VIX not up on the day (both quoted with a previous close), no open put challenged, today's fresh chain (<= 20 min) whose spot is within 2% of QQQ's quote; the expiration nearest 45 days (38..52, a tie takes the later) not already held; the band put; the cash after the credit, less the strikes already secured, must secure 3 x strike x 100.
7. Expiry: a put still open on its expiration day settles at intrinsic x 100.
8. Named divergences recorded in the header: the source's 4% annual yield on the ladder's cash (accrue, LADDER_YIELD) is not paid (the engine has no cash-yield capability); orders are engine children (sales DAY limit at the bid, buy-backs DAY limit at the ask) and a working order counts as done. Removed at cutover: entriesHeld(state), the desk halt / ledger-chain kill switch. The Lazarus lane wrapper adds no broker execution: accounting exit record is 'ladder mark-to-market (shadow)', stop_pct 99.0, max_bars 0.

Accounting / lane-config wrapper (md2 catalog text, identical in the sleeves.json row): entry policy {"policy": "midna_none", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: ladder mark-to-market (shadow)", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time", "plan_overrides": []}. The lane config also records the removed desk-wide gate for these Lazarus ports: the entry policy named midna_block is the upstream red-day buy block (QQQ red AND VIX up AND the name red on the session); the master-desk ports drop that gate, the desk halt, the cross-lane held-by-account check and the shared account cash pool (`sleeves/midna/lanes.py` header) - where a section below says the gate was removed, the config row still naming the policy is the historical record, not a live gate.

## Files in this repo

- This package: `docs/LZ_S_MN_QQQ_LADDER-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code (already in Test): `sleeves/midna/ladder.py` (QqqCspLadder sleeve, cadence_s=300, capital LADDER_NAV; also the identical copy at `packages/claude/master-desk-sleeve-port-library/desk/sleeves/midna/ladder.py`); lane row s_mn_qqq_ladder in `sleeves/lazarus/vendor/lazarus/sleeves.json`
- No file named for s_mn_qqq_ladder itself exists in any searched repo: the lane is the config/shadow binding of the ladder module above; that binding is recorded here rather than reconstructed.
- Data producer named in the header: `packages/claude/master-desk-feedlib/desk/feedlib/midna_options.py` (option-marks port, Cboe delayed quotes) in Test under packages/.
- Nothing was vendored: every code file named here was already in Test.

## Configuration

- Running module: sleeve_id midna_qqq_csp_ladder, family midna, cadence_s=300, capital $1,000,000, params qty 3, delta band [0.05, 0.08] (nearest 0.065), DTE window [38, 52] for new layers.
Lane-config sizing block (sleeves.json row): budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- The lane row's $1,000 / 1 slot is the stocks-desk shadow wrapper; the ladder book itself is the $1,000,000 module book above. State: shadow. Research line in the row: Midna qqq-ladder.ts LADDER_NAV=1e6 LADDER_QTY=3.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Listed QQQ option chain (Cboe delayed quotes via the option-marks producer), QQQ and VIX quotes with previous closes.

## Install and run

1. Clone the Test repo.
2. Take the code files at the exact paths in Files, with the lane row for this id in `sleeves/lazarus/vendor/lazarus/sleeves.json`.
3. Configure the lane with the entry, exit and sizing values in Configuration; confirm the sleeve id in code matches the s_mn_ form of the canonical id.
4. Wire the Data inputs: the sleeve_midna fire file / Tensor-bundle fire channel and the bar / position views the code names.
5. First evaluation: run one evaluation with no qualifying fire / signal and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No dedicated test file for this lane was found in Test. Behaviour checklist:

- The lane emits no broker orders (shadow state); the ladder book is paper-tracked and marked to market.
- A put at <= 7 DTE is bought back; a severe put (spot <= strike, ask >= 3x credit, or delta >= 0.35) is bought back before any roll is considered.
- Roll-up and roll-down follow the DTE, delta-band, credit and cash-secured conditions in the Full algorithm exactly.
- At most one new layer per ISO week, only when QQQ is not down, VIX is not up, no open put is challenged, and the fresh chain is within 2% of the quote.
