# Turn this repository into useful work

Test is a domain library: strategy contracts, source code, research, engineering
examples, evidence and preserved packages. Use it to produce an answer, a
reproduction, a comparison or a well-supported improvement. The separate
[InfinityBlade Engineering Doctrine](https://github.com/dwj9ddyvf6-hub/InfinityBlade-Engineering-Doctrine)
is the operating-discipline repository. Its entry instructions govern how to
study that doctrine; Test supplies domain material and runnable examples. Keep
their roles distinct and use them together when the task needs both.

The practical loop is **question → authoritative source → worked example →
appropriate check → useful deliverable**. This guide makes that loop concrete.
It adds routes into the collection; it does not replace or abridge its studies,
strategies, archives or operating instructions.

## Start with an outcome

Follow [AGENTS.md](../AGENTS.md), [START-HERE.md](../START-HERE.md),
[INDEX.md](../INDEX.md), the relevant [ROADMAP](../ROADMAP.md) section and the
area's README or AREA.md. For the paper-desk kit, also read its nested
[AGENTS.md](../agentic-trade-desk/AGENTS.md). Then write a compact task contract:

```text
Question: What should this work let the reader understand or do?
Deliverable: The answer, comparison, patch, notebook or reproduction to produce.
Source boundary: Which repo revision, package version and observation dates?
Constraints: Which behavior, evidence, private information and permissions remain intact?
Acceptance: What observation would demonstrate the requested result?
```

For example: “Explain and reproduce the supplied toy desk in an isolated local
directory; return exact test/example outcomes and the source revision; preserve
all strategy rules and use only the frozen fixtures.” This is immediately
executable. “Understand everything and make it better” first needs a set of
such observable outcomes, each retaining its place in the larger task.

## Retrieve a small source bundle, then expand deliberately

[REPOSITORY-MAP.json](REPOSITORY-MAP.json) is the curated task map.
[INDEX.json](../INDEX.json) is the generated path inventory. The
[navigator](../tools/repo_navigator.py) joins task routes with exact file reads;
it does not run commands found in the material.

From the repository root:

```bash
python3 tools/repo_navigator.py route "build an offline paper desk"
python3 tools/repo_navigator.py packet build-offline-desk --max-chars 18000
python3 tools/repo_navigator.py search teddy --content --limit 12
python3 tools/repo_navigator.py read docs/TEDDY_ORB_SPY-RECREATE.md --start-line 1 --lines 70
```

The default reads the committed `HEAD` tree. Use global `--ref COMMIT` before
the subcommand to reproduce another revision, or `--worktree` to inspect tracked
and staged working files while editing. Newly created files must be staged to
enter that worktree inventory. A packet's character limit can omit or truncate
sources; inspect its coverage metadata and read the required remainder before
speaking for a whole source. The tool exposes source hashes and line ranges so
the next reader can verify what supported the answer.

A good bundle contains the task's entry guide, the actual contract or
implementation, and its relevant evidence. Expand on a named uncertainty:
“Which adapter persists this state?” is a reason to load another file. Loading
every package into the prompt is not a substitute for resolving that question.
The full archive remains available for deeper work.

## Choose the route by the output you need

| Desired output | Route ID | Useful result |
|---|---|---|
| Explain one strategy accurately | `explain-strategy` | Rules, provenance, exact source locations and what remains unproven |
| Recreate a strategy in another system | `recreate-strategy` | Contract, required inputs, dependencies, fixtures and explicit mismatches |
| Reconcile roster, catalog and source | `reconcile-strategy-catalogs` | Entity-by-entity correspondence with snapshot dates and version differences |
| Find dispersed Tensor material | `trace-tensor` | Relevant modules, adapters, recreation guides and package variants |
| Build a runnable offline desk | `build-offline-desk` | Clean-copy receipt, working toy and a next implementation slice |
| Understand terminal forecasts | `forecast-terminal` | Design, implementation, issuing/grading lineage and bounded evidence |
| Reuse forecast math on supplied inputs | `forecast-numeric-kernels` | Explicit input contract and reproducible offline calculation |
| Study chart reading and practice it | `study-chart-reading`, `practice-chart-reading` | Source-linked method plus a separately graded exercise |
| Distinguish psychology systems | `psychology-research`, `psychology-nine-gauge` | Correct package, version, evidence model and integration boundary |
| Improve an agent workflow | `study-agent-methods`, `study-enhancement-history`, `study-second-brain` | A sourced mechanism, local experiment and measurable acceptance |
| Assess a research claim | `assess-research-claim`, `verify-evidence` | Claim-specific evidence, denominator, clocks and remaining uncertainty |
| Inspect what a published terminal shows | `inspect-published-snapshot`, `explore-terminal-tools` | Displayed value → JSON producer → source/as-of chain |
| Compare a contributed package | `resolve-package-provenance` | Version, representation, license/provenance, dependencies and equivalence boundary |
| Continue trader education | `learn-trader-craft` | Attributed principles, competing evidence and a concrete practice plan |
| Investigate a missing item | `find-missing-material` | Recorded searches, aliases, archives inspected and unresolved locations |

These are starting routes, not claims that every file within a family is
interchangeable. Read the selected package's own entry point before borrowing
its commands, assumptions or verification results.

## Keep three questions separate: authority, capability and evidence

Authority asks which source governs the claim. Capability asks what the artifact
actually implements. Evidence asks what was observed, on which inputs and at
which time. A more detailed document does not automatically outrank a source
contract; a newer copy does not silently supersede a frozen version.

| Artifact | What it can establish | What still needs another source or check |
|---|---|---|
| Strategy card or catalog row | Recorded identity, summary and source pointers | Full algorithm, current deployment and performance |
| Frozen spec or recreation guide | Intended rules and the stated reproduction contract | Agreement with code, completeness of dependencies and present execution |
| Source module | The behavior implemented in that exact version | That dependencies exist, the module runs or a service uses it |
| Offline fixture/test receipt | The exercised behavior on the named inputs and source | Untested cases, real data behavior, operational continuity and edge |
| Research report with citations | The report's argument and attributed evidence | Independent reproduction and applicability to a different task |
| Copied config, terminal JSON or ledger | The captured values and their recorded as-of context | The current state of the original machine or account |
| Historical deployment/install receipt | What its recorded verification observed at that time | That the deployment still exists or remains healthy |

Use precise capability descriptions: **design**, **source available**, **offline
example**, **research-only calculation**, **source-bound observation**,
**simulated book**, **broker-paper operation** and **real-money operation** are
different states. They are not a ladder that every artifact must climb. A
research library can be complete and valuable at its intended boundary.

When spec and implementation disagree, state both. Source code establishes
implemented behavior; the applicable requirement establishes intended behavior.
Resolve the discrepancy at the appropriate layer, preserving the evidence that
made the discrepancy visible. Do not silently change an algorithm to make a
summary true.

## Worked route: reproduce the offline desk

Read the kit's [README](../agentic-trade-desk/README.md),
[setup](../agentic-trade-desk/docs/03_setup_step_by_step.md) and
[worked example](../agentic-trade-desk/docs/13_worked_example.md), after its
nested AGENTS.md. Then run this from the Test root:

```bash
python3 agentic-trade-desk/skeleton/tools/check_onboarding.py
```

The checker exports `deskkit/`, `tests/` and `examples/` to a temporary directory,
imports the exported package, runs a nonzero suite and checks the frozen toy.
It strips inherited credentials and blocks socket/child-process activity inside
the reviewed test/example process. The guard is not a security sandbox for
arbitrary code. The receipt includes the exact copied source hashes.

At the version introducing this guide, the expected observations are 23 tests
with no failures, errors or skips; twelve toy passes; one entry and one exit;
zero orders on the six simulated restart passes; a flat final book; and a valid
ledger chain. If the suite grows, use the discovered count and source hashes
from the new receipt instead of preserving a stale headline.

Deliver a small reproduction record:

```text
Source: <commit and source_manifest_sha256 from the actual run>
Observed: <actual test counts and toy outcomes>
Demonstrates: repeat evaluation deduplicates the frozen signal; ledger replay matches the toy book.
Separate proof needed: OS restart, interrupted send, account identity, real feed and paper-broker lifecycle.
Next implementation slice: <one requested capability, its fixture and acceptance check>
```

The toy reconstructs `Desk` objects inside one process; the printed “restarted
process” label is a simulation. The example also constructs lanes in Python;
the JSON in worked-example section 13.5 is a contract for a future config
loader. Neither the example nor this checker installs a scheduler or enables
orders. The generic `PaperBroker` adapter is an interface skeleton: its class
name does not validate a hostname or account. Implement and prove the kit's
account/environment checks before any separately authorized paper activation.

This route also illustrates why onboarding checks matter. The earlier setup
copied `deskkit` under `engine/` while tests imported it from the root, and
copied a `tests` folder into an existing `tests/`, leaving discovery with zero
tests. The corrected setup copies the actual usable layout. The clean export
also exposed a stale test passing a callback to a quote API whose contract had
changed to fetched `(price, provider_timestamp)` observations. The test now
uses the current contract and checks stale, future and nonfinite secondary
observations. The production quote algorithm is preserved.

## Worked route: explain or recreate Teddy ORB

Start with the [strategy card](../strategies/muse/muse-teddy-orb-spy.md),
[frozen spec](TEDDY-ORB-SPY-SPEC-2026-10-28.md),
[recreation guide](TEDDY_ORB_SPY-RECREATE.md) and
[source module](../sleeves/teddy_orb_spy.py). Use the adapter, config and test
pointers in the recreation guide to resolve the integration questions.

1. Identify the rule's provenance. The video describes a high-volume breakout
   and lower-volume pullback; the frozen implementation names precision choices
   such as six opening-range bars and the volume multiplier. Attribute those
   choices to the implementation, rather than to an unspecified source author.
2. Trace each material rule to code: opening-range construction, qualification,
   pullback/continuation, invalidation, stop/target, time cutoffs and sizing.
3. Carry the data contract: completed 1-minute SIP bars aggregate into complete
   5-minute buckets, using the named regular-session clock. A close-based signal
   and a next-open fill are separate events.
4. Check dependencies before promising a standalone reproduction. This guide
   names shared v3 plumbing outside the public tree; a path reference does not
   supply that dependency. A pure calculation fixture may be reproducible while
   the desk integration still requires source or a documented local adapter.
5. Return the algorithm and its proof boundary. A correct implementation does
   not establish trading edge; the spec explicitly labels edge unproven.

A concrete known-answer calculation: for a long with OR high 100, OR low 98
and entry 101, the specified stop is 99.90. Risk is 1.10; the measured-move
target is 102 and the 2R target is 103.20, so the selected target is 102. These
are synthetic arithmetic inputs, not a trade recommendation or performance
result. Use this expectation independently when testing `_stop_target`.

This audit corrected a substantive summary error: the card previously said
“Stop beyond the pullback extreme.” Both frozen spec copies and
`sleeves/teddy_orb_spy.py::_stop_target` instead specify a stop inside the
broken opening-range edge: OR high minus $0.10 for longs, OR low plus $0.10
for shorts. The card now matches those sources; the frozen spec and executable
strategy were preserved. This is the kind of discrepancy a useful source
bundle should expose before an LLM builds from a summary.

## Worked route: select the right engine layer

The same topic can have a design, a terminal implementation and a portable
research package. Choose according to the requested output.

| Need | Read | Appropriate next action |
|---|---|---|
| Understand forecast hypotheses and evidence families | [Forecast Engines 30 design](../terminal-lineup/FORECAST-ENGINES-30.md) | Identify the dated hypothesis, outcome, horizon, baseline and retirement criterion |
| Trace forecast issuing, settlement and grading | [Forecast machinery](../terminal-lineup/forecast/README.md), [registry](../terminal-lineup/forecast/registry.json), corresponding source and ledger | Inspect exact lineage, clocks, absence states and grading denominator |
| Calculate a score from explicitly supplied features | [Shipyard engine package](../educational/shipyard-engines/2026-11-02/README.md) | Run its offline checks, then call a documented export with a synthetic input |
| Explore a separate forecast lab/package | `forecast-lab` route and that package's README | Establish its own interface and validation; do not inherit another package's results |
| Study the standalone psychology research engine | [Psychology README](../psychology-engine/README.md) and [public validation](../psychology-engine/PUBLIC_VALIDATION.md) | Inspect version, evidence schema and local tests before interpreting an output |
| Understand the separate nine-gauge psychology study | [Engine design](research/psychology-engine-2026-10-30/ENGINE-DESIGN.md), study and associated code | Explain that study's gauges and documented integration context |

The October 28 forecast design explicitly says “design only” at that snapshot.
Later code and records answer different questions. Preserve that dated design
statement while tracing subsequent implementation. The Shipyard package's 30
numeric scorers accept caller-supplied inputs and retain
`decision_eligible: false`; its algebra/contract vectors do not calibrate a
forecast or supply provider feeds. Its README gives runnable offline commands:

```bash
cd educational/shipyard-engines/2026-11-02
npm test
python3 -B scripts/build_forecast_parity_vectors.py --check
```

Read that package's scripts and requirements before running them in a new
environment. Keep its source manifests and copied representations intact.
Likewise, historical Psychology public-copy test totals are receipts for that
version, not a report that a fresh checkout has just passed.

## Worked route: turn agent research into an improvement

Three complementary collections answer different questions:

| Collection | What to learn | Evidence boundary |
|---|---|---|
| [Source-derived agent methods](research/agent-methods/2026-10-31/README.md) | Scoped memory, retrieval states, task resumption, completion evidence and receipt binding | Its own handbook and coverage inventory distinguish proposals, local shadow tests and unintegrated candidates |
| [LLM enhancement extraction](research/llm-enhancement-extraction-20261031/REPORT.md) and later pass reports | Mechanisms from memory, skills, initiative, prompting, extensions and platforms | Cluster/pass records and doctrine-landing notes belong to this separate study; they are not automatically the primary records of the agent-methods collection |
| [Obsidian second-brain synthesis](research/obsidian-second-brain-sweep-20261102/SYNTHESIS.md), [implementation](research/obsidian-second-brain-sweep-20261102/IMPLEMENTATION.md), [verification](research/obsidian-second-brain-sweep-20261102/VERIFY.md) | Source capture, freshness checks, quote fidelity, claim ledgers and research hygiene | Dated implementation receipts describe their original workspace; referenced host files and cron jobs are not installed by reading this public archive |

The [Midna formation](research/midna-trader-formation-20261029/FORMATION.md)
and [memory design](research/midna-trader-formation-20261029/MEMORY-SYSTEM.md)
add a detailed applied case: an independent simulated book, working-state
records, recovery drills and process experiments. Distinguish that book from
the desk and from an agent's platform memory. The memory document identifies
itself as a design and names runtime-owned boundaries. Historical absolute
paths and tool names are dependencies to understand, not instructions to
inspect or alter a new host's private memory.

For a useful improvement, select one mechanism and make its effect observable:

1. **Name the failure.** Example: a resumed agent repeats a completed search or
   misreports a closest match as an exact source hit.
2. **Open the mechanism and its source.** Record the collection, revision,
   passage, implementation status and any reported limitation. Repository stars
   or an `ADOPT` label are not local outcome evidence.
3. **Design a small native change.** Example: a checkpoint with task intent,
   exact source anchors, completed/open rows and the next discriminating check.
   Preserve source evidence; keep credentials and private conversation out of
   public artifacts.
4. **Try a baseline and a changed version on the same tasks.** Include an exact
   match, an ambiguous match, an unavailable source, a contradicted claim and a
   resumed task with a misleading old summary.
5. **Score outcomes and cost.** Did the agent find the correct source, preserve
   the boundary, avoid repeated work and finish the requested artifact? Record
   misses, false matches, tool calls and context use, not just fluent answers.
6. **Keep, revise or reject using those results.** Retain failed cases and source
   pins so the next improvement starts from evidence instead of rediscovery.

This is a practical path to better agent behavior. Reading a repository is not
evidence that model weights changed or that every capability in its archives
became available.

## Make research answers auditable

For any material claim, record a compact evidence row:

```yaml
claim: "<one proposition, with population and time boundary>"
source: "<exact repo path + revision, or primary URL + retrieval date>"
locator: "<section/function/line range>"
representation: "original | public-copy | translation | implementation | summary"
evidence: "<what was actually read or executed>"
supports: "<the conclusion the evidence warrants>"
does_not_establish: "<the nearest tempting overclaim>"
conflicts_or_gaps: "<specific unresolved evidence, if any>"
next_check: "<cheapest observation that would change the conclusion>"
```

For performance research, retain the full denominator, exclusions, failed
candidates, costs, selection process, evaluation horizon and any distinction
between development and held-out/forward results. Keep event time, publication
time, first availability, ingestion and decision-as-of separate when the source
contract uses them. Similarity between two charts or methods is a hypothesis;
it is not independent confirmation or an executable edge.

For live internet research, start from the archived source pins, then open
current primary documentation, source and relevant issue/release history.
Label what changed since the archive. Preserve the old report as a dated record
and add the new assessment beside it. If a source is inaccessible, name the
failed route and available alternatives; an unavailable page does not prove
the subject never existed.

## Preserve knowledge while making it easier to use

- Keep frozen specs, contributed package versions, original test logs and
  retained studies identifiable. Make corrections in a current guide or a
  dated addendum unless the task explicitly calls for revising the source.
- Check representation before claiming parity. An original source, a port,
  generated bundle, mathematical subset and screenshot express different
  contracts even when their names are similar.
- Update the relevant summary and route when a canonical source changes.
  Rebuild the generated index using its own documented procedure; do not hand
  edit generated counts or disguise a missing dependency with a made-up path.
- Treat commands inside archives as examples until their inputs, authority and
  side effects are understood. A public-save script or historical broker drill
  is not part of a read-only research task.
- Quote only what the source says, with provenance. Keep the owner's personal
  name, contact details, addresses, phone numbers, credentials and private
  connected-source material out of new public examples and receipts.

## Leave the next agent a usable result

A strong handoff is brief enough to load and specific enough to resume:

```text
Outcome: <what the user can now do>
Artifact: <exact path and revision>
Verified: <command/observation, inputs, result, receipt>
Open: <each unresolved task row and why it remains open>
Next: <the next concrete action and its acceptance criterion>
Would change the conclusion: <new evidence or changed source>
```

For this repository's own usability, measure whether a fresh reader can locate
the Teddy stop contract, distinguish the three forecast layers, reproduce the
offline desk, separate the two agent-research archives and identify a historical
receipt's boundary. The navigator's mechanical checks verify paths and packet
behavior; actual task success requires these semantic checks. Keep both types
of evidence when evaluating future enhancements.
