# daily_cyan_gbm: Recreation package

Provenance: Source row in strategies/femto/femto-daily-cyan-gbm.md in this repo: The old Alpaca swing desk's Daily Cyan GBM and GBM-rule research on its Tensor engine replica, via Femto-lean (family Femto-lean, asset US equities, timeframe 1d, universe 1,838-name genome, style Tensor signal + frozen rule).

## What this sleeve is
This sleeve buys fresh daily Tensor Cyan fires that a frozen gradient-boosted model scores in its top tier, best score first, and holds 21 sessions. The GBM score itself is produced outside the sleeve (an external scorer over the genome) and arrives as a core Data product; the sleeve module holds the selection, filter and exit law. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/daily_cyan_gbm.py signal(bars, slice_state, context).

## Full algorithm
Constants (sleeves/daily_cyan_gbm.py): HOLD_BARS = 21, SCORE_CUT = 0.00208 (the pre-change absolute cut, the experiment control; the 2026-10-05 recalibration value, the 90th percentile of scores), MIN_PX = 5.0, MIN_DV20 = 1000000, MAX_POSITIONS = 10, NOTIONAL_FRACTION = 0.01, DISASTER_STOP = 0.25, cost model 10 bps per side in the old framework (the module header corrects the earlier misread of that constructor argument as a risk fraction). CONFIG: cadence_s 300, universe (), risk_pct None.

Entries, in code order:
1. Candidates: context.extra rows from the nightly DCG scoring file: daily cyan fires on each genome name's last bar, each carrying the frozen GBM score. Non-finite or non-numeric scores are skipped (the old BC14A-12 guard ported in the module).
2. Cut: with the enhancement on (ENH-DCG-20261024, switch in extra, default ON) the cut is the session's own 90th percentile of scores (percentile90 in the module); with it off the control cut is the absolute SCORE_CUT = 0.00208. Candidates at or above the cut pass.
3. Filters: the signal-day close must be at least MIN_PX = $5 and dv20 (mean 20-day dollar volume, computed by the module's dv20 helper from daily bars) must be at least MIN_DV20 = $1,000,000 on the signal day.
4. Ranking and capacity: best score first; capacity is checked before append against MAX_POSITIONS = 10 counting the existing book.
5. Timing and sizing: buys go market-on-close the next session through the fill law per the card; the executed sizing law in the module is NOTIONAL_FRACTION = 0.01 (see the module header's A2-06 note: the old framework sized centrally, and the port records the executed fraction explicitly). Whole shares under the fill law, at least 1 when afforded.

Exits, in code order: sells are staged at sessions_since >= HOLD_BARS - 1 = 20 sessions after entry, so the next-session fill lands on the 21st session's close (the old 2026-10-07 staging law); the card's backstop is hold x 1.45 + 3 days. The 25 percent disaster stop (DISASTER_STOP = 0.25) is carried from the old sleeve law.

Position management: at most 10 positions, no pyramiding in this module beyond the selection above.

## Files in this repo
- Sleeve module (desk sleeves/daily_cyan_gbm.py): `sleeves/daily_cyan_gbm.py`.
- v3 adapter (desk adapters3/daily_cyan_gbm.py): `adapters3/daily_cyan_gbm.py`; also present as `integration/daily_cyan_gbm_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py; named in the audit record as a shared dependency).
- No separate engine file in the desk tree: the selection law is in `sleeves/daily_cyan_gbm.py` itself; the GBM score is an external Data product, not code in this repo (audit engine_files_needed is empty for this sleeve).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/femto/femto-daily-cyan-gbm.md`.

## Configuration
- Universe: the 1,838-name genome (served as scoring-file rows; CONFIG universe is ()). Asset: US equities. Timeframe: 1d.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the module's executed sizing fraction is NOTIONAL_FRACTION = 0.01 with the fill law described above.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions.

## Data inputs
- DCG scoring file rows: context.extra candidate rows with the frozen GBM score per genome name (producer: the nightly DCG scoring file, the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar).
- bars: split-adjusted daily bars (200 per the card) for dv20, price filters and session counting; desk quotes for the fill law.
- sleeve_state positions with entry date and quantity arrive through the snapshot context.

## Install and run
1. Place the sleeve module at sleeves/daily_cyan_gbm.py and the adapter at adapters3/daily_cyan_gbm.py (repo copies at the same paths). The module needs the desk BaseSleeve / SleeveConfig / Intent plumbing it imports in the fresh desk; the external GBM scorer itself is a Data producer, not a sleeve file.
2. Register the roster row for `daily_cyan_gbm` exactly as in the Configuration section in config/sleeves.json (module adapters3.daily_cyan_gbm).
3. Wire the producers so every snapshot carries: daily bars per genome name, this sleeve's positions, and the nightly DCG scoring rows in extra, ranked after the close for next-session fills.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch1_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check the cut: with the enhancement off, a score of 0.00207 produces no entry and 0.00208 does (subject to the other filters); with it on, the cut is the session's own 90th percentile of the served scores.
- Check the filters: a close under $5, dv20 under $1,000,000, or a non-finite score each exclude the candidate, and ranking is best score first.
- Check capacity and timing: the 11th position is refused, and buys are staged for the next session's market-on-close fill, not the signal session.
- Check the exit staging: a position entered 20 sessions ago is staged for sale so the fill lands on the 21st session's close.
