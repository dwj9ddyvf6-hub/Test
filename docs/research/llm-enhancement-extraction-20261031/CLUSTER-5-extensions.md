# Cluster 5: ChatGPT Web Extensions and Apps

Date inspected: 2026-10-31 (live GitHub API metadata, raw READMEs, root git trees, and selected key files/docs via raw URLs only. No code installed, cloned-and-run, or executed.)

Baseline for transferability judgments: the target stack already has file-based memory with nightly synthesis, a skills library of SKILL.md playbooks, scheduled cron/hook proactivity, a strict engineering doctrine (scope-first, proof-before-green, gate-wired regression blockers), and a personal trading book with its own memory system. A mechanism only scores if it adds something that stack lacks, in a form that survives leaving the ChatGPT web UI.

Honest cluster answer up front: most of this cluster is ChatGPT-web chrome. The transferable residue is small but real: (1) multi-format conversation export as a memory-ingest contract, (2) prompt chains with templated variables as a lightweight precursor to skills/workflows, (3) search-result injection into the prompt as the original real-time grounding pattern, (4) selection-triggered micro-actions and conversation branching, and (5) one genuinely modern piece, codex-chatgpt-web, whose turn-scoped capability token, compaction checkpoint, and Zero Risk manual-send mode are agent-harness design patterns, not UI tricks. Everything tied to ChatGPT DOM selectors, sidebar folders inside chatgpt.com, or a specific vendor web session is SKIP for platform lock-in.

---

## 1. saeedezzati/superpower-chatgpt — Superpower ChatGPT

| Field | Value |
|---|---|
| Stars / forks | 1,707 / 277 |
| Last push | 2024-06-18 |
| License | None declared (no LICENSE in tree) |
| Archived | No |
| Default branch | main |
| Description | ChatGPT with folders, search, export, pinned messages, community prompts, incognito, language/tone |

**What it is:** A Chrome/Firefox extension that patches the ChatGPT web UI with the organization features OpenAI had not shipped at the time.

**Mechanism (from README + tree: `scripts/content/promptChain.js`, `promptLibrary.js`, `promptHistory.js`, `export.js`, `api.js`):**
- Folders with colors, drag-and-drop reorder, trash-drop delete, archived-chat view, full-text search with highlighting across chat history, pinned messages with a quick-nav sidebar.
- Auto Sync / Quick Sync: local copy of all chats (or last 100) kept on the user's machine; export chats/settings/shortcuts/folders in .txt/.json/.md.
- Prompt Chains: save an ordered series of prompts and run them one by one with a single click. This is sequential prompt chaining with no branching, no tool calls, and no result-dependent routing.
- Prompt templates with `{{double-curly}}` variables that prompt the user to fill values before submission; prompt history (every prompt ever typed, saved locally), favorites, `@`/`#` autocomplete menu for prompts and chains, community prompt library with voting/categories.
- Custom Instruction Profiles (multiple saved profiles, one-click switch), Auto Splitter (chunk long input and send sequentially, also used for auto-summarize), Smart Replace (phrase expansion while typing), tone/style/language selectors (~190 languages), model switcher mid-conversation.

**Trait map:** Memory (chat folders/search/pins/local sync), Execution (prompt chains, auto-splitter), Conscientiousness (organization), Intelligence (weak: community prompts).

**Quality evidence:** 1,707 stars shows real demand in 2023-24, but last push June 2024, no license (so code reuse is not legally clean), and the feature set has been progressively absorbed by native ChatGPT (folders/projects, search, custom instructions). Stale DOM-patching extensions break silently when ChatGPT ships UI changes.

**Transferable value:** Low-moderate, idea only. The target stack already exceeds folders/search/pins (file memory + memory_search + nightly synthesis) and exceeds prompt chains (skills + workflows with branching, tools, and verification). Two micro-ideas are worth naming: (a) `{{variable}}` fill-in templates are a good lightweight intake pattern for recurring user prompts, a step below a full SKILL.md; (b) multiple named Custom Instruction Profiles prefigure persona/mode profiles, which the target stack handles via standing context files. Neither needs this code.

**Risks:** Abandonment (16+ months stale), no license, ChatGPT-DOM lock-in, community-prompt supply chain (unvetted prompts injected into sessions), local chat sync is a privacy surface if mishandled.

