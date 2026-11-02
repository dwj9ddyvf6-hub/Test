# ROADMAP: routing by question and topic

Read START-HERE.md first (mandatory protocol), then find your topic below. Each section names the exact files to read, in order, and what each file proves. If your topic is not listed, search INDEX.json by path fragment for the topic word, then read the AREA.md or README.md at the top of the area the hits live in.

## Sleeves and strategies

Read in order:

1. docs/SLEEVES.md: the current desk roster, one row per installed sleeve (336 sleeves) with the code file for each. Its machine-readable twin is docs/SLEEVES.json. This proves what the desk runs today.
2. config/sleeves.json: the roster config of record that docs/SLEEVES.md mirrors (336 sleeves, paper trading only). This proves the roster at the source.
3. docs/ALL-SLEEVES.md: the full accounting of every distinct strategy across all desks (651 strategies), deduplicated and arranged by type, each with its recorded algorithm and variants. Twin: docs/ALL-SLEEVES.json. This proves the whole strategy estate, not just the current desk.
4. docs/CATALOG.json: the catalog data, one card per strategy with variants folded in (269 cards, 15 families). This proves the catalogued set and each card's recorded rules summary.
5. strategies/: the card files themselves, one folder per family; family names and counts are in docs/CATALOG.json and INDEX.json. A card proves what one strategy is and where its code lives.
6. sleeves/: the sleeve source code (319 standalone modules at the top, the rest under family folders; family folders are enumerated in INDEX.json). This is the code the cards describe.
7. laz_sleeves/ and aster_sleeves/: thin sleeve entry points over the shared commons in engines/. desk3/: the v3 desk sleeve collection and portfolio branches. adapters/, adapters3/ and integration/: the adapter sets that wire sleeves into the desk (see the desk code section).

## The desk code

Read in order:

1. docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md: architecture before code: product modes, layers, data contracts, build phases, acceptance checklists.
2. docs/THREE-GUIDES-RECONCILIATION.md: the map between the three agent guides: what all three agree on, what only one teaches, and the differences to decide consciously.
3. docs/AGENTIC_TRADE_DESK_GUIDE.md: the field guide: judgment under operation, scoping, evidence grading, forecast grading machinery, catalogued pitfalls.
4. agentic-trade-desk/README.md, then the kit under agentic-trade-desk/ (skeleton/, docs/, templates/): the runnable skeleton with tests and the operating documents. Paper trading only.
5. desk3/: the v3 desk collection (engine modules at the top, sleeves/ and port_b5/ branches). engines/: the shared engine layer (desk3 bridges and enhancements, sleeve commons in engines/aster_sleeves/ and engines/laz_sleeves/, the roster copy at engines/config/sleeves.json, the transport kernel under engines/universe/). Start with engines/SANITIZATION-NOTE.md for what this copy is.
6. integration/: one adapter per sleeve wiring it into the desk runner, plus integration/Femto-lean_Wiring.md. adapters/ and adapters3/: the earlier standalone and Aster adapter sets.
7. config/sleeves.json: the live roster config the desk code runs.

## The terminal

Read in order:

1. index.html: the repository front door: one page that opens both terminal halves.
2. master/: the mirrored Master Terminal edition (content-hashed JS and CSS assets plus its live data files: deskview.json, edition.json, market.json, pulse.json, sleeves.json, positions.json, charts.json, panels.json, publish-manifest.json). These files prove what the Master half displays and the data it displays it from.
3. terminal-lineup/THE-70-TOOLS.md: the public terminal lineup manifest: the tools and what each one does.
4. terminal-lineup/FORECAST-ENGINES-30.md: the 30 forecast engines, named.
5. terminal-lineup/site/: the tool site (1,915 files): 104 tool pages, each in its own folder with its page and its data, plus the shared code and refresh scripts at the top of site/. A tool folder proves what that tool shows and the data behind it.
6. terminal-lineup/forecast/: the forecast engine code, registry (forecast/registry.json), grading and ledger machinery, and tests (102 files). This proves how forecasts are issued, settled and graded.

## Engines and tools

Read in order:

1. terminal-lineup/forecast/registry.json: the registry of the 30 forecast engines. Then the engine code and grading machinery in terminal-lineup/forecast/.
2. engines/: the shared engine code listed in the desk code section above.
3. tools/build_repo_index.py: the repository's own tooling: the generator that produces INDEX.json and INDEX.md from the live tree.
4. educational/shipyard-engines/: the educational engine collection, kept whole.
5. indicator/BB_RSI_Divergence_Algorithm.md and pine/BB_RSI_Divergence_Indicator.pine: the indicator contract and its TradingView source; the research note is docs/BB_RSI_Divergence_Research.md.
6. psychology-engine/ and docs/research/psychology-engine-2026-10-30/: the two psychology engines (see the research section).

## Research studies

Every study in the repository, named. Under docs/research/:

1. agent-methods (docs/research/agent-methods/2026-10-31/, 4 files): the derived agent-methods study. Read its README.md first, then SOURCE-DERIVED-METHODS.md (the methods), then github-research-complete-20261031.md and github-research-public-coverage-20261031.json (the sweep coverage record). These are summary artefacts; the primary records are the next entry.
2. llm-enhancement-extraction-20261031 (docs/research/llm-enhancement-extraction-20261031/, 26 files): the complete primary extraction records behind the agent-methods study: the three pass reports (REPORT.md, REPORT-PASS2.md, REPORT-PASS3.md), the six cluster extractions (CLUSTER-1-memory.md, CLUSTER-2-skills-agents.md, CLUSTER-3-proactivity.md, CLUSTER-4-prompting.md, CLUSTER-5-extensions.md, CLUSTER-6-platform-lists.md), the six second-pass deep-dives (PASS2-1-superpowers.md through PASS2-6-expansion.md), the five third-pass deep-dives (PASS3-1-issues-releases-tests.md through PASS3-5-practitioner.md), the three verification reports (VERIFY.md, VERIFY-PASS2.md, VERIFY-PASS3.md), and the three doctrine-landing records (DOCTRINE-LANDING-20261031.md, DOCTRINE-LANDING-ROUND2-20261031.md, DOCTRINE-LANDING-ROUND3-20261031.md). These prove, per source, what the enhancement sweep actually found.
3. master-traders-20261029 (docs/research/master-traders-20261029/, 2 files): report.md, the master trader playbook study, with notes/sources-used.md proving its sources.
4. midna-trader-formation-20261029 (docs/research/midna-trader-formation-20261029/, 6 files): FORMATION.md first, then great-traders.md, hedge-funds.md, quants.md, cognition-and-steps.md and MEMORY-SYSTEM.md: the trader formation study.
5. onebar-family-2026-10-30 (docs/research/onebar-family-2026-10-30/ANALYSIS.md, 1 file): the one-bar family analysis.
6. psychology-engine-2026-10-30 (docs/research/psychology-engine-2026-10-30/, 33 files): the live nine-gauge psychology engine's design, theory and measurement study (ENGINE-DESIGN.md, STUDY-THEORY.md, STUDY-MEASUREMENT.md) with its engine code under engine/. The second psychology engine is the standalone package at psychology-engine/ (124 files: engine/, audit/, research/, report/; start at psychology-engine/README.md and PUBLIC_VALIDATION.md).
7. technical-analysis-mastery-20261030 (docs/research/technical-analysis-mastery-20261030/, 28 files): the chart-reading mastery study: census/ (the canon census) and sections/ (the working method), with the combined texts at its top.

Under research/:

8. master-trader-study-2026-10-29 (research/master-trader-study-2026-10-29/, 3 files): study.md and README.md, plus the Word form of the study.
9. technical-analysis-study-2026-10-30 (research/technical-analysis-study-2026-10-30/, 6 files): the study and practice atlas in Markdown, Word and PDF, the full archive ZIP, and SHA256SUMS.txt proving the archive's contents.

Topic shortcuts inside the research: memory systems and agent memory: CLUSTER-1-memory.md and PASS2-3-memory-internals.md in the sweep records. Skills and agent design: CLUSTER-2-skills-agents.md, PASS2-1-superpowers.md, PASS2-2-ecc.md. Proactivity: CLUSTER-3-proactivity.md, PASS2-4-proactivity-internals.md. Prompting: CLUSTER-4-prompting.md, PASS2-5-prompting-corpus.md. Extensions and platforms: CLUSTER-5-extensions.md, CLUSTER-6-platform-lists.md, PASS2-6-expansion.md, PASS3-1 through PASS3-5. What was adopted as operating doctrine: the three DOCTRINE-LANDING files.

## Packages and vendor corpora

Read in order:

1. INDEX.md, packages entry point: the per-author, per-package breakdown with file counts. This proves what packages exist before you open any of them.
2. packages/claude/ (1,105 files): the master desk packages: terminal builder and public app, sleeve port library, parity tools, feed library, forecast system and more, one folder per package.
3. packages/ausar/ (791 files): the Aster desk packages: the R13 baseline and R15 execution packages, the forecast-engines lab, research terminals and rulebooks.
4. packages/grokbot/ (31 files): the md2 master-desk package, the Q07 and RL64 engines, and small tools.
5. Inside any package, read its own README or entry doc first and check its provenance and version before treating it as current: packages are kept whole as contributed, and a historical package is not the current runtime.

## Proofs and tests

Read in order:

1. proof/install/: one JSON install-proof receipt per installed sleeve (22 receipts). A receipt proves what was installed and verified for that sleeve.
2. tests/: the repository-level regression blocker tests (8 files): one-bar, PRZM, Raschke event feed, CCI correlation, Teddy ORB, Trullas variants, and the two VIX hedge blockers. A test file proves the behavior its blockers assert.
3. docs/VERIFY.md and docs/verify/: the verification notes: the code lines each strategy card's rules were read from, and where each copied file came from.
4. INDEX.json: the inventory proof: every file at the indexed commit with its blob sha and size. If a file is claimed to be in this repository, its INDEX.json entry is the proof.

## If your question is not routed here

Search INDEX.json by path fragment for your topic word. Then read the AREA.md or README.md at the top of the area the hits live in, and the ROADMAP section closest to your topic. Concluding that something is absent without an INDEX.json search is a protocol violation (see START-HERE.md).
