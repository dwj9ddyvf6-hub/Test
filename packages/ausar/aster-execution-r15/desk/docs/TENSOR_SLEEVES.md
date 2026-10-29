# Four Tensor paper sleeves: rules and operations

The owner authorized making the Tensor research executable and requested **all four sleeves**. The desk implements them as separate deterministic **local paper** books: **H1STATE**, **WSTATE**, **D20PV**, and **D20TENSOR**. Each book has its own capital, positions, reservations, opportunity state, T+1 spendable cash, execution receipts, and performance. Data may be shared; cash and candidate rankings are not combined. These sleeves submit no orders to Alpaca or any live broker.

This document describes the implemented operational contract. New source, parity, accounting, runtime, CLI, and API receipts identify their exact reviewed versions. Earlier desk audit receipts apply to their original pinned code. Installation, enabling, native-data readiness, current provider connectivity, and an actual observed fill are separate states.

**The desk completed autonomous local-paper entries in the actual 15:30–15:35 UTC window on 2026-10-09.** The complete 1,820-name hourly census reached the unchanged 99% known-coverage gate at **15:34:39.484966 UTC**, 20.515034 seconds before the unchanged deadline: 1,796 ready, six verified ineligible and 18 individually blocked failures. Ten of 65 ranked opportunities filled through normal local-paper execution; 55 were denied by the ten-slot limit. The independent actual-execution audit passed **262 checks**, and the consistent operating-state archive is verified. All four independently funded sleeves remain enabled. This demonstrates the hourly entry pipeline; completed 20-bar exits, daily/weekly opening execution, profitability and QQQ outperformance remain unproved. Earlier misses and failed/cutoff rehearsals are preserved.

The immutable first full hourly census was recorded at **15:33:10.387094 UTC**, 190.387094 seconds after opening, but its 20 failed names were below the required known fraction. A later 19-failure census still could not admit entries. Fair recovery reached 18 failures and 99.010989% known coverage at **15:34:39.484966**; the ten fills occurred at **15:34:39.671126–15:34:39.721320 UTC**. No gate or deadline was relaxed. H1STATE retained $1,228.68 paper cash and zero fixed fees after those entries. The independent audit verified ownership, all higher-ranked selections/exclusions, actual causal quotes, configured adverse slippage, whole-share/cash/liquidity/NAV limits, cumulative debits, immutable source prefixes, native numerical replay and action evidence. Its numeric replay reproduces the frozen rule operands; the original as-of-dependent engine input hash cannot be reconstructed exactly because that snapshot clock was not stored with candidates. That explicit audit limitation does not become a claim of exact original-input-hash replay.

The recorded **main pre-start installation** contains all four enabled local books at $100,000 each, with 5,448 original enrolled seed members (462,015,177 bytes) hash-verified. Repeating installation preserved the same identities and funding. Its pre-start status has zero positions/pending intents, zero native current-cycle coverage, and `worker_alive=false`. The subsequent activation receipt observed `runtime_running=true` and `worker_alive=true` at **13:16:05 UTC on 2026-10-09**, at `http://127.0.0.1:8787`. Current native censuses were warming; a timely complete current opening census or an actual forward fill is not claimed by that receipt.

## Start and inspect

Run from the project directory with the installed Python environment. A fresh application/database remains empty. Restore the pinned research seed before installation, then select an explicit deployment database:

```bash
export ASTER_DB_PATH="$PWD/data/tensor-paper-r12.sqlite"
export ASTER_ACTIONS_CREDENTIALS_FILE=/path/to/private/alpaca-readonly.json
.venv/bin/python -m backend.tensor_cli install --seed-directory data/research-seed-r11/native-inputs --enable
.venv/bin/python -m backend.tensor_cli status
.venv/bin/python -m backend.tensor_cli run
./run.sh
```

Before expecting action-covered entries and payments, configure the required read-only corporate-action access in a private local JSON file containing `key` and `secret` strings, and point `ASTER_ACTIONS_CREDENTIALS_FILE` to it. Keep that environment for the resident process. The adapter reads metadata through GET requests; Tensor sleeves never submit Alpaca orders. Keep credentials outside the source, research archive and exported operating state. Missing or unresolved action evidence can block affected entries and comparable performance.

