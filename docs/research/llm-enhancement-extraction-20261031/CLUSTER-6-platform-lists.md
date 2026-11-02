# Cluster 6: Platform Repos, Curated Lists, siliconjungle

Research date: 2026-10-31. Method: live GitHub API metadata (`api.github.com/repos/<owner>/<repo>`), README and key source files via `raw.githubusercontent.com`, file trees via the git/trees API. No repo code was installed, cloned-and-run, or executed. Judgements are from actual files read, listed per section.

Reference stack for transfer judgements (the stack being enhanced): file-based memory with nightly synthesis, a SKILL.md skills library, cron/hook proactivity, a strict engineering doctrine (proof-before-green, gate-wired regression blockers), and a personal trading book with its own memory system.

Eight traits used throughout: memory, initiation/proactivity, creativity, abstract thinking, conscientiousness, execution, intelligence, real-time.

---

## 1. openai/plugins

| Field | Value |
|---|---|
| Stars / forks | 7,684 / 979 |
| Last push | 2026-10-30 |
| Created | 2026-03-04 |
| Licence | None stated in API metadata (no SPDX) |
| Archived | No |
| Description (API) | "OpenAI Plugins" |

**What it is.** This is not the retired 2023 ChatGPT web-plugin store. In its current form it is OpenAI's curated collection of 62 Codex plugin bundles (counted from the HEAD tree: `plugins/` contains 62 directories, including adobe, airtable, figma, github, gmail, google-calendar, notion, slack, stripe, supabase, vercel, zoom, plus first-party builds such as build-ios-apps, build-web-apps, codex-security, plugin-eval, superpowers, temporal, public-equity-investing, life-science-research, data-analytics, creative-production).

**Mechanism, in plain terms.** A plugin is a directory, not a service. The required file is `.codex-plugin/plugin.json` (a manifest); optional companion surfaces are `skills/` (each skill a SKILL.md plus optional `agents/openai.yaml`, scripts, assets), `.app.json` (a remote MCP app), `.mcp.json` (MCP server config), plugin-level `agents/`, `commands/`, `hooks.json`, and assets. Discovery is a single JSON marketplace file: `.agents/plugins/marketplace.json` (a second `api_marketplace.json` serves API-key-login users). The bundled `.agents/skills/plugin-creator/` is itself a SKILL.md skill with a scaffolding script (`create_basic_plugin.py`) and a full manifest spec (`references/plugin-json-spec.md`): plugin names normalised to lower-case hyphen-case, marketplace entries carrying `policy.installation` (AVAILABLE / NOT_AVAILABLE / INSTALLED_BY_DEFAULT) and `policy.authentication` (ON_INSTALL / ON_USE), ordering in the marketplace array being render order.

Two sub-bundles matter more than the catalogue as a whole:

- `plugins/plugin-eval` (113 files, with coverage fixtures in lcov / Cobertura / final-json formats and a "metric pack"): an evaluation harness for plugins themselves, i.e. scoring a bundle rather than trusting its README.
- `plugins/superpowers` (109 files, a `skills/` tree): the well-known TDD / debugging / brainstorming playbook set, shipped here as ordinary SKILL.md files, proof that the skill format is the portable unit.
- `plugins/codex-security` (203 files, with a completed-scan example containing `coverage.json`, `findings.json`, `report.md`): security scanning packaged as a plugin with evidence files as its output contract.

**Trait map.** Execution (primary: installable capability bundles), intelligence (plugin-eval, life-science-research, public-equity-investing, consensus), creativity (creative-production, canva, figma, remotion), real-time (gmail, google-calendar, slack, datadog, sentry connectors as MCP apps).

**Quality evidence.** Official OpenAI repo, pushed the day before this research, 7.7k stars. Risks to quality are structural, not maintenance: no licence in the API metadata, so code reuse rights are unclear per bundle; each bundle's real quality varies and several are thin wrappers (consensus is 4 files, a manifest plus app/MCP pointers).

**Transferable value.** The bundle anatomy is almost identical to the reference stack's skills library, so there is nothing to port. The genuinely transferable items are: (a) the marketplace manifest pattern, a single ordered JSON index with install/auth policy per entry, as a cleaner index for a large skills library than directory scanning; (b) plugin-eval's premise, that a skill/plugin should ship with coverage fixtures and a metric pack and be scored before adoption; (c) codex-security's output contract (coverage + findings + report as files) for any scanning skill.

**Risks.** Platform lock-in: manifests, marketplace and `agents/openai.yaml` are Codex/ChatGPT surfaces; the portable part is only the SKILL.md content. Licence ambiguity at repo level. Hype risk in individual third-party bundles.

**Verdict: ADOPT-IDEA** (marketplace-manifest index plus eval-before-adopt for skills). The SKILL.md library itself is **ALREADY-HAVE**.

---

## 2. openai/mcp-extensions

| Field | Value |
|---|---|
| Stars / forks | 1,116 / 55 |
| Last push | 2026-10-30 |
| Created | 2026-09-29 |
| Licence | Apache-2.0 |
| Archived | No |
| Description (API) | "Build plugins that feel like native, first-class features of ChatGPT." |

**What it is.** A specification plus TypeScript and Python SDKs (`@openai/mcp-extensions`, `openai-mcp-extensions`) that add ChatGPT-specific capabilities on top of MCP, with one worked example app (Bits & Bolts, a CAD parts library). Read in full: `docs/spec.md` (53 KB) and `docs/patterns.md`.

**Mechanism, in plain terms.** Extensions are declared as server capabilities and cover:

