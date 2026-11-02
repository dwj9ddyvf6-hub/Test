# Pass 3, Dive 3: The Official Vendor Layer

Date: 2026-10-31
Scope: only places Passes 1-2 did not look.
(a) Anthropic published engineering guidance and the anthropics GitHub org
(b) The Agent Skills standard at agentskills.io and its specification
(c) OpenAI agents and evals guidance (Agents SDK docs, openai/evals)
(d) The official MCP Registry API and modelcontextprotocol/servers reference implementations

Yield required: genuinely new finds, and confidence changes about already-adopted
disciplines, each tied to evidence from this layer. Verdict vocabulary:
ADOPT-CODE, ADOPT-IDEA, ALREADY-HAVE, REFERENCE, SKIP (with reason).

Provenance discipline used throughout: material read in full on the primary
surface is marked PRIMARY. Material known through search excerpts, full-text
mirrors, or multiple consistent secondary summaries is marked SECONDARY and is
never presented as a primary read.

---

## 1. Source (a): Anthropic engineering guidance

### 1.1 Effective context engineering for AI agents (PRIMARY, anthropic.com/engineering, published 2025-09-29, updated 2026-10-18)

Load-bearing verbatim:

- "good context engineering means finding the *smallest* *possible* set of
  high-signal tokens that maximize the likelihood of some desired outcome"
- Context rot is grounded in the n-squared pairwise attention cost and a finite
  "attention budget".
- System prompts should sit at the "right altitude": a Goldilocks zone between
  brittle hardcoded logic and vague guidance.
- Just-in-time retrieval: keep lightweight identifiers (file paths, stored
  queries, web links) and load data at runtime. Claude Code is the hybrid
  example: CLAUDE.md dropped in up front, glob/grep for just-in-time retrieval.
- Compaction: Claude Code preserves "architectural decisions, unresolved bugs,
  and implementation details while discarding redundant tool outputs", and
  continues with the compressed context "plus the five most recently accessed
  files". Tuning advice: maximise recall first, then iterate for precision.
  Tool result clearing is "one of the safest lightest touch forms of
  compaction".
- Structured note-taking: the Claude Plays Pokemon tallies are quoted verbatim
  as the worked example ("for the last 1,234 steps I've been
  training... Pikachu has gained 8 levels toward the target of 10").
- Sub-agents return "only a condensed, distilled summary... (often
  1,000-2,000 tokens)".

Verdicts:
- CONFIRMS Discipline 9 (authority hygiene for compaction) and Discipline 5
  (honest recall): vendor practice treats compaction as a recall-first,
  evidence-preserving operation, not a summarise-and-hope operation.
- ADOPT-IDEA: tool result clearing as the first, lightest compaction move,
  before any history rewrite. It is the lowest-risk rung and should be named
  explicitly in the local compaction ladder.
- ALREADY-HAVE: just-in-time retrieval by identifier and sub-agent distilled
  returns are already local practice.

### 1.2 Agent Skills launch post (PRIMARY, anthropic.com, published 2025-10-16, updated 2025-12-18: "We've published Agent Skills as an open standard")

Findings:
- Progressive disclosure in three levels: metadata (name + description)
  pre-loaded at startup, full SKILL.md on trigger, bundled files only as
  needed. With a filesystem and code execution, "the amount of context that
  can be bundled into a skill is effectively unbounded".
- Code as a deterministic tool: the PDF skill's script extracts form fields
  without loading the script or the PDF into context.
- Developing and evaluating guidance, verbatim in the load-bearing parts:
  "**Start with evaluation:** Identify specific gaps... Then build skills
  incrementally"; "Structure for scale"; "Think from Claude's perspective"
  (watch name/description triggering); "**Iterate with Claude:** ...ask Claude
  to capture its successful approaches and common mistakes into reusable
  context and code within a skill... ask it to self-reflect".
- Security: install only from trusted sources; audit less-trusted skills
  (code dependencies, bundled resources, instructions pointing at untrusted
  network sources).

Verdicts:
- CONFIRMS Discipline 6 (skills) and Discipline 7 (library/eval gate,
  scan-before-list). The vendor's own security posture is source trust plus
  manual audit; there is no vendor-supplied scan signal to lean on (see 2.2).

