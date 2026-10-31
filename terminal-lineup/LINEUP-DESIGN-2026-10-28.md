# The Lineup: 20 Free Terminal Tools

Designed 2026-10-28, after the REA master index (114,798 entries, 0 missing) and the corpus analysis landed. Count amended by the owner from 15 to 20 on 2026-10-28 ("Design 20").

## The rules every tool obeys

- **Free in full.** No paywalls, no signups, no logins. Product discipline, never monetization.
- **The useful tool standard.** Discrete (one clear job), valuable, seamless, attractive, easy and fun to use, low cognitive bandwidth, indispensable.
- **No padding.** A second face on a job already in the lineup does not count. Every tool below names the job no other tool in the lineup does.
- **Honesty is the product.** No component in the corpus has a validated predictive edge, so no tool claims one. Every figure carries its source, its as-of time, its coverage, and its forward grade. Empty states say plainly what is missing and why. No internal language on public surfaces.
- **The Record grades everything.** Every tool that publishes a call, a level, or a list writes it to the append-only ledger first, and its public grade at 1, 5, and 21 sessions is part of the tool, not an afterthought.
- **Build order follows live proof.** Waves below run in the analysis's order of decreasing live proof. One tool at a time, completely, before the next begins.

## Wave 1: the proven core (live today in the Morgue engine)

### 1. Morning Map
- **Job:** the pre-open positioning picture for SPY, QQQ, and IWM, in one glance.
- **Moment:** before the open, coffee in hand. **Question it answers:** where are the walls, the flip, and the dark pressure today?
- **Built from:** Morgue Map (net GEX, call/put walls, zero-gamma flip, per-ETF DIX plus constituent DIX at 0.4365 live-graded over 501 of 503 names). Each figure labelled by construction, chain coverage counted on the card.
- **Returns tomorrow because:** the map is redrawn every morning and yesterday's map gets graded in public.
- **Adopted inputs (Codex, 2026-10-28B):** (a) The morgue comparison output now carries the structured overlap report {dix_days, gex_days, minimum_each} (Codex f65f62ad32), adopted in our morgue's `vendor_check.compare` on 2026-10-28B with regression tests; the Map's DIX/GEX validation display uses that shape when it renders validation state. (b) SPECCED FOR BUILD (not built): the metadata-adapter boundary pattern (Codex f951ae5609 / cf62cc2f85) is the integration template for this tool's morgue panel: presence flags for the named feed sections, the feed's byte SHA-256, generation time and session date, and every eligibility (decision / performance / order) false, plus the registered source ID, rights, redistribution, allowed purposes and registry version displayed on the panel itself (Codex 4b146de93d). Completing proof named: a panel build whose rendered output is checked field-by-field against the adapter payload it consumed, with all eligibilities shown false on a real saved feed.

### 2. The Record
- **Job:** the public scoreboard. Every call this terminal has ever published, graded at fixed horizons, losers included, nothing edited.
- **Moment:** any time trust is the question. **Question it answers:** how have these tools actually done?
- **Built from:** Morgue scorecards plus the append-only ledger (novel mechanism N1, ledger-first public grading; no vendor in the corpus grades its own output this way).
- **Returns tomorrow because:** grades mature daily; immature calls show their first-grade date instead of a blank.

### 3. Qualified Board
- **Job:** the short list of names that passed a strict, explained gate today, with the named reason every qualifier and every failure qualified or failed.
- **Moment:** after the open, planning the day. **Question it answers:** what is actually worth a closer look, and why?
- **Built from:** Morgue Board over the 1,838-name universe (confluence config verbatim from its source, transforms labelled as ours). The card states plainly that the score does not rank returns; the gate's transparency is the product.
- **Returns tomorrow because:** the board turns over daily and its picks feed The Record.

### 4. Flow Tape
- **Job:** the intraday options-print tape, readable at a glance: heat, unusual prints, top positions, sentiment.
- **Moment:** during the session. **Question it answers:** where is the options money actually moving right now?
- **Built from:** Morgue Tape, fixture-proven scorer, with the dual-population Algo Score (novel mechanism N2): the same prints scored on the buys-only intake and on all prints, so the intake bias itself is a published figure. Coverage and the latest-quote side limitation printed on the card.
- **Returns tomorrow because:** it is live, and its tags get graded.

### 5. Golden Sweep Wire
- **Job:** one alert type only: golden sweeps, pushed as they happen, each with its outcome appended at fixed horizons.
- **Moment:** the instant it fires. **Question it answers:** a golden sweep just printed; what usually happened next, and what happened this time?
- **Built from:** the Tape's Golden Sweep tag plus The Record's grading loop. The 30-session decision date for this service was already set for 2026-12-08; the design holds that discipline: the Wire ships when its own ledger cohort is mature enough to show outcomes honestly.
- **Returns tomorrow because:** every alert carries a pending grade that resolves in public.

## Wave 2: the calculators (self-contained, no live feed needed)

