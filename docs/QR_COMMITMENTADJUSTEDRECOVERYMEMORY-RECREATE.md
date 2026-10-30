# qr-commitmentadjustedrecoverymemory: Recreation package

## Provenance

- Canonical id: `qr-commitmentadjustedrecoverymemory`; canonical name: CARM recovery memory; aliases: qr_commitmentadjustedrecoverymemory.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type other, family quant_research, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "CARM recovery memory" (also docs/ALL-SLEEVES.md); Test catalog entry 'qr-commitmentadjustedrecoverymemory' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; matching material only as noted in Provenance); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/carm.py. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

CARM recovery memory: a 90% QQQ core plus short intraday trades on registered shock-recovery order-book episodes; with none registered it holds QQQ. Accounting grade PARTIAL (no entry, exit or sizing recorded); the code and card record all three, and the code is the truth.

## Full algorithm

From `sleeves/quant_research/carm.py` (SID qr_commitmentadjustedrecoverymemory) and its card:

1. Core: a declared 90% QQQ core, rebalanced monthly only while the sleeve is flat (drift retained otherwise); the sleeve is at most 10% of equity, 2 positions, 5% per name and per sector; settled cash only.
2. Episodes: registered shock-recovery episodes (cache/qr_carm_registry.json): per episode the native lifecycle summaries of the frozen bid and ask bands (added, executed, cancelled, live and mature-live shares from first-received canonical order-ID events), the anchors, and the fitted lower / upper estimates G_L, O_U, C_U, H, the paired increment, CPDW, plus support counts.
3. Memory (`reference_kernel.cohort_memory` over the episode's events when supplied, else its summaries): commitment M = (E - C + L20) / A per side; the sleeve uses the bid-minus-ask commitment.
4. Admission (`reference_kernel.admit`): gross_lower, qqq_upper, incremental_lower and cost_upper >= 15 bp with overhead, both inequalities, and CPDW > 5 bp; inside the 10:02-14:40 ET entry window; spread <= 4 bp. The card adds: an incremental lower bound > 5 bp and gross lower - QQQ upper > 2 x cost (>= 15 bp) + overhead + 10 bp; one look per episode; none within 30 minutes of the name's last exit or after a 1% daily loss.
5. Support: >= 500 training episodes over 100 dates and 60 calibration dates.
6. Execution: a marketable limit at the ask + one tick, 10-second life, size min(5% equity, the sleeve's room).
7. Exits, first of: the bid 40 bp under the average entry, the bid 60 bp over it, 30 minutes after the first fill, the session close minus 10 minutes; a 1% account daily loss blocks entries and liquidates the sleeve; 30-minute cooldown.
Named divergence in the code header: native order-ID lifecycle data has no free public source; the lifecycles and fitted estimates are registered research inputs. With none registered the account holds its QQQ core.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Sleeve module (already in Test): `sleeves/quant_research/carm.py` (also `packages/claude/master-desk-sleeve-port-library/desk/sleeves/quant_research/carm.py`).
- Shared quant-research support (already in Test): `sleeves/quant_research/r10.py`, `sleeves/quant_research/common.py` (imported by the module).
- Existing strategy card (already in Test): `strategies/quant_research/qr-commitmentadjustedrecoverymemory.md`.
- Rule lines (already in Test): `docs/verify/quant_research.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry for this canonical id; Test catalog entry in `docs/CATALOG.json`.

## Configuration

Book $1,000,000 (card); CORE {QQQ: 0.90}; SLEEVE_MAX 0.10, POSITIONS 2, NAME_MAX 0.05; STOP_BP 40, TARGET_BP 60, HOLD_S 1800, CLOSE_BUFFER_S 600, DAILY_LOSS 0.01, COOLDOWN_S 1800; SPREAD_BP 4.0, CPDW_BP 5.0, COST_FLOOR_BP 15.0; SUPPORT {train_episodes: 500, train_dates: 100, calibration_dates: 60}; WINDOW 10:02-14:40 ET. Universe: QQQ and registered episode stocks. Asset: US equities and QQQ. Timeframe: intraday (<= 30 minutes).

## Data inputs

Registry file cache/qr_carm_registry.json and live quotes. Vendored kernel under desk/vendor/quant_research/r10/carm/ (referenced by the code header).

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (cash, core, or no intent), never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- No registered episode: the account holds only the 90% QQQ core, rebalanced monthly only while flat.
- An episode failing support, the admit inequalities, CPDW > 5 bp, the spread cap, the window, the cooldown or the daily-loss block: no entry.
- An admitted episode: one marketable limit at ask + one tick, 10 s life, size min(5% equity, sleeve room), at most 2 positions.
- Exit fires on the first of -40 bp, +60 bp, 30 minutes, close minus 10 minutes, or the 1% daily-loss liquidation.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