- **Entrypoints**: an app can register a global (sidebar) entrypoint, a per-thread entrypoint, and file-extension handlers that render a custom viewer when a user opens a matching file type.
- **`ui/update-model-context`**: the app pushes context to the model in two distinct channels, made explicit in patterns.md. Explicit context (`content`) is what the user deliberately selects (an annotation, a highlighted part). Background context (`structuredContent`) is where the user currently is in the app (current page, selected object, camera view), updated as they navigate. Groups, change notifications, thumbnails and "background context" are first-class fields. WebMCP lets the web app register tools the model can call directly on the page (`document.modelContext.registerTool`).
- **Composer at-mentions**: the app exposes searchable resources so a user (or the model) can attach a precise reference instead of pasting prose.
- **Form elicitation**: multi-round-trip structured forms with extended string schemas, numeric answers, option descriptions, thumbnails, suggested values, and resource pickers, i.e. the host asks the user a bounded, typed question instead of the model guessing.
- **Structured settings**: the app advertises a settings schema; the host renders it and the server reads/updates it through tools.
- **Display modes and onboarding**: `preferredDisplayMode` / `availableDisplayModes` (inline vs fullscreen), a declared onboarding flow, and opening local files.
- **Caching pattern** (patterns.md): global entrypoints render from a persisted local cache immediately, then refresh with fresh tool results (stale-while-revalidate), because the sidebar must feel native.

**Trait map.** Real-time (primary: live background context from the surface the user is looking at), execution (WebMCP tools, form elicitation instead of free-text guessing), intelligence (structured settings and typed elicitation reduce malformed inputs), initiation (thread/global entrypoints put the capability in front of the user unprompted).

**Quality evidence.** Official OpenAI, Apache-2.0, CI and release-please automation in-tree, SECURITY.md, pushed 2026-10-30. Very young (created 2026-09-29) and explicitly tied to a minimum desktop version in patterns.md (26.928.20710 for the DevDay 2026 APIs), so the surface will churn.

**Transferable value.** The highest-value idea in this cluster for a non-ChatGPT stack is the **explicit vs background context split**: an agent surface should continuously publish a small structured "where the user is / what is selected" object separately from what the user deliberately hands over, and the agent should treat the two with different weight. Second: **typed form elicitation over free-text clarification** for bounded choices, with suggested values and thumbnails. Third: stale-while-revalidate rendering for any always-on agent surface.

**Risks.** Hard platform lock-in to ChatGPT desktop/web; none of this runs in another host today. Spec churn. The SDKs are not needed by a stack that does not build ChatGPT apps.

**Verdict: ADOPT-IDEA** (context-channel split and typed elicitation). Not adopt-code for this stack.

---

## 3. hashgraph-online/awesome-ai-plugins

| Field | Value |
|---|---|
| Stars / forks | 942 / 880 |
| Last push | 2026-10-31 (same day as this research) |
| Created | 2026-04-07 |
| Licence | Apache-2.0 |
| Archived | No |
| Open issues | 80 |
| Description (API) | Curated list of AI plugins for Claude Code, Codex / ChatGPT, Gemini, Antigravity, Pi / Oh My Pi, Grok, OpenCode, Kimi and more |

**What it is.** A cross-ecosystem catalogue, not a ChatGPT-only list. Its machine-readable index `plugins.json` (read directly) reports **1,116 plugins, last_updated 2026-10-31, across 9 platforms** (codex, grok, agent-skills, claude-code, standalone, mcp, kimi, deepseek-harness, opencode). Category counts in that file: Development & Workflow 605, Tools & Integrations 418, Agent Skills 42, DeepSeek Harness 32, OpenCode 14, Grok 4, Kimi 1. The README (262 KB) documents per-ecosystem plugin anatomies (Codex, DeepSeek Harness / Cordis `dsh.bundle`, Grok `.grok-plugin/plugin.json`, Kimi) side by side, which makes it the best single map of how plugin formats differ.

**Mechanism, in plain terms.** Three mechanisms, only one of which is "a list":

1. **A generated index**: `scripts/generate_plugins_json.py` builds `plugins.json` from the README, with CI checks for alphabetical order, contribution validation and plugin validation (`scripts/validate-contribution.py`, `check-alphabetical.py`, plus a test suite under `tests/`).
2. **A mandatory security scan gate**: per `SCANNER_GUIDE.md` (read in full), a listing needs a completed centralised scan by the HOL Plugin Scanner (separate repo, hashgraph-online/hol-guard) with a **normalised score of at least 75/100** before merge. The scanner scores manifest metadata, secrets and dangerous code, transport hardening, CI/dependency hygiene and permission breadth, marketplace metadata, skill security (hooks, env vars, hard-coded paths) and code quality (dynamic execution, shell injection). Output formats include SARIF for the GitHub Security tab. Projects without their own scanner CI take a 10% trust-score reduction. The guide is unusually honest about evidence: a failed workflow conclusion, a missing artefact or a stale bot comment is explicitly **not** a measured score, and a first-time fork's `action_required` workflow has not run at all.
3. **Trust scores and claim/ownership**: listed plugins carry a registry trust score and a "claim your plugin" flow, so a listing is attributable to a maintainer.

