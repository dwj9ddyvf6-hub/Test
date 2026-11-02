# AUDIT 6: charlie947/ai-second-brain

Program: Obsidian second-brain sweep, 2026-11-02. Auditor: workflow agent (audit 6).
Status: PARTIAL by construction. The repo is fully read and classified below; no adoption is proven because this program authorizes audit only, no implementation. The article's advice to run Step 1 of the README against one's own exports was NOT executed: that execution is not authorized in this program, and no ChatGPT or Claude export was requested, downloaded, or processed.

## SCOPE (InfinityBlade)

- Surface: read-only audit of one third-party repo against Midna's existing file-based memory (~/MEMORY.md, ~/memory/ daily logs and people/group pages, ~/workspace/midna-book/ registers). Output is this file only.
- Constraints: no code from the repo was cloned-and-run, installed, or executed; the skill was not installed into any Claude Code or Muse skill directory; all reads were GitHub API, raw file URLs, and web pages. MEMORY.md untouched. No parallel store of facts about the user proposed. No desk strategy, sizing, or Tensor surface touched. No public save. No secrets written anywhere.
- Outcome: the exact repo resolved, its method extracted from source, each mechanism classified ALREADY-HAVE, CANDIDATE, or SKIP against what already exists here, risks named.
- Proof: provenance list at the end names every URL and file read. Classifications cite the local file or system that already implements the equivalent.
- Edges: this repo is a guided onboarding skill for non-technical Mac users of Claude Code and Obsidian. Midna runs on a headless Linux VM, the user's laptop is Windows, and there is no Obsidian install in the loop. That mismatch, plus the single-source-of-truth rule, decides most of the audit.

## 1. Resolution

Resolved: **charlie947/ai-second-brain**, https://github.com/charlie947/ai-second-brain

How resolved, three routes agreeing:

1. Web search ("charlie947 ai github ChatGPT Claude exports Obsidian linked notes") returned the repo directly as the top GitHub result, plus its SKILL.md at a pinned commit, with the description "Build a living, searchable AI second brain from your ChatGPT, Claude, and research history - Karpathy-style. A Claude Code skill."
2. GitHub API `GET /repos/charlie947/ai-second-brain` confirmed it: public, not a fork, created 2026-04-17, MIT license, default branch main, 216 stars and 43 forks at audit time, topics ai, claude-code, karpathy-wiki, knowledge-management, obsidian, pkm, second-brain. Recursive tree at HEAD (6b14a528) is not truncated and contains exactly 10 files.
3. The source article corroborates: Charlie Hills's Substack post "How I built a 2nd brain with AI" (charliehills.substack.com) links https://github.com/charlie947/ai-second-brain as the skill that "walks you through every step inside Claude Code," and its Step 1 prompt text matches the repo's SKILL.md Step 1c verbatim in substance.

The hint "github.com/charlie947/ai-..." therefore resolves uniquely. No other charlie947 repo matches the described function (his other repos are motion-graphics-skills, social-media-skills, and life-automation-skills, none of which touch exports or Obsidian memory).

## 2. What the repo actually is

A single prose skill, not software. Full tree:

- `README.md` (6,373 bytes): pitch, install by `git clone` into `~/.claude/skills/ai-second-brain`, three-step description, trigger phrases, FAQ, credits.
- `SKILL.md` (13,988 bytes): the entire mechanism, a conversational walkthrough script for Claude Code (frontmatter name `ai-second-brain` plus a long trigger description).
- `CHANGELOG.md` (598 bytes): one entry, 1.0.0 on 2026-04-17, initial release only.
- `LICENSE`: MIT.
- `ai-second-brain.skill` (5,820 bytes): a packaged duplicate of the skill, not opened or installed in this audit.
- `render-social-preview.js` (936 bytes) plus `social-preview.html` / `.png`: dev-only tooling that renders the repo's social preview image with Puppeteer. Read as text; irrelevant to the memory method, not executed.
- `.gitignore`, `.gitattributes`: boilerplate.

