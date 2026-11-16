# C1 RUNFILE: Buy panic; hedge reassurance

Program: Six Constructions, Run 2, Cell C1
Registered: 2026-11-15 (America/New_York)
Typed spend: $0.00
Backtest run tonight: none. This file is a verdict record and a pre-registration only.

## 1. Cell verdict

STATUS: BLOCKED
Evidence pointer: filesystem verification in section 2 of this file, run on this estate on 2026-11-15.

Verdict line: C1 is BLOCKED. The claimed prototype cannot be audited, reproduced, or graded on this estate because its source artifacts are not here.

Exact unblocker: the alpha-invention-local folder landing on this estate, containing two_clocks.py, results.json, event_paths.json, and static_fraction_comparison.json, together with the parent event file at edge-audit/repos/master-desk/evidence/edge/2026-11-15/recovery/chaos_v2/CL-03226-detail.json landing on this estate. Both deliveries are required. Until they land, the claimed results stand as an unverified external claim: not reproduced, not adopted, and not treated as results of this program.

The claimed results, recorded as claim only: delayed hedge beat immediate hedge in all three partitions at the 72h endpoint; all incremental bootstrap intervals include zero; fifth-percentile outcomes were worse than the immediate hedge; 12 policies were explored adaptively, with 4 inverse policies added after viewing the first results; there was no untouched holdout; the events were inherited from an earlier broad search; the cost model charged 10bp per one-way turnover on both legs with archived perpetual funding. None of these numbers was verified tonight and none may be cited as a finding.

## 2. Filesystem verification of absence

Commands run 2026-11-15 on this machine, outputs recorded verbatim in substance:

1. ls /workspace/alpha-invention-local/ returned: No such file or directory (exit 2).
2. ls ~/workspace/alpha-invention-local/ (that is, /home/hatch/workspace/alpha-invention-local/) returned: No such file or directory (exit 2).
3. ls on each cited file returned No such file or directory for every one:
   /workspace/alpha-invention-local/two_clocks.py
   /workspace/alpha-invention-local/results.json
   /workspace/alpha-invention-local/event_paths.json
   /workspace/alpha-invention-local/static_fraction_comparison.json
4. ls on the parent event file returned No such file or directory at every candidate root:
   edge-audit/repos/master-desk/evidence/edge/2026-11-15/recovery/chaos_v2/CL-03226-detail.json (relative)
   /workspace/edge-audit/repos/master-desk/evidence/edge/2026-11-15/recovery/chaos_v2/CL-03226-detail.json
   ~/workspace/edge-audit/repos/master-desk/evidence/edge/2026-11-15/recovery/chaos_v2/CL-03226-detail.json
5. A find over ~/workspace for any name matching alpha-invention returned no paths.
6. A find over ~/workspace for any name matching CL-03226 returned no paths.

Conclusion: absence is proven for the cited paths on this estate. This is a route result about artifact location, not a claim that the prototype never existed elsewhere.

## 3. Fresh-data protocol: pre-registration

This protocol is frozen at registration. Any change after the first qualifying forward event is a new trial and is charged to the ledger in section 5.

### 3.1 Universe

Spot assets: ETH, DOGE, LINK, XRP, ADA, SOL. Reference asset: BTC. Bar frame: 4h, completed bars only. An asset enters the forward sample only when its feed rows in section 4 are satisfied; assets without a feed are recorded as not yet live, never backfilled silently.

### 3.2 Event definition (frozen)

For each asset, on each completed 4h bar t:

1. Beta: lagged 180-bar beta of asset returns on BTC returns, estimated on the 180 completed 4h bars ending at bar t minus 1. No bar at or after t enters the estimate.
2. Residual at bar t: asset return at t minus beta times BTC return at t.
3. Residual score: (residual at t minus the lagged 180-bar mean of residuals) divided by the lagged 180-bar RMS of residuals, with mean and RMS computed on the same lagged 180-bar window ending at t minus 1.
4. Shock condition: residual score below -3.
5. Source family magnitude condition: absolute BTC move at bar t at least 1.5 times the lagged 180-bar RMS of BTC returns, same lagged window.
6. Direction filter retained from the local experiment: the BTC bar at t is negative.
7. An event fires only when conditions 4, 5, and 6 all hold on the same completed bar.

### 3.3 Treatment policy: signal-delayed hedge (frozen)

