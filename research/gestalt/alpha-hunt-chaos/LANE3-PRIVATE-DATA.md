# ALPHA HUNT CHAOS LAB, LANE 3: MINE OUR OWN PRIVATE DATA

Owner order Sun 2026-11-15. Read-only inspection of the estate's own records: fills, near-miss logs, signal journals, the Ghost Book, the book ledger, desk sleeve journals, disagreement records, the pattern ledger. Every number below was computed by script from the files named, in this pass. Where the data cannot answer the hunt, the exact missing field is named.

## 0. Inventory: what private data actually exists

| Source | File | Size | Span |
|---|---|---|---|
| Desk sleeve journals | `~/workspace/muse-desk-v3/state/<sleeve>/journal.jsonl` (339 dirs) | 1,353,045 lines total | 2026-10-23 to 2026-11-15 |
| Dispatcher log | `~/workspace/muse-desk-v3/state/dispatcher.jsonl` | 11,976 lines | fills concentrated 2026-11-12 |
| Ghost Book | `~/workspace/midna-book/ghost-book-ledger.jsonl` | 21 rows | fires of 2026-11-11, priced 2026-11-13 |
| Book ledger | `~/workspace/midna-book/ledger.json` | 14 fills, 4 realised, 7 open positions | 2026-10-30 to 2026-11-13 |
| Pattern ledger | `~/workspace/midna-book/typed-layer/pattern_ledger.jsonl` | 35 rows | posed 2026-11-11 |
| Forecast Twin | `~/workspace/midna-book/FORECAST-TWIN-RECORDS.md` | 37 calls | posed 2026-11-12 |
| Bar cache (desk) | `~/workspace/muse-desk-v3/cache/bars/<SYM>/` | 1Day for 22 symbols (515 bars each, 2024-10-25 to 2026-11-13); 1Min for 51 symbol dirs, 21 with complete RTH sessions 2026-10-20 to 2026-11-13 | SPY has 1Hour only, stale after 2026-10-31 |

Journal event census (1,353,045 lines): eval 688,702; unfed 487,327 (36.0 percent of everything the fleet writes is a sleeve evaluating with no data feed); intent 71,495; adapter_eval 63,817; last_evaluation 19,660; the rest under 5,000 each.

Journal intent results (71,495): rejected 44,996 (62.9 percent), queued 11,789, filled 6,803 (9.5 percent), submitted 5,163, duplicate 2,744.

## (a) The near-miss portfolio: what almost fired

**The near-miss population is large and precisely counted. Its forward performance is not computable from the estate's own logs, for one named reason: rejection records do not carry symbol, side, or price.**

Dispatcher rejections (`dispatcher.jsonl`, event `intent_rejected`, n = 2,354), by reason:

- exit_satisfied_no_broker_position: 841 (exit-side housekeeping, not an entry near-miss)
- insufficient_slice_bp: 773 (the true economic near-miss: the sleeve wanted in, buying power said no)
- exit_satisfied_no_sleeve_position: 328
- reconcile_halt: 202
- exit_already_resting_at_broker: 186
- bad_qty 8, bad_kind 5, exit_blocked_opposite_side_resting 11

Broker-terminal rejections (n = 362): code 40310000 insufficient qty 196 (exit-side), code 42210000 position intent mismatch 166; sides: sell 304, buy 58.

The 773 insufficient_slice_bp blocks concentrate: 552 of 773 come from three investandbefree_dmac variants at exactly 184 each (mirrored sleeves re-emitting the same intent), then aster_etf_leader1_m150 (66), aster_etf_qqq_monthly_c098 (54), aster_etf_spy_monthly_c098 (53).

Forward-return test, run anyway on the only reject class that carries a symbol: broker-rejected BUYS with daily-bar coverage, n = 6 of 58. Forward 1-day mean minus 0.94 percent, median minus 0.94 percent, win rate 0 of 6. Sample of 6: no conclusion, reported because the test was run.

