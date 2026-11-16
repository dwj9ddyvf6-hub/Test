# KG-11: THE SHARED PARAMETER NAMESPACE

Built from Pass 2 Lane C's parameter maps (339 sleeves, 10,447 extracted constants, 1,175 distinct names). Pattern rules placed names first; the 81 names no rule could honestly claim went to a Luna 6 bulk classification (81 choice questions, $0.0031); every mapping in NAMESPACE-MAP.json prints its basis, and names below the 0.35 seat-confidence floor are UNMAPPED, never forced.

## 1. COVERAGE CENSUS

| measure | before (same-name only) | after (namespace roles) |
|---|---|---|
| constants in a cross-sleeve class | 9,905 of 10,447 (94.8%) | 10,383 of 10,447 (99.4%) |
| distinct names in a cross-sleeve class | 636 of 1,175 (54.1%) | 1,163 of 1,175 (99.0%) |
| distinct cross-sleeve classes available to a hunt | 636 exact names | 31 roles |

Singleton rescue: 539 names are carried by exactly one sleeve and could never form a class under same-name matching; 534 of them (537 constants) now sit inside a shared role. UNMAPPED: 12 names, 64 constants (0.6% of all constants), each printed in NAMESPACE-MAP.json with the reason it was not placed.

The honest reading of the before column: at instance level the old world already reached 94.8%, because config boilerplate (cadence_s, session, capital_usd, the costs.* block) repeats verbatim in all 339 sleeves. What starved KG-1 was the strategy-bearing tail: 539 names lived on exactly one sleeve, and per-role carrier counts ran 3 to 21 because the same role wore dozens of unrelated names (STOP_FRAC, STOP_PCT, SPECS.stop_pct, DON_STOP_ATR, call.stop). The namespace collapses those into one class per role, below.

## 2. ROLE TABLE

| role | member names | constants | carrier sleeves | definition |
|---|---|---|---|---|
| COSTS | 14 | 1,776 | 339 | Fees, commissions, slippage and basis cost assumptions. |
| PLUMBING | 112 | 1,186 | 277 | Runtime state slots, context objects, computed intermediates. |
| STRUCTURE | 44 | 809 | 339 | Options structure, exit-rule kinds, side/intent maps, geometry. |
| IDENTIFIER | 85 | 746 | 281 | Experiment ids, account/bookkeeping identifiers, hashes, files. |
| SIZE_NOTIONAL | 60 | 646 | 339 | Capital, budget, notional amounts and sizing fractions/caps. |
| POLICY | 53 | 600 | 122 | Declared policy, ruling and decision records. |
| UNIVERSE | 200 | 590 | 143 | Symbol lists, bands, sector maps, traded-symbol declarations. |
| INPUTS | 56 | 569 | 78 | Named data-feed input lists. |
| FAMILY | 17 | 483 | 127 | Strategy family labels. |
| CADENCE | 10 | 403 | 339 | Evaluation or rebalance intervals. |
| RISK | 11 | 394 | 339 | Per-trade risk fractions and buying-power buffers. |
| SESSION | 3 | 366 | 339 | Session mode declarations. |
| THRESHOLD | 119 | 230 | 96 | Signal/gate thresholds, score cuts, spread and price gates. |
| HOLD | 49 | 229 | 144 | Intended holding period, horizon, or time-based exit. |
| FILTERS | 9 | 189 | 74 | Named signal-filter stack entries. |
| STALENESS | 28 | 150 | 105 | Maximum age / freshness limits for bars, quotes, signals. |
| GATE_FLAG | 37 | 140 | 40 | Boolean switches enabling or disabling gates/behaviours. |
| LOOKBACK | 46 | 129 | 68 | Indicator computation periods (MA/RSI/ATR/MACD/channel/beta). |
| MAXPOS | 16 | 127 | 115 | Caps on position/entry counts, slots, sector counts. |
| TIMEFRAME | 21 | 112 | 69 | Bar size / timeframe declarations. |
| STOP | 20 | 97 | 92 | Per-trade stop-loss distance or magnitude. |
| DTE | 19 | 74 | 33 | Options days-to-expiry bounds or targets. |
| WARMUP | 14 | 73 | 54 | Minimum history required before a sleeve trades. |
| WINDOW | 24 | 67 | 58 | Spans in bars/sessions over which signals or events are counted. |
| CALENDAR | 30 | 48 | 8 | Event-calendar dates and earnings/FOMC day counts. |
| ENTRY_WINDOW | 14 | 43 | 30 | Session-clock entry/exit boundaries (hours, cutoffs, seconds). |
| STRIKE_SELECTION | 11 | 37 | 22 | Delta / moneyness / OTM strike-choice parameters. |
| TARGET | 17 | 28 | 23 | Fixed profit-taking level, fraction, or R multiple. |
| WEIGHT | 11 | 24 | 18 | Portfolio weight values and floors. |
| LOSS_LIMIT | 7 | 12 | 11 | Daily or portfolio loss caps. |
| TRAILING | 6 | 6 | 5 | Trailing-stop and giveback protection parameters. |
| UNMAPPED | 12 | 64 | n/a | no rule claimed them and the seat placed none above the floor |