1. Entry: buy the asset at the open of bar t plus 1, initially unhedged.
2. Hedge trigger: after entry, watch completed BTC 4h bars. When two consecutive completed BTC bars following entry are both positive, add the BTC perpetual hedge at the open of the next bar. The hedge is added once only. If the trigger never fires before the endpoint, the position stays unhedged to exit.
3. Hedge sizing: short BTC perpetual units fixed at entry time from the entry price and the lagged beta of section 3.2: hedge notional equals beta times asset position notional at entry, converted to BTC units at the BTC price at entry. Units are fixed at entry even though execution may happen later, and are never rebalanced.
4. Exit: close the asset leg and the hedge leg (if open) at the fixed endpoint, at the endpoint bar open. Two endpoints are registered: 24h after entry (6 bars of 4h) and 72h after entry (18 bars of 4h). The 72h endpoint is primary, matching the claimed partition where the effect was asserted. The 24h endpoint is secondary and reported, never substituted.

### 3.4 Reference policy

Immediate hedge: identical entry, with the full beta-sized BTC perpetual hedge of section 3.3 item 3 opened at the same open as the asset entry, held fixed, and closed at the same endpoint. This is the policy the timing claim must beat.

### 3.5 The four comparators (frozen)

Comparator A, no hedge: identical asset entry and exit, no BTC leg at any time. Purpose: measures whether any hedge helps at all on these events.

Comparator B, fixed half hedge: at the entry open, short 0.5 times the beta-sized BTC perpetual hedge of section 3.3 item 3, units fixed, no additions, closed at the endpoint. Purpose: a simple static partial hedge with no timing logic.

Comparator C, fixed-time delayed hedge: the full beta-sized hedge is added at the first bar open at or after entry time plus 24h, regardless of BTC bar signs, once only, units fixed from entry as in section 3.3 item 3, closed at the endpoint. At the 24h endpoint this comparator adds and closes at the same bar and is reported as degenerate there; its decisive partition is 72h. Purpose: separates clock delay alone from signal-conditioned delay.

Comparator D, pre-specified random activation clock: at entry, an activation bar is drawn for each event by this exact rule: compute SHA256 of the string C1R2 plus the asset symbol plus the event bar timestamp in ISO UTC form, take the first 8 bytes as an unsigned integer, divide by 2 to the power 64 to get u in [0, 1), and set the activation delay in bars to 1 plus floor(u times the number of bars from entry to the endpoint). The full beta-sized hedge is added at the open of that bar, once only, units fixed from entry. If the drawn bar is the endpoint bar itself, the hedge is added and closed at that open and contributes only cost, which is the honest cost of a random clock. Purpose: if a random clock matches the signal clock, the two-positive-bars signal carries no timing information.

All policies share the same events, entries, endpoints, sizing basis, and cost model. Exposure comparability for grading is defined in section 6.

### 3.6 Cost model

Starting model: 10bp per one-way turnover on both legs (asset spot leg and BTC perpetual leg), charged on every open and every close, including a hedge that is added and closed at the same bar. Replacement rule: where an executable quote (a firm bid and ask with timestamp at or before the decision bar open, from the venue of record) is held for a leg at a decision timestamp, the quote half-spread plus the venue fee schedule replaces the 10bp figure for that leg and that event, and the substitution is logged per event. Model-charged and quote-charged results are reported side by side; the quote-charged partition governs the verdict where it exists.

### 3.7 Funding data requirements

1. The BTC perpetual funding prints covering every hour (or the venue native funding interval) of every holding window must be held before an event is graded. Funding paid or received by the short hedge is applied at the printed rates on the fixed hedge units.
2. Archived funding from the claimed prototype is not usable: it is part of the missing artifacts.
3. An event with any missing funding print inside its holding window is recorded as ungradable for the hedged policies, never zero-filled.
4. Funding source of record must be named per event (venue print or named history provider), with the retrieval timestamp logged.

### 3.8 Executable quote requirements

1. For each decision timestamp (entry, hedge addition, exit) the protocol requires, where obtainable: best bid, best ask, and quoted size for the asset spot pair and for the BTC perpetual, from the venue the desk actually routes to.
2. Quotes are captured forward from registration. Historical quote reconstruction is not permitted for the forward sample.
3. Where no quote is held, the event is graded on the cost model of section 3.6 and flagged model-only.

