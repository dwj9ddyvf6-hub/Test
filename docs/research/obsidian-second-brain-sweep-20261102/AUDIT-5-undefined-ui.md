# AUDIT 5: undefined-ui/second-brain-os

Program: Obsidian second-brain sweep, 2026-11-02. Auditor: workflow research agent (item 5).
Status: PARTIAL (audit complete on the load-bearing corpus named below; the 77-page guide prose and the site/course tracks were skimmed by tree and README, not read page by page. Open row named in Section 8.)
Method: READ-ONLY. GitHub API, raw file URLs, and web search only. Nothing cloned-and-run, nothing executed, no installer, script, hook, or README step run. All code below was read as text.

## 0. SCOPE (InfinityBlade)

- Surface: one third-party repo, audited for mechanisms that could extend Midna's existing file-based memory (~/MEMORY.md, ~/memory/, ~/workspace/midna-book/ registers). No files outside this audit were changed. MEMORY.md was not edited.
- Constraints: single source of truth preserved (MEMORY.md + midna-book registers); adoption means native reimplementation only, never importing this repo's code into a production lane unscanned; no desk strategy, sizing, stops, thresholds; Tensor engine untouched; no public save; no secrets in any note (see the rejected tip, Section 6.1).
- Outcome: a resolved repo identity, a mechanism inventory classified ALREADY-HAVE / CANDIDATE / SKIP against the local system, and honest risks.
- Proof: URLs and repo paths read are listed in Section 9; classification is grounded in the local files read (Section 5).
- Edges: the repo is a Claude Code / Obsidian-shaped system; Midna is neither. Mechanisms transfer, tooling mostly does not.

## 1. Resolution (resolved: YES)

- Repo: `undefined-ui/second-brain-os`
- URL: https://github.com/undefined-ui/second-brain-os
- How resolved, three routes, all agreeing:
  1. Web search "github undefined-ui Obsidian starter vault skills commands second brain": first result was the repo README, quoting verbatim "18 skills" and "72 slash commands" and the starter vault copy commands.
  2. Web search "site:github.com undefined-ui obsidian": same repo, multiple files (README, resources/, docs/02-setup/mcp-obsidian.md).
  3. GitHub API: `GET /users/undefined-ui/repos` and `GET /search/repositories?q=user:undefined-ui` returned `second-brain-os` (id 1360367824) among the owner's 6 repos; no other owner repo matches the hint.
- Identity check against the hint: starter vault (`vault-template/`), 18 skills (`skills/second-brain-*/SKILL.md`, 18 directories in the tree), 72 commands (`commands/*.md`, counted in tree plus the commands README grouping). Exact match on all three numbers.
- Repo facts (GitHub API, 2026-11-02): created 2026-09-07, pushed 2026-11-02 (active today), 1,173 stars, 196 forks, 5 open issues, default branch `main`, homepage secondbrainos.dev, licence MIT, primary language listed as HTML (the guide/site payload dominates; the vault machinery is markdown plus small Python). Description: "Guides and resources for AI engineers: an agents course, five handbooks, a hands-on second-brain project and a vetted reading list." Note: the second-brain vault is one project inside a larger guide/course repo, not the repo's whole content.

## 2. What the repo actually is

A Karpathy LLM-wiki implementation, packaged as: a 10-section, 77-page guide (`docs/01-concepts` through `docs/10-troubleshooting`) plus unrelated agent course tracks (`docs/course-*`, `docs/track-*`); a starter vault; 18 Agent Skills; 72 thin slash commands; 6 subagent definitions; 4 dependency-free Python scripts; resource lists; and a static site build (`tools/`, `assets/site/`, `index.html`).

Structural fact that matters for adoption: the commands are deliberately thin. Each `commands/*.md` file is roughly 200 bytes: a one-line description, a scoped instruction, and "Follow the `second-brain-X` skill." All behaviour lives in the 18 SKILL.md files. Nine commands do the real work; the other 63 are scoped entry points (per-source-type ingest variants, per-graph-question variants, etc.).