## 3. THE RE-RUN DIVIDEND: KG-1 ORDER-1 SINGLES ON ROLE CLASSES

Population and machinery identical to KG-1: the 21 graded sleeves with a fwd5 outcome, sleeve-level means, permutation null (4,000 draws), BH deflation inside the order-1 family, verdicts LEAD (q<=0.10) / NOMINAL (p<=0.05) / NULL. Role representatives follow KG-1's first-match discipline over the namespace's (much wider) member sets, with per-role plausible ranges printed in kg11_finalize.py. THRESHOLD, TRAILING and STRIKE_SELECTION are not value-tested: their members mix incommensurable units (VIX points, scores, ATR multiples, deltas), so a median split would be arithmetic on unlike quantities; they enter the namespace as classes for pairs/triples work, not as singles. SIZE_NOTIONAL splits into SIZE_USD and SIZE_FRAC, mirroring KG-1's CAPITAL vs NOTIONAL split.

Medians and carrier counts on the 21-sleeve population:

| feature | carriers | median |
|---|---|---|
| STOP | 5 | 0.08 |
| TARGET | 3 | 0.05 |
| HOLD | 9 | 5.0 |
| LOOKBACK | 8 | 20.0 |
| WINDOW | 1 | 5.0 |
| SIZE_USD | 21 | 10000.0 |
| SIZE_FRAC | 11 | 0.3 |
| RISK | 21 | 0.02 |
| LOSS_LIMIT | 0 | None |
| MAXPOS | 8 | 8.0 |
| DTE | 2 | 14.0 |
| CADENCE | 21 | 300.0 |
| WEIGHT | 2 | 1.0 |
| ENTRY_WINDOW | 0 | None |
| STALENESS | 2 | 3600.0 |

### fwd5 excess vs QQQ (primary): 19 singles tested, 1 LEAD, 1 NOMINAL, 17 NULL

| feature=class | n in | mean in | mean out | diff bp | p | q | verdict |
|---|---|---|---|---|---|---|---|
| FAMILY=Fires and singles | 7 | 828.4 | -183.8 | 1012.2 | 0.0005 | 0.0095 | LEAD |
| FAMILY=Spec-built | 5 | -408.1 | 329.2 | -737.3 | 0.0117 | 0.1116 | NOMINAL |
| FAMILY=Aster | 7 | -155.0 | 307.9 | -462.9 | 0.0952 | 0.6031 | NULL |
| STOP=LOW | 4 | 39.8 | 180.4 | -140.5 | 0.6728 | 0.9085 | NULL |
| STOP=ABSENT | 16 | 145.1 | 180.8 | -35.7 | 0.9085 | 0.9085 | NULL |
| TARGET=LOW | 3 | 202.1 | 145.5 | 56.6 | 0.9035 | 0.9085 | NULL |
| TARGET=ABSENT | 18 | 145.5 | 202.1 | -56.6 | 0.8958 | 0.9085 | NULL |
| HOLD=LOW | 5 | -68.8 | 223.1 | -291.9 | 0.3512 | 0.9085 | NULL |
| HOLD=HIGH | 4 | 490.7 | 74.3 | 416.4 | 0.2362 | 0.9085 | NULL |
| HOLD=ABSENT | 12 | 133.9 | 179.9 | -46.0 | 0.8568 | 0.9085 | NULL |
| LOOKBACK=LOW | 5 | 376.2 | 84.1 | 292.1 | 0.3509 | 0.9085 | NULL |
| LOOKBACK=HIGH | 3 | -67.9 | 190.6 | -258.5 | 0.5391 | 0.9085 | NULL |
| LOOKBACK=ABSENT | 13 | 119.2 | 209.6 | -90.5 | 0.7486 | 0.9085 | NULL |
| SIZE_FRAC=LOW | 6 | 338.9 | 79.5 | 259.4 | 0.3777 | 0.9085 | NULL |
| SIZE_FRAC=HIGH | 5 | 119.5 | 164.3 | -44.8 | 0.8803 | 0.9085 | NULL |
| SIZE_FRAC=ABSENT | 10 | 59.5 | 239.2 | -179.7 | 0.4904 | 0.9085 | NULL |
| MAXPOS=LOW | 5 | 180.8 | 145.1 | 35.7 | 0.9043 | 0.9085 | NULL |
| MAXPOS=HIGH | 3 | 406.0 | 111.6 | 294.5 | 0.4791 | 0.9085 | NULL |
| MAXPOS=ABSENT | 13 | 84.9 | 265.3 | -180.4 | 0.5211 | 0.9085 | NULL |

