# lz_s_mn_w_cyan_adx: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna W cyan high ADX (Midna port)", type forecast and ML models, family 1d unless noted. Algorithm grade PARTIAL in the accounting, gap: sizing not recorded in its consulted sources; sources: md2 catalog entry/exit/strategy text. Alias `lz_s_mn_w_cyan_adx` (md2_catalog, status installed); no Test catalog entry in the accounting (test_entries empty).
- The accounting's sizing gap is filled by the Test record itself: the Lazarus lane config row in Test `sleeves/lazarus/vendor/lazarus/sleeves.json` (the lazarus-desk sleeves.json the Lazarus runtime resolves lanes from) carries this lane's entry, exit and sizing blocks, quoted in the Full algorithm and Configuration sections.
- CODE STATUS: INCOMPLETE-CODE. No code binding this lane id was located in any GitHub repo searched. Filename search of the four batch-start trees found: no s_mn_w_cyan_adx module, adapter or desk3 SPECS entry in Test (the batch-9 fire-consumer engine `desk3/lazarus_midna.py` SPECS covers s_mn_w_cyan_breadth, s_mn_w_cyan_vix, s_mn_d_green_band, s_mn_w_green_smh and s_mn_hourly_1w only); the only adx-named strategy code in Test is the distinct femto lane `sleeves/rule_1w_cyan_mom_adx.py` (also in quant-research-backup at femto-lean/sleeves/rule_1w_cyan_mom_adx.py), which no record ties to this lane id and which is therefore NOT presented as this strategy's code; Silicon and Midna trees contain no file named for this id or for adx strategies. What exists in Test is the lane's config row (quoted below) and the upstream forward engine it points to.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b28_Test_tree.txt, b28_Silicon_tree.txt, b28_quant-research-backup_tree.txt, b28_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its s_mn_ form, and its distinguishing tokens across sleeves/, adapters/, adapters3/, integration/, strategies/, packages/, desk3/ and docs/. The files named below were fetched from Test and read.

## What this strategy is

Weekly Cyan forward lane gated on high ADX, held 126 sessions with no stop, as recorded in its lane config row. This package is graded INCOMPLETE-CODE: the config and plan are on record, but no Test code binds the s_mn_w_cyan_adx lane id, so a faithful recreation of the running lane cannot be proven from the repo alone.

## Full algorithm

Everything the record holds, in evaluation order; gaps are marked, not filled:

1. Signal: a sleeve_midna fire for this lane (producer sleeve_midna, fire file shadow/paper_sleeve/live/midna/midna_fires_v1.json). The lane label and its research line record the upstream spec: Midna forward.ts FORWARD_SPECS id=w-cyan-adx, ruleId=V2-1W-CYAN-RAW-H126-f10092bc, FORWARD_NAV=20000, FORWARD_SLOTS=6. The ADX threshold and the Cyan fire definition for this spec are not in the record (not in the accounting, not in the lane row, not in any card in Test).
2. Entry wrapper (lane row / accounting, identical): policy midna_block, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, order capped_limit_day, stock_red false, qqq_red false.
3. Sizing (lane row): $1,000 a position, 2 slots, $2,000 budget, cap 1.0% of dv20, min dv20 $100,000 (full block in Configuration).
4. Exit (lane row / accounting): no stop (stop_pct 99.0), time exit 126 sessions, hold_from fill, hold unit 1d in the row (the label's W is weekly; the row's kind is 1d - recorded as found, not reconciled).
5. Generic forward-engine behaviour in Test (`sleeves/midna/forward_scan.py` + `sleeves/midna/forward.py`, rule lines in `docs/verify/midna.md`): weekly Cyan entries with dollar-volume, breadth or VIX limits; up to 6 hits per account, best score first; entry from 10:00 ET on the session after the signal; sells once the hold (21, 126 or 252 sessions) is reached; sizing qty = floor((20,000 / 6) / (price x (1 + cost))), capped by cash. Whether the ADX spec follows this exact form is not in the record for this lane id.

## Files in this repo

- This package: `docs/LZ_S_MN_W_CYAN_ADX-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Config (already in Test): lane row s_mn_w_cyan_adx in `sleeves/lazarus/vendor/lazarus/sleeves.json`
- Upstream engine named by the row's research line (already in Test, but not bound to this lane id by any record): `sleeves/midna/forward.py`, `sleeves/midna/forward_scan.py`
- NOT this strategy's code (distinct lane, recorded to prevent confusion): `sleeves/rule_1w_cyan_mom_adx.py`
- No dedicated module, adapter, desk3 SPECS entry, strategy card or test for s_mn_w_cyan_adx was found in Test, Silicon, quant-research-backup or Midna.
- Nothing was vendored: every code file named here was already in Test.

## Configuration

- Lane row: kind 1d, enabled true, state live, account TEST. Entry / exit / sizing blocks as quoted in the Full algorithm.
Lane-config sizing block (sleeves.json row): budget_usd 2000, max_slots 2, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Account TEST (broker account id in the row is an internal test account label, omitted here); enabled true; state live unless noted; status text: ready (Midna port; start FLAT; Midna positions are reference only). Source producer: sleeve_midna (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Upstream spec values from the research line: FORWARD_NAV 20000, FORWARD_SLOTS 6.
- ADX lookback and threshold: not in the record. Cadence and state beyond the above: not in the record.

## Data inputs

- Accounting filter record: data sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Midna's daily panel, the Tensor engine and the frozen v4 GBM (verify rule lines for the forward engine generally). Lane-specific inputs beyond the fire file: not in the record.

## Install and run

1. Clone the Test repo.
2. Take the lane row for s_mn_w_cyan_adx in `sleeves/lazarus/vendor/lazarus/sleeves.json` and the forward engine files in Files.
3. STOP: no code in the repo binds this lane id or records its ADX gate. A recreation beyond the config and plan quoted here would require the upstream forward.ts FORWARD_SPECS entry for id=w-cyan-adx (ruleId V2-1W-CYAN-RAW-H126-f10092bc), which is not in any searched repo. Do not substitute `sleeves/rule_1w_cyan_mom_adx.py`: no record ties it to this lane.
4. If that spec is obtained, wire the sleeve_midna fire channel and re-grade this package before treating any recreation as faithful.

## Verification

No test for this lane exists in Test. Behaviour checklist from the recorded plan only (necessary, not sufficient, for faithfulness):

- Entries follow the recorded wrapper: capped_limit_day, max delay 65 minutes, limit band 5.0%, buffer 1.0%.
- Sizing is $1,000 a position, at most 2 slots, dv20 floor $100,000, cap 1.0% of dv20.
- No stop exit occurs; the only recorded exit is the 126-session time exit.
- The ADX gate itself cannot be verified from the repo record: it is not in the record.