### 3.9 Collateral and liquidation observation requirements

For every hedged event, the forward log must record:

1. Margin mode and collateral posted for the BTC perpetual leg, in quote currency, at hedge open.
2. The liquidation price of the hedge at open, and the maintenance margin rate applied.
3. The mark price path of the BTC perpetual at bar granularity across the holding window, including the worst intrabar adverse excursion against the short hedge.
4. The closest approach of mark to liquidation price, as a percentage of the gap at open.
5. A liquidation outcome flag: if the mark crosses the liquidation price at any intrabar point before the endpoint, the event outcome is the liquidation outcome at the crossing bar, with the asset leg closed at that bar open of the next bar, and the event is never silently carried to the endpoint as if the hedge survived.
6. The asset leg maximum drawdown inside the window, recorded alongside, so a hedge that survives while the asset leg collapses is visible in the record.

No event is graded for any hedged policy without items 1 to 5 present or explicitly marked unobtainable with the reason named.

### 3.10 Forward start definition

1. Registration time: 2026-11-15, America/New_York. The forward sample consists only of events whose signal bar t completes strictly after this runfile is saved.
2. Events are detected on the crypto complex the desk already feeds (section 4), on completed 4h bars only, in real time or on the first snapshot after completion. No event whose signal bar completed before registration counts, and no historical bar is admitted retroactively.
3. Primary grading partition: pooled events across live assets at the 72h endpoint. Per-asset partitions are secondary.
4. First grading checkpoint: after 20 qualifying pooled events at 72h, or 6 months after the first live asset feed is complete, whichever comes later. The falsifier of section 6 is evaluated at that checkpoint and at every 20 further events.
5. Overlapping events on the same asset are permitted and recorded with their overlap; no deduplication rule is applied after the fact.

## 4. Held feed sources on this estate, and named data rows

Verified by inspection on 2026-11-15.

### 4.1 Held: spot bars

Source: ~/workspace/muse-desk-v3/state/warm_bars.json, produced by the desk warm layer (~/workspace/muse-desk-v3/desk3/warm.py, CRYPTO_FETCHES, Alpaca crypto bars), refreshed on the desk cycle.

Coverage found in the retained file:
1. ADA/USD 4Hour: 546 bars, 2026-08-17T00:00:00Z to 2026-11-15T20:00:00Z. Native 4h, satisfies the ADA spot leg.
2. LINK/USD 4Hour: 546 bars, 2026-08-17T00:00:00Z to 2026-11-15T20:00:00Z. Native 4h, satisfies the LINK spot leg.
3. ADA/USD 1Hour: 743 bars, 2026-10-16T00:00:00Z to 2026-11-15T22:00:00Z.
4. SOL/USD 15Min: 2970 bars, 2026-10-16T00:00:00Z to 2026-11-15T22:15:00Z. Finer than 4h; a 4h series would need a registered aggregation. The desk resampler at ~/workspace/muse-desk-v3/desk3/crypto_bars.py aggregates complete UTC buckets from a 1Hour tape; a 15Min aggregation rule is not yet registered.
5. BTC/USD 1Day: 501 bars, 2025-07-03T00:00:00Z to 2026-11-15T00:00:00Z (also served as BTC-USD). Daily only.
6. ETH/USD 1Day: 501 bars, same span as BTC daily. Daily only.
7. DOGE/USD and XRP/USD: no series held at any frame.

Also held but not sufficient for this cell: ~/workspace/research_notes/decisions-api-leverage-20261114/conversion/cv2_btc_bars.json, daily BTC closes beginning 2023-12-01. Daily closes cannot serve a 4h beta, residual, or bar-sign rule.

Warm layer fetch configuration (desk3/warm.py): ADA/USD 1Hour 30 days, ADA/USD 4Hour 90 days, LINK/USD 4Hour 90 days, BTC/USD 1Day 500 days, ETH/USD 1Day 500 days, SOL/USD 15Min 30 days. Note: a 180-bar 4h beta window is 30 days, so the 90-day 4h fetches hold roughly 540 bars and cover the window with room; the window requirement is satisfiable for ADA and LINK from the live fetch shape.

### 4.2 Held: perpetual bars, basis, quotes, funding (ADA and LINK only)

