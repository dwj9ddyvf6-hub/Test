# 08 — Research, validation, and testing

Two kinds of validation matter and are often confused:

1. **Is the strategy any good?** (statistics; slow; mostly answers "no")
2. **Does the desk do what the strategy says?** (engineering; fast; the source of most real losses of value)

Common implementation failures include exits that cannot fire, fills modeled from stale prices, missing data interpreted as a signal, and recovery reversing the intended side. Retuning a strategy does not repair these defects. **Fix implementation gaps against the sleeve's own spec; do not retune the strategy to compensate.**

## 8.1 Research hygiene

* **Pre-register** the hypothesis, universe, definition, hold, and the tests that would falsify it *before* looking at results.
* **Three data splits**: train (find), holdout (confirm), **fresh/forward** (never touched until the end — ideally *live shadow* data after the freeze date).
* **Point-in-time** data only: survivorship (include delisted), no look-ahead (indicators using a bar that had not closed), no restated fundamentals.
* **Costs**: spread, impact, borrow, fees; use conservative assumptions; test sensitivity.
* **Multiple testing**: you ran many cells; some pass by chance. Correct within the *hypothesis family* (not across every cell you ever tried) and report how many cells you looked at.
* **Effect sizes and intervals**, not p-values alone; cluster by time (overlapping outcomes are not independent).
* **Judge the right statistic**: a strategy whose profits come from a few large winners cannot be judged by the median or "drop the top 5"; those statistics reject it by construction. Choose the statistic that matches the *claimed* edge, and say so beforehand.
* **Power check**: plant a known edge in synthetic data and see whether your gates would find it. Our own gates — train CI > 0 *and* plateau *and* holdout CI > 0 *and* multiple-testing correction *and* median > 0 *and* drop-top-5 > 0 — could not pass a real lone narrow edge: the bootstrap p-value floor (1/n_boot) times thousands of cells made a Benjamini–Hochberg threshold unreachable for any single discovery, and a 25-observation holdout had a confidence interval so wide that even a large planted edge could not clear it. **Gates that only control false positives silently kill real edges.** Measure both.
* **Revival asymmetry**: killing one idea takes one failed gate; reviving needs three passes — decide this deliberately, and keep a kill ledger so killed ideas do not return under new names.
* **Name things by source definition**, carry identity/date/units/timeframe beside every row; similar labels hide different semantics.
* Treat **narrative** (reports, cards, status text) as claims: each sentence must be checkable against the numbers (direction, threshold, units, timeframe). A page said "a fear day" next to a +1.2% index move.

## 8.2 From research to the desk: the translation layer

| research artefact | desk artefact | check |
|---|---|---|
| fire files with dates and reference prices | signal feed with validity windows | age check + schema check + "seen until decided" |
| backtest entry convention (e.g. next open) | modelled fill price rule | unit test of the fill price |
| exit conventions (time/target/trail) | exit routes with the host's inputs | exit audit |
| size classes | `slot_usd`, `size_class` | sizing test with the real slot |
| universe filters | feed-side filters | count the universe each day; alert on collapse |
| external code (vendored) | pinned bytes + manifest | hash check at startup |

Run an **identity audit**: for each sleeve compare the desk's decisions with the origin's on the same historical inputs. A 4,000-random-case parity test on a single boolean gate found an inverted rule; a "per-sleeve logic diff" against a pinned commit found missing fill-time risk blocks (a high-volatility shock freeze, end-of-year and event-day blocks).

## 8.3 Testing pyramid for a desk

1. **Static**: compile, lint, secret scan.
2. **Unit**: ids, tick rounding, caps, FSM transitions, clock/session math, reconcile arithmetic.
3. **Invariant tests that fail on the old code** (one per bug-log row).
4. **Fake-broker lifecycle**: partial fills, refusals, timeouts, crash between send and save, final-state handling, deadline expiry, one-bad-fire isolation, restart no-reentry.
5. **Replay/parity**: ledger replay == book; origin parity on random inputs.
6. **Rehearsal**: a dry run of N sleeves through a realistic day with frozen data; measure first/steady pass time, memory, order count; assert **all** orders came from the shadow/fake broker.
7. **Load**: synthetic hundreds of sleeves (state clearly that load tests on synthetic sleeves prove capacity, not alpha).
8. **Regression harness** (`regress.py`): one command, groups, PASS / WARN / FAIL / SKIP-with-reason; **SKIP is never PASS**; blockers named in the bug log must exist (`bug_log:every_row_has_live_blocker`). Run before every push; run fast subset after every change; full nightly.
9. **Restore drill** and **boot drill** (kill everything, boot, assert recovery).
10. **Forward test**: the desk itself in shadow/paper for weeks.

