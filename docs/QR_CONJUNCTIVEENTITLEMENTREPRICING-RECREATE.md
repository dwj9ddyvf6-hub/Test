# qr-conjunctiveentitlementrepricing: Recreation package

## Provenance

- Canonical id: `qr-conjunctiveentitlementrepricing`; canonical name: CER entitlement repricing; aliases: qr_conjunctiveentitlementrepricing.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type other, family quant_research, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "CER entitlement repricing" (also docs/ALL-SLEEVES.md); Test catalog entry 'qr-conjunctiveentitlementrepricing' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; matching material only as noted in Provenance); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/cer.py. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

CER entitlement repricing: a 49% QQQ / 49% SPY core that funds 2% stock positions when a registered project's required entitlement conditions all turn true; with no projects registered it holds the core. Accounting grade PARTIAL (no entry, exit or sizing recorded); the code and card record all three, and the code is the truth.

## Full algorithm

From `sleeves/quant_research/cer.py` (SID qr_conjunctiveentitlementrepricing) and its card:

1. Account: $1m reference capital, QQQ 49% / SPY 49% / cash 2%; each episode displaces 1% of each index for a 2% stock position; at most 4 issuers, 8% of the sleeve in stocks, 4% per operator / buyer / region cluster. No shorting, derivatives or borrowing.
2. Decision at 16:15 ET each session over the registered projects (cache/qr_cer_registry.json: each project's frozen AND graph of 1..8 required predicates, horizon H in {21, 63}, the after / before equity-cash value intervals and the dated equity value; the proofs with their publication / receipt / extraction / verification / effective clocks; the matured-episode history).
3. Closure (`reference_kernel_r10.closure`): every required predicate TRUE now, not all TRUE at the prior 16:15 snapshot, and a new usable TRUE proof in between.
4. Economics: `robust_conversion_screen(after, before, equity value)` > 0 (None = unsupported economics: abstain).
5. Support: at least 100 matured episodes, 40 issuers, 10 operator-region groups and 36 months of labels.
6. Forecast: the registered net dual-index forecast above the 50 bp buffer.
7. Entry: the next session from 09:45 ET, the donor sale (1% QQQ, 1% SPY) and a limit buy at most 25 bp above the offer; an admission expires after five sessions, an unfilled order after one session.
8. Exits, first trigger: H sessions from the first fill, a revoked required condition (a usable FALSE / conflicting proof), a 12% loss on the observed bid; the donor is restored with the proceeds.
Named divergence in the code header: proofs and project economics have no free public feed; they are registered research inputs. With none registered the account holds its funded core.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Sleeve module (already in Test): `sleeves/quant_research/cer.py` (also `packages/claude/master-desk-sleeve-port-library/desk/sleeves/quant_research/cer.py`).
- Shared quant-research support (already in Test): `sleeves/quant_research/r10.py`, `sleeves/quant_research/common.py` (imported by the module).
- Existing strategy card (already in Test): `strategies/quant_research/qr-conjunctiveentitlementrepricing.md`.
- Rule lines (already in Test): `docs/verify/quant_research.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry for this canonical id; Test catalog entry in `docs/CATALOG.json`.

## Configuration

Book $1,000,000; CORE {QQQ: 0.49, SPY: 0.49}; DONOR {QQQ: 0.01, SPY: 0.01}; STOCK_W 0.02, MAX_ISSUERS 4, MAX_STOCKS 0.08, MAX_CLUSTER 0.04; SUPPORT {episodes: 100, issuers: 40, groups: 10, months: 36}; BUFFER 0.005, STOP_LOSS 0.12, LIMIT_BPS 25; DECIDE_HM 16:15, ENTRY_HM 09:45; ADMISSION_SESSIONS 5. Universe: QQQ, SPY and registered project issuers. Asset: US equities and ETFs. Timeframe: 1d (21- or 63-session hold).

## Data inputs

Registry file cache/qr_cer_registry.json and live quotes. Vendored kernel under desk/vendor/quant_research/r10/cer/ (referenced by the code header).

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (cash, core, or no intent), never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- No registered project closing: the account holds QQQ 49% / SPY 49% / cash 2%.
- A project failing closure, the economics screen, support, or the 50 bp forecast buffer at the 16:15 decision: no admission.
- An admitted project: entry only from 09:45 within 5 sessions, donor sale 1% + 1%, limit buy at most 25 bp above the offer, 2% stock position.
- Exit fires on the first of H sessions, a revoked condition, or a 12% bid loss, and the donor is restored.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