**Mining the list for the eight traits.** Keyword counts over `plugins.json` descriptions: memory 73 entries, test 67, image 42, video 42, github 40, research 36, browser 33, guard 31, security 27, eval 17, scan 15, music 14, monitor 12, schedule 11, exa (web search) 11, reason 10, thinking 8, obsidian 8, diagram 7, remember 5, calendar 8. The density is in developer-workflow verification and memory, not in consumer ChatGPT services, which is the opposite of the older list in section 4. Five entries were inspected properly as their own repos in sections 5 to 9 (done-gate, falsegreen-skill, codex-context-guard, codex-honcho, ejentum-mcp), chosen because they target conscientiousness, memory-under-compaction and abstract reasoning, the traits least covered by platform bundles. Other notable entries not individually inspected: Agent Guard (hooks that block or mask secret leaks, local by default, no telemetry), keep-the-why (project memory of decisions, rejected alternatives, workarounds and incident learnings), MoonMind (self-hosted orchestration of coding agents through durable Temporal workflows with a dashboard), Obsidian Second Brain (47 slash commands plus scheduled maintenance agents over a vault), MorningAI (monitoring 80+ entities across 6 sources into scored daily reports), Task Scheduler (a local MCP server turning task lists into capacity-aware schedules).

**Trait map.** Conscientiousness (primary: the scan gate and trust score), execution, memory, intelligence.

**Quality evidence.** Pushed the same day as the research, 942 stars, 880 forks (fork count close to star count signals heavy contributor throughput rather than readership), tests and multiple validation workflows in-tree. Counterweight: 80 open issues and a catalogue whose individual entries are only as good as a 75/100 automated baseline plus review, which the guide itself says is "not a claim that software is risk-free".

**Transferable value.** The **scan-before-list gate with a numeric threshold, a published scoring rubric, SARIF output, and a trust penalty for projects that do not run the scanner themselves** is a ready-made adoption policy for any skills/connectors library: no skill enters the library unscanned, and the score is attached to the entry. Also transferable: generating the human README and the machine index from one source so they cannot drift.

**Risks.** Depending on an external registry and a scanner the stack does not control; trust scores are a third party's judgement, not proof. Catalogue breadth invites indiscriminate adoption.

**Verdict: ADOPT-IDEA** (scan gate and trust-scored index for the skills library); the list itself is **REFERENCE** for discovery.

---

## 4. Asdivyansh/Awesome-ChatGPT-Plugins

| Field | Value |
|---|---|
| Stars / forks | 20 / 3 |
| Last push | 2026-10-25 |
| Created | 2026-10-16 |
| Licence | CC0-1.0 |
| Archived | No |
| Description (API) | "The curation of most useful ChatGPT Plugins - Free and Open Source" |

**What it is.** A very new, small-maintainer rebuild of the classic awesome-ChatGPT-plugins genre, but on the modern plugin definition. Its README (182 KB, 959 outbound links) opens by defining a plugin as skills (SKILL.md) plus an app (remote MCP server) plus optional MCP Apps UI, and it catalogues **4,338 plugins** (its own "What 4,338 plugins tell us" section) across about 30 consumer and business categories, with structured data in `data/plugins.json`, `data/plugins.csv` and `data/curated.json`, category pages under `catalog/` (including `catalog/mcp-endpoints.md`, creativity, data-and-analytics, scientific-research, security), and a build-your-own section covering official docs, standards and specs, frameworks and SDKs, UI kits, testing and debugging, hosting, templates, open-source plugins worth studying, and skills.

**Mechanism, in plain terms.** A scraped and normalised directory snapshot: `scripts/scrape_directory.js` pulls the public plugin directory, `scripts/normalise_snapshot.py` normalises it, and `scripts/build_catalog.py` generates the category catalogues from the data files. The categories are the mechanism: they are a taxonomy of what people actually ask an assistant to connect to (web search and scraping, automation and agents, docs and knowledge, project and task management, meetings and scheduling, investing and markets, data and BI, research and science, security).

**Mining for the eight traits.** Compared with section 3, this list is where the *service* coverage lives: real-time market and finance plugins, web browsing and search (62 "web" and 39 "brows" mentions in the README), research and science (45 "research" mentions, scholarly search, Wolfram-style computation), creativity (design, whiteboards, image/video/audio generation), and scheduling/meetings. That is also its weakness for this stack: almost all of these are hosted third-party services reached through ChatGPT, not mechanisms that transfer. The entries with transferable mechanism are the ones it shares with the other lists (skills, MCP endpoints, testing/debugging tooling), so no additional repos were inspected from this list alone; the five deep inspections in sections 5 to 9 came from the Hashgraph list where the same trait areas have open, inspectable code.

**Trait map.** Real-time and creativity (by category coverage), execution, intelligence.

**Quality evidence.** Weak by the numbers: 20 stars, 3 forks, created 2026-10-16, one maintainer, a links-check workflow only. Recency is real (pushed 2026-10-25) but there is no security gate, no trust scoring and no per-entry verification comparable to section 3.

**Transferable value.** Two things: (a) its category taxonomy as a gap checklist, i.e. which capability areas a personal agent stack has no answer for (meetings/scheduling, CRM, travel, legal, health); (b) the `catalog/` plus `data/*.json|csv` pattern of publishing one dataset in human and machine form. The 4,338-entry corpus is a market census, not an adoption list.

**Risks.** Highest platform lock-in in the cluster: entries are ChatGPT directory listings, many are paid or OAuth-gated hosted services, and directory listings rot quickly. Small maintainer base means link and status decay. No security screening of listed items.

**Verdict: REFERENCE** (taxonomy and census only). Do not adopt entries from it without an independent inspection of the underlying repo.

---

## 5. kuroudo-ai/done-gate (mined from awesome-ai-plugins)

| Field | Value |
|---|---|
| Stars / forks | 0 / 0 |
| Last push | 2026-09-30 |
| Licence | MIT |
| Description (API) | Stop AI coding agents (Claude Code, OpenAI Codex) from saying "fixed" without evidence. Stdlib Python, no network. |

