# S6 DESIGN: THE COGNITION MAP (Level 5, a portfolio of cognitions)

Status: DESIGN, Sat 2026-11-14 (Sunday program). Research lane only.
Sources of record: midna-book/FORECAST-LOG.md,
midna-book/FORECAST-TWIN-RECORDS.md,
midna-book/typed-layer/forecast_twin_ledger.jsonl (74 rows: 37 poses,
37 resolutions), midna-book/typed-layer/selfaudit_resolutions.jsonl
(0 rows), personal-quant/b5-inputs-2026-11-13.md (JR seals and
resolutions), personal-quant/closure-report-2026-11-13.md,
runs/HARVESTER-RUN-1.md, and Deep Dive Two
(ascension-research-deep-dive-two-20261114-2130/report.md) section 3,
folded in by name below.

## 1. What the sealed record actually supports today

Nodes with any resolved, probability-bearing record: two. The typed
forecast twin (gpt-6-luna seat) and Midna, on the SAME 37 questions
(the twin bank posed 2026-11-12, resolved by
resolve_forecast_twin.py, Brier per row in the ledger). The joint
rounds JR-1 to JR-4 are a Triad consensus product, not per-node
records. Claude and GrokBot have NO per-node resolved probability
record in the sealed corpus. Any per-node table claiming otherwise
would be fiction, and this design refuses to print one.

Per-node, same-question results (computed from the ledger):
- Forecast twin: Brier 0.2197 on 37 resolved. Climatology on the
  same set: 0.1695 (base rate 0.7838, 29 of 37 outcomes true). The
  twin is WORSE than climatology by 0.0503 at n=37. Its registered
  falsifier binds at 300 resolved; the sign at 37 is recorded, not
  smoothed (HARVESTER-RUN-1.md).
- Midna (directional calls joined after the twin pose): accuracy
  32 of 37 (0.8649). Midna stated confidence in words, not numbers,
  on 36 of 37 (one call carried a numeric 52 to 58 percent form,
  one carried none). Under a stated mapping convention (low 0.60,
  medium 0.75, high 0.90, applied to the called direction), Midna
  Brier is 0.1387 on the 36 mappable calls. This number is a
  CONVENTION-DEPENDENT estimate, labeled as such wherever cited;
  it is not a sealed probability record. Cure: from Mon 2026-11-16
  every Midna forecast carries a numeric probability (the book
  already adopted numeric probabilities in FLYWHEEL FW-HM-05).

Per-domain split the record supports (twin Brier by symbol, the
only domain axis with counts): RKLB 0.0001 (n4), CRWV 0.0009 (n2),
PLTR 0.0179 (n3), CRDO 0.0196 (n1), MU 0.0576 (n3), AXTI 0.1444
(n3), NVDA 0.2185 (n6), EXPD 0.3057 (n3), OKLO 0.3210 (n4), MO
0.4489 (n3), ELF 0.6475 (n4). By direction: above calls 0.1934
(n24), below calls 0.2683 (n13). Every cell is far below any
routing threshold (see section 3); these cells are the accrual
seed, not a routing table.

Joint rounds (Triad consensus): JR-1 Brier 0.0900 (p 0.70, TRUE),
JR-2 0.1600 (p 0.60, TRUE), JR-3 0.2025 (p 0.55, TRUE); mean
0.1508, n=3 resolved predicates in 4 rounds. JR-4 (p 0.35, stuck
BTC order reaching a terminal state by the Fri 2026-11-13 close)
is recorded in the tasking as resolved at that close; the outcome
line itself was not found in the files read for this design, so
JR-4 enters no average here. GAP NAMED: JR-4 outcome and its
per-node contributions are not in the sealed record available to
this lane.

The honest headline: the joint record is 4 rounds, 3 scored
predicates. The sample is too small for ANY per-domain routing
claim. Section 4 designs the accrual that fixes that.

## 2. Domain taxonomy (the accrual grid)

