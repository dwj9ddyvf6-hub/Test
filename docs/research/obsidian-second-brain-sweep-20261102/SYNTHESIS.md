# SYNTHESIS: Obsidian second-brain sweep, adoption verdicts

Program: Obsidian second-brain sweep, 2026-11-02. Synthesis lead pass.
Inputs read in full: AUDIT-1-kepano.md, AUDIT-2-agricidaniel.md,
AUDIT-3-eugeniughelbur.md, AUDIT-4-astrohan.md, AUDIT-5-undefined-ui.md,
AUDIT-6-charlie947.md, AUDIT-7-mehmetgoekce.md (all in this folder);
workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md;
the midna-book file list and CHARTER.md; the enhancement disciplines
section of ~/AGENTS.md (items 13 to 35) and the tools it names in
~/workspace/tools/.

Status: PARTIAL by construction. This document delivers classifications
and native implementation specs. No adoption below is implemented or
proven by this program: each ADOPT item is a spec for a separate,
owner-visible implementation pass with its own tests and proof, and its
status stays UNVERIFIED until that proof exists on the final system
state. Nothing in this program edited ~/MEMORY.md, any register, any
desk file, or any public surface.

## SCOPE (InfinityBlade)

- Surface: one synthesis document in this program folder, classifying
  every mechanism the seven audits extracted and specifying the small
  set worth adopting natively.
- Constraints: single source of truth preserved. ~/MEMORY.md and the
  midna-book registers are the memory architecture; every adoption
  extends them or the research_notes layer beside them, never creates
  a parallel store of facts about the user, and never edits MEMORY.md.
  Read-only toward every third-party repo: adoption means native
  reimplementation of a mechanism in our own files, never importing
  their code, skills, hooks, or installers. No desk strategy, sizing,
  stops, or thresholds; the Tensor engine is never touched. No public
  save. No secret, key, token, or credential in any memory file, note,
  or vault page, ever (see the Rejected list, Section 4).
- Outcome: a de-duplicated overlap map, one verdict per canonical
  mechanism (ADOPT with spec, ALREADY-HAVE with the existing machinery
  named, or SKIP with reason), and an explicit rejected list.
- Proof: the verdict counts in Section 2.1 sum exactly across the
  tables in Sections 2.2 to 2.4 (6 + 18 + 24 = 48 canonical mechanism
  rows). Each ADOPT spec names its own proof, to be produced by its
  implementation pass, not by this document.
- Edges: several audit CANDIDATEs are runtime-owned surfaces (people
  pages, MEMORY.md itself). Those are classified SKIP in this program
  with the authority reason named, not silently dropped.

## 1. Overlap map

### 1.1 Where the seven repos duplicate each other

The seven repos are not seven systems. They are one pattern, stated
seven times, plus a format layer and a handful of genuinely original
mechanisms each.

Core pattern shared by six of seven (all except kepano): Andrej
Karpathy's LLM Wiki. Immutable raw sources compiled by an agent into
linked Markdown pages, with an index, an append-only log, ingest /
query / lint flows, and contradictions preserved instead of overwritten.

| Cluster | 1 kepano | 2 AgriciDaniel | 3 eugeniughelbur | 4 Astro-Han | 5 undefined-ui | 6 charlie947 | 7 MehmetGoekce |
|---|---|---|---|---|---|---|---|
| Raw sources compiled into linked pages | no (format only) | yes, core | yes, wiki layout option | yes, core | yes, core | yes, Step 2 | yes, core (L2) |
| Fixed frontmatter / typed page schemas | properties only | yes | yes | header blocks | yes | 4-field minimum | yes, 5 types |
| Index catalog plus append-only log | Bases is an index alternative | yes | yes | yes | yes, plus Gaps | index only | hub indexes plus Access-Log |
| Ingest flow with triage and compile | no | yes, with value gate | save / ingest commands | yes, with dispositions | yes, with scoped variants | per-source prompt | 5-phase ingest |
| Lint / health pass | no | deterministic lint | health plus freshness lint | 3-tier lint plus checker script | lint plus metrics | one prompted check only | 13-rule lint |
| Contradictions preserved, never silently resolved | no | yes | reconcile, with quote-proof | Status blocks | yes, supersession rules | named in lint prompt only | State plus History blocks |
| Query: index first, then search, cite pages | no | yes, budgeted tiers | /obsidian-world load ritual | yes | yes, with Read footer | no | Hub-Index-Routing |
| Session load / save ritual | no | hot cache plus hooks | /obsidian-save and /obsidian-world, core pitch | deliberately none | no | no | deliberately no hook |
| Hooks or scheduled automation | no | SessionStart / Stop hooks | hooks plus scheduled agents plus background agent | deliberately none | docs-only hooks advice | no | none of its own |
| Obsidian as the surface | yes, the whole repo | vault target | vault target | format only | vault target | vault target | Logseq or Obsidian |
| Secrets in memory instructed | no | no, prohibited | no, keys kept outside vault | no | no, prohibited | no | YES, L1 credentials (REJECTED, Section 4) |

Genuinely original contributions, one or two per repo, are where all
adoption value lives:

- kepano: Bases, the idea of an index as a query over properties
  instead of a hand-maintained copy. Everything else is dialect.
- AgriciDaniel: hash-preconditioned operation transactions with
  content-bound approvals, the three-ledger provenance split
  (source manifest, source ledger, claim ledger with independence
  keys), the compilation-value gate, and extractive fold checks.
- eugeniughelbur: the OKM freshness policy with a mechanical linter
  (FRESH-1 to FRESH-5), reconcile's verbatim quote-proof gate, and
  bi-temporal timeline arrays.
- Astro-Han: the report-only grounding verifier (check_evidence.py
  pattern) with its compile-time locate-before-write half, the
  machine-readable No material triage disposition, the three-tier
  lint authority table, and the archived-answer page class.
- undefined-ui: the bounded raw ingest queue (oldest first, stop and
  report over 20 pending, fixed report shape), typed links, the Gaps
  queue, and the four-number link-graph health series with vanity
  metrics banned.
- charlie947: one thing only, a native ingest path for external AI
  chat exports, wrapped in onboarding for non-technical Mac users.
- MehmetGoekce: the L1-honesty package (asserts-current-behavior
  claim class, verified stamps, due windows, read-only evidence
  re-verification with correction-atomicity), hub routing-line
  discipline, and demote-not-delete LRU prune.

Duplication inside the sweep itself: the bounded raw inbox
(undefined-ui candidate 1), the immutable source archive
(AgriciDaniel), and the raw-versus-compiled split (charlie947) are
one mechanism stated three times. The synthesis counts it once
(ADOPT A1). The freshness lint (eugeniughelbur) and the verified
stamp package (MehmetGoekce) are two halves of one staleness problem
and are adopted as one package (ADOPT A3).

### 1.2 Where they duplicate what we already run

Our existing architecture, per MEMORY-SYSTEM.md and the live tree:
Tier 0 platform memory (~/MEMORY.md, ~/memory/ daily logs with claim
id, verbatim quote, and source message ids, people and groups pages
with INDEX.md files, nightly alignment synthesis); Tier 1
~/workspace/midna-book/CONTEXT-SNAPSHOT.md (template-bound, rewritten
nightly from registers, outgoing version archived, monthly recovery
drill); Tier 2 midna-book registers (STATE.md, RULINGS.md,
OPEN-THREADS.md, LESSONS.md with CANDIDATE to TESTED to RULE or DEAD
lifecycle, STRATEGIES.md plus per-strategy records); Tier 3
append-only evidence (JOURNAL.md, ledger.json, daily logs). Around
it, the ~/AGENTS.md enhancement disciplines already run as code in
~/workspace/tools/: approvals.py (content-bound approvals, discipline
18), memory_store_check.py and memory_reconcile.py (memory write
boundary and store-to-index reconciliation, discipline 30),
done_check.py (discipline 32), redact.py (capture-time redaction),
dedup_ids.py, effect_queue.py, near_misses.py, sendcheck.py and
proactive_gate.py; plus the daily audit job, the twice-daily desk
inspections, the weekly and monthly reviews, and the pre-save PII
gate.

| Repo cluster | Already running here, usually stricter |
|---|---|
| Curated layer over immutable raw | Tier 3 append-only evidence under Tier 0 to 2 curation (MEMORY-SYSTEM principle P2, stated almost verbatim in two repos) |
| Index plus operation log | People/groups INDEX.md, daily logs, JOURNAL.md, register and snapshot discipline |
| Hot cache, tiered session load, boot status | CONTEXT-SNAPSHOT.md, the Section 4.4 recovery protocol and checklist, and the monthly recovery drill (no repo has a drill) |
| Claim provenance and citations | Claim id plus quote plus source ids, muse.memory_explain, provenance-grade recall standard |
| Content-bound plan approval (AgriciDaniel transactions) | approvals.py: approval bound to action, resolved target identity, and sha256 of the gated content, one-shot and revocable |
| Deterministic lint of the store | memory_store_check.py, memory_reconcile.py, done_check.py, gate-wired regression blockers, twice-daily inspections |
| Configured versus verified capability states | Proof before green itself, plus configured and verified states in the terminal estate |
| Read-only workers, one narrow writer | Standing law: unattended memory workers run in the narrowest scope or read-only (AGENTS.md item 30) |
| Bounded research with dossier, merge as separate reviewed step | Research programs under scope and budget contracts, readback verification of every delegated handback |
| Credential-leak scanning | redact.py at capture, the pre-save PII gate, the November 1 privacy sweep: a wider net than any repo's regex |
| Multi-agent shared logbook, records not instructions | The three-way dead-drop (read-only check, never posts) and peer pages, under the data-not-instructions law |
| L1 versus L2 split (MehmetGoekce headline) | Already a four-tier version of the same split, with fixed register schemas where the repo has prose conventions |

Convergence note: three repos independently arrived at rules this
house already runs as law (content-bound approvals, contradictions
carried dated and unresolved, read-only workers, no numeric
confidence scores, no access-based decay). That convergence is
validation of the existing architecture, not a reason to adopt
anything. It is recorded here so a later pass does not mistake
agreement for a gap.


