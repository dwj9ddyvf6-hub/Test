# C1 Feed Inventory, verified first-hand 2026-11-15

Workstream W7, C1 fresh-data protocol arming. Typed spend: $0.00.
Paper logging only. No orders were placed and no desk, book, or trading state was touched.

## Protocol needs (C1-RUNFILE.md section 3)

1. Spot 4h bars, completed only, for ETH, DOGE, LINK, XRP, ADA, SOL, and BTC as market reference. At least 180 lagged bars per asset before any event can qualify.
2. BTC perpetual prices at 4h granularity for the hedge leg marks.
3. BTC perpetual funding prints covering every holding window (venue native interval; an event with a missing print inside its window is ungradable for hedged policies, never zero-filled).

## What this estate held before this workstream (re-verified tonight)

Desk warm layer, ~/workspace/muse-desk-v3/state/warm_bars.json, fetched_at 2026-11-15T23:15:12Z, read directly tonight:

1. ADA/USD 4Hour: 546 bars, 2026-08-17T00:00:00Z to 2026-11-15T20:00:00Z. Held.
2. LINK/USD 4Hour: 546 bars, same span. Held.
3. BTC/USD and ETH/USD: 1Day only, 501 bars each. No 4h series.
4. SOL/USD: 15Min only, 2974 bars. No native 4h series.
5. DOGE/USD and XRP/USD: no series at any frame.

Desk perpetual state:

1. ~/workspace/muse-desk-v3/cache/bars/ holds PF_ADAUSD and PF_LINKUSD only. No BTC perpetual bars anywhere.
2. ~/workspace/muse-desk-v3/state/kraken_funding.json holds PF_ADAUSD and PF_LINKUSD only (519 hourly prints each at last runfile inspection).
3. ~/workspace/muse-desk-v3/state/coinalyze_funding_history.json holds ADA, ENJ, and LINK symbols only. No BTC funding.

Existing capture jobs: the desk warm layer and the Kraken producer cover the ADA and LINK legs only. No existing job on this estate captures BTC 4h bars, any of the missing spot 4h legs, BTC perpetual bars, or BTC perpetual funding. The runfile data rows C1-DATA-01 to C1-DATA-05 were all still open at the start of this workstream.

## Capture cure built tonight (public keyless sources only)

Source selection, routes tried in order:

1. Binance public REST (api.binance.com spot klines, fapi.binance.com futures klines and fundingRate). FAILED from this host. Exact response: "Service unavailable from a restricted location according to 'b. Eligibility' in https://www.binance.com/en/terms." Route failure recorded, route revised, not treated as task impossibility.
2. Bybit public REST (api.bybit.com v5 market kline, linear BTCUSDT). FAILED from this host. Exact response: "The Amazon CloudFront distribution is configured to block access from your country."
3. Kraken public REST OHLC, interval 240: WORKS for all seven spot pairs. Pairs used: XBTUSD (BTC), ETHUSD, XDGUSD (DOGE; the DOGEUSD alias resolves to the same XDGUSD book), XRPUSD, ADAUSD, LINKUSD, SOLUSD. Kraken returns at most the last 720 bars per call, about 120 days at 4h, which covers the 180 bar warmup with room.
4. OKX public REST: WORKS. history-candles for BTC-USDT-SWAP at bar 4H gives the BTC perpetual price series; funding-rate-history for BTC-USDT-SWAP gives funding prints at the OKX native 8h interval. Pagination note: funding history paginates to older prints with the "after" parameter (verified live; the "before" parameter returns newer prints).

Capture job: capture.py in this folder, run hourly by cron job c1-watcher-cycle through run_cycle.sh. It polls both sources and merges idempotently into the store in this folder (one JSON file per series, keyed by timestamp). No API keys are used or needed.

## First verified records (read back from the store after capture)

Capture run at 2026-11-15T23:33Z to 23:37Z, store read back and checked:

1. Spot 4h, each of BTC, ETH, DOGE, XRP, ADA, LINK, SOL: 721 bars stored, 720 completed plus the current forming bar. First bar 2026-07-18T20:00:00Z, last (forming) bar 2026-11-15T20:00:00Z. Current window named partial: the 2026-11-15T20:00:00Z bar is still forming and is flagged complete=0 in the store; the watcher uses completed bars only.
2. BTC perpetual 4h (OKX BTC-USDT-SWAP): 400 bars stored, 399 completed plus the forming bar. First bar 2026-09-10T08:00:00Z, last (forming) bar 2026-11-15T20:00:00Z.
3. BTC perpetual funding (OKX BTC-USDT-SWAP): 292 prints stored. First print 2026-08-10T16:00:00Z, last print 2026-11-15T16:00:00Z. Cadence check on read-back: maximum gap between consecutive prints is 28800 seconds, exactly the 8h native interval, no gaps.
4. Price sanity on read-back: BTC spot last completed close and forming bar near 64,985 USD; BTC perpetual near 65,023 USD. Basis is small and sane. Funding last print rate 0.0000117815109256 (about 1.18bp per 8h), plausible magnitude.

## Inventory verdict against protocol needs

1. Spot 4h for all six assets plus BTC: CLOSED by the Kraken capture. Backfilled depth 720 completed bars per symbol, against a 180 bar warmup requirement.
2. BTC perpetual prices: CLOSED by the OKX capture. Backfilled depth 399 completed bars.
3. BTC perpetual funding prints: CLOSED by the OKX capture. Backfilled depth 292 prints at a clean 8h cadence, and the series is current.
4. Executable quotes (runfile 3.8): not captured by this watcher. Outcomes are graded on the 10bp cost model and flagged model_only, exactly as runfile 3.8 item 3 specifies.
5. Collateral and liquidation records (runfile 3.9 items 1 and 2): unobtainable by construction in a paper watcher with no margin account. Every outcome record names this explicitly; the mark path excursion and asset leg drawdown items are recorded from held bars.