### 1.3 Effective harnesses for long-running agents (PRIMARY, anthropic.com/engineering, published 2025-11-26)

Findings:
- Initializer agent vs coding agent split. The initializer creates init.sh, a
  progress file (claude-progress.txt), an initial git commit, and a feature
  list of "over 200 features", all initially "failing".
- Coding agents "edit this file only by changing the status of a passes
  field". JSON was chosen for the feature list because "the model is less
  likely to inappropriately change or overwrite JSON files compared to
  Markdown files". "It is unacceptable to remove or edit tests."
- One feature at a time; leave a clean state (git commit plus progress
  summary). The failure mode of marking complete without end-to-end testing
  is cured by explicitly prompting browser-automation testing "as a human
  user would".
- Get-bearings ritual each session: pwd, read git logs and progress files,
  read the feature list, pick the highest-priority unfinished feature, run
  init.sh plus a basic end-to-end test before starting work.

Verdicts:
- CONFIRMS Discipline 8 (completion/execution: evidence, per-plan ledger,
  gate protection). This is the vendor's own long-running harness and it is
  structurally the same shape.
- ADOPT-IDEA (new transfer): state the feature/plan list in JSON, not
  Markdown, because models overwrite JSON less inappropriately; and make only
  the passes/status field editable. This is a concrete, cheap hardening of the
  local per-plan ledger.

### 1.4 Demystifying evals for AI agents (published 2026-01-09; read in full via a GitHub mirror of the official page, 0langa/anthropic-official-resources; provenance flagged, not a direct anthropic.com read)

Load-bearing verbatim and near-verbatim:

- Outcome defined against transcript: "The outcome is the final state in the
  environment at the end of the trial. A flight-booking agent might say 'Your
  flight has been booked'... but the outcome is whether a reservation exists
  in the environment's SQL database."
- "it's often better to grade what the agent produced, not the path it took";
  partial credit for multi-component tasks; graders must be resistant to
  bypasses and hacks.
- Capability evals start low; regression evals sit "nearly 100%"; capability
  evals "graduate" to regression. "**Eval saturation**... An eval at 100%
  tracks regressions but provides no signal for improvement."
- Roadmap Step 0: "20-50 simple tasks drawn from real failures is a great
  start". Step 2: two experts must reach the same pass/fail verdict; create a
  **reference solution** proving solvability; "a 0% pass rate across many
  trials (i.e. 0% pass@100) is most often a signal of a broken task". Step 3,
  **balanced sets**: "Test both the cases where a behavior *should* occur and
  where it *shouldn't*. One-sided evals create one-sided optimization."
  Step 4: isolated trials (Claude was observed gaining an unfair advantage
  "by examining the git history from previous trials"). Step 5: LLM judges
  should be given a way out ("return 'Unknown'"), with each dimension graded
  by an isolated judge. Step 6: read transcripts; "Failures should seem
  fair". CORE-Bench anecdote: 42% to 95% after fixing rigid grading and
  ambiguity.
- pass@k (at least one success in k trials) vs pass^k (all k succeed;
  0.75^3 is about 42%) are defined here. Pass 1 attributed these metrics to
  ECC; this post is their official source.

Verdicts:
- CONFIRMS Discipline 7 (pass@3 / pass^k thresholds) and Discipline 3
  (false-green defence): the official eval doctrine is outcome-first, which
  is the same claim as proof-before-green.
- ADOPT-IDEA additions to Discipline 7: (i) every eval task carries a
  reference solution proving solvability; (ii) a 0% pass@100 result is treated
  first as a broken-task signal, not a model failure; (iii) balanced
  should/should-not sets are mandatory, not optional; (iv) trials are
  isolated so prior-trial artifacts cannot leak; (v) LLM judges get an
  explicit "Unknown" exit.

### 1.5 Building effective agents (SECONDARY: search excerpts, primary page not opened in full)

- Workflows are "orchestrated through predefined code paths"; agents are
  systems where "LLMs dynamically direct their own processes". Five patterns:
  prompt chaining, routing, parallelization, orchestrator-workers,
  evaluator-optimizer.