Ghost Book as near-miss record (`ghost-book-ledger.jsonl`): 21 Tensor fires priced, 0 resolved. Every fire names 28 never-traded consuming families; the selector priced alternatives per fire (verdicts: 11 BEST, 10 NO OPTIONS EDGE; r_to_target ranges minus 1.0 to 9.51, with the 4 known minus 1.0 rows). Resolution is blocked twice over: the resolver has not run, and only 1 of the 21 symbols (MU) has daily bars in the desk cache, so even a manual mark is impossible for 20 of 21 from estate data alone.

**Hypothesis H-A (testable, currently unmeasurable):** the insufficient_slice_bp blocked-entry portfolio, equal-weighted at each block's reference price, has a forward return different from the filled-entry portfolio. What fills the gap: add `symbol`, `side`, and `ref_price` to the dispatcher `intent_rejected` record and to the journal `intent` record at emission. Both records today carry only event, intent_id, reason/result, and sleeve. One logging change converts 773 historical-style blocks per period into a shadow portfolio.

## (b) Cross-sleeve conjunctions and lead-lag

**Finding B1: the fleet's apparent breadth is partly mechanical duplication.** Dozens of aster sleeves have byte-identical journal event counts (the c098/m150 pairs and fullcash/vol1pct pairs: e.g. aster_abs_neg_ada_fullcash and aster_abs_neg_ada_vol1pct both 3,993 lines with identical eval/unfed splits; aster_etf_qqq_monthly_c098 5,047 lines vs its m150 twin 5,018). Co-firing among mirror twins is the same signal counted twice, not independent confirmation. Any fleet breadth, dispersion, or conjunction statistic computed on the raw 339 overstates independent agreement. The deduplicated family count was not computed in this pass; the identical-count pairs visible in the census number in the dozens.

**Finding B2: true multi-sleeve conjunctions are nearly absent from the fill record.** Dispatcher fills (`dispatcher.jsonl`): 849 buy_to_open fills form only 39 (day, symbol) groups; exactly 1 group has 2 or more distinct sleeves buying the same symbol the same day: 2026-11-12, SPY, bought by bta_onebar_basket, aster_etf_leader1_m150, and aster_etf_spy_monthly_c098 (all index sleeves, so this is basket overlap, not discovery). Caveat that governs the whole fill record: 1,090 of 1,125 fills are dated 2026-11-12 and 1,078 carry imported = true; the dispatcher fill history is effectively one session deep (the virtual-book dual-read import), so conjunction absence may be a record-depth artifact, not fleet behavior.

**Lead-lag: not computable.** Journal intent records carry no symbol for most sleeves (only the BTC sleeves suffix the symbol into the intent_id, e.g. aster_native_btc_eth_sma200-...-BTC-USD). A lead-lag matrix needs (sleeve, symbol, timestamp) triples; the journals provide (sleeve, timestamp, result) only. What fills the gap: the same logging change as H-A (symbol on intent records), after which the 71,495-row intent history becomes a conjunction and lead-lag corpus retroactively only if the field is added going forward; the existing history stays symbol-less.

## (c) Our own fills as signal

**Book level (`ledger.json`): the resolved sample is 4 trades, 4 losses.** SHOP minus $863.20, MO minus $838.48, ELF minus $251.43, NVDA minus $507.02; total realised minus $2,460.13, win rate 0 of 4. Equity path: $100,000 (2026-10-30) to $97,301.52 (2026-11-13). Four trades decide nothing statistically; they are reported because they are the entire resolved book sample and nobody had summed them in one place outside the weekly review.

**Desk level (`dispatcher.jsonl`):** buy_to_open fills on daily-bar-covered symbols, n = 95 of 849 (most fills are on symbols outside the 22-symbol daily cache). Forward 1-day return from fill-date close: mean minus 0.71 percent, median minus 0.68 percent, win rate 0 of 95. This looks damning and is not: the fills are one session (2026-11-12) marked to the next session (2026-11-13, a down day for the basket), so the number measures one day's tape, not a fleet effect. Forward 5-day is not computable (bars end 2026-11-13).