### 6. Payoff Sketch
- **Job:** draw any multi-leg options spread's expiration payoff: profit and loss at every price, breakevens, capped or open tails.
- **Moment:** before placing a spread trade. **Question it answers:** what does this trade actually make or lose, and where?
- **Built from:** the payoff calculator proven 9 of 9 on hash-pinned fixtures, then built natively in the Morgue checklist build.
- **Adopted input (Codex, 2026-10-28B), SPECCED FOR BUILD (not built):** when this tool emits an evidence-contract record for a user scenario, it uses Codex's option-lab record shape (commit 3484d58a18) as the template: state `inferred`, source user/manual-input, ALL five clocks explicitly absent, each with a named missingReason, and a derived feature carrying implementation SHA-256 (hash of the pricing functions' source text), parameters SHA-256 and result SHA-256, run through validateObservation / validateFeatureRecord / assessDecisionEligibility / assessFeatureLineage with blockers rendered. Completing proof named: a fixture case in the contract fixture suite asserting both validations pass and eligibility fails closed with an "availability is not verified" blocker, exactly as Codex's EVIDENCE-option-strategy-contract-lineage case does. The oracle crosscheck (ADOPTION-PROGRESS, option-stack phase) already proved model parity; this note adds the lineage half only.
- **Returns tomorrow because:** it is the tool you open before every spread, and sketches are shareable links (no accounts).

### 7. Expected Move Map
- **Job:** the expected-move map for a name or index: the priced range, drawn day by day.
- **Moment:** before earnings, events, or any held position. **Question it answers:** how much move is already priced in?
- **Built from:** the 15.87 expected-move construction, fixture-pinned including its rounding pipeline. Labelled as a published construction, reproduced faithfully, not a desk invention.
- **Returns tomorrow because:** the map resets daily and its ranges get graded against realized moves.

### 8. The Screener
- **Job:** filter the universe by plain conditions (price, volume, volatility, trend) and get a clean, sortable list.
- **Moment:** idea hunting, any time. **Question it answers:** which names match my conditions right now?
- **Built from:** the Finviz-style filter subset from the checklist build, on our own data routes.
- **Returns tomorrow because:** saved screens are shareable links, and screen results can be sent to the Board's gate with one tap (the gate still decides).

### 9. Portfolio Builder
- **Job:** turn a list of tickers into a weighted portfolio sketch with its combined profile.
- **Moment:** when a watchlist becomes a plan. **Question it answers:** what does this basket look like as one position?
- **Built from:** the Danelfin-style Layer-B portfolio builder from the candidate calculators.
- **Returns tomorrow because:** baskets are living links that re-price daily.
- **Adopted gates (Codex):** the Danelfin point-in-time rebalance planner gates (evaluation 05 section 2 item 3) are the binding spec for this tool: refuse selection on snapshots older than 7 days, refuse on partial or undeclared snapshots, and never invent membership past the last snapshot.

### 10. Activity Profile
- **Job:** one ticker's options activity profile: where its flow concentrates, how unusual today is for this name.
- **Moment:** when a name starts moving. **Question it answers:** is this name's options activity actually unusual for it?
- **Built from:** the Bullflow-style activity profile candidate. Per-name baselines, not market-wide hype rankings.
- **Returns tomorrow because:** unusual-for-it is a daily question with a daily answer.

## Wave 3: the studies panes (what usually happens next, with n on every cell)

### 11. Gap-Fill Pane
- **Job:** for today's gap-ups and gap-downs, the historical record: how often gaps like this filled, and how fast.
- **Moment:** the first hour. **Question it answers:** do gaps like this one usually fill?
- **Built from:** Morgue studies gap-fill (live-graded n=186, fills=85 at first grading). Every cell carries its n; thin cells say so.

### 12. Opening Range Pane
- **Job:** the opening-range and initial-balance record: what usually follows a break of the first hour's range.
- **Moment:** late morning. **Question it answers:** when the opening range breaks, what has the rest of the day usually done?
- **Built from:** Morgue studies ORB/IB (live-graded n=186).

### 13. Earnings Drift Pane
- **Job:** for tonight's and last night's earnings names, the distribution of what the stock did in the days after similar reports.
- **Moment:** earnings season, morning and evening. **Question it answers:** after a report like this, what did the next 1, 5, and 21 sessions usually look like?
- **Built from:** Morgue studies earnings distributions (live-graded n=35; the pane shows the small n honestly until it grows).

### 14. Wall Check
- **Job:** grade the Map's walls and flip: when price reached a published wall, what happened next, split by market positioning sign.
- **Moment:** any time the Map is on screen. **Question it answers:** have these levels actually meant anything?
- **Built from:** the wall-validation harness, whose grading definitions are imported from the scorecards, never forked, with a parity test between the two. One wall number, one definition, everywhere.
- **Note:** this tool is where analysis conflict C2 lands; the studies-card wall path is cured or declared no-data before this ships.

## Wave 4: the second-look tools (novel combinations)

