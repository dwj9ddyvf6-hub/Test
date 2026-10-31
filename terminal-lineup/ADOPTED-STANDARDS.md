# ADOPTED STANDARDS — Terminal Lineup

Adopted 2026-10-28 by the owner's order: adopt whatever tools, processes and
ideas are good in Codex's (Ausar's) work, including items we are
skeptical about in labelled, honest form, never as more than they are.

Source of truth for what is good: `05-EVALUATION.md` (Codex review,
2026-10-28), sections 2, 3 and 7, as cited per standard below.
Attribution is to Codex's work. This document is our lineup's copy:
the standards below are standing lineup law for our artifacts, not a
claim about the state of Codex's tree.

---

## 1. GESTALT's seven design rules — standing lineup law

Source: Codex's GESTALT synthesis. Evaluation §2 item 7
(feeds The Record / The Receipts; described there as "a page of rules
we already run on").

These seven rules govern every lineup tool, in substance verbatim:

1. **Record-before-display.** The organizing object is a dated
   evidence record, not a vendor score. The record is written before
   anything is displayed from it.
2. **Measurement vs interpretation.** A measured value and an
   interpretation of it are different things, kept separate and
   labelled as such. Never present an interpretation as a measurement.
3. **Absence is not zero.** Missing data is not a zero value. Absence
   carries its own explicit state (see Standard 2).
4. **Coverage travels to the decision.** Whatever coverage, gaps, and
   limits a record carries travel with it to the decision that uses
   it. A decision surface never shows a cleaner picture than the
   record behind it.
5. **Fixed horizons.** Horizons are fixed in advance and stated. A
   result is not re-horizoned after the fact to make it look better.
6. **Correlated-evidence separation.** Evidence that shares a source
   or a primitive is not independent confirmation. Correlated
   evidence is separated and counted as what it is: one family, not
   many votes.
7. **Research is not order authority.** Research, however strong,
   does not by itself authorize an order. Order authority is a
   separate gate.

## 2. The evidence contract — the lineup's canonical trust layer

Source: Codex's evidence contract (EVIDENCE-CONTRACT v1.0.0 and
`evidence-contract.mjs`). Evaluation §2 item 5 (design A−,
integration B+; feeds the evidence/provenance layer, the shared trust
surface for Morning Map, The Record, Qualified Board and every other
tool) and §7 item 4 (adopt the contract as canonical, contract first,
emitters second).

Adopted terms:

- **Five clocks.** Time is carried as five first-class clock fields,
  not one timestamp. Note: the four-clock prose in older synthesis
  (GESTALT's canonical record and SECOND-PASS) is **superseded by
  five**. Evaluation §4 item 5 and §5 (conflict C14) establish this:
  the prose/display side saying four is the stale side; the contract
  implementing five is correct. Any lineup document or display still
  saying four clocks is stale and must be corrected to five.
- **Explicit absence states.** Absence is represented by named,
  explicit states, never by a blank, a default, or a zero.
- **`known_zero` strictness.** A zero counts as a known zero only
  under the contract's strict conditions (an explicit marker /
  declaration, probe-verified in the evaluation). No-print or no-data
  is not a known zero by default.
- **Fail-closed decision eligibility.** Decision eligibility is
  assessed fail-closed: a record that does not meet the contract is
  not decision-eligible, and its blockers are enumerated rather than
  waived.
- **Empty verified registry until a source is reviewed.** The
  verified registry (`verifiedRefs`) starts empty by design, so
  nothing can be decision-eligible yet. A source enters the registry
  only after it is actually reviewed. Adopting the contract does not
  make any tool an emitter of it: per Evaluation §2 item 5 and §3,
  no tool emits the contract yet, and no lineup claim may say
  otherwise until a named tool's output validates through the
  eligibility assessment with its blockers enumerated (§7 item 4
  proof standard).

## 3. Candidate-register triple — mandatory spec format for every remaining lineup build