Below floor (counted, not tested): 30 cells: STOP=HIGH (n=1), TARGET=HIGH (n=0), WINDOW=LOW (n=1), WINDOW=HIGH (n=0), WINDOW=ABSENT (n=20), SIZE_USD=LOW (n=20), SIZE_USD=HIGH (n=1), SIZE_USD=ABSENT (n=0), RISK=LOW (n=21), RISK=HIGH (n=0), RISK=ABSENT (n=0), LOSS_LIMIT=LOW (n=0), LOSS_LIMIT=HIGH (n=0), LOSS_LIMIT=ABSENT (n=21), DTE=LOW (n=2), DTE=HIGH (n=0), DTE=ABSENT (n=19), CADENCE=LOW (n=19), CADENCE=HIGH (n=2), CADENCE=ABSENT (n=0), WEIGHT=LOW (n=2), WEIGHT=HIGH (n=0), WEIGHT=ABSENT (n=19), ENTRY_WINDOW=LOW (n=0), ENTRY_WINDOW=HIGH (n=0), ENTRY_WINDOW=ABSENT (n=21), STALENESS=LOW (n=2), STALENESS=HIGH (n=0), STALENESS=ABSENT (n=19), FAMILY=Lazarus/Q07/MN (n=2)

### fwd5 raw (secondary): 19 singles tested, 1 LEAD, 0 NOMINAL, 18 NULL

| feature=class | n in | mean in | mean out | diff bp | p | q | verdict |
|---|---|---|---|---|---|---|---|
| FAMILY=Fires and singles | 7 | 337.2 | -242.4 | 579.6 | 0.0015 | 0.0285 | LEAD |
| LOOKBACK=HIGH | 3 | -466.2 | 20.3 | -486.5 | 0.0862 | 0.8152 | NULL |
| FAMILY=Spec-built | 5 | -313.3 | 33.3 | -346.7 | 0.1287 | 0.8152 | NULL |
| STOP=LOW | 4 | -151.4 | -25.2 | -126.2 | 0.6536 | 0.9615 | NULL |
| STOP=ABSENT | 16 | -42.1 | -71.9 | 29.8 | 0.9208 | 0.9615 | NULL |
| TARGET=LOW | 3 | -139.0 | -34.2 | -104.8 | 0.7196 | 0.9615 | NULL |
| TARGET=ABSENT | 18 | -34.2 | -139.0 | 104.8 | 0.7183 | 0.9615 | NULL |
| HOLD=LOW | 5 | -189.3 | -5.4 | -183.8 | 0.4776 | 0.9615 | NULL |
| HOLD=HIGH | 4 | -117.6 | -33.1 | -84.5 | 0.7613 | 0.9615 | NULL |
| HOLD=ABSENT | 12 | 32.0 | -157.4 | 189.4 | 0.3837 | 0.9615 | NULL |
| LOOKBACK=LOW | 5 | -28.0 | -55.8 | 27.9 | 0.9175 | 0.9615 | NULL |
| LOOKBACK=ABSENT | 13 | 38.9 | -192.3 | 231.2 | 0.2932 | 0.9615 | NULL |
| SIZE_FRAC=LOW | 6 | -154.1 | -7.2 | -146.9 | 0.5594 | 0.9615 | NULL |
| SIZE_FRAC=HIGH | 5 | 67.1 | -85.5 | 152.6 | 0.5666 | 0.9615 | NULL |
| SIZE_FRAC=ABSENT | 10 | -44.4 | -53.6 | 9.2 | 0.9615 | 0.9615 | NULL |
| MAXPOS=LOW | 5 | -71.9 | -42.1 | -29.8 | 0.9135 | 0.9615 | NULL |
| MAXPOS=HIGH | 3 | -238.9 | -17.6 | -221.3 | 0.4564 | 0.9615 | NULL |
| MAXPOS=ABSENT | 13 | 3.3 | -134.5 | 137.8 | 0.5486 | 0.9615 | NULL |
| FAMILY=Aster | 7 | -231.4 | 41.9 | -273.3 | 0.2037 | 0.9615 | NULL |

