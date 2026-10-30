# lz_s_mn_hedge: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna QQQ->TZA hedge (Midna port)", type market timing and rotation, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_hedge` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- Strategy card in Test: `strategies/midna/mn-qqq-flip5-tza.md`, whose Code section names Midna v3 `sleeves/lazarus/s_mn_hedge.py` and notes it reads a hedge_signal input with no producer in this repo, at $300 of a $1,000 budget. Running module read in full.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

Hedge lane: when the QQQ hedge signal is on, hold TZA (3x inverse small caps) at 30% of the sleeve's $1,000 budget; exit when the signal turns off or after 20 sessions (module header).

## Full algorithm

In evaluation order, from `sleeves/lazarus/s_mn_hedge.py` `evaluate()` (read in full):

1. Session: if the view has no session, return []. Inputs: bars_1day, positions, hedge_signal; the signal is 'on' only when view['hedge_signal'] is exactly True. Upstream meaning (card): flip5 - QQQ's slow Tensor state turned bearish on one of the last five closed daily bars; with nothing held, flip5 stages a buy for the next session's open.
2. Exits first, for each held TZA position (needs TZA bars): if the signal is not on, exit the full quantity at the last TZA close, reason mn_hedge_signal_off; else if sessions held >= MAX_SESSIONS 20, exit, reason mn_hedge_max20.
3. Entry: only when nothing is held, the signal is on, and TZA bars exist. ENH19 stale-bar gate (on by default): if the last TZA bar is stale for the session, journal the refusal (exp ENH19-LAZB7-20261024) and do not enter; exits are untouched by the gate.
4. Size: qty = _qty_for(BUDGET_USD $1,000 x WEIGHT 0.30, last TZA close) = $300 of exposure; if qty <= 0, no intent. Entry intent reason mn_hedge_signal_on.

Accounting / lane-config wrapper (md2 catalog text, identical in the sleeves.json row): entry policy {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: hedge exit on flip off / max 20 sessions", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 20, "rest": "time", "plan_overrides": []}. The lane config also records the removed desk-wide gate for these Lazarus ports: the entry policy named midna_block is the upstream red-day buy block (QQQ red AND VIX up AND the name red on the session); the master-desk ports drop that gate, the desk halt, the cross-lane held-by-account check and the shared account cash pool (`sleeves/midna/lanes.py` header) - where a section below says the gate was removed, the config row still naming the policy is the historical record, not a live gate.

## Files in this repo

- This package: `docs/LZ_S_MN_HEDGE-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Strategy card: `strategies/midna/mn-qqq-flip5-tza.md`
- Code (already in Test): `sleeves/lazarus/s_mn_hedge.py` (also `laz_sleeves/s_mn_hedge.py`, `integration/s_mn_hedge_adapter.py`); lane row in `sleeves/lazarus/vendor/lazarus/sleeves.json`
- Dependency named by the code's imports: `laz_sleeves._common` (the module imports _bar_stale, _bars, _enh19_on, _intent, _journal19, _positions, _qty_for, _session, _sessions_held from it); no laz_sleeves/_common.py file was found in the Test tree listing taken at batch start - recorded as a dependency gap, not reconstructed.
- Master-desk form (card): `sleeves/midna/shadow.py`. Rule lines: `docs/verify/midna.md`
- Nothing was vendored: every code file named here was already in Test.

## Configuration

- Sleeve id in running code: `s_mn_hedge`. BUDGET_USD $1,000, WEIGHT 0.30, MAX_SESSIONS 20, 1 slot. Inputs (bars_1day, positions, hedge_signal).
Lane-config sizing block (sleeves.json row): budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Card sizing for the upstream book: notional = 30% x $100,000 at the open; the v3 lane runs $300 of its $1,000 budget (card Code note). Research line in the row: Midna shadow.ts stepHedge HEDGE_WEIGHT=0.3 HEDGE_MAX_SESSIONS=20.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- A boolean hedge_signal input (no producer in this repo, per the card); TZA daily bars; QQQ daily bars upstream for flip5 (card Data: QQQ and TZA daily bars from the hourly watch).

## Install and run

1. Clone the Test repo.
2. Take the code files at the exact paths in Files, with the lane row for this id in `sleeves/lazarus/vendor/lazarus/sleeves.json`.
3. Configure the lane with the entry, exit and sizing values in Configuration; confirm the sleeve id in code matches the s_mn_ form of the canonical id.
4. Wire the Data inputs: the sleeve_midna fire file / Tensor-bundle fire channel and the bar / position views the code names.
5. First evaluation: run one evaluation with no qualifying fire / signal and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No dedicated test file for this sleeve was found in Test; rule lines at `docs/verify/midna.md`. Behaviour checklist:

- With hedge_signal not exactly True and a position held, the full position exits with reason mn_hedge_signal_off.
- A position held >= 20 sessions exits even while the signal stays on.
- Entry occurs only flat, signal on, fresh TZA bars, sized at $300 / last close whole shares; a stale last bar blocks the entry and is journaled.
