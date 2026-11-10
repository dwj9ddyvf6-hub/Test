# Repository index

The complete measured file inventory and collection map. [INDEX.json](INDEX.json) is the machine-readable twin; [docs/REPOSITORY-MAP.json](docs/REPOSITORY-MAP.json) supplies curated meanings and task routes when present. No catalog or prose page substitutes for the full inventory.

Total files indexed: 8318

Indexed commit: `444aac90283e4f386a1428995089f11dd1346caf`. Source commit timestamp: 2026-11-10T21:33:33Z.
Total indexed bytes: 1112366197 (only the two generated index outputs have null hashes and sizes).

## What this repository is

A public, versioned library of strategy cards, implementation copies, research studies, educational engines, terminal snapshots and paper-desk engineering guides. Its contents preserve multiple independent systems and historical states. A committed file or historical receipt does not prove a currently active service, feed, trading account, deployment or profitable strategy.

## Reading order and first useful actions

1. [START-HERE.md](START-HERE.md): the entry protocol and evidence boundaries.
2. This map, then the relevant [ROADMAP.md](ROADMAP.md) topic and area entrypoint.
3. [docs/LLM-OPERATING-GUIDE.md](docs/LLM-OPERATING-GUIDE.md): source-to-answer workflows, examples and bounded checks.
4. Use the offline navigator to find exact paths or build a bounded reading packet. It reads repository content; it does not activate any service.

```sh
python3 tools/repo_navigator.py search "tensor"
python3 tools/repo_navigator.py route "forecast engines"
python3 tools/repo_navigator.py check
```

For manual readers, [docs/CATALOG.json](docs/CATALOG.json) catalogs strategy cards; [docs/ALL-SLEEVES.json](docs/ALL-SLEEVES.json) is the broader deduplicated accounting; [docs/SLEEVES.json](docs/SLEEVES.json) describes the committed roster. They have different denominators and purposes.

## Map of every top-level area

Counts and bytes below are derived from the selected Git tree, not copied from older prose. Curated descriptions do not determine coverage: newly added areas remain visible even before a route is written.

| Area | Files | Bytes | Purpose and entrypoints |
| --- | ---: | ---: | --- |
| (root) | 14 | 275999 | Repository entrypoints, complete inventories and family build records. |
| .github | 1 | 2539 | New or unclassified area: inspect its files and add a curated route. |
| adapters | 31 | 118837 | Standalone adapters for recorded sleeve builds. [adapters/AREA.md](adapters/AREA.md) |
| adapters3 | 266 | 133931 | The Aster adapter collection, paired with its sleeve variants. [adapters3/AREA.md](adapters3/AREA.md) |
| agentic-trade-desk | 56 | 293028 | Paper-desk engineering guide, offline skeleton and templates. [agentic-trade-desk/README.md](agentic-trade-desk/README.md) |
| aster_sleeves | 12 | 22813 | Aster entrypoints over the shared engine commons. [aster_sleeves/AREA.md](aster_sleeves/AREA.md) |
| config | 2 | 147700 | Versioned paper-only roster configuration; a snapshot, not current-runtime proof. [config/AREA.md](config/AREA.md) |
| desk3 | 51 | 432587 | Packaged desk-engine modules, sleeves and portfolio branches. [desk3/AREA.md](desk3/AREA.md) |
| docs | 1222 | 21421462 | Catalogs, strategy accounting, recreation contracts, verification and research. [docs/AREA.md](docs/AREA.md) |
| educational | 40 | 687906 | Preserved standalone educational engine packages and their boundaries. [educational/AREA.md](educational/AREA.md) |
| engines | 20 | 314575 | Shared-engine copies, bridges, configuration snapshot and sanitization provenance. [engines/AREA.md](engines/AREA.md) |
| indicator | 2 | 9040 | Indicator algorithm contracts linked to the Pine sources. [indicator/AREA.md](indicator/AREA.md) |
| integration | 328 | 361125 | Integration adapters and their recorded wiring guide. [integration/AREA.md](integration/AREA.md) |
| laz_sleeves | 11 | 13767 | Lazarus entrypoints over the shared engine commons. [laz_sleeves/AREA.md](laz_sleeves/AREA.md) |
| master | 104 | 26962226 | Externally mirrored terminal assets and dated data; check producer clocks. Mirror updates may replace this directory wholesale. |
| packages | 1928 | 117474908 | Whole contributed packages retained with source identity and version distinctions. [packages/AREA.md](packages/AREA.md) |
| pine | 2 | 10723 | Pine Script sources for the recorded indicator contracts. [pine/AREA.md](pine/AREA.md) |
| proof | 23 | 62879 | Historical install receipts; their scopes and dates bound what they demonstrate. [proof/AREA.md](proof/AREA.md) |
| psychology-engine | 124 | 5023354 | Standalone market-psychology research and reference implementation. [psychology-engine/README.md](psychology-engine/README.md) |
| research | 10 | 16948760 | Preserved standalone studies, documents and practice archives. [research/AREA.md](research/AREA.md) |
| sleeves | 571 | 5590203 | Strategy implementation copies, grouped by family and standalone modules. [sleeves/AREA.md](sleeves/AREA.md) |
| strategies | 270 | 528417 | Strategy cards; the catalog is one collection within the repository. [strategies/AREA.md](strategies/AREA.md) |
| terminal-lineup | 3216 | 915339007 | Tool-site snapshots, forecast research, grading code and build records. [terminal-lineup/AREA.md](terminal-lineup/AREA.md) |
| tests | 11 | 130527 | Repository-level test sources; executing a test is separate from reading it. [tests/AREA.md](tests/AREA.md) |
| tools | 3 | 59884 | Offline navigation and inventory tools for readers and maintainers. [tools/AREA.md](tools/AREA.md) |

