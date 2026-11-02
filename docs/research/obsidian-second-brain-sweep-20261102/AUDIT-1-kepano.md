# AUDIT 1: kepano/obsidian-skills

Program: Obsidian second-brain sweep, 2026-11-02. Auditor: workflow agent (audit 1).
Status: PARTIAL by construction. The repo is fully read and classified below; no adoption is proven because this program authorizes audit only, no implementation. Every mechanism is classified ALREADY-HAVE, CANDIDATE, or SKIP with a reason.

## SCOPE (InfinityBlade)

- Surface: read-only audit of one third-party repo against Midna's existing file-based memory (~/MEMORY.md, ~/memory/, ~/workspace/midna-book/ registers). Output is this file only.
- Constraints: no code from the repo was cloned-and-run or executed; all reads were GitHub API, raw file URLs, and web pages. MEMORY.md untouched. No parallel store of facts about the user proposed. No desk strategy, sizing, or Tensor surface touched. No public save.
- Outcome: the exact repo resolved, its mechanisms extracted from source, each classified against what already exists here, risks named.
- Proof: provenance list at the end names every URL and file read. Classifications cite the local file that already implements the equivalent.
- Edges: the repo is format knowledge for the Obsidian app. Midna's memory is runtime-managed Markdown on a headless Linux VM with no Obsidian install; that mismatch decides most of the audit.

## 1. Resolution

Resolved: **kepano/obsidian-skills**, https://github.com/kepano/obsidian-skills

How resolved, three routes agreeing:
1. Web search ("kepano obsidian skills GitHub Claude") returned multiple independent sources naming `kepano/obsidian-skills` as Steph Ango's (Obsidian CEO, @kepano) Agent Skills repo, including the install line `npx skills add git@github.com:kepano/obsidian-skills.git`.
2. GitHub API `GET /repos/kepano/obsidian-skills` returned the repo directly: description "Agent skills for Obsidian. Teach your agent to use Obsidian CLI and open formats including Markdown, Bases, JSON Canvas.", created 2026-01-02, MIT license, default branch main, 50,618 stars and 3,579 forks at audit time.
3. Third-party corroboration (vibecoding.app review, memory-atlas adapter README, claude-code-playbook) all point at the same owner/name and the same skill list.

The task hint said six skills; the live tree carries exactly six: obsidian-markdown, obsidian-bases, json-canvas, obsidian-cli, defuddle, knap. (Older secondary sources say five; knap is the later addition. The repo itself is the authority.)

## 2. What the repo actually is

Pure documentation. The full recursive tree contains only Markdown files, two plugin manifests (`.claude-plugin/plugin.json` v1.0.1, `marketplace.json`), and the MIT LICENSE. There is no code, no script, no hook, no installer inside the repo. Each skill is one SKILL.md (Agent Skills spec frontmatter: name + description) plus, for three skills, a references/ folder.

What it is not: it contains no memory system. No ingest pipeline, no query or lint flow over a knowledge store, no session load/save ritual, no memory splitting, no curation or supersession rule. It teaches an agent to *author valid Obsidian files*. Any "second brain" behavior would have to come from Obsidian itself or from other repos in this sweep; this one is the file-format layer only.

## 3. Mechanisms extracted (from source)

### 3.1 obsidian-markdown (SKILL.md, 196 lines; references PROPERTIES.md, CALLOUTS.md, EMBEDS.md)
- Obsidian Flavored Markdown authoring workflow: frontmatter properties first, content, wikilinks for internal notes, embeds, callouts, then verify in reading view.
- Wikilinks: `[[Note]]`, `[[Note|Display]]`, `[[Note#Heading]]`, block links `[[Note#^block-id]]` with `^block-id` anchors appended to paragraphs.
- Embeds: `![[Note]]`, `![[image.png|300]]`, `![[doc.pdf#page=3]]`.
- Callouts: `> [!type]`, foldable with `-`/`+`, custom titles, nesting.
- Properties: YAML frontmatter with typed values; defaults `tags`, `aliases`, `cssclasses`; nested tags `#nested/tag`; hidden comments `%%...%%`; highlights `==text==`; LaTeX; Mermaid with `internal-link` class.

### 3.2 obsidian-bases (SKILL.md, 499 lines; references FUNCTIONS_REFERENCE.md)
- `.base` files: YAML defining database-like views over notes selected by frontmatter properties.
- Structure: global `filters` (recursive and/or/not objects over expressions like `file.hasTag("x")`, `status == "active"`), `formulas` (computed properties, e.g. `(date(due) - today()).days`), `properties` display names, `summaries` (Sum, Average, Median, Earliest, Unique, etc.), and `views` (table, cards, list, map) each with own filters, order, groupBy, limit.
- Three property classes: note properties (frontmatter), file properties (`file.name`, `file.mtime`, `file.backlinks`, `file.links`...), formula properties. Validation step: check YAML validity and that every referenced property/formula exists.