**What it is / mechanism.** A stop hook for Claude Code and Codex. When the agent's turn ends with a completion claim ("fixed", "done"), the hook checks whether that same turn contains any test result, exit code or command output. If there is none, it blocks the reply **once** with a short instruction to check now or state that the result is unverified, then lets the agent continue. Implementation is stdlib-only Python with no network access, installed either as a plugin or by an `install.py` that backs up existing settings, adds only its own hook line, and is idempotent.

**Trait map.** Conscientiousness (primary and almost pure).

**Quality evidence.** Zero stars and a single recent push, so no social proof at all; the offsetting evidence is the constraint profile (stdlib only, no network, one-shot rather than a loop, honest "unverified" escape hatch instead of forcing a fake test).

**Transferable value.** The reference stack already states proof-before-green as doctrine, but doctrine is a prompt-level rule an agent can believe it has satisfied. done-gate is the same rule as a *mechanical* gate keyed on evidence present in the turn, with the important design choice of blocking once and offering the honest downgrade ("unverified") rather than demanding a pass. That is a strictly stronger enforcement shape than a written rule.

**Risks.** Tiny, unproven project; hook behaviour depends on host support; the claim detector is necessarily heuristic and will both miss paraphrases and occasionally fire on innocent uses of "done".

**Verdict: ADOPT-IDEA** (turn-level evidence check on completion claims). The underlying rule is ALREADY-HAVE as doctrine; the mechanism is the new part.

---

## 6. vinicq/falsegreen-skill (mined from awesome-ai-plugins)

| Field | Value |
|---|---|
| Stars / forks | 2 / 1 |
| Last push | 2026-10-19 |
| Licence | MIT |
| Description (API) | LLM skill that finds false-green tests across Python/TS/JS/Robot using the J1-J6 protocol |

**What it is / mechanism.** A skill (with static-scanner siblings: `falsegreen` for Python/pytest, `falsegreen-js`, `robotframework-falsegreen`) that detects **false-green tests: tests that stay green when the code they cover is broken**. The README's canonical example is a test that asserts a result against the mock's own return value, so it passes for any implementation; the fix is an independently computed expected value. Detection is an ordered six-judgement protocol (J1 to J6, with S-codes for structural patterns) applied semantically by an LLM, which the author positions as a superset of the static catalogues because it can judge what a test was *meant* to prove. Distributed via npm with docs and a CI badge; listed in the HOL registry with a trust-score badge.

**Trait map.** Conscientiousness (primary), intelligence (semantic judgement about test intent).

**Quality evidence.** Very small (2 stars) but unusually well packaged for its size: CI, published packages on PyPI and npm for the whole family, online docs, and a concrete falsifiable claim per finding (this test cannot fail when the code is wrong). The semantic pass is LLM judgement, so findings need review rather than blind trust.

**Transferable value.** Directly complementary to a gate-wired regression-blocker regime: blockers prove a test passes on fixed code, but nothing in a normal gate proves the test would *fail* on the broken code. A false-green audit, run over blocker tests specifically, closes exactly that hole, and the J-protocol's vocabulary (expected value borrowed from the code under test, mock asserted back to itself, assertion-free tests) is a usable checklist even without the tool.

**Risks.** Small project, LLM-based findings can be wrong in both directions, and the full protocol lives partly in external docs. Treat output as candidate findings.

**Verdict: ADOPT-CODE** (as a skill candidate for auditing blocker tests, with findings reviewed) / ADOPT-IDEA for the J1-J6 checklist if the code is not taken.

---

## 7. GreenLv/codex-context-guard (mined from awesome-ai-plugins)

| Field | Value |
|---|---|
| Stars / forks | 4 / 0 |
| Last push | 2026-10-31 |
| Licence | Apache-2.0 |
| Description (API) | "A local correctness sidecar for long-running Codex tasks." |

**What it is / mechanism.** A plugin with nine lifecycle hooks that protects long-running tasks against context loss. It keeps a **private checklist of authoritative requirements** for the task, restores that checklist when the session is compacted or resumed, and **checks recorded evidence before accepting a completion claim**. It is explicitly designed to sit beside, not replace, the host's plan, goals, memories, subagents, worktrees and transcript. The README (18 KB, version 0.15.1 dated 2026-10-05) is unusually rigorous about its own limits: separate-HOME pinning for upgrades, no migration of old task state, hook trust must be granted through the normal client flow and never by editing trust hashes, and public availability is defined by GitHub Release readback.

**Trait map.** Memory (primary: requirements survival across compaction), conscientiousness (evidence check before completion), execution (long-task continuity).

**Quality evidence.** Small (4 stars) but the most carefully documented project in this cluster relative to its size: CI, HOL scanner badge, compatibility and session-storage docs, a behaviour baseline document, and explicit statements of what was and was not acceptance-tested (bounded native macOS/Windows acceptance; earlier CLI versions not retested).

**Transferable value.** Two separable ideas. (a) **A task-scoped, authoritative requirements checklist that is re-injected on compaction/resume**, distinct from general long-term memory: general memory answers "what is true about the user", this answers "what must this specific task not lose". (b) **Completion claims validated against recorded evidence**, not against the agent's current context, which may have lost the very requirement it is claiming to satisfy. Both map cleanly onto a file-based stack (a per-task requirements file plus an evidence log) without the plugin.

**Risks.** Built for Codex hooks and `CODEX_HOME` semantics; version churn is high (0.15.x) and upgrades deliberately do not migrate state. Small maintainer base.

**Verdict: ADOPT-IDEA** (per-task authoritative checklist restored on compaction, plus evidence-checked completion).

