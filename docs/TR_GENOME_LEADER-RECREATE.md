# tr-genome-leader - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Leader genome", type momentum, family tensor_research, style evidence "Momentum", universe "1,838-name genome roster", asset class US equities, timeframe "1h / 1d / 1wk", creator "FolioTend / Griffith Tensor research (archived desk research), as a forward-test book", algorithm grade PARTIAL with gaps: entry/signal rule, exit rule and sizing "not recorded in any consulted source"; algorithm sources: Test catalog entry/variants. Those gaps are closed below by the strategy card and the code in this repo.
- Strategy card in Test: `strategies/tensor_research/tr-genome-leader.md` (status live), naming the code `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py` and `sleeves/tensor_research/feedlib/tensor_research.mjs`, with rule lines in `docs/verify/tensor_research.md`. The card also records that the FolioTend research sidecar source file itself is not in this repo; the desk book in tensor_research.py is the executable form present here, and its genome detector consumes the sidecar's per-bar genome marks.
- Code search record, in order: dwj9ddyvf6-hub/Test (fresh recursive tree plus the content reads named under Files in this repo); dwj9ddyvf6-hub/Silicon (fresh recursive tree, grepped for the canonical id, its aliases and its family tokens: no matching path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree, same grep: no matching path); dwj9ddyvf6-hub/Midna (fresh recursive tree, same grep: no matching path, except where a note below says otherwise). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

A forward-test event book over the 1,838-name genome roster: it buys a stock when the Tensor research sidecar marks it a Leader genome (extended, strong, active) on a completed buy bar, on the hourly, daily or weekly timeframe, and sells at the close of bar 20. In code the sleeve id is genome_leader and the genome id is LEADER.

## Full algorithm

From the card and `sleeves/tensor_research/tensor_research.py` (GENOMES map genome_leader -> LEADER; detect_genome; EventBook for genome_leader over intervals 1h, 1d, 1wk; HORIZON = 20; STUDY_SIDE_BPS = 25.5):

1. Event detection (detect_genome): on a frame's last completed bar, if the bar's sidecar record carries a genome whose id is LEADER, emit one event for (genome_leader, symbol, interval, bar timestamp) tagged LEADER. The detector itself applies no further numeric filter; the Leader mark is the sidecar's, and the card records what that mark means: the five Leader tests are close at least 8% above EMA 21; Tensor medium RSI at least 60; the event bar's relative volume at least 1.2; 20-bar path efficiency at least 0.30; at least 4 bullish votes; shown only on a bar with a Tensor buy marker or a phenotype, with at least 3 of the 5 tests passing, read on the bar before the event.
2. Freshness: only the bar just completed counts, and the roster's run publishes once at least half its names reach it (card Entry section).
3. Entry (EventBook): the next bar's open, a market order within that hour (hourly) or session (daily, weekly); skipped once that window has passed. (The EventBook desk path in code enters on a break of the signal bar's high within its entry window, with the order expiring at the window end; both forms are recorded in the sibling genome packages in this repo, and the card form above is this strategy's own record.)
4. Exit: the close of bar 20 after the event bar (market-on-close when it ends a session); horizons = (20,) on every event.
5. Sizing: one equal slot per event: the $100,000 book / (1,838 names x 3 timeframes), about $18; skipped when the book lacks the cash. Modeled cost 25.5 bp per side (25 bp slippage + 0.5 bp fee; 51 bp round trip).

## Files in this repo

- This package: `docs/TR_GENOME_LEADER-RECREATE.md`
- Strategy card: `strategies/tensor_research/tr-genome-leader.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py` (GENOMES, detect_genome, EventBook genome_leader, research_sleeves())
- Feedlib: `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`
- Rule lines: `docs/verify/tensor_research.md`
- Not in this repo (recorded on the card): the FolioTend research sidecar source `desk/vendor/foliotend_research/v619/app/lib/foliotend-research-sidecar.ts`; tensor_research.py pins it by archive repo, commit and blob hash (V619 record).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`; Test catalog entry `tr-genome-leader` in `docs/CATALOG.json`

## Configuration

- Book: $100,000; slot = book / (1838 x 3), about $18 per event; cost 25.5 bp per side.
- Code constants: GENOMES {genome_leader: LEADER}; HORIZON 20; intervals (1h, 1d, 1wk); the V619 sidecar source record (archive repo foliotend-research-operations-archive, commit and blob pinned in tensor_research.py).
- No further configuration is recorded for this strategy; anything further is not in the record.

## Data inputs

- Completed regular-session hourly bars (1 year), daily bars (2 years) and weekly bars (10 years) for the 1,838-name roster, from Alpaca SIP with keys, else Yahoo (card Data section).
- The pinned Tensor engine v698 runner output per name and timeframe, including each bar's sidecar genome marks (the LEADER mark is an input, not computed by the detector in this repo).

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc and the ALL-SLEEVES accounting entry for this strategy.
3. Confirm `sleeves/tensor_research/tensor_research.py` still maps genome_leader to LEADER and registers its EventBook over (1h, 1d, 1wk) in research_sleeves().
4. Wire the roster bar feeds and the Tensor runner output so frames carry sidecar genome marks; run the book's evaluation per completed bar on each timeframe.
3. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec from the Full algorithm (no dedicated test file for this exact id was found in Test):

- A last completed bar whose sidecar genomes do not include LEADER produces no event, whatever its other marks.
- A LEADER mark on a bar that is not the just-completed bar produces no entry (stale events are skipped once their entry window passes).
- Each event takes exactly one slot of about $18 from the $100,000 book; an event with no cash for its slot is skipped, not resized.
- A held event position exits at the close of bar 20 after its event bar.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