## 3. Mechanism inventory (what is mechanical enough to adopt)

### 3.1 Two-layer vault layout
- `raw/` (immutable source material, never edited after it lands; `raw/assets/` for attachments), `wiki/` (the agent-owned compiled layer), `projects/` (pipeline layer), `output/` (generated material for outside use), `templates/`, plus vault-root `CLAUDE.md` as the operating contract.
- Wiki split by page type: `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/synthesis/`, plus `wiki/index.md` (catalog of every page, with a Gaps section) and `wiki/log.md` (one append-only line per operation: `DATE OPERATION target -> result`).
- Project layer kept separate from the knowledge layer on purpose (docs/01-concepts/two-layers.md): projects consume wiki concepts into `Inputs/`, work in `Process/`, emit `Outputs/`, and finished project work is ingested back into the wiki (`/ingest-mine`). Merging the layers is named as the failure mode.
- Source: `vault-template/CLAUDE.md`, `vault-template/` tree, `docs/02-setup/vault-structure.md` (by tree), two-layers doc (read in full).

### 3.2 Page contracts and frontmatter schema
Fixed frontmatter on every page (docs/04-structuring/frontmatter-schema.md, vault CLAUDE.md, `vault-template/templates/*.md`):
```yaml
title: Canonical name
type: source | entity | concept | synthesis
created: YYYY-MM-DD
updated: YYYY-MM-DD
aliases: []
tags: [two or three, controlled vocabulary]
```
Source pages add `url`, `author`, `published`; entity pages add `kind: person | org | product | tool`.
- Per-type body contracts: source pages keep claims attributed ("this source says X, not X is true"); concept pages carry In one paragraph / Where it came from / What supports it / What argues against it / Open questions / Related; synthesis pages carry The question / What the sources say / Where they disagree / Current position / What would change it, and may exist only when they say something no single source did.
- Schema discipline: leave a field out rather than guess it; keep tags to 2 to 3 from a maintained vocabulary held in CLAUDE.md (new tags proposed, never silently invented); schema changes are rare and, when made, backfilled across the whole vault in one pass.
- Confidence labels for claims: stated (primary source) / reported (secondary) / self-reported (by the party it benefits, label never dropped) / unverified.

### 3.3 Linking rules
- Link the first mention of any concept or entity on every page with `[[wikilinks]]`; linking is bidirectional at ingest time (source page links out, targets link back).
- A page with no outbound links is a dead end; no inbound links is invisible; both are lint findings.
- Missing target: still write the link, then create the page in the same run or record it under Gaps in `index.md`. Prefer a link over a restatement.
- Typed links (docs/05-graphs/typed-links.md): a deliberately small 5-relation vocabulary (supports, contradicts, extends, part-of, applies), encoded inline as Dataview fields (`supports:: [[Page]]`) for claim-level relations or in frontmatter for page-level relations. This is what makes "everything that argues against this page" a query instead of a read.

### 3.4 Ingest flow (skill: second-brain-ingest)
1. Read the source completely before writing anything. 2. Search the wiki for existing entities/concepts first (in a mature vault most work is updating, not creating). 3. Write the source page with claims attributed. 4. Extract concepts/entities, one page per idea, calibration: a source usually yields 1 to 3 concepts worth their own page; a concept that cannot be explained without this one source stays inside the source page. 5. Link both directions; create missing targets or log them as Gaps. 6. Update index.md and append to log.md in the same run. 7. Report in a fixed shape: Ingested / New pages n (list) / Updated pages n (list) / Links added n / Contradictions found / Gaps created.
- Scoped variants: ingest-url, ingest-youtube, ingest-pdf, ingest-paper, ingest-chats, ingest-voice, ingest-newsletter, ingest-highlights; `/ingest` with no argument processes everything in `raw/` without a source page, oldest first, and stops and reports if more than 20 are pending. Backfill skill does bulk archives in batches. Chat-import skill converts exports to per-conversation markdown (with the privacy warning in Section 6).