**Verdict: SKIP (platform lock-in to ChatGPT web UI; mechanisms already superseded by skills/workflows and file memory; no license).** The prompt-chain and templated-prompt ideas are noted as REFERENCE-level concepts only, already implemented in stronger form.

---

## 2. pionxzh/chatgpt-exporter — ChatGPT Exporter

| Field | Value |
|---|---|
| Stars / forks | 2,849 / 273 |
| Last push | 2026-10-30 |
| License | MIT |
| Archived | No |
| Default branch | master |
| Description | Export and share your ChatGPT conversation history |

**What it is:** A Tampermonkey userscript (distributed via GreasyFork and as `dist/chatgpt.user.js`) that exports ChatGPT conversations out of the web UI.

**Mechanism (verified in tree, not just README):** Dedicated exporter modules under `src/exporter/`: `markdown.ts`, `html.ts` (+ `htmlTemplate.ts`), `json.ts`, `text.ts`, `image.ts` (screenshot/PNG), plus `meta.ts`. Supported formats per README: copy-as-text, PNG screenshot, Markdown, HTML, and JSON in three dialects: OpenAI official format, TavernAI/SillyTavern, and Ooba. Export All for bulk export. Supporting utils for citations, LaTeX, image files/cache, conversation list, and format tests (`tests/markdown-format.test.ts`, `tests/json-export.test.ts`, `tests/export-content.test.ts`). Notably the repo itself carries `.agents/skills/browser-test/SKILL.md`, i.e. it is maintained with agent skills.

**Trait map:** Memory (primary: durable, portable conversation records), Conscientiousness (faithful formatting, citations, LaTeX preservation), Execution (bulk export).

**Quality evidence:** Strongest maintenance signal in the early part of this cluster: pushed 2026-10-30 (yesterday relative to inspection), MIT, release-please automation, real format tests. 2,849 stars.