Source: Codex's candidate register and registers' generation
discipline. Evaluation §2 item 8 and §7 item 7 ("Use the
candidate-register triple as the spec format for the remaining lineup
builds").

Every remaining lineup build's spec must be written, **before the
build starts**, in this triple:

1. **Evidence class** — what class of evidence the build rests on.
2. **Reconstruction choices** — every choice the desk made in
   reconstructing, stated as the desk's choice. Evaluation examples:
   Stock Rover percentile = desk reconstruction; Danelfin tie rules
   and 7-day freshness = local choices; OptionStrat models =
   clean-room, no parity claimed.
3. **Non-claims** — what the build explicitly does not claim.

A spec without all three, written before its build starts, is not a
lineup spec. Full semantic completion is stated honestly in the same
spirit: the registers state it as 0/86, and lineup specs state their
own completion the same way, never rounded up.

## 4. Zerith / DeepSeek source-audit method — standard for any future source-available family

Source: Codex's Zerith and DeepSeek source audits. Evaluation §2
item 10 and §4 (Phase 2 section, on the pinned-source state).

For any future family where source is available, the audit standard
is:

- **Pin the source.** Pin the exact blob or tag audited (worked
  examples: the Zerith blob exactly matching the 1,043-line local
  snapshot; DeepSeek pinned at tag v2.0.0). An unpinned audit is not
  an audit.
- **Falsifiable findings.** Findings are specific and falsifiable:
  named code, named behaviour, checkable by a reader against the
  pinned source.
- **Corrections with arithmetic shown.** Where an audit corrects a
  peer's published error, the correction shows its arithmetic
  (worked example: Zerith, 450 pips / 27.5 lot-pips ≈ $275,
  replacing 500 / $375+, recomputed exactly in the evaluation).
  A correction without shown arithmetic does not meet the standard.

This is the method exemplar for source-available families: deepening
that corrects the record instead of inflating it.

## 5. Rights-gate practice — where terms say do not build, one row saying why

Source: Codex's rights-gate practice (SpotGamma and Trade Ideas
rights gates; SOURCE-RIGHTS recheck). Evaluation §2 item 11 and
§§10–11 of the targets review as summarized in §2 item 11 (feeds the
gating step for every lineup tool that touches a rights-held family).

- Where a family's terms say **do not build**, the answer is **one
  row saying why** (worked examples: SpotGamma and Trade Ideas, each
  correctly a ~1-row gate).
- The conflict is **carried as an open conflict, never smoothed
  over** (worked example: the Arkham finding, public SaaS terms
  exclude bots/AI/ML while a hosted MCP is marketed, carried as an
  unresolved conflict).
- A rights gate is a complete, correct outcome for that family. It
  is not a gap to be filled by building anyway, and no lineup tool
  may route around it.

## 6. Do-not-adopt list — explicit

Source: Evaluation §7 item 10, verbatim in substance. These are not
adopted, and the labels below must survive into the consolidated
index and the lineup specs verbatim:

- **The static GEX lab's numbers** until its formula is fixed
  (Evaluation §3 and §4 item 1: its gamma loses moneyness decay,
  wrong by up to 2173× off-ATM, and its fixture certifies its own
  bug at the least sensitive point; walls, net GEX and the
  zero-gamma crossing from that lab are unreliable away from ATM).
- **Leadr candidates as anything but labelled worksheets**
  (Evaluation §3: worksheets, not evidence about Leadr; the
  authenticated score is server-computed).
- **The Stock Rover composite as a vendor score** (Evaluation §3:
  it is a desk reconstruction, not Stock Rover's score; everything
  past the midrank ranking is declared desk invention).
- **Scoped row counts as coverage** (Evaluation §3: scoped
  requirement rows are a template output, not coverage; 683 of 735
  scoped rows are explicit GAPs, so the register is predominantly a
  map of what is not known or built).
- **Any "terminal is live" sentence that does not name which
  terminal** (Evaluation §3: every non-lab screen of Codex's
  terminal app is a synthetic, honestly labelled demo, and that app
  does not consume Morgue output; corpus conflict C15).

---

## Addendum (2026-10-28, spec-upgrades phase) — skeptical adoptions, labelled

### A. Evidence graph — grouping view only