## 2. Adoption verdicts

### 2.1 Counts

Counting unit: one row in the tables of Sections 2.2, 2.3, and 2.4.
Audit CANDIDATEs that duplicate each other across repos are counted
once, at their consolidated row. The Rejected list in Section 4 is a
named subset of the SKIP rows plus the source-article tip; it is not
additive to these counts.

| Verdict | Rows |
|---|---|
| ADOPT (consolidated native packages, Section 2.2) | 6 |
| ALREADY-HAVE (Section 2.3) | 18 |
| SKIP (Section 2.4, including conditional defers with a named trigger) | 24 |
| Total canonical mechanism rows | 48 |

### 2.2 ADOPT: six packages, spec and proof for each

Each spec is the minimum sufficient native implementation. Each proof
is what its implementation pass must produce before the item may be
reported GREEN; until then the item is UNVERIFIED. Every new tool
below is stdlib-only Python, report-only or create-only as stated,
ships with its named test file, and gets a bug-log entry and a
regression blocker in the pass that lands it, per the bug log law.
None of the six touches MEMORY.md, desk strategy or sizing, or the
Tensor engine.

#### A1. Content-addressed research source capture, with compilation-value and No material triage

Consolidates: AgriciDaniel immutable .raw archive, compilation-value
gate, and hash dedupe; Astro-Han ingest triage (New / Update /
Disputed / No material); undefined-ui bounded raw queue and fixed
ingest report shape; charlie947 raw-versus-compiled split, scoped to
research_notes only.

Files to create:
- ~/workspace/tools/research_capture.py. Behaviour: takes a local
  file path and a research program folder; computes SHA-256; copies
  the file create-only into
  ~/workspace/research_notes/<program>/sources/raw/ (an identical
  hash already present is a no-op reported as already captured; the
  same slug with different content creates a new dated capture and
  never overwrites); creates or updates
  ~/workspace/research_notes/<program>/sources/MANIFEST.json in the
  same write, each entry carrying sha256, captured date, original
  filename, byte size, and locator or URL when supplied. No network,
  no execution of the captured file, no writes outside the named
  program folder.
- ~/workspace/research_notes/RESEARCH-INGEST.md. The convention:
  pending sources are processed oldest first; more than 20 pending
  stops the pass and reports the count; every source earns exactly
  one disposition, New, Update, Disputed, or No material, recorded
  in the program's INGEST-LOG.md in the exact machine-readable form
  `## [YYYY-MM-DD] ingest | <disposition>: <raw path>`; the
  compilation-value gate in words: a page is created or expanded
  only when the source adds durable synthesis, navigation, a
  decision, or a reusable connection, and a source may earn only a
  manifest record or a No material log line, never a paraphrase made
  merely to create a page; the fixed ingest report shape (new,
  updated, links, contradictions, gaps).
- Per program, on its next ingest after adoption: sources/raw/,
  sources/MANIFEST.json, INGEST-LOG.md. No mass backfill of existing
  program folders.

Proof: ~/workspace/tools/test_research_capture.py passes, covering
duplicate capture as a no-op, changed content creating a second
capture with the first byte-identical on readback, and manifest hash
equal to an independent sha256sum of the captured file; plus one
real capture into this sweep's folder with the manifest read back.

#### A2. Report-only grounding verifier, with the locate-before-write rule

Consolidates: Astro-Han check_evidence pattern (C1 and C2), the
strongest single mechanism in the sweep; AgriciDaniel fold numeric
traceability is the same instinct and is served by this tool for
research pages.