## Packages by contributing desk

Packages are retained whole. A package's README, manifest and source version determine its scope; the most recent directory name is not authority to replace another implementation.

- **ausar**: [aster-desk-r13-baseline](packages/ausar/aster-desk-r13-baseline/) (267), [aster-execution-r15](packages/ausar/aster-execution-r15/) (312), [ausar-archive-rulebooks](packages/ausar/ausar-archive-rulebooks/) (16), [codex-repo-hosted-snapshot-site](packages/ausar/codex-repo-hosted-snapshot-site/) (10), [forecast-engines-lab](packages/ausar/forecast-engines-lab/) (36), [rea-register-builder-scripts](packages/ausar/rea-register-builder-scripts/) (14), [shipyard-forecast-engine-integration](packages/ausar/shipyard-forecast-engine-integration/) (4), [shipyard-live-site-runtime](packages/ausar/shipyard-live-site-runtime/) (33), [shipyard-research-terminal](packages/ausar/shipyard-research-terminal/) (80), [silicon-market-terminal](packages/ausar/silicon-market-terminal/) (14), [tastytrade-readonly-cli](packages/ausar/tastytrade-readonly-cli/) (5).
- **claude**: [femto-repo-terminal-surfaces](packages/claude/femto-repo-terminal-surfaces/) (262), [femtolean-vendor-forecast-branch](packages/claude/femtolean-vendor-forecast-branch/) (30), [master-desk-ai-tools](packages/claude/master-desk-ai-tools/) (12), [master-desk-analysis](packages/claude/master-desk-analysis/) (9), [master-desk-feedlib](packages/claude/master-desk-feedlib/) (64), [master-desk-forecast-system](packages/claude/master-desk-forecast-system/) (37), [master-desk-lab](packages/claude/master-desk-lab/) (17), [master-desk-learn-scorecards](packages/claude/master-desk-learn-scorecards/) (11), [master-desk-morgue-engine](packages/claude/master-desk-morgue-engine/) (34), [master-desk-parity-tools](packages/claude/master-desk-parity-tools/) (142), [master-desk-picker](packages/claude/master-desk-picker/) (7), [master-desk-record-ext](packages/claude/master-desk-record-ext/) (10), [master-desk-sleeve-port-library](packages/claude/master-desk-sleeve-port-library/) (301), [master-desk-terminal-builder](packages/claude/master-desk-terminal-builder/) (104), [master-terminal-public-app](packages/claude/master-terminal-public-app/) (65).
- **grokbot**: [backup-sync](packages/grokbot/backup-sync/) (1), [kz-check](packages/grokbot/kz-check/) (1), [master-desk-md2](packages/grokbot/master-desk-md2/) (23), [q07-1w-swing-lz](packages/grokbot/q07-1w-swing-lz/) (2), [rl64](packages/grokbot/rl64/) (3), [trullas-replay](packages/grokbot/trullas-replay/) (1).

## Research collections, enumerated from the tree

These are independent source collections unless their own records establish a lineage. Coverage, conclusions and adoption status belong to each study's dated evidence. Listing a collection does not claim a fresh scientific validation.

