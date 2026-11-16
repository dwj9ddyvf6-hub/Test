# Best Trade Setups Board — Redesign Best Practices

## Summary

Five convergent lessons from credible products and engineering literature:

1. **A board is a lifecycle, not a list.** Every credible product examined uses explicit states (pending/watch → active → completed/expired/cancelled), a time-box after which an untriggered idea auto-expires, and a visible closure record. Silent disappearance is the anti-pattern; TradingView even makes published ideas non-deletable and editable only briefly, forcing closure to happen as an appended update.
2. **“Extended” and “invalidated” are measurable, pre-declared states, not vibes.** The clearest retail convention is IBD's: a buy zone ends 5% above the buy point, losses are cut at 7–8%, and most profits are taken at 20–25%. Translate those percentages into your own instrument/ATR terms, but pre-declare them per setup type.
3. **An options spread is a different instrument from the stock plan that inspired it.** It must be presented in its own arithmetic — legs, strikes, expiry, net debit/credit, max loss, max gain, breakeven — with underlying levels relabelled as *reference / thesis-invalidation levels*, never as a “stop” that will execute. There is no resting stop on the underlying for a defined-risk spread.
4. **Spliced facts are prevented structurally, not editorially.** One immutable source event/record per plan, provenance on every fact group, and fail-closed cross-field validation (e.g. long: stop < entry < target) that *rejects* publication rather than warning. Backfilling provenance after the fact defeats the gate.
5. **Publish is a separate, protected step with its own time budget.** Deadline propagation (Google SRE), per-task timeouts (Airflow), partitioned/checkpointed recompute (Dagster/Airflow practice) and idempotent partial publication mean a long compute pass can delay *freshness*, but must never starve *publication* for an hour.
6. **Sub-1 reward-to-risk is not automatically bad — undisclosed sub-1 R:R is.** At first-target R:R of 0.35, the breakeven win rate is 74.1% before costs (`1/(1+R)`). A card that prints “0.35R” without that number, the strategy's realised win rate, and the payoff to the *final* target is materially misleading.

Confidence: high on options arithmetic, IBD thresholds, SRE/Airflow patterns and the R:R formula (primary/vendor sources, several verified live); medium on lifecycle display durations and target-spacing — no universal standard exists there, so the rules below are labelled **proposed** where they are synthesis rather than sourced convention.

---

## Findings

### 1. Setup Lifecycle & Board Composition

**What credible products do**

- **Explicit state machine.** A documented signal lifecycle (MQL5 signal guide, index) runs PREVIEW → PENDING → ACTIVE → COMPLETED, with two distinct non-loss exits: EXPIRED (entry never reached inside the allowed window) and CANCELLED (pattern failed post-detection validation). Crucially, expired/cancelled are recorded as *not a loss — no trade was ever opened*. Conflating “never triggered” with “lost” corrupts both the board and the track record.
- **Time-boxed pending ideas.** In that same lifecycle, a pending signal auto-expires if price does not reach entry within a set window (default 30–50 bars in the example). The generalisable rule is *refresh-or-drop*: an idea survives only if it is re-validated; age alone kills it.
- **Entry zone with a hard top — “extended”.** IBD defines the actionable range as the buy point up to 5% above it (verified live on its profit-taking page, which states the 20–25% zone is measured from the ideal buy point and the ideal buying range runs to +5%). Past that top the stock is conventionally described as extended / past the buy zone — it may be a fine holding, but it is no longer a *new entry* at the published plan's prices, because the stop distance (and therefore R) has silently grown.
- **Pre-declared exit rules drive removal.** IBD's companion rules — cut losses at 7–8% below purchase, take most profits at 20–25% — are the triggers that move a name off the active list. IBD Leaderboard operationalises this as a separate **Cut List**: stocks are moved there when they flash sell signals, so departure is itself a published event, not a deletion (GlobeNewswire/IBD product description, index; secondary reviews describe the same add/remove signalling and timestamps).
- **Complete plans, short intended dwell.** IBD SwingTrader (secondary review, index) ships each name with exact buy zone, profit target and stop-loss, targets a typical 5–10 day holding period, and pushes alerts when a name enters its zone or hits a sell signal. The board's dwell expectation is stated up front, per product.
- **Permanent, append-only idea record.** TradingView's publishing rules (support, index): ideas can be edited only for ~15 minutes after publication, cannot be deleted, and authors are directed to use “Update Idea” to report how a setup played out. Motley Fool's scorecard model (primary Fool article, index) keeps every pick — including large losers — visible to members from day one. Both are the same principle: the historical record is immutable; only status changes.
- **Does an idea retire when the publisher itself trades it? No sourced product does this — and research regulation points the other way.** FINRA Rule 2241 requires firms to have policies designed so a research analyst does not benefit from knowledge of a report's content or timing ahead of its intended audience, plus conflict disclosure in reports (SEC approval order, index; the order discusses the older NASD paradigm of a restricted window around publication — 30 days before to 5 days after — replaced by a “reasonably designed” firm policy). The compliant patterns are therefore: (a) publish first, trade later / within a disclosed blackout, (b) disclose the publisher's position on the card, and (c) if the desk *does* take the trade, that is an **activation/fill event** on the same record — not a reason to pull the idea. Retiring an idea *because* the house traded it would hide exactly the conflict readers most need to see, and would let a publisher front-run its own board in appearance even in a paper-trading context. For a paper desk: freeze the published plan at publication, log the paper fill against it, and disclose “desk paper position: open/closed” on the card.