Source: Evaluation §3 and §5 (novelty N3 downgrade) and 02-SYNTHESIS-REVIEW §8.
Adopted only as a design and a grouping view for The Receipts' (tool 19)
lineage display, as recorded in that tool's design section. No engine
consumes a graph; no persisted lineage DAG exists; no lineup claim may
describe a graph engine, and the view ships only when a tool actually
emits the lineage it displays.

### B. Leadr worksheets — internal diagnostics only, never public claims

Source: Evaluation §3 (both Leadr candidates are worksheets, not evidence
about Leadr) and §7 item 10; 02-SYNTHESIS-REVIEW §§3–4.
Codex's 55-field metadata worksheet and the v3Effective candidate
(17 leaves, 14 computable, market-context category permanently no-data)
are adopted ONLY as labelled diagnostic worksheets for the Qualified
Board's internal build process. Labels required on any use, verbatim in
substance: "labelled diagnostic worksheet", "not Leadr's server score",
and "the authenticated Leadr score is server-computed". Neither worksheet
may be presented as a public claim about Leadr's server score, a
demonstrated Leadr scoring formula, or evidence about Leadr. The 55-field
table's 60% coverage floor is, in the source code's own words, not
established for that table, and any use must carry that note too.

### C. Scoped requirement rows — work queue only, with the evidence-class column

Source: Evaluation §3, §7 item 9, and 04-TARGETS-REVIEW open item 2.
Codex's scoped requirement register is adopted into our work queue ONLY
with the evidence-class column added (source-pinned / docs-rich /
docs-only / boundary-only / rights-gate), as defined in
`specs/evidence-class-column.md`, which is the binding format for any
future aggregation. Scoped row counts are not coverage (see section 6).

## Addendum (2026-10-28B) — Codex new commits, adopted patterns

Source: CODEX-NEW-20261028B analysis of Codex commits f65f62ad32 through
b44e2eac32 (Silicon main, 2026-10-28). Only items graded strong or sound
in that analysis are adopted here; mechanical items are not.

### D. Startup self-check for contract consumers (cf62cc2f85, sound)

A consumer of the evidence contract or a source registry refuses to
start unless its registry entry matches its declared posture (for the
morgue metadata adapter: entry present, rights unknown, ingestion
metadata-only). Registry binding is enforced at module load, not by
documentation. The `morgue.local-snapshot` registry entry itself is
adopted into our registry copy when our morgue panel lands (specced in
the Morning Map adopted-input note), not before.

### E. Override ledger for generated registers (4b146de93d / f81962869d, sound / strong)

Hand triage of a generated register lives in a durable override ledger
that the generator consumes and validates on regeneration (path must be
an indexed row, no duplicates, disposition fields non-empty), so a human
decision survives rebuilds instead of being edited into generated
output. Adopted for the REA master index as
`~/workspace/rea-master-index/TRIAGE-OVERRIDES.csv`. One correction to
Codex's implementation is adopted WITH the pattern: disposition fields
allow an explicit `not_applicable` value. Codex's strictly-boolean
validator forced a repository-configuration file's row to claim
rights_checked and implementation_mapped true where both were
not applicable (labelling flaw named in the analysis); our ledger does
not repeat it.

### F. Minimum-evidence-to-resume table (f8a95f41fe, sound)

Every blocked family in the REA index carries, next to its blocked
state, the exact resumption artifact: the concrete evidence that would
unblock it, named as an artifact, not a sentiment. A blocked row
without its resumption artifact named is incomplete.

### G. Per-row evidence_limit on mapping artifacts (b44e2eac32, sound)

A crosswalk or mapping artifact carries its non-claim on every row
(an `evidence_limit` column), not only in a header. A mapping
establishes neither contents nor rights unless a row's own evidence
says so.

### H. Metadata-adapter boundary pattern (f951ae5609, strong)

The first integration slice between a data engine and a terminal
surface carries metadata only: presence flags for named sections, a
byte hash, generation time and session date, with rights and
availability unknown, point-in-time not run, and decision /
performance / order eligibilities all false, in code. Values move
only when their own evidence contract passes. Specced for the
Morning Map morgue panel (LINEUP-DESIGN tool 1 note).

### I. Curated-row counting (3484d58a18, strong)