`install` verifies every enrolled unquarantined/nonbenchmark seed group, the frozen model exports, and the engine source manifest before preparing four dedicated books with **$100,000 of virtual principal each**, or $400,000 total virtual funding. Fixed funding client IDs make repeated installation idempotent. `--enable` enables entry evaluation; omitting it leaves new installations disabled. A later repeated installation preserves the installation's bound configuration rather than silently undoing an operator pause. Use the enablement API to resume entries.

The global `--db PATH` option belongs **before** the subcommand. Without it, the CLI uses `ASTER_DB_PATH`, then `data/aster.sqlite`. Default seed directory is `data/research-seed-r11/native-inputs`. The named CLI uses the full source-bound enrollment files: **1,820 hourly names, 1,815 daily names, and 1,813 weekly names**, with the daily enrollment shared as observations by its two independent books. These membership counts include names that may currently fail readiness/eligibility. The final CLI receipt identifies the actual chosen database, frozen enrollment files, book IDs, and enabled flags.

`status` reports current enablement, enrolled-universe coverage, native cycle status, independent cash, pending orders, and owned holdings. Readiness distinguishes full-census completion, valid coverage, verified ineligible names, unavailable names, and whether the configured coverage policy permits healthy entries. The strategy catalogue supplies the latest decision/denial receipts. CLI `run` executes **one explicit fenced supervisor cycle**, with a force flag internal to that operator command; it can perform that requested cycle while globally paused. It does not start a background daemon. The resident service maintains the durable `tensor-strategies` operations schedule when its process and global runtime are running; the configured schedule has a one-second interval. Each run is bounded and may complete only part of data acquisition. A one-second schedule is not a promise that thousands of histories can be downloaded and processed in one second.

Run `./run.sh` for the resident API and interface using the same configured database. Stopping that service stops automatic work. Pausing only a sleeve's entries preserves its owed exits; stopping the process or globally pausing the runtime stops automatic execution until it resumes. Do not delete the database to pause trading.

## API contract

The service exposes schemas through `/docs`:

| Route | Meaning |
|---|---|
| `GET /api/strategies` | Installed sleeves; a fresh database returns an empty list |
| `GET /api/strategies/catalogue` | Available frozen definitions plus installation/readiness/decision snapshot |
| `POST /api/strategies/install` | Explicitly install one sleeve in an already prepared independent local book |
| `POST /api/strategies/run` | Queue the fenced strategy schedule; it does not imply a synchronous fill |
| `PATCH /api/strategies/{installation_id}` | Supply only `{"enabled": true}` or `{"enabled": false}` |

Installation binds `sleeve`, `book_id`, an installation `id`, fixed `symbols` or a shipped `universe_file`, and a configuration hash. Low-level installation defaults to `enabled=false`. The same identity cannot silently bind a different configuration or another book. Accepted sleeve aliases include `H1_STATE_REPAIR`, `W_STATE_REPAIR`, `D20_PV`, and `D20_TENSOR`; receipts use canonical IDs.

Provider/model/data failures leave an explicit blocked state. `POST /api/strategies/run` queues work under the resident runtime's fence; a globally stopped runtime does not become running solely because a cycle was requested. Disabling entries does not liquidate the book, forget its cooldown, erase settlement obligations, or cancel an owed time exit.

## Frozen trading rules

| Sleeve | Selection | Priority at a common entry clock | Hold |
|---|---|---|---|
| H1STATE | Seven-channel native repair over three completed hourly transitions | Repair score, then symbol | 20 observed hourly bars |
| WSTATE | Same repair predicate over completed weekly transitions | Repair score, then symbol | 20 observed weekly bars |
| D20PV | Frozen original daily price/volume forecast meets its saved threshold | Predicted net-QQQ excess, then symbol | 20 observed daily bars |
| D20TENSOR | Frozen original daily price/volume + Tensor forecast meets its saved threshold | Predicted net-QQQ excess, then symbol | 20 observed daily bars |

All sleeves exclude `SPY`, `QQQ`, `B`, and `GOLD`. SPY/QQQ are benchmarks; B/GOLD remain archived-identity quarantines. No historical top-winner list becomes a current buy list. Each installation freezes its actual enrolled universe. Reduced enrollment, unavailable symbols, and unsuccessful history initialization remain visible; a subset cannot inherit full-roster research performance.