- [docs/research/agent-methods/](docs/research/agent-methods/) — 4 files. Read: [docs/research/agent-methods/2026-10-31/README.md](docs/research/agent-methods/2026-10-31/README.md)
- [docs/research/llm-enhancement-extraction-20261031/](docs/research/llm-enhancement-extraction-20261031/) — 26 files. Read: [docs/research/llm-enhancement-extraction-20261031/REPORT.md](docs/research/llm-enhancement-extraction-20261031/REPORT.md)
- [docs/research/master-traders-20261029/](docs/research/master-traders-20261029/) — 2 files. Read: [docs/research/master-traders-20261029/report.md](docs/research/master-traders-20261029/report.md)
- [docs/research/midna-trader-formation-20261029/](docs/research/midna-trader-formation-20261029/) — 6 files. Read: [docs/research/midna-trader-formation-20261029/FORMATION.md](docs/research/midna-trader-formation-20261029/FORMATION.md)
- [docs/research/obsidian-second-brain-sweep-20261102/](docs/research/obsidian-second-brain-sweep-20261102/) — 10 files. Open the directory, then search INDEX.json for its files.
- [docs/research/onebar-family-2026-10-30/](docs/research/onebar-family-2026-10-30/) — 1 files. Read: [docs/research/onebar-family-2026-10-30/ANALYSIS.md](docs/research/onebar-family-2026-10-30/ANALYSIS.md)
- [docs/research/psychology-engine-2026-10-30/](docs/research/psychology-engine-2026-10-30/) — 33 files. Read: [docs/research/psychology-engine-2026-10-30/ENGINE-DESIGN.md](docs/research/psychology-engine-2026-10-30/ENGINE-DESIGN.md)
- [docs/research/repository-enhancement-2026-11-07/](docs/research/repository-enhancement-2026-11-07/) — 2 files. Read: [docs/research/repository-enhancement-2026-11-07/README.md](docs/research/repository-enhancement-2026-11-07/README.md)
- [docs/research/technical-analysis-mastery-20261030/](docs/research/technical-analysis-mastery-20261030/) — 28 files. Open the directory, then search INDEX.json for its files.
- [research/master-trader-study-2026-10-29/](research/master-trader-study-2026-10-29/) — 3 files. Read: [research/master-trader-study-2026-10-29/README.md](research/master-trader-study-2026-10-29/README.md)
- [research/technical-analysis-study-2026-10-30/](research/technical-analysis-study-2026-10-30/) — 6 files. Read: [research/technical-analysis-study-2026-10-30/README.md](research/technical-analysis-study-2026-10-30/README.md)

## Educational and reference implementations

- [psychology-engine/README.md](psychology-engine/README.md): the standalone psychology research/reference package, release notes and offline checks.
- [docs/research/psychology-engine-2026-10-30/](docs/research/psychology-engine-2026-10-30/): the separate nine-gauge study and implementation snapshot. Do not merge their status or evidence.
- [educational/shipyard-engines/](educational/shipyard-engines/) — 39 files. [educational/shipyard-engines/2026-11-02/README.md](educational/shipyard-engines/2026-11-02/README.md)

## Terminal, implementation and evidence routes

- [terminal-lineup/THE-70-TOOLS.md](terminal-lineup/THE-70-TOOLS.md) and [terminal-lineup/FORECAST-ENGINES-30.md](terminal-lineup/FORECAST-ENGINES-30.md) retain historical titles; the tree and registry determine the captured contents.
- [terminal-lineup/site/](terminal-lineup/site/) — 2923 files: tool pages, assets, source and dated data.
- [terminal-lineup/forecast/](terminal-lineup/forecast/) — 129 files: forecast implementations, registry, grading and tests.
- [terminal-lineup/records/](terminal-lineup/records/) — 16 files: historical build and source-discovery records.
- [master/](master/) — 104 files: externally mirrored terminal assets and snapshots.
- [docs/VERIFY.md](docs/VERIFY.md), [docs/verify/](docs/verify/) and [proof/install/](proof/install/): source attribution and historical receipts. Check the captured source, date and exact claim before relying on them.
- [engines/SANITIZATION-NOTE.md](engines/SANITIZATION-NOTE.md): disclosed representation differences in copied source.
- [agentic-trade-desk/README.md](agentic-trade-desk/README.md): paper-desk architecture, offline skeleton and operational guide; it does not authorize an account or order.
- [ROADMAP.md](ROADMAP.md): the cross-directory Tensor route and other source-to-claim reading sequences.

## Coverage and preservation contract

INDEX.json has 8318 sorted file entries. All source blobs are included with exact Git blob hashes and byte sizes. Only `INDEX.md` and `INDEX.json` are generated self entries, with null hashes/sizes; `tools/build_repo_index.py` is ordinary hashed source. When an output is absent from the selected source tree, its marked self entry anticipates the generated file and is not a claim it was already committed.

A file inventory proves paths and byte identity, not semantic correctness or runtime behavior. Unsupported submodules, truncated snapshots, duplicate paths, unsafe paths and missing hashes/sizes fail explicitly rather than yielding a partial inventory described as complete. The index does not enumerate files inside archives; use their own manifests and the artifact's documented extraction procedure.

## Reproduce and check

```sh
# Exact committed source; no GitHub connection required.
python3 tools/build_repo_index.py --local-repo . --ref HEAD --out-dir .
# Read-only comparison: catches missing/new paths, changed bytes, counts and prose drift.
python3 tools/build_repo_index.py --local-repo . --ref HEAD --out-dir . --check
# Pre-commit candidate; does not mutate the Git index or write Git objects.
python3 tools/build_repo_index.py --local-repo . --staged --out-dir /tmp/test-index
# Original API and offline-snapshot modes remain available.
python3 tools/build_repo_index.py --branch main --out-dir /tmp/test-index-api
python3 tools/build_repo_index.py --tree-json snapshot.json --out-dir /tmp/test-index-snapshot
```

For a published inventory, commit source changes first, generate from that pinned source commit, and then commit the two generated outputs. The later index-only commit may have a different HEAD while every non-self source hash still matches; `--check` verifies those hashes instead of requiring an impossible self-referential commit ID. An explicit `--map-file` can supply annotations for a saved snapshot. Generation never pushes, posts, activates services or changes trading state.