- Agent-computer interface (ACI) investment: "we actually spent more time
  optimizing our tools than the overall prompt" (SWE-bench); poka-yoke tool
  design, where requiring absolute paths killed a relative-path error class.

Verdict: ALREADY-HAVE / REFERENCE. Consistent with local workflow practice;
no new mechanism beyond the ACI emphasis, which is picked up in 1.6.

### 1.6 Writing effective tools for agents (SECONDARY: full-text mirrors in search results, not read on anthropic.com)

- Principles: choose what to implement and what not to; namespace tools;
  return meaningful, high-signal results; token efficiency; prompt-engineer
  the tool descriptions.
- Consolidation: one schedule_event tool beats list/create primitives.
- Namespacing by service and resource; the prefix-vs-suffix choice has
  "non-trivial effects" on evals, so measure it.
- Build the eval first; have an agent analyse transcripts and rewrite tool
  descriptions against that eval. Sonnet 3.5 reached state of the art on
  SWE-bench Verified after tool-description refinements.

Verdict:
- ADOPT-IDEA (extends Disciplines 6 and 7 to the tool surface): tool
  descriptions are eval-tested artifacts in the same sense skill descriptions
  are. The local eval gate currently covers skills; the vendor evidence says
  the tool surface deserves the same treatment, including measuring
  namespacing choices instead of assuming them.

### 1.7 Multi-agent research system (SECONDARY: consistent across many secondary summaries, primary page not opened)

- Lead Opus 4 plus Sonnet 4 subagents beat single-agent Opus 4 by 90.2% on an
  internal research eval. Multi-agent uses roughly 15x chat tokens; agents
  roughly 4x. Token usage explains about 80% of BrowseComp variance.
- The lead saves its plan to memory to survive the context limit.
- Delegation contract per subagent: objective, output format, tool/source
  guidance, clear boundaries. Effort scaling written into prompts: 1 agent
  for simple fact-finding, 2-4 for comparisons, more than 10 for complex
  research.
- Subagents store work externally and return lightweight references, avoiding
  a "game of telephone".

Verdict: ALREADY-HAVE via local workflow briefs, with one new sliver worth
adopting: ADOPT-IDEA, explicit numeric effort scaling in delegation prompts.

### 1.8 Claude memory tool and context editing (SECONDARY: multiple summaries quoting the docs consistently; docs pages not opened directly)

- Memory tool: type "memory_20250818", name "memory", generally available, no
  beta header, Claude 4+. It is client-side: the model issues commands and
  the host handler executes them. Six commands under /memories: view
  (optional view_range), create, str_replace (unique match required),
  insert, delete, rename. The API auto-injects a protocol to view /memories
  before doing anything else. Path traversal defence is the handler's
  responsibility (a /memories/../../secrets.env access must fail). View
  truncates above 16,000 characters.
- Context editing (beta header context-management-2025-06-27):
  clear_tool_uses_20250919 defaults to trigger at 100,000 input tokens, keep
  3 tool uses, with clear_at_least, exclude_tools (for example ["memory"]),
  and clear_tool_inputs defaulting to false. A warning is issued as clearing
  approaches so the agent can save to memory first. Clearing invalidates the
  prompt cache, hence clear_at_least.
- Threshold compaction (compact_20260112) defaults to trigger at 150,000
  tokens, minimum 50,000.
- Launch claim (Sonnet 4.5, 2025-09-29, via a secondary summary): context
  editing plus memory together gave +39% internal performance; context
  editing alone +29%.
- Cookbooks: tool_use/memory_cookbook.ipynb, tool_use/memory_tool.py,
  tool_use/context_engineering/context_engineering_tools.ipynb; a memory demo
  uses a "MEMORY PROTOCOL" prompt (check /memories before reviewing, update
  with insights).

Verdicts:
- CONFIRMS Disciplines 4 and 5 strongly, by contrast. Anthropic's own shipped
  memory is plain client-side file CRUD under /memories with a check-first
  protocol: no extraction, no graph, no ranking, no supersession. The
  sophisticated local memory disciplines are not duplicated by the vendor;
  official practice validates files-as-memory as the substrate.