Common current-bar eligibility is at least **234 observed completed rows** (`bar_index >= 233`), price at least $5, finite positive native ATR14, and at least $1 million mean **native-bar** dollar volume over current and previous 19 rows. This mean is `close * volume`, not a replacement daily volume statistic for hourly or weekly bars. Completion must precede or equal actual usability, and usability must be no later than the decision. Daily models also require native feature readiness and their canonical source anchor. Weekly history needs roughly four and a half years before the 234-row requirement can pass.

### H1STATE and WSTATE

The fixed vote channels are `stoch`, `aroon`, `di`, `obv`, `squeeze`, `pivot`, and `wave`. Published bullish is +1, bearish is −1, and absent is null. Define `B(i) = bullish_votes(i) - bearish_votes(i)`.

Require:

1. Seven votes available at `i` and `i-3`.
2. `B(i) - B(i-3) >= 2`.
3. At least two **distinct** channels have any numeric increase in one of the three adjacent transitions `i-3→i-2`, `i-2→i-1`, or `i-1→i`.

A null operand makes that comparison false. Each channel counts once. Intermediate rows need not have seven votes. A channel can increase and later reverse; the rule does not substitute two endpoint bearish-to-bullish flips. No green, cyan, Swing, breakout, or positive-final-balance requirement is added.

The score is:

```text
repair + 0.01 * current_balance
       + 0.001 * clip(native_OBV_slope5 / current_volume, -10, 10)
```

The missing/zero-volume ratio contributes zero for ranking. Rank descending score, then ascending symbol. Greedily accept at most one signal per symbol per 20 observed row indices. A signal at `i` makes the next allowable origin `i+20`. Advance this opportunity cooldown even if funding, capacity, or entry enablement later denies the order. Bootstrap historical signals initialize state; they do not authorize current late orders.

### D20PV and D20TENSOR

The original saved model thresholds are inclusive:

- D20PV: `prediction >= 0.006985566706545021`.
- D20TENSOR: `prediction >= 0.006122960477423353`.

Prediction is a **return fraction of modeled net stock return minus gross QQQ return**, not a win probability or guaranteed gain. The threshold is the original training-prediction 95th percentile. It does not select the top 5% of today's securities and is not recalculated from current data.

Daily origins occur only when:

```text
bar_index % 20 == int(full_SHA256(symbol_UTF8).hexdigest(), 16) % 20
```

Use the full 256-bit digest and the original canonical index from zero. A fresh rolling 234-row window cannot silently reset this phase or indicator ages. Canonical history must start at the bound per-symbol R11 source timestamp. Once a forward history reaches the original archived endpoint, that endpoint must also occupy its original row ordinal; preserving only the first timestamp is insufficient if middle rows were dropped or reindexed. The endpoint/count check does not certify bitwise equality of every provider-revised OHLCV value; revision provenance stays explicit.

D20PV preserves its six ordered price features. D20TENSOR adds the original 29 ordered Tensor transforms, for 35 total. Saved training medians, tree nodes, feature order, and model hashes remain fixed. Native-ready missing votes become model-neutral zero; this is distinct from state repair's seven-vote endpoint requirement. Runtime uses verified portable numerical tree exports and performs no unpickling, fit, calibration, or threshold search. Source identity, feature shape, history anchor, or export failures block inference.

No future 20-bar maturity, later return, eventual close, or benchmark label is required to admit today's origin. Retain unselected scores and missing-next-open origins. The two daily books rank independently by their own frozen prediction; neither uses the repair score or the other book's selections.

## Container deployment

The supplied container packaging includes Node 22 and the frozen `strategies/` assets in its Python/Bookworm runtime. Compose stores the database and external seed in the private `desk-state` volume mounted at `/data`. Restore and verify the exact seed from the host or an authenticated external restoration step, then provision it into `/data/research-seed-r11/native-inputs` before installation and use that explicit path. The host CLI default points into the application directory. The image does not ship `gh` or GitHub authentication; presence of the restorer script is not evidence of authenticated in-container restoration. Optional GET-only action credentials belong at `/data/alpaca-readonly-credentials.json`, or the container path supplied by `ASTER_CONTAINER_ACTIONS_CREDENTIALS_FILE`. Credentials are external data, not part of the image or research archive. Missing optional action reads keep unsupported payments unresolved.