There is no ingest script, no converter, no template file, no hook, and no test anywhere in the repo. Every transformation the method describes is performed by the host LLM at runtime, driven by prompt text in SKILL.md. That matters for adoption: there is nothing to import, only procedures to reimplement natively, which is exactly what this program's rails require anyway.

What it is not: it contains no query engine, no memory curation or supersession rule, no staleness handling, and no provenance discipline. Contradiction handling is one suggested prompt ("check the wiki for contradictions, orphan pages, and missing concept pages") with no schema, no evidence standard, and no gate.

## 3. Mechanisms extracted (from source)

### 3.1 Step 1: AI Brain (the step the article scopes this item to)

- 1a. User-only data exports, sequenced by latency: ChatGPT first (Settings, Data Controls, Export data; emailed link, hours to 3 days), then Claude (Settings, Privacy, Export Data; about 5 minutes). The skill pauses for user confirmation at each handoff.
- 1b. Vault setup: `mkdir -p ~/Desktop/Brain` (single-word folder name mandated; spaces are called out as a known failure), user drags both unzipped export folders in, agent verifies with `ls`, user opens the folder in Obsidian via "Open folder as vault."
- 1c. The organise prompt, pasted into a fresh Claude Code session rooted at the vault folder: convert all ChatGPT and Claude conversations into individual markdown files with frontmatter (title, date, tags, category); then launch 10 sub-agents in parallel to smart-tag names, people, places, recurring themes, projects, and topics; link everything together with wikilinks so the Obsidian graph connects related conversations.
- Result claimed: one markdown file per conversation, entity and theme tags, wikilink graph, browsable via Obsidian Graph View (Cmd+G).

Mechanical content worth noting: per-conversation file splitting, a four-field frontmatter minimum, parallel fan-out tagging over a fixed entity taxonomy (people, places, themes, projects, topics), and wikilinks as the only link type. There is no deduplication rule, no chunking rule for very long conversations, no handling of attachments or shared links inside exports, and no verification step after the sub-agents finish.

### 3.2 Step 2: Karpathy Wiki

