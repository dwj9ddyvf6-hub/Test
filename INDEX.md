# Repository index

Start here. This file is the map of the whole repository for a reader (human or LLM) arriving cold. Its machine-readable twin is [INDEX.json](INDEX.json), generated from the same inventory by [tools/build_repo_index.py](tools/build_repo_index.py).

Total files indexed: 6274

Indexed commit: `8e3ff93d80b0abbe3184bd8383d2fd2b1f45c8ca`. Generated at: 2026-10-31T21:14:10Z. Total size of indexed files (self entries excluded, their sizes are null): 210710778 bytes.

## What this repository is

A public library of trading strategies and the desk software around them: strategy cards, sleeve source code, recreation notes that let anyone rebuild a strategy from its recorded rules, the public terminal tool lineup, forecast and psychology engines, research works, and the guides that teach an agent or a person how to build a desk like this. Paper trading only.

## Reading order

1. This file, INDEX.md: the map.
2. [INDEX.json](INDEX.json): every file, when you need the exact path, size or blob sha of anything.
3. [README.md](README.md): the strategy catalog front page.
4. [docs/CATALOG.json](docs/CATALOG.json): the catalog data, one card per strategy with variants folded in; the cards themselves live under strategies/.
5. [docs/ALL-SLEEVES.md](docs/ALL-SLEEVES.md): the full accounting of every distinct strategy across all desks, with its machine-readable twin docs/ALL-SLEEVES.json.
6. [docs/SLEEVES.md](docs/SLEEVES.md): the current desk roster, one row per installed sleeve, mirrored from config/sleeves.json.
7. The research collections under docs/research/ and research/ (see entry points below).
8. [terminal-lineup/THE-70-TOOLS.md](terminal-lineup/THE-70-TOOLS.md): the public terminal lineup and its tools, then the site and forecast code beneath it.

## Map of every top-level area

| Area | Files | Bytes | What it is |
| --- | ---: | ---: | --- |
| (root) | 9 | 241157 | Repository root: the README catalog front page, this index, the agent rules file, and the build notes for the newest sleeve families. |
| adapters | 29 | 111436 | Standalone desk adapters for recently built sleeves (one-bar, Trullas variants, Teddy ORB, PRZM and others), one file per sleeve. |
| adapters3 | 265 | 133233 | The Aster adapter set: one adapter module per Aster sleeve variant, mirroring the sleeves they wire in. |
| agentic-trade-desk | 55 | 280328 | The operational kit for running an agentic trade desk: a runnable skeleton, docs and templates. Paper trading only. |
| aster_sleeves | 10 | 5105 | Aster sleeve entry points (thin wrappers over the shared engine commons). |
| config | 1 | 146936 | Desk configuration. config/sleeves.json is the live roster config mirrored into this repository. |
| desk3 | 50 | 431768 | The desk3 sleeve collection and its portfolio branches. |
| docs | 1165 | 15695249 | Documentation at scale: the strategy catalog data, the current-desk and all-strategies accountings, one algorithm and recreation document per strategy, verification notes, and the research collections under docs/research/. |
| engines | 19 | 313734 | Shared engine code: desk3 bridges and enhancements, sleeve commons, the roster config copy and a transport kernel. |
| indicator | 1 | 8192 | A single indicator package. |
| integration | 327 | 360381 | Integration adapters that wire each sleeve into the desk runner, plus the wiring guide. |
| laz_sleeves | 10 | 13080 | Lazarus sleeve entry points (thin wrappers over the shared engine commons). |
| packages | 1927 | 117474045 | Whole packages contributed by the desk's builders, grouped by author. See the packages entry point in INDEX.md for the per-author breakdown. |
| pine | 1 | 9994 | Pine Script sources. |
| proof | 22 | 62140 | Install proof records: one JSON receipt per installed sleeve under proof/install/. |
| psychology-engine | 124 | 5023354 | The standalone market-psychology engine package: engine code, audits, research and reports. One of the two psychology engines in this repository. |
| research | 6 | 16775075 | Standalone research works. Home of the technical analysis study and practice archive (Markdown, PDF, DOCX and ZIP forms of the same work). |
| sleeves | 569 | 5584627 | Sleeve source code grouped by family, plus standalone sleeve modules at the top of the folder. |
| strategies | 269 | 527337 | Strategy cards: one card per catalogued strategy, grouped by family folder. The family folders are enumerated in docs/CATALOG.json and in INDEX.json; they are not repeated in this prose map. |
| terminal-lineup | 1406 | 47409099 | The public terminal lineup: the tool site under site/, the forecast engines under forecast/, build records, design documents, the oracle and the workflow scripts that built the tools. |
| tests | 8 | 104508 | Repository-level regression blocker tests. |
| tools | 1 | 0 | Repository tooling. Home of build_repo_index.py, the generator that produces INDEX.json and INDEX.md. |

## Entry points into every major collection

### Strategies catalog

- [docs/CATALOG.json](docs/CATALOG.json): catalog data for the strategies, one card per strategy.
- strategies/: the card files themselves, one folder per family. Family folder names and counts are in INDEX.json.
- [docs/ALL-SLEEVES.md](docs/ALL-SLEEVES.md) and docs/ALL-SLEEVES.json: every distinct strategy across all desks, deduplicated, arranged by type.
- docs/: one algorithm document and one recreation document per strategy sit directly under docs/ alongside the catalog files; their exact names are in INDEX.json.

