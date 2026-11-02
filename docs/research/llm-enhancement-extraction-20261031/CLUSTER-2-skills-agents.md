# Cluster 2: Skills and Agent Systems

Deep inspection date: 2026-10-31. Method: live GitHub API metadata (`api.github.com/repos/<owner>/<repo>`), README via `raw.githubusercontent.com`, git trees via API (`git/trees/HEAD?recursive=0/1`), and targeted reads of load-bearing `SKILL.md` / reference files. No repo code was installed, cloned-and-run, or executed. Judgments below are from the actual files, not README marketing alone.

Baseline stack used for every transfer judgment (the stack this cluster would have to improve):

- File-based memory with nightly synthesis (curated long-term file, daily notes, people/group pages, derived alignment synthesis).
- A skills library of `SKILL.md` playbooks (system skills in `/opt/muse/skills/`, custom skills in `~/workspace/custom-skills/`), with skill search and connector docs.
- Scheduled cron and hook proactivity (recurring checks, inspections, event-driven hooks).
- A strict engineering doctrine (InfinityBlade): SCOPE first, minimum sufficient change at the source, proof before green from the final artifact, bug log plus gate-wired regression blockers for everything, route failure is not impossibility.
- A personal trading book / desk with its own memory, ledger, and grading system.

Trait vocabulary used throughout: memory, initiation / proactivity, creativity, abstract thinking, conscientiousness, execution, intelligence, real-time.

---

## 1. obra/superpowers

### Metadata

| Field | Value (live API, 2026-10-31) |
|---|---|
| Full name | `obra/superpowers` |
| Description | "An agentic skills framework & software development methodology that works." |
| Stars | 309,852 |
| Forks | 27,560 |
| Created | 2025-10-09 |
| Last push | 2026-10-29T23:35:34Z |
| Archived | No |
| License | MIT |
| Default branch | `main` |
| Open issues | 375 |

### What it is