- ADOPT-IDEA (refines Disciplines 9 and 5): a named clear / compact /
  remember triage with numeric defaults (clear at 100k keeping 3 tool uses;
  compact at 150k), exclude_tools protecting memory from clearing, and a
  save-before-clearing warning step.

### 1.9 anthropics/skills and the skill-creator meta-skill (skill-creator read via a line-checked secondary at HEAD 8a1541c, 2026-09-29; repo-level facts SECONDARY)

This is the single highest-value artifact in the dive.

- skill-creator (skills/skill-creator/SKILL.md, about 485 lines) is the
  official meta-skill implementing an eval loop: draft 2-3 test prompts, save
  them to evals/evals.json, run each in its own subagent with and without the
  skill, grade assertions, benchmark pass rate, time, and tokens, and run a
  blind A/B between versions.
- Description optimizer: 20 eval queries (8-10 should-trigger plus 8-10
  near-miss should-not), a 60% train / 40% held-out test split, iterating
  while selecting on the held-out score.
- Verbatim: "Claude tends to undertrigger skills... make the skill
  descriptions a little bit 'pushy'"; and "simple, one-step queries like
  'read this PDF' may not trigger a skill even if the description matches
  perfectly, because Claude can handle them directly with basic tools".
- Repo facts at that HEAD: 19 skill folders; the document skills (docx, pdf,
  pptx, xlsx) are source-available, not open source; the rest are Apache-2.0;
  the repo also contains spec/ and template/.

Verdicts:
- CONFIRMS Discipline 6 (TDD-for-skills) and upgrades its build spec. Pass 2
  took the method from Superpowers; the vendor ships the same method as an
  artifact, with concrete numbers for descriptions specifically that Pass 2
  lacked: a 20-query balanced trigger set and a 60/40 train/held-out split,
  with with-vs-without subagent benchmarking. ADOPT-IDEA: adopt those numbers
  as the local description-testing standard.
- WARNING to Discipline 6's description hygiene: the official guidance cuts
  against a purely minimal description. Because the model undertriggers,
  descriptions should be "pushy", and all trigger context must live in the
  description itself, since body "when to use" text arrives too late to
  affect triggering. The hygiene rule survives in narrowed form: triggers
  only, no workflow summary, but written assertively.
- STRUCTURAL LIMIT (new): one-step tasks may never trigger a skill however
  good the description is. Skills wrapping one-step jobs are structurally
  unreliable and should not be gated as if triggering were under the author's
  control.

---

## 2. Source (b): The Agent Skills standard

### 2.1 Specification (PRIMARY, agentskills.io/specification, updated 2026-08-04)

- Frontmatter: name (required, max 64 chars, lowercase/numbers/hyphens, no
  leading, trailing, or consecutive hyphens, must match the parent
  directory); description (required, max 1024 chars, "Should describe both
  what the skill does and when to use it", plus keywords); license
  (optional); compatibility (optional, max 500 chars); metadata (optional
  string-to-string map); allowed-tools (optional, marked "(Experimental)").
  The body has no format restrictions.
- Progressive disclosure budgets: metadata "(~100 tokens)", instructions
  "(< 5000 tokens recommended)", resources as needed. "Keep your main
  SKILL.md under 500 lines." "Keep file references one level deep from
  SKILL.md. Avoid deeply nested reference chains."
- Validation via the skills-ref reference library. Optional directories:
  scripts/ (self-contained, helpful errors), references/, assets/.

Verdict: ALREADY-HAVE / REFERENCE. Local skills already follow the shape;
the numeric budgets (500 lines, under 5000 instruction tokens, one-level-deep
references) are worth recording as the conformance yardstick.

### 2.2 Governance and gaps (SECONDARY: Anthropic news post plus Oct 2026 analyses)

- Anthropic donated Agent Skills to the Agentic AI Foundation (AAIF, Linux
  Foundation) on 2026-10-22: name and logo, GitHub org, agentskills.io
  domain. Lead maintainers are named individuals.
- Scale figures are Anthropic's own: ">70 agent platforms", "1 million
  skills published and nearly 280 million installed" (installs trace to
  Vercel skills.sh and "do not represent unique people").