### 3.5 Query flow (skill: second-brain-query)
- Core rule: every claim in the answer comes from a vault page and names it; model knowledge not in the vault is labelled outside knowledge or omitted. A silent fallback to priors is named the most damaging failure.
- Workflow: start from `index.md` (not a full-text sweep), follow links outward one hop at a time, stop when pages stop adding. Output ends with a fixed footer: `Read: <pages consulted>` and `Not covered: <what the vault does not answer>`. If the vault has nothing, say so in one sentence and stop.
- Retrieval command family built on this: ask, know, connect (path between two ideas), compare, sources (what a claim rests on), gaps, contradicts (argue against me), timeline, trace (which pages an answer used), changed-my-mind.

### 3.6 Contradictions, supersession, changed-my-mind
- Never overwrite on disagreement: record both positions on the page, each attributed and dated, with what would settle it. If new evidence is clearly better, mark the old claim superseded (struck through, dated, source cited) and keep it. Never resolve by recency. (docs/04-structuring/contradictions-and-supersession.md)
- Changed-my-mind skill: reconstructs Was / Now / What moved it / Firmness (what would move it again) from superseded claims and dated contradictions; distinguishes genuine revision from error correction; flags still-unresolved contradictions as the most actionable output; an empty period is reported in one line, never padded.

### 3.7 Lint and health (skills: second-brain-lint; scripts as text)
- Lint workflow: inventory by type; build the link graph from `[[wikilinks]]`; broken links split into typos/renames (fix) vs genuine gaps (to index Gaps); orphans (link them or flag as deletion candidates); stubs (under roughly 40 words, no links; flag for re-ingest from raw/); schema violations; near-duplicates (propose merges, never perform unsolicited); index drift. Core rule: report before repairing; mechanical fixes are automatic, semantic decisions (delete, merge) need the owner's yes. Cadence: weekly, or after an import over about 20 sources, not after every ingest. Fixed output shape ending in orphan rate, broken-link rate, stub rate.
- Scripts (read as text, not run): `scripts/vault_stats.py`, `scripts/link_check.py`, `scripts/graph_export.py` (CSV edges or GraphML), `scripts/chat_export_to_md.py`. All four import only Python stdlib (os, re, sys, json, csv, argparse, collections, xml.sax). No network, no subprocess, no eval/exec found on a source scan. They skip `.claude/`, `.obsidian/`, `templates/`, `scripts/`, `raw/`, CLAUDE.md and README.md so counts describe the wiki, not the tooling.
- Metrics skill: exactly four numbers appended to a dated log and compared to the previous entry (orphan rate, average degree, component count, stale-concept rate, stale = untouched 90+ days); page count and word count are explicitly banned as health signals; interpret only what changed; recommend at most one fix.

### 3.8 Graph analysis (skill: second-brain-graph, read-only)
Orphan rate (healthy under 5 percent), average degree, components and main-component share, hubs (pages that swallowed the graph, split candidates), bridges (pages holding clusters together; what breaks if they are wrong), clusters (what the vault is actually about vs what the owner thinks). Commands: graph, graph-export, orphans, hubs, bridges, clusters, typed-links, stale.

### 3.9 Review cadence and scheduled maintenance
- Review skill: diff the period from log.md and frontmatter dates; find clusters that gained links (where attention actually went); surface unresolved contradictions and open questions; find thin-but-often-linked pages; recommend exactly three next reads/writes, each tied to a page; keep it under a page; a quiet week is reported in one line.
- Schedule (docs/06-agents/scheduled-maintenance.md): ingest daily, link weekly, lint weekly after the linker, review weekly, metrics monthly. Every run must produce three things: a log entry, a git commit naming the run, and a visible report (counts, not just completion, so "ingested 0 sources" is visible). Silent-failure detection: report counts plus a monthly look at commit frequency. Start manual: run each job by hand for a week before scheduling it; schedule ingest last because it writes most.

