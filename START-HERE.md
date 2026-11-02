# START HERE: mandatory first read

You are an LLM (or a person) arriving cold at a large repository: 7,226 files in 24 top-level areas. Readers who start from the README alone, or from the strategy catalog alone, miss about three quarters of what is here, because the catalog covers only one collection (269 strategy cards) out of 7,226 files. This file exists so that cannot happen again. Follow the protocol below before answering anything about this repository.

## Mandatory reading protocol

Do these steps in order, in full, before answering any question about this repository:

1. Read this file, START-HERE.md, completely.
2. Read INDEX.md: the prose map of the whole repository, with per-area counts and entry points into every major collection.
3. Read the ROADMAP.md section for your topic: it names the exact files to read, in order, and what each file proves.
4. Read the area entry doc for each area you touch: the README.md or AREA.md at the top of that area's folder.
5. Only then open the specific files your question needs. Use INDEX.json (every file, with its path, size and blob sha) to find exact paths.

## Anti-miss rules (binding)

- Never answer from README.md alone. README.md is the strategy catalog front page; it is not the map of the repository.
- Never treat docs/CATALOG.json as the catalog of the repository. It catalogs 269 strategy cards in one collection only. The repository also holds the desk code, the terminal, the engines, the tools, the packages, the proofs and the research studies, none of which are in CATALOG.json.
- AGENTS.md is guardrails for working safely in this repository. It is not a map and it does not replace steps 1 to 4.
- If something is not found, search INDEX.json by path fragment before concluding it is absent. Absence from a prose page is not absence from the repository.
- If a count matters, take it from INDEX.json or INDEX.md at the indexed commit, and say which commit you counted. Check the indexed commit in INDEX.md against the branch HEAD before quoting counts: the index describes the commit it names, and later mirror commits can move data files (notably under master/) past it.
- Every top-level area is listed in the map below. If your answer touches an area you have not read the entry doc for, say so instead of guessing.

## What this repository is

A public library of trading strategies and the desk software around them: strategy cards, sleeve source code, recreation notes that let anyone rebuild a strategy from its recorded rules, the public terminal and its tool pages, forecast and psychology engines, whole packages from the desk's builders, install proofs, tests, and the research studies the desks were built on. Paper trading only.

## Complete map of every top-level area

Counts are files (blobs) at the index commit named in INDEX.md, regenerated as part of the discoverability cure that added this file. Total: 7,226 files.

| Area | Files | What it is |
| --- | ---: | --- |
| (root) | 13 | Repository root: the entry files (START-HERE.md, ROADMAP.md, INDEX.md, INDEX.json, README.md, AGENTS.md, index.html), and the build notes for the newest sleeve families. |
| adapters | 31 | Standalone desk adapters for recently built sleeves (one-bar, Trullas variants, Teddy ORB, PRZM and others), one file per sleeve. |
| adapters3 | 266 | The Aster adapter set: one adapter module per Aster sleeve variant, mirroring the sleeves they wire in. |
| agentic-trade-desk | 55 | The operational kit for running an agentic trade desk: a runnable skeleton, docs and templates. Paper trading only. |
| aster_sleeves | 12 | Aster sleeve entry points (thin wrappers over the shared engine commons). |
| config | 2 | Desk configuration. config/sleeves.json is the live roster config mirrored into this repository (336 sleeves, paper trading only). |
| desk3 | 51 | The desk3 sleeve collection and its portfolio branches: the v3 desk engine modules, sleeve modules and portfolio books. |
| docs | 1207 | Documentation at scale: the strategy catalog data, the current-desk and all-strategies accountings, one algorithm and recreation document per strategy, verification notes, and the research collections under docs/research/. |
| educational | 40 | The shipyard engines collection (educational/shipyard-engines/): self-contained educational trading engines and their supporting material, kept whole. |
| engines | 20 | Shared engine code: desk3 bridges and enhancements, sleeve commons, the roster config copy and a transport kernel. |
| indicator | 2 | A single indicator package: the BB/RSI divergence indicator algorithm contract (its Pine Script source is under pine/). |
| integration | 328 | Integration adapters that wire each sleeve into the desk runner, plus the wiring guide. |
| laz_sleeves | 11 | Lazarus sleeve entry points (thin wrappers over the shared engine commons). |
| master | 75 | The mirrored Master Terminal edition: the combined terminal's Master half as published web assets (content-hashed JS and CSS) plus its live data files (deskview.json, edition.json, market.json, pulse.json, sleeves.json, positions.json, charts.json, panels.json, publish-manifest.json). Reached from the repository front door, index.html. |
| packages | 1928 | Whole packages contributed by the desk's builders, grouped by author (ausar, claude, grokbot), kept whole rather than cherry-picked. |
| pine | 2 | Pine Script sources (the BB/RSI divergence indicator for TradingView). |
| proof | 23 | Install proof records: one JSON receipt per installed sleeve under proof/install/. |
| psychology-engine | 124 | The standalone market-psychology engine package: engine code, audits, research and reports. One of the two psychology engines in this repository. |
| research | 10 | Standalone research works: the technical analysis study and practice archive, and the master trader study, in Markdown, PDF, DOCX and ZIP forms. |
| sleeves | 571 | Sleeve source code grouped by family, plus standalone sleeve modules at the top of the folder. |
| strategies | 270 | Strategy cards: one card per catalogued strategy (269 cards), grouped by family folder. The family folders are enumerated in docs/CATALOG.json and in INDEX.json. |
| terminal-lineup | 2174 | The public terminal lineup: the tool site under site/ (104 tool pages), the forecast engines under forecast/ (30 engines), build records, design documents, the oracle and the workflow scripts that built the tools. |
| tests | 9 | Repository-level regression blocker tests. |
| tools | 2 | Repository tooling. Home of build_repo_index.py, the generator that produces INDEX.json and INDEX.md. |

## Where to go next

- By topic: ROADMAP.md routes by question (sleeves and strategies, desk code, terminal, engines and tools, research studies, packages, proofs and tests) with the exact files to read in order.
- By collection: INDEX.md lists entry points into every major collection, including the per-author breakdown of packages/ and every research study under docs/research/ and research/.
- By exact path: INDEX.json lists every one of the 7,226 files with size and blob sha.
