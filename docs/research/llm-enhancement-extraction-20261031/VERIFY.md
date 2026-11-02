# Verification of REPORT.md: LLM Enhancement Extraction Catalog

Verifier: independent workflow Verify agent. Date: 2026-10-31 (checks run about 12:38 to 12:45 ET).
Method: live GitHub API (`api.github.com/repos/...`, contents API with raw accept header, git/trees API) via curl/urllib, plus actual repo files (README, SKILL.md, docs .mdx, prompt extraction) for mechanism claims. The report itself states its figures are "live API values retrieved on 2026-10-31", so star counts were judged against same-day values, allowing trivial intra-day drift (a few stars).

## Overall verdict: PASS

No material errors. Two minor wording errors were found and corrected in place in REPORT.md under a "Verification corrections" heading at the top of the file. No shortlist claim was unsupported, so nothing was downgraded. Every repo named in the coverage ledger that was sampled exists, and the repos marked Unreachable/Redirected were honestly marked (both confirmed below).

## Sampled claims (24 repo checks, 8 mechanism checks; requirement was at least 10 claims including at least 4 mechanisms)

### Existence, stars, last activity, license

| # | Claim in REPORT.md | Live API result 2026-10-31 | Outcome |
|---|---|---|---|
| 1 | obra/superpowers: 309,852 stars, 27,560 forks, pushed 2026-10-29, MIT, created 2025-10-09 | 309,856 stars, 27,561 forks, pushed 2026-10-29T23:35Z, MIT, created 2026-10-09 (2025-10-09T19:45Z) | PASS (drift +4/+1 stars/forks, same day) |
| 2 | affaan-m/ECC: 293,818 stars, pushed 2026-10-30, MIT | 293,826 stars, pushed 2026-10-30T03:06Z, MIT | PASS (drift +8) |
| 3 | supermemoryai/supermemory: 31,480 stars, pushed 2026-10-30, MIT | 31,480 stars on first check (31,481 on a later same-day check), pushed 2026-10-30, MIT | PASS |
| 4 | mem0ai/mem0: 68,158 stars, pushed 2026-10-30, Apache-2.0 | 68,159 stars, pushed 2026-10-30, Apache-2.0 | PASS (drift +1) |
| 5 | qualixar/superlocalmemory: 269 stars, pushed 2026-10-28, AGPL-3.0; tree about 5,303 entries | 269 stars, pushed 2026-10-28, AGPL-3.0; recursive tree exactly 5,303 entries, not truncated | PASS (exact) |
| 6 | thunlp/ProactiveAgent: 684 stars, Apache-2.0, pushed 2026-05-12 | 684 stars, Apache-2.0, pushed 2026-05-12T08:51Z | PASS (exact) |
| 7 | tao-hpu/awesome-proactive-agents: 7 stars, CC0 per README footer | 7 stars; API license field is null, but README footer states "License: CC0" verbatim | PASS (report's qualification was accurate) |
| 8 | promptfoo/promptfoo: 26,669 stars, MIT, pushed day of inspection | 26,670 stars, MIT, pushed 2026-10-31 | PASS (drift +1) |
| 9 | openai/plugins: 7,684 stars, pushed 2026-10-30, no licence in API metadata; 62 plugin bundles counted in tree | 7,684 stars, pushed 2026-10-30, license null; tree yields exactly 62 plugin directories | PASS (exact) |
| 10 | vinicq/falsegreen-skill: 2 stars, MIT (via README badge/family packaging) | 2 stars, MIT, pushed 2026-10-19, default branch master | PASS |
| 11 | kuroudo-ai/done-gate: 0 stars, single push date 2026-09-30 | 0 stars, pushed_at 2026-09-30T00:06Z (7 commits spanning 2026-09-27 to 09-30; "single push" is accurate as a pushed_at claim) | PASS |
| 12 | bytedance/UI-TARS: 11,654 stars, Apache-2.0, last push 2026-01-27 | 11,654 stars, Apache-2.0, pushed 2026-01-27 | PASS (exact) |
| 13 | letta-ai/letta: 25,306 stars, Apache-2.0, pushed 2026-10-18 | 25,306 stars, Apache-2.0, pushed 2026-10-18 | PASS (exact) |
| 14 | dair-ai/prompt-engineering-guide: 79,699 stars, MIT, last push 2026-03-11 | 79,699 stars, MIT, pushed 2026-03-11 (full_name dair-ai/Prompt-Engineering-Guide) | PASS (exact) |
| 15 | GreenLv/codex-context-guard: 4 stars, Apache-2.0, pushed 2026-10-31 | 4 stars, Apache-2.0, pushed 2026-10-31 | PASS |
| 16 | miuuyy/codex-chatgpt-web: 15,338 stars, MIT, pushed 2026-10-30 | 15,338 stars, MIT, pushed 2026-10-30 | PASS (exact) |
| 17 | findscripter/everything-skills: 6 stars, licence Other/NOASSERTION, 1,115 SKILL.md in tree | 6 stars, NOASSERTION, recursive tree SKILL.md count exactly 1,115 | PASS (exact) |
| 18 | hashgraph-online/awesome-ai-plugins: 942 stars, 880 forks, Apache-2.0; plugins.json counted at 1,116 entries | 942 stars, 880 forks, Apache-2.0; plugins.json parses with exactly 1,116 plugins | PASS (exact) |
| 19 | pionxzh/chatgpt-exporter: 2,849 stars, MIT, pushed 2026-10-30 | 2,849 stars, MIT, pushed 2026-10-30 | PASS (exact) |
| 20 | fainir/most-capable-agent-system-prompt: 880 stars, MIT, pushed 2026-10-30, exactly 4 files | 880 stars, MIT, pushed 2026-10-30; tree is exactly 4 files (.gitignore, LICENSE, README.md, SVG) | PASS on these points; line-count wording corrected (see Errors) |

### Coverage-ledger honesty (existence / unreachable / redirected)

| # | Ledger claim | Live result | Outcome |
|---|---|---|---|
| 21 | bytedance/UI-TARS-2 "Unreachable as a repo (does not exist)" | API returns HTTP 404 Not Found | PASS (honestly marked) |
| 22 | microsoft/HoloAssist "Unreachable as a repo" | API returns HTTP 404 Not Found | PASS (honestly marked) |
| 23 | codelion/optillm "Redirected" to algorithmicsuperintelligence/optillm (4,333 stars, Apache-2.0) | API returns HTTP 301 to the renamed repo; following it gives algorithmicsuperintelligence/optillm, 4,333 stars, Apache-2.0, pushed 2026-10-31 | PASS on status; parenthetical method detail corrected (see Errors) |
| 24 | Ledger existence sweep: 32 further ledger repos sampled (memoryplugin/mcp-server 1 star, memoryplugin/agent-skills 6, MemTensor/MemOS 12,208, plastic-labs/codex-honcho 66 pushed 2026-09-01, ejentum/ejentum-mcp 16, kyegomez/tree-of-thoughts 4,593, assafelovic/gpt-researcher 30,402, langfuse/langfuse 36,796 NOASSERTION, saeedezzati/superpower-chatgpt 1,707 pushed 2024-06-18 no licence, sailist/chatgpt-enhancement-extension 328 pushed 2023-04-19 MIT, ChatGPTBox-dev/chatGPTBox 10,776, interstellard/chatgpt-advanced 6,426 pushed 2024-08, doggy8088/ChatGPTToolkitExtension 194 no licence, lencx/Noi 9,072, nextai-translator 25,023 AGPL-3.0, Wangnov/chatgpt-skill 7 pushed 2026-06-10 no licence, taishi-i/awesome-ChatGPT-repositories 3,336 CC0, liutj9/ProactiveEval 5 no licence with all 5 commits on 2025-08-28, DenisSergeevitch/chatgpt-custom-instructions 2,810 pushed 2026-03-14 no licence, letta-ai/letta-code exists, and 8 siliconjungle repos: ambient-ai-chat 0, cabinet, computational-markdown 5, ink-knowledge 0, fs-mcp 0, mcp-template 0, mcp-package-readme 0, llm-fact-log 5 no licence) | All 32 returned HTTP 200 with star/push/license values matching the report | PASS |

### Mechanism descriptions (checked against actual repo files; requirement at least 4, checked 8)

| # | Mechanism claimed | File evidence | Outcome |
|---|---|---|---|
| M1 | Superpowers verification-before-completion: Iron Law "no completion claims without fresh verification evidence", 5-step gate, claim/requires table; 15 skills, 300 files | skills/verification-before-completion/SKILL.md contains the Iron Law verbatim, the 5-step Gate Function, and the Common Failures table (Tests pass / Agent completed requires VCS diff); tree is exactly 300 files with exactly 15 SKILL.md | PASS |
| M2 | ECC instincts (continuous-learning-v2): atomic trigger-to-action units, confidence 0.3 to 0.9, project-scoped by git remote hash, promotion to global in 2+ projects, evolve into skills; 1,068 SKILL.md in tree | skills/continuous-learning-v2/SKILL.md states all of these (confidence 0.3-0.9 weighted, project detection via git remote URL hashed, Project to global when seen in 2+ projects, hooks on PreToolUse/PostToolUse, background Haiku observer, corrections/error resolutions/repeated workflows as sources); tree SKILL.md count exactly 1,068, total 6,449 files as reported | PASS |
| M3 | falsegreen-skill (Shortlist #3, the only ADOPT-CODE): six-judgement J1-J6 protocol, mock-asserted-back-to-itself canonical example, fix is an independently computed expected value | README and SKILL.md (default branch master) contain the full J1-J6 table, the exact mock example (`assert result == mock_rate.return_value`) and the independent-oracle fix (`assert result == 90`); repo description itself names the J1-J6 protocol; CI badge, npm package, HOL trust badge present as reported | PASS, shortlist claim supported, no downgrade |
| M4 | done-gate (Shortlist #8): stop hook blocks a completion claim once if the same turn has no test result/exit code/command output, with an honest unverified escape | README confirms every element verbatim, plus stdlib-only Python, installer back-up/idempotence, and stated limits (checks evidence exists, not that it supports the claim) | PASS |
| M5 | Supermemory (Shortlist #4): static/dynamic profile split, typed edges updates/extends/derives, expiry/forgetting | README shows profile.static (long-term facts) and profile.dynamic (recent context) returned with search; apps/docs/concepts/graph-memory.mdx documents Updates, Extends, and Derives sections and automatic forgetting | PASS |
| M6 | Mem0: single-pass ADD-only extraction, entity linking, fused semantic + BM25 + entity retrieval, temporal ranking; README caveats headline benchmarks are managed-platform numbers | README contains all four mechanism bullets verbatim and the managed-platform caveat verbatim | PASS |
| M7 | tao-hpu pilot + theta inequality (Shortlist #1): intervene iff E[benefit] minus E[cost] > theta; deterministic stdlib pilot seeding must/may/must-not windows from HoloAssist annotations, TMLR 2026 companion survey | README line 11 states the inequality verbatim; README links the TMLR 2026 survey on OpenReview and describes pilot/ exactly as reported (standard library only, deterministic, results.txt expected output) | PASS |
| M8 | ProactiveAgent (Shortlist #1): ActivityWatch sensing, separate reward model F1 0.918, ProactiveBench 6,790 events | README confirms ActivityWatch collection, reward model 0.918 F1, and event counts totalling 6,790 (2,275 + 2,354 + 2,161) | PASS |

## Errors found and corrected in REPORT.md

1. Minor, fainir line count (Section 2.2): "a single 2,950-line README" conflated two figures. Live file: README is 3,325 lines; the extracted copy-paste prompt block is 2,949 lines / 110,967 characters (matching the cluster file's prompt word/character counts). Corrected in place. This does not affect any verdict: fainir is ALREADY-HAVE with slivers, not a shortlist item, and its momentum-queue mechanism was verified in the prompt text (DEFAULT MOMENTUM QUEUES section, five queues named).
2. Minor, codelion/optillm ledger parenthetical (Section 6): "(API returned no repo under the old owner...)" is wrong as a method detail; the API returns HTTP 301 Moved Permanently to the renamed repo. Corrected in place. The Redirected status and the inspection target were correct.

Both corrections are noted at the top of REPORT.md under "Verification corrections", as required.

## Notes on non-errors

- Star/fork differences of +1 to +8 on the largest repos (superpowers, ECC, mem0, promptfoo, supermemory) are intra-day drift after the cluster passes retrieved their values; the report explicitly frames its figures as retrieved values from 2026-10-31, and push dates and licenses matched exactly in every sampled case.
- YETI and PRISM in the ledger carry no owner/repo path and are marked "Unreachable in this pass (assessed only as entries in the awesome list... no individual verdict issued)", which is an honest marking rather than a false existence claim.
- siliconjungle/ink-knowledge is marked "Inspected (README level only; licence, tree, and code not checked, stated)" in the ledger, matching its actual state (repo exists, 0 stars, MIT, pushed 2026-10-17).