Source: desk snapshots at ~/workspace/muse-desk-v3/state/snapshots/ (latest inspected 2026-11-15), produced by KrakenProducer in ~/workspace/muse-desk-v3/desk3/producers3.py.

Coverage found:
1. PF_ADAUSD 4Hour bars: 2000 bars, 2025-12-17T16:00:00+00:00 to 2026-11-15T20:00:00+00:00 (also a 240Min key).
2. PF_LINKUSD 4Hour bars: 2000 bars, same span (also a 240Min key).
3. kraken.basis, kraken.quote, and kraken.funding keys present for the ADA and LINK basis sleeves.
4. Funding history file: ~/workspace/muse-desk-v3/state/kraken_funding.json: PF_ADAUSD 519 hourly prints, 2026-10-25T01:00:00+00:00 to 2026-11-15T22:00:00+00:00; PF_LINKUSD 519 hourly prints, same span. The producer also merges Coinalyze funding history (Binance symbols mapped to Kraken perps, 90-day window) for ADA and LINK only.

These are asset perps, not the BTC hedge instrument. They prove the desk has a working Kraken perpetual feed shape, but they do not satisfy the BTC hedge leg.

### 4.3 Named data rows (not held; each is an open row, not a silent gap)

DATA ROW C1-DATA-01, BTC perpetual feed: no BTC perpetual series is held anywhere found on this estate: no PF_XBTUSD or equivalent BTC perp bars, no BTC perp executable quotes, no BTC perp funding prints. This is the hedge instrument of the construction. Without it, no hedged policy can be priced forward. Owner: desk feed work. Status: OPEN.

DATA ROW C1-DATA-02, BTC spot 4Hour bars: only BTC/USD daily bars are held (section 4.1 item 5). The event rule needs BTC 4h returns for the 180-bar beta, the residual, the magnitude condition, and the two consecutive positive BTC bars trigger. A BTC/USD 4Hour fetch in the warm layer (90 days, mirroring LINK) would close this row. Status: OPEN.

DATA ROW C1-DATA-03, ETH spot 4Hour bars: only ETH/USD daily bars are held. ETH cannot enter the forward sample until a 4Hour fetch exists. Status: OPEN.

DATA ROW C1-DATA-04, DOGE and XRP spot 4Hour bars: no series held at any frame. Both assets stay out of the forward sample until fetched. Status: OPEN.

DATA ROW C1-DATA-05, SOL 4Hour aggregation rule: SOL is held at 15Min only. A registered complete-bucket aggregation from 15Min to 4h, or a native SOL/USD 4Hour fetch, is required before SOL events can fire. Status: OPEN.

Consequence for the forward start: at registration, zero of the six claimed assets can complete the full rule forward, because the BTC legs (DATA ROW C1-DATA-01 and C1-DATA-02) are missing for every asset. ADA and LINK are closest: their spot 4h legs are live today. The forward clock of section 3.10 starts per asset when its rows close, and the checkpoint rule counts from the first asset fully live.

## 5. Trial ledger for C1

1. INHERITED trials: 12 policies explored in the claimed prototype, recorded here as inherited and unverified. Composition as claimed: 8 policies in the first exploration, plus 4 inverse policies added adaptively after viewing the first results. The events behind them were inherited from an earlier broad search and there was no untouched holdout. These 12 trials count against the C1 family trial budget in any future deflated grading, and their results are not evidence on this estate.
2. Tonight: 1 trial charged, this pre-registration of the fresh-data protocol (treatment, reference, and comparators A to D as one registered design).
3. Running charged total for the C1 family: 13 trials (12 inherited unverified plus 1 registered tonight).
4. Any protocol change after the first forward event, any added comparator, and any endpoint change is a further trial and must be appended to this ledger with its date and reason before use.

## 6. Falsifier

The delayed-hedge timing claim is: conditioning the hedge start on two consecutive positive BTC bars adds value over simply hedging, beyond what delay alone or partial hedging explains.

The claim is killed on fresh data if, at a grading checkpoint of section 3.10, any one of the following holds at the 72h endpoint, net of the governing cost treatment of section 3.6 and with funding applied per section 3.7:

1. Simple comparator match: Comparator B (fixed half hedge), Comparator C (fixed-time delayed hedge), or Comparator D (random activation clock) matches or beats the signal-delayed treatment on mean net outcome, at comparable exposure, where comparable exposure means the comparator average absolute BTC hedge notional across the holding window is within 10 percent of the treatment figure, or the comparator achieves its match with strictly less exposure. A match is a difference whose bootstrap interval includes zero or favors the comparator.
2. Reference failure: the signal-delayed treatment fails to beat the immediate hedge reference on mean net outcome on the fresh sample. The claimed edge was defined against immediate hedging; failing that comparison forward ends the claim regardless of the other comparators.
3. Tail failure with no compensating mean: the treatment fifth-percentile outcome is worse than the immediate hedge fifth percentile (the same weakness the claimed prototype reported) while its mean net advantage over immediate is zero or negative. A worse tail bought with no mean is a kill, not a tradeoff.

Survival requires all three tests passed at the same checkpoint: the treatment beats immediate, beats or separates from every simple comparator at comparable exposure, and does not pair a worse fifth percentile with a non-positive mean edge. Anything less, and C1 is recorded as falsified on fresh data and closed, with the checkpoint evidence filed in this program home.

## 7. What was not done tonight

1. No backtest was run. No claimed number was recomputed, reproduced, or estimated from memory.
2. No feed was built. The data rows of section 4.3 are named and left open for desk feed work; building them was outside this cell.
3. No file outside this runfile was modified.

STATUS: BLOCKED. Evidence pointer: section 2 of this file (filesystem absence) and section 4 (feed inspection of ~/workspace/muse-desk-v3/state/warm_bars.json, ~/workspace/muse-desk-v3/state/snapshots/, and ~/workspace/muse-desk-v3/state/kraken_funding.json).

## 8. Route 2 (amendment, 2026-11-15): estate-wide inventory and reconstruction decision

STATUS for Route 2: BLOCKED. A faithful reconstruction is not possible on held data.
Evidence pointer: the inventory in section 8.1 of this file, verified on this estate on 2026-11-15.
Typed spend: $0.00.

### 8.1 Estate-wide inventory (wider than the desk-state scope of section 4)

Search scope and method: the whole ~/workspace tree was walked by filename for data files (10,804 files matched the broad pattern covering btc, xbt, bitcoin, eth, doge, xrp, ada, link, sol, funding, warm_bars, ohlc, and bars), and every plausible candidate was inspected individually. Content scans covered the desk state (muse-desk-v3 state, snapshots, and cache), the morgue caches, personal-quant, research_notes/alpha-hunt-chaos-20261115, research_notes/decisions-api-leverage-20261114, and the jarvis workflow probe and test caches. Large files were scanned in chunks or with grep and were never loaded whole into memory.

Held, by source:

A. Spot 4h bars for C1 assets.
1. ~/workspace/muse-desk-v3/state/warm_bars.json: ADA/USD 4Hour, 546 bars, 2026-08-17T00:00:00Z to 2026-11-15T20:00:00Z. LINK/USD 4Hour, 546 bars, same span. (Same as section 4.1; a duplicate copy sits in research_notes/decisions-api-leverage-20261114/keepgoing2/wave6/desk-copy/state/warm_bars.json, and warm_bars_extended.json in keepgoing2 holds the same crypto section plus a LINK/USD 1Day series. No new series in either copy.)
2. Kraken spot 240 minute raw probe files in ~/workspace/.jarvis/workflow-runs/workflow-run-4eb44660ffae4f6a83dded3d0ee2aafc/work/probe/: ohlc_ADAUSD_240.json, ADAUSD spot, 721 bars, 2026-06-26T12:00:00+00:00 to 2026-10-24T12:00:00+00:00; ohlc_LINKUSD_240.json, LINKUSD spot, 721 bars, same span. These duplicate the ADA and LINK spot legs from a second print; they add no new asset and no BTC leg.
3. SOL: no native 4h series anywhere. Held only as SOL/USD 15Min in warm_bars.json, 2970 bars, 2026-10-16T00:00:00Z to 2026-11-15T22:15:00Z. Aggregating 15Min to 4h would give about 185 bars total, which barely covers the 180 bar warmup alone with no room for events plus endpoints, and the aggregation is unregistered; flagged, not used.
4. ENJ 4h exists (research_notes/alpha-hunt-chaos-20261115/pass2/work/kg6/enj_bars_4h.json, ENJ spot 4h, 720 bars, 2026-07-18T16:00:00+00:00 to 2026-11-15T12:00:00+00:00), but ENJ is not one of the six C1 assets. Recorded only because it shows a 4h crypto fetch pattern exists elsewhere on the estate.

