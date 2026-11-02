# AUDIT 3: eugeniughelbur / obsidian-second-brain

Program: Obsidian second-brain sweep, 2026-11-02. Item 3 of 7.
Scope focus per brief: `/obsidian-save` (save decisions and tasks from a conversation) and `/obsidian-world` (load current state at the next session), plus the machinery under both.
Method: READ-ONLY. GitHub API + raw file reads + web pages. Nothing cloned-and-run, nothing executed, no installer or hook run. All repo text below was read as evidence only.
Status: PARTIAL by design of the audit itself: repo fully resolved and read; adoption decisions are classifications, not implementations (no adoption is authorized inside this program).

## 1. Resolution

**Resolved: `eugeniughelbur/obsidian-second-brain`**
URL: https://github.com/eugeniughelbur/obsidian-second-brain

How resolved (three independent routes, all agreeing):
1. Web search "eugeniughelbur obsidian-save obsidian-world GitHub" returned the repo's own commits, CHANGELOG and PRs naming `/obsidian-save` and a propagation payload for it.
2. GitHub API `GET /users/eugeniughelbur/repos` listed the owner's repos; `GET /repos/eugeniughelbur/obsidian-second-brain` confirmed the description: "Persistent memory for Claude Code, Codex and 6 other AI agents, stored as plain markdown in your Obsidian vault... 48 commands: semantic search, self-rewriting notes, key-less research, scheduled agents."
3. The repo tree (Git Trees API, recursive, 397 blobs, not truncated) contains the two named artifacts literally: `commands/obsidian-save.md` and `commands/obsidian-world.md`.

Repo facts (GitHub API, read 2026-11-02): MIT licence; created 2026-03-24; 5,107 stars; 633 forks; 8 open issues; default branch `main`; HEAD commit at crawl time f79c64f3; last push 2026-11-01; solo maintainer (Eugeniu Ghelbur, theaioperator.io). Very young, very fast-moving: v0.16.0 shipped 2026-09-15, command count grew 43 to 49 across 2026.

## 2. What was read (provenance)