```bash
docker compose build desk
docker compose run --rm desk python -m backend.tensor_cli install --seed-directory /data/research-seed-r11/native-inputs --enable
docker compose up -d desk
```

The full image build in this workspace was deliberately stopped at the filesystem reserve to preserve space for the resident desk. The separate **offline thin-container runtime check passed at 15:17:43 UTC**, bound to repaired runtime `27c3b260` and provider `9bbff46e`, with Python 3.12.15 and Node 22.23.3. It matched all 93 native columns in three frame fixtures, confirmed full/fast operand parity, verified frozen assets/anchors and matched 32 daily prediction probes. It performed no market requests, installation, funding, financial trials or broker orders. This bounded check assembled the actual Node binary, built UI and read-only sources/assets in an existing Python container. Its empty CLI status had zero installed sleeves and no live worker. It does not certify a completed full-image build, authenticated seed restoration or persistent mounted-volume installation.

## Surgical selection, entry, and exit

The runtime attempts the **entire frozen enrollment census** before allocating candidates. It shares immutable provider observations, validates the exchange calendar, computes full-prefix native features, records decisions, and orders candidates deterministically. A missing warm-up with verified insufficiency is known ineligible; a failed or stale provider read remains unavailable with its own receipt. A partial scan is never presented as a completed ranking.

Hourly acquisition runs first and the decision clock advances between frames. While hourly sleeves are installed, the worker defers broad daily/weekly acquisition throughout the hourly opening window and during the 60 seconds before an immediate hourly boundary. This priority remains in force after hourly buys are queued, so normal fill processing can run before unrelated scans. Already completed cached daily/weekly censuses may still allocate at their eligible opening, and owned exits remain serviced. A cold install must prewarm its full daily/weekly census before the shared 09:30 opening; an unprepared book stays blocked rather than selecting from a partial roster.

Two source-coverage regimes are distinguished. The strict default, `missing_data_policy="require_complete_enrollment"`, blocks all entries in an enrollment with an unresolved source failure. The named CLI explicitly selects `missing_data_policy="exclude_unavailable_with_census_receipts"`: every enrolled name must still be attempted, and **at least 99% valid or verified-ineligible coverage** is required before admitting healthy candidates. This 99% threshold is fixed in this runtime policy; there is no `minimum_known_coverage` configuration parameter. Unavailable names are individually blocked and retained in the census/denial records. More extensive failures or an incomplete census block all new entries. Every admission links to a content-hashed full-census receipt, including known/failed counts. This is a disclosed forward execution choice for current provider availability, not a winner filter, model refit, or re-evaluation of R11 returns.

The pinned current asset-status evidence marks BLFS, CRNX, EA, LEG, QRVO, and WBD inactive and nontradable at its recorded observation. These six names remain in the original enrollment and its denominator, with individually verified-ineligible receipts; they are not erased from the source universe. The evidence establishes status at its captured time, not a permanent historical or future asset master. The actual policy and evidence hashes belong to each installation. Full-roster throughput must still meet the opening contract. A missed window is a measured operational result, not a retroactive fill.

Forward ingestion retains the immutable research/previously observed prefix and appends only new genuinely completed native periods. Later ordinary overlapping vendor corrections are audited against the original values and retained as raw provider revisions; they do not rewrite R11 or silently change an earlier decision. The named CLI binds `forward_revision_policy="retain_frozen_prefix_audit_minor"`, allowing audited retention of original overlap values when the maximum OHLC relative correction is at most 5%; completion-clock changes or larger price-basis changes remain blocking errors pending a supported action/basis review. The stricter `reject_any_revision` mode is available. Appended data must overlap and bridge the bound source series rather than silently omit intermediate native periods. Current Yahoo chart responses may also contain a zero-volume session-close point quote: an identified hourly/weekly point stub is quarantined as a quote, not counted as an OHLCV feature bar. Unfinished native periods remain excluded. A calendar close alone cannot finalize a cached partial candle. Native admission requires completion no later than both the actual fetch receipt and decision clock; `usable_at = max(first_observed_at, fetched_at, completed_at)`. A genuine post-close reread of identical content can therefore become usable while preserving the immutable first-seen receipt. Advancing the decision clock without a post-close fetch cannot manufacture knowledge. Full revision receipts and the source-receipt journal retain these diagnostics. These ingestion choices and their guard thresholds are part of the forward regime; original full-history research performance is not reasserted for it.