### Sleeves

- sleeves/: sleeve source code, grouped by family folder with standalone modules at the top.
- [config/sleeves.json](config/sleeves.json): the roster config the current-desk view mirrors.
- [docs/SLEEVES.md](docs/SLEEVES.md) and docs/SLEEVES.json: the installed roster, one row per sleeve with its code file.
- aster_sleeves/ and laz_sleeves/: thin sleeve entry points over the shared commons in engines/.
- desk3/ and engines/desk3/: the desk3 collection and its engine bridges.

### Packages by author

- packages/ausar/ (791 files): aster-desk-r13-baseline (267), aster-execution-r15 (312), ausar-archive-rulebooks (16), codex-repo-hosted-snapshot-site (10), forecast-engines-lab (36), rea-register-builder-scripts (14), shipyard-forecast-engine-integration (4), shipyard-live-site-runtime (33), shipyard-research-terminal (80), silicon-market-terminal (14), tastytrade-readonly-cli (5).
- packages/claude/ (1105 files): femto-repo-terminal-surfaces (262), femtolean-vendor-forecast-branch (30), master-desk-ai-tools (12), master-desk-analysis (9), master-desk-feedlib (64), master-desk-forecast-system (37), master-desk-lab (17), master-desk-learn-scorecards (11), master-desk-morgue-engine (34), master-desk-parity-tools (142), master-desk-picker (7), master-desk-record-ext (10), master-desk-sleeve-port-library (301), master-desk-terminal-builder (104), master-terminal-public-app (65).
- packages/grokbot/ (31 files): backup-sync (1), kz-check (1), master-desk-md2 (23), q07-1w-swing-lz (2), rl64 (3), trullas-replay (1).

### Docs and research

- docs/: catalog, accountings, per-strategy algorithm and recreation documents, guides and verification notes.
- docs/verify/: verification notes.
- docs/research/: the collected research works, including the two below.
- Psychology engine, first of two: [psychology-engine/](psychology-engine/README.md), the standalone package with engine/, audit/, research/ and report/ sections.
- Psychology engine, second of two: docs/research/psychology-engine-2026-10-30/, the research build with its own engine under docs/research/psychology-engine-2026-10-30/engine/ and the study papers beside it.
- Technical analysis, first of two: docs/research/technical-analysis-mastery-20261030/, the mastery work with census/ and sections/ folders and the combined texts at its top.
- Technical analysis, second of two: research/technical-analysis-study-2026-10-30/, the study and practice archive in Markdown, PDF, DOCX and ZIP forms.
- docs/research/onebar-family-2026-10-30/: the one-bar family analysis.

### Terminal lineup

- [terminal-lineup/THE-70-TOOLS.md](terminal-lineup/THE-70-TOOLS.md): the lineup manifest.
- terminal-lineup/site/ (1164 files): the public tool site; each tool has its own folder with its page and data, and the refresh scripts sit at the top of site/.
- terminal-lineup/forecast/ (88 files): the forecast engines, their registry, grading and ledger code, and their tests. See also terminal-lineup/FORECAST-ENGINES-30.md.
- terminal-lineup/ root: design documents, bug logs, build progress files and 110 workflow scripts that built the tools.
- terminal-lineup/oracle/: the oracle provenance record. terminal-lineup/records/: build and search records. terminal-lineup/specs/: specifications.

### Integration, proof and engines

- integration/: one adapter per sleeve wiring it into the desk runner, plus integration/Femto-lean_Wiring.md.
- adapters/ and adapters3/: standalone and Aster adapter sets.
- proof/install/: one JSON install-proof receipt per installed sleeve.
- engines/: shared engine code (desk3 bridges, sleeve commons, roster config copy, transport kernel).
- tests/: repository-level regression blocker tests.
- agentic-trade-desk/: the operational kit and runnable skeleton; start at agentic-trade-desk/README.md.

## Coverage statement

Every file present at the indexed commit (`8e3ff93d80b0abbe3184bd8383d2fd2b1f45c8ca`) is listed in INDEX.json: 6274 entries in total, covering every blob in the tree at that commit. The three index files themselves (INDEX.md, INDEX.json, tools/build_repo_index.py) are the only entries whose sha and size are null; they are marked "self": true because a file cannot contain its own hash. All other entries carry the exact git blob sha and size from the tree. Nothing at the indexed commit is omitted, and no path is listed that was not in the tree, apart from the self entries for the two index files created by the generation itself.

## How to regenerate

Run the generator from a checkout or any folder:

    python3 tools/build_repo_index.py --out-dir .

It resolves the default branch, fetches that branch's HEAD commit and its full recursive tree from the GitHub API (set GITHUB_TOKEN to authenticate), and rewrites INDEX.json and INDEX.md deterministically: same commit in, byte-identical files out. A saved tree snapshot can be indexed offline with --tree-json. Uploads to this repository go through the repository's gated contents route only, never raw git pushes from an index run.