- Folder pair inside the same vault: `raw/` (immutable user-dropped sources: PDFs, articles, transcripts, notes) and `wiki/` (LLM-compiled articles).
- The operating instructions are not in this repo: Step 2a downloads Karpathy's gist instruction file with `curl -L https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw -o ~/Desktop/Brain/CLAUDE.md`, with a WebFetch-and-Write fallback. The vault's agent behavior is therefore defined by an externally fetched, mutable gist.
- Ingest flow (Step 2c prompt): for each source in `raw/`, write a summary page in `wiki/`, create or update relevant topic and concept pages, add wikilinks between related pages, and maintain an index file listing every wiki page with a one-line description.
- Source intake also offers a NotebookLM path (pull a notebook's sources into `raw/`), which depends on the Step 3 connector setup.
- Maintenance ritual (Step 2d, the only lint flow in the repo): periodic, user-prompted health checks for contradictions, orphan pages, and missing concept pages, plus conversational page surgery ("split this page", "merge these two").

### 3.3 Step 3: Living Wiki

- 3a. MCP connectors: Gmail (forwarded articles and threads), Granola (meeting transcripts, decisions, action items), NotebookLM (existing notebooks). NotebookLM requires a separate one-time `notebooklm login` in a Terminal window outside Claude Code.
- 3b. iMessage Channels: `claude --channels plugin:imessage@claude-plugins-official` runs a Mac-side listener over the user's own iMessages. Requires Full Disk Access for Terminal and Automation permission for Messages. The user texts their own number; the running Claude Code session processes the message against the wiki and replies in-thread. Stops when Claude Code closes or the Mac sleeps; `claude --resume` restarts it.
- 3c. Three scaffolded slash commands, each generated from a prompt and saved as a command file:
  - `/today`: reads today's Google Calendar and urgent Gmail, cross-references the wiki for context on the people and projects involved, returns a prioritised day plan.
  - `/ideas`: reads recent Granola transcripts, Gmail threads, and wiki pages, finds patterns and emerging topics, generates content ideas and missed opportunities.
  - `/create`: takes a topic, pulls wiki context, drafts a finished content piece (post, newsletter, script, infographic outline) in the user's voice.
  Commands also work remotely by texting them through iMessage Channels.

### 3.4 The onboarding pattern itself

- Step 0 pre-flight: confirm Claude Code, Obsidian, and export status before touching anything; kick off the slowest dependency (ChatGPT export) first.
- Explicit agent-can vs user-only division at every step, with pauses, plain-English explanations before commands, and honoring "skip step 1" partial entry.
- A troubleshooting list naming its own observed failure modes: spaces in folder names, running `claude` from the wrong working directory, NotebookLM login attempted inside Claude Code, Channels dying on sleep, Full Disk Access needing a Terminal restart, gist download failure.

## 4. Comparison against what already exists here

Local baseline read for this audit: `workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md` (the design spec for Midna's memory), the structure of `~/MEMORY.md`, and the `~/workspace/midna-book/` file list including `memory/` (STATE.md, RULINGS.md, OPEN-THREADS.md, LESSONS.md, STRATEGIES.md, CONFIRMATION-TALLY.md, snapshots/, strategies/).

Midna's existing stack already covers most of this repo's territory, at higher rigor:

- Platform memory: `~/MEMORY.md` (curated long-term record), `~/memory/YYYY-MM-DD.md` append-only daily logs with claim, quote, and source provenance, `~/memory/people/` and `~/memory/groups/` pages with INDEX.md files, and the nightly alignment synthesis. Conversations with Midna are captured continuously by the runtime; there is no export-and-convert gap for the primary agent history.
- Operational memory: the midna-book snapshot stack (CONTEXT-SNAPSHOT.md Tier 1; STATE, RULINGS, OPEN-THREADS registers Tier 2; journal and ledger Tier 3), with freshness stamping, a recovery checklist, monthly recovery drills, lessons graduation (CANDIDATE to TESTED to RULE or DEAD), and per-strategy records. This exceeds the repo's wiki discipline on every axis the repo addresses: provenance, staleness, contradiction handling (dated conflicts carried, never silently resolved), and proof.
- Connectors and daily rituals: Gmail and Google Calendar are already connected; the personal quant schedule and the daily audit job already produce pre-open, midday, pre-close, and close-review passes richer than `/today`; IDEAS.md is already fed by the daily audit, which is the `/ideas` mechanism with a scrutiny bar attached.
- Phone access: the user already reaches Midna from his phone through the app and a paired device, with a draft-and-tap rule for outbound patient texts. iMessage Channels would be a second, weaker channel with broader OS permissions.

### Classification

| Mechanism | Verdict | Reason |
|---|---|---|
| Step 1 export-to-markdown conversion with frontmatter (title, date, tags, category) | CANDIDATE (scoped) | Genuinely new only as an ingest path for histories Midna does not already capture: the user's ChatGPT (Sol) and standalone Claude conversations. Native reimplementation would convert an export, if the user ever provides one, into the existing daily-log and people-page pipeline, never into a new vault. Audit only here; no export was requested or processed. |
| 10-sub-agent parallel entity tagging (people, places, themes, projects, topics) | ALREADY-HAVE | The relationships pass already maintains people and group pages from conversation, ordered by closeness, and the daily logs already extract claims with sources. The repo's version is the same idea with no provenance and no verification. |
| Wikilinks and graph view as the linking model | SKIP | Midna's memory is consumed by the agent through search and structured registers, not browsed in Obsidian; there is no Obsidian install and no graph surface. Markdown links and INDEX.md files already serve navigation. Adopting wikilink syntax would add a second link convention to files whose consumers do not parse it. |
| `raw/` immutable sources plus `wiki/` compiled pages split | CANDIDATE (partial) | The principle is already the local shape (append-only logs and evidence at the bottom, curated layers above, per MEMORY-SYSTEM.md P2), but an explicit raw-versus-compiled split with create-or-update topic pages is not uniformly applied inside `workspace/research_notes/`, where sources and syntheses intermingle. A native adoption would name that split in research-note conventions only. It must never be applied to MEMORY.md or the midna-book registers, which already have their own layering. |
| Index file listing every page with a one-line description | ALREADY-HAVE | `~/memory/people/INDEX.md`, `~/memory/groups/INDEX.md`, and midna-book `memory/STRATEGIES.md` are exactly this. |
| Periodic health check for contradictions, orphans, missing concept pages | CANDIDATE | Local equivalents exist in pieces (memory reconcile, snapshot health checks, twice-daily desk inspections), but there is no single named lint pass over the people/group pages and registers that reports contradictions, orphan pages (no inbound reference), and missing concept pages as one list. Small, mechanical, and reimplementable natively as a read-only report feeding the existing audit; it must report, not auto-rewrite. |
| Karpathy `CLAUDE.md` downloaded by curl from a gist | SKIP | Fetching a mutable third-party instruction file into the root an agent reads as standing orders is a supply-chain and prompt-injection exposure, and the content is unpinned (no hash, no version). Any wiki instruction file here is written locally under local law, never fetched live. See Risks. |
| MCP connectors for Gmail, Granola, NotebookLM | SKIP | Gmail is already connected through the local connector with its own approval rules. Granola and NotebookLM are not in the user's stack, and installing a third-party NotebookLM skill plus a browser login flow adds an unaudited dependency for a source the user does not use. |
| iMessage Channels with Full Disk Access and Automation permission | SKIP | Grants an always-on local session read access to all iMessages and control of Messages, dies on sleep, and duplicates phone access the user already has. The permission breadth is disproportionate to the benefit, and a self-text loop is a fragile trigger surface. |
| `/today` slash command | ALREADY-HAVE | The standing schedule (pre-open read, midday read, pre-close pass, close review, desk health) plus connected calendar and Gmail cover this with more structure and fixed cadence. |
| `/ideas` pattern-mining command | ALREADY-HAVE | The daily audit already writes at least one genuinely considered idea, or a reasoned note that none survived scrutiny, into midna-book IDEAS.md. The repo's version has no scrutiny bar. |
| `/create` drafting command | SKIP | Content drafting in the user's voice for external publication is not a memory mechanism, and this program adopts memory mechanisms only. Nothing here needs it. |
| Guided onboarding pattern (pre-flight, agent-can vs user-only pauses, slowest dependency first, troubleshooting list) | ALREADY-HAVE | Local skills and job bodies already encode pre-flight checks, approval pauses, and named failure modes at higher specificity (InfinityBlade scope blocks, gated approvals). The pattern is sound; it is not new here. |
| Single-word vault folder, "Open folder as vault" | SKIP | Obsidian-application mechanics with no local counterpart or need. |

## 5. Risks

- **Externally fetched instruction file.** Step 2a's curl of Karpathy's gist into `CLAUDE.md` means the vault's standing agent instructions are whatever that gist contains at download time, unpinned and unsigned. In this repo it is presented as a convenience; adopted carelessly, the same pattern would let any edited gist rewrite agent behavior. Recorded as SKIP above; the local rule stands: instruction files are authored and reviewed here.
- **Privacy claim versus mechanism.** The README FAQ says data "never leaves your machine" because files are local, while Step 1c sends the content of every exported conversation through Claude Code to Anthropic for tagging, in 10 parallel sub-agents. The exports are the user's complete ChatGPT and Claude history, the most concentrated personal corpus he has. Local file storage does not make the processing local. Any future native ingest must state this plainly and run only on an export the user explicitly provides for that purpose.
- **Permission breadth in Step 3b.** Full Disk Access for Terminal plus Automation control of Messages, held by a long-running session, is the widest permission grant in any repo in this sweep. It also reads messages from third parties who never consented to wiki processing.
- **Parallel store of truth.** The whole method builds a new Obsidian vault as the memory. Adopted wholesale it would create a second store of facts about the user competing with ~/MEMORY.md, which this program expressly forbids. Only the scoped ingest candidate survives, and only because it feeds the existing pipeline rather than founding a new one.
- **No verification anywhere.** The organise step has no post-check: sub-agent tagging quality, missed conversations, broken links, and invented tags are never measured. Under local law an unverified conversion is UNVERIFIED, not done. The repo's own troubleshooting list covers setup failures only, never output correctness.
- **Secrets in memory: REJECTED.** The owner has expressly rejected the suggestion, present in the source-article orbit of this sweep, that secrets, keys, or credentials be kept in memory or notes. That tip is recorded here as rejected, not adopted, not deferred. Credentials live only in the Secure Vault and connector-managed storage; no audit candidate in this file involves placing any secret in any note, vault page, or memory file.
- **Maintenance and platform drift.** One release (1.0.0, 2026-04-17), a changelog with a single entry, one author, and hard dependencies on Claude Code's Channels plugin, the NotebookLM skill ecosystem, macOS permission flows, and a personal gist. Several of those surfaces have already changed naming and behavior since April 2026 in the wider ecosystem. Low stars-to-forks maturity (216 stars, 43 forks) for a tool that asks for data exports and disk access.
- **Mac-centrism.** Steps assume macOS throughout (Cmd+Space Terminal flow, iMessage, Full Disk Access). The user's laptop is Windows and Midna's VM is Linux; Step 3b cannot run in either environment here.
- **Code risk is low but nonzero.** The only executable in the repo, `render-social-preview.js`, launches Puppeteer with `--no-sandbox` and expects an npm install; it is author-side preview tooling, was read as text only, and is not part of any adoption path.
- **Licence.** MIT, with a credits-preservation request for Karpathy, Freedman, and Isenberg. No licence obstacle to reimplementing the procedures natively; the ideas themselves are credited to those three in the repo, not original to it.

## 6. Bottom line

charlie947/ai-second-brain is a friendly onboarding wrapper around other people's ideas: Freedman's export organisation, Karpathy's raw/wiki pattern, Isenberg's slash commands. For a non-technical Mac user starting from zero it is a real service. For this system it is mostly a mirror: Midna already has continuous capture, provenance-grade logs, entity pages, registers, scheduled daily passes, and connected Gmail and Calendar, all under stricter rules than the repo proposes. Three scoped candidates survive: a native export-ingest path for external AI histories (only if the user supplies an export, feeding the existing pipeline), an explicit raw-versus-compiled split in research-note conventions, and a named contradiction/orphan/missing-page lint report over the existing memory pages. Everything else is ALREADY-HAVE or SKIP, and Step 1 execution remains unauthorized and undone.

## Provenance

Resolved and read 2026-11-02 via:

- Web search: "charlie947 ai github ChatGPT Claude exports Obsidian linked notes" and "site:github.com charlie947" (search sessions 7498464679690123974, 806117125964108482).
- GitHub API: https://api.github.com/repos/charlie947/ai-second-brain and https://api.github.com/repos/charlie947/ai-second-brain/git/trees/HEAD?recursive=1 (HEAD 6b14a5282f3fe1cbb6beb45b7a9444adcc0f84ab, tree not truncated, 10 files).
- Raw files read in full: https://raw.githubusercontent.com/charlie947/ai-second-brain/main/README.md , /SKILL.md , /CHANGELOG.md , /.gitignore , /render-social-preview.js (read as text, never executed).
- Source article: https://charliehills.substack.com/p/how-i-built-a-2nd-brain-with-ai (via search result text).
- Local baseline: workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md , ~/MEMORY.md (structure and head), ~/workspace/midna-book/ file list including memory/ registers, workspace/research_notes/obsidian-second-brain-sweep-20261102/ (peer audit format).
- Not read: ai-second-brain.skill (binary package, duplicate of SKILL.md, not installed or opened), social-preview.png (image asset).
