# AUDIT 4 — Astro-Han/karpathy-llm-wiki

Program: Obsidian second-brain sweep, 2026-11-02. Auditor: workflow subagent, item 4.
Status: PARTIAL (audit complete on the final repo state read; adoption itself is not
authorized in this program, so candidate verdicts are recommendations, not landings).

## SCOPE (InfinityBlade)

- Surface: one third-party repo, read-only, assessed for mechanisms that could extend
  Midna's existing file-based memory (~/MEMORY.md, ~/memory/, ~/workspace/midna-book/).
- Constraints: no clone-and-run, no execution of any repo code, installer, hook or README
  step; code read as text evidence only. No edit to MEMORY.md. No parallel store of facts
  about the user. No secrets in any note. No desk strategy, sizing, stops, thresholds, or
  Tensor changes. No public save.
- Outcome: a mechanism-by-mechanism classification (ALREADY-HAVE / CANDIDATE / SKIP)
  grounded in files actually read, with risks named.
- Proof: provenance list below; every load-bearing claim cites a repo file read in full
  or a local file read in full.
- Edges: the upstream idea (Karpathy's gist) is not this repo; downstream forks and
  catalogues were used only to resolve identity, not as evidence about this repo's code.

## 1. Resolution

Resolved: **Astro-Han/karpathy-llm-wiki**
URL: https://github.com/Astro-Han/karpathy-llm-wiki

Three routes, all converging:

1. Web search "Astro-Han karpathy wiki github" returned the repo directly as result 2,
   plus two independent catalogues naming it verbatim:
   tmad4000/listhub `research/llm-wikis-catalog.md` ("Astro-Han/karpathy-llm-wiki —
   https://github.com/Astro-Han/karpathy-llm-wiki — One Agent Skill for Claude Code /
   Cursor / Codex") and naoyanickf/awesome-llm-wiki.
2. GitHub API `GET /repos/Astro-Han/karpathy-llm-wiki` returned 200 with matching
   description: "Agent Skills-compatible LLM wiki for Claude Code, Cursor, and Codex.
   Build a Karpathy-style knowledge base from raw sources, citations, and linting."
3. A third-party research extraction (epappas/alexandria
   `docs/research/raw/05_astrohan_karpathy_llm_wiki_repo.md`) independently records the
   same full name, URL and SKILL.md layout.

Repo facts from the API (read 2026-11-02): created 2026-04-05T06:17:20Z, last push
2026-07-23T16:57:44Z, default branch main, HEAD tree sha
eafcc77001e496cc43499e4923b663aec722c813, 2,659 stars, 313 forks, 11 open issues,
language Python, licence MIT (LICENSE: "Copyright (c) 2026 Yuhan Lei").
Tree is tiny: README.md (7,852 B), SKILL.md (14,342 B), LICENSE, assets/karpathy-tweet.png,
examples/ (4 files), references/ (4 templates), scripts/check_evidence.py (14,475 B),
tests/test_check_evidence.py (28,043 B). There is no package, no server, no hook code.

## 2. Provenance: files read in full

From the repo (via raw.githubusercontent.com and the GitHub API, read as text, never run):

- README.md
- SKILL.md (the load-bearing file; the whole system is this prompt contract)
- scripts/check_evidence.py (the only executable code in the repo)
- tests/test_check_evidence.py (head plus structure; confirms the checker is run locally
  via subprocess in tests, fixtures are synthetic Ghostty/numbers examples)
- references/article-template.md, references/archive-template.md,
  references/index-template.md, references/raw-template.md
- examples/README.md, examples/log-sample.md, examples/ai-coding-tools-index.md
- LICENSE (head, MIT)

Local comparison sources read:

- ~/workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md (the
  governing design: Tier 0 platform memory, Tier 1 CONTEXT-SNAPSHOT.md, Tier 2 registers
  STATE/RULINGS/OPEN-THREADS, Tier 3 append-only evidence; principles P1 one source of
  truth per fact class, P2 append-only bottom / curated top, P3 claims carry sources and
  dates, P5 proof before green)
- ~/MEMORY.md structure (curated facts/laws, CHAT LAW, standing rulings)
- ~/workspace/midna-book/ file list, including memory/ (STATE.md, RULINGS.md,
  OPEN-THREADS.md, LESSONS.md, STRATEGIES.md, CONFIRMATION-TALLY.md, strategies/,
  dated snapshots/ CONTEXT-2026-10-29..31)

Security grep performed on the fetched text: `check_evidence.py` contains no urllib,
requests, socket, subprocess, os, eval or network call; imports are only re, sys,
dataclasses, pathlib. README/SKILL/references/examples contain no secret, password,
API-key, token, hook or cron instruction (the only "hook" hit is the README explicitly
refusing automatic hooks, see Risks).

## 3. What the repo actually is

Not an Obsidian vault and not an app. It is one Agent Skills skill: a SKILL.md prompt
contract that tells any compatible agent (Claude Code, Cursor, Codex, OpenCode) to
maintain a two-directory markdown wiki inside the user's own project. Installation in the
README is `npx add-skill Astro-Han/karpathy-llm-wiki` (not run here, and not recommended
as an import path, see Risks). Claimed production basis: a private wiki of 94 articles,
99 sources, 13 topic directories, maintained daily since April 2026, 87 log entries in
the last 7 days at README writing time. Those numbers are the author's claim about a
private corpus; they are not verifiable from this repo.

### 3.1 Architecture (SKILL.md, "Architecture")

Three layers under a project root:

- `raw/<topic>/` — immutable source material. The agent reads it, never modifies it.
  One level of topic subdirectories.
- `wiki/<topic>/` — compiled knowledge articles, fully agent-owned, one level of topic
  subdirectories only, no deeper nesting. Two special files: `wiki/index.md` (global
  index, one row per article grouped by topic: link, one-line summary, Updated date) and
  `wiki/log.md` (append-only operation log).
- `SKILL.md` itself is the schema layer; `references/` holds the four templates.

Initialization happens only on the first Ingest: create missing `raw/`, `wiki/`,
`wiki/index.md` ("# Knowledge Base Index"), `wiki/log.md` ("# Wiki Log"), never overwrite.
Query or Lint against a missing wiki must refuse ("Run an ingest first to initialize the
wiki") rather than auto-create.

File formats (from references/):

- Raw file: `# {Title}` then blockquote header `> Source:`, `> Collected: YYYY-MM-DD`,
  `> Published: YYYY-MM-DD or Unknown`; body is the source text preserved faithfully,
  formatting noise cleaned, opinions never rewritten. Filename
  `raw/<topic>/YYYY-MM-DD-descriptive-slug.md`, kebab slug max 60 chars, date prefix
  omitted when the published date is unknown, numeric suffix on collision.
- Article: `# {Title}` then blockquote header `> Sources: {Author, date; ...}`,
  `> Raw: [links to ../../raw/...]; ...`, `> Updated: {date the knowledge content last
  changed, not typo fixes}`; body sections distil rather than copy; optional Status
  blocks placed directly under a contested claim; optional See Also section with
  file-relative links.
- Index: per-topic table `| Article | Summary | Updated |`, topic header plus a one-line
  topic description; archived answers prefixed `[Archived]` in the Summary.
- Archive page (a saved query answer): Sources are links to wiki articles (no Raw field),
  `> Archived: {date}`, explicitly a point-in-time snapshot that is never cascade-updated.
- Status blocks (article-template.md): `> **Status: Outdated** (YYYY-MM-DD)` with what
  changed, and `> **Status: Disputed**` with the competing claims, each source-attributed.
  The old claim stays in place; history is never silently rewritten.
- Log entries (examples/log-sample.md): `## [YYYY-MM-DD] ingest | <title>` with
  `- Disposition:`, `- Raw:`, `- Updated:` cascade lines; `## [date] query | Archived: <t>`;
  `## [date] lint | <N> issues found, <M> auto-fixed`.

Relative-link discipline is specified exactly: inside wiki files, links are relative to
the current file (`../../raw/<topic>/<file>.md` from an article); in conversation output,
citations are project-root-relative (`wiki/topic/article.md`); archiving a query answer
requires rewriting the paths from the second convention to the first.

### 3.2 The Grounding Invariant (SKILL.md)

"Every load-bearing fact in wiki/ — numbers, dates, direct quotes — exists verbatim in
the raw/ files linked by that article's Raw field." Compile establishes it
(locate-before-write); lint verifies the mechanical part of it. Because raw/ is
immutable, a verified article stays verified, so there is no incremental verification
state: the checker re-runs over the whole wiki in seconds.

### 3.3 Ingest flow (SKILL.md, "Ingest")

1. Fetch: get the source by whatever tools exist; if unreachable, ask the user to paste.
2. File it in raw/: reuse an existing topic directory if close enough, new directory only
   for a genuinely distinct topic; template header; preserve text.
3. Triage (after filing, before touching wiki/): full-text search wiki/ on the source's
   key entities and synonyms, then state one disposition: New, Update, Disputed (may
   combine with New/Update), or No material (exclusive). No material keeps the raw file,
   logs it, and stops; do not force an article out of a thin source.
4. Compile: same core thesis as an existing article means merge into it (add source to
   Sources/Raw, update sections); new concept means a new article named after the
   concept, not the raw file; multi-topic material goes in the most relevant directory
   with See Also cross-references. One source can do several of these at once.
   Source fidelity rule: every number, date and direct quote must be located in the raw
   file (grep or read) before it is written, and written exactly as found ("if the source
   says 42K, write 42K, not 42,000"). Derived values must show their components so each
   component is findable in raw. A value that cannot be located is dropped or stated
   without precision.
5. Cascade updates: after the primary article, do not rely on the index; full-text search
   the whole wiki for the source's key entities, aliases and touched claims, and update
   every materially affected non-archive article, refreshing its Updated date.
   Superseded or contradicted claims get Status blocks, never silent rewrites. Archive
   pages are exempt from cascade.
6. Post-ingest: update index.md for every touched article; append the log entry. The
   No material log heading `## [date] ingest | no material: <root-relative raw path>` is
   specified as "the machine-readable inventory key" the checker later parses.
7. Research variant (multi-source ingest) only on explicit user request: split the topic
   into angles, search official names/abbreviations/synonyms, deliberately search the
   opposing side (failures, criticism, failed replications) for any core claim, save
   sources as usual; searching may parallelise, compilation must not, because index.md,
   log.md and cascade updates are shared state.

### 3.4 Query flow (SKILL.md, "Query")

1. Read wiki/index.md to locate candidates, then full-text search wiki/ with key terms
   and synonyms. Never claim the wiki has no relevant content until both the index and
   the full-text search are empty, and say that you searched.
2. Read the found articles and synthesise.
3. Prefer wiki content over training knowledge; cite with markdown links to the articles.
4. Answer in conversation; write no files unless asked. Archiving (only on explicit ask)
   follows section 3.1's archive rules: always a new page, never a merge, index entry
   prefixed [Archived], log line appended.

### 3.5 Lint flow (SKILL.md, "Lint") — three authority tiers

This is the most carefully designed part of the repo. Authority is split by risk:

Safe Fixes (agent auto-fixes):
- Index consistency: file missing from index gets an entry (`(no summary)` placeholder,
  Updated from article metadata or file mtime); index entry pointing at a nonexistent
  file is marked `[MISSING]`, never deleted (the user decides); stale Updated in the
  index is synced from the article.
- Internal links, Raw references, See Also links: a dead target is searched by filename
  across the tree; exactly one match means fix the path; zero or multiple matches means
  report (See Also is the exception: zero matches means remove the link, since a dead
  cross-reference is not load-bearing).

Mechanical Reports (run the script; report only, never auto-fix facts):
`python3 <skill-dir>/scripts/check_evidence.py <project-root> [articles...]`
is report-only by construction ("never modifies files", "The exit code carries no
information; the report is the interface"). Its three sweeps:
- Fidelity suspects: extract a frozen, closed candidate set from each article (quotes of
  15+ characters including blockquotes, ISO dates YYYY-MM-DD/YYYY-MM, and high-signal
  numbers: thousands-grouped, dotted, suffixed K/M/B/%, or 4+ digits; small plain
  integers, signs, currencies and spelled-out dates are deliberately excluded), strip
  fences, inline code, links, metadata headers and Status blocks, then verify each
  candidate appears verbatim in the body (metadata header excluded, so a Collected date
  cannot false-pass) of the raw files in the article's Raw field. Misses are "suspects,
  not verdicts": derived values and product names legitimately appear, and a human/agent
  judges each against raw context.
- Evidence errors: articles that cannot be verified at all (missing Raw field on a
  non-archive article, unresolvable Raw links, Raw links escaping raw/ via path
  resolution). Archive pages (Archived header, no Raw) are exempt by rule.
- Unreferenced raw files: raw files no article references, excluding files whose log
  entry carries the No material heading (parsed from log.md). Everything else is a
  genuine ingest backlog reminder.
Post-lint, append `## [date] lint | <N> issues found, <M> auto-fixed` to log.md.

Judgment Reports (agent reports, never fixes): cross-article factual contradictions,
outdated claims lacking a Status block, missing conflict annotations, obviously missing
cross-references (suggest, do not add silently), malformed Status blocks (Outdated
missing its date, either missing its explanation), orphan pages with no inbound links,
missing cross-topic references, frequently mentioned concepts lacking a dedicated page,
archive pages whose cited sources have since substantially changed.

### 3.6 Deliberate non-features (README, "Design Boundaries")

The README records rejected machinery, with reasons from three months of production
logs: no source-hash freshness tracking (raw/ is immutable; hashes guard impossible
events), no persisted line-number citations (every observed fidelity error was "value
absent from the source", which whole-file grep catches), no numeric confidence/quality
scores ("false precision with no calibration"), no per-article review dates, no
access-based decay ("frequently asked is not the same as true"), no retract/bad-source
machinery yet, no automatic hooks or scheduled runs (those belong to the agent harness,
not a tool-agnostic skill), no vector/graph search at 50K–100K tokens of curated wiki
(grep and read are more reliable; add tooling only when recall measurably degrades), no
typed relationship ontologies (link semantics live in the surrounding prose), no OKF
conformance yet (v0.1 draft spec).

## 4. Comparison against Midna's existing system

Existing baseline (from MEMORY-SYSTEM.md and the live tree): Tier 0 platform memory
(MEMORY.md curated by hourly upkeep, append-only daily logs with claim id / quote /
source message ids and muse.memory_explain provenance, people/groups pages with
INDEX.md) is canonical for facts about the owner. The midna-book layer adds Tier 1
CONTEXT-SNAPSHOT.md (rewritten nightly from registers, outgoing version archived to
memory/snapshots/), Tier 2 registers with fixed schemas (STATE, RULINGS, OPEN-THREADS,
LESSONS with a CANDIDATE→TESTED→RULE/DEAD lifecycle, STRATEGIES plus per-strategy
records), Tier 3 append-only evidence, dated-conflict carrying (both readings kept,
neither silently resolved), memory-store/reconcile checks, and a monthly recovery drill
as the proof gate. In other words, Midna already runs a Karpathy-style compiled-memory
system, with stronger provenance and governance than this repo, aimed at facts about the
user and the trading operation rather than at research topics.

### ALREADY-HAVE

- A1. Immutable evidence under a curated layer. Their raw/ vs wiki/ is our Tier 3
  append-only evidence (daily logs, journal, ledger) under Tier 0/1/2 curation
  (MEMORY-SYSTEM.md principle P2, stated almost verbatim). No action.
- A2. Global index plus append-only operation log. Their wiki/index.md and wiki/log.md
  correspond to people/groups INDEX.md, MEMORY.md's dated program records, the daily
  logs, and midna-book's register/snapshot discipline. No new index or log file is needed.
- A3. Never silently rewrite history; mark superseded/contested claims in place. Their
  Status: Outdated / Disputed blocks are the same rule as our supersession chain in
  MEMORY.md, the alignment synthesis's dated-conflict practice, and MEMORY-SYSTEM.md
  section 8. Their block format is a candidate micro-format (see C5), the rule itself is
  already law here.
- A4. Query discipline: search the index and the full text (with synonyms) before
  claiming absence, and say what was searched. This is existing practice via
  muse.memory_search plus the InfinityBlade coverage-ledger rule (prove absence
  separately; never claim "everything" beyond the recorded corpus). The dual-search
  wording is a good phrasing of a rule we already hold.
- A5. Grep-and-read over vector/graph search at this corpus scale, no numeric confidence
  scores, no access-based decay, no per-page review timers. Their Design Boundaries list
  matches standing local doctrine (memory freshness is judged by timestamps inside the
  data; UNMEASURED is never reported as 0 or OK). Agreement, not adoption.
- A6. Compilation must be serial because index/log/cascade are shared state. Our
  equivalent already exists: single-writer discipline on MEMORY.md (runtime upkeep owns
  it) and on the snapshot rewrite (one audit job). No action.
- A7. Session load/save ritual: there is none in this repo, by design (no hooks, no
  scheduled runs; harness's job). Our snapshot recovery protocol and checklist
  (MEMORY-SYSTEM.md sections 4.4–4.5) already exceed anything here. SKIP-shaped, listed
  here so the absence is on the record: nothing to import for session ritual.

### CANDIDATE (genuinely new and useful; reimplement natively, never import)

- C1. Mechanical grounding verifier for compiled research pages (strongest candidate).
  A report-only script in the check_evidence.py pattern: extract a frozen candidate set
  (15+ char quotes, ISO dates, high-signal numbers) from a compiled page, grep each
  verbatim against the bodies of the source files named in the page's source field,
  report suspects/errors/unreferenced sources, fix nothing, exit code carries no
  verdict. Midna has claim-level provenance for memory (memory_explain) and a gestalt
  claims checker for the doctrine corpus, but no general literal-vs-source verifier for
  the research_notes corpus, which is exactly where compiled wiki-style pages live
  (trader-formation, doctrine-application, this sweep). Adoption shape: a native script
  under ~/workspace/tools/ with a gate-wired regression blocker per the bug-log law, a
  frozen candidate set documented in its docstring, and the suspect-not-verdict rule
  kept. Effort is small; the false-positive discipline (strip fences/code/metadata/
  status blocks; exclude the source files' own metadata headers) is the part worth
  copying as behaviour, specified in our own code.
- C2. Compile-time locate-before-write rule. "Locate every number, date and quote in the
  source before writing it; write it exactly as found (42K, not 42,000); derived values
  show their components; an unlocatable value is dropped or de-precised." Our provenance
  standard (P3) requires sources and dates on claims but does not state this
  value-level rule. Adopting it as a written rule for research synthesis pages (and as
  the compile-time half that C1's lint verifies) is a one-paragraph doctrine addition
  with real fidelity payoff.
- C3. Ingest triage with a No material disposition that is machine-readable. The four-way
  disposition (New / Update / Disputed / No material, No material exclusive) plus the
  rule "keep the source, log it, force no page" plus encoding the No material log
  heading as the exact key a later unreferenced-source sweep parses. We already keep
  dead lessons and parked items as negative context, but our research ingest has no
  named no-material disposition, and our unreferenced-source checks cannot distinguish
  "deliberately not compiled" from "backlog". Adopt for research_notes ingest: a dated
  log line per source with disposition, and the sweep exemption keyed on it.
- C4. Three-tier lint authority as an explicit template for memory/research lint passes:
  Safe Fixes auto-fix only structural facts with a deterministic rule (index vs files,
  Updated sync, dead-link repair on exactly-one filename match, [MISSING] marking
  instead of deletion); Mechanical Reports never auto-fix facts; Judgment Reports never
  fix at all. Our inspections already behave close to this, but the tier table, and
  especially the exactly-one-match / zero-or-multiple-report link rule and the
  mark-don't-delete index rule, are crisper than our current written lint conventions.
  Adopt as wording in the relevant audit/inspection charter, not as new machinery.
- C5. Status block micro-format for research pages: an inline blockquote directly under
  a superseded or disputed claim, `Status: Outdated (date)` or `Status: Disputed`, each
  with source attribution and explanation, malformed-block detection as a lint item
  (Outdated without a date is a defect). Our dated-conflict practice lives at the MEMORY
  and synthesis level; research_notes pages currently have no standard inline form.
  Small, native, useful.
- C6. Cascade-update step for research ingest: after compiling the primary page,
  full-text search the corpus for the source's entities and aliases (not just the index)
  and update every materially affected non-archive page, refreshing a content-change
  Updated date (explicitly not the filesystem timestamp, and not typo fixes). Our
  nightly snapshot rewrite does this for operational state; research pages have no
  equivalent obligation, which is how stale sibling pages survive a new source. Adopt
  as an ingest checklist step for research programs.
- C7. Archived-answer pages as a distinct page class: a saved query synthesis is always
  a new page (never merged into compiled articles), carries an Archived date, cites the
  compiled pages it drew on, has no source/raw field, is exempt from the grounding
  verifier and from cascade updates, and carries an index marker ([Archived] prefix).
  We save research answers ad hoc; a named class with those five properties prevents
  synthesised answers from silently becoming load-bearing compiled knowledge. Low cost,
  real hygiene.

### SKIP

- S1. Adopting the repo as a system (a new raw/ + wiki/ store for facts about the owner or
  the operation). Direct duplication of Tier 0/Tier 2 and a second source of truth,
  expressly barred by the program rails and by MEMORY-SYSTEM.md P1. The mechanism set
  above is adoptable only scoped to research-topic corpora that are not user facts.
- S2. Installing the skill (`npx add-skill Astro-Han/karpathy-llm-wiki`) or copying
  SKILL.md / scripts/ into any production skill directory. Unscanned third-party prompt
  import: its trigger description fires on any mention of "LLM wiki" and on "what do I
  know about", which would shadow our own memory-query behaviour. Reimplement candidates
  natively instead. (Read-only reading of the files, as done here, is the sanctioned
  route.)
- S3. Their file-layout specifics as new conventions for memory: one-level topic
  directories, wiki/index.md and wiki/log.md filenames, the raw filename datestamp
  scheme. Our layout (memory/ daily logs, people/groups pages, midna-book registers and
  dated snapshots) already covers these functions with stricter schemas; renaming to
  match a younger system buys nothing.
- S4. The production-scale claims (94 articles / 99 sources) as evidence for adoption.
  Unverifiable from the repo (the corpus is private); the examples/ folder proves the
  formats render, not that the workflow compounds. Adoption rests on mechanism fit
  (section 4), not on the author's numbers.

## 5. Risks

- R1. Parallel-store risk (main risk). The system's whole shape invites standing up a
  second knowledge base next to MEMORY.md. Mitigated only by scoping any adoption to
  research corpora and keeping MEMORY.md / midna-book registers as the sole store for
  user and operation facts (S1).
- R2. No phone-home, no hooks, no session-start execution found. The only code is
  check_evidence.py: stdlib-only, report-only, no network, no writes (verified by grep
  over the fetched source). The README explicitly refuses automatic hooks and scheduled
  runs. The installer path (npx add-skill) is the one supply-chain surface, and it is
  not needed for native reimplementation (S2).
- R3. Secrets in memory: this repo contains NO instruction to store secrets, keys or
  credentials in notes (searched README, SKILL.md, references/, examples/). Separately
  and for the record of this program: the source-article tip suggesting keeping secrets
  in memory is REJECTED by the owner. Nothing in any candidate above involves credential
  material, and no adoption may add a secrets-in-notes practice. Wiki/raw files are
  plain markdown in a project tree; anything sensitive ingested there would sit
  unencrypted and grep-able, which is a further reason ingest triage must exclude
  credential-bearing sources.
- R4. Checker limits are real and stated by the author: the frozen candidate set misses
  small plain integers, currencies, signs and spelled-out dates; derived values and
  product names surface as false suspects; suspects require judgment. Adopting C1
  without keeping the suspect-not-verdict rule would manufacture false defects. Also,
  the grounding invariant only covers values; a page can pass the checker while its
  prose mischaracterises a source.
- R5. Licence and maintenance: MIT (Yuhan Lei, 2026), so native reimplementation of the
  mechanisms carries no licence friction; mechanisms/ideas are not the code. Maintenance
  is young and single-author-shaped: created 2026-04-05, last push 2026-07-23 (about
  three months before this audit), 11 open issues, no releases in the tree read. Fine
  for idea adoption; another reason not to depend on the upstream artifact itself.
- R6. Trigger breadth if the skill were ever installed: "what do I know about" is a
  general memory question in this house; a foreign skill claiming it could route user
  questions to a research wiki instead of MEMORY.md. Recorded under S2.
- R7. Obsidian fit is by file format only: everything is plain markdown with relative
  links, so any adopted page conventions render in Obsidian unchanged; the repo itself
  ships no Obsidian configuration, graph view setup or plugin assumptions.

## 6. Verdict

RESOLVED and audited. The repo is a small, clean, MIT prompt-contract skill whose value
is four mechanical disciplines Midna does not yet have in written, native form: a
report-only literal grounding verifier (C1) with its compile-time locate-before-write
half (C2), a machine-readable ingest triage including No material (C3), and a three-tier
lint authority table (C4); plus three smaller conventions (C5 Status blocks, C6 cascade
updates for research pages, C7 archived-answer page class). Its architecture, index/log
discipline, conflict carrying and grep-over-vectors stance are ALREADY-HAVE. Its store
must never be adopted for user facts (S1), its code and SKILL.md must not be imported
(S2), and the secrets-in-memory tip circulating in this program's source material is
recorded as REJECTED (R3). No candidate is landed by this audit; landing any of C1–C7 is
a separate, owner-visible step with its own blocker tests under the bug-log law.