**Adoptable rules — Lifecycle**

1. Use six states only, shown verbatim on the card: `Watch (pending entry)` · `Active` · `Target hit` · `Invalidated` · `Expired — never triggered` · `Closed — other (reason required)`. Never reuse “closed” without a reason code.
2. Every card is born with `expires_at`. Default time-box: **5 trading days for a pending swing idea, 10 trading days maximum for an active idea** (aligned to SwingTrader's stated 5–10 day horizon) unless the setup type declares otherwise at publication. No silent extensions: extension = a new validation timestamp + a visible “refreshed” note, max 1 extension.
3. Extended rule: if price closes **>5% above the top of the entry zone** (or >1× the planned stop distance past entry, whichever comes first) before triggering, move to `Expired — ran past entry (extended)`, do not chase by widening entry or stop. Re-entry requires a *new* card with a new ID.
4. Invalidation rule: a close through the invalidation/stop level, or the thesis event failing (e.g. breakout closes back inside the base), moves the card to `Invalidated` in the same publish cycle in which it is detected — never at end-of-week tidy-up.
5. Departures stay visible: a **“Recently closed” rail for at least 5 trading days** (proposed; no universal standard found), each row reading `Idea closed: <reason> · <date> · outcome in R`, and a permanent archive/scorecard thereafter. Nothing is ever deleted from the archive.
6. Publisher-interest rule: publication timestamp precedes any desk (paper) fill timestamp on the same name; the card discloses desk paper status; a desk fill changes status to Active, it never removes the card.
7. Staleness on the surface: every card shows `Plan as of <timestamp>` and `Prices checked <timestamp>`; if prices are older than one publish cycle, the card is badged `Stale — awaiting refresh` rather than presenting old levels as live.

**Strongest sources — §1**
- IBD, *When to Take Profits* — https://www.investors.com/ibd-university/how-to-sell/taking-profits/ (verified live, 2026-10-16)
- TradingView Support, *Publishing and updating ideas* — https://in.TradingView.com/support/solutions/43000591338-publishing-and-updating-ideas/ (index)
- SEC, *Order Approving FINRA Rule 2241* — https://www.sec.gov/rules/sro/finra/2015/34-75471.pdf (index)

### 2. Options Positions in a Plan

**What quality platforms do**

- **The payoff arithmetic is standardised and always complete.** The Options Industry Council (OIC) bull-call-spread brief, reproduced by InvestorPlace (index), and Investopedia's vertical-spread table (index) agree on the same four numbers for a debit call vertical: **max loss = net debit paid; max gain = (short strike − long strike) − net debit; breakeven = long strike + net debit**; both legs same expiry, same class, different strikes. Credit verticals mirror this (max gain = credit; max loss = width − credit; breakeven = short strike ∓ credit). Any card missing one of these is incomplete by industry convention.
- **The order ticket is the de-facto lay template.** tastytrade's ticket/support docs (verified live) display, before an order is sent: probability of profit (PoP), probability of making 50% (P50), delta, theta, max profit/loss and buying-power effect, with a warning that the figures apply only at order entry because markets move. That set — PoP, max P/L, cost — is what lay readers have been trained to expect.
- **Management conventions replace a stop order.** tastytrade-derived practice widely cited in education (index): close/ manage defined-risk spreads at **50% of max profit**, and manage/roll-or-close at **21 days to expiry (DTE)** rather than holding into expiration, because assignment/pin risk and gamma rise sharply near expiry. Barchart education uses the analogous options-native stop for calendars: close if loss reaches ~20–30% of premium paid — i.e. stops for spreads are conventionally expressed as **% of debit/credit or spread value**, not as an underlying price.
- **Why there is no underlying stop:** a vertical spread's risk is already capped at the debit (debit spread) by construction; a stop-market order on the *stock* cannot execute an options spread, and a stop on the *spread price* can trigger on wide/illiquid marks and slippage. OCC's *Characteristics and Risks of Standardized Options* (the ODD, referenced by SEC/broker sources, index) is the canonical disclosure that must be pointed to. Schwab/Fidelity education consistently frame verticals as same-expiry, defined-risk/defined-reward structures (index).

**How to frame underlying levels honestly on the card**

- Label the stock levels as **“Underlying reference levels — not orders”**: resistance = the level the thesis needs (often ≈ short strike / target zone); support / thesis-invalidation = “if the stock closes below $X, the reason for this spread is gone — the desk's convention is to close the spread; your max loss remains capped at the $Y debit even if you do nothing.”
- Show a separate, options-native exit rule: e.g. “Close if the spread can be bought/sold at 50% of max profit, if spread value falls to 50% of debit paid, or at 21 DTE — whichever first.” That is executable; “stop = $X on the stock” is not.

**Adoptable rules — Options**

1. Mandatory card fields, no exceptions: strategy name in plain English (“Bull call spread — bet on a moderate rise, risk capped”), long leg (buy, strike, expiry), short leg (sell, strike, same expiry), net debit/credit **per share and per contract (×100)**, max loss, max gain, breakeven — with the formula shown once in a help note.
2. Show expiry as a date **and** DTE, plus “manage by” date (= expiry − 21 days, or the desk's earlier date). Flag earnings/dividend dates falling before expiry on the card.
3. Never print the word “Stop” next to an underlying price for a spread. Use two distinct rows: `Thesis invalid if (underlying, reference only): …` and `Spread exit rule (executable): close at …% of debit / by <date>`.
4. State in one sentence, on every spread card: “Risk is capped at the debit paid; no stop order protects or is needed for that cap, and gains are capped at the short strike.”
5. Include PoP only if its model/source and timestamp are named (as tastytrade does at order entry); otherwise omit it rather than printing an unlabelled probability.
6. Link the OCC Options Disclosure Document and note pin/assignment risk if holding through expiry is contemplated.

**Strongest sources — §2**
- OIC strategy brief via InvestorPlace, *Options Strategies: Bull Call Spread* — https://investorplace.com/2011/03/options-strategies-bull-call-spread/ (index)
- tastytrade Support, *Reviewing Trade Details Before Sending an Order* — https://support.tastytrade.com/support/s/solutions/articles/43000528791 (verified live, 2026-10-16)
- Investopedia, *Vertical Option Spreads* (summary table of all four verticals) — https://www.investopedia.com/articles/active-trading/032614/which-vertical-option-spread-should-you-use.asp (index)

### 3. Record Integrity / No Spliced Facts

**The failure mode, named**

Splicing = a derived record whose fields were taken from *different* upstream trades/events and joined on a loose key (ticker + date, say) rather than on the identity of one source record. Each field is individually “true somewhere”; the record as a whole describes a trade that never existed. This is the data-engineering analogue of cross-source conflation, and of a join fan-out/grain error.

**Patterns that prevent it**

- **Single source of truth per record, event as the unit.** AWS Prescriptive Guidance on event sourcing (index): state changes are logged as immutable events in an append-only event store, which serves as the single source of truth from which current state is derived by replay. Translated: a plan card is a *projection of one plan event* (`plan_id` + version), never a hand-assembled collage of fields from jobs that ran at different times.
- **Atomic fact groups / transactional outbox.** The companion AWS pattern (transactional outbox, listed in the same guidance) writes the record and the event announcing it in one transaction, so downstream never sees a half-updated plan. In pipeline terms: entry, stop, targets, instrument terms and timestamps are written **atomically or not at all**.
- **Contracts + tests at the boundary.** dbt's model (index): built-in tests (`unique`, `not_null`, `accepted_values`, `relationships`) plus singular SQL tests that must return zero rows encode invariants where the model lives and run in `dbt build`, so a violating record cannot merge/publish unnoticed. Great Expectations checkpoints do the same as a validation gate before release. Confluent Schema Registry compatibility modes (BACKWARD/FORWARD/FULL_TRANSITIVE, index) reject incompatible schema/record versions at registration rather than letting consumers discover corruption.
- **Provenance that travels with the record.** Engineering write-ups on provenance (index) stress: a derived record that drops its source reference and evidence status will be treated downstream as more certain than it is; and *backfilled* provenance is not provenance — a fail-closed gate must reject before any write/bulk action, on every entry path, with no bypass, even at the cost of friction. A warning-and-proceed log is not fail-closed.
- **Cross-field invariants as publish gates.** Beyond per-field checks, the record must satisfy joint invariants — the class of test dbt/Great Expectations express as multi-column expectations (e.g. `expect_column_pair_values_A_to_be_greater_than_B`).

**Adoptable rules — Integrity**

1. One plan = one immutable source record with `plan_id`, `source_system`, `source_record_id`, `source_timestamp`, `ingested_at`, `plan_version`. Entry, stop, T1, T2, legs and expiry must all carry the **same** `source_record_id`; a publish job that finds mixed source IDs in one card **rejects the card**.
2. No field-level cherry-picking: joins to enrich a card may add *display context only* (company name, logo) and may never overwrite a trade field. Trade fields are write-once per version; a correction creates version n+1 with a visible change note.
3. Fail-closed invariant gate before publish (long plans; mirror for shorts/spreads). Reject — do not warn — if any fail: `stop < entry_low ≤ entry_high < T1 < T2`; all prices > 0; R:R recomputed from the card's own fields matches the displayed R:R within 0.01; for spreads: long/short strikes, same expiry, debit = long premium − short premium, max loss/gain/breakeven recompute exactly; `expires_at > published_at`; quote timestamp within the publish window.
4. Provenance is captured at ingest, never inferred later. A record with missing provenance is quarantined (visible internally, never published) until a human re-sources it from the original record — not by guessing a plausible source.
5. Publish is atomic per card and per board snapshot: readers see either the whole old board or the whole new board (snapshot/version ID on the page), never a board where half the cards are from pass N and half from pass N+1 — unless §4's staged mode is explicitly badged per card.
6. Keep the raw upstream payload (or its hash + retrievable reference) for every published card, so any card can be replayed/audited to its single source — the event-sourcing test.

**Strongest sources — §3**
- AWS Prescriptive Guidance, *Event sourcing / Transactional outbox patterns* — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html (index / landing verified)
- dbt vs Great Expectations test patterns (built-in + singular tests) — https://github.com/shiningflash/data-engineering-practice-problems/blob/HEAD/problems/089-great-expectations-vs-dbt-tests/solution.md (index, inspectable repo)
- *A Backfilled Provenance Record Is Not a Real One* (fail-closed provenance) — https://medium.com/@FrankGoortani/a-backfilled-provenance-record-is-not-a-real-one-585afe371a8c (index)

### 4. Publish Cadence Under Long Batch Jobs

**The anti-pattern**

One monolithic “pass” that must finish before anything publishes couples the *slowest* computation to the *freshness promise*. If the pass overruns its scheduler timeout, the publish step is never reached, the board goes stale for an hour, and — worse — the next run may overlap or be skipped. Google SRE's framing (verified live): work that will arrive after its deadline is wasted work; systems should check how much deadline remains *before each stage* and abandon or degrade, rather than consuming resources on a result no one will use in time.

**Patterns from SRE / pipeline practice**

- **Deadline propagation + stage checks (Google SRE, Ch. 22).** A single absolute deadline is set at the top and passed down; each stage checks remaining time before starting. Apply literally: the *publish deadline* is fixed by the board's promised cadence; compute stages inherit what's left, not the other way round.
- **Per-task timeouts, not one global timeout (Airflow docs, index).** Airflow separates `execution_timeout` (per task instance — exceeding it fails that task), `dagrun_timeout` (whole run) and `sla`/`sla_miss_callback` (alerting on lateness). A publish task with its own small timeout cannot be starved by a compute task with a large one if they are separate tasks in separate pools/queues.
- **Priority and resource isolation.** Airflow pools and `priority_weight`, and Dagster's asset/partition model (index), exist to let a small critical job pre-empt or bypass a large backfill: partitions materialise independently, freshness policies track per-asset staleness, and a failed partition does not block unrelated partitions from materialising.
- **Checkpointing / state table.** Pipeline practice (index): a control/state table keyed by `batch_id × step` records SUCCESS per step; on retry, completed steps are skipped and only the missing tail runs. Combined with idempotent writes (upsert by natural key; re-running a step is a no-op, not a duplicate), a timed-out pass resumes instead of restarting.
- **Staged / incremental publishing.** Publish what has passed validation, in priority order, as a new snapshot version; keep serving the last good snapshot until the new one is complete (the canary/gradual-rollout principle in Google SRE release engineering, index). Freshness degrades gracefully and *visibly*, per card, instead of the whole board freezing.
- **Timeout budgeting (AWS Builders' Library, via secondary summaries, index).** Every remote call gets an explicit timeout; retries are bounded, backed off with jitter, and charged against a retry budget, all inside the caller's deadline — never an open-ended wait inside a batch step.

**Adoptable rules — Cadence**

1. Split the pass into three independently schedulable jobs with separate timeouts: `validate/expire existing cards` (minutes, highest priority) → `publish` → `compute new candidates`. **Publish-before-compute:** at each cadence tick, first expire/invalidate and re-publish the existing board from last validated state, *then* start new computation.
2. Budget the hour (example for a 60-minute cadence): publish step hard deadline = **10 minutes**, reserved and unborrowable; compute gets the remaining budget minus a 10-minute safety margin, and must checkpoint at least every 15 minutes. When the compute deadline hits, it stops and publishes its validated partial results (rule 4) instead of running on.
3. Every step is idempotent and checkpointed by `(pass_id, step, plan_id)`; a re-run skips SUCCESS steps. No step may hold a lock that blocks the publish job.
4. Partial publication is allowed, but labelled: cards from the current pass carry the new snapshot ID; not-yet-recomputed cards carry the previous snapshot ID + `Checked <time>` badge. Never mix snapshots silently (§3, rule 5 is satisfied by *badging*, not by blocking).
5. Alert on the publish SLA, not just on job failure: if no new snapshot has published within **1.5× the cadence interval**, page/alert and auto-serve the last good board with a visible “Delayed — last updated <time>” banner. A loud stale board beats a silently stale one.
6. Priority order inside compute: (1) invalidations/expiries of live cards, (2) price/status refresh of live cards, (3) new candidates in board-priority order, (4) backfill/research extras — so a timeout always sacrifices the least reader-critical work first.

**Strongest sources — §4**
- Google SRE Book, Ch. 22 *Addressing Cascading Failures* (deadlines & propagation) — https://sre.google/sre-book/addressing-cascading-failures/ (verified live, 2026-10-16)
- Apache Airflow docs (execution_timeout / dagrun_timeout / SLA) — https://airflow.apache.org/docs/apache-airflow/2.5.2/_api/airflow/models/dag/index.html (index)
- AWS Builders' Library, *Timeouts, retries, and backoff with jitter* — https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/ (index, via secondary citation)

### 5. Reward-to-Risk Disclosure & Target Conventions

**The maths that must be on the card**

- R:R here = reward-to-risk = (target − entry) ÷ (entry − stop) for a long. Its honest companion is the **breakeven win rate = 1 ÷ (1 + R)** (Ticksprout risk lesson and FastBull expectancy explainer, both index; same formula in TradingView education). Table every editor should internalise:

| R (to that target) | Breakeven win rate (pre-costs) |
|---|---|
| 0.35 | **74.1%** |
| 0.50 | 66.7% |
| 1.00 | 50.0% |
| 1.50 | 40.0% |
| 2.00 | 33.3% |
| 3.00 | 25.0% |

- Expectancy, not R:R alone, decides viability: `E = p·W − (1−p)·L − costs`. Sub-1 R:R is legitimate **only** in high-win-rate systems — e.g. defined-risk credit spreads, mean-reversion/first-target scalps, or a T1 that is a *partial* exit with the remainder running to a further target — and only when the publisher can show the realised win rate for that setup type comfortably exceeds breakeven (a prudent buffer is +10–15 points over breakeven, a convention cited in retail education, index — treat as proposed editorial buffer, not a standard).
- **Targets belong at structure, not at a ratio.** The honest-use literature is explicit in paraphrase: a target placed at a distance merely to manufacture an attractive ratio has an invented numerator; targets should sit at a level, structure or measured move (next resistance, base height, prior high), and R:R is then *reported*, not *engineered*. IBD's 20–25% profit zone is the complementary convention: it is derived from how far growth stocks historically travel after a proper base, not from stop arithmetic.
- **T1 vs final target.** Quoting only T1 R:R understates a multi-target plan; quoting only final-target R:R overstates what a reader who exits at T1 earns. Credible plans disclose both, plus the assumed split (e.g. “half at T1, half at T2”) so a blended R can be computed.
- **Targets are objectives, not orders.** Unless a resting limit order is actually being recommended, phrasing must be conditional and evaluative — “objective”, “zone to consider trimming”, “ desk reviews here” — not “sell at $X” as if execution were guaranteed, and never implying the price reaching T1 is the same as a fill at T1 (gaps, intraday spikes vs closes).

**Target spacing / materiality**

No exchange, broker or standard-setter publishes a universal minimum T1–T2 spacing — this was searched and not found. The defensible materiality tests are cost- and volatility-based (proposed rules 3–4 below): a target increment smaller than round-trip costs + typical spread/slippage, or smaller than normal noise (≈1 ATR of the timeframe), is not a distinct objective, it is noise dressed as precision.

**Adoptable rules — R:R & targets**

1. Every card prints, adjacent to each other: `Risk (entry→stop)`, `Reward to T1`, `R to T1`, `Reward to final target`, `R to final target`, and `Breakeven win rate at T1 = 1/(1+R₁)`. No R number appears without its breakeven win rate next to it.
2. Sub-1 flag: if R to T1 < 1.0, the card must carry a visible `Low reward-to-risk to first target` badge **and** one sentence of justification naming the mechanism (partial exit / high historical win rate / defined-risk spread) **and** the setup family's realised win rate + sample size, or the card does not publish. If R to the *final* target is also < 1.0 and no such evidence exists, do not publish the plan.
3. Materiality (proposed): publish T2 only if `T2 − T1 ≥ max(0.5 × risk distance, 1 × ATR(14) on the plan timeframe, 3 × estimated round-trip cost)`. Otherwise merge T1/T2 into a single target zone.
4. Targets must name their anchor in text (“T1 = prior high at $X”, “T2 = measured move / next resistance at $Y”). A target with no named anchor is treated as a §3 validation failure.
5. Phrasing standard: headings read `Profit objective (not an order)`; body copy uses “consider taking partial profits near…”, states the close-vs-intraday basis (“on a closing basis”), and notes that gaps can skip a target/stop entirely.
6. Track record by R bucket: the archive (§1) reports realised win rate and average R separately for sub-1-T1 plans, so the justification in rule 2 remains auditable; if realised win rate falls below breakeven + 5 points over a rolling 30-plan sample, sub-1 plans are suspended automatically (proposed threshold).

**Strongest sources — §5**
- Ticksprout, *Risk to reward, honestly* — http://ticksprout.com/learn/fx/risk-management/risk-to-reward-honestly/pdf (index)
- FastBull, *Why a High Risk-Reward Ratio Can Still Lose Money: Win Rate, Expectancy and Position Sizing* — https://www.fastbull.com/newsdetail/risk-reward-expectancy-win-rate-4386617_0 (index)
- IBD, *When to Take Profits* (20–25% zone anchored to the buy point) — https://www.investors.com/ibd-university/how-to-sell/taking-profits/ (verified live, 2026-10-16)

---

## Could not verify

- **A universal “closed ideas shown for N days” standard** — none found across TradingView, IBD, Fool or broker boards; §1 rule 5 (5 trading days + permanent archive) is a proposed house rule.
- **A universal minimum T1–T2 spacing or a ban on sub-1 R:R** — none found in broker/exchange education; §5 rules 3 and 6 are proposed, cost/ATR-based.
- **Whether any named signal service retires an idea solely because the publisher traded it** — no such policy found; regulation (FINRA 2241) instead mandates anti-front-running policies and disclosure, which §1 rule 6 follows.
- **dbt official model-contracts page and Dagster official freshness-policy page** were not retrieved directly in this run; the dbt/Great Expectations and Dagster claims rest on inspectable secondary/repo sources found via search (index only).
- tastytrade's 50%-profit / 21-DTE management conventions are widely cited in education but were verified here through secondary sources, not a single tastytrade primary page stating both numbers.

## Sources

All read 2026-10-16. “Verified live” = page opened and read in the research browser / text fetch; “index” = search-result text only.

- Google SRE, *Addressing Cascading Failures* — https://sre.google/sre-book/addressing-cascading-failures/ — verified live
- IBD, *When to Take Profits* — https://www.investors.com/ibd-university/how-to-sell/taking-profits/ — verified live
- tastytrade Support, *Reviewing Trade Details Before Sending an Order* — https://support.tastytrade.com/support/s/solutions/articles/43000528791 — verified live
- AWS Prescriptive Guidance, *Event sourcing* — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html — index / landing opened
- MQL5, *Signal Types, States, and Lifecycle* — https://www.mql5.com/en/blogs/post/767493 — index
- TradingView Support, *Publishing and updating ideas* — https://in.TradingView.com/support/solutions/43000591338-publishing-and-updating-ideas/ — index
- TradingView Support, *Why was my idea unsuggested?* (15-min edit lock, no deletion) — https://www.tradingview.com/support/solutions/43000630296-why-was-my-idea-unsuggested/ — index
- SEC, *FINRA Rule 2241 approval order* — https://www.sec.gov/rules/sro/finra/2015/34-75471.pdf — index
- GlobeNewswire, *IBD Products / Leaderboard & Cut List* — https://WWW.GLOBENEWSWIRE.COM/news-release/2018/04/02/1458552/0/en/IBD-Products-Significantly-Outperform-the-S-P-500.html — index
- IBD, *8-Week Hold Rule / sell rules summary* — https://www.investors.com/how-to-invest/investors-corner/how-to-invest-8-week-hold-rule-helps-latch-on-to-big-winners/ — index
- Nasdaq, *When to Take Profits If a Stock Rallies 20% (Leaderboard Cut List example)* — https://www.nasdaq.com/articles/when-take-profits-if-stock-rallies-20-2017-11-13 — index
- Motley Fool, *6 Conclusions After 200 Months of Stock Advisor Picks (transparent scorecard)* — https://fool.com/investing/2018/10/22/6-conclusions-weve-reached-after-200-months-of-sto.aspx — index
- TraderHQ, *IBD SwingTrader Review (buy zone / target / stop, 5–10 day holds)* — https://Traderhq.com/investors-business-daily-swingtrader-review-stock-trading-technical-analysis/ — index
- OIC via InvestorPlace, *Bull Call Spread* — https://investorplace.com/2011/03/options-strategies-bull-call-spread/ — index
- Investopedia, *Which Vertical Option Spread Should You Use?* — https://www.investopedia.com/articles/active-trading/032614/which-vertical-option-spread-should-you-use.asp — index
- Nasdaq, *Don't Let a Good Options Spread Expire (50% max-profit management, tastytrade)* — https://www.nasdaq.com/articles/dont-let-a-good-options-spread-expire — index
- Barchart, *Options Outlook (spread stop as % of premium; defined risk)* — https://www.barchart.com/story/news/7558869/options-outlook-calendar-spread-screener-results-for-october-14th — index
- dbt / Great Expectations test patterns repo — https://github.com/shiningflash/data-engineering-practice-problems/blob/HEAD/problems/089-great-expectations-vs-dbt-tests/solution.md — index
- *A Backfilled Provenance Record Is Not a Real One* — https://medium.com/@FrankGoortani/a-backfilled-provenance-record-is-not-a-real-one-585afe371a8c — index
- Apache Airflow docs, *DAG / task timeouts & SLA* — https://airflow.apache.org/docs/apache-airflow/2.5.2/_api/airflow/models/dag/index.html — index
- Ticksprout, *Risk to reward, honestly* — http://ticksprout.com/learn/fx/risk-management/risk-to-reward-honestly/pdf — index
- FastBull, *Risk-Reward, Win Rate & Expectancy* — https://www.fastbull.com/newsdetail/risk-reward-expectancy-win-rate-4386617_0 — index
- DayTradingToolkit, *Win Rate vs Risk Reward: Expectancy* — https://daytradingtoolkit.com/beginners-guide/win-rate-vs-risk-reward-expectancy — index