The repaired ingestion contract binds the canonical seed identity and membership in `a_tensor_prefix_bindings`: source SHA, original row count, first/end timestamps and original endpoint opening. A historical timestamp newly supplied at or before the retained immutable endpoint is quarantined, with the raw provider row and diagnostic receipt retained; it cannot shift source ordinals, model phase or repair cooldown. Migrating an already malformed nonfinancial cached prefix restores the exact pinned original rows plus only genuinely later periods, invalidates affected candidate/cooldown/cycle-read state, and appends a `tensor_native_prefix_repair` event. Any same-book/symbol fill or active intent blocks this migration pending explicit review; financial execution is never rewritten.

A nonnative weekly supplemental aggregate is excluded only when it is the final Yahoo row, its timestamp exactly equals the explicitly supplied `vendor_regular_market_timestamp`, and that timestamp is no later than the actual fetch. Price shape and nearest-week rounding cannot justify exclusion or relabeling. This guard supplements the distinct zero-volume session-close quote-stub rule; raw source revisions remain intact. These repair contracts need post-repair source/audit/live-roster receipts before current operational acceptance.

Ready coverage left by an older integration cannot bypass canonical-prefix verification merely because a durable census cursor has advanced. The acquisition pass rewinds to the earliest ready name lacking its persistent prefix binding, while current failed/verified-ineligible assessments remain explicit. An admission barrier requires the corresponding verified binding; original candidate/cooldown evidence is changed only when a pre-financial comparison actually establishes a malformed prefix. A bound immutable prefix alone does not mean the name was scored at the current origin: after restart or prefix repair, acquisition must also revisit every absent current-origin assessment independently of the saved cursor or binding. Current failed/verified-ineligible assessments remain explicit and the same bounded fair read budget applies. Admission requires a completed current census, not just a completed historical cursor.

The hourly intraday point-quote exclusion is separate from the weekly aggregate: it requires a final Yahoo row at the exact `vendor_regular_market_timestamp`, flat OHLC and zero volume. A nonflat hourly row, missing/mismatched marker or nonfinal row cannot qualify.

Provider omission exemptions require `omitted_bar_rows` and `source_row_count` to prove exact raw row indices, timestamp membership and invalid or missing OHLCV fields, including inconsistent high/low/open/close shape. An excused normal native period must still complete after both the actual fetch and decision clocks. A malformed nonnative weekly supplemental row may instead be quarantined only when it is the final raw Yahoo row, at the exact declared regular-market timestamp; it cannot be relabeled as a week or become features. Unknown/completed omissions and malformed nonflat hourly supplements remain blocking. Normal native partial rows are excluded before numeric validation while genuinely unfinished; completed malformed OHLCV still fails. Raw fields/source/evidence are retained. No omitted or unfinished row contributes a feature, bar count, cooldown or learned label.

Weekly source requests also bind their actual query boundary. For a named weekly lookback, the Yahoo adapter sends explicit `period1` at the preceding Monday 00:00 America/New_York and `period2` at the actual current request time, then retains `request_window` metadata. A named range beginning midweek can otherwise label a clipped aggregate as a complete week and falsely trigger the unchanged 5% overlap-basis gate. This query correction includes every session of the first requested week; it does not rewrite any original research row or relax the basis threshold. Vendor interval identity and canonical native labels remain checked.

Causal availability is checked across the entire supplied prefix. A repaired original seed may have a later actual availability receipt than a retained forward tail, so daily inference must wait for the maximum usable time across all rows, including the exporter's second conversion, rather than only the newest market bar. Receipt times need not increase with source-bar order. Never backdate a new seed receipt or sort/rebase market ordinals to evade this requirement. Failed sources remain in fair bounded retry; after every enrollment member has been attempted, the full acquisition budget can service the failed backlog while original windows and coverage rules remain enforced.

NYSE regular-session hourly buckets start at 09:30 New York time. The final bucket can be 30 minutes, including half-day sessions; it counts as one observed row. Daily completion is the actual session close. Weekly completion is the last actual session close in that week. Source midnight/Monday keys are identities, not tradable prices. Holidays and daylight saving come from the validated calendar. Unclosed, future, malformed, or unusable rows cannot become inputs.

