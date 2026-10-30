# qr-contractqueuerevaluation: Recreation package

## Provenance

- Canonical id: `qr-contractqueuerevaluation`; canonical name: CQR contract queue revaluation; aliases: qr_contractqueuerevaluation.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type other, family quant_research, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "CQR contract queue revaluation" (also docs/ALL-SLEEVES.md); Test catalog entry 'qr-contractqueuerevaluation' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; matching material only as noted in Provenance); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/cqr.py. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

CQR contract queue revaluation: buys an issuer the session after a registered contract award re-optimizes its order book to a positive value gain, for up to 63 sessions; with no packets registered it holds cash. Accounting grade PARTIAL (no entry, exit or sizing recorded); the code and card record all three, and the code is the truth.

## Full algorithm

From `sleeves/quant_research/cqr.py` (SID qr_contractqueuerevaluation) and its card:

1. Account: $1m in cash and stocks, at most 5% per issuer, 25% per sector, 15% per program cluster and 20 issuers, at least 5% cash; unallocated cash stays cash.
2. Decision at the 16:15 ET cutoff over the registered contract packets (cache/qr_cqr_registry.json: the issuer's documented order book before and after the award, each order's quantity, avoidable contribution per unit, resource use per unit, mandatory flag and documented shortfall remedy; the qualified resource capacity; the uncounted collectible settlement; the issuer's market value and its registered OOF excess forecast; the matured cluster history).
3. Revaluation (`queue_delta_r10.paired_delta(before, after, capacity, settlement)`): both books re-optimised under the same physical capacity (the kernel's certified one-period LP); delta_usd / market value must be > 0.
4. Support: 100 mature contract clusters, 20 issuers, 24 origin months (and 30 older OOF calibration clusters).
5. Economics: the registered excess forecast above full costs (max(15 bp, measured) per side) + 50 bp. The card phrases the admission bar as the forecast above 2 x max(15 bp, the measured side cost) + 50 bp.
6. Entry: the next regular session 09:35-10:05 ET on observed quotes, whole shares, expiring 10:05; weight = min(5%, the 25% sector and 15% cluster room, the 95% gross room) per the card.
7. Exits: 63 observed sessions, an observed 8% position loss, an adverse operative revision (the packet's `revoked` flag); a 20% account loss liquidates and pauses entries for 20 sessions.
Named divergence in the code header: contract packets have no free public source; they are registered research inputs. With none registered the account stays in cash.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Sleeve module (already in Test): `sleeves/quant_research/cqr.py` (also `packages/claude/master-desk-sleeve-port-library/desk/sleeves/quant_research/cqr.py`).
- Shared quant-research support (already in Test): `sleeves/quant_research/r10.py`, `sleeves/quant_research/common.py` (imported by the module).
- Existing strategy card (already in Test): `strategies/quant_research/qr-contractqueuerevaluation.md`.
- Rule lines (already in Test): `docs/verify/quant_research.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry for this canonical id; Test catalog entry in `docs/CATALOG.json`.

## Configuration

Book $1,000,000; MAX_ISSUER 0.05, MAX_SECTOR 0.25, MAX_CLUSTER 0.15, MAX_ISSUERS 20, MIN_CASH 0.05; SUPPORT {episodes: 100, issuers: 20, months: 24}; COST_FLOOR 0.0015, BUFFER 0.005, STOP_LOSS 0.08, ACCOUNT_STOP 0.20, PAUSE 20; HOLD 63; ENTRY_FROM 09:35, ENTRY_TO 10:05. Universe: registered contract issuers. Asset: US equities. Timeframe: 1d (up to 63 sessions).

## Data inputs

Registry file cache/qr_cqr_registry.json and live quotes. Vendored kernel under desk/vendor/quant_research/r10/cqr/ (referenced by the code header).

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (cash, core, or no intent), never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- No registered packet: the account stays in cash.
- A packet with paired_delta / market value <= 0, failing support, or failing the economics bar at the 16:15 cutoff: no entry.
- An admitted issuer: entry only the next session 09:35-10:05, whole shares, expiring 10:05, within the issuer / sector / cluster / issuer-count caps and the 5% minimum cash.
- Exit fires on the first of 63 sessions, an 8% loss, or a revoked packet; a 20% account loss liquidates and pauses entries for 20 sessions.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