From the repo at `main` via raw.githubusercontent.com (copies held in the workflow workdir, not the workspace):
- `README.md` (83,911 bytes, read in full by sections: How It Works, all 49 commands table, The Vault is Alive / OKM, Background & Scheduled Agents, Vault Architecture, Install, FAQ)
- `SKILL.md` (90,569 bytes: Core Operating Principles read in full; per-command sections for save/world read; headings surveyed for the rest)
- `commands/obsidian-save.md`, `commands/obsidian-world.md` (both in full: these are the brief's two items)
- `commands/obsidian-reconcile.md`, `commands/obsidian-graduate.md`, `commands/obsidian-catchup.md`, `commands/obsidian-health.md`, `commands/obsidian-find.md`
- `references/freshness-policy.md` (the OKM spec, in full), `references/ai-first-rules.md`, `references/write-rules.md`, `references/vault-schema.md`, `references/folder-map.md`
- `AI-FIRST.md`, `SECURITY.md`, `.env.example`, `CHANGELOG.md` (via search excerpts)
- `hooks/hooks.json`, `hooks/load_vault_context.py`, `hooks/obsidian-recall.py` (source read as text, never run)
- `scripts/session_archive.py` (header and design contract read as text)
- Full recursive tree listing (397 files), including `scripts/` (~70 Python/shell helpers), `integrations/obsidian-mcp-server/`, `integrations/telegram-journal/`, `adapters/` for 8 agent CLIs
- Author's article: theaioperator.io, "HUGE update on obsidian-second-brain: The Architect" (2026-06-02)

Local comparison sources read:
- `~/workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md` (Midna's memory design: tiers, snapshot protocol, registers, lessons lifecycle, recovery drill)
- `~/MEMORY.md` structure (section survey only; never edited)
- `~/workspace/midna-book/` and `~/workspace/midna-book/memory/` file lists (CHARTER, JOURNAL, ledger.json, CONTEXT-SNAPSHOT, STATE.md, RULINGS.md, OPEN-THREADS.md, LESSONS.md, STRATEGIES.md, snapshots/, strategies/ all exist: the MEMORY-SYSTEM design is implemented, not just specified)
- `~/memory/` daily logs and `~/memory/people/`, `~/memory/groups/` indexes (platform layer, from session context)

## 3. The system in one paragraph

A Claude Code skill (plus adapters generating equivalent builds for Codex, Gemini, OpenCode, Copilot, Grok Bot, Hermes, Pi) that operates a plain-markdown Obsidian vault as the agent's persistent memory. One codebase, 49 slash commands in four layers: Operations (save, ingest, daily, tasks, people, boards, health, reconcile, merge, export), Thinking (challenge, panel, emerge, distill, graduate), Context (one command: `/obsidian-world`), Research (X, web, YouTube, podcasts, NotebookLM). Two layouts (Obsidian-style folders or wiki-style `raw/` + `wiki/`). A vault-root `_CLAUDE.md` operating manual, an `index.md` catalog, append-only operation logs, and a maintenance doctrine named OKM (Open Knowledge Metabolism). Optional hooks (session-start context load, post-write format validation, post-compaction background agent), optional scheduled agents, an optional MCP server exposing the vault as tools, and an optional Telegram capture bot.

## 4. Mechanisms extracted

### 4.1 /obsidian-save (the save ritual)
- Trigger phrases in 6 languages; also proactive: the agent is instructed to *remind* the user to save after 10+ exchanges, at wrap-up signals ("ok", "thanks", "done"), and when a logical work block completes.
- Flow: read `_CLAUDE.md`; optionally archive the raw chat (see 4.6); scan the whole conversation; classify items into people / projects / tasks / decisions / ideas / deals / content; spawn one parallel subagent per class; each searches before creating (duplicates are "vault rot"), creates or updates the typed note, then propagates: daily note gets links to everything saved; boards, project notes, people notes cross-updated per a fixed propagation table ("never create an orphaned note").
- Absorbs the dev-log command: a substantial work session also yields a dated dev-log note linked from project + daily note.
- Every note written follows the AI-first rule (4.4).

### 4.2 /obsidian-world (the load ritual)
- Progressive disclosure with explicit token budgets: L0 Identity (~170-200 tokens: `SOUL.md`/`About Me.md`, `CRITICAL_FACTS.md`, `CORE_VALUES.md`), L1 Navigation (~1-2K: `index.md` catalog + last 10 operation-log entries), L2 Current State (~2-5K: Home/Dashboard, today's + last 3 daily notes, active kanban boards, prior session digests), L3 Deep Context (5-20K, on demand only: active project notes, knowledge notes, recent people).
- After L0-L2 it presents a fixed five-line boot status: who I am to you / current priorities (top 3-5) / open threads from last session / overdue-needs-attention / today so far. Explicitly "a boot-up sequence, not a report."
- `CRITICAL_FACTS.md`: a separate ~120-token file of always-needed facts (timezone, manager, location, company, role), capped under 150 tokens, loaded every session, updated whenever a critical fact changes.
- `PINNED.md`: task-scoped pinning. During a long task the agent writes critical task facts/schemas to `PINNED.md` at vault root; it loads at L0; cleared when the task ends. Explicitly aimed at surviving context compaction.
- Missing identity files trigger a 5-7 question bootstrap interview.

### 4.3 Vault structure and note format
- Two layouts with a folder-map resolver so commands work in either: Obsidian-style (`Daily/`, `People/`, `Projects/`, boards) or wiki-style (`_CLAUDE.md`, `index.md`, `log.md`, `raw/` immutable sources, `wiki/{entities,concepts,projects,daily,logs,reviews,tasks,decisions}`, `boards/`, `templates/`).
- Per-type frontmatter schemas (vault-schema.md): daily, project, task, entity, source, concept, dev log, decision record (ADR), kanban board, goal. Naming conventions and Dataview query patterns included.
- `index.md`: catalog of all pages, one line each, grouped by folder; read first for navigation instead of searching; updated on every create/delete.
- Operation log: append-only; modern vaults split it per day (`Logs/YYYY-MM-DD.md`, `**HH:MM** - action | description`), root `log.md` becomes a pointer file; a migration script converts the monolithic form.

### 4.4 AI-first note rules (references/ai-first-rules.md)
Every note: (1) self-contained context, (2) a `## For future agent` 2-3 sentence preamble so any agent can judge relevance in 10 seconds, (3) rich frontmatter (`type`, `date`, `tags`, `ai-first: true` + type fields), (4) a recency marker on every external claim ("X raised $24M (as of 2026-04, source)"), (5) sources preserved verbatim with URLs inline, (6) mandatory `[[wikilinks]]` for every person/project/concept, (7) confidence levels (`stated | high | medium | speculation`). A PostToolUse hook (`validate-ai-first.sh`) mechanically validates writes against the format. Anti-fabrication hard rules: search exhaustively before claiming absence ("false absence is the most common failure mode"); never invent facts or dates; unknowns marked `TBD`.

### 4.5 OKM freshness policy (references/freshness-policy.md + scripts/freshness_lint.py)
The repo's most formal mechanism. One rule: **every stored fact must be timeless, dated, or a pointer; nothing may claim to be current without a stamp.**
- Slow facts ("wiring", stable 7+ days) are stored. Fast facts ("meter", can change within 7 days: counts, balances, statuses) are NOT stored bare: they are stored as a dated snapshot ("2026-07-13: pipeline at 13 open deals") or as a pointer ("Where truth lives: <CRM link>. Last observed: 13 (as of 2026-07-13)").
- The one illegal form: a present-tense claim about a fast fact, undated, outside a dated container.
- A linter enforces it: FRESH-1 (error) unstamped quantitative present-tense claim about a volatile noun outside a dated container; FRESH-2 (warning) stamp older than the freshness window (default 7 days); FRESH-3 (error) pointer with an unresolvable target; FRESH-4 dated containers are exempt immutable history; FRESH-5 (warning) unused suppression directives. A per-line `<!-- freshness: example -->` escape exists for quoting the illegal form.
- The refresh loop is the maintenance: aged stamps get exactly three answers: re-observe (update value + stamp), convert (drop the number, keep the pointer), retire (move into a dated note where it becomes immutable history). Run weekly.
- `/obsidian-health` runs this lint plus contradiction scan, orphan detection, stale-claim flags, a typed-edge lint over a `relations:` graph, and an opt-in tag taxonomy audit.

### 4.6 Raw session archive (scripts/session_archive.py, opt-in)
`/obsidian-save` rewrites a conversation into notes and drops the conversation; their cited "Memory Tax" study (arXiv 2610.34073) measured that rewrite losing facts. The fix: with `OBSIDIAN_SESSION_ARCHIVE=1`, save also writes a redacted copy of the raw chat to `raw/sessions/`: user+agent speech only (tool calls, tool output, thinking, injected context, subagent chains dropped, which is also where they note the bulk and the secrets live), secrets redacted by pattern before writing, files keyed by session id (re-save refreshes in place), cut at turn boundaries into linked parts of ~7,000 characters because their semantic index only embeds the first chunks of a note. Notes written by save link the archive part they came from in `sources:` frontmatter, so a note can be followed back to the full chat.

### 4.7 Bi-temporal facts
When a fact changes, never overwrite: append to a `timeline:` frontmatter array with event time (`from`/`until`), transaction time (`learned`), and `source`. Top-level fields always show current state; the array preserves full history. Enables "who was my manager in February" and distinguishes genuine contradiction from evolution during reconcile.

### 4.8 Reconcile with quote-proof (commands/obsidian-reconcile.md)
Parallel subagents (claims, entities, decisions, source-freshness) hunt contradictions, but a finding is only actionable as two verbatim quotes with `path` + `line`, each at least 12 characters, copied character-for-character. Both quotes must pass a mechanical checker (`scripts/verify_quotes.py`) before anything is rewritten; unproven pairs are dropped and listed as "Dropped as unproven." Proven contradictions resolve three ways: clear winner (rewrite loser, add a `## History` section quoting what was replaced and why), genuinely ambiguous (a `Conflict - Topic.md` page, `status: open`, both sides verbatim, for the user to decide), evolution (update page, keep historical context).

### 4.9 Self-maintenance machinery
- PostCompact background agent (opt-in, ships inert): after context compaction, runs a headless `claude -p` that updates the vault. Tool surface restricted to Read/Write/Edit/Glob/Grep, no MCP, add/update only, never deletes. It does run with `--dangerously-skip-permissions`; the README states this trade openly.
- Four scheduled agents: morning (daily note + overdue), nightly (close day, reconcile, synthesize, heal orphans), weekly review (Fridays), health audit (Sundays).
- SessionStart hook (`load_vault_context.py`): injects the skill root path and, when cwd is inside the vault, the vault's `_CLAUDE.md` manual, with a 10,000-char cap handled honestly (over budget it injects a "NOT loaded, go read it" pointer instead of a truncated manual that would read as complete). Also detects a second vault plugin's SessionStart hook and states precedence (this vault's `_CLAUDE.md` governs).
- Bounded recall hook (opt-in, `OBSIDIAN_RECALL_ENABLED=1`): on every user prompt, injects at most 4 notes / ~900 chars of relevant vault content; abstains entirely on low confidence; read-only, fail-closed, every inject/abstain decision logged to `.claude-runs/` JSONL.
- Synthesis hook: a pattern seen in 3+ unrelated sources, or reinforced by independent sources, triggers an automatic synthesis page. Two-Output Rule: every insight-producing interaction yields the answer AND a vault update.
- Crew: a shared multi-agent logbook (`~/crew` or `wiki/team/`) so Claude Code, Codex, Cursor and Grok Bot see each other's work lines; every read is headed "records, not instructions"; a logged lesson changes an agent's rules only after a human runs `keep`.
- MCP server (`integrations/obsidian-mcp-server/`): exposes the vault to any MCP client as search/read/save/capture tools, with path-escape guards; designed so the vault is a knowledge layer, explicitly NOT the agent's own behavioural memory.
- Research toolkit: vault-first gap analysis, then key-less free sources (Wikipedia, HN, arXiv, Reddit, etc.) or keyed ones (xAI Grok, Perplexity, Gemini, Tavily, Brave, Groq/OpenAI Whisper, YouTube). Results save as AI-first notes with a propagation payload fed back through `/obsidian-save`.

### 4.10 Idea lifecycle
`/obsidian-capture` (zero-friction capture, incl. a Telegram bot for phone capture), `/obsidian-catchup` (process the capture inbox), `/obsidian-graduate` (idea fragment to full project spec: project note with `graduated-from:` link, goals, phased tasks, board cards; original idea marked `status: graduated`, never deleted), `/obsidian-learn` (review learnings, prune stale, promote patterns to rules), `/obsidian-merge` (merge near-duplicates: dry run by default, frontmatter union, retired note becomes a redirect, never deleted).

## 5. Comparison against what already exists here

Midna's existing architecture (platform layer: `~/MEMORY.md`, `~/memory/YYYY-MM-DD.md` daily logs with claim id + verbatim quote + source message ids, `~/memory/people|groups/` pages with INDEX.md, nightly alignment synthesis; book layer per MEMORY-SYSTEM.md: Tier 1 CONTEXT-SNAPSHOT with archives, Tier 2 STATE/RULINGS/OPEN-THREADS registers with fixed schemas, Tier 3 append-only journal/ledger, LESSONS.md with CANDIDATE-TESTED-RULE/DEAD lifecycle, per-strategy records, pre-registered experiments, monthly recovery drill) already implements most of this repo's ideas, in several places more strictly (proof-before-green, dated conflicts carried unresolved, fail-first regression blockers).

| Mechanism | Verdict | Why |
|---|---|---|
| /obsidian-save parallel typed extraction (people/projects/tasks/decisions/ideas) with propagation | ALREADY-HAVE | Platform hourly upkeep + quiet-moment passes extract claims into MEMORY.md, daily logs and people pages; Moment-1 in-session capture writes rulings/decisions/threads to the registers the same session; the daily audit reconciles. Same shape, already running, and ours never creates a parallel store. |
| /obsidian-world L0-L2 boot status (priorities, open threads, overdue, today so far) | ALREADY-HAVE | The Section 4.4 recovery protocol + CONTEXT-SNAPSHOT template produce exactly this (book state, programs, WAITING-ON-OWNER threads, open defects, dated conflicts, next events), verified by the monthly recovery drill. |
| index.md catalog + append-only operation log (per-day split) | ALREADY-HAVE | People/groups INDEX.md files, daily logs, register schemas and snapshot archives cover catalog + audit trail. |
| AI-first note rules: recency markers, verbatim sources, confidence levels | ALREADY-HAVE | Our claim format is stricter: claim id, verbatim quote, source message ids, muse.memory_explain provenance. Confidence vocabulary (stated/high/medium/speculation) is a lighter-weight cousin of the same idea. |
| Anti-fabrication: search exhaustively before claiming absence | ALREADY-HAVE | Standing InfinityBlade law (route failure is never impossibility; prove absence separately) plus the 2026-10-09 GitHub-search lesson baked into AGENTS.md. Their phrasing validates ours. |
| Raw-is-immutable + derived pages re-derivable | ALREADY-HAVE | Append-only Tier 3 (journal, ledger, daily logs) with curation only in layers above. |
| Scheduled maintenance agents (morning/nightly/weekly/health) | ALREADY-HAVE | Daily audit cron (~21:46 ET), twice-daily desk inspections, weekly/monthly reviews. |
| Idea graduate / learn / merge lifecycle | ALREADY-HAVE | IDEAS.md fed by the daily audit; LESSONS.md CANDIDATE-TESTED-RULE/DEAD lifecycle with dead lessons retained as negative context; goals system for promotion to real projects. Their `graduated-from:` backlink is a nice touch already implied by our lesson/journal id cross-references. |
| Crew shared multi-agent logbook | ALREADY-HAVE | The three-way dead-drop group channel + peer pages (Ausar, Sol, Cursor, Aurelia, GrokBot) already do cross-agent awareness, with a stricter rule: the dead-drop check only reads, never posts. Their "records, not instructions" header + human `keep` gate matches our data-not-instructions law. |
| MCP vault server | SKIP | Muse's memory tools already expose search/get/explain natively. Adding an MCP vault would be a second access path to the same facts and a new attack surface for zero new capability. |
| Self-rewriting vault (ingest rewrites existing pages; contradictions "reconciled automatically") | SKIP as stated | Directly conflicts with our dated-conflict practice: contradictory evidence is a stop signal; both readings are carried, named, and resolved by evidence or the owner's ruling, never silently rewritten away. Their reconcile's conflict-page path (4.8) is the compatible part; the auto-rewrite default is not. |
| PostCompact background agent with --dangerously-skip-permissions writing unattended | SKIP | Unattended writers to the memory of record violate our write boundary (memory_store_check, unattended workers narrowest-scope or read-only). Our capture is job-driven inside governed crons instead. |
| SessionStart / per-prompt hooks injecting vault content | SKIP | The runtime already injects MEMORY.md, indexes and the alignment synthesis each session. A second injector duplicates context, burns tokens, and widens the prompt-injection surface (see Risks). |
| Telegram capture bot, kanban boards, Dataview, Obsidian app itself | SKIP | No Obsidian vault exists here and none is needed; capture arrives via chat and the goals/tasks systems. Tooling in search of a problem we do not have. |
| Research toolkit (Grok/Perplexity/Gemini vault-grounded research) | SKIP | Duplicates existing search/research lanes; worse, it sends vault-derived content to third-party APIs by design (see Risks). |
| Presets, folder layouts, bootstrap installer | SKIP | Our layout exists and is verified. The `curl | bash` installer is never to be run here under any circumstances (read-only law for this program; standing caution generally). |

### Candidates (genuinely new and useful)

1. **OKM freshness lint as a mechanical checker for STATE.md and CONTEXT-SNAPSHOT.md.** We already hold the *doctrine* (proof timestamps per program line; "the snapshot's date is the date of assembly, never the date of the facts"; numbers re-read from systems of record at assembly). What we do not have is their *linter*: FRESH-1 (unstamped present-tense quantitative claim outside a dated container = error), FRESH-2 (stamp older than window = must be answered re-observe / convert / retire), FRESH-3 (pointer must resolve). Reimplementing a small native lint over the two files, wired into the daily audit's existing health checks (MEMORY-SYSTEM Section 8.5), converts a writing habit into a gate. Highest-value item in this repo for us.
2. **Reconcile's verbatim quote-proof gate.** Our dated-conflict practice carries both readings but has no mechanical step proving a claimed contradiction exists in the sources before work is spent on it. Their rule (two character-exact quotes with path:line, machine-verified, unproven pairs dropped and listed as dropped) is a clean, small addition to the weekly review's divergence pass between RULINGS.md and MEMORY.md.
3. **Bi-temporal `timeline:` arrays on people pages.** Our people pages carry dated claims in prose; a structured `from / until / learned / source` array would make "who was X's role in February" and evolution-vs-contradiction checks mechanical. Bounded candidate: the people pages are runtime-owned, so this is a proposal to the platform layer's conventions, not something to hand-edit page by page.
4. **Explicit token budgets per recovery layer.** /obsidian-world's L0/L1/L2 budgets (~200 / ~1-2K / ~2-5K tokens, L3 on demand only) formalize what our recovery protocol does by file order. Adding a stated budget per tier to the snapshot protocol (Tier 1 already targets under 200 lines) is a cheap sharpening, and `PINNED.md`-style task pinning maps to a "current task" block in the snapshot that is cleared at task close. Minor but real.
5. **Proactive save reminder triggers.** Our capture Moments are event-driven (rulings, decisions) and job-driven (daily audit). Their behavioural triggers (wrap-up signals, logical work-block completion, long-exchange count) are a small native addition to Moment 1 for non-ruling context that currently relies on the audit's nightly sweep to catch. Minor candidate; must stay silent in the main chat per chat law.

## 6. Risks (named honestly)

- **Secrets in memory: the tip is REJECTED.** Per the owner's standing ruling for this program, any suggestion from the source-article ecosystem around this repo that secrets or credentials belong in memory files (the always-loaded `CRITICAL_FACTS.md` pattern invites exactly this drift: "facts needed in every conversation") is expressly REJECTED and recorded here as rejected. No secret, key, token or credential ever goes into MEMORY.md, any register, any note or any vault page; credentials live only in the Secure Vault / connector store. In-repo mitigations exist and are noted fairly: their `.env.example` keeps API keys OUTSIDE the vault at `~/.config/obsidian-second-brain/.env` with 600 permissions, and `session_archive.py` redacts by pattern before writing. But the redaction is best-effort regex, and anything a user pastes into a chat (a key, a password) is one missed pattern away from sitting in `raw/sessions/` forever. The pattern of an always-loaded personal-facts file is safe only under a hard no-secrets rule, which is ours.
- **Hooks run code on session start and on every write.** `hooks.json` wires SessionStart (context injection), PostToolUse on every Write/Edit (validation), and PostCompact (spawns a headless agent). Any of these is a persistence and prompt-injection surface if the repo or a vault's `_CLAUDE.md` is ever compromised; the SessionStart hook deliberately injects file content into model context. Their own Crew FAQ concedes the framing header "can't guarantee" log lines won't be read as orders. We do not adopt hook machinery from third-party repos, full stop.
- **The background agent writes unattended with permissions skipped.** Opt-in and tool-restricted, and honestly documented, but it is still an unsupervised writer to the user's memory of record. Incompatible with our memory write boundary.
- **Research toolkit phones home with vault content.** Gap-fill queries and the top-12 vault notes are sent to xAI, Perplexity, Google Gemini, Tavily, Brave, Groq/OpenAI. That is vault exfiltration by design, consented per-run by the user of that tool, but it must never be pointed at Midna's memory files.
- **Auto-open side effect.** Research saves shell out to `open`/`xdg-open` on every saved note unless `RESEARCH_AUTOOPEN=0`; their own changelog records a test that launched the maintainer's real Obsidian app. A reminder that "read the source" ≠ "the source is inert": several scripts have side effects beyond writing notes.
- **Duplication of the single source of truth.** Wholesale adoption would stand up a second store of facts about the user (People/, Projects/, Decisions/, daily notes) next to MEMORY.md and the registers. Two stores of the same facts diverge; that is the exact failure our P1 principle exists to prevent. Only mechanism-level adoption (Section 5 candidates), never store-level adoption.
- **Auto-rewrite vs evidence preservation.** "The vault rewrites itself; contradictions reconcile automatically" is the opposite posture from append-only evidence with dated conflicts carried openly. Adopting the posture, not just the tool, would quietly degrade our provenance standard.
- **Maintenance and licence.** MIT licence is clean for reimplementation of ideas. But: solo maintainer, repo created 2026-03-24, extremely rapid churn (49 commands, format changes across versions, a "Silent Failure" release name), bus factor 1. Anything adopted must be reimplemented natively in our files (per program law), never depended on as an external skill install that can change under us.
- **Token and context cost.** The full SKILL.md is 90 KB and the AI-first spec 32 KB; their own SessionStart hook documents the 10,000-char injection cap failure mode (a truncated manual that reads as complete). Importing their operating manual wholesale would crowd out the context our own laws need.

## 7. Verdict

RESOLVED and audited. The repo is real, active, MIT-licensed, and unusually well-documented; its two named commands do what the brief said. Most of its architecture is ALREADY-HAVE here, in several places in stricter form. Five bounded CANDIDATES are worth carrying into the sweep synthesis, led by the OKM freshness lint (a mechanical checker for a doctrine we already hold) and the verbatim quote-proof gate for contradiction work. Wholesale adoption, the hook/background-agent machinery, the research toolkit, and any secrets-in-memory practice are SKIP / REJECTED for the reasons named above. No files in Midna's memory system were changed by this audit.