B. BTC bars, and the other assets.
1. BTC spot 4h bars: NOT HELD anywhere found. No file, key, or series at 4h, 240 minute, or any other intraday frame for BTC spot exists in any searched store.
2. BTC spot daily only, in every place it appears: warm_bars.json BTC/USD 1Day, 501 bars, 2025-07-03 to 2026-11-15; research_notes/decisions-api-leverage-20261114/abyss/crypto_bars.json BTC/USD, 2145 daily bars, 2021-01-01 to 2026-11-15; abyss/coinbase_daily.json BTC/USD, 3241 daily bars, 2018-01-01 to 2026-11-15; abyss/kraken_daily.json BTC/USD, 721 daily bars, 2024-11-25 to 2026-11-15; conversion/cv2_btc_bars.json, daily closes beginning 2023-12-01; research_notes/alpha-hunt-chaos-20261115/pass2/work/unblock1/fetched/BTC_USD.json, 76 daily bars, 2026-09-01 to 2026-11-15; jarvis coinbase test caches, BTC-USD 1Day.jsonl only. Daily bars cannot serve a 4h beta, residual, magnitude filter, or two-positive-bars trigger.
3. ETH spot: daily only, in the same files as item B2 (501, 2145, 3241, and 721 daily bars respectively). No ETH 4h anywhere.
4. DOGE and XRP: no series at any frame in any searched store.
5. Morgue large caches: ~/workspace/morgue/data_cache/deep_bars.json (about 1.15 GB, daily equity board panel; chunk grep found no BTC/USD 4Hour key, no PF_XBTUSD, and no BTCUSDT; its one "BTC" key is a daily equity panel series beginning 2021-04-16 at prices near 500 dollars, which is not the crypto asset) and ~/workspace/morgue/data_cache/board_bt_bars.json (no crypto 4h keys). personal-quant holds reports and audits only, no bar data for the six assets.

C. BTC perpetual, the hedge instrument.
1. BTC perpetual bars: NOT HELD. No PF_XBTUSD, PI_XBTUSD, or equivalent BTC perpetual OHLC series was found in any searched store.
2. Closest held items, neither usable as a bar series: futures_instruments.json in the jarvis probe folder named in item A2 lists PF_XBTUSD and PI_XBTUSD instrument metadata only, with no price history; futures_tickers.json in the same folder holds one PF_XBTUSD ticker snapshot at 2026-10-24T15:25:16Z carrying a single fundingRate value at that instant. One snapshot is not a price series and not a funding history.
3. Asset perpetuals held, wrong instrument for this hedge leg: PF_ADAUSD 4Hour and PF_LINKUSD 4Hour (desk snapshots, 2000 bars each, per section 4.2; desk cache at ~/workspace/muse-desk-v3/cache/bars/PF_ADAUSD/4Hour.jsonl and PF_LINKUSD/4Hour.jsonl, 2049 bars each, first 2025-11-25T20:00:00+00:00, last 2026-11-02T04:00:00+00:00; jarvis probe charts_PF_ADAUSD_4h.json and charts_PF_LINKUSD_4h.json, 2000 candles each, 2025-11-25 to 2026-10-24). Substituting an asset perpetual for the BTC perpetual would change the construction; flagged as a deviation and not used.

D. Funding.
1. BTC perpetual funding history: NOT HELD. No BTC, XBT, or BTCUSDT funding series was found in any searched store.
2. Held funding, all for other instruments: ~/workspace/muse-desk-v3/state/kraken_funding.json, PF_ADAUSD and PF_LINKUSD, 519 hourly prints each, 2026-10-25T01:00:00+00:00 to 2026-11-15T22:00:00+00:00; ~/workspace/muse-desk-v3/state/coinalyze_funding_history.json, ADAUSDT, ENJUSDT, and LINKUSDT, 2022 hourly prints each, 2026-08-23T16:00:00+00:00 to 2026-11-15T21:00:00+00:00; research_notes/alpha-hunt-chaos-20261115/pass2/vein2_work/ OKX funding files for ADA and LINK, 292 prints each, plus ENJ funding files in pass2/work/kg6/. None of these prices the BTC hedge leg.