Register counts count only curated, source-anchored rows, never
generator-templated rows. Codex deflated his own unified index from
752 rows / 52 families to 31 rows / 11 families on this principle
(9 bounded candidates + 8 OptionStrat public-surface + 14 scoped
curated records). Applied to our master index: aggregations cite
curated rows only, and the codex-delta files record file-level units
one by one, never templated expansions.

### J. Current REA denominator (f65f62ad32, sound, scope half strong)

The active REA scope denominator is 100 passes / 86 families
(Wave 1: 23, Wave 2: 52, pre-sweep: 25; 12 repeat families account
for the 14 extra passes). The 99-pass and 94-complete figures are
dated predecessors, kept in the record as such, not current counts.

## Standing note on proof

Per InfinityBlade and Evaluation §7's proof standard: an adoption in
this document is a standard for our builds, proven only when a named
lineup artifact is checked against it on its final state. This
document's existence proves the standards were written down; each
build's compliance is proven on that build, not inherited from here.

---

## Addendum (2026-10-28) — No disclaimer copy

NO DISCLAIMER COPY (the owner, 2026-10-28): no disclaimer-style copy on any reader surface of any tool, in pages or generated data, ever. Factual state (dates, coverage, completeness, grading state, no-data states) is information, not a disclaimer, and stays. Every future build brief carries this rule.

## Addendum (2026-10-29, deep pass 3.2 items 8, 9, 12): diagnostics and audit patterns

### K. Source clock as a data arrival diagnostic (3.2 item 8, M12)

Our refresh fleet carries a source clock in
`forecast/diagnostics_patterns.py`, run by
`site/source_clock_diagnostic.py` over refresh runner logs and
written to `site/source-clock/data.json`. It prints, per source, a
freshness expectation (Laplace smoothed arrival frequency with a
Wilson interval, pooled exact source, then source family, then
refused), labelled as a data arrival diagnostic and never a market
forecast. It is not ledgered and not graded. His flaw is fixed on
import: when the estimate is refused for insufficient history, the
interval is suppressed with the estimate. A history row whose label
timing contradicts its declared horizon kills the whole estimate.

### L. Boundary map sweeps as the parity standard (3.2 item 9, M10, M15)

Parity for any scorer mirror is proven by boundary sweeps through
both implementations (`boundary_sweep`, `parity_sweep` in
`forecast/diagnostics_patterns.py`): one feature corners, pairwise
corners and joint corners, including clip regions, zero branches and
passed event style branches. One synthetic interior vector never
counts as parity. Any new multiplicative scorer ships with its
corner map reviewed before publication; `site/boundary_check.py`
runs the standing check over the FE17 centre adopted for Engine 12.
An abstained baseline produces no map at all.

### M. Confluence renormalisation discipline (3.2 item 12, L01)

Any composite score that renormalises over present inputs prints
coverage beside the score in the same visual weight, and coverage
floors are computed on weight, not count. The shared implementation
is `renormalised_composite` and `format_score_with_coverage` in
`forecast/diagnostics_patterns.py`. Wired surfaces: the Qualified
Board (coverage in the same strong element as the score, with the
70 percent floor carried as data) and the Living Router, Engine 18
(coverage weight on every published contested row, in the ledger
value and in a table column of the same weight as the chances).
Audit of the other named surfaces: Engine 17 applies a fixed shape
multiplier and Engine 20 ranks by graded error; neither renormalises
a composite over present inputs, so neither gains a coverage field
until the day one does.

## Addendum (2026-10-29, deep pass 3.2 items 10, 11, 14): guard, panel discount, HAR control

### N. FE12 session quality guard (3.2 item 10)

A one sided liquidity deterioration flag, never an engine and
never a probability: every input enters as max(0, value), the
scale is graded (no sigmoid, whose saturation the source read
flagged), and his intercept and weights are not imported. The
shared form is `fe12_session_quality_guard` in
`site/engine_adaptations.py`, consumed as a band widener
(`fe12_widen_band`, and `bands_for` in
`refresh_correctedband.py`) and as an abstention raiser
(`fe12_abstention_threshold`). Missing inputs are named and
never zero filled; with no supplied inputs the guard is
not_recorded and changes nothing.