The research reference enters at open `i+1` and exits at open `i+21`: **20 complete observed native holding bars**. A forward entry must originate from the latest eligible completed native period, then use an actual observed quote at or after the next eligible opening. The entry window is bounded to **300 seconds** by default, and may be configured more narrowly. An expired hourly signal cannot be replayed at today's quote. No previous opening price is fabricated after the receipt arrived. Provider revision observation time and raw quote timestamps remain in the receipts.

The paper fill anchors the holding clock to the **actual filled native period**. Held bars are counted from that anchor using observed completed periods. No stop, target, trailing exit, winner filter, or glyph-based early sale is added. At 20 held native bars, sell the remaining owned quantity at an eligible actual opening. A failed or missed time exit remains owed and may retry at the next eligible observed opening; hourly retries use the hourly native grid, daily/weekly retries use actual daily exchange openings. Disabling new entries does not disable this obligation. Ending a download does not invoke R11's study-terminal liquidation convention.

Each book defers new allocations while an owned risk-reducing sell is pending. After that sell actually fills, the next timely pass reranks/recomputes slots, equity, and spendable T+1 cash; the unsettled proceeds are not recycled. Held-data/owned-exit service and ordinary fill processing receive priority around broad scans. The final independent mixed-holding stall harness confirms an owed exit filled through normal execution before an immature held-data read and broad-source stall; its synthetic clock and isolated database do not attest to actual market liquidity or live census capacity. Coverage/action/source-basis deferrals are audit records, while successful entry/exit records link an actual durable intent.

Entry reservations count against ten slots and spendable cash. Duplicate evaluation, restart, partial fills, cancellation, and retry retain the original client intent and decision linkage. An existing holding or pending buy prevents a second position in the same book. The same name in another independent sleeve remains a separately owned exposure; consolidated monitoring makes that overlap visible.

Broad source acquisition uses at most 32 reader workers. Exact persisted coverage-tail metadata is atomically bound to frame, symbol, revision, the actual compressed-history hash, row count and last native clocks; it selects the query lookback without a redundant full-history decode. Legacy hints are verified/primed before the opening, and malformed legacy records remain isolated with their original evidence. The full native history still passes the actual input gates. Compact unsorted JSON with level-1 zlib changes physical storage bytes only: the decoder preserves every typed native-bar scalar, row order and causal clock. This does not shorten indicator history, rebase ordinals or alter the frozen engine input identity.

A source-valid H1STATE/WSTATE name under a strictly unexpired, pinned persisted opportunity cooldown may be admitted as a proved no-new-opportunity assessment without recomputing indicators. The complete merged history, actual closure, prefix identity and source gates are still verified. Receipts explicitly mark `native_features_recomputed=false`; equality, absent/invalid state, prefix repairs, first evaluation and daily models use full inference. Existing same-origin candidates remain intact. The exact proof conditions are in the archive rulebook.

## Capital, costs, and settlement

At most ten long whole-share positions are allowed in each book. For each new entry, the reference capacity is:

```text
min(0.10 * current_book_equity,
    0.01 * signal_mean20_native_bar_dollar_volume,
    available_settled_cash)
```

Reference shares are the floor of that capacity divided by `entry_open * 1.001`. The research fee is 10 bp of notional on each side. The named local-paper installation sets **10 bp adverse price slippage and zero fixed order fee**: quote-based buy prices move upward and sell prices downward. This has the same proportional round-trip arithmetic at identical underlying quotes, but remains a different execution record from the research's opening price plus fee. Forward sizing also covers configured adverse slippage and any explicit per-order fee. Actual quote timing, cent rounding, and fill prices remain visible; do not relabel slippage as a broker commission or assume a historical opening quote was realized.

For $100,000 equity, $2 million native-dollar-volume mean, ample settled cash, and $50 price, reference capacity is $10,000. `floor(10,000 / 50.05)` gives **199 shares**, with a $9,959.95 modeled debit. Existing gains are not rebalanced back to 10%; the cap governs a new allocation. The capacity mean is measured at the signal, not from the future entry bar's realized volume.

