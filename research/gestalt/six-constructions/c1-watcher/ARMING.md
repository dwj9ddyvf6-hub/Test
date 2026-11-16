# C1 Watcher Arming Record, 2026-11-15

Workstream W7. Typed spend: $0.00. Paper logging only.

## Verdict: ARMED

STATUS: GREEN for arming. Evidence pointer: state.json, last_capture.json, the store files, and the cron read-back named below, all in this folder, all produced and read back on 2026-11-15 after the last code change.

## Per-series status at arming

1. Spot 4h BTC (Kraken XBTUSD): 720 completed bars, current. LIVE.
2. Spot 4h ETH (Kraken ETHUSD): 720 completed bars, current. LIVE.
3. Spot 4h DOGE (Kraken XDGUSD): 720 completed bars, current. LIVE.
4. Spot 4h XRP (Kraken XRPUSD): 720 completed bars, current. LIVE.
5. Spot 4h ADA (Kraken ADAUSD): 720 completed bars, current. LIVE.
6. Spot 4h LINK (Kraken LINKUSD): 720 completed bars, current. LIVE.
7. Spot 4h SOL (Kraken SOLUSD): 720 completed bars, current. LIVE.
8. BTC perpetual 4h (OKX BTC-USDT-SWAP): 399 completed bars, current. LIVE.
9. BTC perpetual funding (OKX BTC-USDT-SWAP, 8h prints): 292 prints, maximum gap 28800 seconds, last print 2026-11-15T16:00:00Z. LIVE.

## Warmup

The 180 bar warmup is satisfied from backfill on day one for every asset: 720 completed bars per symbol against a 180 bar requirement. Warmup completion date: 2026-11-15 (the arming date). Backfilled history is used for warmup estimation only. Per runfile 3.10, no backfilled bar can produce a forward event: the watcher armed at 2026-11-15T23:35:40Z (state.json, armed_at), and only signal bars completing strictly after that timestamp are scanned. The first forward-eligible signal bar is the bar starting 2026-11-15T20:00:00Z, completing 2026-11-16T00:00:00Z.

## Watcher behavior (watcher.py, frozen spec of C1-RUNFILE.md section 3)

1. Event detection exactly per runfile 3.2: lagged 180 bar beta on 4h bar returns (close over open, the source family definition), residual score normalized by the lagged 180 bar residual mean and RMS, score below -3, absolute BTC move at least 1.5 times the lagged 180 bar RMS of BTC returns, BTC signal bar negative.
2. Entry unhedged at the next bar open. Treatment hedge: full entry-fixed beta-sized BTC perpetual hedge added at the next open after two consecutive completed positive BTC bars, once only.
3. Policies tracked at the fixed 24h (6 bar) and 72h (18 bar) endpoints: treatment signal-delayed, reference immediate hedge, comparator A no hedge, comparator B fixed half hedge, comparator C fixed-time delayed hedge, comparator D random activation clock (exact SHA256 rule of runfile 3.5 D). The task brief named the first four comparators; C and D are also implemented because the frozen runfile registers them, so the watcher covers the full registered design.
4. Costs at 10bp per one-way turnover on both legs, outcomes flagged model_only (no executable quotes held, per runfile 3.8 item 3). Funding applied at OKX printed rates on the fixed hedge units; a hedged outcome with a funding gap inside its window is recorded ungradable, never zero-filled (runfile 3.7 item 3).
5. Ledger: ledger.jsonl in this folder, append-only. At arming it holds 0 events and 0 outcomes. Zero is a count, not a failure: no forward bar has completed since arming yet.

## Self-test evidence (not forward evidence)

Before arming, the detection and outcome code was run once against the backfilled history in a throwaway script that wrote nothing to the ledger. It found 9 historical qualifying bars across the six assets (ETH 4, LINK 2, DOGE 1, ADA 1, SOL 1, XRP 0) and computed sane 24h and 72h outcomes for all six policies where perp and funding coverage existed. These historical bars are warmup self-test only and are not admitted to the forward sample.

## Cron wiring

Cron job id: c1-watcher-cycle. Schedule: interval 1h, timezone America/New_York, enabled. Read back after creation and verified: body runs run_cycle.sh in this folder, then reads back state.json and the ledger tail. First scheduled run: Sun 2026-11-15 19:36:15 EST. The full cycle was also run once by hand at 2026-11-15T23:37:33Z and exited clean (cycle ok line in the run output, capture.log and watcher.log in this folder).

## Named open rows (handled as the protocol specifies, not silent)

1. Executable quotes (runfile 3.8): not held. Outcomes are model_only until a quote capture exists. This does not block arming; the protocol names this exact handling.
2. Collateral and liquidation price (runfile 3.9 items 1 and 2): unobtainable in a paper watcher with no margin account; named as unobtainable in every outcome record.
3. Venue note: the hedge instrument of record for the forward sample is the OKX BTC-USDT-SWAP perpetual (prices and funding), and spot legs are Kraken USD pairs. Both sources are named per event and per outcome in the ledger records. The desk Kraken PF_XBTUSD feed was not used because this estate holds no such series (see FEED-INVENTORY.md); Kraken futures chart history was not offered by the public endpoint tested (404 on the v3 charts path), while OKX offered full public history for both prices and funding.

## Files

1. capture.py: public keyless capture (Kraken spot, OKX perp and funding).
2. watcher.py: event detection, policy tracking, outcome maturation.
3. run_cycle.sh: capture plus watcher, one cycle.
4. store/: spot_BTC.json, spot_ETH.json, spot_DOGE.json, spot_XRP.json, spot_ADA.json, spot_LINK.json, spot_SOL.json, perp_BTC.json, funding_BTC.json.
5. ledger.jsonl: append-only event and outcome ledger (0 rows at arming).
6. state.json: watcher state, armed_at, scan cursor, per-asset status.
7. last_capture.json, capture.log, watcher.log: capture and run evidence.
8. FEED-INVENTORY.md: feed inventory and capture cure record.