### 3.10 Subagent role split (agents/)
Six Claude Code agent definitions. Four are read-only by design (reviewer, researcher, graph-analyst, curator: tools Read/Glob/Grep class), two write (ingestor, linker, links only) and those two carry the narrowest instructions. Rationale stated in agents/README.md: a bad analysis run cannot damage the vault, and git history stays readable because every content change traces to an ingest or a link pass.

### 3.11 Hooks (docs only, docs/06-agents/hooks.md)
No hook code or settings file ships in the repo tree (verified in the full recursive tree: no `.claude/settings*`, no hook scripts). The guide recommends hooks for: frontmatter validation before a write (blocking), lint after a run, commit after a scheduled run, notify on any deletion. Rules: fast (well under a second), silent on success, mechanical only (no judgement in a hook), blocking behaviour decided explicitly per hook, and a warning that a blocking hook failing for an unrelated reason can silently stop scheduled ingest for a week.

### 3.12 Guardrails (docs/06-agents/safety-and-guardrails.md)
"Keys, not prompts": control what is possible at the permission level; a CLAUDE.md instruction is a preference on top of a boundary. Scope write access to the vault, not the home directory; connectors read-only wherever possible. No deletion without a log.md line naming it and why (merges count as deletions). Git is the real safety net: commit before any run that writes at scale; scheduled runs commit their own work; read the diffs of scheduled runs occasionally. Dry runs for anything touching many files (`/dry-run`: list every page that would be created, updated, deleted, plus links; write nothing). Scope-creep instruction: do the job asked, list anything else noticed, change nothing else. `/rollback` and `/audit` commands exist as scoped entry points on the same ideas.

### 3.13 Projects, outputs, self-testing
- Project skill/commands: project scaffolding with its own CLAUDE.md (example project in the template has Feedback/Inputs/Outputs/Process folders), project-status, decisions, commitments, handoff, scope (pull knowledge into a project).
- Write/report/publish skills: draft and outline from concept pages; research reports; publish skill is a pre-publish safety check, not a publisher.
- Quiz skill and `/explain`: test the owner from their own pages and surface gaps; teaching-yourself is a guide section (docs/08-outputs).

### 3.14 Setup and portability surface
Install is copy commands: clone, `cp -r vault-template ~/brain`, `cp -r skills` and `commands` into the vault's `.claude/`, copy `scripts/` into the vault so /metrics, /health and /graph-export can find them; open the folder in Obsidian. Optional MCP route (docs/02-setup/mcp-obsidian.md): Obsidian Local REST API plugin plus `mcp-obsidian`, or the plugin's built-in MCP server (risk notes in Section 6). Also a `.claude-plugin/marketplace.json` at repo root and a plugin bundle under `plugins/agents-course/` (that bundle belongs to the agents course, not the vault).

## 4. Classification against Midna's existing system

Local baseline read for this comparison: `workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md` (the memory design spec: Tier 0 platform memory, Tier 1 CONTEXT-SNAPSHOT, Tier 2 registers STATE/RULINGS/OPEN-THREADS, Tier 3 evidence, lessons ledger, strategy records, recovery drill), the structure of ~/MEMORY.md (curated facts, laws, people/group pointers), and the ~/workspace/midna-book/ file list including `midna-book/memory/` (STATE.md, RULINGS.md, OPEN-THREADS.md, LESSONS.md, STRATEGIES.md, snapshots/, strategies/, CONFIRMATION-TALLY.md), plus standing workspace law in AGENTS.md (memory write boundary, memory_store_check, memory_reconcile, dated-conflict practice, blocker gates).

