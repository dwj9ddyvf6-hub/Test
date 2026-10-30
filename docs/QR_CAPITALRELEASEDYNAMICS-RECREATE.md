# qr-capitalreleasedynamics: Recreation package

## Provenance

- Canonical id: `qr-capitalreleasedynamics`; canonical name: CRD capital release; aliases: qr_capitalreleasedynamics.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type other, family quant_research, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "CRD capital release" (also docs/ALL-SLEEVES.md); Test catalog entry 'qr-capitalreleasedynamics' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; matching material only as noted in Provenance); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/crd.py. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

CRD capital release: a weekly optimized long book of up to 30 registered capital-release candidates; with no decision documents registered it holds cash. Accounting grade PARTIAL (no entry, exit or sizing recorded); the code and card record all three, and the code is the truth.

## Full algorithm

From `sleeves/quant_research/crd.py` (SID qr_capitalreleasedynamics) and its card:

1. Account: $1m, cash plus at most 30 names, 5% a name, 25% a sector, 20% a positive-correlation cluster (0.7), gross <= 95%, cash >= 5%, forecast annualised volatility <= 20% on the 20-session covariance, ordinary weekly buys + sells <= 30% NAV; idle cash stays cash.
2. Weekly decision (Friday 16:15 cutoff, frozen for the next session) over the registered decision document (cache/qr_crd_registry.json: per decision session the optimisation domain: names, then-known sectors, the cluster partition, the 20-session covariance, the synchronized lower-mean gross scenarios and cash gross, each candidate's frozen evidence: residual rank and rank 20 sessions earlier, the 10-session residual sum, the release flag, the calibrated and rank-only forecasts with their SEs, the Kish origin ESS, the calibration origin dates, the round trip cost, and the trailing ADV; per session close the held names' monitoring evidence: rank, conservative forecast, fundamental eligibility).
3. Entry gate (`crd_r10.entry_allowed`): release flag; rank 0.60-0.95 and +0.20 in 20 sessions; positive residual sum; ESS >= 30; >= 100 calibration dates; increment over rank-only - 1.645 SE > 0; forecast - 1.645 SE > round trip + 0.002. Names neither admitted nor held leave the domain.
4. Plan (`crd_r10.optimize_target` over the held weights at the executable marks; trade only when the robust log-wealth gain > log(1.0002) or holding is illegal), `crd_r10.round_target` to whole shares under the caps.
5. Execution: the next session 09:35-10:05 ET, sells first, at most 0.5% of the trailing ADV per name and session; the unfilled remainder expires at 10:05.
6. Exits (`crd_r10.exit_decision`, at each session's first pass on the previous close): residual rank < 0.40, a conservative forecast <= 0, lost fundamental eligibility, a hard cap breach, an 8% entry-to-close drawdown, a 20% peak-to-close account drawdown (liquidates everything); a drawdown exit starts a five-session entry cooldown. Release expiry alone is no exit.
Named divergences in the code header: the canonical inputs have no free source and the kernel's interface takes the synchronized scenarios and calibration from its caller; the decision documents are registered research inputs. With none registered the account stays in cash. The 5%-of-interval-volume participation cap is not enforced; the 0.5% ADV cap is.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Sleeve module (already in Test): `sleeves/quant_research/crd.py` (also `packages/claude/master-desk-sleeve-port-library/desk/sleeves/quant_research/crd.py`).
- Shared quant-research support (already in Test): `sleeves/quant_research/r10.py`, `sleeves/quant_research/common.py` (imported by the module).
- Existing strategy card (already in Test): `strategies/quant_research/qr-capitalreleasedynamics.md`.
- Rule lines (already in Test): `docs/verify/quant_research.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry for this canonical id; Test catalog entry in `docs/CATALOG.json`.

## Configuration

Book $1,000,000; at most 30 names, 5% a name, 25% a sector, 20% a positive-correlation cluster (0.7), gross <= 95%, cash >= 5%, forecast volatility <= 20%, weekly turnover <= 30% NAV (all from the code header and card). Decision: Friday 16:15 cutoff. Execution window 09:35-10:05 ET, <= 0.5% ADV per name per session. Universe: registered decision documents. Asset: US equities. Timeframe: 1w decisions.

## Data inputs

Registry file cache/qr_crd_registry.json and live quotes (marked at the mid, per the card). Vendored kernels under desk/vendor/quant_research/r10/crd/ (referenced by the code header). Parity note in the code header: tools/parity/qr_r10_kernels.py -> docs/receipts/parity/qr_r10_kernels.json.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (cash, core, or no intent), never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- No registered decision document: the account stays in cash.
- A candidate failing any entry_allowed condition (release, rank band and rise, residual sum, ESS, calibration dates, either 1.645 SE test): it leaves the domain and is not bought.
- A plan with robust log-wealth gain <= log(1.0002) and legal holding: no trade. Execution only the next session 09:35-10:05, sells first, <= 0.5% ADV, remainder expires.
- Exit fires on the first listed exit_decision trigger at a session's first pass; a 20% account drawdown liquidates everything; a drawdown exit starts a 5-session cooldown.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