**Transferable value:** Moderate, and the cleanest ADOPT-IDEA in the cluster. The lesson is not "export ChatGPT chats" (the target agent's transcripts already live in its own store). The lesson is the export contract: one canonical conversation, multiple faithful renderings (Markdown for human/memory ingest, structured JSON for machine re-ingest, HTML/PNG for sharing), with citations and math preserved and format behavior pinned by tests. That is exactly the discipline a memory system needs when conversations become long-term memory inputs, and the multi-dialect JSON (official / Tavern / Ooba) is a reminder to export in the consumer's schema, not the producer's. Applied here: any future transcript-to-memory or transcript-to-archive exporter for the target stack should ship Markdown + a structured JSON in one pass, with format tests, rather than ad hoc copy-paste.

**Risks:** Userscript/Tampermonkey dependency and ChatGPT DOM/API lock-in for the capture half; the export half is portable. Low security risk (local export). No abandonment risk at present.

**Verdict: ADOPT-IDEA (multi-format, test-pinned conversation export contract: Markdown + structured JSON + share rendering, citations/LaTeX preserved). Not ADOPT-CODE: the capture layer is ChatGPT-specific and the target stack owns its transcripts natively.**

---

## 3. sailist/chatgpt-enhancement-extension — ChatGPT Enhancement Extension

| Field | Value |
|---|---|
| Stars / forks | 328 / 30 |
| Last push | 2023-04-19 |
| License | MIT |
| Archived | No (but effectively abandoned) |
| Default branch | master |
| Description | An all-in-one plugin to improve your ChatGPT experience |

**What it is:** An early (2023) all-in-one ChatGPT extension: prompt hints, PDF reading, Markdown conversion, export buttons, and cross-page prompting without an API key.

**Mechanism (from README + tree):**
- Prompt hint: type `/` in the input to get a prompt menu; Enter sends, Tab edits.
- PDF support: drag a PDF into the textarea and each page becomes a prompt, with extra instructions appended per page from a Regex Prompt Group: a rule set that matches page/text patterns and appends the corresponding prompt suffix. This is the one distinctive mechanism: regex-conditioned prompt augmentation over chunked document pages.
- Markdown conversion of dialogues; injected button group (copy/save/export); admin dashboard (options page managing prompt hints, regex groups, saved dialogue history).
- All-in-one / cross-page: select text on any page and re-prompt it into the one open ChatGPT page (keys `c` send, `x` menu); omnibox entry (`. ` prefix) to ask via the address bar.

**Trait map:** Intelligence (document chunk-and-prompt), Execution (cross-page selection prompting), Memory (weak: saved dialogue history in options).

**Quality evidence:** Weak. 328 stars, last push April 2023, ships a committed `dist.crx` (and a `.bak`), predates modern ChatGPT file upload, native PDF handling, and current extension APIs. Treat as a historical artifact.

**Transferable value:** One idea only. Page-chunking a PDF and appending pattern-matched instructions per chunk (Regex Prompt Group) is a crude ancestor of document-ingest pipelines: chunk, classify by pattern, attach the right instruction per chunk. The target stack's document handling and skills already do this more rigorously, and natively multimodal reading makes the page-as-prompt hack obsolete. The `/` prompt-hint menu is now a universal UI convention (slash commands), already present in the target environment.

**Risks:** Abandonment (2023), ChatGPT DOM lock-in, committed binary crx is an audit smell, no maintenance against current web APIs.

**Verdict: SKIP (abandoned 2023, platform lock-in). Historical REFERENCE only for regex-conditioned per-chunk prompt augmentation, already superseded.**

---

## 4. ChatGPTBox-dev/chatGPTBox — ChatGPTBox

| Field | Value |
|---|---|
| Stars / forks | 10,776 / 879 |
| Last push | 2026-10-27 |
| License | MIT |
| Archived | No |
| Default branch | master |
| Description | Integrating ChatGPT into your browser deeply |

**What it is:** The most mature general browser-integration extension in the cluster: summon an LLM on any page, summarize pages, run selection tools, embed answers beside search results and on sites like GitHub/YouTube/Reddit, and talk to many model backends through one UI.

**Mechanism (verified in tree):**
- Provider abstraction: `src/services/apis/` has separate adapters for ChatGPT Web, OpenAI API, Azure, Claude API/Web, Bing/Bard web, Moonshot, and a custom OpenAI-compatible API (`custom-api.mjs`, `openai-compatible-core.mjs`, `provider-registry.mjs`), with per-provider tests. LiteLLM/one-api/Ollama/OpenRouter can be fronted as a custom model. This is a real multi-provider registry, not a single-vendor wrapper.
- Anywhere invocation: Ctrl+B floating dialog, right-click page summarize (Alt+B), independent conversation page, mobile support.
- Selection tools: highlight text anywhere and run translate / summarize / polish / sentiment / paragraph-divide / code-explain / query as configurable micro-actions.
- Site adaptations: search engines plus Reddit, Quora, YouTube, GitHub, GitLab, StackOverflow, Zhihu, Bilibili, each toggleable, with config verification CI (`verify-search-engine-configs`, `verify-configs.yml`) and a coverage badge.
- Conversation branching: static cards / floating boxes support multi-branch conversations (fork a thread visually and pursue alternatives in parallel).
- Privacy posture stated and checkable: no data collection, manual activation by default, prompts/page content sent only when a feature is triggered.

**Trait map:** Execution (primary: LLM at the point of selection, anywhere), Real-time (page context summarization), Intelligence (multi-model access), Creativity (branching conversations).

**Quality evidence:** Strong: 10,776 stars, pushed 2026-10-27, MIT, unit tests per provider adapter, CI config verification. Actively maintained despite the legacy premise.

**Transferable value:** Moderate as ideas, none as code for this stack. Three patterns transfer conceptually: (1) Selection-triggered micro-actions: the smallest useful agent surface is "select X, run a named transformation" — the target stack expresses this as skills invoked on supplied text/files, which is more powerful but less frictionless; the friction lesson is real. (2) Conversation branching as a first-class object: fork an analysis into parallel alternatives and compare, which maps to subagent/workflow fan-out in the target stack (ALREADY-HAVE in stronger form). (3) Provider registry with per-adapter tests and config verification: a clean pattern for any multi-model routing, relevant if the stack ever abstracts model providers, and its test-per-adapter discipline matches the doctrine's blocker law. The browser-embedding itself does not transfer: the target agent is not a browser sidebar.

**Risks:** Browser-extension permission surface (page content to configured providers), web-session backends (ChatGPT/Claude/Bing web adapters) are ToS-fragile and break with vendor changes, platform lock-in to the browser as host. Maintenance is good, which lowers abandonment risk.

**Verdict: ALREADY-HAVE for branching (subagents/workflows) and provider abstraction in spirit; ADOPT-IDEA (selection-triggered named micro-actions as a low-friction invocation pattern) as a minor note. Overall REFERENCE. No code adoption: host is the browser, target host is an agent runtime.**

---

## 5. interstellard/chatgpt-advanced — WebChatGPT

| Field | Value |
|---|---|
| Stars / forks | 6,426 / 816 |
| Last push | 2024-08-13 |
| License | MIT |
| Archived | No |
| Default branch | main |
| Description | WebChatGPT: augments your ChatGPT prompts with web results |

**What it is:** The original "give ChatGPT web access" extension, from before ChatGPT had browsing. README itself states the repo stopped receiving updates after 2023-06-30 as the project moved toward a credential/server product; last push Aug 2024.

**Mechanism (from README FAQ + tree: `src/content-scripts/web_search.ts`, `src/content-scripts/api.ts`, `src/util/promptManager.ts`, `src/components/promptEditor.tsx`):**
- Two modes, both client-side (hence the access-to-all-websites permission): (1) web search: run the query against a search engine, fetch top results; (2) URL extraction: pull readable text from URLs named in the prompt.
- Retrieved text is injected into the prompt sent to ChatGPT, with controls surfaced in a toolbar/prompt editor (number of results, time ranges and similar parameters in the product's UI generation).
- The pattern in one line: retrieve, then prepend/attach the evidence to the user prompt so a frozen model answers from fresh sources.

**Trait map:** Real-time (primary, this is the canonical pre-native-browsing grounding mechanism), Intelligence (answers grounded in retrieved evidence rather than parametric memory).

**Quality evidence:** Historically important, 6,426 stars, but frozen: vendor-native browsing/search made the extension's core redundant, and the author publicly wound the repo down in 2023. DOM/search-scraping approaches are brittle.

**Transferable value:** The mechanism is fundamental and the target stack already lives it: browser.search / browser.open retrieval, grounding answers in fetched sources, and treating retrieved content as data not instructions. WebChatGPT is useful as the clean historical statement of retrieve-then-inject, including its failure mode worth remembering: everything retrieved lands in the prompt as undifferentiated text, which is precisely the prompt-injection surface modern stacks must fence (the target stack's external-content rules exist because of this pattern). No new capability to adopt.

**Risks:** Abandoned/frozen, all-websites permission, search scraping brittleness, unfiltered injection (by modern standards a security anti-pattern if copied naively).

**Verdict: ALREADY-HAVE (equivalent: the agent's native web search/fetch with external-content fencing). REFERENCE as the historical origin of retrieve-then-inject grounding.**

---

## 6. doggy8088/ChatGPTToolkitExtension — ChatGPT Toolkit Extension

| Field | Value |
|---|---|
| Stars / forks | 194 / 40 |
| Last push | 2026-10-21 |
| License | None declared |
| Archived | No |
| Default branch | main |
| Description (translated) | Improves ChatGPT, Gemini, Claude, Phind, Groq sites: auto-fill prompts from URL, prompt buttons after responses |

**What it is:** A small, actively maintained multi-site prompt-delivery extension (Traditional Chinese origin, localized en/ja/zh-TW).

**Mechanism (from README + tree: `CUSTOM_PROMPTS.js`, `link-builder.html`, `scripts/content.js`, `src/content/`, `src/background/`):**
- URL-as-prompt-carrier: open a chat site with `#autoSubmit=1&prompt=<text>` (or `autoSubmit=0` to prefill only) and the extension fills (and optionally submits) the prompt. Prompts become bookmarks, shareable links, and browser address-bar search shortcuts (e.g. keyword `g` + Tab).
- Prompt Link Builder: turn any prompt into a bookmark, a Markdown link, or an omnibox shortcut targeting ChatGPT, ChatGPT Images, Claude, Gemini, Groq, Perplexity, or a custom URL/GPT.
- Auto prompt buttons after each response (configurable common follow-ups, defined in CUSTOM_PROMPTS), double-click a sent prompt to edit it in place, markmap libraries bundled (mind-map rendering of responses is part of the toolkit's orbit via bundled markmap assets in tree).

**Trait map:** Execution (one-click/one-link task initiation), Initiation/proactivity (weak: suggested follow-up buttons after each response), Memory (prompts as bookmarks/links, a portable prompt library).

**Quality evidence:** Small (194 stars) but alive: pushed 2026-10-21, has CHANGELOG, publish workflow, TypeScript build. No license declared, which blocks code reuse.

**Transferable value:** One neat idea: a prompt (i.e. a task invocation) encoded as a portable, shareable URL/bookmark with explicit auto-submit vs prefill-only semantics. That is deep-linking for agent tasks: a link that opens the agent with the task prefilled, and a separate explicit flag for "run it" vs "let me review first". The prefill-vs-autosubmit distinction is a genuinely good safety affordance and maps directly onto approval-gated actions in the target stack. Follow-up prompt buttons are the consumer version of "suggest the next step", already present in the target agent's behavior. Scale and code do not transfer; the deep-link semantics do, as a minor idea.

**Risks:** No license, small maintainer base, depends on five-plus vendors' web UIs and URL/hash conventions, autoSubmit links are a social-engineering vector if a user clicks a crafted prompt link (prefill-only default would be safer; the tool does support it).

**Verdict: ADOPT-IDEA (minor: deep-link task invocation with explicit prefill vs auto-run semantics). Otherwise SKIP: no license, web-UI lock-in.**

---

## 7. lencx/Noi — Noi

| Field | Value |
|---|---|
| Stars / forks | 9,072 / 719 |
| Last push | 2026-08-21 |
| License | None declared in API metadata (no LICENSE at root in tree listing) |
| Archived | No |
| Default branch | main |
| Description | Less chaos. More flow. |

**What it is:** A desktop app (by the author of the popular ChatGPT desktop wrapper) that hosts many AI web services in one window with workspace organization. Current positioning per README: interaction-first workflow, multi-window parallel workspaces, session isolation, local-first data, prompt management, built-in terminal, and a `noi` CLI that tools like Claude Code / Codex / Gemini CLI can use to control it.

**Mechanism (from README + configs verified via raw URLs):**
- Curated service registry as data: `configs/noi_awesome.json` is a tree of folders (AI, Dev, Other, Session isolation) containing entries like ChatGPT, Claude, Gemini, Grok, each with url, favicon, `ask: true` flags; `configs/noi.conf.json` is a large declarative settings file (windows/tabs/PiP layout, history/prompt/ask-log caps such as max_history_search 1000, max_ask_archive 10000, and an extensive keyboard-shortcut map). The workspace is config, not code.
- Session isolation: separate sessions/partitions per service instance so contexts (accounts, projects) stay cleanly separated, including a dedicated "Session isolation" folder pattern in the default registry.
- Unified Ask: one input can address multiple AI services (`ask` views grouping ChatGPT/Claude/Gemini/Grok in an AI Playground view), prompt management for reuse/iteration, history and prompts stored locally.
- `noi` CLI: external agents/CLIs can drive the app, turning a human multi-AI inbox into a programmable surface.

**Trait map:** Execution (parallel workspaces, one ask to many models), Memory (local prompt/history management), Intelligence (multi-model comparison in one place), Conscientiousness (session isolation as context hygiene).

**Quality evidence:** 9,072 stars, pushed Aug 2026, active releases (v1.1.0 referenced). License not declared in metadata, so treat code as not reusable. It is a host shell for other vendors' web apps, with all the fragility that implies (webview breakage, vendor ToS on embedded sessions).

**Transferable value:** Two ideas, both already substantially present in the target stack: (1) Session isolation as an explicit, named pattern: separate clean contexts per project/account so memory does not bleed. The target stack does this with separate chats, goal workspaces, and people/group memory pages; Noi is a good consumer-grade proof that users feel the pain isolation solves. (2) Workspace-as-config: the entire service/folder/shortcut layout in declarative JSON files that can be diffed, versioned, and regenerated. That aligns with the target stack's file-based ethos. The multi-model Ask fan-out is ALREADY-HAVE via subagents on different tasks, though not as a single consumer window. No code or app adoption: the target agent should not be run inside a webview shell aggregating chat sites.

**Risks:** Platform lock-in to vendor web UIs inside webviews, session/cookie concentration (many AI accounts in one app profile is a high-value target), undeclared license, desktop-app attack surface.

**Verdict: REFERENCE (session isolation and workspace-as-config, both already embodied in the target stack in stronger form). SKIP the app itself.**

---

## 8. nextai-translator/nextai-translator — NextAI Translator

| Field | Value |
|---|---|
| Stars / forks | 25,023 / 1,851 |
| Last push | 2026-10-31 (same day as inspection) |
| License | AGPL-3.0 |
| Archived | No |
| Default branch | main |
| Description | Browser extension + cross-platform desktop app for translation based on ChatGPT API |

**What it is:** The largest repo in the cluster by stars: a selection/pop-up translator that grew into a multi-provider desktop + browser tool. Renamed from a ChatGPT-branded name after an OpenAI trademark warning (stated in README).

**Mechanism (from README + tree: `src/`, `e2e/` Playwright specs, `clip-extensions/` for PopClip/SnipDo):**
- Selection-triggered action modes: highlight text anywhere and run one of three fixed LLM operations: translate, polish, or summarize, across 55 languages, streaming, with customizable prompt text per operation.
- Multi-provider LLM backends (OpenAI, Azure OpenAI, MiniMax, and others, plus an OpenAI-compatible gateway), i.e. the same operation layer decoupled from the model vendor.
- Beyond text selection: screenshot translation, text-to-speech, vocabulary book with LLM-generated memory aids for saved words.
- Distribution breadth as a mechanism: browser extension, desktop app (Tauri-class cross-platform), and clip extensions that hook other selection tools (PopClip, SnipDo), all sharing the operation definitions.

**Trait map:** Execution (instant selection-to-result), Intelligence (language transformation quality), Creativity (weak: polishing).

**Quality evidence:** Excellent maintenance: 25,023 stars, pushed the day of inspection, Playwright e2e + unit-test CI, dependabot. AGPL-3.0 is the catch: copyleft makes code adoption into a non-AGPL stack a legal problem, so value here is ideas only.

**Transferable value:** Low for this stack. The durable idea is the fixed action-mode trio (translate / polish / summarize) bound to a selection: a tiny, predictable verb set the user can invoke without composing a prompt. That is the same micro-action pattern as ChatGPTBox's selection tools, and the target stack already covers all three verbs via skills/instructions on demand, plus native translation ability. The vocabulary book with generated memory aids is a nice learning-loop pattern (save item, generate mnemonic, review) but it serves language learning, not this user's agent traits. Nothing here enhances memory, proactivity, or reasoning for the target stack.

**Risks:** AGPL contamination if code were copied, API-key handling across many surfaces, provider-gateway promotion in README (a sponsored default suggestion) is a supply-chain nudge to ignore. No abandonment risk.

**Verdict: SKIP (a polished end-user translator; its verbs are already native to the agent, and AGPL blocks code reuse). REFERENCE only for the selection-bound fixed-verb pattern, duplicated by ChatGPTBox above.**

---

## 9. miuuyy/codex-chatgpt-web — Codex ChatGPT Web

| Field | Value |
|---|---|
| Stars / forks | 15,338 / 1,214 |
| Last push | 2026-10-30 |
| License | MIT |
| Archived | No |
| Default branch | main |
| Description | Use ChatGPT Web (including Pro) as a native model in Codex, with context, tools, streaming and images, without using Codex quota |

**What it is:** The outlier, and the only repo in the cluster that is agent infrastructure rather than ChatGPT UI polish. A launcher + loopback daemon that registers ChatGPT Web models (including Pro tiers) in Codex's native model picker, drives a signed-in ChatGPT session in an embedded Electron browser, and, in Full harness mode, gives the web model access to the local task's files, terminal, and tools through MCP. Extensive docs were read for this entry: `docs/architecture.md` and `docs/security-model.md`, plus the adapter tree.

**Mechanism (verified in docs + tree `src/adapters/chatgpt-web/`):**
- Responses-API bridge: Codex talks to a loopback daemon; the daemon forwards turns to a fresh ChatGPT conversation (Temporary Chat by default in browser-only mode), streaming back, with images and full context. Up to five task-bound browser tabs, each task/model/effort/compaction epoch leasing its own surface; a sixth concurrent turn fails explicitly rather than degrading.
- Turn-scoped capability token (the standout security pattern): for each turn the daemon mints a random token, embeds it in that one ChatGPT prompt, and the MCP connector must present it; the server claims an internal binding plus a request-scoped activity lease, dispatches immediately, and never exposes the internal handle to the model. MCP can invoke only tools advertised by the active outer Codex turn; a proxy enforces a bounded `wait_agent` polling contract and blocks recursive raw exec. Completion is gated by a two-phase broker fence that re-reads state and commits only if no tool invocation is in flight.
- Compaction as a transaction: files `compaction-handoff.ts`, `compaction-transaction.ts`, `compaction-continuation.ts`, `rolling-checkpoint.ts`. When context fills, the same web agent produces a one-shot structured checkpoint, the old surface closes, and the next epoch starts from the checkpoint; context-only continuations must bind the exact checkpoint + source instruction to the native thread/turn/model, and a checkpoint alone does not grant filesystem authority (authority is re-proven from the canonical local rollout: cwd, roots, sandbox policy).
- Zero Risk mode: no page automation at all. The human pastes and sends the prepared prompt manually, clicks Sent, and only then does the MCP connector act. Automation risk is traded for a human in the loop at the exact trust boundary.
- Identity discipline: the connector has an exact name (`Codex Native2`); the legacy `Codex Native` connector is never selected or refreshed as a fallback, upgrades invalidate model caches explicitly, grouped model efforts must have identical context/compaction budgets or catalog generation rejects the mismatch rather than silently shrinking a budget.
- It even ships a skill: `skills/pro-researcher/SKILL.md` (with an agents/openai.yaml), plus prompt-contract and compaction tests (`tests/prompt-contract.test.ts`, `tests/compaction-task-context.test.ts`, `tests/zero-risk-*.test.ts`).
- Stated trust model: repo content, tool output, websites, and prompt text are untrusted data; the browser profile lives in the OS user's private app-data, never in prompts or descriptors; tunnel key is file-referenced with user-only permissions, never in command arguments.

**Trait map:** Intelligence (routes a stronger/external model into an agent harness), Execution (full tool use via MCP), Memory (compaction checkpoints and rolling checkpoints as engineered context memory), Conscientiousness (capability scoping, explicit failure instead of silent fallback, budget-mismatch rejection), Real-time (streaming bridge).

**Quality evidence:** Strong and current: 15,338 stars in a short life, pushed 2026-10-30, MIT, CI + release workflows, SECURITY.md, TROUBLESHOOTING.md, and a test suite aimed at exactly the risky seams (prompt contract, compaction context, Zero Risk lifecycle, MCP observation). The docs are unusually honest about residual risks (loopback port has no independent bearer token; same-user processes can reach it; prompt injection in Full mode can invoke write/command tools).

**Transferable value:** Highest in the cluster, as design patterns, not as a product to run. Four patterns are directly relevant to any agent stack, including this one: (1) Turn-scoped capability tokens: authority minted per turn, bound to one prompt/turn, never reusable across turns, internal handles never model-visible. (2) Compaction checkpoints that carry context but not authority: a summary may continue a conversation, but filesystem/tool authority must be re-proven from the canonical record, never inherited from the summary. That is a precise, adoptable rule for any system with compaction/synthesis (the target stack's nightly memory synthesis is exactly such a surface: synthesis is memory, not authorization). (3) Zero Risk manual-send mode: for the highest-risk bridge, put the human's explicit send action at the boundary instead of automating around them, mirroring the target stack's draft-and-tap patterns. (4) No silent fallback identities/budgets: reject mismatches explicitly rather than degrading quietly, which is the doctrine's fail-closed stance stated as product behavior. Running the product itself is NOT recommended here: it exists to spend a ChatGPT subscription as a Codex model, depends on ChatGPT web DOM contracts and an OpenAI tunnel, and would add a browser-session theft surface for no capability the target stack lacks.

**Risks:** Prompt injection with real tool access in Full mode (author's own warning), ChatGPT session/profile theft value, ToS fragility of driving ChatGPT Web as an API, DOM-contract breakage, loopback-daemon local-process exposure, and rapid model-name churn in its catalog (the README's model lineup is time-sensitive marketing surface; the architecture is the durable part).

**Verdict: ADOPT-IDEA (four harness patterns: turn-scoped capability tokens; checkpoints carry context, never authority; human-send Zero Risk boundary for high-risk bridges; explicit rejection over silent fallback). REFERENCE for implementation. Do NOT adopt the product/code into this stack: ChatGPT-web session lock-in and session-theft surface.**

---

## Cluster Summary: Ranking by Transferable Value

| Rank | Repo | Verdict | Transferable core |
|---|---|---|---|
| 1 | miuuyy/codex-chatgpt-web | ADOPT-IDEA | Turn-scoped capability tokens; compaction checkpoints that never carry authority; Zero Risk human-send boundary; fail-closed identity/budget checks |
| 2 | pionxzh/chatgpt-exporter | ADOPT-IDEA | Multi-format, test-pinned conversation export contract (Markdown + structured JSON dialects + share rendering) for memory ingest |
| 3 | ChatGPTBox-dev/chatGPTBox | REFERENCE / ALREADY-HAVE | Selection micro-actions, conversation branching, per-adapter-tested provider registry |
| 4 | doggy8088/ChatGPTToolkitExtension | ADOPT-IDEA (minor) | Deep-link task invocation with prefill vs auto-run as separate explicit flags |
| 5 | lencx/Noi | REFERENCE | Session isolation as named context hygiene; workspace-as-declarative-config |
| 6 | saeedezzati/superpower-chatgpt | SKIP | Prompt chains and `{{var}}` templates, folders/search: all superseded by skills/workflows and file memory; stale, unlicensed |
| 7 | interstellard/chatgpt-advanced | ALREADY-HAVE | Retrieve-then-inject grounding; native in target stack, with injection fencing the original lacked |
| 8 | nextai-translator/nextai-translator | SKIP | Fixed selection verbs already native; AGPL blocks code reuse; end-user translator, not agent enhancement |
| 9 | sailist/chatgpt-enhancement-extension | SKIP | Abandoned 2023; regex per-chunk prompt augmentation is of historical interest only |

Cluster-level findings:

1. The ChatGPT-web extension era produced organization and export layers for a host that had none. An agent that owns its files, memory, and transcripts starts past all of it. Folders, pins, sidebar search, and prompt libraries recur in four of nine repos and transfer least, because they are UI furniture for someone else's app.
2. The mechanisms that do transfer are all boundary mechanisms, not UI mechanisms: how conversations leave a system faithfully (exporter), how authority enters a turn and expires (codex-chatgpt-web), how a task arrives prefilled but not auto-run (Toolkit), and how retrieved text enters a prompt (WebChatGPT, whose naive version is now a security lesson).
3. Prompt chaining appears only in its weakest form (Superpower's linear chains, sailist's regex suffixes). Nothing in this cluster competes with SKILL.md playbooks or workflows; the cluster confirms, rather than fills, that gap.
4. Maintenance split is stark: exporter, ChatGPTBox, Toolkit, translator, and codex-chatgpt-web were all pushed within days of inspection (Oct 2026); Superpower (2024), WebChatGPT (2024, self-declared frozen 2023), and sailist (2023) are historical. Noi sits between (Aug 2026).
5. Licensing split matters for any future code interest: MIT for exporter, ChatGPTBox, WebChatGPT, sailist, codex-chatgpt-web; AGPL for the translator (idea-only); no license declared for Superpower, Toolkit, and Noi (idea-only by default).

## Coverage Ledger

| Repo | Status | Evidence |
|---|---|---|
| saeedezzati/superpower-chatgpt | Inspected | API metadata, README (raw, main), root tree + content scripts listing |
| pionxzh/chatgpt-exporter | Inspected | API metadata, README (raw, master), root tree + `src/exporter/` modules and tests listing |
| sailist/chatgpt-enhancement-extension | Inspected | API metadata, README (raw, master), root tree |
| ChatGPTBox-dev/chatGPTBox | Inspected | API metadata, README (raw, master), root tree + `src/services/apis/` adapters and tests listing |
| interstellard/chatgpt-advanced | Inspected | API metadata, README incl. FAQ (raw, main), root tree + content-scripts listing |
| doggy8088/ChatGPTToolkitExtension | Inspected | API metadata, README (raw, main, bilingual), root tree |
| lencx/Noi | Inspected | API metadata, README (raw, main), root tree, `configs/noi.conf.json` and `configs/noi_awesome.json` via raw URLs |
| nextai-translator/nextai-translator | Inspected | API metadata, README (raw, main), root tree incl. e2e/clip-extensions |
| miuuyy/codex-chatgpt-web | Inspected (deepest) | API metadata, README (raw, main), root tree + adapter listing, `docs/architecture.md` and `docs/security-model.md` via raw URLs |

Unreachable: none. Redirected/renamed: none among the nine (all resolved under the given owner/name). Note: nextai-translator's README states the project itself was renamed after an OpenAI trademark warning; the GitHub path given is current. WebChatGPT's README states its repo stopped receiving feature updates after 2023-06-30; recorded as frozen, not unreachable. No repo was installed, cloned, or executed; all reading was via api.github.com and raw.githubusercontent.com.