### ALREADY-HAVE (do not adopt; local version is equal or stronger)
1. Curated top layer over append-only evidence. Their wiki-over-raw is the same shape as MEMORY.md over ~/memory/ daily logs, and MEMORY-SYSTEM P2. Local version adds claim ids, quotes, and source message ids (provenance-grade), which their log.md one-liners lack.
2. Entity pages. ~/memory/people/ and ~/memory/groups/ with INDEX.md ordered by closeness are their wiki/entities/, already maintained hourly.
3. Index kept current in the same run. People/groups INDEX.md plus midna-book registers already do this; a lagging index is already treated as drift locally.
4. Contradictions carried, never silently overwritten; supersession with history kept. Local dated-conflict practice (MEMORY-SYSTEM Section 8.2, alignment synthesis carrying both readings) is the same rule, with a stricter resolution protocol (owner asked, neither reading silently dropped).
5. Periodic review cadence. Daily audit (about 21:46 ET), weekly review, monthly constitution/recovery review already exist and are job-owned; their ingest/link/lint/review/metrics cadence maps onto these one for one.
6. Lint/health as a scheduled gate. Local memory_store_check.py and memory_reconcile.py plus the twice-daily desk inspections and gate-wired regression blockers exceed their weekly lint; their "mechanical fixes automatic, semantic decisions proposed" split is already local law for memory workers (narrowest scope or read-only).
7. Scheduled runs must leave a log entry, a commit-equivalent, and a visible counts-bearing report; silent failure is the named enemy. Already standing local practice (seal receipts, inspection reports, "silent is an open defect").
8. Read-only vs narrow-writer agent split. Already law locally: unattended memory workers run in the narrowest scope or read-only (AGENTS.md round-5 item 30); four of their six agents add nothing.
9. Dry-run, rollback, no-delete-without-a-record, git as safety net. Covered and stronger locally: recoverable trash, backup seals with proven restores, gated approvals bound to content hash, effect queue receipts.
10. Project layer separate from knowledge layer. Local goals workspaces (files/ vs hidden_files/) plus research_notes/ program homes are this split, with a lifecycle owner per program.
11. Decisions/commitments extraction. Covered by the tracking system, RULINGS.md, and OPEN-THREADS.md; their /decisions and /commitments are views Midna already keeps as registers.
12. Privacy audit and secrets scan as a named pass. Covered by the pre-save PII gate, the privacy sweep practice, and Secure Vault discipline; their /secrets report format (file and type, never the value) matches local rule exactly.
13. Query with citations and named gaps. muse.memory_search / memory_explain already return sourced snippets and provenance; the "say what is not covered" half is standing reporting law (PARTIAL with open rows named).

