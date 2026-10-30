# ausar_pb4: Recreation package

## Provenance

- Canonical id: `ausar_pb4`; canonical name: Weekly multi-indicator recovery · weekly; aliases: ausar_pb4.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type forecast and ML models, family tensor, algorithm grade PARTIAL; accounting gaps: sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Weekly multi-indicator recovery · weekly" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; md2 catalog entry/exit/strategy text; alias record sources: md2_ausar_map, md2_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree; research notes only as noted in Provenance, no deployable sleeve code for these ids).
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/aster_tensor_w1_recovery.py + desk3/aster_batch1.py. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

Weekly multi-indicator recovery: the Tensor StateRepairPolicy on the weekly frame. It buys US equities whose 7-vote Tensor balance is repairing on completed weekly bars and holds each position for 20 weekly bars. The accounting entry text for ausar_pb4 and the StateRepairPolicy code in this repo state the same rule (balance up at least 2 over the 4-bar panel, at least 2 of 7 vote channels rising, rank by repair + 0.01 x balance + 0.001 x clipped OBV-slope/volume, 20-bar exit); the code is the truth where they differ in wording. Accounting grade PARTIAL with the single gap 'sizing not recorded'; the code records the sizing, stated below.

## Full algorithm

From `desk3/aster_batch1.py` (SPECS: kind="tensor", frame="1wk", tf="1Week", cadence_s=3600, session="rth"; inputs tensor, bars, positions) and `docs/ASTER_TENSOR_W1_RECOVERY-ALGORITHM.md` in this repo, in evaluation order:

1. Exits first; if any exit intent is emitted, the call returns exits only. The only designed exit is time: a position is sold in full when the current panel bar index minus its entry bar index reaches 20 native (weekly) bars; a late observation still exits (the accounting phrases this as: exit after twenty completed weekly holding bars; an overdue owned exit remains eligible when a new price arrives). Exit price is the latest weekly bar close when available. No price stop and no profit target.
2. Panel: a symbol needs at least a 4-bar panel on the weekly frame, consuming canonical Tensor products via view["tensor"]; no tensor key in the snapshot means the sleeve is UNFED, never fake-fed. Vote channels (7): stoch, aroon, di, obv, squeeze, pivot, wave; a row's balance is bullish votes minus bearish votes (or the row's own balance field). Excluded symbols: SPY, QQQ, B, GOLD.
3. Repair test on the last 4 bars: balance[-1] - balance[0] >= 2; at least 2 of the 7 vote channels strictly increase across at least one adjacent transition in the panel; total_votes == 7 at both panel ends; the latest row's native status, when present, must be "ready".
4. Price/volume gates on the latest panel row: close >= 5, dollar_volume20 >= 1,000,000, atr14 > 0. Warmup: the current bar index + 1 must be >= 234. Cooldown: 20 native bars after an entry (state records next_eligible_bar_index = entry bar index + 20; a view-supplied next_eligible map can override per symbol). The accounting entry text records the same gates and notes the installed cooldown prevents repeated overlapping opportunities.
5. Ranking: repair + 0.01 * balance[-1] + 0.001 * clip(obv_slope5 / volume, -10, 10); ties break by symbol ascending. Entries fill the free slots in rank order; at most 10 positions held.
6. Execution-price revalidation (ENH-B13-TENSORREC-REPRICE-20261024, switch default ON; OFF restores the panel-close rule exactly): when a current bar exists, the $5 floor is revalidated against its latest close (a current close below 5 refuses the entry) and sizing uses that close instead of the panel close.
7. Sizing: budget = min(0.10 * equity, 0.01 * DV20, cash); shares = floor(budget / (execution price * 1.001)); shares < 1 emits nothing. Orders are buy entries at the execution price.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Sleeve wrapper (already in Test): `sleeves/aster_tensor_w1_recovery.py` (also `adapters3/aster_tensor_w1_recovery.py`, `integration/aster_tensor_w1_recovery_adapter.py`); SLEEVE_ID `aster_tensor_w1_recovery`, delegating to `desk3/aster_batch1.evaluate`; its docstring names it the Tensor weekly state-repair recovery sleeve.
- Shared engine (already in Test): `desk3/aster_batch1.py` (SPECS entry kind="tensor", frame="1wk"; StateRepairPolicy).
- Existing algorithm doc for the aster id (already in Test): `docs/ASTER_TENSOR_W1_RECOVERY-ALGORITHM.md`; rule lines: `docs/verify/ausar.md` section "Tensor state repair (hourly / weekly)"; family card: `strategies/ausar/tensor-state-repair.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry "Weekly multi-indicator recovery - weekly".

## Configuration

- Frame 1wk (1Week bars); cadence_s 3600; session rth; inputs tensor, bars, positions. At most 10 positions; excluded SPY, QQQ, B, GOLD.
- Universe and slice capital for the ausar_pb4 accounting entry itself: not in the record (the accounting records universe and timeframe as not recorded for this entry); the values above are the in-repo implementation's own spec.

## Data inputs

Accounting filter note for this entry: completed Yahoo bars, canonical v698 where applicable, actual received execution quotes. Engine producers: bars (900 s freshness), tensor_bundle (86400 s, outputs tensor), broker_readback (900 s, positions), quotes (60 s).

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / data inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (no intent / UNFED), never fake-fed.
5. Call the module's evaluate entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- A symbol whose 4-bar panel balance rises by less than 2, or with fewer than 2 rising vote channels, or with total_votes other than 7 at a panel end: no entry.
- A symbol with latest close < 5, dollar_volume20 < 1,000,000, atr14 <= 0, fewer than 234 bars, or inside its 20-bar post-entry cooldown: no entry.
- Sizing never exceeds floor(min(0.10 x equity, 0.01 x DV20, cash) / (price x 1.001)); holdings never exceed 10.
- A held position exits in full when the panel bar index reaches entry + 20 weekly bars, including on a late observation; no other exit fires.
- With no tensor key in the snapshot the sleeve emits nothing (UNFED, never fake-fed).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
