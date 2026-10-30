# WSTATE - Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "WSTATE", type forecast and ML models, algorithm grade PARTIAL with gaps: ["entry/signal rule not recorded in any consulted source", "exit rule not recorded in any consulted source", "sizing not recorded in any consulted source"], and UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description". The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". Alias status: ausar_deployed, "mode=original_independent_local_paper running=False". Classification evidence on the accounting entry: "Classification 2026-10-30: forecast and ML models (code evidence): desk3/aster_batch1.py aster_tensor_w1_recovery StateRepairPolicy: consumes canonical Tensor products, entry on a 4 bar panel repair vote, exit at entry bar plus 20"
- That classification reading is the linkage for this package: it identifies WSTATE with the StateRepairPolicy port in Test at `desk3/aster_batch1.py`, sleeve `aster_tensor_w1_recovery` (kind tensor, frame 1wk). The module header (read for this package) states the port is from backend/tensor_strategy.py StateRepairPolicy (R11) and gives the full parameter set quoted below. No file named WSTATE itself exists in any searched repo, and the accounting records no algorithm text for WSTATE itself; the algorithm below is the identified code's, and the identification rests on the classification evidence quoted above.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree plus content read of `desk3/aster_batch1.py`; the only WSTATE tree hit is an unrelated Kafka documentation page in Silicon's research mirror, ScreenerOptionFlowState.md, which is not this strategy); dwj9ddyvf6-hub/Silicon (recursive tree; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree; no path named for this id).

## What this strategy is

A weekly Tensor state-repair recovery sleeve: it consumes canonical Tensor products (the Tensor engine itself is untouched), detects a 4-bar panel whose vote balance has repaired upward, buys, and exits 20 native (weekly) bars after entry. The accounting records no strategy description for WSTATE itself: "No strategy description recorded in consulted sources."

## Full algorithm

Evaluation order (from `desk3/aster_batch1.py` `_eval_tensor` for frame 1wk and the module header):

1. Inputs: canonical Tensor panels at the 1-week frame, per symbol; excluded symbols: SPY, QQQ, B, GOLD. A symbol needs at least 4 panel bars; total_votes must equal 7 at both the first and the current bar of the 4-bar window, and a recorded native_status, when present, must be "ready".
2. Filters on the current bar: close >= 5; DV20 >= $1,000,000; ATR14 > 0; and the warming rule: the current bar index + 1 must be at least 234 (minimum source bars).
3. Repair test: balance is the panel's vote balance; repair = balance(current) - balance(first of the 4 bars) must be >= 2; and at least 2 of the 7 vote channels (stoch, aroon, di, obv, squeeze, pivot, wave) must be increasing across some adjacent transition in the 4 bars.
4. Cooldown: after an entry, the symbol is not eligible again until entry bar index + 20 (next_eligible_bar_index, 20 native bars).
5. Ranking: score = repair + 0.01 x balance(current) + 0.001 x clip(OBV_slope5 / volume, -10, 10); candidates sorted by descending score, then symbol ascending.
6. Sizing: shares = floor(min(0.10 x equity, 0.01 x DV20, cash) / (price x 1.001)); at most 10 positions held (free slots = 10 - open positions). Executable-price revalidation (the module's ENH batch 13 treatment, default on): when a current weekly bar exists, its close replaces the panel close for the $5 floor check and sizing, and a current close below $5 refuses the entry.
7. Exit: at entry bar + 20 native bars (a late observation still exits); no other exit rule is in the code for this sleeve.
8. Cadence (code spec): 3600 seconds, regular trading hours, timeframe 1Week. If the snapshot carries no tensor key, the registry marks the sleeve UNFED, never fake-fed (module header).
9. Accounting gaps for WSTATE itself (entry/exit/sizing "not recorded in any consulted source" in the accounting itself) are filled above only from the identified in-repo code named in Provenance; anything beyond it is not in the record.

## Files in this repo

- This package: `docs/WSTATE-RECREATE.md`
- Code (already in Test; nothing vendored): `desk3/aster_batch1.py` (sleeve `aster_tensor_w1_recovery`, `_eval_tensor`, `_tensor_panels`, vote channels in VOTE_NAMES, excluded set TENSOR_EXCLUDED).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id.

## Configuration

- Sleeve spec (code): kind tensor, frame 1wk, tf 1Week, cadence_s 3600, session rth.
- Excluded: SPY, QQQ, B, GOLD. Floors: close >= 5, DV20 >= $1,000,000, ATR14 > 0, minimum source bars 234. Max positions 10. Cooldown 20 native bars. Hold 20 native bars.
- Deployed status for this id (accounting): mode=original_independent_local_paper, running=False.
- Any further configuration for the deployed form: not in the record.

## Data inputs

- Canonical Tensor products at the 1-week frame (panel rows with votes, balance, close, ATR14, DV20, volume, OBV slope 5, bar index), via the snapshot's tensor view.
- Weekly bars for the executable-price revalidation and exit pricing.
- Positions, equity and cash from the desk snapshot.

## Install and run

1. Clone this repository (Test) and check out the main branch.
2. Open `desk3/aster_batch1.py` and locate the `aster_tensor_w1_recovery` spec and `_eval_tensor`.
3. Provide a snapshot carrying the tensor view (1-week panels), weekly bars, positions, equity and cash in the shape that module documents; without a tensor key the sleeve is UNFED and emits nothing.
4. Run on the 3600-second cadence in regular trading hours.
5. Verify against the Verification section before treating any recreation as faithful.

## Verification

- No dedicated test file for this sleeve was found in Test.
- Behaviour checklist: no entry when total_votes is not 7 at either end of the 4-bar panel, when repair < 2, when fewer than 2 vote channels increase, when close < 5, DV20 < $1,000,000 or ATR14 <= 0, for an excluded symbol, inside the 20-bar cooldown, or before 234 source bars; shares equal floor(min(0.10 x equity, 0.01 x DV20, cash) / (price x 1.001)) and holdings never exceed 10; every position exits at entry bar + 20 native bars; with no tensor key in the snapshot the sleeve emits nothing.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.