### CANDIDATE (genuinely new or a real sharpening; adopt natively, in this order)
1. **An immutable `raw/` ingest inbox for research material, with a bounded queue rule.** Midna's research intake (research_notes/, desk lanes) has no single never-edited raw layer with an oldest-first queue, a hard pending cap (theirs: stop and report over 20), and a fixed ingest report shape (new/updated/links/contradictions/gaps). Adopt as a convention inside the existing research workflow only; distilled output still lands in MEMORY.md / registers, never in a new vault. This is the repo's strongest transferable mechanism.
2. **Typed-link vocabulary for the registers and research notes.** Five relations (supports, contradicts, extends, part-of, applies) as inline fields or frontmatter on research and strategy pages. Local links are untyped; this makes "everything that contradicts this claim" and "what this lesson rests on" mechanical queries across LESSONS.md, STRATEGIES.md, and research notes. Small, cheap, compounding.
3. **A Gaps section as a first-class index element.** Their index.md carries "pages that are linked but do not exist yet." Local indexes list what exists; nothing lists referenced-but-missing pages/topics as a maintained queue. Adopt as a section in the relevant local index/register (for example OPEN-THREADS or a research index), fed at ingest time.
4. **Link-graph health as a dated, append-only metrics series with banned vanity numbers.** Four numbers only (orphan rate, average degree, component count, stale-page rate at 90+ days), appended, compared to the previous entry, at most one recommended fix, page/word counts explicitly not health. Local lint checks existence and schema; it does not trend the link graph of ~/memory/ plus midna-book/memory/ over time. Reimplement the counting natively (their scripts are stdlib-clean as a spec, Section 3.7; do not import them unscanned).
5. **Query ritual footer and index-first traversal as a written protocol.** Start from the index, follow links one hop, end with `Read:` and `Not covered:` lines. Memory search exists, but no standing protocol forces the not-covered line on vault-derived answers outside formal reports. Cheap to adopt as a response convention for research answers.
6. **Changed-my-mind trace as a fixed output format.** Was / Now / What moved it / Firmness, distinguishing revision from correction, with unresolved contradictions listed as the actionable tail. Local supersession records the facts; this format is a better periodic surface for rulings and strategy verdicts at the weekly/monthly review. Adopt as a review section template, fed from RULINGS.md and the dated-conflict list.
7. **Concept-page body contract for research synthesis pages.** Question / What the sources say / Where they disagree / Current position / What would change it, plus the rule that a synthesis page exists only when it says something no single source did, and the 4-level confidence labels (stated / reported / self-reported / unverified, with self-reported never losing its label). Local research notes are free-form; this contract would make vendor and strategy research pages comparable. Adopt for research_notes synthesis pages only, not for MEMORY.md.
8. **Quiz/explain-back self-test from own pages.** No local equivalent: generating recall questions from the owner's own recorded positions to expose gaps. Low value for the desk, real value for the owner's professional training material if ever wanted. Record as a candidate, lowest priority, no action implied.

### SKIP (with reason)
1. **The vault itself, and Obsidian.** Adopting vault-template/ as a store would create a parallel source of truth next to MEMORY.md and the midna-book registers, which program rails forbid. Obsidian, its graph view, Dataview, Templater, and the 7,400-plugin catalog are a human browsing layer Midna does not need; her read access requirement is already met by the file tools.
2. **Claude Code packaging.** Skills/commands/agents install by copying into `.claude/`; Midna's skill system has its own format, size gates, and trigger evals. Reimplement mechanisms as native skills if adopted; do not copy these files in.
3. **The MCP-for-Obsidian route.** A local HTTP API with a bearer key granting full read/write to the notes, served only while the app runs, to solve a problem Midna does not have (she reads the files directly). See risk 6.2.
4. **Scheduled Claude Desktop / headless-Claude tasks as specified.** Midna already has cron with goal ownership, receipts, and inspections; their schedule is a cadence idea (already-have), not a mechanism to import.
5. **Graph export to Gephi/GraphML and the static site build.** Presentation tooling for a human PKM hobbyist; no local consumer. The graph metrics (candidate 4) are the valuable part, not the export.
6. **Bulk chat-export import as a default intake.** Their own docs warn chat history is where the privacy problem bites hardest and redaction after ingest does not work. Midna's platform memory already captures conversation through its own governed pipeline; a second bulk import path adds exposure and duplication for no gain.
7. **The agents course and handbook tracks** (docs/course-*, docs/track-*, resources/ reading lists). General agent-engineering education, not memory mechanisms; out of scope for this program.
8. **/publish and the publishing workflow.** No public save leaves this program, and local publishing already runs through the gated path with PII scanning. Their pre-publish check adds nothing over the local gate.

## 5. What already exists here (evidence pointers)
- ~/MEMORY.md: curated long-term memory, laws first, people/group pointers, dated program records. Canonical for facts about the owner.
- ~/memory/ daily logs, people/, groups/: append-only evidence and entity pages with INDEX.md files.
- ~/workspace/midna-book/: CHARTER.md, JOURNAL.md, ledger.json, CONTEXT-SNAPSHOT.md, IDEAS.md, and memory/ registers (STATE, RULINGS, OPEN-THREADS, LESSONS, STRATEGIES, CONFIRMATION-TALLY, snapshots/, strategies/).
- workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md: the design spec those registers implement (tiers, schemas, recovery drill, dated conflicts, lessons lifecycle CANDIDATE to TESTED to RULE or DEAD).
- ~/workspace/research_notes/obsidian-second-brain-sweep-20261102/: this program's home (AUDIT-1 and AUDIT-4 already present at audit time).