**Fleet intensity vs the market:** total journal intents per day vs next-day QQQ close return, n = 15 days (2026-10-23 to 2026-11-12): correlation 0.046, slope plus 0.038 percent per additional 1,000 intents. No relation. The intent stream is dominated by rejection noise (10,662 rejections on 2026-11-12 alone), so raw intensity is a machine-health gauge, not positioning.

Verdict for (c): on current records there is no evidence the fleet's aggregate positioning predicts anything, and the records are too shallow (one dispatcher session, four book trades) for the null to mean much either. The forward test that would settle it: dispatcher fills accrue from Mon 2026-11-16 under the new session; re-run this exact script at 20 live sessions.

## (d) Decompositions: time of day, day of week, session segments

**Session-segment decomposition of the 1Min cache** (21 symbols with complete RTH sessions, 14 sessions each, 294 symbol-sessions, 2026-10-20 to 2026-11-13; segments in ET):

| Segment | n | Mean | Median | Win rate |
|---|---|---|---|---|
| Overnight (prev close to open) | 294 | +15.6 bp | +1.7 bp | 50% |
| Open drive (09:30 to 10:30) | 294 | +11.7 bp | +11.2 bp | 53% |
| Midday (10:30 to 15:00) | 294 | minus 28.9 bp | minus 17.1 bp | 43% |
| Close hour (15:00 to 16:00) | 294 | minus 7.8 bp | minus 8.0 bp | 47% |
| Full intraday (open to close) | 294 | minus 24.8 bp | minus 1.6 bp | 50% |

The shape rhymes with the Focus-names overnight find on an independent universe (these are large caps, not the Focus 30): overnight and the open drive carried the positive expectancy in this window; midday was the drag. Honest caveat: the window itself was intraday-weak (full intraday mean minus 24.8 bp), so segment means inherit the window's drift; the claim worth testing is the ordering, not the levels.

Per-symbol overnight means (n = 14 each): MSFT +192.1 bp and AMZN +158.1 bp are earnings-gap contaminated (both reported in the window) and should be excluded from any structural read; then MU +70.6, AVGO +63.7, LLY +48.2, CRWD +47.7, JPM +46.4, TSLA +45.1 bp at the top; NVDA minus 100.8 and CAT minus 108.4 bp at the bottom. QQQ itself: overnight +5.2 bp, open drive +9.1 bp, close hour minus 7.7 bp.

**The fleet's own clock is a machine clock, not a market clock.** Journal intents by ET hour run 2,014 to 5,996 in every hour of the day, peaking at 12:00 ET (5,996) with no RTH concentration (crypto and replay cycles evaluate around the clock). By weekday: Thu 16,053 and Wed 15,315 of 71,495 (44 percent on two days, driven by the Nov 11-12 rejection spikes), weekends 14,736 (replay plus crypto). Dispatcher fills by ET hour are an artifact, not behavior: 721 of 1,125 at 09 ET is the Nov 12 import burst.

**Hypothesis H-D (testable from Monday):** entries timestamped in the midday segment underperform open-drive entries on the same sleeves. The book's new shadow logs (D1, G1 forward log) carry timestamps from Mon 2026-11-16; grade entries by segment at the first 20 resolved shadow fires per family. Falsifier: midday entries match or beat open-drive entries on mean net R at that sample.

## (e) Disagreement magnitude vs forward outcome

**The disagreement data exists; the outcome half has never been graded. Resolved pairs available for this test today: zero.**

- Ghost Book votes (`ghost-book-ledger.jsonl`): the bull/bear vote field has almost no variance to test with. 17 of 21 fires sit at bull 6 / bear 1; the other 4 at 7 / 0. A near-constant cannot predict anything, and with 0 of 21 fires resolved there is no outcome column anyway.
- Pattern ledger (`pattern_ledger.jsonl`, 35 rows): the typed seat's form classification matches the recorded truth form on 32 of 35 (91.4 percent). But continuation_5 resolutions are pending on 35 of 35 rows and continuation_10 on 35 of 35. The seat's probability output (continuation_5 mean 0.265, range 0.11 to 0.45) has never been scored against a single outcome.
- Forecast Twin (`FORECAST-TWIN-RECORDS.md`): 37 calls posed 2026-11-12 with twin probabilities and the owner's joined-after stances recorded; the file's own header says resolutions are all pending and names the resolver (`resolve_forecast_twin.py`, grades mechanically from SIP closes after each horizon). The horizons have passed; the resolver has not been run.
- Dead drop and Crosswalk corpora: narrative posts only; no structured (disagreement size, resolved outcome) pairs exist in either corpus.