---

## 8. plastic-labs/codex-honcho (mined from awesome-ai-plugins)

| Field | Value |
|---|---|
| Stars / forks | 66 / 15 |
| Last push | 2026-09-01 |
| Licence | MIT |
| Description (API) | Honcho memory plugin for OpenAI Codex, harness-level integration via Codex hooks |

**What it is / mechanism.** Hosted long-term memory for Codex, powered by Plastic Labs' Honcho API. Lifecycle hooks capture each session, queue the capture to disk locally first (so capture never blocks a turn or hits the network mid-conversation), upload in the background, and inject relevant context back at session start. Beyond startup injection it offers active recall (search history and query what the service has inferred about the user mid-task), memory scoping per directory, per git branch or per chat instance, and a shared config at `~/.honcho/config.json` so memory follows the user across tools (Claude Code, Cursor, Codex integrations all read the same file).

**Trait map.** Memory (primary and only).

**Quality evidence.** The most adopted mined repo here (66 stars), npm-published, MIT, clear prerequisites. Last push 2026-09-01, so about two months stale at research time. The mechanism is mostly a thin harness over a hosted, key-gated API (`hch-` keys), so the repo itself contains little of the actual memory logic.

**Transferable value.** Two design details are worth copying into a local system: **local-first capture with background upload** (never let memory writing block or fail a turn) and **branch/directory-scoped memory partitions** so project context does not bleed across projects. The core capability, cross-session recall with nightly-style synthesis, is already present in the reference stack in file form, with the advantage of being inspectable and portable.

**Risks.** Hosted dependency and data egress: session content leaves the machine to a third-party API, keys are required, and the memory store is not the user's own files. Pricing/availability risk sits outside the repo. That is a worse trade than the existing local memory for a personal stack.

**Verdict: ALREADY-HAVE** (file-based memory with nightly synthesis is the equivalent, and is local). Copy only the capture and scoping details.

---

## 9. ejentum/ejentum-mcp (mined from awesome-ai-plugins)

| Field | Value |
|---|---|
| Stars / forks | 16 / 4 |
| Last push | 2026-06-11 |
| Licence | MIT (the MCP wrapper) |
| Description (API) | MCP server for the Ejentum API. 8 cognitive operations across 4 harnesses (reasoning, code, anti-deception, memory) |

**What it is / mechanism.** An MCP server whose tools return a *cognitive operation* before the agent generates: a structured procedure (numbered steps, the failure pattern to refuse, and a falsification test) paired with an executable reasoning topology, a DAG of those steps with decision gates, parallel branches, bounded loops, meta-cognitive exits and escape paths. Eight tools in four harnesses (reasoning, code, anti-deception, memory), each in two modes: dynamic (top-1 match from a library of 679 operations, selected by semantic match on the query string) and adaptive (an adapter LLM rewrites every step and DAG node with task-specific identifiers, at about 2 to 3 seconds of extra latency, paid tiers only). Offered over stdio via npm and as a hosted streamable HTTP endpoint.

**Trait map.** Abstract thinking (primary), intelligence, conscientiousness (the anti-deception harness and the built-in falsification test per operation), memory (memory harness).

**Quality evidence.** Real packaging (npm, MCP registry listing) but a thin wrapper: the operation library and the adapter live behind a paid hosted API with a 30-day trial, so the repo cannot be audited for the claims that matter, and there is no published benchmark in the README showing the operations improve outcomes. Last push 2026-06-11.

**Transferable value.** The *shape* is the value, not the service: a library of named reasoning procedures, each carrying (steps, failure pattern to refuse, falsification test) and a DAG topology with bounded loops and explicit exits, retrieved by semantic match to the task and instantiated with task-specific identifiers before work starts. That is a richer unit than a prose SKILL.md and could be applied to a local skills library: add a "failure pattern to refuse" and a "falsification test" field to each skill, and represent multi-branch procedures as a small DAG rather than a linear checklist.

**Risks.** Closed, paid, hosted core; unauditable library; latency and cost per call; vendor lock-in for the one part that matters. Marketing language ("cognitive operations") outruns the evidence supplied.

**Verdict: REFERENCE** (borrow the procedure schema: steps plus refused failure pattern plus falsification test). Do not adopt the service.

---

## 10. siliconjungle page 2: enumeration

`GET api.github.com/users/siliconjungle/repos?page=2&per_page=100` returned exactly **100 repositories** (541 stars in total across the page; 42 pushed in 2025 or later). The page is dominated by three unrelated bodies of work: CRDT and local-first data-structure experiments from 2022 to 2024 (cabinet, causal-tree, crdt-tutorials at 159 stars, delta-crdt, fixed-json-crdt, recycle-list-crdt, run-length-crdt-set and many siblings), a 2026 Ink programming-language ecosystem (ink-lang, ink-planner, ink-knowledge, ink-runtime and a family of lowering/runtime packages, plus Inkwell game-publishing and WebGPU renderer repos), and small JavaScript utilities and game experiments.

Flagged as relevant to LLM enhancement and inspected: `llm-fact-log`, `fs-mcp`, `mcp-template`, `mcp-package-readme`, `ambient-ai-chat`, `cabinet`, `computational-markdown`, and (README level only) `ink-knowledge`. Screened and **not** flagged as LLM-enhancing: `chat-gpt-rpg` (a 2023 ChatGPT-driven game shell with no reusable mechanism described), `screenshot-to-react` (screenshot to React code generation, a single-purpose demo), `recommending-content-based-on-group-interests` (2020, no description or mechanism), `ai-sfx`, `art-styles-dataset`, `feelings-list`, `kiki-bouba-sorted-fonts`, `gemstones` and `portrait-assets` (asset/dataset repos), the CRDT set beyond cabinet, and the Ink/WebGPU/game repos (compiler and rendering work whose LLM relevance is incidental). That screening is by name, description and dates from the page-2 listing; repos not flagged were not opened, and are recorded as screened-out rather than inspected.