Strategy-owned books preserve exact-cent sale-settlement records. Net sale proceeds contribute to equity immediately but become spendable only at the **next actual NYSE session open**, including holidays. Cash is reduced by unsettled proceeds and pending reservations before another buy. A Friday sale does not release on Saturday or a Monday holiday. No other book supplies a missing balance, and no margin or automatic cash-interest assumption is introduced.

Account and order events are atomic, ownership-bound, and append-only. The local executor's generic bookkeeping cash is distinct from the strategy's spendable settled-cash view. Ledger reconciliation must preserve both views and their release timestamps. A failure to reconcile pauses new risk; it does not invent inventory, settlement, or successful exits.

### Implemented corporate-action accounting

`backend/tensor_actions.py` implements separately evidenced local-paper split and distribution accounting. Events bind source observations and definitions to an owned book. A timely verified split atomically adjusts whole-share quantity and cost basis, cancels stale orders in the old share units, and retains any fractional cash-in-lieu claim separately. Conflicting evidence or a late split after affected fills requires review rather than rewriting the ledger. Idempotent action identity prevents duplicate application. Old source quotes are valued in the current share units without editing the stored quote.

Yahoo establishes a USD listing and an evidenced **nonspendable ex-dividend receivable** from the quantity owned before the ex-date opening. Yahoo's ex-date event does not provide a pay date. A separate GET-only Alpaca corporate-action source can independently match symbol, ex-date, rate, domestic identity, and declared payable/process dates. Local-paper release uses the **later declared payable/process date at 09:30 New York time**, only after that time has passed and the matching source has actually been observed. A missing Alpaca currency field uses the explicitly evidenced Yahoo domestic-USD listing convention; an explicit contradiction or ambiguous matching records withhold payment.

This is a declared-date **local-paper simulation**, not proof that Alpaca or a broker credited real cash. Missing read configuration, dates, identity, rates, or entitlement evidence leaves the receivable pending. A fractional cash-in-lieu mark is provisional and nonspendable; release requires a trusted dated receipt for its measured amount. Unresolved fractional claims, action conflicts, or missing action coverage block comparable performance/affected risk admission rather than establish fabricated wealth. Action payments do not receive the sale-proceeds T+1 rule a second time; they become local paper cash when the independently matched payment convention is actually evidenced.

A known post-seed split also blocks new native-feature entries for that name pending an explicit source-basis review. The original research prefix is not split-adjusted or rewritten. A split discovered in candidate action preflight still blocks a subsequent buy. Separately observed completed clocks continue to service owed exits, and genuine action handling updates actual owned share units. None of this turns R11's raw-price benchmark evidence into a validated dividend-inclusive total-return study.

## Observe readiness and forward evidence

Before expecting trades, inspect all of the following:

- Four installations exist and each maps to a different local book with its own explicit funding receipt.
- Enrollment/source/model hashes match the frozen installation; canonical daily history and its endpoint ordinal pass.
- Every enrollment member has a current-cycle census receipt, with valid native coverage, verified ineligibility, and individually blocked unavailable names separated; the configured strict or 99% forward coverage gate actually passes.
- Entry enablement, global runtime state, scheduler heartbeat, pending reservations, cash availability, and T+1 release are visible.
- The opening window was met; stale or delayed quotes were not reused as a historical open.
- Due exits, missed exit obligations, partial fills, denials, native held-bar counts, corporate-action state/receivables, NAV, and concentrated cross-sleeve exposures are retained.

The retained source-only 1,820-name hourly computation took **277.316 seconds**. A later full-manager source-fixture benchmark took **255.033 seconds**, or **262.033 seconds** after seven one-second intertick gaps, with a synthetic 1.2-second delay per read. It timed the full 1,820-name seed/hash/calendar/native/cache/database/census path, with entries disabled and zero intents/fills. Its original runtime pin is `647b3f5ce8508a6854fdb28a2034b35a129d2af9b6faec84730901885adfbf5a`, before the final unrelated-acquisition coordinator change. Keep each earlier receipt's source identity unchanged. These measurements exclude actual live vendor availability and action/quote/fill work; they show fixture capacity, not a completed current market-opening census or profitability.

The target is to beat QQQ and SPY after measured costs. Track every sleeve against date-aligned price benchmarks and distinguish deposits from returns. A four-book dashboard is not a previously tested blended portfolio. Until sufficient actual forward observations exist, report the historical reference and current operational evidence separately rather than labeling an installed book profitable.

