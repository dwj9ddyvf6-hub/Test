# mn-hyperliquid-floor - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Hyperliquid momentum floor", type momentum, family midna, style momentum, universe "Hyperliquid perps with day notional >= $25M", asset class crypto perps, timeframe intraday (10-min scan), creator "Midna's TypeScript desk (equity books), ported line for line to the master desk", algorithm grade PARTIAL with gaps: entry/signal rule, exit rule and sizing not recorded in any consulted source. Alias midna_hyperliquid_momentum_floor, status test_catalog live (entry mn-hyperliquid-floor).
- Test catalog entry: `docs/CATALOG.json` entry 'mn-hyperliquid-floor'.
- Strategy card in Test: `strategies/midna/mn-hyperliquid-floor.md` ("Trades the strongest uncrowded daily mover among liquid Hyperliquid perps, long or short, with a 2R target." Status live; notes: the master desk drops Midna's 3% daily-loss halt.) The card names the code: `sleeves/midna/hyperliquid.py`, rule lines in `docs/verify/midna.md`.
- Source pinning in the code: the module docstring and SOURCE record in `sleeves/midna/hyperliquid.py` pin the original TypeScript desk sources by commit and blob (src/lib/desk.ts lines 194-387 for runScan / propose, with decide / applyExits / closeAt / maybeWatch; src/lib/decide.ts for pickScan, classifySetup, stopDistancePct, sizeTrade, levels, withinCaps, fillPrice, exitSignal; src/lib/market.ts for the feed), and state the port is line for line on Hyperliquid's public book (desk/feedlib/midna_hyperliquid.py in the master-desk layout).
- Code search record, in order: dwj9ddyvf6-hub/Test (recursive tree plus content read of `sleeves/midna/hyperliquid.py` and the card: both found in Test, listed under Files in this repo); dwj9ddyvf6-hub/Silicon (recursive tree: the only hyperliquid-named paths are unrelated Nansen rea-teardown JavaScript assets, no sleeve code); dwj9ddyvf6-hub/quant-research-backup (recursive tree: no hyperliquid floor sleeve path); dwj9ddyvf6-hub/Midna (recursive tree: the original TypeScript desk is the pinned source of the Test port; no separate Python sleeve for this id, and the port in Test is the executable form). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

A single-book intraday momentum floor on liquid Hyperliquid perpetuals: every 10 minutes it scans the liquid perps, picks the strongest uncrowded daily mover (majors first), sizes it by a fixed risk fraction against a range-based stop, enters with a 2R target, and closes the position when the mark crosses the stop or the target. At most 3 positions are open at once and no coin is opened twice.

## Full algorithm

From the code in Test (`sleeves/midna/hyperliquid.py`: module functions classify_setup, candidates, pick_scan, stop_distance_pct, size_trade, levels, within_caps, fill_price, exit_signal, step, and class HyperliquidFloor). The accounting graded this PARTIAL; the rules below are supplied by the card and the code, and the accounting gaps are named at the end.

Constants (verbatim from the code): RULES {trendPct 0.01, crowdedLongFunding 0.00004, crowdedShortFunding -0.00001, minStopPct 0.006, rangeMultiple 1.2, fallbackStopPct 0.012, maxStopPct 0.08, rewardMultiple 2, slippageBps 1, minDayNotional 25,000,000, minNotional 50, watchMinutes 10, rejectCooldownHours 6, startingCash 100,000}; LIMITS {riskPerTradePct 0.5, maxOpenPositions 3, dailyLossHaltPct 3 (removed, see step 8), maxGrossNotionalPct 60, singleNameNotionalPct 20}; MAJORS (BTC, ETH, SOL).

Evaluation order in step(book, now, market, equity), called from HyperliquidFloor.signal(view):
1. Stale or empty market (market stale or no quotes) returns no orders.
2. Exits first: for each open position, read its coin's mark; exit_signal is "stop" when a long's mark is at or below its stop (a short's at or above), else "target" when a long's mark is at or above its target (a short's at or below), else none. On a signal the position is removed from the book and an exit order is emitted at fill_price for exits (the mark minus 1 bp for a long, plus 1 bp for a short; slippageBps 1, applied against the position on entry and in its favour on exit per fill_price).
3. Scan gate: if the last scan was less than watchMinutes 10 minutes ago, return the exit orders only. Otherwise record the scan time and prune reject cooldowns whose until time has passed.
4. Setup classification (classify_setup): with changePct ch and funding f (both must be finite): long when ch >= 0.01 and f <= 0.00004 (funding at most 0.004%, not a crowded long); short when ch <= -0.01 and f >= -0.00001 (funding at least -0.001%, not a crowded short); otherwise no setup.
5. Pick (pick_scan): keep quotes with dayNotional >= 25,000,000; rank by |changePct| descending; drop names with no setup and names in a (coin, side) 6-hour reject cooldown; if any of BTC, ETH, SOL qualifies, pick the strongest qualifying major, else the strongest qualifying name overall. No qualifying name means no ticket.
6. Stop and levels: stop distance pct = stop_distance_pct(mean hourly range of the last 8 hours) = min(max(0.006, range * 1.2), 0.08); with no candle range it is the fallback 0.012 (1.2%). Levels: for a long, stop = mark * (1 - stop_pct) and target = mark * (1 + stop_pct * 2); for a short, stop = mark * (1 + stop_pct) and target = mark * (1 - stop_pct * 2) (the 2R target).
7. Coin veto and sizing: if the picked coin is already open, no ticket. size_trade: no ticket at 3 open positions, on a non-positive or non-finite stop, or on non-positive equity; budget = equity * 0.5% (riskPerTradePct); notional = floor(min(budget / stop_pct, 20% of equity single-name cap, 60% gross cap minus gross already used)); gross room under $50 means no ticket; a floored notional under $50 (minNotional) means no ticket.
8. Door checks (the immediate approval, decide): if the mark is already through the stop, or the book is at 3 open positions, or the notional fails within_caps (single-name cap or gross room, with 0.5 tolerance), no ticket. Otherwise enter at fill_price for entries (mark plus 1 bp for a long, minus 1 bp for a short), qty = notional / entry, and record the position {side, entry, stop, target, notional, qty, openedAt}.
9. Removed at cutover (recorded in the code, REMOVED list): the daily loss halt (day P&L <= -3% -> no new risk until the next UTC day), and with it rollDay / refreshHalt. The LIMITS dailyLossHaltPct 3 value remains in the record as the removed gate's value; the sleeve CONFIG params carry removed_gates naming it and limits without it.
10. Engine-layer behaviour in HyperliquidFloor.signal (named divergences in the code): the floor queued every ticket for operator approval with the watch off until armed; the forward test runs the watch armed and approves each ticket at once (so no ticket is ever rejected and the reject cooldown never starts). A coin trades as its Kraken Futures perpetual on the sim venue sim:kraken_futures (notional sized on the Hyperliquid mark, filled at the Kraken quote); a coin Kraken does not list like for like is not traded and its ticket is recorded as an unfilled signal intent. The engine accrues Kraken perpetual funding on the open book and charges venue costs instead of the 1 bp slippage. A recorded position whose perp is gone is closed in the book; an exit sent is remembered in the closing state and sent again until its perp is flat. OrderSpec window is 600 seconds on both enter and exit intents.
11. Accounting gaps, per the accounting itself: entry/signal rule, exit rule and sizing were not recorded in any consulted accounting source; steps 1-10 above come from the strategy card and the code in Test, not from the accounting.

## Files in this repo

- This package: `docs/MN_HYPERLIQUID_FLOOR-RECREATE.md`
- Sleeve code (already in Test): `sleeves/midna/hyperliquid.py` (HyperliquidFloor; RULES, LIMITS, SOURCE pinning, step()).
- Strategy card: `strategies/midna/mn-hyperliquid-floor.md`.
- Rule lines: `docs/verify/midna.md`.
- Accounting and catalog: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`; `docs/CATALOG.json` entry mn-hyperliquid-floor.
- Other copies in Test (already present, not the primary source): `packages/claude/master-desk-sleeve-port-library/desk/sleeves/midna/hyperliquid.py`, `packages/claude/master-desk-feedlib/desk/feedlib/midna_hyperliquid.py`, `packages/claude/master-desk-parity-tools/tools/parity/midna_hyperliquid.py`.

## Configuration

- SleeveConfig in HyperliquidFloor: sleeve_id midna_hyperliquid_momentum_floor, family midna, cadence_s 60, capital 100,000 (RULES startingCash), universe (), schedule always, needs feeds [midna_hyperliquid], venue_pref sim:kraken_futures, params {rules: RULES as above, limits: LIMITS without dailyLossHaltPct, removed_gates: the daily-loss halt record, watch: "armed", approval: "immediate"}, state_schema {pos, lastScanAt, cooldowns, closing}.
- The scan cadence inside the algorithm is watchMinutes 10 (the 60-second sleeve cadence polls; step() enforces the 10-minute scan gate).
- Accounting-level configuration beyond the catalog entry: not in the record.

## Data inputs

- Hyperliquid public market data, delivered as view.extra midna_hyperliquid: quotes per coin {coin, mark, changePct (day move), funding, dayNotional}, hourly ranges per coin (ranges: the mean hourly range of the last 8 hours, for the stop distance), and a stale flag.
- The Kraken mapping for the sim venue (market kraken: {coin: perp symbol}) and the book's held perps, pending orders and equity, from the engine view.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc, the accounting entry in `docs/ALL-SLEEVES.json`, and the card `strategies/midna/mn-hyperliquid-floor.md`.
3. Confirm `sleeves/midna/hyperliquid.py` is present at that path.
4. Wire the midna_hyperliquid feed so each pass carries non-stale quotes (mark, day change, funding, day notional), hourly ranges, and the Kraken perp mapping, in the shapes the Full algorithm describes.
5. Register the sleeve as midna_hyperliquid_momentum_floor on the sim venue sim:kraken_futures with the Configuration values and run the desk cycle; the entry point is HyperliquidFloor.signal(view).
6. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec derived from the Full algorithm (no per-sleeve test file for this exact canonical id is present in this repo):

- Classification: a coin up exactly 1% with funding exactly 0.004% classifies long; up 1% with funding above 0.004% classifies no setup; down exactly 1% with funding exactly -0.001% classifies short.
- Liquidity and pick: a coin with day notional $24,999,999 is never picked; when a major and a stronger non-major both qualify, the major is picked; a (coin, side) inside its 6-hour reject cooldown is passed over.
- Stop: a mean hourly range of 0.4% gives a stop distance of 0.6% (the floor); 5% gives 6%; 10% gives 8% (the cap); no range gives 1.2%.
- Sizing: with equity $100,000 and a 1% stop, the risk budget is $500 and the raw notional $50,000, capped to $20,000 by the single-name cap; a resulting notional under $50, a full gross cap, or 3 open positions each produce no ticket.
- Exits and timing: a long whose mark touches its stop or target closes at the mark adjusted by 1 bp as in fill_price; no new scan occurs within 10 minutes of the last, while exits are still evaluated on every pass.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
