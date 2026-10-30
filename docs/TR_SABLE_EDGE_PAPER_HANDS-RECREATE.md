# tr-sable-edge-paper-hands: Recreation package

## Provenance

- Canonical id: `tr-sable-edge-paper-hands`; canonical name: Edge paper hands (10 lineages); aliases: sable_edge_paper_hands.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type other, family tensor_research, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Edge paper hands (10 lineages)" (also docs/ALL-SLEEVES.md); Test catalog entry 'tr-sable-edge-paper-hands' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree; research notes only as noted in Provenance, no deployable sleeve code for these ids).
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/tensor_research/tensor_research.py + sleeves/tensor_research/feedlib/. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

Edge paper hands (10 lineages): ten equal sub-books, one per trading lineage, buy a watchlist stock on a clean completed-hour Tensor BUY and sell on a clean SELL, inside Sable's swing bracket and each lineage's rule. Accounting grade PARTIAL (entry, exit and sizing recorded as gaps in the accounting); the card and rule lines in this repo record all three.

## Full algorithm

From the strategy card `strategies/tensor_research/tr-sable-edge-paper-hands.md` and the family module, in evaluation order:

1. Each completed regular-session hour, 2-11 minutes after it closes, the watchlist and held names are read.
2. Buy: the hour's Tensor state is VECTOR_BUY with exactly one buy-green or buy-gold marker, for a name the sub-book does not hold.
3. Gates: under 6 positions, cash for a share, the regular session, price <= 1.85 ATR above the 64-hour support, RSI <= 72, no ETF, not parked, the sub-book not parked by a 2% day loss.
4. Lineage rules that act here: PTJ sizes down when its sub-book is red on the day; Druckenmiller, once holding a name, buys another only on a gold read; Minervini sells a holding at or under cost when the hour prints no buy.
5. Exit: a clean Tensor SELL (VECTOR_SELL with exactly one sell-red or sell-magenta) sells the holding. Bracket on each hour's close: stop at entry - 1.6 ATR, target at entry + 2.8 ATR (the hour's ATR, at least 1.5% of entry); market orders.
6. Sizing: each sub-book is a tenth of the $100,000 book: shares = min(0.5% of equity / 1.6 ATR, 15% of equity / price, 98% of cash / price); 0.25% and 8% when sized down.
Card notes: the Edge brief (headlines, filings, the scan) is empty here, so the lineage rules that need it never fire; Qullamaggie's 3% risk is recorded but not used in sizing; the source's break-even step at +1.6 ATR is reset by the stop floor on every pass, so it never fires.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Shared engine (already in Test): `sleeves/tensor_research/tensor_research.py` (the master-desk forward-test book module for the tensor_research family), with feedlib `sleeves/tensor_research/feedlib/tensor_research.py` and `sleeves/tensor_research/feedlib/tensor_research.mjs` (for the paper-hands book: `sleeves/tensor_research/feedlib/tensor_research_hands.mjs`).
- Strategy card (already in Test): `strategies/tensor_research/tr-sable-edge-paper-hands.md`.
- Rule lines (already in Test): `docs/verify/tensor_research.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry for this canonical name; Test catalog entry in `docs/CATALOG.json`.
- Named on the card as not in this repo: `desk/vendor/foliotend_research/autopilot/scout-hands.mjs`, `desk/vendor/foliotend_research/autopilot/lineage.mjs`. The Tensor engine itself is a hard rail and is not part of this package.

## Configuration

Universe: AAPL, MSFT, NVDA, AMZN, JPM, XOM (SPY, QQQ, IWM, SMH as context). Asset: US equities. Timeframe: 1h. Book $100,000 split into 10 equal lineage sub-books. Card status: waiting.

## Data inputs

The canonical hourly series (1 year) of the watchlist and held names, read by the v698 Tensor engine; quotes built from the same hours.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / data inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (no intent / UNFED), never fake-fed.
5. Call the module's evaluate entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- An hour whose Tensor state is not VECTOR_BUY, or with other than exactly one buy-green/buy-gold marker: no buy.
- A buy failing any gate (6 positions, price more than 1.85 ATR above the 64-hour support, RSI > 72, ETF, parked, 2% day-loss park): no buy.
- A clean VECTOR_SELL with exactly one sell-red/sell-magenta sells the holding; the bracket stop/target are entry -/+ 1.6 / 2.8 ATR with ATR at least 1.5% of entry.
- Shares equal min(0.5% of equity / 1.6 ATR, 15% of equity / price, 98% of cash / price) per sub-book (0.25% / 8% when sized down).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