### 8.3.1 Test hygiene lessons
* **Tests must never touch live state** (live input files, live ledger, live order mode). Run them on a **copy** of live inputs or on frozen fixtures. A test suite that rewrote live producer files on every regress could hand a running pass a torn file.
* **Tests must import the checkout they live in**, not a hard-coded production path (a branch's tests silently exercised main's code).
* **Fixtures that hard-code live names** (a specific ticker "that is currently in a lane") rot the day the data changes and produce failures *with no product fault*. Synthesize fixtures; match orders by id, not by symbol.
* **A guard hole**: 18 bug-log rows named a test file as their blocker, but nothing ever ran it; it had been failing for days. Every named blocker must be executed by the harness.
* **Timing-dependent tests** are labelled and quarantined with a documented reason; never deleted silently.
* A test that checks `"a fear day so far" in note` matches `"not a fear day so far"`. Add negation cases.

## 8.4 Evidence discipline ("green is an evidence state")

Report exactly one of **GREEN / PARTIAL / BLOCKED / UNVERIFIED**.
* GREEN needs evidence from the **final** artifact, after the **last** change, at the boundary the claim names.
* "Command exited 0", "the toast appeared", "the commit exists locally" are not the boundary. For a push: verify the remote ref. For a deployment: verify the live version responds. For a backup: restore it. For a fix: reproduce the original failure on the old code, then show it gone on the new, then show nearby invariants hold.
* Don't generalize from adjacent proof (a build ≠ runtime; one interval ≠ every timeframe; desktop ≠ mobile; a source test ≠ a deployed worker).
* A later "small cleanup" invalidates earlier proof to the extent it can affect it.
* Keep a **compact incident receipt**: outcome and scope, protected state, expected vs observed, first failed boundary, hypothesis and the discriminating check, root cause, minimum repair and guard, final artifact, post-change proof, status, remaining uncertainty, where the lesson was recorded.

## 8.5 Measuring performance honestly

* Report **forward** results with the number of trades, the date range, costs assumed and the benchmark; show losing sleeves too.
* Do not annualize a few weeks.
* Distinguish **desk P&L** from **strategy P&L** (timing slippage, rejected orders, caps).
* Paper fills are optimistic about liquidity and queue priority. Micro-cap fills in particular: treat paper results as an upper bound.
* A record of the market around each decision (1-minute bars ±30 min and quotes ±60 s around each intent/fill, append-only, GET-only) lets you later judge fill quality vs VWAP/mid and entry timing — record first, analyze later, never feed it back into control flow.

## 8.6 Efficiency work without weakening evidence

When something is slow: **measure the whole path stage by stage**, find the dominant constraint, fix *that*, re-measure. Examples: a "parallel" queue still serialized at the CPU stage (use bounded CPU workers, recycled to limit native memory growth); one chart cache miss per request multiplied by a burst (single-flight coalescing); a vendored function was O(n²) (a shim that early-exits with identical outputs on a corpus); a loop re-evaluated unchanged sleeves off-session (skip when inputs/position/cash unchanged, but re-evaluate at least hourly, never during market hours). Never speed up by shrinking the workload, dropping identity/freshness/completeness checks, or treating synthetic load as production proof. Report the exact workload and environment of each measurement; don't compare unlike probes.

## 8.7 When the human gives a concrete correction
Treat it as a **falsification test** of your hypothesis. Reproduce the exact route and identity they named; look for a second implementation, stale cache, wrong version or environment mismatch; change the hypothesis before acting again. Don't re-ask a decision they already made.


## Addendum — measurement traps (from the archive review)

- **Universe and filings must be point-in-time**, including delisted names; do not let *missingness* encode the future (P-111).
- **Don't clip the tail you claim to harvest.** Benchmark against **matched controls** (same volatility/size) and the *same conditions without the signal* (P-112).
- **Nulls need many draws; count the books you tried; deflate** (P-113). Compare a ranking rule with **random books of the same width** from the same eligible names (P-114).
- **Indicators that describe the past**: measure excess after entry, excluding the signal bar (P-115).
- **Provisional vs completed candles**: a quote is not a candle; label provisional decisions and log disagreements (P-116). **Census the data first** (P-117).
- **Learning is gated on forward sample size**; run alternatives in shadow books; the learner records excursions without editing rules (P-118). Cross-check published artifacts (P-119). Reconcile corporate-action units (P-120).
- Honest typical outcome: most 'edges' vanish against matched nulls; a small number of context-conditional effects survive. Report that plainly.