- The AAIF roadmap only *proposes* versioned releases, a formal proposal
  process, and security guidance. The spec has six frontmatter fields and
  **no version number and no signature/source field**. The skills-ref
  validator is described in a spec-repo analysis as "for demonstration
  purposes only". Discovery paths fragment: the client guide recommends
  scanning .agents/skills/, Claude Code uses .claude/skills/, Copilot and
  VS Code scan several locations.

Verdict:
- CONFIRMS Discipline 7's scan-before-list by NEGATIVE evidence. Neither the
  spec nor its validator provides any safety or provenance signal; the local
  scan gate fills a gap the official layer leaves open rather than
  duplicating an official mechanism. This is a warning about the ecosystem,
  not a contradiction of the discipline: anything imported on spec
  conformance alone is unvetted.

---

## 3. Source (c): OpenAI agents and evals guidance

### 3.1 Agents SDK sessions (PRIMARY, openai.github.io/openai-agents-python/sessions)

- A session cannot be combined with conversation_id, previous_response_id, or
  auto_previous_response_id in the same run.
- Before-run retrieval and after-run persistence are automatic.
  session_input_callback customises the history/new-input merge (the callback
  receives copies; filtering history does not re-save old items).
  SessionSettings(limit=N) caps retrieved history.
- pop_item() is documented explicitly for corrections: pop the assistant and
  user item, then ask the corrected question. Interrupted runs resume with
  the same session ID and backend.
- Backends: SQLiteSession, AsyncSQLiteSession, RedisSession,
  SQLAlchemySession, MongoDBSession (atomic sequence counter), DaprSession
  (TTL/consistency), OpenAIConversationsSession,
  OpenAIResponsesCompactionSession, AdvancedSQLiteSession
  (branching/analytics), EncryptedSession (encryption plus TTL wrapper).

Verdicts:
- ALREADY-HAVE in file form, with naming worth adopting: ADOPT-IDEA, treat
  pop_item-style correction and callback-style history pruning as named,
  bounded history-edit operations rather than ad hoc edits (supports
  Discipline 5's reviewed correction lifecycle).

### 3.2 OpenAIResponsesCompactionSession (PRIMARY, same docs) - new mechanism

- Compaction "treats the clear-and-rewrite operation as a recoverable
  replacement at the wrapper boundary": on failure or cancellation it
  attempts to restore the previous history.
- It serialises add_items(), pop_item(), and clear_session() with
  compaction; it records a wrapper generation and "skips the stale
  compaction instead of replacing newer history".
- Auto-compaction blocks streaming completion. compaction_mode is auto,
  previous_response_id, or input, with input mode as the source-of-truth
  fallback when store=False.

Verdict:
- ADOPT-IDEA (strengthens Discipline 9): a transactional safety contract for
  any local compaction that rewrites stored history - generation-checked,
  serialised against concurrent edits, and restore-on-failure. Local
  compaction currently has hygiene rules; this supplies the missing failure
  semantics.

### 3.3 Agents SDK overview (PRIMARY)

Primitives: Agents, Agents as tools / Handoffs, Guardrails, built-in tracing;
sandbox agents (manifest-defined files, resumable sandbox sessions);
human-in-the-loop; Sessions as "a persistent memory layer for maintaining
working context within an agent loop". Verdict: REFERENCE, no new mechanism
beyond 3.4.

### 3.4 Guardrails (official docs via search excerpt of openai.github.io/openai-agents-python/guardrails; SECONDARY-grade provenance)

- Input guardrails run ONLY on the first agent; output guardrails ONLY on
  the agent producing final output; tool guardrails on EVERY guarded
  function-tool invocation (input before, output after).
- Input guardrails default to parallel (run_in_parallel=True): "if the
  guardrail's tripwire is triggered, the agent may have already consumed
  tokens and executed tools before being cancelled". Blocking mode
  (run_in_parallel=False) completes before the agent starts. Tripwires raise
  Input/Output/Tool GuardrailTripwireTriggered exceptions.

Verdict:
- WARNING, load-bearing for Discipline 1's designed fire-time gate and for
  Discipline 9: a parallel-by-default gate is not a gate for anything with
  side effects. Where effects matter, the gate must be blocking, or enforced
  per-tool before execution. Any local design that borrows the
  guardrail shape must specify its execution mode explicitly; "there is a
  guardrail" is not evidence that anything was prevented.

### 3.5 OpenAI Evals: hosted shutdown and the open-source framework (SECONDARY: multiple Oct 2026 reports citing OpenAI's deprecations page; openai/evals repo not opened directly)

- The hosted Evals platform was announced deprecated on 2026-06-03, goes
  **read-only on 2026-10-31 (today)**, and the dashboard/API shut down on
  2026-11-30. OpenAI's migration guide points to **Promptfoo** (which OpenAI
  acquired, announced 2026-03-09).