---

## 11. siliconjungle/llm-fact-log

| Field | Value |
|---|---|
| Stars / forks | 5 / 0 |
| Last push | 2024-01-16 (created the same day) |
| Licence | None stated |
| Description (API) | "Failed experiment" |

**What it is / mechanism.** A single-file experiment (`index.js`, read in full). Statements are converted by GPT-4 into triples `{a, relationship, b}` (nouns, lower-cased, self-reference replaced with "user") and appended to a fact log; each entity and relationship gets an embedding. A question is converted into assertion triples the same way, then each unknown term is snapped to the nearest existing entity or relationship by cosine similarity, and the log answers by exact triple match. The author is blunt in the README: "The current implementation doesn't work very well", and suggests a merge step that considers the whole statement, plus a post-step asking whether the question is true given the data.

**Trait map.** Memory (primary), abstract thinking (knowledge as triples).

**Quality evidence.** Self-declared failure, one day of work in January 2024, no tests, hard-coded placeholder API key pattern in the source, obsolete model and embedding names. Its honesty is its value.

**Transferable value.** A clean negative result with a diagnosis: triple extraction plus embedding-snapping loses exactly the context that makes facts true or false, and exact-match assertion cannot handle negation, time or uncertainty. A file-based memory that keeps claims with provenance, dates and supersession (rather than bare triples) already avoids this failure mode. Worth citing when anyone proposes reducing memory to a triple store.

**Risks.** None if not adopted; it is abandonware by its author's own label.

**Verdict: REFERENCE** (as a documented negative result for triple-store memory).

---

## 12. siliconjungle/fs-mcp

| Field | Value |
|---|---|
| Stars / forks | 0 / 0 |
| Last push | 2025-05-20 |
| Licence | None stated |
| Description | MCP server with basic filesystem capabilities |

**What it is / mechanism.** Read from source (`src/fs-spec.js`, `src/generic-spec-server.js`). A filesystem MCP server (ls, readFile, writeFile, mkdir, rename, rm) built on a reusable pattern (see section 13). The notable detail is the path guard: every path is resolved against a root taken from `FS_ROOT` or the working directory, and any resolved path that does not start with that root throws "Path escapes project root". Parameters are Zod shapes with encoding aliases normalised (`utf-8` to `utf8`) and sensible defaults.

**Trait map.** Execution (primary).

**Quality evidence.** Zero stars, no licence, no tests, tiny surface. The root-escape guard is real code, not a claim.

**Transferable value.** Only the guard pattern and the alias-tolerant parameter shapes. Filesystem access itself, with stronger permissioning, is already core to the reference stack.

**Risks.** A write-capable filesystem server with only a prefix check is not a security boundary worth importing (symlinks are not addressed in the code read).

**Verdict: ALREADY-HAVE** (filesystem tools), with the root-confinement check noted as a pattern to verify in existing tooling.

---

## 13. siliconjungle/mcp-template (and the SpecServer pattern)

| Field | Value |
|---|---|
| Stars / forks | 0 / 0 |
| Last push | 2025-05-19 |
| Licence | None stated |
| Description | MCP server template |