## 6. Risks, honestly

### 6.1 Secrets in memory: REJECTED, recorded
The program brief states that one source article item in this sweep suggests keeping secrets in memory, and that the owner expressly rejects that tip. Recorded here as required: **the tip is REJECTED. No secret, key, token, or credential is ever written into MEMORY.md, any daily log, any register, or any vault-style note.** Credentials live only in the Secure Vault / approved connector storage.
For the record, this repo itself is on the safe side of that line, which is worth stating plainly so the rejection is not misattributed: its privacy doc (docs/09-maintenance/privacy-and-secrets.md) lists "Credentials of any kind" under what does not belong, its guardrails doc repeats it, and its /secrets command scans for credentials and reports file and type, never the value. The risk in this repo is not that it stores secrets; it is that its chat-import and bulk-ingest paths can carry secrets in transit (see 6.4), which is exactly why the decide-at-capture rule matters.

### 6.2 MCP / Local REST API exposure (if the setup guide were followed literally)
docs/02-setup/mcp-obsidian.md instructs enabling a community plugin that opens a local HTTP server whose key grants full read and write access to every note. The doc does warn to keep it on 127.0.0.1 and treat the key like a password, but the mechanism still widens the blast radius from "agent with scoped file access" to "any local process that learns one bearer string." Not adopted (SKIP 3).

### 6.3 Hooks and scheduled unattended writes (pattern risk, not shipped code)
No executable hook ships in the repo, but the guide's recommended operating mode is hooks on writes plus daily scheduled runs that ingest, link, and commit unattended. Their own docs name the failure modes: a blocking hook failing for an unrelated reason can silently stop ingest for a week; a scheduled run that completes while doing nothing useful looks identical to success unless counts are reported. Any local adoption of candidates 1 or 4 must inherit the local, stronger versions of these controls (receipts, counts, inspections), not the guide's lighter ones.

### 6.4 Ingest propagation risk
The repo is explicit and correct that redaction after ingest does not work: material propagates into concept pages, links, and synthesis pages. Chat exports are called out as the highest-risk source. This cuts both ways for adoption: candidate 1 (raw inbox) must adopt their decide-at-capture rule with it, or the inbox becomes a way to launder unreviewed material into the distilled layer.

### 6.5 Duplication of the single source of truth (the main adoption risk)
The system's whole premise is "the agent maintains your knowledge in a vault." Run as designed next to Midna's stack, it would hold a second set of facts about the owner, a second rulings history (its log.md and supersession records), and a second review cadence, and the two would diverge silently. Every candidate in Section 4 is therefore scoped to extend an existing local file or register; none creates a vault, a second index of the owner, or a second log.

### 6.6 Plugin supply chain
The resources docs recommend many third-party Obsidian plugins; the repo itself notes every plugin is code with write access to the notes running alongside an agent that also writes to them. Not adopted, but named because a reader following the guide casually meets the plugin catalog early.

### 6.7 Phone-home / telemetry check on the shipped scripts
Clean on read: the four scripts import stdlib only, open only vault-local files, and contain no network, subprocess, or dynamic-execution calls (source scan, Section 3.7). The site JavaScript under assets/site/ was not audited line by line; it is a static guide site with no local consumer, and it is in the SKIP set. No claim is made about it beyond that.

### 6.8 Licence and maintenance
MIT licence, no copyleft obstacle to native reimplementation of ideas (mechanisms here are conventions and prompts, in any case). Maintenance risk is real: the repo is about eight weeks old at audit time, appears to be a single-author project (owner undefined-ui, with Claude credited as co-author in third-party coverage), and is moving fast (pushed the day of this audit). Anything adopted must therefore be adopted as a local convention owned locally, never as a dependency on upstream files that may be restructured next month. Star count (1,173) is social proof, not a stability signal.