### 3.3 json-canvas (SKILL.md, 244 lines; references EXAMPLES.md)
- `.canvas` files per JSON Canvas Spec 1.0: top-level `nodes` and `edges` arrays.
- Nodes: unique 16-char hex `id`, `type` (text/file/link/group), `x/y/width/height`, optional color; array order is z-index. Edges: `fromNode`/`toNode` plus side anchors and labels.
- Mechanical validation ritual after every create/edit: JSON parses, all IDs unique, every edge endpoint resolves to an existing node, new nodes placed with 50-100px spacing to avoid overlap.

### 3.4 obsidian-cli (SKILL.md, 106 lines)
- Command surface over a *running* Obsidian instance: `obsidian read/create/append/search`, `daily:read` / `daily:append`, `property:set`, `tasks`, `tags`, `backlinks`; targeting by `file=` (wikilink-style name resolution) or `path=`, and `vault=<name>`.
- Plugin dev loop: `plugin:reload`, `dev:errors`, `dev:screenshot`, `dev:dom`, `dev:console`, and `obsidian eval code="..."` (arbitrary JavaScript in the app context).

### 3.5 defuddle (SKILL.md, 41 lines)
- External CLI (kepano/defuddle, npm): `defuddle parse <url> --md` extracts clean readable Markdown from a web page, stripping navigation/ads to save tokens; `--json` and `-p <property>` metadata modes.

### 3.6 knap (SKILL.md, 102 lines)
- External CLI (obsidianmd/knap, npm, Node 20+): renders Markdown templates (`{{ var }}`, `|` filters, `{% if/for %}` logic, `yaml_property` filter for correct frontmatter quoting) from JSON/CSV data.
- `knap validate` checks template syntax statically; `knap batch` generates one file per CSV row / JSON object with filename templates, `--dry-run`, duplicate-name detection, overwrite gating.
- Documented pipeline: defuddle JSON output piped into knap to turn a web page into a templated note.

## 4. Classification against what exists here

Local baseline read for comparison: `workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md` (the memory design: Tier 0 platform memory, Tier 1 CONTEXT-SNAPSHOT, Tier 2 registers STATE/RULINGS/OPEN-THREADS/LESSONS/STRATEGIES with fixed schemas), the structure of ~/MEMORY.md (curated facts/laws with dated claims), and the ~/workspace/midna-book/ file list (CHARTER, JOURNAL, ledger.json, memory/ registers and snapshots all present on disk).

| Mechanism | Class | Reason |
|---|---|---|
| Fixed-schema frontmatter/properties on notes | ALREADY-HAVE (stronger) | Midna's registers already carry fixed field schemas (MEMORY-SYSTEM.md sections 3.4-3.6, 5.2) enforced by audit checks; platform claims carry id/date/source. Obsidian properties are a looser, untyped-by-default version of the same idea. |
| Wikilinks / block IDs for internal cross-reference | SKIP | Our files cross-reference by explicit path and claim id, resolvable by grep and `muse.memory_explain`. Wikilinks only resolve inside Obsidian; adopting the syntax without the app adds a dialect nothing here renders, and renaming safety (Obsidian tracks renames) is moot where paths are cited verbatim by law. |
| Callouts, highlights, embeds, hidden comments | SKIP | Presentation dialect for a human reading in Obsidian. Our Markdown is consumed by agents and rendered surfaces that do not interpret OFM; callouts would degrade to raw `> [!warning]` text. |
| Bases: derived views (filters/formulas/summaries) computed over note properties instead of hand-maintained index notes | CANDIDATE (pattern only) | The genuinely interesting idea in the repo: an index that is a *query*, not a maintained copy, so it cannot drift from the records it lists. Our INDEX.md files and STRATEGIES.md index are hand/runtime maintained. If register volume grows, a native reimplementation (a small script that renders a view from register frontmatter) would extend the existing registers without a parallel store. Value is conditional and modest today; the `.base` format itself is SKIP (needs Obsidian to render). |
| JSON Canvas spatial files + ID/edge validation ritual | SKIP (format); ALREADY-HAVE (ritual) | No spatial-canvas need in the memory system. The validate-after-edit discipline (unique IDs, all references resolve) is already our practice via regression blockers and read-back verification. |
| obsidian-cli vault operations (search, backlinks, daily append, property set) | SKIP | Requires the Obsidian desktop app open; this VM is headless and has no vault. The same operations here are file reads, grep, and the memory tools. `daily:append` parallels our daily logs, which the runtime already owns. |
| defuddle clean web extraction | CANDIDATE (low) | A token-saving clean-Markdown extractor is a real, small utility. But our browser fetch already returns page text, and adopting it means an npm global install of third-party code, which this program forbids running unscanned. Reimplement-or-defer: note as a candidate only if web-ingest volume makes extraction cost material. |
| knap template + data rendering, batch generation, validate-before-render | ALREADY-HAVE (pattern) | The snapshot rewrite is already template-bound (MEMORY-SYSTEM.md section 4.2 normative template) and produced from structured registers; batch note generation from CSV/JSON is not a current memory need. The `yaml_property` quoting lesson is worth one line if we ever generate frontmatter mechanically: quote via a YAML emitter, never string interpolation. |
| Agent Skills packaging itself (SKILL.md + references/, agentskills.io spec) | ALREADY-HAVE | Our own skill system uses the same shape (name/description frontmatter, references on demand); this repo is a conforming example, not a new mechanism. |