Files to create:
- ~/workspace/tools/check_evidence.py. Native, stdlib only (re, sys,
  pathlib, dataclasses), report-only: it writes nothing and its exit
  code carries no verdict. Behaviour: for each compiled research
  page, extract a frozen candidate set (direct quotes of 15 or more
  characters, ISO dates, and high-signal numbers: thousands-grouped,
  dotted, suffixed K/M/B/percent, or 4 or more digits); strip fenced
  and inline code, links, metadata headers, and Status blocks (A6
  format) before extraction; verify each candidate appears verbatim
  in the body, metadata header excluded, of the source files named
  in the page's Sources or Raw field, resolving those files through
  the A1 manifest where one exists. Report three sections only:
  fidelity suspects (misses, which are suspects and never verdicts,
  since derived values and product names legitimately appear),
  evidence errors (page has no source field, a source link does not
  resolve, or a source path escapes the program's sources/ tree),
  and unreferenced sources (raw captures no page references,
  exempting captures whose INGEST-LOG.md line carries the No
  material key from A1). It also flags malformed A6 Status blocks.
- ~/workspace/tools/test_check_evidence.py, fixtures below.
- The locate-before-write rule written into RESEARCH-INGEST.md
  (created in A1): every number, date, and quote is located in the
  source before it is written and written exactly as found (42K in
  the source is 42K on the page, not 42,000); a derived value shows
  its components so each is findable; a value that cannot be located
  is dropped or stated without precision.

Proof: the fixture test passes and demonstrates the fail direction:
a planted altered number is flagged as a suspect, a verbatim page
reports clean, a missing source field is an evidence error, and a No
material capture is not reported unreferenced. Then a first live run
over this sweep's folder is filed in this folder with counts, with
suspects judged individually in that report, not waved through.

#### A3. Freshness lint and verified-claim package for the operational registers

Consolidates: eugeniughelbur OKM freshness lint (FRESH-1, FRESH-2,
FRESH-3); MehmetGoekce L1 claim class with verified stamps and the
prune evidence loop with correction-atomicity. Scoped to the
midna-book registers only: STATE.md, RULINGS.md operational lines,
and CONTEXT-SNAPSHOT.md. MEMORY.md is runtime-owned and out of
scope; people and groups pages are out of scope.

Files to create or change:
- ~/workspace/tools/freshness_lint.py. Native, stdlib only,
  report-only. Behaviour over STATE.md and CONTEXT-SNAPSHOT.md:
  FRESH-1 (error): a present-tense quantitative claim about a
  volatile noun (counts, balances, statuses, roster sizes) outside a
  dated container and without a proof timestamp; FRESH-2 (warning):
  a stamp older than its window (STATE.md program rows, 7 days per
  MEMORY-SYSTEM Section 3.4; snapshot age, 36 hours per Section
  4.3), where each aged stamp must be answered in the register as
  re-observe (new value, new stamp), convert (number dropped,
  pointer kept), or retire (moved into a dated note as history);
  FRESH-3 (error): a pointer or proof path that does not resolve.
- Claim-class fields, added by the register schemas' owners in the
  implementation pass, not by this program: a STATE.md or RULINGS.md
  line asserting current system behavior may carry
  `asserts-current-behavior: true` with `verified: YYYY-MM-DD`;
  decisions, preferences, identity, and rationale carry `false` and
  are never due. Due means never verified or older than 90 days.
  The due list is computed by freshness_lint.py from those fields;
  no stale flag is ever stored as a second field.
- Evidence loop, run inside the existing weekly review: for each due
  claim, read-only local evidence only (file existence and content,
  manifests, version and help output; never a side-effecting command,
  never a remote fetch), verdict per claim of supports, contradicts,
  or inconclusive, recorded in the weekly review file.
  Correction-atomicity is the binding rule: a contradicted claim may
  be re-stamped only together with its corrected text, applied at
  once to the register body, its description or index line, and any
  snapshot line carrying it. Demotion or deletion of any claim keeps
  per-item owner confirmation and a dated archive copy first; nothing
  is automatic.
- Wiring: the daily audit's health checks gain this lint as check
  M10, added to the audit job body with cron.update preserving the
  existing body, schedule, and delivery, verified with cron.view.
  MEMORY-SYSTEM.md Section 8.5 is amended in the same pass to record
  M10, so the spec and the gate do not drift.

Proof: fixtures in ~/workspace/tools/test_freshness_lint.py pass and
demonstrate the fail direction (a planted unstamped claim errors
FRESH-1, an aged stamp is listed, a broken proof pointer errors
FRESH-3); a live run over STATE.md and CONTEXT-SNAPSHOT.md produces
a due list filed with the weekly review; and at least one due claim
is processed end to end with its verdict and, if contradicted, its
atomic correction shown by readback of all three locations.

#### A4. Verbatim quote-proof gate for contradiction work

Source: eugeniughelbur reconcile. Our dated-conflict practice
(MEMORY-SYSTEM Section 8.2) already carries both readings unresolved;
what it lacks is a mechanical proof that a claimed contradiction
exists in the sources before work is spent on it.

Files to create or change:
- ~/workspace/tools/verify_quotes.py. Native, stdlib only,
  report-only. Behaviour: input is a list of (path, line, quote)
  triples naming two sides of an alleged contradiction; each quote
  must be at least 12 characters and match the cited line
  character-for-character; the tool prints pass or fail per quote
  with the file and line, and writes nothing.
- The weekly review's RULINGS.md versus MEMORY.md divergence pass,
  and the monthly full diff, gain one rule in their written agendas:
  a contradiction is actionable only when both of its quotes pass
  verify_quotes.py; pairs that do not pass are dropped from the work
  list and listed by name in the review file under "Dropped as
  unproven". Proven but genuinely ambiguous pairs become dated
  conflict entries under Section 8.2, both readings verbatim. No
  contradiction is ever auto-rewritten by this gate.

Proof: ~/workspace/tools/test_verify_quotes.py passes (an exact quote
passes; a one-character mutation fails; a quote shorter than 12
characters is refused); and one real weekly or monthly review file
shows the gate in use, including its Dropped as unproven list, even
if that list is empty and says so.

#### A5. Machine-readable claim ledger for research and forecast claims

Source: AgriciDaniel claim ledger and source ledger, scoped down.
Scope is research and forecast claims only. Facts about the user are
never entered: MEMORY.md stays canonical there. No desk strategy,
sizing, or threshold is a claim-ledger entry.

Files to create:
- ~/workspace/research_notes/claim-ledger.json, created with its
  schema header and an empty entries list. Entry fields: claim_id
  (deterministic, produced with the dedup_ids.py convention),
  statement, locations (pages carrying the claim), supporting and
  contradicting source ids (from A1 manifests), authority per source
  (official, primary, secondary, community, synthetic, unknown),
  independence_key per source (sources sharing a key, or the same
  canonical origin under respelling, do not count as independent
  corroboration), risk (ordinary or high), assessment (accepted,
  provisional, contested, unsupported, deprecated), refresh_due
  (date). Staleness is computed from refresh_due at read time and
  never stored as a flag.
- ~/workspace/tools/claim_ledger.py. A validator only: it checks the
  schema and the acceptance rules and reports violations, writing
  nothing. Rules: accepted requires at least one fresh, active,
  non-synthetic supporting source; high-risk accepted requires
  supporting sources with at least two distinct independence_keys;
  unsupported is a valid assessment, not an error; contradictions
  are preserved (a claim with contradicting sources is contested
  unless the contradiction is itself resolved by a dated entry).

Proof: ~/workspace/tools/test_claim_ledger.py passes, covering:
syndicated copies sharing one independence_key fail the high-risk
acceptance rule; an entry past refresh_due is reported stale by
computation; an unsupported entry validates clean. The live ledger
validates clean on its schema at creation, and the first real
entries are added only by a research pass that cites its A1 sources.

#### A6. Research page hygiene convention: lint authority tiers, Status blocks, cascade updates, archived answers, Gaps

Consolidates: Astro-Han three-tier lint authority (C4), Status block
micro-format (C5), cascade-update step (C6), and archived-answer
page class (C7); undefined-ui Gaps queue and synthesis page
contract; charlie947 named lint report, as the report this
convention produces for research folders.

File to create:
- ~/workspace/research_notes/RESEARCH-CONVENTIONS.md, containing:
  1. The three-tier lint authority table. Safe Fixes, applied and
     listed: index entries synced to pages, a dead index entry
     marked [MISSING] and never deleted, a dead internal link
     repaired only when a filename search finds exactly one match
     (zero or multiple matches are reported, never guessed).
     Mechanical Reports, produced by A2's verifier and never
     auto-fixed. Judgment Reports (contradictions, missing conflict
     annotations, orphan pages, frequently mentioned concepts with
     no page), reported and never fixed by the lint pass.
  2. Status block micro-format: directly under a superseded or
     disputed claim, `> **Status: Outdated** (YYYY-MM-DD)` or
     `> **Status: Disputed**`, each with what changed and its source
     attribution; the old claim stays in place. A block missing its
     date or explanation is malformed and is an A2 lint item.
  3. Cascade step for research ingest: after the primary page is
     compiled, full-text search the program corpus for the source's
     entities and aliases, not just the index; update every
     materially affected non-archive page; refresh its Updated date
     to the content-change date, never the filesystem timestamp and
     never for typo fixes.
  4. Archived-answer class: a saved query synthesis is always a new
     page, never merged into compiled pages; it carries an Archived
     date, cites the compiled pages it drew on, has no Sources or
     Raw field, is exempt from A2 verification and from cascade
     updates, and is prefixed [Archived] in its program index.
  5. Gaps: each research program index or INGEST-LOG.md carries a
     Gaps section listing pages and topics that are referenced but
     do not exist, added at ingest time, as a queue.
  6. Synthesis page contract: a synthesis page exists only when it
     says something no single source did, and carries The question,
     What the sources say, Where they disagree, Current position,
     and What would change it; claim confidence labels are stated,
     reported, self-reported, and unverified, and a self-reported
     label is never dropped downstream.

Proof: RESEARCH-CONVENTIONS.md exists and is cited from
RESEARCH-INGEST.md (A1); and one demonstration lint pass over this
sweep's folder, run under the authority table, is filed in this
folder listing its Safe Fixes applied, its Mechanical Reports, and
its Judgment Reports separately, with no Judgment item fixed by the
pass. That report, not the convention document alone, is the proof.


### 2.3 ALREADY-HAVE: 18 rows, existing machinery named

| # | Mechanism (source repos) | Already running as |
|---|---|---|
| H1 | Fixed-schema frontmatter and typed pages (2, 3, 4, 5, 7; kepano properties) | MEMORY-SYSTEM Sections 3.4 to 3.6 and 5.2 register schemas enforced by the daily audit; platform claims carry id, date, and source; midna-book registers on disk |
| H2 | Index catalog plus append-only operation log (2, 3, 4, 5, 6, 7) | People and groups INDEX.md, ~/memory/ daily logs, JOURNAL.md, snapshot archives |
| H3 | Hot cache, tiered load (L0/L1/L2), five-line boot status (2, 3) | CONTEXT-SNAPSHOT.md Tier 1, MEMORY-SYSTEM Section 4.4 recovery protocol and checklist, monthly recovery drill |
| H4 | Save only on explicit selection; no automatic whole-transcript capture (2) | Memory write boundary, AGENTS.md item 30; memory_store_check.py blocks out-of-boundary writes |
| H5 | Claim provenance with specific citations (2, 3, 5) | Daily-log claim id, verbatim quote, and source message ids; muse.memory_explain; claim-state-aware reporting in inspections |
| H6 | Contradictions preserved, supersession with history, never resolved by recency (2, 3, 4, 5, 7) | Dated-conflict practice, MEMORY-SYSTEM Section 8.2; MEMORY.md supersession chain; alignment synthesis carrying both readings. A4 adds only the proof gate on top |
| H7 | Content-bound approvals: inspect, approve the exact content, apply (2) | approvals.py, discipline 18: bound to action, target identity, and content sha256, one-shot, revocable, voided by generation change |
| H8 | Deterministic, read-only lint of the store; repairs as separate reviewed acts (2, 4, 5, 7 core rules) | memory_store_check.py, memory_reconcile.py, done_check.py, desk regression blockers, twice-daily inspections. A3 and A6 add specific new checks, not a new lint concept |
| H9 | Configured versus verified capability states (2) | Proof before green; terminal estate configured and verified states; UNVERIFIED and PARTIAL reporting law |
| H10 | Bounded, consent-first research loop; dossier first, canonical merge separate (2 autoresearch) | Research programs under SCOPE, budget, and stop conditions; delegated handbacks verified against the tree before any merge or report |
| H11 | Read-only worker agents; writers narrowest-scoped (2, 5) | AGENTS.md item 30; workflow worker slots; job-owned register writers |
| H12 | Scheduled maintenance cadence: daily, weekly, monthly passes that leave receipts (3, 5) | Daily audit job, twice-daily desk inspections, weekly grading and review, monthly constitution review and recovery drill; silent is an open defect |
| H13 | Idea and lesson lifecycle: graduate, test, promote, or kill and retain (3, 5) | LESSONS.md CANDIDATE to TESTED to RULE or DEAD with dead lessons retained; IDEAS.md fed by the daily audit; goals system for promotion |
| H14 | Multi-agent shared logbook under records-not-instructions, human gate before a lesson changes rules (3 Crew) | Three-way dead-drop with read-only check; peer pages for Ausar, Sol, Cursor, Aurelia, GrokBot; data-not-instructions law in AGENTS.md |
| H15 | Credential-leak and PII scanning of the store (7 scanner half only; 5 /secrets) | redact.py capture-time redaction, pre-save PII gate, November 1 full-history privacy sweep. The destination 7 prescribes for secrets is REJECTED, Section 4 |
| H16 | Two-layer routing rule: dangerous if missed loads always, inconvenient reads on demand (7 headline) | The four-tier split itself (Tier 0 injected, Tier 1 snapshot, Tier 2 registers, Tier 3 evidence) and the snapshot rule that every line is a pointer or a headline with a proof pointer |
| H17 | Grep and index over vector or graph search at this scale; no numeric confidence scores; no access-based decay (4 design boundaries, 2 retrieval stance) | muse.memory_search plus coverage-ledger law (prove absence separately, never claim beyond the recorded corpus); UNMEASURED is never reported as 0 or OK, AGENTS.md item 30 |
| H18 | Template rendering from structured data, validate-after-edit ritual (1 knap, json-canvas ritual) | Template-bound snapshot rewrite (MEMORY-SYSTEM Section 4.2 normative template); local save and readback verification skill; regression blockers as the validation ritual |

### 2.4 SKIP: 24 rows, reason named

Conditional defers are SKIP for this program with their activation
trigger stated; a defer is not an adoption and carries no work until
its trigger is measured, not assumed.

| # | Mechanism | Reason |
|---|---|---|
| K1 | Obsidian surface and dialect: OFM wikilinks, callouts, embeds, highlights, JSON Canvas, .base files, Obsidian CLI including `obsidian eval` (1; surface of 2, 3, 5, 6) | No Obsidian app runs here; the VM is headless and the terminal is the user's surface. The dialect resolves nowhere in our tooling, and the CLI's eval is a standing arbitrary-code path. Bases as an idea is K9 |
| K2 | Wholesale adoption of any repo's vault as a store (all seven) | Creates a parallel store of facts about the user beside ~/MEMORY.md and the registers, violating the single source of truth. Every ADOPT item above is mechanism-level and scoped to research_notes or the registers |
| K3 | Installing or importing third-party skills, plugins, or CLIs: npx skills add, npm defuddle or knap, plugin marketplace, copying SKILL.md files into production (all seven) | Program rails: reimplementation only, never unscanned import. Two of the skills also carry trigger descriptions broad enough to shadow native memory-query behavior |
| K4 | Session, per-prompt, and post-compaction hooks, and any unattended background agent writing memory (2 hooks, 3 hooks and background agent, 5 docs advice) | Third-party code executing on session start and on writes is a persistence and prompt-injection surface; the permission-skipping writer is separately REJECTED, Section 4 |
| K5 | MCP servers exposing the vault (3, 5, 6 connector step) | A second access path to the same facts with a bearer key granting full read and write, solving a problem direct file access does not have |
| K6 | Egress research profiles: vault content sent to third-party research APIs, Anthropic contextual prefixes under allow-egress, remote rerank (3 toolkit, 2 profiles) | Memory content leaving the machine as gap-fill queries is exfiltration by design here; the hard-reject form is Section 4, R7 |
| K7 | A local BM25 plus Ollama rerank stack (2) | Duplicates muse.memory_search with a second index and a large model dependency; no measured retrieval failure justifies it |
| K8 | Defuddle-style clean web extraction utility (1) | SKIP, conditional defer. Browser fetch already covers the need. Trigger to revisit: measured web-ingest volume where extraction cost is material, and then only as a native or separately scanned and pinned install, never an unscanned npm global |
| K9 | Bases-style query-defined index views (1) | SKIP, conditional defer. The pattern is sound and our INDEX.md files are hand or runtime maintained. Trigger: index drift becomes a measured problem (repeated stale-index defects), not a volume guess |
| K10 | Tiered query read budgets (Quick 12 KiB, Standard 48 KiB, Deep 128 KiB) and the labelled-query retrieval bench (2) | SKIP, minor defer. Memory search already returns bounded, sourced results. Trigger: a measured retrieval-quality failure on a store we control |
| K11 | Extractive log fold with batch 2^k rollups (2) | SKIP, defer. Governed compaction already exists (2026-10-31 rulings: exact-duplicate compaction with receipts, 90-day retention for templated restatements). Trigger: daily-log or snapshot-archive volume that exact-duplicate compaction demonstrably cannot hold. Its numeric-traceability check is served sooner by A2 |
| K12 | Stable page addresses (c-000001) as a second addressing layer (2) | Our files are path-addressed and claims already carry permanent ids; a second layer is bookkeeping with no failure it prevents |
| K13 | Methodology modes (LYT, PARA, Zettelkasten), preset layouts, folder-map resolvers, import-into-wiki migration (2, 7) | Our layout is fixed by law and verified. A switchable filing methodology is a fork risk against the single source of truth |
| K14 | Per-operation Git checkpoints (2, 5, 7) | The backup seal system already versions the workspace with proven restores; per-operation commits would flood history |
| K15 | Bi-temporal timeline: arrays on people pages (3) | SKIP in this program on authority, not merit: people pages are runtime-owned, and this program may not edit or re-schema them. Recorded here so the idea is visible to the platform layer's own review, with no work implied |
| K16 | Formal per-layer token budgets and a PINNED current-task block (3) | SKIP, minor defer. Tier 1 already targets under 200 lines and the recovery checklist already bounds the load. Trigger: a recovery drill failure attributed to layer size |
| K17 | Proactive save-reminder triggers (wrap-up signals, exchange counts) (3) | SKIP, defer. Moment 1 capture plus the daily audit sweep already catch rulings and decisions; reminder pings also sit badly with the main chat law's silence rules. Trigger: a named ruling lost because neither Moment 1 nor the audit caught it |
| K18 | Typed-link vocabulary (supports, contradicts, extends, part-of, applies) (5) | SKIP, defer. No local consumer parses typed links today, so the vocabulary would be annotation without a query behind it. Trigger: A6 lint passes repeatedly needing relation-filtered queries over research pages |
| K19 | Four-number link-graph health series, access log with matched reasons, LRU demote-not-delete prune (5, 7) | SKIP, conditional defer as one package. Sound mechanics, unproven need: register and index volume is small and nothing has been shown unroutable due to size. Trigger: measured index bloat or orphan growth in an A6 or store-check report. Any future access log stays strictly separate from near_misses.py, which is diagnostics only and never feeds ranking or demotion by law |
| K20 | Universal hub routing-line discipline and the exact State plus History block format (7) | SKIP, low defer. People and groups index lines already pair path with description (H16). Extending a 120-character routing discipline to every register is formatting work with no measured retrieval failure behind it; A3's routing-specific value (due claims) is adopted without it |
| K21 | Native export-ingest for external AI histories (ChatGPT, standalone Claude) (6) | SKIP, conditional. Genuinely new only if the owner supplies an export for that purpose; none was supplied or requested in this program, and Step 1 execution was unauthorized and undone in the audit. If an export is ever supplied, the path is: per-conversation Markdown with frontmatter, into the existing daily-log and people-page pipeline, never a new vault, with the off-machine processing caveat stated to the owner first |
| K22 | Minor output formats as a bundle: changed-my-mind trace, query Read and Not covered footer, quiz and explain-back self-testing (5) | SKIP, low defer. The underlying practices exist (supersession records, PARTIAL reports naming open rows, H6 and H13). The exact formats add polish, not capability; the quiz has no current consumer |
| K23 | Non-memory tooling bundle: Telegram capture, kanban boards, Dataview, graph export to Gephi, static site and course tracks, /create drafting, iMessage Channels, Granola and NotebookLM connectors (3, 5, 6) | Not memory mechanisms, or channels and services the user does not use, or surfaces Midna already reaches by stronger routes. The iMessage permission pattern is separately REJECTED, Section 4 |
| K24 | Generic reasoning rituals and author production claims as adoption evidence (2 think loop; 4 and 5 scale claims) | InfinityBlade review-mode order already governs reasoning gates. Unverifiable private-corpus numbers (94 articles, daily compounding) prove the formats render, not that a mechanism fits here; adoption above rests on mechanism fit only |

## 3. What adoption changes, in one paragraph

If all six ADOPT packages land with their proofs, exactly three
surfaces change: research_notes gains a capture, ingest, and hygiene
discipline (A1, A2, A6) with a claim ledger beside it (A5); the
midna-book registers gain a mechanical freshness gate and a
verified-claim due list (A3); and contradiction work anywhere in the
reviews gains a quote-proof gate before it may consume effort (A4).
Nothing about facts concerning the user moves, no new store opens,
and MEMORY.md is touched by none of it.

## 4. Rejected list (explicit, with reasons)

Rejected means refused, not deferred: these do not return on a
trigger. Each is recorded so no later pass resurrects it as a repo's
recommended practice.

- R1. Keeping secrets in memory. A source-article item in this
  sweep's corpus suggests storing secrets, keys, or credentials in
  memory or notes for convenience. REJECTED by the owner, expressly
  and in advance, and recorded here as rejected. No secret, key,
  token, or credential is ever written into ~/MEMORY.md, any daily
  log, any register, any research note, or any vault page. Secrets
  live only in the Secure Vault and connector-managed storage, used
  through the approved credential flow. Plain Markdown is the
  widest-circulating, most-quoted, most-backed-up surface in this
  system, which is exactly why nothing secret may sit on it.
- R2. Credentials must live in the auto-loaded memory layer
  (MehmetGoekce/llm-wiki: README, docs/l1-l2-architecture.md "if it
  is a secret, it goes in L1. Period.", FAQ, SKILL.md, and a
  reference_creds.md example). This is R1 in its most explicit repo
  form and is REJECTED on the same grounds. Its stated justification,
  git exclusion of the memory directory, is not a secret store:
  auto-loaded memory is injected into sessions, summarized, backed
  up, and synced. The separable sound half, scanning the on-demand
  layer for credential patterns and blocking on a hit, is endorsed
  and already ALREADY-HAVE as H15. A leaked credential here is
  rotated and removed, with at most a vault pointer recorded, never
  the value.
- R3. Downloading standing instructions from a mutable third-party
  source at setup time (charlie947 Step 2a: curl of an unpinned gist
  into the vault CLAUDE.md). REJECTED. Instruction files in this
  system are authored and reviewed locally; an unpinned external
  file that an agent reads as standing orders is a supply-chain and
  prompt-injection exposure, whatever it contains today.
- R4. An unattended background agent writing to the memory of record
  with permissions skipped (eugeniughelbur PostCompact agent,
  --dangerously-skip-permissions). REJECTED. It is incompatible with
  the memory write boundary (AGENTS.md item 30: unattended memory
  workers run in the narrowest scope or read-only), however honestly
  the source documents the trade.
- R5. Auto-rewriting memory on ingest and auto-reconciling
  contradictions (eugeniughelbur self-rewriting vault posture).
  REJECTED as a posture. Contradictory evidence is a stop signal
  here: both readings are carried dated and unresolved until new
  evidence from the system of record or the owner's ruling settles them
  (MEMORY-SYSTEM Section 8.2). The compatible half of that repo,
  reconcile's quote-proof and conflict-page path, is adopted as A4
  precisely because it does not auto-resolve.
- R6. Broad-permission channel patterns as an intake route:
  iMessage Channels holding Full Disk Access plus Messages
  Automation in a long-running session (charlie947 Step 3b), and a
  local HTTP MCP server whose single bearer key grants full read
  and write to every note (undefined-ui setup guide). REJECTED as
  patterns. The permission breadth is disproportionate to any intake
  benefit, and both duplicate access the user already has by safer
  routes.
- R7. Sending memory or vault content to third-party APIs to fill
  knowledge gaps (eugeniughelbur research toolkit sending vault
  notes and gap queries to xAI, Perplexity, Gemini, Tavily, Brave,
  and transcription providers; AgriciDaniel allow-egress profiles
  sending page bodies off-machine). REJECTED for any surface
  containing facts about the user. Ordinary web research on public
  topics under existing program scopes is unaffected; what is
  rejected is memory content as the query payload.

## 5. Program status and next step

Per-repo audit status stands as delivered in AUDIT-1 to AUDIT-7.
This synthesis is PARTIAL in the InfinityBlade sense: the overlap
map is complete over the seven audits as delivered, the verdict
tables sum (6 + 18 + 24 = 48), and the rejected list is explicit,
but no ADOPT item is implemented, so none is GREEN. The next step,
if the owner wants it, is a separate implementation program that
lands A1 to A6 in spec order (A1 and A2 first, since A5 and A6 cite
their files), each with its named tests, bug-log entry, and blocker,
and each reported on its own proof. Nothing in that program needs a
ruling on desk strategy, sizing, or the Tensor engine, and nothing
in it edits MEMORY.md.

Provenance: the seven audit files in this folder (each carrying its
own repo-level provenance), MEMORY-SYSTEM.md, the midna-book file
list and CHARTER.md, ~/AGENTS.md enhancement disciplines items 13 to
35, and the ~/workspace/tools/ file list those items name.