A complete software-development methodology packaged as 15 composable, auto-triggering skills plus a `SessionStart` bootstrap hook, ported to roughly 17 harnesses (Claude Code, Codex, Cursor, Gemini CLI, Copilot CLI, OpenCode, Pi, Hermes, Muse, and others, each with its own plugin manifest in the same repo). Verified from the tree: exactly 15 skill directories under `skills/`, 300 total files, per-harness plugin folders (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.muse-plugin/`, etc.), `hooks/hooks.json` + `hooks/session-start`, and a `docs/superpowers/specs/` folder showing the project dogfoods its own spec-first process.

The 15 skills: `brainstorming`, `using-git-worktrees`, `writing-plans`, `subagent-driven-development`, `executing-plans`, `dispatching-parallel-agents`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `requesting-code-review`, `receiving-code-review`, `finishing-a-development-branch`, `diagnosing-superpowers`, `writing-skills`, `using-superpowers`.

### Mechanism in plain terms

1. **Bootstrap compulsion.** `using-superpowers` is injected at session start. Its rule, read verbatim from the file: if there is even a 1% chance a skill applies, the agent MUST invoke it before any response, including clarifying questions. It ships a "Red Flags" rationalization table ("This is just a simple question", "I remember this skill", "I'll just do this one thing first") that names the exact thoughts an agent uses to skip the process, and rebuts each one. Process skills (brainstorming, systematic-debugging) fire before implementation skills.
2. **A gated pipeline, not advice.** brainstorming (tease out intent, play it back in digestible chunks, get sign-off) -> worktree isolation with a clean test baseline -> `writing-plans` (bite-sized 2 to 5 minute tasks with exact file paths, complete code, verification steps) -> execution, either fresh-subagent-per-task with a two-stage review after each task (spec compliance, then code quality) or inline execution with one final whole-branch review -> TDD enforced inside implementation -> code review between tasks, critical issues block -> branch finishing with test verification and explicit merge / PR / keep / discard options.
3. **TDD as deletion threat.** `test-driven-development` enforces RED-GREEN-REFACTOR and, per the README summary, deletes code written before its test. This is conscientiousness made mechanical rather than exhortatory.
4. **Verification gate.** `verification-before-completion` states an "Iron Law": NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE. It defines a 5-step gate (identify the proving command, run it fresh and full, read output and exit code, verify, only then claim), a table of what each claim actually requires (tests pass requires test output with 0 failures, not a previous run; agent completed requires a VCS diff, not the agent's report), and its own rationalization-prevention table.
5. **Skills tested like code.** `writing-skills` is the most original file in the repo. Its thesis: "Writing skills IS Test-Driven Development applied to process documentation." A skill is only written after running pressure scenarios with subagents WITHOUT the skill and documenting the exact rationalizations the agent used to violate the rule (RED), then writing the minimal skill that addresses those specific violations (GREEN), then finding new rationalizations and plugging them (REFACTOR). It also has a sharp authoring rule: a skill's `description` must state only triggering conditions ("Use when...") and must never summarize the workflow, because an agent that reads a workflow summary in the description follows the summary instead of reading the skill.
6. **Self-diagnosis.** `diagnosing-superpowers` lets a user ask "figure out what went wrong in this session" (or name a past session id); the skill reads the transcript, reports what happened with line-level evidence across cost/time, plan adherence, quality evidence, and repeated work, and can package a scrubbed bundle for a bug report.
7. Small telemetry caveat, disclosed in the README itself: the optional brainstorming visual companion loads a logo from the vendor site carrying the Superpowers version (no project, prompt, or agent details, per the README), disableable via `SUPERpowers_DISABLE_TELEMETRY` / standard telemetry env vars.

### Trait map

| Trait | How |
|---|---|
| Conscientiousness | Primary. Verification Iron Law, TDD deletion, review gates, rationalization tables. |
| Execution | Primary. Plan granularity (2 to 5 min tasks with exact paths), subagent-per-task dispatch, worktree isolation. |
| Intelligence | Secondary. Brainstorming-before-building and systematic 4-phase debugging replace guess-first behavior. |
| Abstract thinking | Secondary. Spec/design documents played back in chunks before any plan exists. |
| Initiation / proactivity | Narrow: skills auto-trigger without being asked, but only inside a user-started coding session. No background or scheduled initiation. |
| Memory | Weak by design. Plans and specs are files, but there is no cross-session memory system, no synthesis, no learned preferences. |
| Creativity | Brainstorming skill only; structured divergence before convergence. |
| Real-time | None. |

### Quality evidence

- Scale and recency are exceptional on the retrieved numbers: 309,852 stars, 27,560 forks, created 2025-10-09, pushed 2026-10-29 (2 days before inspection), not archived, MIT.
- Maintenance signals in the tree itself: dated design specs through 2026-10-06, a dedicated eval harness referenced for skill-behavior tests (`superpowers-evals`, "drill"), plugin-infrastructure tests, and a strict contribution rule (no new skills generally accepted; updates must work across all supported harnesses; skill changes must follow `writing-skills`).
- Risk to the numbers: star count alone does not prove per-skill quality, and 375 open issues shows real surface area. The mechanism files read for this inspection (using-superpowers, verification-before-completion, writing-skills) are, however, substantively written, internally consistent, and clearly iterated against real agent failure modes, which is stronger evidence than the star count.

### Transferable value for the baseline stack

**Already covered, do not duplicate:** The pipeline's core (spec first, plan, TDD, verify before claiming done, review delegated work against the artifact) is already law in the baseline doctrine, and in several places the doctrine is stricter: InfinityBlade requires proof from the FINAL artifact, gate-wired regression blockers for every fix, and a bug log. Installing Superpowers wholesale would create a second, competing source of truth for the same behaviors, which the doctrine explicitly forbids ("never create a second source of truth to work around the first"). The baseline also already has subagent/workflow dispatch, worktrees-equivalent isolation via workflow runs, and a skills library with the same `SKILL.md` format.

**Genuinely additive, three items:**

1. **TDD-for-skills (`writing-skills`).** The baseline creates skills from recurring work but does not require a failing-first pressure test of the skill itself. Adopting the method (baseline scenario without the skill, record the exact rationalization, write the minimal skill against it, re-test, plug loopholes) would materially raise skill reliability. This is a method adoption, not a code adoption.
2. **Rationalization tables as a format.** Both `using-superpowers` and `verification-before-completion` enumerate the agent's own likely excuses in a two-column Thought / Reality table. The baseline doctrine states rules; it does not systematically pre-rebut the specific self-talk that bypasses them. Adding a rationalization table to the highest-stakes existing playbooks (proof-before-green, save/read-back verification, delegated-handback verification) is cheap and directly targets observed failure modes.
3. **Session self-diagnosis (`diagnosing-superpowers`).** A standing "what went wrong in that session, with line-level transcript evidence, across cost / plan adherence / quality evidence / repeated work" diagnostic is not a named baseline capability. The baseline learns from failures case by case; this packages it as a repeatable skill with fixed lenses. Worth building natively in the baseline's own terms rather than importing.

Also noted and already matched: the `description`-must-not-summarize-the-workflow authoring rule is a useful lint for the baseline's existing skill descriptions, checkable in one pass.

### Risks

- **Doctrine collision (main risk).** Two mandatory process systems giving orders in the same session will conflict on edge cases (for example, Superpowers' "invoke a skill before ANY response including clarifying questions" vs the baseline's scope/authority boundaries). Selective idea adoption avoids this; wholesale install does not.
- **Coding-only scope.** Nothing here helps the personal, scheduling, memory, or trading sides of the baseline stack.
- **Telemetry.** Minor, disclosed, disableable; noted for completeness.
- **Abandonment risk:** Low on current evidence (active push, multi-harness maintenance burden being visibly carried).
- **Security risk:** Low to moderate. Skills are markdown plus a small brainstorming server script and shell hook scripts; the hook runs at session start, so any adoption must be by reading, not by blind plugin install.

### Verdict

**ADOPT-IDEA** (selective, three items: TDD-for-skills method, rationalization tables in high-stakes playbooks, a native session-diagnosis skill). Do NOT adopt the code/framework wholesale: its core pipeline is ALREADY-HAVE via InfinityBlade plus the existing skills library, and a parallel mandatory methodology would violate the single-source-of-truth rule.

---

## 2. Wangnov/chatgpt-skill

### Metadata

| Field | Value (live API, 2026-10-31) |
|---|---|
| Full name | `Wangnov/chatgpt-skill` |
| Description | Skill for controlling ChatGPT with Claude Code / Codex (bilingual, Chinese first) |
| Stars | 7 |
| Forks | 0 |
| Created | 2026-05-25 |
| Last push | 2026-06-10T16:15:49Z |
| Archived | No |
| License | None returned by the API (`license: null`); README badges link to a LICENSE file. Treat as unlicensed until verified in-repo. |
| Default branch | `main` |
| Open issues | 0 |

### What it is

A "manual-style" skill pair, not a CLI or wrapper: two markdown handbooks that teach a coding agent (Claude Code or Codex) how to operate the user's already-logged-in ChatGPT web session through a browser bridge, so the agent can delegate questions, Deep Research, file/app queries, and conversation management to a ChatGPT subscription without any API key, cookie copying, or session storage. Verified from the tree: `claude-chatgpt-skill/SKILL.md` + references + examples, and a parallel `codex-chatgpt-skill/` variant, plus a heartbeat shell script. Platform badge: macOS. Hosts: Claude Code (via the `claude-in-chrome` MCP) and Codex (via the Codex Chrome Extension).

### Mechanism in plain terms

1. **Reuse, never re-authenticate.** The agent reuses the user's existing Chrome tab/session. Hard rules in the SKILL.md: no independent browser profile, no touching cookies/session/API keys, never click OAuth consent on the user's behalf, destructive ChatGPT actions (delete, clear Memory) require verbal user confirmation.
2. **Vision-over-selectors doctrine.** Deliberately no DOM selectors, no state machine, no coordinates. The agent reads the page (`read_page` / `get_page_text`), judges by visible text and ARIA labels, and acts. The stated rationale is resilience to ChatGPT UI drift, at the cost of reliability on any given day.
3. **The watcher pattern (the repo's one real invention).** Long ChatGPT generations (Pro measured up to 21 minutes, Deep Research up to hours) must not block the main agent. After submitting, the main agent spawns a cheap background watcher subagent (specified as Haiku, `run_in_background: true`) whose entire job is a polling loop: fetch full page text, scan from the END upward for completion signals (the footer disclaimer plus a past-tense "thought for Xm Ys" marker plus expected content keywords), scan for in-progress signals, and, with higher priority, scan for needs-user-input signals (a clarifying question, an app authorization prompt, login wall, rate limit, CAPTCHA, truncated-output "continue" button). The main model stays completely silent (the README claims 0 interruptions of the main Sonnet session during a 21-minute Pro task, watcher cost about 86k Haiku tokens) and only speaks when the watcher returns the full result. The Codex variant substitutes a heartbeat/automation poll with a pull fallback.
4. **Model waiting matrix.** Documented expected waits per tier: Instant under 30s, Thinking 1 to 3 min, Pro 5 to 10 min (21 min max observed), Deep Research minutes to hours, each with a different waiting strategy. If the requested model is not selectable, the skill forbids silently substituting another model; it must report the actually visible options.
5. **Three-tier result capture.** Ordinary replies via page-text to Markdown; Deep Research / Canvas artifacts via the artifact's own export-to-Markdown; images via share-then-download.
6. **Full management surface.** Conversation (delete/archive/share/pin/move to project), project (create/instructions/knowledge base/delete), Memory, library, and shared-link revocation, each annotated with GUI pitfalls (for example, the reliable in-project signal is the composer placeholder showing the project name, not the sidebar state).
7. **Honest limitation, documented in the skill itself:** file upload is permanently unavailable from Claude Code because the underlying `file_upload` validation requires a session id with a `local_` prefix that only the desktop cowork mode has. The skill documents this root cause instead of letting the agent retry blindly.

### Trait map

| Trait | How |
|---|---|
| Execution | Primary. Delegation of a second model's labor through a GUI, end to end, including capture and filing. |
| Real-time | Partial. Live operation of a live web product; waiting strategies are the core problem it solves. |
| Initiation / proactivity | The watcher/heartbeat lets long external work proceed without babysitting, a proactivity enabler, though the initial delegation is user-prompted. |
| Intelligence | Indirect: access to a different model family's Pro/Thinking/Deep Research as a second opinion. |
| Conscientiousness | Good safety rules (no silent model substitution, no OAuth on behalf, confirmation for destructive ops). |
| Memory, creativity, abstract thinking | No system of its own; it can read/clear the OTHER product's memory, which is management, not memory enhancement. |

### Quality evidence

- Very small and quiet: 7 stars, 0 forks, last push 2026-06-10 (about 4.5 months before inspection), single-author appearance, no license confirmed via API. Version badge claims v0.8.0.
- Counterweight: the files themselves are unusually well-observed. The watcher reference, the completion-signal hierarchy, the upload root-cause write-up, and the pitfall annotations read like hard-won operational notes from real runs, with measured numbers. This is a high-craft, low-adoption artifact.
- The mechanism is inherently perishable: it depends on ChatGPT web UI text (including a specific disclaimer string as the completion oracle), a specific MCP bridge, and subscription entitlements, all of which can change without notice.

### Transferable value for the baseline stack

The baseline stack already has the important equivalents and better ones: a genuine peer relationship with a ChatGPT instance through other channels, background subagents and durable workflows for long work (workflows survive daemon restarts, which a browser watcher does not), and browser tooling of its own. Delegating through a consumer ChatGPT web UI would be a downgrade in reliability and auditability for work the baseline already routes directly, and it is macOS/Chrome-bridge specific while the baseline's browser is its own Chromium.

One pattern is worth keeping, and the baseline mostly has it in spirit: **delegate-and-watch with a cheap watcher and a strict completion oracle.** The concrete refinements this repo adds are (a) defining completion by multiple end-of-output signals plus expected-content keywords rather than "the page stopped changing", (b) giving needs-human-input detection priority over still-generating detection in every poll, and (c) a costed example of keeping the expensive main model entirely out of the waiting loop. If the baseline ever needs to babysit a long external web generation, those three rules are the right shape. As a pattern note it is a paragraph, not an adoption.

Nothing here touches memory, the trading book, scheduling, or the doctrine.

### Risks

- **Platform lock-in (highest in this cluster).** Entirely bound to ChatGPT web, one vendor's UI strings, one browser bridge per host, and a paid subscription's model names that the README itself notes drift.
- **Fragility / abandonment.** 7 stars, no push in 4.5 months, UI-oracle design. Any ChatGPT UI change can break completion detection silently (the worst failure: reporting a truncated answer as complete, mitigated but not eliminated by its keyword checks).
- **Security / account risk.** An agent operating a logged-in consumer account, managing its Memory and deleting conversations, is a large blast radius for a markdown handbook with no code review surface. Its own safety rules are good, but they are prompt-level, probabilistic guards. Automating a personal ChatGPT account also carries ordinary account-risk if usage patterns look automated.
- **License uncertainty.** API reports no license; reuse rights are unclear.

### Verdict

**REFERENCE.** Keep for the watcher/completion-oracle pattern and as a pitfall catalogue if ChatGPT-web delegation is ever needed. Do not adopt: small, stale, unlicensed-per-API, macOS-specific, and the baseline already delegates and background-waits through stronger native machinery.

---

## 3. findscripter/everything-skills

### Metadata

| Field | Value (live API, 2026-10-31) |
|---|---|
| Full name | `findscripter/everything-skills` |
| Description | "A curated, cross-referenced encyclopedia of 1100+ open-source agent skills (native languages kept) and 1600+ indexed skill repos. Install as a Claude Code marketplace plugin." |
| Stars | 6 |
| Forks | 2 |
| Created | 2026-06-02 |
| Last push | 2026-10-31T03:56:55Z (same day as inspection) |
| Archived | No |
| License | "Other" (NOASSERTION). Per-file reality is mixed: original entries default to CC-BY-4.0 per its SCHEMA; curated entries keep their upstream licenses. |
| Default branch | `main` |
| Open issues | 0 |

### What it is

Not a skill but a skill encyclopedia and discovery layer: 1,115 bundled `SKILL.md` files (counted from the recursive tree) organized into 11 volumes by domain (00-meta through 10-platform), plus an index of 1,600+ external skill repositories that are summarized but NOT copied in. It installs as a Claude Code marketplace plugin by volume (for example `02-engineering@everything-skills`), and ships generated navigation artifacts: a catalog, a tag index, a knowledge graph (`INDEX/graph.md` / `graph.json`, README claims 6,787 relation edges), a `search.json`, a `quality.json`, and a zero-dependency local search CLI (`npm run skill -- search / list / why / repo / eval`).

### Mechanism in plain terms

The mechanism is the schema, read from `SCHEMA.md`, not the volume of content:

1. **Structured discovery frontmatter.** Every skill's YAML frontmatter is the single source for all generated indexes. Required: `name` (equals folder), `title`, `description`, `domain`, `status` (draft/stable/deprecated), `agents` (controlled vocabulary of compatible harnesses). The `description` must follow a structured template: when to use it (scenario), what it does (action + product), what it is NOT for (negative boundary), and explicit trigger words, all in one line, because the agent matches on this field.
2. **A typed relationship graph.** Four distinct edge types in frontmatter: `requires` (prerequisites), `related` (see-also), `combines_with` (composes into a larger workflow), `supersedes` (paired with deprecation + a mandatory reason for orphans). The README's starter bundles are just paths through this graph (for example onboarding -> monorepo navigation -> spec workflow).
3. **Provenance as a build gate.** `data/skill-provenance.json` records every skill's path, local SHA-256, original-vs-curated type, and source declaration; curated entries must carry `source` and `source_license`, and the generator hard-errors on proprietary / source-available / unlicensed upstream content. Resource files carry pinned SHA-256 and fixed source URLs, checked read-only before any build writes anything; a damaged or missing manifest must not be silently rebuilt to hide the problem. Historical entries whose original revision was never recorded stay explicitly `unrecorded` with a null SHA rather than being backfilled with today's HEAD.
4. **Quality facets kept separate from content.** `INDEX/quality.json` is generated from a separate overrides file with controlled vocabularies: review_status (unreviewed/reviewed/needs-review/archived), source_freshness, license_confidence, capabilities (for example read-only), security_risk, and runtime dependencies. Missing evidence defaults conservatively, and `unknown/unreviewed` explicitly means "no claim established", not "probably fine".
5. **Retrieval evaluated, honestly scoped.** The search CLI's `eval` command runs a checked-in task set and the README states plainly that the score measures retrieval coverage on those examples, not runtime or security certification.
6. **Native languages kept.** Skills stay in their original language (much of the meta volume is Chinese with English trigger aliases), rather than being machine-translated.

Content spot-checks (00-meta volume): several entries are genuinely meta-cognitive and well-specified, including `agent-self-reflection` (five-dimension step-back review triggered by "zoom out / are we overthinking this"), `filesystem-context-offload` (write large outputs to files, keep pointers in context, recall by grep/line-range), `context-budget-audit` (inventory skills/agents/MCP/rules by token cost, rank cuts), `closed-loop-delivery` (acceptance-criteria-driven delivery with runtime evidence), `idea-darwin-evolution` (score / deepen / cross-breed / mutate ideas over rounds with lineage cards), and `parallel-agent-dispatch` (one subagent per independent failure domain, then conflict-check and full verification).

### Trait map

| Trait | How |
|---|---|
| Intelligence | Primary, as breadth: 1,115 task playbooks across engineering, documents, data, AI, business, creative, productivity, security, and verticals. |
| Abstract thinking / creativity | The 00-meta volume specifically: first-principles auditing, premortem, adversarial mentoring, decision frameworks, idea evolution. |
| Memory | Not memory of the user; it is external procedural memory (a library), plus a provenance/freshness memory ABOUT the library. |
| Execution | Via composition: `requires`/`combines_with` paths turn single skills into workflows. |
| Conscientiousness | In its governance layer: provenance gates, license hard-errors, conservative quality defaults. The skills themselves vary. |
| Initiation, real-time | None. It is a static, if frequently regenerated, library. |

### Quality evidence

- Actively maintained at the index level: pushed the same day as inspection, generated artifacts regenerated by a GitHub workflow (`index.yml`).
- Adoption is minimal (6 stars, 2 forks), the repo is 5 months old, and per-skill quality is necessarily uneven at 1,115 entries: the repo's own quality system marks much as unreviewed, which is honest but means the catalog cannot be trusted wholesale. Many entries are curated from third parties (visible `source` / `source_license` fields, for example MIT skills sourced from other collections).
- The governance machinery (schema validation, provenance checks, license gating) is real and enforced by its build scripts per SCHEMA.md, which distinguishes it from a bare awesome-list. That machinery, not the content count, is the quality signal.

### Transferable value for the baseline stack

**The content: low direct value.** The baseline already has a curated skills library tuned to its user, plus skill search across a large catalog. Bulk-importing 1,115 third-party playbooks of uneven review status would dilute trigger precision, inflate context/discovery noise, and import unknown-quality instructions, the exact failure its own `context-budget-audit` skill warns about. Individual meta skills (self-reflection, context-budget-audit) are worth reading as references when building native equivalents, not importing.

**The schema: genuinely additive, three ideas.**

1. **Typed skill relationships.** The baseline's skills are a flat searchable list. Adding `requires` / `related` / `combines_with` / `supersedes` (+ deprecation reason) to skill frontmatter would let the agent compose workflows deliberately and retire skills cleanly instead of accumulating them. This is the single most portable idea in this repo.
2. **Quality facets as separate, conservative metadata.** A per-skill record of review status, freshness, license confidence, capabilities, and security risk, with "unreviewed" as the honest default, maps directly onto the baseline's proof-before-green culture and would make skill search results self-qualifying.
3. **Negative-boundary descriptions.** Requiring every skill description to state what it is NOT for, alongside triggers, is a small authoring rule that reduces false triggering. It pairs naturally with Superpowers' "description states triggers, not workflow" rule (Cluster repo 1): together they fully specify a better description standard than either alone.

Its provenance discipline (never backfill an unrecorded origin with today's HEAD; a broken manifest is a stop, not a silent rebuild) is already baseline doctrine in other domains and needs no adoption, but the convergence is noted as validation.

### Risks

- **Supply-chain / instruction risk (main risk).** 1,115 third-party-authored instruction files are 1,115 prompt-injection and bad-practice surfaces. Its license gate checks licensing, not behavior. Any use must be per-skill reading, never bulk install.
- **Licensing heterogeneity.** "Other / NOASSERTION" at repo level, CC-BY-4.0 defaults, and per-entry upstream licenses mean attribution and reuse terms vary per file.
- **Hype-vs-substance gap.** "Encyclopedia of everything" framing with 6 stars; the durable value is the index machinery, not encyclopedic coverage.
- **Abandonment risk:** Moderate. Same-day pushes show current life, but a one-maintainer index of 1,600+ external repos decays fast if regeneration stops; the bundled snapshot would remain readable regardless.
- **Platform:** Claude Code marketplace-first, though plain `SKILL.md` folders plus AGENTS/GEMINI/CLAUDE entry files make it readable by other harnesses, including this one.

### Verdict

**ADOPT-IDEA** (schema only: typed skill relationships, separate conservative quality facets, negative-boundary descriptions). The content library itself is **REFERENCE**: browse it when a new skill is needed, read any candidate in full, never bulk-install.

---

## 4. affaan-m/ECC

### Metadata

| Field | Value (live API, 2026-10-31) |
|---|---|
| Full name | `affaan-m/ECC` |
| Description | "The agent harness performance optimization system. Skills, instincts, memory, security, and research-first development for Claude Code, Codex, Opencode, Cursor and beyond." |
| Stars | 293,818 |
| Forks | 43,484 |
| Created | 2026-01-18 |
| Last push | 2026-10-30T03:06:42Z |
| Archived | No |
| License | MIT (repo); a hosted Pro tier and GitHub App exist alongside the free OSS core |
| Default branch | `main` |
| Open issues | 191 |

### What it is

The largest system in this cluster by an order of magnitude: a cross-harness "agent harness operating system" of, per its README's annotated catalog and confirmed in scale by the recursive tree (6,449 files), 71 specialized subagent definitions, 300+ skills in the catalog narrative (1,068 `SKILL.md` files counted in the tree, counting per-harness copies under `.agents/skills/` and other adapter trees), 98 slash-command shims, language rule packs, runtime hooks, install/repair/sync scripts, and adapters for a dozen-plus harnesses. Root files are declared the single source of truth; platform adapters package the same workflows rather than forking them. It also ships three longform guides (shortform, longform, security) and two companion products: AgentShield (config security scanner, npm) and a Memory Vault runtime (npm `ecc-universal`).

### Mechanism in plain terms

Five mechanisms matter; the rest is a large, competent skills/agents catalog of the now-standard kind.

1. **Instincts: atomic, confidence-scored, project-scoped learning (`continuous-learning-v2`).** This is the repo's most original mechanism, read from its SKILL.md. Hooks on every tool use (PreToolUse/PostToolUse, claimed 100% capture vs v1's end-of-session Stop hook) record prompts, tool calls, and outcomes into per-project `observations.jsonl`. A background cheap-model observer extracts "instincts": atomic units of one trigger + one action, domain-tagged, evidence-backed, with a confidence score from 0.3 (tentative) to 0.9 (near-certain), learned from user corrections, error resolutions, and repeated workflows. v2.1 scopes instincts per project (project identified by git remote hash) to prevent cross-project contamination, promotes a project instinct to global only when seen in 2+ projects, injects at most 6 instincts at session start ranked by confidence plus project/stack relevance with a 0.7 default injection threshold, and can cluster mature instincts and "evolve" them into full skills, commands, or agents. Storage deliberately lives outside the harness config dir so background writes are not blocked by sensitive-path guards.
2. **Memory Vault with a trust boundary.** A portable Markdown memory format (`ecc.memory.v1`) shared across harnesses, with project / team / user scopes, a CLI + optional MCP server exposing only save/search/read/doctor, handoffs addressed to a target harness, and an explicit doctrine, stated repeatedly: memory is UNREVIEWED context, never executable policy; recalled content must be verified against authoritative sources; promotion to governed documentation is a human act; project memories are fail-closed gitignored by default. Memory bodies are accepted only via stdin/file, not command-line values (a small, real security detail).
3. **Deterministic enforcement outside the prompt.** Hooks are treated as executable configuration and used for gates: a GateGuard that blocks destructive shell commands (rm, force checkout, destructive find) before they run, context/scope/loop monitors with configurable budgets, memory-persistence hooks, and strictness profiles. The design claim, in its own comparison table: quality checks should not "depend on reminders" to the model.
4. **AgentShield: scanning the harness itself.** A static analyzer (claimed 1,282 tests, 98% coverage, 102 rules, built at a hackathon) that audits the agent's own configuration as an attack surface: secrets patterns, permission auditing, hook injection analysis, MCP server risk profiling, and agent/skill config review across CLAUDE.md, settings, MCP configs, hooks, agents, and skills, with CI-friendly exit codes and an optional three-agent red-team/blue-team/auditor deep mode. The README is notably careful about runner provenance: it refuses to bless an unversioned one-shot download and says registry publication alone is not an audit.
5. **Eval-driven development (`eval-harness`).** Evals as "unit tests of AI development": capability evals and regression evals defined BEFORE coding, graded by code-based, model-based, rule, or human graders, tracked with pass@k (at least one success in k) and pass^k (all k succeed) reliability metrics, benchmarked across model versions.
6. Supporting economics: a token-optimization doctrine (default to the cheaper model, subagents on the cheapest tier, compact at 50% context rather than 95%, cap active MCPs/tools because tool descriptions eat the window, strategic compaction at logical breakpoints via a dedicated skill), and a skill-creator that mines git history to draft skills and instincts.

### Trait map

| Trait | How |
|---|---|
| Memory | Primary and most differentiated: instincts (procedural, confidence-weighted) + Memory Vault (portable, scoped, trust-bounded). |
| Conscientiousness | Primary: GateGuard, hooks-as-enforcement, AgentShield self-audit, verification loops, TDD evidence trails (plan, RED evidence, GREEN, fresh-context review). |
| Execution | Primary: 71 scoped subagents, fresh-context reviewer separation (the writer never reviews its own context), worktree parallelization. |
| Intelligence | Secondary: research-first skills, iterative retrieval for subagents, model routing by task difficulty. |
| Initiation / proactivity | Moderate: session-start injection of relevant instincts and persisted context makes the agent start informed; learning is automatic. No scheduled autonomy of its own. |
| Abstract thinking | Via planner/architect agents and plan-as-artifact discipline. |
| Creativity, real-time | Not a focus. |

### Quality evidence

- Retrieved scale is enormous (293,818 stars, 43,484 forks, created 2026-01-18, pushed 2026-10-30), with a versioned guided installer (pinned `ecc-universal@2.2.3` in docs), dry-run install modes, per-harness lifecycle handling, a regression test guarding a historically repeated hooks bug, a SECURITY.md with private vulnerability reporting, and a supply-chain incident response doc. The README's own security/provenance caution (official sources only, malware warning about mirrors, pinned-version-is-not-an-audit disclaimer) is the behavior of a project that has been targeted because of its popularity.
- Depth checks passed: the continuous-learning-v2 and eval-harness SKILL.md files are detailed, versioned, and internally consistent with the README's claims (thresholds, storage paths, command names all match).
- Discounts: the headline counts blur canonical vs per-harness copies (the tree's 1,068 SKILL.md files vs the catalog's ~314 canonical skills, which the README itself explains as adapters packaging the same workflows; a reader must count carefully, as with any roster). A commercial Pro tier ($19/seat/mo for private repos via the GitHub App) sits beside the MIT core, so some future capability may land behind the hosted product. 191 open issues at this scale is unremarkable.

### Transferable value for the baseline stack

**Already covered:** The baseline's nightly-synthesis memory is, for a single user, arguably stronger than the Vault for semantic memory (it curates, supersedes, and derives an alignment synthesis, where the Vault deliberately keeps everything unreviewed). The baseline also already has hooks, crons, subagent/workflow orchestration with fresh-context review, a regression-blocker gate that exceeds ECC's eval harness in strictness for code, model-cost awareness, and a skills library. ECC as a system install would be a second harness competing with the native one, the same single-source-of-truth problem as Superpowers, at much larger scale.

**Genuinely additive, four items, in value order:**

1. **Instincts as a memory TYPE the baseline lacks.** Baseline memory is semantic/episodic and human-curated in effect (facts, decisions, relationships). It has no atomic, confidence-scored PROCEDURAL layer: small trigger->action behaviors extracted automatically from corrections and repeated workflows, project-scoped, injected in a small ranked budget at session start, and promoted only on cross-context repetition. The desk side of the baseline (bug log, doctrine lessons) captures some of this manually and only for engineering. The instinct model, especially project scoping, the 0.7 injection threshold, the cap of ~6 injected, and evolve-into-skill promotion, is a complete, field-tested design for the missing layer. ADOPT-IDEA, build natively.
2. **AgentShield's category: audit the agent's own configuration.** The baseline gates code changes rigorously but has no equivalent standing scan of its own skills, hooks, connector configs, and permission surfaces for secrets, over-broad permissions, and injection risk. The checklist taxonomy (5 categories, ~102 rules) is the transferable asset, whether or not the tool itself is ever run.
3. **The Vault's trust-boundary wording, verbatim-grade.** "Memory is unreviewed context, not executable policy; verify against authoritative sources; promotion is a human act." The baseline's security posture already treats retrieved content as data, but stating this as a formal property OF the memory system, with scopes and a doctor/validation command, sharpens it. Cheap to adopt as doctrine language.
4. **pass@k / pass^k for agent reliability.** The baseline grades trading sleeves against benchmarks and gates code with tests, but does not grade AGENT task reliability itself with at-least-one-of-k vs all-of-k metrics across prompt/skill changes. ECC's eval-harness framing gives a ready vocabulary for regression-testing changes to the baseline's own skills and doctrine.

### Risks

- **Install blast radius (main risk).** ECC is designed to write hooks, rules, MCP configs, and settings into every harness it touches, via npm one-liners. Run as documented on the baseline's machine it would rewire the working stack. Any adoption must be read-only study plus native reimplementation, never the guided installer. The repo itself warns that hooks/MCP/instructions are executable configuration; that warning applies to ECC too.
- **Supply chain.** Popularity makes it a mirror/typosquat target (its own warning). npm dependencies of the universal package are unaudited by this inspection.
- **Commercial drift.** MIT core "forever" per the README, but the Pro/GitHub-App tier creates an incentive gradient; the free surface could stagnate relative to the hosted one.
- **Complexity / context cost.** Its own docs warn that enabling everything destroys the context window; a 300-skill, 71-agent surface is the opposite of the baseline's curated minimalism.
- **Abandonment risk:** Low near-term (daily pushes, large contributor surface), but the maintenance burden is huge and single-brand-centered.

### Verdict

**ADOPT-IDEA** (four items: instinct-type procedural memory built natively, an AgentShield-style self-configuration audit, Vault trust-boundary language for memory, pass@k/pass^k agent-reliability grading). Do NOT install the system or its npm packages on the baseline stack. Its generic skills/agents catalog is REFERENCE only.

---

## 5. fainir/most-capable-agent-system-prompt

### Metadata

| Field | Value (live API, 2026-10-31) |
|---|---|
| Full name | `fainir/most-capable-agent-system-prompt` |
| Description | "A copy-paste system prompt that has your coding agent (Claude Code, Codex, Cursor) build a self-improving agent system for any computer work." |
| Stars | 880 |
| Forks | 129 |
| Created | 2026-03-28 |
| Last push | 2026-10-30T02:30:28Z |
| Archived | No |
| License | MIT |
| Default branch | `main` |
| Open issues | 1 |

### What it is

A single-file artifact: the entire repo is a README (about 2,950 lines; the prompt itself about 16,800 words / 111,000 characters / roughly 23,000 tokens) plus a license and one architecture diagram. There is no code. The README is the product: a copy-paste bootstrap prompt that instructs whatever coding agent receives it to BUILD a durable, self-improving agent operating system around itself, either as a harness wrapper over the existing agent (default) or as native runtime code on an agent SDK. A companion repo by the same author packages a ready-made subset as installable skills/hooks for those who do not want the build-it-yourself route. Verified from the tree: exactly 4 files.

### Mechanism in plain terms

The prompt is an architecture specification written as orders. Its load-bearing parts, read from the prompt body:

1. **Reader contract first.** It tells the agent HOW to consume it: read the non-negotiables first, immediately write a short local operating summary file (so the 23k-token prompt does not have to survive in context), ask only questions whose answers are dangerous to assume, and treat a strategy essay without artifacts as failure. First milestone is fixed: prove ONE closed loop end to end (goal -> task graph -> execution -> verification -> memory update -> human visibility -> one lesson learned) before any breadth.
2. **Filesystem-first project operating system.** Every project folder carries a canonical file pack (`project/charter`, `plan.md`, `tasks.md`, `knowledge.md`, `decisions.md`, `status.md`, `handoff.md`, `FAILURE.md`, `artifacts/`, `evals/`, `runs/`) with the doctrine that conversations, hidden context, and vendor session history are NOT canonical memory; the files are. Databases and dashboards may mirror/index the files, never replace them. Read before acting, update during execution, record decisions and failures when they happen, leave an explicit handoff.
3. **Reliability math.** Workflows multiply per-step failure ("the march of nines"): 90% per-step reliability is untrustworthy at length. Conclusions: skills alone are insufficient because prompt-only behavior is probabilistic; anything that must happen every time must be CODIFIED (hooks, scripts, gates), not requested; verifiers are separate layers, not self-checks.
4. **Momentum engine (its most distinctive section).** The system must never stall: it maintains five live queues at all times (`now`, `next`, `blocked`, `improve`, `recurring`), a next-work selection rule (unblock the milestone, fix reliability/verification gaps, convert repeated work into reusable assets, add eval coverage, expand breadth last), momentum ratchets (every success must leave a reusable asset: a skill, workflow, eval, template, monitor, policy, or memory artifact), mechanical anti-stall rules (a blocker older than a short interval gets decomposed and sidecar work proceeds in parallel; the same failure twice requires a guardrail/test/policy, not a retry; idle waiting time is filled with eval, memory-cleanup, or backlog work), a first-72-hours bias, and a "never finish empty-handed" rule (every substantial run ends with updated state, visible evidence, a reusable artifact, a clear next step, and at least one improvement candidate).
5. **Layered memory taxonomy.** Hot (current contract/plan/tasks/blockers), warm (active project knowledge/decisions/conventions), cold (archives/incidents/history), plus episodic, semantic, procedural, and preference memory, and temporal memory with supersession and freshness metadata; promotion from episodic to semantic; provenance and confidence on learned facts.
6. **Self-improvement engine with eval protection.** Two modes: inline learning after every task (record what worked/failed/slowed, classify the gap, update the smallest useful artifact, add an eval if a blind spot was exposed) and a background loop (one bounded hypothesis, one change, run a representative eval slice, keep if better and safe, revert if worse, log). Failure gap taxonomy with 13 classes (missing skill/tool/permission/memory, bad decomposition, bad verification, unsafe autonomy, poor model routing, context overload, weak observability, missing eval, external dependency, bad requirements), each mapped to its most leverageful repair type. Explicit ban: no giant prompt surgery without eval protection.
7. **Governance and economics as architecture.** Autonomy levels (supervised/guided/autonomous/trusted) earned from outcomes rather than declared, per-action approval gates, budgets per task/goal/project/day with pause-on-exceed, model routing (cheap models for classification/drafts, strong models for planning/review/adversarial checks), full observability (task/agent/tool lifecycles, costs, stuck tasks, retry storms, incidents with postmortems), and context-decay management (plan recitation, handoffs, fresh-session resume from files).

### Trait map

| Trait | How |
|---|---|
| Initiation / proactivity | Primary and best-in-cluster on paper: momentum queues, anti-stall rules, background compounding loops, proactive-vs-reactive work ratio as a tracked metric. |
| Memory | Primary: the layered taxonomy and filesystem-first doctrine. |
| Execution | Primary: task graphs, build order, closed-loop-first milestone, harness library. |
| Conscientiousness | Primary: verification layers, codify-the-mandatory rule, governance, budgets, incident handling. |
| Abstract thinking | Strong: capability defined across 9 dimensions (breadth, depth, reliability, transfer, memory, self-improvement, governance, economics, durability), success metrics defined before building. |
| Intelligence | Architectural rather than model-level: routing, evals, and decomposition. |
| Creativity | Only as breadth expansion and external-intelligence experiments in the improve queue. |
| Real-time | Monitors/recurring loops are specified, but nothing is implemented. |

### Quality evidence

- As a document: coherent, specific, and unusually self-aware (it anticipates skimming, context loss, and stall behavior, and engineers against all three). The research appendix and subsystem reference map ground its layers in named prior systems. Pushed 2026-10-30, MIT, 880 stars / 129 forks in 7 months: respectable for a single prompt file.
- As a system: UNPROVEN by construction. There is no code, no test, no eval result, and no reference deployment in the repo; every capability claim is a claim about what a recipient agent MIGHT build. The quality of any resulting system depends entirely on the executing agent and the user's supervision. This is the cluster's widest gap between design quality and evidence.
- Honest self-disclosure helps: the README states the token cost plainly, warns that instructions-file use exceeds recommended file sizes on both major harnesses (and gives the exact config fix for one), and distinguishes the bootstrap-once use from the expensive always-on system-prompt use.

### Transferable value for the baseline stack

This repo is best read as a mirror: the baseline stack ALREADY implements most of its architecture in production rather than on paper. Filesystem-first project state (goal workspaces with their own files), layered memory with nightly synthesis and supersession, cron/hook proactivity, subagent/workflow orchestration with checkpointing, a strict verification doctrine that codifies mandatory steps as gate-wired tests (exactly its "codify, don't request" conclusion, taken further), budgets/approvals, and failure-driven doctrine updates. Adopting the prompt itself would be actively harmful: pasting a 23k-token generic bootstrap over a mature, tuned stack invites the agent to scaffold a parallel system, a second source of truth, on top of the working one.

Residual additive ideas, three, all small:

1. **The five momentum queues as a named checklist.** The baseline has goals, tracking items, crons, and open-defect reporting (open problems must be named on every relevant report until cured, which is stronger than this prompt for defects). What it does not have as one artifact is the `improve` queue discipline: a standing, always-nonempty list of self-improvement work (eval gaps, flaky workflows, stale assumptions) that idle/background capacity drains by rule, plus the explicit next-work priority order. Worth adopting as a lightweight convention, not a build.
2. **The 13-class gap taxonomy for failure classification.** The baseline root-causes failures well but classifies them in prose. A fixed taxonomy (missing skill/tool/permission/memory, bad decomposition, bad verification, context overload, missing eval, etc.) attached to post-failure records would make patterns across failures countable, which is what turns anecdotes into a repair queue.
3. **Two tracked ratios:** percentage of work completed proactively vs reactively, and memory reuse rate. Both are named success metrics in the prompt; both are measurable in the baseline from existing logs; neither is currently a headline number. The proactive ratio in particular is the honest scoreboard for the baseline's initiation trait.

Everything else (ratchets, never-finish-empty-handed, autonomy earned from outcomes) restates baseline practice in good language; the language itself is useful for onboarding documents but changes no behavior.

### Risks

- **Bootstrap-over-a-running-system risk (main risk, specific to this stack).** Used as directed (paste into a fresh agent), it builds a greenfield system. Used carelessly on the baseline, it would duplicate and destabilize. The risk is in application, not content.
- **Unproven claims.** No evidence any single deployment of this prompt produced a system meeting its own success metrics. Treat as design literature.
- **Token/context cost.** 23k tokens per request if misused as a standing system prompt; the README itself steers against this.
- **Abandonment risk:** Low consequence; a static document cannot break. Maintenance matters little.
- **Security risk:** Minimal as text. Indirect risk: a system built from it with "trusted" autonomy levels and broad computer-work surfaces, built quickly by an agent, could outrun its governance. Not this repo's code, but its ambition.

### Verdict

**ALREADY-HAVE** (equivalents: filesystem-first state = goal workspaces and project files; layered memory + synthesis = the memory system; codified verification = InfinityBlade plus gate-wired regression blockers; proactivity = cron/hook lanes and open-defect law, which exceed the prompt's versions). Residual ADOPT-IDEA slivers: the five-queue momentum checklist with an explicit improve queue, the 13-class failure gap taxonomy, and proactive-vs-reactive / memory-reuse ratios as tracked metrics. Do not run the prompt against the live stack.

---

## Cluster summary: ranking by transferable value

Ranking criterion: marginal improvement to the baseline stack (which is already strong on doctrine, memory, and proactivity), weighted by evidence that the mechanism works as described.

| Rank | Repo | Verdict | Highest-value transferable item |
|---|---|---|---|
| 1 | affaan-m/ECC | ADOPT-IDEA (4 items, no install) | Instincts: atomic, confidence-scored, project-scoped procedural memory that evolves into skills. The one memory type the baseline lacks, with field-tested parameters (0.7 injection threshold, ~6 injected, promote on 2+ contexts). Runner-up: AgentShield's audit-the-harness-itself category. |
| 2 | obra/superpowers | ADOPT-IDEA (3 items, no install) | TDD-for-skills: pressure-test a skill against subagents without it, record exact rationalizations, write the minimal skill, re-test. Plus rationalization tables as a format, and a packaged session-diagnosis skill. Highest evidence quality in the cluster. |
| 3 | findscripter/everything-skills | ADOPT-IDEA (schema only); content REFERENCE | Typed skill graph (`requires`/`related`/`combines_with`/`supersedes`) plus separate conservative quality facets and negative-boundary descriptions. Turns a flat skill list into a composable, self-qualifying library. |
| 4 | fainir/most-capable-agent-system-prompt | ALREADY-HAVE; 3 sliver ideas | The momentum-queue checklist with a standing improve queue, the 13-class failure gap taxonomy, and proactive-vs-reactive ratio as a tracked metric. Best design mirror in the cluster, weakest evidence (no code, no deployment proof). |
| 5 | Wangnov/chatgpt-skill | REFERENCE | The cheap-watcher delegation pattern with a multi-signal end-of-output completion oracle and needs-human-input priority. Competent craft, but narrow, stale, unlicensed-per-API, and locked to another product's web UI. |

**Cross-cluster findings (patterns no single repo owns):**

1. **The field has converged on the baseline's architecture.** Files as canonical memory, skills as procedural memory, hooks/codified gates over prompt requests, fresh-context review, verify-before-claiming: all five repos assert some subset, and the baseline already runs the union. The marginal value in this cluster is in refinements, not foundations.
2. **The two refinements that recur and are worth real work:** (a) learning at FINER granularity than a skill or a memory entry, with confidence attached (ECC instincts; everything-skills quality facets apply the same instinct to the library itself), and (b) testing the instruction artifacts themselves with the same rigor as code (Superpowers TDD-for-skills; ECC pass@k/pass^k). Both point the same direction: the baseline's next reliability gains come from measuring and scoring its own playbooks, not from adding more of them.
3. **Description hygiene is a shared discovery.** Superpowers (triggers only, never summarize the workflow) + everything-skills (must state the negative boundary) together define a complete skill-description standard. A one-pass lint of existing skill descriptions against both rules is the cheapest concrete win in this cluster.
4. **Nothing in this cluster enhances the trading book directly, and nothing enhances real-time capability at all.** All five repos are coding-agent-centric, batch/session-paced systems. Any claim that this cluster improves market-facing or real-time traits would be unsupported by the files inspected.
5. **Adoption shape for the whole cluster is "read and reimplement natively, never install."** Three of five repos are designed to write hooks/settings into the harness on install; doing so on a tuned stack creates competing sources of truth, which the baseline doctrine forbids. Every ADOPT-IDEA above is a design transfer, not a dependency.

## Coverage ledger

| Repo | Status | Evidence |
|---|---|---|
| obra/superpowers | INSPECTED | Live API metadata; full README; recursive tree (300 files, 15 skills enumerated); full reads of `skills/using-superpowers/SKILL.md`, `skills/verification-before-completion/SKILL.md`, head of `skills/writing-skills/SKILL.md`. |
| Wangnov/chatgpt-skill | INSPECTED | Live API metadata; full README (bilingual, Chinese sections read in the original); recursive tree; full head read of `claude-chatgpt-skill/SKILL.md`; `references/watcher-subagent.md` read. Limitation: the Codex variant SKILL.md was tree-verified and README-compared but not read in full; the Claude variant was treated as canonical. |
| findscripter/everything-skills | INSPECTED | Live API metadata; README head and generated-index sections; recursive tree (2,835 files, 1,115 SKILL.md counted); `SCHEMA.md` read; 6 meta-volume SKILL.md files spot-read (self-reflection, context offload, context budget, closed-loop delivery, idea evolution, parallel dispatch). Limitation: 1,115 skills cannot be individually read; content-quality claims rest on the meta-volume sample plus the repo's own quality metadata design, and are stated as such. |
| affaan-m/ECC | INSPECTED | Live API metadata; README including What's Inside, Key Concepts, Why Choose ECC, Memory Vault, Token Optimization, and Security sections; recursive tree (6,449 files); full head reads of `skills/continuous-learning-v2/SKILL.md` and `skills/eval-harness/SKILL.md`; hooks directory listing. Limitation: at 300+ canonical skills and 71 agents, the catalog beyond the mechanisms named was sampled, not exhausted; companion products (AgentShield, ecc-universal) were assessed from this repo's documentation and file structure, not by running them (per research-only rails). |
| fainir/most-capable-agent-system-prompt | INSPECTED | Live API metadata; complete tree (4 files, the README is the artifact); README framing sections read in full; prompt body read across its major systems (reader contract, momentum engine, filesystem OS, planning doctrine, reliability math, memory system, model routing, governance, eval/self-improvement engine, gap taxonomy, observability, context management, multi-agent patterns) via section extraction. |

Unreachable: none. Redirected: none. All five repos returned live API metadata and raw content on 2026-10-31. Star/fork figures are as returned by the API at inspection time and are reported as retrieved values, not independently audited.
