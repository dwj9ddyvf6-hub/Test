# Pass 2, Dive 6: Second-Order Expansion

Research date: 2026-10-31. Method: live GitHub API metadata, READMEs and named key files via raw.githubusercontent.com, machine-readable indexes parsed locally. No repo code installed or executed. Verdict vocabulary, reference stack, and trait list are pass 1's (REPORT.md). Anything below that duplicates a pass-1 verdict is one line, per the brief.

## How the expansion was mined (coverage, stated honestly)

- **hashgraph-online/awesome-ai-plugins**: `plugins.json` re-parsed in full (1,116 entries, last_updated 2026-10-31). Pass 1 keyword-counted it and deep-inspected 5 entries, naming 6 more notables without opening them. This dive opens 4 of those notables (keep-the-why, MoonMind, Agent Guard, Obsidian Second Brain) plus 3 found by mechanism-keyword mining of the same file (tree-ring-memory via "forget/consolidat", bilinc via "provenance", red-green-proof via "verify"), plus the scanner repo itself (hol-guard), which pass 1 only read about through the list's guide.
- **taishi-i/awesome-ChatGPT-repositories**: pass 1 sampled 7 of 18 per-category data files (1,221 records). This dive fetched and parsed the 11 un-sampled files (chatbots a/b, CLIs a/b, NLP a/b, browser-extensions a/b, reimplementations, unity, awesome-lists; 1,536 records). Yield was thin by design of the source: chatbots/CLIs/NLP are dominated by model clients, model weights, and single-purpose apps with no transferable agent mechanism. Two finds cleared the bar: khoj-ai/khoj (in repos-nlp-a.json) and f/awesome-chatgpt-prompts (in repos-awesome-lists.json, since renamed; see §14).
- **Asdivyansh/Awesome-ChatGPT-Plugins**: `data/plugins.json` re-parsed in full (4,338 entries). Only 131 entries carry a github.com website at all, and 1,162 carry named skills, but the entries are ChatGPT directory listings, not repos; the GitHub-backed ones sampled (amd/skills, SpannDaMan/agent-churn-control) are vendor skill catalogs or 2-star utilities. No ASD-only repo cleared the proper-inspection bar; this confirms pass 1's REFERENCE (census only) verdict with direct evidence rather than changing it. One-line dispositions in the ledger.
- **Peer references from inside pass-1 top repos**: Graphiti and bounded-loops and Squish were all named in Cluster 1's references table as "noted, not inspected"; Cognee is the third major open memory engine in the same comparison set Supermemory's MemoryBench names (Mem0, Zep/Graphiti). All four are inspected here. Superpowers and ECC cite no external peer repo with a mechanism pass 1 lacked (their citations are to their own skills); the proactive list's un-inspected code entries (YETI, PRISM) remain arXiv-only with no repo found, logged in the ledger, not silently dropped.

**14 repos inspected properly below.** Sections 1 to 5 are the top finds.

---

## 1. oliver-zehentleitner/keep-the-why — the missing memory type: rationale (mined from awesome-ai-plugins)

| Field | Value (live API, 2026-10-31) |
|---|---|
| Stars / forks | 233 / 14 |
| Last push | 2026-10-30 |
| Licence | MIT |
| Description | "The why layer of repo-native project memory" |

**What pass 1 missed.** Pass 1 named this repo in one clause ("project memory of decisions, rejected alternatives, workarounds and incident learnings") and never opened it. It is the most complete design in either pass for a memory type the reference stack handles only incidentally (bug log, doctrine lessons): **decision rationale as a governed, linted, versioned corpus**, stored as Markdown in the repo it describes, captured by a SKILL.md skill in four modes (continuous capture during work; retrospective recovery from git history/issues with explicit "couldn't reconstruct" honesty; knowledge-transfer interviews; maintenance with supersession).

**Artifact extracted verbatim (source: README.md, "Format" section).** The entry field table, complete:

| Field | Meaning (as written in the source) |
|---|---|
| **Id** | A UUID (version 4), the entry's address, the first header line, made by an OS command, never changed. Headings get reworded and files split; the Id stays, so every reference keeps working, across repositories too |
| Decision / behavior | What was actually done |
| Rejected alternative(s) | What else was considered, and why it lost |
| Reason | Why the chosen path won |
| **Type** | `decision` \| `workaround` \| `incident` \| `constraint` \| `undefined — <reason>` |
| **Status** | `active` \| `superseded` \| `open` \| `needs-review` \| `pending-confirmation` |
| **Evidence** | `confirmed` \| `inferred` \| `unknown` — how certain the rationale is |
| Source | Where the rationale came from (interview, issue, commit, postmortem) |
| Revisit when | A concrete trigger that should prompt re-checking the entry |
| See | Another entry this one follows from: `<locator> — <its Id> — as of <date>` |
| **Superseded by** | On every `superseded` entry: the successor's Id, a cross-project reference, or `none — <why nothing replaced it>` |

