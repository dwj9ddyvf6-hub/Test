# qr-auctionimpulseresponsetrading: Recreation package

## Provenance

- Canonical id: `qr-auctionimpulseresponsetrading`; canonical name: AIRT auction impulse; aliases: qr_auctionimpulseresponsetrading.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type other, family quant_research, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "AIRT auction impulse" (also docs/ALL-SLEEVES.md); Test catalog entry 'qr-auctionimpulseresponsetrading' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; matching material only as noted in Provenance); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/airt.py. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

AIRT auction impulse: buys a stock after a registered opening-auction impulse routes to continuation or recovery with calibrated expectancy, holding up to 30 minutes; with no episodes registered it holds cash. Accounting grade PARTIAL (no entry, exit or sizing recorded in the accounting); the code and card in this repo record all three, and the code is the truth.

## Full algorithm

From `sleeves/quant_research/airt.py` (SID qr_auctionimpulseresponsetrading, capital 1000000.0, cadence_s 60, schedule rth) and its card:

1. Inputs: registered morning episodes (cache/qr_airt_registry.json): per symbol and session the frozen 09:35 detector inputs: opening displacement x0 (factor residual, bp), volume and auction ratios v0 / a0, residual scale, the two dose probes' paths x1 / x2, signed-flow fractions q1 / q2, impacts eta1 / eta2, VWAPs, spreads, midpoint, 20-day ADV, last-60-second dollars, 1-minute sigma, and the matured policy-label records of the episode's cell.
2. Route (`airt_r1.route`): continuation or recovery; requires v0 >= 2, a0 >= 1.25, |x0| >= max(20 bp, 1.5 sigma0), second-probe spread <= 8 bp and <= 70% of the first, plus the route's flow / impulse / VWAP conditions. The card states the routes as: continuation (an up move holding >= 80% through both probes with buying flow, building impact and the mid above both VWAPs) or recovery (a down move with selling then neutral flow, rebounding impact and the mid above the first VWAP).
3. Support (`airt_r1.calibration` on the cell's records): >= 200 earlier events over >= 60 session dates; day-cluster mean and SE of the exact policy label.
4. Admission (`airt_r1.expectancy_admitted`): mean - 1.645 SE > 2 x round trip + 10 bp.
5. Size (`airt_r1.size_shares`: 0.1% equity / d, 10% equity, 0.1% ADV, 2% of the last minute's dollars) inside `airt_r1.portfolio_capacity` (4 names, 40% gross, 25% sector, 10% name; no entry after a 0.5% session loss or a 5% peak drawdown), with d = `airt_r1.stop_distance(D, sigma1m)`; the card gives d = max(10 bp, half the displacement, 2 x the 1-minute sigma).
6. Entry: a marketable limit capped at the decision ask + 2 bp, 90 seconds, one attempt per symbol and session, by the 09:50 probe deadline.
7. Exits (`airt_r1.exit_reason`), first of: stop at entry x (1 - d), target at entry x (1 + 2d), the recovery thesis when the residual reaches zero, 30 minutes after the first fill, flat by 15:45.
Named divergence in the code header: the detector's inputs need the official opening cross and related feeds with no free live source; the morning episodes are registered research inputs. With none registered the sleeve stays in cash.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Sleeve module (already in Test): `sleeves/quant_research/airt.py` (also `packages/claude/master-desk-sleeve-port-library/desk/sleeves/quant_research/airt.py`).
- Shared quant-research support (already in Test): `sleeves/quant_research/r10.py`, `sleeves/quant_research/common.py` (imported by the module).
- Existing strategy card (already in Test): `strategies/quant_research/qr-auctionimpulseresponsetrading.md`.
- Rule lines (already in Test): `docs/verify/quant_research.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry for this canonical id; Test catalog entry in `docs/CATALOG.json`.

## Configuration

Book $1,000,000; params {positions: 4, gross: 0.4, sector: 0.25, name: 0.10, deadline: 09:50, flat: 15:45, cap_bp: 2.0, window_s: 90}; cadence_s 60; schedule rth; needs quotes (equity). Universe: registered morning episodes. Asset: US equities. Timeframe: intraday (<= 30 minutes).

## Data inputs

Registry file cache/qr_airt_registry.json and live quotes (SPY for the recovery residual). Vendored decision kernels under desk/vendor/quant_research/r10/airt/ (referenced by the code header; the sleeve module itself is in this repo at the path listed).

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (cash, core, or no intent), never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- No registered episode for the session: no entry, the sleeve holds cash.
- An episode failing route, calibration support (< 200 events or < 60 dates), or the expectancy test (mean - 1.645 SE <= 2 x round trip + 10 bp): no entry.
- A routed, admitted episode: one entry attempt only, limit at ask + 2 bp, 90 s, by 09:50, sized by the size_shares / portfolio_capacity rules above.
- Exit fires on the first of stop, target (2d), recovery residual zero, 30 minutes after first fill, or 15:45 flat.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