- The openai/evals GitHub repo remains the open-source framework plus a
  benchmark registry: an eval is a dataset plus grading logic (string_check,
  text_similarity, label_model, score_model, python graders; multiple
  graders per eval in the migration tables).
- Hosted JSONL export does NOT carry grader definitions (support answer,
  2026-07-03); definitions must be pulled via the API before shutdown.

Verdicts:
- CONFIRMS Pass 1's promptfoo-pattern adoption: OpenAI itself now points
  there.
- ADOPT-IDEA (portability rule for Discipline 7): a release gate must live in
  files you own. Hosted eval definitions and baselines are not fully
  exportable, so any gate that exists only inside a hosted product has an
  expiry date.

---

## 4. Source (d): Official MCP Registry and reference servers

### 4.1 Registry API (PRIMARY, live query 2026-10-31 17:10 UTC)

- GET https://registry.modelcontextprotocol.io/v0/servers?search=memory&limit=20
  returned 20 records with metadata.nextCursor, against schema
  https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json.
  Each record carries _meta."io.modelcontextprotocol.registry/official" =
  {status: "active", statusChangedAt, publishedAt, updatedAt, isLatest}.
- Multiple versions of the same server are all returned (for example
  ai.korely/memory 1.0.0 with isLatest:false and 1.0.1 with isLatest:true;
  ai.smartmemory/compose-mcp 0.4.1 through 0.7.2). Consumers must filter on
  isLatest; the API does not do it for you.