Entries live one file per topic under `context/`, found through `context/index.md` whose 36-heading skeleton is always present so parallel branches cannot collide in the index. The structural half is mechanically enforced by a companion linter (`keep-the-why-lint`, PyPI, schema-version-aware; an entry without an Id is a linter error from context-schema 0.18.0), while the README is explicit that whether the rationale is *true* stays human judgment. Unattended sessions write entries flagged `pending-confirmation` rather than asking into the void or dropping the finding. The author ran a controlled experiment on the core claim (20 fresh sessions asked to simplify a retry wrapper, 10 with the rejected alternative recorded, 10 without; transcripts and grades in `experiments/rejected-change/`).

**Design invariants.** (1) Rationale is a separate corpus from facts: its unit is decision + rejected alternative + reason, not a claim. (2) Identity is a UUID, never a heading, so references survive edits and cross repos. (3) Every entry carries an evidence grade and a revisit trigger; supersession must name its successor or explain its absence. (4) Structure is linted; truth is not pretended to be. (5) Capture defaults to proactive-with-ask-only-when-unsure, and loading is engineered (hook or entry-point section) with measured load rates (10/10 with hook vs 0/10 without, per the README's own measurements), not left to description matching.

**Verdict: ADOPT-IDEA (new, not in pass 1's shortlist).** Build the rationale entry schema natively for the two corpora that need it (engineering decisions/doctrine lessons; trading-book decisions): Id, Rejected alternative(s), Evidence (confirmed/inferred/unknown), Revisit when, Superseded by, as required fields, with the linter idea folded into the existing gate (a structural check, not the PyPI tool). This is a genuine pass-1 gap: Shortlist #2 (instincts) captures trigger-to-action procedures and #4 captures fact supersession, but neither captures *why a path was rejected*, which is the knowledge whose absence makes an agent re-propose a dead design. Effort: Small to Medium.

---

## 2. eugeniughelbur/obsidian-second-brain + OKM — freshness as a linted rule (mined from awesome-ai-plugins)

| Field | Value |
|---|---|
| Stars / forks | 5,073 / 627 |
| Last push | 2026-10-28 |
| Licence | MIT |
| Description | "Persistent memory for Claude Code, Codex and 6 other AI agents, stored as plain markdown in your Obsidian vault" |

**What pass 1 missed.** Named in one clause ("47 slash commands plus scheduled maintenance agents"), never opened. The vault product itself (49 commands, 8 harness builds) is ALREADY-HAVE in substance (file memory, people/project pages, scheduled maintenance). The load-bearing find is a one-page companion spec pass 1 did not know existed: **OKM (Open Knowledge Metabolism)**, a freshness discipline for any AI-maintained markdown folder, enforced by a reference linter (`scripts/freshness_lint.py`, run by its health command).

**Artifact extracted verbatim (source: `references/freshness-policy.md` in the repo).** The rule and its legal/illegal forms:

> One rule, enforced by a lint: **every stored fact must be timeless, dated, or a pointer. Nothing may claim to be current without a stamp.**
> - **Slow fact** ("the wiring"): stable for roughly 7 days or longer. Stored.
> - **Fast fact** ("the meter"): can change within 7 days. Live counts, open tickets, balances, statuses. Fast facts live in their home systems; the folder only points at them.
> Legal forms: **1. Timeless** (no date needed, does not decay). **2. Snapshot** (a dated observation; anything inside a dated note or under a dated heading is automatically a snapshot). **3. Pointer** ("Where truth lives: [link]. Last observed: 13 open deals (as of 2026-07-13)").
> The one illegal form: a present-tense claim about a fast fact, with no date, outside a dated container. "This is the sentence that becomes a lie next Tuesday while still reading as truth."

And the lint rules (same source, condensed only for length; rule IDs and semantics verbatim): **FRESH-1 (error):** a quantitative present-tense claim about a volatile noun outside a dated container must carry an `as of` stamp or be rewritten as a pointer; a line quoting the illegal form carries `<!-- freshness: example -->` to suppress FRESH-1 for that line only. **FRESH-2 (warning):** a stamp older than the freshness window (default 7 days) flags the line. **FRESH-3 (error):** a pointer must have a resolvable target. **FRESH-4 (exempt):** dated containers are immutable history. **FRESH-5 (warning):** an unused suppression directive warns. The refresh loop per aged line is exactly three answers: **re-observe, convert (to pointer), or retire (into a dated note)**.

Two further mechanisms worth recording: (a) **bounded recall with abstention**: a per-prompt hook injects at most 4 notes / ~900 chars, or **nothing at all when confidence is low**, with every inject/abstain decision logged; an independent, file-level corroboration of SLM's tiered-recall idea (Shortlist #5). (b) Its **background agent safety shape**: fires after compaction, ships inert and opt-in, tool surface restricted by removal (`--tools "Read,Write,Edit,Glob,Grep"`, no MCP, no shell, no network), and **adds and updates only, never deletes or merges**, which is SLM's addition-only maintenance rule arrived at independently.

**Verdict: ADOPT-IDEA (new).** The timeless/dated/pointer rule plus a FRESH-1-style check is a direct, cheap upgrade to the file memory's authoring discipline and to Shortlist #4/#5: pass 1 adopted expiry for temporary facts, but nothing governed *unstamped fast facts written as if current*, which is the commonest way a memory file silently rots. The vault product: ALREADY-HAVE / do not install. Effort: Small (authoring rule plus a heuristic lint in the nightly pass; the reference linter is MIT but heuristic-tuned to its own vault, so reimplement the rule, not the script).

---

## 3. qualixar/bounded-loops — gated loops with the gate protected from the worker (peer reference from SuperLocalMemory)

| Field | Value |
|---|---|
| Stars / forks | 4 / 1 |
| Last push | 2026-10-02 |
| Licence | Apache-2.0 |
| Description | "Bounded Loops & Graphs: 69 agent loops (65 keyless), 7 reference graphs, independent gates, declared bounds" |

**What pass 1 missed.** Cluster 1 listed this as a companion project ("69 agent loops and reference graphs with independent gates and verifiable receipts") and inspected nothing. The artifacts are stronger than the summary: the gate is protected from the worker by construction, and every loop ships a negative control.

**Artifacts extracted verbatim (sources named per artifact).**

`loops/bug-fix-red-green/loop.yaml` (complete):

```yaml
name: bug-fix-red-green
description: >
  Drive an agent until a failing pytest passes.
  The canonical Loop Engineering example: "keep working until the test is green."
  Provides a self-contained red-green loop as a runnable repository artifact.
pattern: evaluator-optimizer
role:
  - backend
  - engineering
rung: L2
spec: PROMPT.md
# The gate's verification anchor. The engine refuses any runner write to a
# path matching these globs, so the agent (or a community cassette) cannot
# neuter the test to fake a green gate.
forbid:
  - "seed/test_*.py"
runner:
  default: stub
gate:
  kind: pytest
  run: "pytest -q"
bounds: bounds.yaml
memory: STATE.md
```

`loops/bug-fix-red-green/bounds.yaml` (complete): `max_iterations: 15`, `no_progress_window: 3`, `max_tokens: null`, `max_wallclock_s: 1440`, `sandbox: true`, `quarantine_inputs: true`, `schema: null`, `trace: true`, `require_approval: false`.

Engine invariants (README, "Bounded loops in depth" and "Nine enforced bounds"): on every lap the runner works in a quarantined scratch copy, the gate evaluates independently, and only `verdict.passed` can produce DONE ("no code path branches on `agent_claimed_done`"); the controller refuses to run if `worker is gate` (object identity); gate kinds across the 69-loop catalog are 44 command, 10 jsonschema, 9 pytest, 3 composite, 1 osv, 1 checkov, and **"No loop uses 'an LLM decides' as its gate"**; the catalog's exemplar loops ship `wreck.sh`, which runs the same prompt ungated so the reader can watch the agent claim GREEN while pytest fails. The README is honest about the identity check's limit (a rubber-stamping wrapper passes it), which raises rather than lowers its credibility.

**Verdict: ADOPT-IDEA (strengthens Shortlist #6 and #8, does not change them).** Three concrete transfers: (1) a `forbid:` list in any gated workflow: the paths the worker may never write because the gate reads them (the citation-existence loop puts its checker and reporter in `forbid:`); this closes a hole pass 1's false-green audit (#3) does not cover, since a test can be honest and still be edited by the worker it judges. (2) Declared bounds as a file (iterations, no-progress window, wall-clock, token budget, kill switch env var checked before every lap) rather than prose. (3) The negative-control habit: every gate ships an ungated `wreck` run demonstrating the failure it exists to catch. The engine itself: REFERENCE (the workflow system here already provides durable orchestration; adopting a second loop engine would be a second source of truth).

---

## 4. hashgraph-online/hol-guard — the scanner artifact behind pass 1's scan gate (mined from awesome-ai-plugins' own pointer)

| Field | Value |
|---|---|
| Stars / forks | 1,041 / 227 |
| Last push | 2026-10-31 (day of inspection) |
| Licence | Apache-2.0 |
| Description | "Open-source antivirus for AI agents" |

**What pass 1 missed.** Pass 1 read the list's SCANNER_GUIDE.md and adopted the 75/100 gate as policy (Shortlist #7), but never opened the scanner repo, so the actual scoring artifact was unexamined. It is specified, versioned, and more conservative than the guide implied: quality scores are "normalized across applicable checks, so optional surfaces do not inflate a package's grade", and skill trust is not a private rubric but the published HCS-28 baseline.

**Artifact extracted verbatim (source: `docs/trust/skill-trust-local.md` in the repo).** HCS-28 baseline adapter table (complete):

| Adapter ID | Weight | Contribution Mode |
|---|---|---|
| `verification.review-status` | 0.50 | universal |
| `verification.publisher-bound` | 0.20 | universal |
| `verification.repo-commit-integrity` | 0.40 | universal |
| `verification.manifest-integrity` | 0.30 | universal |
| `verification.domain-proof` | 0.10 | universal |
| `metadata.links` | 0.30 | universal |
| `metadata.description` | 0.25 | universal |
| `metadata.taxonomy` | 0.20 | universal |
| `metadata.provenance` | 0.25 | universal |
| `upvotes` | 1.00 | conditional |
| `safety.cisco-scan` | 1.00 | universal |
| `repository.health` | 1.00 | conditional |

Aggregation rules (same source, verbatim in substance): clamp components to [0,100]; missing universal components materialize as 0; each adapter total is the arithmetic mean of its components; conditional adapters enter the denominator only when they emit scores; the composite is the weighted mean of included adapter totals. Local read-mode mappings are equally explicit (for example `verification.review-status` is 100 only when the package declares `verified=true`, otherwise 0; `safety.cisco-scan` is universal 0 when no Cisco results exist, so an unscanned skill is penalized, not excused). Scanner check categories (README): manifest validation; hardcoded secrets, unsafe MCP commands/transports, risky approval defaults; GitHub Actions permissions and pinned dependencies; packaging (README/license present, skill frontmatter, committed env files); code quality (dynamic execution, shell injection). CLI surface includes `scan`, `lint --explain <RULE>`, `lint --fix`, `verify [--online]`, `submit --attest`, with text/json/markdown/SARIF reports, and a config file (`.plugin-scanner.toml`) whose repo-owned baselines only take effect when the Action is run with `trust_repository_policy: true`, a deliberate anti-self-grading guard.

**Verdict: ADOPT-IDEA (refines Shortlist #7 with the artifact itself).** Pass 1's conclusion stands and is now grounded: adopt the HCS-28-shaped weighting as the local scan rubric (universal-missing-equals-0 and conditional-denominator rules are the two details worth copying exactly, since they are what stop a thin package scoring well by omission), and copy the `trust_repository_policy` guard pattern for any scanner whose config lives in the repo being scanned. Evaluating the tool itself for the skills library is now a reasonable next step pass 1 could not have recommended, because the rubric is published and the repo is active and Apache-2.0; that evaluation is still a separate decision, not taken here.

---

## 5. getzep/graphiti and topoteretes/cognee — the open temporal-graph engines (peer references from Supermemory's comparison set)

### 5a. getzep/graphiti

| Field | Value |
|---|---|
| Stars / forks | 32,391 / 3,324 |
| Last push | 2026-10-28 |
| Licence | Apache-2.0 |
| Description | "Build Real-Time Knowledge Graphs for AI Agents" |

**Mechanism (from README, "What is a Context Graph?").** A context graph has four components: **Entities** (nodes with summaries that evolve), **Facts/Relationships** (edges as triplets, each with a temporal validity window: when it became true and when it was superseded), **Episodes** (the raw data as ingested; every derived fact traces back to an episode), and **Custom Types** (developer-defined Pydantic ontology, prescribed or learned). Facts are invalidated, not deleted, on change ("Query what's true now, or what was true at any point in time"); construction is incremental (no batch recompute); retrieval is hybrid semantic + BM25 + graph traversal. Companion paper: arXiv 2501.13956 (Zep temporal knowledge graph architecture).

**What this changes versus pass 1.** Pass 1 adopted Supermemory's updates/extends/derives vocabulary (Shortlist #4) from a *closed* engine's documentation. Graphiti shows the same problem solved openly with a sharper primitive: **bi-temporal validity windows on the fact itself** (valid-time plus ingestion/episode provenance), from which "updates" is a derived view rather than a stored edge label. The refinement for #4: when the file memory records a supersession, record the replaced fact's validity window (true from / true until / learned on) explicitly, not only the edge type; that is what makes "what did we believe on date X" answerable, a question the current synthesis cannot answer cleanly. **Verdict: ADOPT-IDEA (that one primitive) / REFERENCE (framework).** Do not adopt the product: it requires a graph database (Neo4j/FalkorDB/Neptune) as a second memory truth, the same ground as pass 1's MemOS skip.

### 5b. topoteretes/cognee

| Field | Value |
|---|---|
| Stars / forks | 32,955 / 3,445 |
| Last push | 2026-10-30 |
| Licence | Apache-2.0 |
| Description | "The open-source AI memory platform for agents" |

**Mechanism (from README, "How Cognee works").** Four verbs: `remember` (store content or code into permanent memory, or into a session when a session ID is supplied), `recall` (retrieve with automatic routing or a chosen strategy), `improve` (enrich memory, apply feedback, and **bridge session knowledge into the graph**), `forget` (remove an item or dataset). Two details pass 1 had nowhere: (1) **session distillation**: session memory is a separate, cheaper tier, and only *accepted* lessons are curated across into permanent memory by the improve step, an explicit promotion gate between episodic and permanent storage; (2) a **no-LLM local mode** (GLiNER extraction + local embeddings) in which ingestion and retrieval work and "LLM-dependent improvement stages skip automatically", a graceful-degradation contract stated in the quickstart itself.

**Verdict: ADOPT-IDEA (session-to-permanent promotion gate) / SKIP the platform** (same second-truth ground as Graphiti; also a Postgres/graph/vector stack). The promotion gate refines Shortlist #2 and #4: the nightly synthesis currently promotes daily-note material by inclusion; Cognee's shape makes promotion an explicit, named step with an acceptance criterion (only accepted lessons cross), which is auditable in a way inclusion is not. One line for the rest: its four-verb surface duplicates Supermemory's three-verb surface, already catalogued.

---

## 6. michielhdoteth/squish-memory — calibrated confidence, not just tiers (peer reference named in Cluster 1)

| Field | Value |
|---|---|
| Stars / forks | 12 / 2 |
| Last push | 2026-10-02 |
| Licence | None stated in API metadata (NOASSERTION) |
| Default branch | master (README 404s on main; read on master) |
| Description | "Calibrated recall confidence (ECE 0.055) and honest abstention" |

**What pass 1 understated.** Cluster 1's references table dismissed Squish in one line as "same idea family as SLM's tiered recall; noted as a search by-catch only, not inspected." Inspection shows the overlap is only the abstention half. The distinct mechanism is **calibration as a published, measurable property**: the README claims expected calibration error (ECE) 0.055 on its eval set, with the operational meaning stated verbatim: "When it says 90% confident, it is right about 90% of the time. Not a score. A number your agent can act on." Recall returns NO CONFIDENT MATCH when nothing clears the bar; memories carry temporal validity windows and decay scoring; storage is one local SQLite file; session-start injection is budgeted at 50 to 200 tokens.

**Verdict: ADOPT-IDEA (refines Shortlist #5).** SLM gave the tiers (supported / closest-only / not present); Squish adds the missing discipline for the tier boundary: the confidence attached to a recall should be *calibrated and periodically measured* (a small held-out set of known-answer recall probes, scored for ECE-style agreement), otherwise "supported" is an unmeasured self-assessment. That is a small, concrete addition to #5's monthly memory evaluation. Product: SKIP (12 stars, no licence stated, paid desktop tier; nothing to lift as code).

---

## 7. ReARCLabs/bilinc — versioned memory verbs with two-step rollback (mined from awesome-ai-plugins, "provenance")

| Field | Value |
|---|---|
| Stars / forks | 0 / 0 |
| Last push | 2026-10-26 |
| Licence | BUSL-1.1 for the service per its own README ("cloud-only and BUSL-1.1"); API metadata NOASSERTION |
| Description | "Hosted memory for AI agents: commit, recall, revise, snapshot and roll back agent state with provenance" |

**Mechanism (artifacts from README, SDK section).** A key-addressed memory where every write returns a version and writes are optimistic-concurrency checked (`revise(..., expected_version=...)` is refused if the memory moved since the read; `revise` on a missing key fails rather than creating). The verb set is the artifact: `commit` (save with source, returns version), `recall` (shows when each memory was last confirmed and marks entries past their review window as possibly outdated, hiding nothing), `revise` (correct, never create; reason accepted), `forget` (reason **required** and recorded; `purge=True` additionally removes stored content from checkpoints and history, keeping key name and change fingerprints), `confirm` (record that a memory is still accurate; costs one write), `snapshot` / `diff` / `rollback`, where rollback is two-step: a free preview issues a confirmation token and only the execute call carrying that token restores. The README states the design maxim directly: "Similar is not the same as current": semantic search returns similar texts and cannot say which is current; keyed recall returns the current value with who wrote it, why, and when last confirmed.

**Verdict: ADOPT-IDEA (three small transfers refining Shortlist #5) / SKIP the product** (hosted, cloud-only, BUSL, zero adoption). Transfers: (1) **forget requires a recorded reason, and purge is a distinct, stronger verb** than forget, matching and sharpening SLM's erasure-with-receipt rule; (2) **last-confirmed stamping with a review window**: a memory past its window is *marked* possibly outdated at recall time, not deleted and not silently trusted (pairs with OKM's FRESH-2 in §2; two independent sources arriving at stamp-and-flag is corroboration); (3) **two-step destructive recovery** (preview issues the token, execute requires it) as the shape for any future bulk memory rewrite.

---

## 8. TerminallyLazy/tree-ring-memory-codex-plugin — configured is not active (mined from awesome-ai-plugins, "forget/consolidat")

| Field | Value |
|---|---|
| Stars / forks | 0 / 0 |
| Last push | 2026-10-28 |
| Licence | MIT |
| Description | "Codex plugin wrapper for Tree Ring Memory local-first agent memory lifecycle guidance" |

**Mechanism.** A wrapper plugin over a project-local CLI (canonical project: TerminallyLazy/Tree-Ring-Memory, named in the README; the wrapper was inspected, the canonical repo was not, and is logged as such). Transferable shapes: (a) **receipt-backed harness readiness**, stated verbatim in the README: "Configuration is not activation proof. A harness is `active` only after a fresh, matching receipt shows scoped recall and safe context injection from a new session", with non-active states named (`configured-awaiting-proof`, `needs-trust`, `needs-plugin`, `needs-project-mount`, `needs-user-review`, `unsupported`) and an instruction not to manufacture bridge files or receipts; (b) installer discipline (version-pinned installer, SHA-256 published in the README, "Do not pipe a network response directly to a shell", verify `--version` output before use, dry-run-first for adapter writes, version floors below which a runtime may preview but must not persist); (c) memory writes scoped to "validated decisions, lessons, warnings, and user preferences", explicitly *without storing a transcript*.

**Verdict: ADOPT-IDEA (readiness states only) / REFERENCE.** The configured-vs-active distinction is proof-before-green applied to integrations, and it is worth one line in any future connector/skill adoption checklist: an integration is not "installed" until a fresh session produces a receipt of it working. The product itself is a 0-star wrapper around an uninspected core; nothing else transfers.

---

## 9. JeongJaeSoon/agent-guard — the commit-boundary guard (mined from awesome-ai-plugins)

| Field | Value |
|---|---|
| Stars / forks | 38 / 0 |
| Last push | 2026-10-30 |
| Licence | MIT |
| Description | "Real-time secret-leak guardrails for AI coding agents (Claude Code, Codex), Git hooks, and CI" |

**Mechanism (from README).** Local-first, no telemetry, built on gitleaks. Three layers: pre-tool hooks that block risky `.env` reads and mask secret-like tool output; a **pre-commit scan of the staged added lines** (covering the index plus what `git commit -a`/pathspecs stage implicitly, shell code passed via `bash -c`/`eval`/aliases checked as the command itself), which **refuses `--no-verify` and `--no-gpg-sign` on agent-issued commit/push commands** so the agent cannot switch the check off with a flag; and a GitHub Action as the post-push backstop. Failure semantics are explicit and configurable: a scan that could not run is not treated as clean; the plugin default warns-and-continues on infrastructure failure while `AGENT_GUARD_INFRA_FAILURE_MODE=closed` blocks, and the native hook and Action fail closed regardless.

**Verdict: ADOPT-IDEA.** Pass 1's protections sit at the public-write boundary (the PII gate on API writes) and at adoption time (scan-before-list, #7). This is the missing third boundary, the local commit, with two details worth copying verbatim into any local guard: agents may not pass the flag that disables the guard, and the infra-failure mode is a named, documented setting rather than an accident. The tool itself is a plausible ADOPT-CODE candidate for a later evaluation (MIT, shell/jq/gitleaks only), but that evaluation is not this pass.

---

## 10. RooAGI/red-green-proof — the revert step, as a skill (mined from awesome-ai-plugins, "verify")

| Field | Value |
|---|---|
| Stars / forks | 0 / 0 |
| Last push | 2026-09-01 |
| Licence | MIT |
| Description | "Turn a suspected bug into a proven one: red first, green second, red again on purpose" |

**Artifact extracted verbatim (source: README.md, "The loop").**

> 1. **Verify the cause, do not infer it.** Label every claim `Proven` / `Inferred` / `Unknown`. Check `git log -S` before treating behaviour as a bug; it may have been deliberate.
> 2. **Write the test. Watch it fail** against the code as it is now.
> 3. **Fix it**, smallest change that goes green.
> 4. **Revert the fix. Confirm red. Restore.** If it stayed green, the test is fake; rewrite it.
> 5. **Run the full suite and type checks.**
>
> "A bug is not fixed because the tests pass. A bug is fixed when a test **fails without your fix and passes with it**, and you have watched it do both."

Plus: for code that cannot be invoked directly (closures, route handlers), extract / structural / model / characterization tests are permitted, each with an honesty label required in the file header. Its two caught cases (a concurrency test whose writers never interleaved; a fault test whose injected failure never reached the error path) are the same failure class as falsegreen's canonical mock example, caught mechanically rather than semantically.

**Verdict: ADOPT-IDEA (companion procedure to Shortlist #3).** Pass 1's false-green audit is a periodic semantic review (J1 to J6). This is the per-fix mechanical twin: the revert-and-watch-red step, performed once at fix time, proves fail-direction for that specific blocker at near-zero cost. The two compose: revert-proof at authoring time, J-protocol audit periodically. Pass 1's #3 conclusion is strengthened, not changed. The skill file itself is a reasonable ADOPT-CODE candidate on a later pass (MIT, single-purpose); 0 stars means no social proof either way.

---

## 11. MoonLadderStudios/MoonMind — durable orchestration, confirmed equivalent (HOL notable, opened)

| Field | Value |
|---|---|
| Stars / forks | 13 / 5 |
| Last push | 2026-10-31 |
| Licence | Apache-2.0 |
| Description | "Run Claude Code, Codex, and any Omnigent agent with superior security, resiliency, and observability" |

**Mechanism (from README).** A self-hosted single-operator app: Temporal tracks steps, retries, and schedules so work resumes after a worker restart; agents (via the Omnigent backend) run inside container boundaries and submit build/test jobs without receiving the host Docker socket; Provider Profiles separate model credentials from application login and from source-control access (three distinct settings, deliberately); a dashboard exposes progress, logs, diagnostics, and artifacts per run. Honest operating notes include: a healthy dashboard alone does not mean an agent is ready to run; secret scanning of outbound text is opt-in and off by default; saving results and publishing changes carry different permissions.

**Verdict: ALREADY-HAVE / REFERENCE.** Durable, resumable, checkpointed multi-agent execution with inspectable run artifacts is exactly the reference stack's workflow system (which additionally reuses completed children on relaunch). Nothing transfers except one phrasing worth keeping: credential planes (app login, provider, source control) named as three separate settings, a tidy checklist for any future multi-account surface. Do not install: a second orchestration plane is a second source of truth for run state.

---

## 12. khoj-ai/khoj — second brain with scheduled automations (mined from taishi-i repos-nlp-a.json)

| Field | Value |
|---|---|
| Stars / forks | 37,915 / 2,529 |
| Last push | 2026-08-02 |
| Licence | AGPL-3.0 |
| Description | "Your AI second brain. Self-hostable" |

**Mechanism (from README overview).** Self-hostable personal AI: chat over local documents (markdown, org-mode, PDF, Word, Notion, images) plus web answers, custom agents with their own knowledge/persona/model/tools, semantic document search, access from browser/Obsidian/Emacs/desktop/phone/WhatsApp, and **automations**: scheduled recurring research delivered as personal newsletters and smart notifications to the inbox.

**What pass 1 missed and what it changes.** Nothing to pass 1's conclusions; the entry exists to close a mining gap honestly. Khoj is the largest repo in the taishi tail files (37.9k stars) and the only one whose mechanism touches initiation: scheduled automations producing digests unprompted. That pattern is ALREADY-HAVE here in stronger form (cron lanes with delivery discipline and, after Shortlist #1, priced gates; Khoj's automations have no intervention-cost concept at all). Everything else (document chat, custom agents, multi-surface access) is ALREADY-HAVE or a product surface this stack does not need. **Verdict: ALREADY-HAVE / SKIP the code** (AGPL-3.0; a full second application beside the agent). Recorded so the tail-category mining cannot be accused of skipping the biggest fish in it.

---

## 13. f/prompts.chat (formerly f/awesome-chatgpt-prompts) — the prompt corpus, post-rename (mined from taishi-i repos-awesome-lists.json)

| Field | Value |
|---|---|
| Stars / forks | 175,413 / (forks not re-read after redirect) |
| Last push | Not re-read; see redirect note |
| Licence | Not re-verified after redirect |
| Description (post-rename) | "f.k.a. Awesome ChatGPT Prompts. Share, discover, and collect prompts from the community" |

**Coverage honesty.** The taishi snapshot lists `f/awesome-chatgpt-prompts` at 162,000 stars. The live API returns HTTP 301 Moved Permanently for that name to repository ID 574523116, which resolves to **f/prompts.chat** at 175,413 stars. Pass 1 never inspected either name. The repo is now a self-hostable prompt-collection site whose corpus is the long tail of "act as X" persona prompts.

**Verdict: REFERENCE / SKIP for adoption.** The corpus is prompt content, not mechanism: persona prompts are superseded here by skills with procedures, gates, and evidence rules, and bulk-importing community prompts would be the same injection-surface error pass 1 flagged for everything-skills' content. Its one transferable datum is sociological, already known: persona prompting is what the public means by prompt engineering, which is why the mechanism-level finds in both passes come from elsewhere. Recorded as Redirected in the ledger, following pass 1's optillm precedent.

---

## 14. One-line dispositions (duplicates and sub-bar finds; no section, per the brief)

- **kiycoh/silica-harness** (HOL, "silica"): Obsidian vault as agent memory over MCP with gated note writing and session-opening hooks. Duplicates §2's vault verdict and pass 1's memory verdicts. REFERENCE.
- **syedair/ai-memory-skill** (HOL): markdown memory skill with a consolidation pass. Duplicates pass 1's MemoryPlugin-skill protocol and Supermemory verdicts. SKIP.
- **Ar9av/obsidian-wiki** (HOL): builds cross-linked vaults from docs and session history. Duplicates §2. REFERENCE.
- **amd/skills** (ASD GitHub-backed, 471 stars): official vendor catalog of agent skills for one hardware stack. Duplicates openai/plugins' bundle-anatomy verdict. REFERENCE.
- **SpannDaMan/agent-churn-control** (ASD GitHub-backed, 2 stars): "stop duplicate agent work with local evidence reuse." One-line idea already covered by workflow child-reuse. SKIP.
- **TerminallyLazy/Tree-Ring-Memory** (canonical core behind §8): named, not inspected; logged, not dropped.
- **YETI, PRISM** (proactive list): no code repo found in either pass; arXiv entries only. Unreachable as repos, as in pass 1's ledger.

---

## What changes a pass-1 conclusion (summary for reconciliation)

1. **New adoption candidate, absent from the shortlist: keep-the-why's rationale memory (§1)** and **OKM's freshness rule (§2)**. Both are file-native, cheap, and govern corpora the stack already keeps. If round-2 reconciliation adds two items, these are they, ahead of several pass-1 near misses.
2. **Shortlist #4 refined (§5a):** bi-temporal validity windows (true-from / true-until / learned-on) are a sharper primitive than edge labels alone; record the window on supersession.
3. **Shortlist #5 refined twice (§6, §7):** add calibration measurement to the recall tiers (Squish), and adopt forget-requires-reason plus last-confirmed stamping with a review window (Bilinc, corroborated independently by OKM's FRESH-2).
4. **Shortlist #3 strengthened (§10):** pair the periodic J1 to J6 semantic audit with a per-fix mechanical revert-proof.
5. **Shortlist #7 grounded (§4, §9):** the HCS-28 weight table and aggregation rules are now extracted verbatim, and a third enforcement boundary (the local commit, with no-disable-flag and named infra-failure mode) joins public-write and adoption-time.
6. **Shortlist #8 / #6 strengthened (§3, §8):** gate-protection via `forbid:` paths and declared bounds files (bounded-loops); configured-is-not-active readiness receipts (Tree Ring).
7. **No pass-1 verdict is overturned.** Graphiti/Cognee confirm the memory shortlist's direction from open implementations; Khoj, MoonMind, and prompts.chat confirm their ALREADY-HAVE/SKIP classes with direct inspection instead of inference; the ASD list's REFERENCE verdict now rests on a full parse rather than sampling.

## Coverage ledger (pass 2, this dive)

| Source | State |
|---|---|
| hashgraph-online/awesome-ai-plugins `plugins.json` | Parsed in full (1,116 entries); 8 repos deep-inspected (§1, §2, §7, §8, §9, §10, §11, plus hol-guard §4 reached via the list) |
| taishi-i per-category files (11 un-sampled in pass 1) | Fetched and parsed (1,536 records); 2 repos deep-inspected (§12, §13); remainder screened out as clients/weights/apps with reasons stated in the mining note |
| Asdivyansh `data/plugins.json` | Parsed in full (4,338 entries); GitHub-backed subset enumerated (131); 2 sampled (§14); no repo cleared the inspection bar, stated as a finding |
| Peer references (Graphiti, Cognee, bounded-loops, Squish) | Deep-inspected (§3, §5, §6) |
| f/awesome-chatgpt-prompts | Redirected (301) to f/prompts.chat; resolved and dispositioned (§13) |
| TerminallyLazy/Tree-Ring-Memory (canonical), YETI, PRISM | Named, not inspected / unreachable as repos; logged in §14, never silently dropped |