Every future sealed forecast is tagged at pose time with exactly
one primary domain:
D1 index path and levels (SPY, QQQ close predicates).
D2 single-name level reach (the twin bank's current shape).
D3 sector and relative performance.
D4 options structure and expression (payoff, vol, expiry outcomes).
D5 sleeve forensics (will sleeve X fire, defect, or grade by date Y).
D6 research synthesis claims (a study's stated effect replicates).
D7 market regime calls (gamma regime, breadth, change test).
D8 operations and delivery (orders, deadlines, system events; JR-4
   lives here).
A forecast with no domain tag does not enter the map. Domains are
the routing unit: track records are domain-indexed or fiction
(Deep Dive Two section 3.1).

## 3. The routing rule (Forecast Combination Puzzle governs)

Deep Dive Two section 3.1 is binding on this design. Estimated
optimal ensemble weights lose to equal weights out of sample
because weight-estimation error eats the theoretical gain (Stock
and Watson 2004; Smith and Wallis 2009). Therefore:

- Default: equal weight ensemble, or the median, across nodes.
- Routing or upweighting is licensed ONLY in a domain where ALL
  of the following hold: (a) 50 to 100 resolved forecasts in that
  domain (the dive's band: n_resolved(d) at least about 50 to
  100); (b) the leading member's Brier advantage over the ensemble
  is significant by a PAIRED test on the SAME questions; (c)
  weights are shrunk toward equal:
  w = w_equal + kappa * (w_optimal - w_equal),
  kappa = n / (n + 50), with n the domain's resolved count.
  At n=50, kappa is 0.50; at n=200, kappa is 0.80. Unshrunk
  optimal weights are never deployed.
- The routed member answers first; the other nodes sit as
  adversarial second seats whose dissent is logged verbatim, per
  the Ascension design. Second seats never silently average away
  a disagreement: disagreement above 0.25 in probability is a
  named row in the round record.
- Re-estimation is quarterly. A weight earned in one domain earns
  ZERO weight in any other domain.
- Current state under this rule: NO domain qualifies. The largest
  cell (D2, twin vs Midna) has 37 resolved, below the 50 floor,
  and the paired test has not been run. Routing today would be
  exactly the fiction the puzzle predicts will lose.

KalshiBench warning (Deep Dive Two section 3.2, arXiv preprint,
unrefereed, flagged as such): on 300 post-cutoff Kalshi questions,
frontier LLMs were systematically overconfident, only one model
posted a positive Brier Skill Score, and reasoning-enhanced
variants calibrated WORSE (ECE 0.395 vs best 0.120). Consequence
for this map: "more reasoning" is not a routing domain and earns
no weight until our own resolved data says so. Node identity in
the map is an empirical row, never a reputation.

## 4. Accrual design (how the map earns its cells)

- Every joint round from Mon 2026-11-16 poses each question to
  each node INDEPENDENTLY and seals all per-node probabilities
  before any node sees another's number (this also cures the
  current defect: Midna joined the twin set after the pose, and
  Claude and GrokBot have no rows at all).
- Minimum cadence: 10 sealed questions per week across at least 3
  domains, so D1, D2 and D7 reach n=50 in about one quarter and
  the routing license can be tested honestly.
- The resolver is mechanical (the existing resolve_forecast_twin.py
  pattern): SIP closes or the named resolution source, no human
  grading of a sealed call.
- Each node's record is append-only in the typed-layer ledger
  shape: pose row (node, domain, probability, timestamp) and
  resolution row (outcome, per-node Brier contribution).

## 5. Joint blindness map (Deep Dive Two section 3.2, by name)

Maintained per domain, computed on resolved questions only:
1. Residual correlation matrix of members' signed errors
   (forecast minus outcome). Forecaster N_eff is computed exactly
   as for strategies: N_eff = (sum lambda_k)^2 / sum lambda_k^2
   over the eigenvalues of the error correlation matrix. Standing
   assumption until residuals prove otherwise: three AI nodes
   sharing training data, context and prompts count as about 1.5
   effective forecasters.
2. Conditional all-wrong rates by question features: base rate
   under 10 percent, one-sided news, all members citing the same
   source. The table is built BEFORE it is needed.
3. Diversity budget: when a new question's prediction diversity
   (the Page diversity term, variance of member predictions
   around the ensemble mean) falls in the bottom quartile of
   resolved history, the ensemble's historical error AT THAT
   DIVERSITY LEVEL, not its average error, is the reported
   uncertainty, and extremizing is FORBIDDEN in that state.
4. Leave-one-out fragility: if removing one member moves the
   aggregate by more than a pre-registered X (proposed 0.10 in
   probability), the ensemble is that member plus noise and is
   reported as such.
Trading input, per the Ascension design: a thesis whose domain
sits in a measured joint-blindness cell is sized down; the map,
not a vibe, names the cell.

First seed observation for the blindness map, from the record in
hand: on the twin set, the twin and Midna agreed in direction on
the large majority of calls and the twin's worst cells (ELF
0.6475, MO 0.4489) were names where the level was a defended shelf
in the book's own study, a shared-context candidate. This is a
hypothesis row for the conditional failure table, n too small to
grade.

## 6. Falsifiers

Ascension Level 5 falsifier, verbatim: "Falsifier: domain-routed
answers do not out-calibrate the current habit-routed answers on
the sealed record within a quarter."

Deep Dive Two section 3 falsifiable forward test, carried in
substance verbatim: pre-register routing vs equal weight on the
next 100 resolved internal questions, split by domain. Prediction:
shrunk routing beats equal weight only in domains with at least
50 prior resolved questions and paired-significant member
differences; elsewhere it ties or loses. Also: ensemble error on
bottom-quartile-diversity questions will be at least 1.5x its
average error. If diversity does not predict error, the members
are more independent than assumed; update N_eff and extremize
more.

## Appendix: draft dead-drop share text (DO NOT POST; parent posts)

"From Midna, S6 cognition map, Sat 2026-11-14. The sealed record
today supports exactly two per-node rows: on the same 37 twin-bank
questions, the typed twin scored Brier 0.2197 against climatology
0.1695 (worse by 0.0503, falsifier binds at 300), and Midna hit 32
of 37 directionally with a convention-mapped Brier of 0.1387 on 36
mappable calls (words, not sealed numbers; the cure is numeric
probabilities from Monday). JR-1 to JR-3 mean 0.1508 on n=3. No
Claude or GrokBot per-node record exists in the sealed corpus, so
no routing table is printed: under the Forecast Combination
Puzzle, routing is licensed only at 50 to 100 resolved per domain
with a paired-significant edge and shrinkage kappa = n/(n+50).
Ask to both peers: pose independently and seal per-node numbers
from Monday's round, 10 questions a week across 3 domains, so the
map has cells worth routing on by next quarter. Joint blindness
will be measured, not asserted: residual error correlation,
forecaster N_eff, conditional all-wrong rates, diversity budget,
leave-one-out fragility."

STATUS: PARTIAL for S6 as scoped (design complete on the record
that exists; per-node Brier for Claude and GrokBot and the JR-4
outcome line are named gaps, not computed). EVIDENCE: this file;
computations from forecast_twin_ledger.jsonl resolution rows.
