# ausar_pb3: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json, also docs/ALL-SLEEVES.md): canonical name "Hourly multi-indicator recovery · hourly", type forecast and ML models, family tensor. Algorithm grade PARTIAL, unresolved false. Accounting sources: ausar_map params/variant, md2 catalog entry/exit/strategy text. Recorded accounting gaps: sizing not recorded in any consulted source.
- Accounting home record: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Hourly multi-indicator recovery · hourly" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; md2 catalog entry/exit/strategy text; alias record sources: md2_ausar_map, md2_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads named in this package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries).
- Code home: dwj9ddyvf6-hub/Test (code already in Test): desk3/aster_batch1.py (StateRepairPolicy, 1h frame) + sleeves/aster_tensor_h1_recovery.py + adapters3/aster_tensor_h1_recovery.py + integration/aster_tensor_h1_recovery_adapter.py; algorithm doc docs/ASTER_TENSOR_H1_RECOVERY-ALGORITHM.md.

## What this strategy is

Hourly multi-indicator recovery · hourly Type: forecast and ML models; family: tensor. Universe: not recorded in consulted sources. Asset class: not recorded. Timeframe: not recorded. Creator / source: not recorded. Style evidence in the accounting: Classification 2026-10-30: forecast and ML models (config evidence): Accounting entry for ausar_pb3: a four bar Tensor panel must show balance improving by at least two with at least two of seven component votes increasing, ranked by repair, a Tensor model repair signal

## Full algorithm

Accounting record for ausar_pb3, in full as held: Entry: a four-completed-bar panel must show Tensor balance improving by at least two, with at least two of seven component votes increasing; requires seven votes, ready inputs, price >= $5, twenty-bar dollar volume >= $1 million and positive ATR; rank by repair + 0.01 x current balance + 0.001 x clipped OBV-slope/volume; the installed cooldown prevents repeated overlapping opportunities. Exit: after twenty completed hourly holding bars; an overdue owned exit remains eligible when a new price arrives. Sizing: not in the record (the accounting's recorded gap). Data: completed Yahoo bars, canonical v698 where applicable, actual received execution quotes.

Identification: that text matches exactly the Tensor StateRepairPolicy on the 1h frame implemented in Test as aster_tensor_h1_recovery (algorithm doc docs/ASTER_TENSOR_H1_RECOVERY-ALGORITHM.md, derived from desk3/aster_batch1.py; source backend/tensor_strategy.py, R11). Its code rules, in evaluation order:

- Spec: kind tensor, frame 1h, tf 1Hour, cadence_s=3600, session rth; inputs (tensor, bars, positions) via view tensor (no tensor key means UNFED, never fake-fed). Vote channels (7): stoch, aroon, di, obv, squeeze, pivot, wave; a panel row's balance is bullish votes minus bearish votes (or the row's own balance field); excluded symbols SPY, QQQ, B, GOLD; at most 10 positions held.
- Exits first; if any exit intent is emitted the call returns exits only.
- A symbol needs at least a 4-bar panel. Repair test on the last 4 bars: balance[-1] - balance[0] >= 2; at least 2 of the 7 vote channels strictly increase across at least one adjacent transition in the panel; total_votes == 7 at both panel ends; the latest row's native status, when present, must be ready.
- Price/volume gates on the latest panel row: close >= 5, dollar_volume20 >= 1,000,000, atr14 > 0. Warmup: current bar index + 1 >= 234. Cooldown: 20 native bars after an entry (next_eligible_bar_index = entry bar index + 20; a view-supplied next_eligible map can override per symbol).
- Ranking: repair + 0.01 * balance[-1] + 0.001 * clip(obv_slope5 / volume, -10, 10); ties by symbol ascending; entries fill the free slots (10 minus held) in rank order.
- Execution-price revalidation (ENH switch default ON; OFF restores the panel-close rule exactly): when a current bar exists, the $5 floor is revalidated against its latest close and sizing uses that close instead of the panel close.
- Sizing (from the code, filling the accounting gap): budget = min(0.10 * equity, 0.01 * DV20, cash); shares = floor(budget / (execution price * 1.001)); shares < 1 emits nothing. Orders are buy entries at the execution price.
- Exit: the only designed exit is time: a position is sold in full when the current panel bar index minus its entry bar index reaches 20 native bars (late observation still exits), at the latest bar close on the sleeve's timeframe.

## Files in this repo

- This package: docs/AUSAR_PB3-RECREATE.md
- Accounting: docs/ALL-SLEEVES.json, docs/ALL-SLEEVES.md
- Code home (see Provenance): dwj9ddyvf6-hub/Test (code already in Test): desk3/aster_batch1.py (StateRepairPolicy, 1h frame) + sleeves/aster_tensor_h1_recovery.py + adapters3/aster_tensor_h1_recovery.py + integration/aster_tensor_h1_recovery_adapter.py; algorithm doc docs/ASTER_TENSOR_H1_RECOVERY-ALGORITHM.md

## Configuration

Frame 1h (1Hour bars); cadence 3600 s; session rth; at most 10 positions; excluded SPY, QQQ, B, GOLD; warmup 234 bars; cooldown 20 native bars. Accounting status: blocked (md2_catalog), present in roster (md2_ausar_map). Slice capital is the shared aster_batch1 spec's slice for this sleeve; the exact slice value is in desk3/aster_batch1.py and is not restated here beyond the sizing formula in the algorithm.

## Data inputs

Declared inputs: tensor, bars, positions (algorithm doc). Accounting data note: completed Yahoo bars, canonical v698 where applicable, actual received execution quotes.

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path (all are already in Test for a built package; for an INCOMPLETE-CODE package there is no code to place).
3. Wire the producers so the inputs named under Data inputs arrive in the shapes the Full algorithm describes, with the configuration under Configuration.
4. Run the sleeve's entry point named in the code (its sleeves() factory or evaluate(view, ctx) wrapper) on a fixture snapshot that satisfies the entry conditions and confirm the expected intent before any live use.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

- No entry with fewer than 4 panel bars, balance improvement under 2 over the last 4 bars, fewer than 2 of 7 vote channels increasing, total_votes not 7 at either panel end, close under $5, DV20 under $1,000,000, non-positive ATR14, warmup under 234 bars, or inside the 20-bar cooldown.
- Excluded symbols SPY, QQQ, B, GOLD never enter; holdings never exceed 10.
- Ranking follows repair + 0.01 * balance[-1] + 0.001 * clip(obv_slope5 / volume, -10, 10), ties by symbol ascending; shares = floor(min(0.10 * equity, 0.01 * DV20, cash) / (execution price * 1.001)).
- The only exit is the full sale at 20 native bars from the entry bar index (late observation still exits), and an evaluation emitting an exit emits no entry.