### 15. Squeeze Watch
- **Job:** the ranked squeeze-watch list: high short interest names scored on the published v6 formula, with the vendor's calibration printed as the vendor's.
- **Moment:** weekly scan, and whenever a name rips. **Question it answers:** which crowded shorts are actually coiled?
- **Built from:** the Squeeze pane (vendor-verbatim formula, gate edges fixture-tested). Borrow fee shows as honest no-data until a route exists. Its data route is the frailest in the lineup, so it ships with its coverage on its face.

### 16. Fear Day List
- **Job:** on fear days only, the list of names the fear-day evidence actually supports looking at. On calm days it says so and shows nothing.
- **Moment:** the mornings everyone else is panicking. **Question it answers:** is today a fear day, and if so, what has historically been worth attention on days like this?
- **Built from:** the fear-day research line (positive information coefficients across two eras in the cross-check record) plus the terminal's existing fear-day logic. An empty list on a calm day is the tool working, not failing.

### 17. Pullback Norm
- **Job:** find pullbacks that are deep or shallow compared to the stock's own history, not compared to a fixed band.
- **Moment:** scanning for entries in names you already like. **Question it answers:** is this dip actually big for this stock?
- **Built from:** the cross-check survivor candidate (novel candidate N10: pullback depth normalised by the stock's own norm). Labelled on its face as an unproven candidate, and every signal it publishes goes to The Record to be graded. This is the lineup's research instrument: it earns trust forward or it gets retired in public.

### 18. The Second Opinion
- **Job:** one ticker in, one honest count out: how many independent kinds of evidence actually support this name, with correlated sources discounted instead of stacked.
- **Moment:** when three tools seem to agree and you want to know if they are really one tool wearing three hats. **Question it answers:** how many separate reasons are there, really?
- **Built from:** evidence-family consensus discounting (novel mechanism N3). No vendor in the corpus discounts its own alerts for sharing an underlying primitive; this tool exists because ours will not pretend otherwise.
- **Adopted input (Codex, 2026-10-28):** Codex's SECOND-PASS false-consensus / dependency table is this tool's analytical core. It is saved as `specs/second-opinion-evidence-families.md` (Silicon blob 76cecd3a, sha256 verified identical to the local adopted copy) and groups apparent confirmations by shared primitive (price bars, options prints, modelled inventory, and the other families in the table) so a consensus view reports independent evidence families present, not vendor or alert counts.

### 19. The Receipts
- **Job:** tap any figure anywhere on the terminal and get its receipt: source, as-of time, coverage, method (observed, published, reproduced, or inferred), and its grade so far.
- **Moment:** the moment of doubt. **Question it answers:** where did this number come from, and should I trust it?
- **Built from:** the evidence and provenance layer (novel mechanism N4, the fail-closed eligibility contract) turned into a user-facing feature instead of plumbing. This is the trust surface for the other 19 tools, and it is a tool in its own right because verification is a job users actually have.
- **Adopted design (Codex, skeptical adoption, 2026-10-28):** Codex's evidence graph is adopted ONLY as its grouping view, as the design for this tool's lineage display. Stated plainly: this is a design and a grouping view, no engine consumes a graph, and the tool ships the view only when a tool actually emits the lineage it displays. No lineage display ships on lineage no tool has emitted.
- **Adopted display pattern (Codex, 2026-10-28B):** the explicit gate-line rendering from Codex f8a95f41fe: market-values included yes/no, availability evidence state, point-in-time validation state, and the decision / performance-claim / order-submission gates are each rendered as their own named line, none collapsed into a single status sentence. This is the display half of the evidence contract in Standard 2; our surfaces compute blockers from data (stricter than the static constants in Codex's adapter), but the named-line rendering is adopted as-is.

### 20. State Analogue
- **Job:** describe today's market state in five coordinates, find the historical days most like today, and show what came next.
- **Moment:** when the day feels familiar and you want the record, not a feeling. **Question it answers:** what happened after days like this one?
- **Built from:** the P_NN state-vector construction (recombined, honestly labelled). It ships on day one as an honest progress pane: history accrued so far against the 126 sessions it needs, and it becomes a full tool the day the floor is met. Shipping the counter instead of a fake answer is the lineup's honesty standard in miniature.

## What is deliberately not in the lineup

- **No forecast service.** The Forecast Factory's outputs ship only as a research note (what replicated, what died). 63 of 1,217 cells surviving replication is a finding, not a product.
- **Nothing built on the unbacked teardowns.** TheStrat and the big bundle dissections carry zero to near-zero test backing; no public tool stands on them.
- **No prediction claims anywhere.** The lineup sells nothing and promises nothing except this: every number shows its source, and every call gets graded in public.

## Build sequence

Wave 1 in order (1 to 5), then Wave 2 (6 to 10), then Wave 3 (11 to 14), then Wave 4 (15 to 20), with The Receipts' plumbing laid during Wave 1 so every later tool is born with receipts. One tool at a time, completely: live data, honest empty states, plain language, fast. The Record grades each tool from its first day live.