Below floor (counted, not tested): 30 cells: STOP=HIGH (n=1), TARGET=HIGH (n=0), WINDOW=LOW (n=1), WINDOW=HIGH (n=0), WINDOW=ABSENT (n=20), SIZE_USD=LOW (n=20), SIZE_USD=HIGH (n=1), SIZE_USD=ABSENT (n=0), RISK=LOW (n=21), RISK=HIGH (n=0), RISK=ABSENT (n=0), LOSS_LIMIT=LOW (n=0), LOSS_LIMIT=HIGH (n=0), LOSS_LIMIT=ABSENT (n=21), DTE=LOW (n=2), DTE=HIGH (n=0), DTE=ABSENT (n=19), CADENCE=LOW (n=19), CADENCE=HIGH (n=2), CADENCE=ABSENT (n=0), WEIGHT=LOW (n=2), WEIGHT=HIGH (n=0), WEIGHT=ABSENT (n=19), ENTRY_WINDOW=LOW (n=0), ENTRY_WINDOW=HIGH (n=0), ENTRY_WINDOW=ABSENT (n=21), STALENESS=LOW (n=2), STALENESS=HIGH (n=0), STALENESS=ABSENT (n=19), FAMILY=Lazarus/Q07/MN (n=2)

### The dividend, stated plainly

No role single reaches LEAD on the primary outcome. The namespace widens every role's carrier set (STOP goes from KG-1's narrow pattern to the full member set; HOLD, LOOKBACK and WINDOW likewise), and the singles verdict does not move: at order 1, on 21 sleeves, sleeve outcomes still separate by family and not by any single parameter role, however the role is measured. That is a stronger null than KG-1's, because it survives the wider, semantically complete classes instead of nine hand-mined patterns.

Testability on this population, printed rather than smoothed: of the 49 order-1 singles enumerated (15 role features x 3 classes + 4 family cells; the two aster_tensor sleeves carry family Aster in Lane C's register, so no Tensor family cell exists on this population), 19 met the >=3-in/>=3-out floor on 21 sleeves (16 of them role cells). Several roles have 0-2 carriers among the 21 graded sleeves (LOSS_LIMIT 0, ENTRY_WINDOW 0, WINDOW 1, DTE 2, WEIGHT 2, STALENESS 2, TARGET 3) and contribute only below-floor cells; the role null below is a null over the roles this population can carry, and the carrier table above names exactly which.

Control check: the FAMILY singles in this re-run use the identical machinery and reproduce KG-1's order-1 family diffs to the tenth of a bp (FAMILY=Aster: diff -462.9bp, q 0.6031, NULL; FAMILY=Fires and singles: diff 1012.2bp, q 0.0095, LEAD; FAMILY=Spec-built: diff -737.3bp, q 0.1116, NOMINAL). The Fires verdict is identical (LEAD). One bookkeeping difference, printed rather than smoothed: Spec-built's q moves from KG-1's 0.0999 (LEAD) to 0.1116 (NOMINAL) because the BH family here is this run's 19 tested singles, not KG-1's order-1 set; the underlying diff (-737.3bp) and raw p are the same object. So the role nulls above are read on a machine that demonstrably still finds the separations KG-1 found. KG-1's own order-1 parameter singles were NULL on both outcomes for all nine of its features; the comparison is printed in kg11_rerun.json beside this run's full cell table.

## 4. LIMITS

- The re-run population is the same 21 sleeves KG-1 had; the namespace cannot manufacture outcomes, and most role classes still split a 21-sleeve population. The dividend of the namespace is structural (complete classes for pairs/triples and for the enlarged population the unblock lanes are grading), not a new order-1 separation today.
- Role representatives are first-match in map order inside printed plausible ranges, KG-1's discipline; a sleeve with several unlike members in one role is represented by the first, which is a convention, printed here rather than hidden.
- Seat classifications carry their argmax probabilities in NAMESPACE-MAP.json; the seat classified names, it did not grade anything.

STATUS: GREEN for the build (namespace complete and proven on the final artifacts: every one of the 1,175 names is either role-placed with a printed basis or UNMAPPED with a printed reason; the re-run executed on the identical population and machinery as KG-1); the re-run's substantive verdict is printed in section 3 (no role single separates at order 1; the strengthened null is the finding).