### 6.9 Claude Code lock-in shape
Commands, agents, hooks advice, and scheduling instructions are all written for Claude Code / Claude Desktop. The SKILL.md files use the portable Agent Skills format, which is why the mechanisms read cleanly; the surrounding operating instructions do not transfer and should not be treated as neutral.

## 7. Verdict

PARTIAL adoption value, concentrated in a few conventions. The repo's architecture (curated wiki over immutable raw, entity/concept/source/synthesis typing, contradiction preservation, cadenced review) is the same architecture Midna already runs, in several places in a stronger form (provenance-grade daily logs, gated memory writes, recovery drills, blocker-wired lint). What is genuinely worth taking is small and specific: the bounded raw ingest queue with its fixed report shape, typed links, a maintained Gaps list, a four-number link-graph health series with vanity metrics banned, the query footer protocol, the changed-my-mind output format, and the synthesis page contract. Everything else is already-have, or is Obsidian/Claude Code packaging that would duplicate or weaken the local system.

## 8. Open rows
- The 77-page guide prose beyond the load-bearing docs listed in Section 9, the six remaining SKILL.md files not read in full (backfill, chat-import, project read; publish, rename, report, transcript, write skimmed via the skills index and command stubs), and assets/site JavaScript were not read line by line. The mechanism inventory rests on the vault CLAUDE.md, the structuring/agents/maintenance docs, 12 of 18 skills, the command layer, the agents index, and all four scripts, which is where the repo itself says the behaviour lives. Status stays PARTIAL on that named row, not GREEN.

## 9. Provenance (URLs and paths read)
Resolved via:
- https://github.com/undefined-ui/second-brain-os (repo page / API: GET /repos/undefined-ui/second-brain-os, GET /users/undefined-ui/repos, GET /search/repositories?q=user:undefined-ui)
- Full recursive tree via GET /repos/undefined-ui/second-brain-os/git/trees/main?recursive=1 (406 entries, not truncated)

Read in full via raw.githubusercontent.com/undefined-ui/second-brain-os/main/ :
- README.md, LICENSE
- vault-template/CLAUDE.md, vault-template/README.md, vault-template/wiki/index.md, vault-template/wiki/log.md, vault-template/templates/concept.md, vault-template/templates/entity.md, vault-template/templates/source.md, vault-template/templates/synthesis.md
- skills/README.md; SKILL.md for second-brain-ingest, second-brain-lint, second-brain-query, second-brain-privacy, second-brain-project, second-brain-review, second-brain-write, second-brain-merge, second-brain-changed-my-mind, second-brain-metrics, second-brain-graph, second-brain-quiz
- commands/README.md, commands/secrets.md, commands/privacy.md, commands/lint.md, commands/health.md, commands/ingest.md, commands/ask.md
- agents/README.md, agents/reviewer.md
- scripts/README.md, scripts/vault_stats.py, scripts/link_check.py, scripts/graph_export.py, scripts/chat_export_to_md.py (source read as text only)
- docs/01-concepts/two-layers.md, docs/01-concepts/llm-wiki-pattern.md, docs/04-structuring/frontmatter-schema.md, docs/04-structuring/linking-rules.md, docs/04-structuring/index-and-log.md, docs/04-structuring/page-types.md, docs/04-structuring/contradictions-and-supersession.md, docs/05-graphs/typed-links.md, docs/06-agents/hooks.md, docs/06-agents/safety-and-guardrails.md, docs/06-agents/scheduled-maintenance.md, docs/09-maintenance/privacy-and-secrets.md, docs/09-maintenance/lint-and-health.md

Local files read for comparison:
- workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md
- ~/MEMORY.md (structure and head sections)
- ~/workspace/midna-book/ file list and midna-book/memory/ register heads
- ~/workspace/AGENTS.md, ~/AGENTS.md (standing memory law)