What fills the gap, in order: (1) run the named forecast-twin resolver and the pattern-ledger continuation grading; both grade mechanically from closes that already exist, converting 72 posed predictions into the estate's first resolved disagreement sample; (2) log vote dispersion per Ghost Book fire (the full vote distribution, not the modal 6/1 split) so the field carries variance; (3) only then does the T7 test (disagreement buckets vs outcome monotonicity) have an input.

## What is missing, collected in one place

1. Symbol, side, and reference price on dispatcher `intent_rejected` records and journal `intent` records. This single gap blocks the near-miss portfolio (a), conjunction and lead-lag history (b), and any per-symbol fleet positioning test (c).
2. Resolutions: Ghost Book 0 of 21, pattern ledger 0 of 70 continuation checks, Forecast Twin 0 of 37. The estate poses predictions and prices fires; it does not yet grade them. The resolvers exist by name; they have not run.
3. Price coverage for resolution: the desk bar cache holds daily bars for 22 symbols and complete 1Min for 21, while the fleet trades 33 symbols in the dispatcher record alone and the Ghost Book fires on 21 names of which 20 have no cached bars. A resolver cannot mark what the cache cannot price.
4. Dispatcher fill depth: 97 percent of fills are one imported session (2026-11-12). Every fill-based statistic in this report is one session deep until live sessions accrue from Mon 2026-11-16.
5. SPY daily bars: absent from the cache (1Hour only, stale after 2026-10-31). QQQ daily carried the market-proxy load in this pass.

## Numbers that survive scrutiny, restated

- 487,327 of 1,353,045 journal lines (36.0 percent) are `unfed` evaluations: over a third of fleet activity is sleeves evaluating without data. Source: census of `~/workspace/muse-desk-v3/state/*/journal.jsonl`.
- 44,996 of 71,495 journal intents (62.9 percent) end rejected; 6,803 (9.5 percent) end filled. Same source.
- 773 dispatcher entry blocks for insufficient slice buying power, 552 of them from three mirrored dmac variants. Source: `dispatcher.jsonl`.
- Midday was the only persistently negative session segment across 294 symbol-sessions (mean minus 28.9 bp, win 43 percent) while overnight (+15.6 bp) and open drive (+11.7 bp) were positive. Source: `cache/bars/*/1Min.jsonl`, 2026-10-20 to 2026-11-13.
- The book's entire resolved sample is 4 trades, all losses, minus $2,460.13. Source: `~/workspace/midna-book/ledger.json`.
- 72 posed typed-layer predictions (35 pattern rows x 2 horizons is 70 checks, plus 37 twin calls) stand at 0 resolved. Sources: `pattern_ledger.jsonl`, `FORECAST-TWIN-RECORDS.md`.

STATUS: PARTIAL. Hunts (d) and the censuses inside (a), (b), (c), (e) are proven on the final files with the numbers above; the forward-performance cores of (a), (b), (c), and (e) are BLOCKED on named missing fields and unrun resolvers, each with its filler named. Evidence pointers: `~/workspace/muse-desk-v3/state/dispatcher.jsonl`; `~/workspace/muse-desk-v3/state/*/journal.jsonl` (339 files, 1,353,045 lines); `~/workspace/muse-desk-v3/cache/bars/` (1Day 22 symbols, 1Min 21 complete-session symbols); `~/workspace/midna-book/ghost-book-ledger.jsonl`; `~/workspace/midna-book/ledger.json`; `~/workspace/midna-book/typed-layer/pattern_ledger.jsonl`; `~/workspace/midna-book/FORECAST-TWIN-RECORDS.md`. Scripts run in this pass: census, dispatcher fill/reject mining, journal intent mining, session-segment decomposition (kept in the lane's scratch, reproducible from the files named).