The automatic `benchmark-history` schedule archives daily QQQ and SPY observations. Strategy-owned NAV comparisons require matching vendor adjusted-close benchmark series and clean, aligned closing valuations; a raw-close series cannot stand in for a distribution-inclusive account comparison. Missing benchmark/action/valuation evidence withholds comparable returns and excess-return metrics. This reporting requirement does not change the frozen entry predicates or turn the raw-open historical research into a total-return study.

R11's best relevant historical books returned 30.0452% for hourly state repair, 70.5415% for weekly state repair, 92.2193% for D20PV, and 66.0337% for D20TENSOR. The hourly window is January–September 2026; the other three are January 2025–September 2026. Daily price/volume beat its Tensor-augmented pair on that reused period. Research roster survivorship, action/dividend adjustments, authenticated historical receipts, actual spreads/fills, and concentrated winners remain limits. These numbers do not certify current provider readiness, the forward incomplete-availability/retained-prefix regime, a dividend-inclusive total return, or future outperformance.

The paused pre-repair operating database is preserved in `operating-state/pre-live-prefix-repair/STATE_ARCHIVE.json` and three ordered gzip parts: 209,809,408 reconstructed SQLite bytes, 149,507,351 compressed bytes, a successful SQLite check and full reconstruction SHA verification. It has four installed books and zero intents, fills or positions. It preserves the actual data/candidate diagnostics before migration, rather than representing current repaired readiness. Follow the archive's part order to reconstruct into a fresh database; preserve the running database.

## Source and verification locations

- Frozen native engine/adapter provenance and finite parity receipts: [`strategies/tensor_state_repair/engine/README.md`](../strategies/tensor_state_repair/engine/README.md), `SOURCE_MANIFEST.json`, and `STATE_FAST_TEST_RECEIPT.json`. The final manifest binds 26 files, including 24 byte-identical R11 scientific sources and 20 unchanged frozen modules; its SHA-256 is `5f38a63a611bdfbe62ceb6a0619f64559e7b9d136f51ac57597988d8da2ee28c`. The 24 combined native/fast-state checks passed without refits or financial trials. The earlier `TEST_RECEIPT.json` remains labeled by its original adapter hash.
- Original model artifacts, numerical exports, canonical daily anchors, and export parity: `strategies/tensor_daily20/models/MANIFEST.json`, `EXPORT_PROVENANCE.json`, and `DAILY_SOURCE_ANCHORS.json`.
- Exact rules and full R11 reference bindings: the new R12 `RULEBOOK.md` and `researchmanifest.json`, saved alongside this implementation in the quant research archive.
- Main installation/pre-start evidence: R12 `verification/MAIN_DESK_INSTALL.json` and `MAIN_DESK_PRESTART_STATUS.json`; resident activation: `MAIN_DESK_ACTIVATION.json`, with separate health/strategy snapshots. Independent final integration: `INDEPENDENT_INTEGRATION_FINAL.json`. Source-fixture timing receipts preserve their original pre-final runtime hashes.
- R11 immutable source: [`REPORT.md`](https://github.com/dwj9ddyvf6-hub/quant-research-backup/blob/4b08cfddcc67d6542e7cb583223874f839cd8f2b/research-archives/2026-10-09-tensor-forensic-edge-study-r11/REPORT.md).

The frozen whole-backend receipt records **495 tests passing in 35.167 seconds**. The independent receipt binds runtime `27c3b260ffd6d273ca4a1b0c0236ae3475703da941fd08138b482e898c465256` and provider `9bbff46e826cfac32e13a70fcf7b44a604aab0a80e9eaf23666ed6627e598285`, with **171 Tensor tests and 15 isolated harness checks passed** and source unchanged. These checks cover native/model parity, all four holding/exit paths, conservation, causal receipts, source normalization, restart recovery, bounded acquisition, exact cache/codec integrity, persisted-cooldown proof and owned exits before stalls. They establish finite implementation correctness within their tested scope; live opening capacity, realized fills and profitability require separate evidence. Earlier genuine receipts retain their original source identities and the failed actual/rehearsal outcomes remain archived.

Main installation and resident activation have been observed. Current timely full-census operation, persistent host supervision, an actual forward fill, and date-aligned comparable performance still require their own receipts.