**What it is / mechanism.** The interesting artefact is shared with fs-mcp and mcp-package-readme: `src/generic-spec-server.js` defines a `SpecServer` class that takes a declarative spec object (`{id, description, tools: [{name, description, parameters, execute}]}`) and registers every tool with the MCP SDK over stdio, normalising return values into MCP content, extracting Zod shapes from parameters, and converting thrown errors into `isError` results. A CLI entry point loads any spec module by path and serves it, so a new MCP server is one spec file (fs-mcp's `fs-spec.js`, the template's `template-spec.js`, package-readme's `package-readme-spec.js`).

**Trait map.** Execution (primary: cost of adding a new tool surface).

**Quality evidence.** Three sibling repos use the same core, which is mild evidence the pattern held up for its author; otherwise zero adoption, no licence, no tests.

**Transferable value.** A genuinely neat idea for a stack that keeps adding small tool surfaces: declare tools as data (name, typed parameters, one execute function) and let one generic host handle protocol, error shaping and result normalisation. It lowers the marginal cost of a new connector to a single file. The reference stack's connector docs already standardise the *documentation* side; this standardises the *server* side.

**Risks.** Unlicensed and unmaintained-looking; the MCP SDK has moved since May 2025, so the code would need re-checking rather than copying.

**Verdict: REFERENCE** (declarative spec-to-MCP-server pattern). Not adopt-code without a licence and a freshness pass.

---

## 14. siliconjungle/mcp-package-readme

| Field | Value |
|---|---|
| Stars / forks | 0 / 0 |
| Last push | 2025-05-14 |
| Licence | None stated |
| Description | MCP server returning the README.md for any npm package (GitHub-first lookup, npm fallback) |

**What it is / mechanism.** A single-tool MCP server on the SpecServer pattern: given a package name, fetch its README from GitHub first, falling back to npm. That fallback ordering (primary source first, registry second) is the whole mechanism.

**Trait map.** Intelligence / real-time (marginal: faster access to primary documentation).

**Quality evidence.** Zero stars, one tool, no licence.

**Transferable value.** Negligible as a tool; the GitHub-first, registry-fallback ordering is a one-line principle already embodied in reading raw source over summaries.

**Verdict: SKIP** (trivial; the same lookup is already available through raw URL fetches and connector docs).

---

## 15. siliconjungle/ambient-ai-chat

| Field | Value |
|---|---|
| Stars / forks | 0 / 0 |
| Last push | 2026-03-14 (created the same day) |
| Licence | MIT |
| Description (API) | "ambient ai chat" |

**What it is / mechanism.** A monorepo ("Social Platform"): an in-memory Node chat/event server, a Next.js mobile-first multiplayer chat client, a CLI client intended for agents or users, and shared protocol types. Read from the README and server sources (`apps/server/src/search.ts`, `state.ts`). The LLM-relevant machinery: every message gets an OpenAI embedding held in memory; search combines semantic cosine ranking with a hand-weighted exact/partial token score (exact phrase 1,500, exact token 260, partial token 110, with reasons recorded); **thread summaries are generated automatically every N messages and per-user profile memory summaries every N authored messages** (interval env vars), persisted with the rest of the state to a single JSON file; there are AI summarise and ask-the-thread endpoints, and a command directory with embeddings so an agent can be *recommended* the right command for a natural-language intent ("find old onboarding messages").

**Trait map.** Memory (primary: interval-triggered thread and per-user profile summaries), real-time (ambient, in-stream processing rather than on request), initiation (command recommendations), intelligence (hybrid semantic plus lexical search with explicit scoring).

**Quality evidence.** Zero stars and one day of commits, so it is a prototype, not a product. The code read is coherent (typed state store, separated search module) and the state model is honest about being in-memory with a JSON snapshot.

**Transferable value.** The **interval trigger** is the transferable piece: summarise on a count of new items rather than only on a clock, so a busy thread gets summarised sooner and a quiet one is not re-summarised. Hybrid search with published weights and recorded match reasons is also a good pattern for searching a memory corpus, because it makes a ranking explainable. The reference stack already does nightly (clock-based) synthesis and per-user profile memory; count-based triggers would be an addition, not a replacement. Command recommendation by embedding similarity is a small, useful idea for a large skills library: recommend the skill, not just search it.

**Risks.** Prototype quality, OpenAI-only embeddings, in-memory state with a single-file snapshot does not scale, and it is a chat product rather than an agent memory layer.

**Verdict: ADOPT-IDEA** (count-triggered summarisation; explainable hybrid search; skill recommendation by intent).

---

## 16. siliconjungle/cabinet

| Field | Value |
|---|---|
| Stars / forks | 3 / 0 |
| Last push | 2022-04-14 |
| Licence | None stated |
| Description | "A key value store & subscriptions wrapping a json blob crdt (shelf)" |

**What it is / mechanism.** A key-value store with subscriptions layered over "shelf", a JSON-blob CRDT, with list CRDT and OT variants in-tree and Jest tests for the state-based shelf. It is local-first sync infrastructure: multiple writers can edit a JSON document offline and converge.

**Trait map.** Memory (only indirectly: shared state that survives offline edits).

**Quality evidence.** Dated 2022, three stars, no licence, minimal README. Part of the author's large CRDT body of work, which is serious, but this repo is an early piece of it.

**Transferable value.** Low for an LLM agent stack whose memory is single-writer files with a synthesis pass; CRDT convergence matters when several agents write the same memory concurrently, which is a real future problem for multi-agent setups but not solved by adopting a 2022 JavaScript prototype.

**Risks.** Abandoned, unlicensed, and would be a new storage substrate under memory, which is the highest-blast-radius place to experiment.

**Verdict: REFERENCE** (note for the multi-writer memory problem only).

---

## 17. siliconjungle/computational-markdown

| Field | Value |
|---|---|
| Stars / forks | 5 / 0 |
| Last push | 2023-03-15 |
| Licence | None stated |
| Description | "A way to add computation and user input to markdown." |

**What it is / mechanism.** A Next.js experiment (tree read: `core/code-execution.js`, components for a code editor and JSON viewer, a small hand-written parser/interpreter under `tiny-parser/`) that embeds computation and interactive inputs inside Markdown documents, so a document can compute rather than only describe.

**Trait map.** Creativity / execution (documents as runnable artefacts).

**Quality evidence.** 2023 prototype, five stars, no licence, game-related scaffolding mixed into `core/`, no tests visible in the tree.

**Transferable value.** The idea, live documents whose numbers are computed in place, is already realised more safely in the reference stack by generated artefacts and reports built from source data. Nothing here improves on that.

**Verdict: SKIP** (superseded idea, abandoned prototype).

---

## 18. siliconjungle/ink-knowledge (README-level inspection only)

| Field | Value |
|---|---|
| Stars / forks | 0 / 0 |
| Last push | 2026-10-17 |
| Licence | Not checked (README-level inspection only) |
| Description (API) | "Independently versioned proof packages and optimisation knowledge for Ink" |

**What it is / mechanism.** Content-addressed knowledge storage for the author's Ink language: canonical entries stored as `store/objects/<sha256>.json`, a rebuildable SQLite discovery index, and a strict separation of authority, stated in the README as "Storage never grants proof authority": the planner may search and select, but proof checking stays in an independently buildable semantic core, entries are explicit about what they do *not* certify, synthetic probe workloads are labelled as proposals rather than observed usage, and a phase with no admissible proposal retains the baseline.

**Trait map.** Conscientiousness (primary: storage, search and proof kept as separate authorities), memory (versioned knowledge packages).

**Quality evidence.** Zero stars, part of an actively developed (October 2026) personal language ecosystem, very dense and domain-specific README. Inspected at README level only, so no claim is made about the code.

**Transferable value.** The authority separation is a crisp statement of a principle the reference stack already follows (a memory entry or a search index is evidence to consult, never proof; verification happens in an independent check). The "entries state what they do not certify" habit is also worth copying into knowledge stores.

**Verdict: REFERENCE** (principle already embodied in the doctrine; no code relevance outside Ink).

---

## Cluster summary: ranking by transferable value

1. **Verification triad from the Hashgraph list: falsegreen-skill, done-gate, codex-context-guard.** The single highest-value vein in this cluster. Each attacks a different way an agent fools itself: tests that cannot fail, completion claims with no evidence in the turn, and requirements lost to compaction before the completion claim is judged. All three are mechanisms, not advice, and all three plug into an existing doctrine-plus-blockers regime.
2. **openai/mcp-extensions: the explicit vs background context split, plus typed form elicitation.** The best new interaction model here: continuously published structured "where the user is" context, kept separate from deliberately supplied context, and bounded typed questions instead of free-text guessing.
3. **hashgraph-online/awesome-ai-plugins: the scan gate.** A numeric threshold (75/100), a published rubric, SARIF output, and a trust penalty for projects that do not scan themselves, used as an adoption policy for a skills/connectors library. Also the best discovery index in the cluster (1,116 entries, machine-readable, updated the day of research).
4. **ejentum-mcp's procedure schema** (steps, failure pattern to refuse, falsification test, DAG topology) as an upgrade to plain prose skills. Idea only; the service is closed and paid.
5. **openai/plugins: marketplace manifest and plugin-eval.** A single ordered index with install/auth policy per entry, and the expectation that a bundle ships with fixtures and a metric pack.
6. **siliconjungle/ambient-ai-chat: count-triggered summarisation and explainable hybrid search.** Small, real code, two portable ideas for a memory system that currently summarises on a clock.
7. **siliconjungle's SpecServer pattern** (one declarative spec file per MCP server) and **llm-fact-log** as a documented negative result for triple-store memory.
8. **plastic-labs/codex-honcho**: confirms the reference stack's memory design and adds two details (local-first capture, branch-scoped partitions), but its hosted model is a worse trade than local files.
9. **Asdivyansh/Awesome-ChatGPT-Plugins**: useful as a capability taxonomy and a 4,338-entry census of what people connect assistants to; weakest evidence and highest lock-in in the cluster.
10. **cabinet, computational-markdown, mcp-package-readme, ink-knowledge**: reference or skip. Interesting, but either abandoned, domain-bound, or already superseded in this stack.

**Overall cluster character.** Platform repos and curated lists mostly deliver *distribution and packaging* mechanisms rather than new cognition. The cognition-level gains found here came from small, single-purpose community projects buried in a list, not from the platform bundles. Almost everything in the two awesome lists that looks like a capability is a hosted service behind ChatGPT or Codex; the transferable residue is packaging discipline, verification gates, context plumbing, and a handful of memory triggers.

## Coverage ledger

**Inspected (metadata + README + tree, plus named source files):**
- openai/plugins: metadata, README, full HEAD tree (62 plugin directories counted); plugin-creator SKILL.md and plugin-json spec read.
- openai/mcp-extensions: metadata, README, tree; `docs/spec.md` and `docs/patterns.md` read in full.
- hashgraph-online/awesome-ai-plugins: metadata, README, tree; `plugins.json` parsed and counted (1,116 entries); `SCANNER_GUIDE.md` read in full.
- Asdivyansh/Awesome-ChatGPT-Plugins: metadata, README, tree; category and data-file structure read.
- kuroudo-ai/done-gate, vinicq/falsegreen-skill, GreenLv/codex-context-guard, plastic-labs/codex-honcho, ejentum/ejentum-mcp: metadata and README for each (all five reached and read).
- siliconjungle/llm-fact-log: metadata, README, tree, `index.js` read in full.
- siliconjungle/fs-mcp: metadata, README, tree; `src/fs-spec.js` and `src/generic-spec-server.js` read.
- siliconjungle/mcp-template, siliconjungle/mcp-package-readme: metadata, README, tree (shared generic-spec-server core read via fs-mcp).
- siliconjungle/ambient-ai-chat: metadata, README, tree; `apps/server/src/search.ts` and `apps/server/src/state.ts` read.
- siliconjungle/cabinet: metadata, README, tree.
- siliconjungle/computational-markdown: metadata, README, tree.

**Inspected at README level only (labelled as such in its section):**
- siliconjungle/ink-knowledge: README read; licence, tree and code not checked.

**Enumerated but not individually inspected:**
- siliconjungle page 2: all 100 repositories listed via the API and screened by name, description, stars and push date. Flagged-relevant repos are the ones above; the remaining roughly 92 (CRDT experiments, Ink language and Inkwell/WebGPU repos, utilities, games, asset datasets) were screened out with reasons recorded in section 10 and were not opened.
- Entries inside the two awesome lists other than the five in sections 5 to 9: counted and keyword-mined from `plugins.json` and the READMEs, with notable ones named in section 3, but not opened individually. The instruction's cap of five proper inspections from the lists was observed.

**Unreachable / redirected:** none. Every repository named in the task returned live API metadata and a readable README on 2026-10-31. No redirects were encountered. Note that openai/plugins and openai/mcp-extensions have both changed meaning since their names were coined (Codex plugin bundles and ChatGPT MCP app extensions respectively, not the 2023 web-plugin system); that is a content change, not a redirect, and is flagged in their sections.