- Sample names in the memory search: ai.brainmemory/brain,
  ai.chipp/chipp-memory, ai.justonce/memory, ai.memoryrouter/memoryrouter,
  ai.monolithos/cloud-memory, ai.primaxiom.memory/reasongraph ("time
  travel"), ai.smartmemory/smartmemory-mcp.
- The listing carries publisher-declared metadata only: name, version,
  repository, transport, packages/remotes, status, isLatest. There is no
  rating, scan, or verification field.

Verdicts:
- CONFIRMS Discipline 7's scan-before-list by NEGATIVE evidence, same as
  2.2: registry presence is a directory entry, not a vetting result.
- REFERENCE: the isLatest-filtering behaviour is a concrete consumer-side
  trap worth recording for any future registry use.

### 4.2 Registry as a whole (SECONDARY: registry-derived directories)

- One directory built from the official registry (theworldofai.org, verified
  2026-10-31) lists **2,977 active servers** and explicitly disclaims: "We
  have not installed these servers and we do not rate them. Nothing here says
  a server is safe, maintained, or does what it claims."
- Another registry-derived directory claims 32,727 registry total and about
  12,000 curated. Counts are not comparable across surfaces and neither
  figure is asserted here as a registry fact.

### 4.3 Reference servers (modelcontextprotocol/servers; SECONDARY via registry mirrors, DeepWiki, and the Docker catalog)

- Seven maintained reference servers: Everything, Fetch, Filesystem, Git,
  Memory, Sequential Thinking, Time. Older servers (SQLite, Postgres,
  GitHub, Brave Search, Slack, Puppeteer) are archived or deprecated; GitHub
  is now first-party at github/github-mcp-server.

**Memory server** (@modelcontextprotocol/server-memory): a knowledge graph
of Entities (name, entityType, observations[]), Relations (directed, active
voice), and Observations ("Should be atomic (one fact per observation)").
Nine tools: create_entities, create_relations, add_observations,
delete_entities, delete_observations, delete_relations, read_graph,
search_nodes, open_nodes. Local JSONL storage, single-agent. read_graph
returns the entire graph. There is no supersession, no provenance, no
temporal validity, and no tiered recall. Released v2026.7.4 on 2026-07-04
after a gap of about five months.

- Verdict: SKIP as a memory system; REFERENCE as the negative example. It is
  exactly the bare entity/relation/observation triple store that Pass 1
  cited llm-fact-log against: no negation, time, or uncertainty handling,
  and whole-graph reads. CONFIRMS Disciplines 4 and 5 by contrast - the
  official reference implementation is the floor, not the target.

**Filesystem server**: tools include read_file/read_text_file,
read_multiple_files, write_file, edit_file (git-style diff), list_directory,
directory_tree, search_files, get_file_info, move_file, create_directory,
list_allowed_directories, all confined to configured allowed directories.

- Verdict: ALREADY-HAVE / SKIP. The allowed-directories pattern is clean but
  already held locally in a stronger form.

**Sequential Thinking server**: one sequentialthinking tool recording
thoughts with revision and branching fields; no verification of the
thoughts.

- Verdict: SKIP. A thought log with no verification; the local
  tree-of-thought discipline is already held as an idea in a stronger form.

---

## 5. Confidence changes against the 12 landed disciplines

| Discipline | Verdict from this layer | Basis |
|---|---|---|
| 1. Proactivity (offline scorer + designed gate) | WARNING (design constraint) | 3.4: a parallel gate can let tools execute before the tripwire; the fire-time gate must be blocking or per-tool where effects matter |
| 2. Instincts (ECC) | No contact | Nothing in the vendor layer touches confidence-scored instincts |
| 3. False-green defence | CONFIRMS | 1.4 outcome-over-transcript grading; 1.3 "It is unacceptable to remove or edit tests" |
| 4. Memory profile/graph | CONFIRMS (by contrast) | 1.8 vendor memory is plain file CRUD; 4.3 reference Memory server has no supersession, provenance, or temporal validity |
| 5. Honest recall | CONFIRMS, plus ADOPT-IDEA | 1.1 recall-first compaction; 1.8 clear/compact/remember triage with numeric defaults; 3.1 named bounded history-edit operations |
| 6. Skills | CONFIRMS and UPGRADES, plus WARNING | 1.9 skill-creator supplies the missing description-testing numbers (20 queries, 60/40 split); WARNING: descriptions must be "pushy" against undertriggering, and one-step tasks may never trigger |
| 7. Library/eval gate | CONFIRMS, plus ADOPT-IDEA | 1.4 reference solution, balanced sets, broken-task signal, trial isolation; 2.2 and 4.1 scan gap confirmed by negative evidence; 3.5 portability rule (gate must live in owned files) |
| 8. Completion/execution | CONFIRMS, plus ADOPT-IDEA | 1.3 initializer/coding split, progress file, get-bearings ritual; new transfer: plan list in JSON with only the status field editable |
| 9. Authority hygiene / compaction | CONFIRMS, plus ADOPT-IDEA | 1.1 tool-result clearing as lightest rung; 3.2 transactional compaction contract (generation-checked, serialised, restore-on-failure) |
| 10. Bounded hidden-rubric pass | No contact | No vendor-layer evidence either way |
| 11. Rationale memory | Weak CONFIRMS | 1.7 lead agent saving its plan to memory to survive context limits is adjacent practice, not the discipline itself |
| 12. Freshness | No contact | No vendor-layer evidence either way |

No landed discipline is contradicted by this layer. Two disciplines receive
warnings that narrow how they may be implemented (1 and 6); none requires
reversal.

## 6. New finds, consolidated

1. skill-creator description optimizer: 20-query balanced trigger set, 60/40
   train/held-out split, with-vs-without subagent benchmark. ADOPT-IDEA
   (upgrades Discipline 6's build spec).
2. Demystifying Evals additions: reference solution per task, 0% pass@100 as
   a broken-task signal, mandatory balanced should/should-not sets, trial
   isolation, "Unknown" exit for LLM judges. ADOPT-IDEA (Discipline 7).
3. Guardrail execution modes: parallel-by-default can execute tools before
   the tripwire; blocking or per-tool enforcement required for side effects.
   ADOPT-IDEA as a design constraint on Disciplines 1 and 9.
4. Transactional compaction session: generation-checked, serialised,
   restore-on-failure replacement of stored history. ADOPT-IDEA
   (Discipline 9).
5. Clear/compact/remember triage with numeric defaults (clear 100k / keep 3,
   compact 150k, exclude_tools protecting memory, save-before-clearing
   warning). ADOPT-IDEA (Disciplines 5 and 9).
6. Plan/feature list in JSON with only the status field editable, because
   models overwrite JSON less inappropriately than Markdown. ADOPT-IDEA
   (Discipline 8).
7. Tool descriptions as eval-tested artifacts, including measured
   namespacing choices. ADOPT-IDEA (extends Disciplines 6 and 7 to the tool
   surface).
8. Eval portability rule: a release gate must live in files you own; hosted
   eval definitions are not fully exportable. ADOPT-IDEA (Discipline 7).
9. Named bounded history-edit operations (pop_item correction pattern,
   callback pruning). ADOPT-IDEA, largely ALREADY-HAVE in file form.
10. Numeric effort scaling in delegation prompts (1 / 2-4 / 10+ agents).
    ADOPT-IDEA sliver; the delegation contract itself is ALREADY-HAVE.
11. MCP Memory reference server. SKIP as a system, REFERENCE as the negative
    example for Disciplines 4 and 5.
12. MCP Filesystem server: ALREADY-HAVE / SKIP. Sequential Thinking server:
    SKIP.
13. Agent Skills spec conformance budgets (500 lines, under 5000 instruction
    tokens, one-level-deep references). REFERENCE.

## 7. Coverage ledger

Read in full on the primary surface:
- Anthropic: context engineering post; Agent Skills post; long-running
  harnesses post; agentskills.io specification.
- OpenAI: Agents SDK sessions docs; Agents SDK overview.
- MCP Registry API: one live query (search=memory, limit=20), 2026-10-31
  17:10 UTC, 20 records returned.

Read in full via a mirror of the official page (flagged):
- Anthropic: Demystifying evals for AI agents (GitHub mirror
  0langa/anthropic-official-resources).

Known through search excerpts, full-text mirrors, or consistent secondary
summaries (flagged inline, never upgraded to primary):
- Anthropic: Building effective agents; Writing effective tools for agents;
  Multi-agent research system; memory tool and context editing docs;
  skill-creator SKILL.md (line-checked secondary at HEAD 8a1541c).
- Agent Skills governance and AAIF donation; OpenAI guardrails docs excerpt;
  OpenAI Evals deprecation and migration reporting; MCP reference server
  details via registry mirrors, DeepWiki, and the Docker catalog.

## 8. Looked-and-empty ledger

- MCP Registry API categories: no category parameter was found. "Top servers
  by category (memory / productivity / knowledge)" is not a registry-native
  cut. Only the search=memory sample was pulled; productivity and knowledge
  category trawls are looked-and-empty as API categories.
- GitHub API counts: star and fork counts were not systematically pulled this
  dive. Secondary figures for anthropics/skills conflict (about 173k vs
  about 179k, Sep 2026) and for agentskills/agentskills sit around
  24-25.7k; none is asserted here.
- GitHub issues and discussions trawl (highest-reaction threads) for
  anthropics/skills, agentskills, the OpenAI repos, and
  modelcontextprotocol/servers: NOT PURSUED in this dive. Logged honestly as
  a gap, not as an empty result.
- openai/evals repository: not opened directly; the account in 3.5 rests on
  framework descriptions plus the hosted-platform deprecation reporting.
- Claude docs pages for the memory tool, context editing, and compaction:
  not opened directly; parameters in 1.8 come from multiple secondary
  summaries quoting the docs consistently.
- No source in scope was found to be unreachable; the gaps above are
  provenance and depth gaps, not access failures.