Net: no mechanism in this repo fills a gap in the memory architecture. It is an authoring-format pack for an app we do not run. Two pattern-level candidates (query-derived index views; a clean-extraction utility) are recorded, both conditional, neither urgent.

## 5. Risks

- **Execution surface in obsidian-cli**: `obsidian eval` runs arbitrary JavaScript in the Obsidian app context, and the skill instructs the agent to use it. If this skill were ever installed alongside a real vault, that is a standing code-execution path into the app holding the notes. Not present here; named so it is never adopted casually.
- **Install routes execute third-party code**: the README's routes (`npx skills add`, `npm install -g defuddle`, `npm install -g knap`, plugin marketplace) all fetch and run external packages. Per this program's rails none were run; any future adoption must be a native reimplementation or a scanned, pinned install approved separately.
- **App dependency / headless mismatch**: obsidian-cli and Bases rendering require Obsidian installed and, for the CLI, running. On this VM that dependency fails closed (nothing works), which is safe but makes most of the pack dead weight.
- **Parallel-store risk**: the natural way to "use" this pack is to stand up an Obsidian vault and start keeping notes there. That would create a second store of facts about the user beside ~/MEMORY.md and the midna-book registers, violating the single-source-of-truth rail. Any future use must be as a *rendering/view layer over the existing files only*, never a new home for facts.
- **Secrets in notes**: this repo itself never suggests storing secrets in notes. Separately, per the program brief, a source-article tip suggesting keeping secrets in memory was reviewed and is **REJECTED by the owner**: no secret, key, token, or credential is ever written into any memory file, note, or vault page, in this system, regardless of source. Recorded here as rejected so no later pass resurrects it.
- **License/maintenance**: MIT, single-author (Steph Ango), created 2026-01-02, last push 2026-09-15 at audit time, 75 open issues. License is no barrier to reimplementation; maintenance is healthy but bus-factor is one person plus the Obsidian team. Low risk either way because nothing here is load-bearing for us.
- **No phone-home in the repo itself**: the repo is static Markdown and JSON manifests; nothing in it collects or transmits data. The external CLIs it points to were not run or audited here, so no claim is made about their network behavior.

## 6. Verdict

kepano/obsidian-skills is a well-made, MIT-licensed format-teaching pack: six SKILL.md files that make an agent write valid Obsidian Markdown, Bases, and Canvas files, drive the Obsidian CLI, and use two companion extraction/templating CLIs. It contains no memory architecture: no ingest, query, lint, session, or curation mechanism to adopt. Against Midna's existing system (runtime-curated MEMORY.md, claim-sourced daily logs, schema-bound midna-book registers, template-bound snapshot with a recovery drill), every load-bearing idea it has is already present in a stronger form. The only genuinely new pattern worth keeping on the list is Bases' query-defined index views, a candidate for a native reimplementation over the existing registers if index drift ever becomes a measured problem. Everything else is SKIP, mostly because it is dialect or tooling for a desktop app this system does not run.

## Provenance

Read in full unless noted:
- https://api.github.com/repos/kepano/obsidian-skills (metadata) and `.../git/trees/main?recursive=1` (full tree)
- https://raw.githubusercontent.com/kepano/obsidian-skills/main/README.md
- https://raw.githubusercontent.com/kepano/obsidian-skills/main/LICENSE
- https://raw.githubusercontent.com/kepano/obsidian-skills/main/.claude-plugin/plugin.json and marketplace.json (plugin.json read; marketplace.json fetched, 268 bytes)
- skills/obsidian-markdown/SKILL.md; references/PROPERTIES.md, CALLOUTS.md (heads read), EMBEDS.md (via SKILL.md summary)
- skills/obsidian-bases/SKILL.md; references/FUNCTIONS_REFERENCE.md (head read)
- skills/json-canvas/SKILL.md; references/EXAMPLES.md (head read)
- skills/obsidian-cli/SKILL.md; skills/defuddle/SKILL.md; skills/knap/SKILL.md
- Web search results: vibecoding.app Obsidian Skills review; muslewski/memory-atlas adapter README; cormff/claude-code-playbook companion skills doc (corroboration of identity and skill list)
- Local: workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md; ~/MEMORY.md (structure, head); ~/workspace/midna-book/ recursive file list; ~/workspace/AGENTS.md and ~/AGENTS.md (house rules)