### 8.2 Decision: no faithful rebuild, on any subset

The frozen rule needs, per asset, spot 4h bars AND BTC 4h bars over a common window with at least 180 warmup bars, plus BTC perpetual prices and BTC perpetual funding for the hedged policies. BTC 4h bars, BTC perpetual bars, and BTC perpetual funding history are each entirely absent from this estate. Therefore not even the ADA and LINK subset, whose spot 4h legs are held, can produce a single faithful event (the beta, residual, magnitude filter, and hedge trigger all run on BTC 4h returns) or a single hedged policy price. No reconstruction code was written and no reconstruction was run. Building one against a proxy would grade a different construction, not this rule, and would not be a replication attempt of the specified rule.

Proxies considered and rejected as deviations, none used quietly or otherwise:
1. BTC daily bars in place of BTC 4h bars: changes the frame of every estimated quantity in the rule.
2. ADA or LINK perpetual prices or funding in place of the BTC perpetual leg: changes the hedge instrument.
3. The single PF_XBTUSD ticker snapshot in place of a perpetual bar series and funding history: one instant, no series.
4. Aggregating SOL 15Min bars to 4h for the SOL leg: unregistered aggregation, about 185 bars against a 180 bar warmup, and moot while the BTC legs are missing.

### 8.3 Route 2 verdict, agreement statement, and trial charge

Verdict: BLOCKED. The Route 2 unblocker is data, named exactly: (1) BTC spot 4Hour bars covering a common window with the asset spot 4h bars, with at least 180 warmup bars before the first graded event; (2) BTC perpetual 4Hour bars (PF_XBTUSD or the venue equivalent) over the same window; (3) BTC perpetual funding prints covering every holding window in that sample. Route 1 remains the open unblocker for the claimed source artifacts themselves, already recorded in section 1; Route 2 does not close it and does not replace it.

Agreement statement: there are no reconstruction numbers to agree or disagree with the claimed table (for example the claimed 72h delayed hedge means of 2.169 / 2.362 / 3.539 percent, and the claimed 24h delayed means of 3.587 / 1.922 / 2.595 percent). The claimed results therefore stand on this estate exactly as they stood after Route 1: an unverified external claim, not reproduced, not contradicted, and not graded, because no faithful local sample exists to grade them against.

Trial charge for Route 2: 0 reconstruction trials. Basis: no reconstruction was run and no policy comparison was computed, so there is nothing to charge as a reconstruction trial; the inventory and this verdict are not backtest trials. The C1 ledger total in section 5 is unchanged at 13 trials (12 inherited unverified plus 1 registered pre-registration), separate from any future reconstruction trials. If the data named above lands and a reconstruction is run later, that run and each policy comparison it reports will be charged at that time as reconstruction trials, labeled as such and kept separate from the 12 inherited trials.

STATUS: BLOCKED. Evidence pointer: section 8.1 of this file (estate-wide inventory, 2026-11-15) and section 8.2 (subset decision).

## 9. Addendum, 2026-11-15 (audit landing; registered text above is untouched)

Route 1 UNBLOCKED and CLOSED: Astra's six-constructions package landed Sun 2026-11-15 (repo dwj9ddyvf6-hub/cos2-estate, branch research/six-constructions-20261115, head c2cba0d433823c56cdb3b9680f69c58365a35ab2; mirrored copy in dwj9ddyvf6-hub/master-desk, head 3bc102f26abc0bda30da0e547c4c25e626f09514, content-identical 88 of 88). The audit of the landed artifacts is complete: verdict REPRODUCED. His code on his archived inputs produces his claimed table (18 of 18 cells at 3 decimals, event counts 44/59/37, 27,513 of 27,513 recorded values matched, exactly in the pinned environment). Full record: ~/workspace/research_notes/astra-six-constructions-20261115/ASTRA-SIX-AUDIT-2026-11-15.md.

Route 2 (reconstruction): RETIRED AS MOOT, because the audit reproduced. The data rows C1-DATA-01 to C1-DATA-05 remain open in their forward-protocol role only (section 3.10 per-asset start), not as audit blockers.

The fresh-data protocol of section 3 remains the forward test, frozen as registered. The claimed result's standing is unchanged: exploratory, adaptive, intervals including zero, no untouched holdout. The audit graded the artifact's fidelity, not the strategy.
