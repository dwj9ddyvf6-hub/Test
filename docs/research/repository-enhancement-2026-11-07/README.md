# Research-backed design for an agent-readable research library

Research date: **2026-11-07**. This report concerns the design of the Test research and software library. The companion [source ledger](SOURCES.json) records 15 source groups, inspected portions, limitations, and exact commits for five external repositories. This is an external research synthesis and an enhancement design, not a claim that every archived strategy has been validated or that every LLM will improve.

The objective is to preserve the library's full substance while increasing the proportion an arriving reader can locate, understand, reproduce and use correctly. The strategy catalog, historical packages, research studies, source code, examples, terminal assets and operating guides have different jobs. An effective entry route makes those jobs visible without replacing the underlying material.

## What the evidence supports

[Agent Skills](https://agentskills.io/specification) and [Anthropic's context-engineering guidance](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) support layered access: a discoverable entry, task-specific instructions, then relevant supporting resources. A full archive and a focused working context can coexist. Preserve the source; improve the route.

Evidence also argues against declaring success from prompt volume. [Evaluating AGENTS.md, v3](https://arxiv.org/html/2602.11988v3) found no statistically significant task-resolution gains in its tested settings, despite increased cost. Its Python-task scope does not settle this library's needs. It does establish a reason to test guidance rather than assume that more instructions are better.

Long-context evidence is similarly conditional. [Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/) identified position sensitivity in tested models. [Retrieval Quality at Context Limit](https://research.google/pubs/retrieval-quality-at-context-limit/) reports strong simple-fact retrieval for Gemini 2.5 Flash even near its limit. Neither result proves how a reader will reconcile conflicting strategy versions or reconstruct a multi-file engine. Evaluate those tasks directly.

## Design decisions and acceptance criteria

The following are proposed design contracts. Their presence in this report does not assert that all have been implemented.

| Enhancement | What it adds | Acceptance evidence |
| --- | --- | --- |
| Complete inventory plus relevance search | Exact paths and bounded ranked discovery serve different needs. | Inventory coverage at a declared snapshot; retrieval cases with expected source paths. |
| Task routes | A purpose, reading order, authoritative files, prerequisites and output for each common job. | A cold reader can complete a route without guessing which collection is authoritative. |
| Runnable first result | A synthetic, local example establishes an observable outcome before external integrations. | Fresh-environment execution produces the stated artifact with no private credentials. |
| Version and provenance records | Source identity, revision, derivation and supersession remain visible. | Every claimed result links to the exact evidence and its relevant time or version. |
| Capability boundaries | Research code, archived packages, local simulation and operational state are distinguishable. | Examples cannot silently convert a repository snapshot into a live-runtime claim. |
| Retrieval evaluation | Missing, ambiguous and superseded evidence become explicit test cases. | Gold-source recall, false-current answers and justified abstention are measured separately. |

[Aider's inspected repository-map implementation](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repomap.py) demonstrates relevance-ranked code navigation. The transferable principle is to separate a complete inventory from a compact task view. This does not require adopting its dependencies or treating a ranked subset as proof that other material is absent.

## Task routes that exploit the library's breadth

A route should teach a reader to produce a useful result, not merely give a folder tour.

1. **Reconstruct a strategy.** Start with the declared strategy identity and card; trace the exact source, configuration, adapter and recreation note. State which assumptions need data and which behavior can be checked offline. Produce a reproducibility record with all unresolved dependencies.
2. **Understand a forecast.** Trace observations into features, forecasts, assessment and the displayed result. Retain source time, receipt time, usable time and the applicable evaluation horizon. Identify whether the evidence is historical or current.
3. **Compare two implementations.** Establish identities and versions before comparing behavior. Record shared concepts, differing contracts and the observation that would distinguish them. Similar names do not establish equivalence.
4. **Learn a research method.** Pair a source-backed worked example with a transfer problem and a failure case. Keep the complete study available for deeper reading.
5. **Build a local desk example.** Follow the setup contract, run a synthetic scenario and inspect the resulting state. Treat external services and account access as separate integrations.
6. **Audit a public artifact.** Follow its provenance back through the generating activity, inputs and revision. Compare the artifact itself with the claim being made.

Each route can use the same compact template:

```text
Goal:
Use when:
Authoritative entry points:
Required inputs and dependencies:
Read in this order:
Produce:
Verify:
Version/time assumptions:
Missing or ambiguous evidence:
Related deeper material:
```

The template is an original design proposal informed by S01, S05, S09, S10 and S15. It does not override repository instructions or authorize external actions.

## Retrieval and archival fidelity

[LongMemEval](https://arxiv.org/abs/2410.10813) separates memory abilities such as temporal reasoning, updates and abstention. For this library, translate those categories into cases: find the correct historical version, reconcile a superseded note, distinguish two similarly named engines, and say what cannot be established from available evidence.

Start with deterministic lexical and path search over a declared inventory. Return the matched path, match reason and snapshot identity. If semantic retrieval is later added, compare it against that baseline on held-out questions. Additional infrastructure should solve a measured retrieval problem.

A search result is a lead. A document's current location does not make its contents current. A publication date is not a deployment date. A hash establishes file identity, not the truth of every sentence. [W3C PROV-DM](https://www.w3.org/TR/prov-dm/) supplies useful provenance concepts; a simple local schema can capture them without claiming standards compliance.

Preserve historical artifacts and attach explicit errata or supersession links when appropriate. Do not silently rewrite a record of an earlier decision into the present decision. Public examples and provenance should remain free of private identity or account data.

## Evaluate usefulness at the outcome

Provider guidance from [OpenAI](https://developers.openai.com/api/docs/guides/evaluation-best-practices) and [Anthropic](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) recommends task-specific evaluation and calibrated grading. Use several distinct measurements:

- **Repository integrity:** links resolve, inventories match the declared snapshot, and examples execute.
- **Retrieval quality:** expected source coverage, ambiguity handling, version correctness and unsupported absence claims.
- **Task outcome:** a reader produces the requested artifact and correctly explains what the evidence establishes.
- **Efficiency:** elapsed time, calls and actual measured tokens, each with explicit units.
- **Reliability:** repeated trials on the same task, retaining failures and partial outcomes.

For a behavioral comparison, hold the task, model version, tool access, environment and budget constant. Compare the prior and revised repository state on matched cases. Store the task, repository revision, input fixtures, output artifacts, grader rationale and measurements. Freeze a held-out set before tuning. A simulated fixture pass is useful evidence about that fixture, not a general improvement percentage.

[The inspected skill-creator code](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator/scripts/aggregate_benchmark.py) reinforces the need to inspect measurement code: preserve unknown values as unknown, and do not relabel character counts as token counts.

## Adoption sequence

The upgrade has concrete implementation entry points for these ideas:

| Research-backed objective | Repository artifact | What to inspect |
| --- | --- | --- |
| Task-oriented access | [LLM operating guide](../../LLM-OPERATING-GUIDE.md) and [task map](../../REPOSITORY-MAP.json) | Reading routes, requested outputs and authority boundaries. |
| Bounded, source-linked retrieval | [Repository navigator](../../../tools/repo_navigator.py) | Revision selection, source hashes, line ranges and truncation metadata. |
| Reproducible local entry | [Onboarding checker](../../../agentic-trade-desk/skeleton/tools/check_onboarding.py) | Clean-copy execution and the resulting source-bound receipt. |

These links identify implementation surfaces inspected during the upgrade. The
research report does not substitute for their final verification receipts or a
controlled LLM trial.

1. Repair broken entry points and reproducibility contracts.
2. Add task routes and bounded search while preserving complete sources.
3. Add local examples and provenance-aware retrieval cases.
4. Run the repository's deterministic checks on the final tree.
5. Run controlled LLM comparisons before claiming behavioral gains.

This research proposes stronger access, execution and evaluation around the existing library. It does not reduce the archive to a summary, establish trading profitability, or certify live systems.

## Research coverage

The [ledger](SOURCES.json) distinguishes empirical studies, open specifications, provider guidance and inspected implementations. External repositories were inspected at these commits:

| Repository | Inspected commit |
| --- | --- |
| agentskills/agentskills | `83021e2be457a9b6679148719c1f6074f0ad975e` |
| agentsmd/agents.md | `d001185d792eb6402a58e4cbef1c228b309ec25d` |
| anthropics/skills | `2c5958ecac7cee2b583967a2c4981d0f4a75c579` |
| SWE-agent/mini-swe-agent | `04d809ceab9df28f9adaed044884180159172930` |
| Aider-AI/aider | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` |

File-level links and blob hashes are in the ledger. Research access date is 2026-11-07. Later source revisions may differ.