### O. FE20 panel reliability discount (3.2 item 11)

The standard discount for panel derived inputs is
`fe20_panel_reliability` in `site/engine_adaptations.py`:
stability times coverage over 1 plus abs drift, applied by
`fe20_discounted`. First applications: the 13F holder counts
and the dark print combined aggregate, each publishing a
panel_reliability block in its data file and recording panel
composition snapshots (13f-tracker/panel-history.json,
dark-prints/panel-history.json) so a drift series can be
built. While a panel's drift leg has no series, its
reliability is not_recorded and its inputs are published raw,
never discounted under an invented number.

### P. FE08 HAR control on QLIKE (3.2 item 14)

Engines 1 and 7 are graded against the FE08 fixed weight HAR
form (0.50 log rv 1, 0.30 log rv 5, 0.20 log rv 22) as a
control column on QLIKE, in `har_control_report` in
`forecast/grading.py`, printed by `forecast/run_grading.py`
beside the paired baseline report. The control is a baseline
to beat, not a forecast; the engine variance equivalents are
stated in the grading module (Engine 7: median realised vol
quantile squared; Engine 1: 68 percent band half width,
annualised).

## Addendum (2026-10-29, deep pass 3.2 items 13 and 15): static GEX cross check, FE research registry

### Q. Static GEX single convention cross check (3.2 item 13)

One transparent convention, computed from our own chain
snapshots and published beside the modelled inventory surfaces,
never instead of them: calls positive, puts negative, dollar
figure gamma times sign times open interest times 100 times
spot squared times 0.01, walls from the per strike totals, and
the flip level from a 101 point grid with each contract's
implied volatility held constant across the grid. The constant
IV assumption is stated wherever the flip is printed, and every
flip carries an IV sensitivity band (the grid rerun at 0.80x
and 1.25x every volatility). A contract counts only with both
open interest and implied volatility on the snapshot; the rest
are excluded and counted. The shared implementation is
`static_gex_snapshot` in `site/static_gex.py`, refreshed by
`site/refresh_staticgex.py` into `site/static-gex/`, which also
prints the modelled ladder's flip beside the static flip and
the difference between them, unresolved by design.

### R. New territory FE engines as registry research questions (3.2 item 15)

FE01, FE05, FE21, FE25, FE19 and FE07 live in
`forecast/registry.json` under `research_questions`, in that
first pass order, each with its statement, its data routes with
an honest existing, partial or absent status, and the decision
rule that could promote it. They are not engines: nothing in
the registry grades them and no forecast issues under them.
FE02's Hurst gate and FE06's sector diffusion damper are
admitted only as conditioner candidates on named engines
(Engines 3 and 9; Engines 17 and 18), recorded and not wired
until their missing estimators and specifications exist. FE27's
reaction sign is adopted as an input form for Engine 24 cohort
definitions (caller supplied cycle_reaction_sign and
regime_confidence, declared at issuance); FE27 itself is not
adopted while its horizon contradiction stands. The registry
validator enforces the entry shape, the conditioner targets
and the form's engine binding.

## Addendum S (2026-10-29, deep pass 3.2 item 2): Aperture proof gate, hardened

A name earns a proof state from its own episode history under
one frozen rule, aperture_episode_rule_v1, carried per engine
in forecast/registry.json on Engines 19 and 20 and nowhere
else: the entry condition, episode spacing, friction, split
and thresholds change only by changing the registry. Every
state the gate prints is provisional, in the gate's own
output, in site/proof-gate/data.json and on every scanner
surface (the display string is "PROVISIONAL <state>", never
the bare state). No name may print SUPPORTED until its
episode record survives a Benjamini-Hochberg correction
across the whole scanned universe at the frozen alpha; a raw
pass that fails the correction prints MIXED with its reason.
Every scan ledgers one forward record per name under Engine
19, graded from the realised forward return when the horizon
has traded, so a provisional state is a claim the record later
checks, not a verdict. The implementation is
forecast/proof_gate.py, refreshed by
site/refresh_proofgate.py, which streams the DEEP panel
symbol by symbol and never loads it whole.
