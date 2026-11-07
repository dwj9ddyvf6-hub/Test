# Start here: turn the library into a useful answer

**Test is the public source and research library.** It preserves strategy cards, implementation copies, reconstruction notes, independent studies, educational engines, terminal snapshots and paper-desk engineering guides. [InfinityBlade Engineering Doctrine](https://github.com/dwj9ddyvf6-hub/InfinityBlade-Engineering-Doctrine) is the companion operating discipline: how an agent scopes, investigates, verifies and reports work. Use the two together without confusing a research record with an installed capability.

The library is larger than its strategy catalog. The complete measured inventory is [INDEX.md](INDEX.md), with every path, Git blob hash and size in [INDEX.json](INDEX.json). Counts belong to that captured source tree; this page deliberately does not maintain a competing total. The catalog's strategy cards are one collection, not the denominator for the repository.

## Mandatory reading protocol

1. Read this page completely, then [INDEX.md](INDEX.md), the map of every top-level area and research collection.
2. Choose the relevant [ROADMAP.md](ROADMAP.md) route. Read the README or AREA.md for each area you will use, plus any narrower AGENTS.md before editing or running its code.
3. Read [docs/LLM-OPERATING-GUIDE.md](docs/LLM-OPERATING-GUIDE.md) for the source-to-answer workflow appropriate to your task. It explains how to turn the material into a bounded explanation, reproduction, comparison or verification.
4. Open the exact source, configuration, dependency and evidence files the route identifies. Do not substitute a summary, filename or status label for those files.
5. Report the source revision and what the inspected material supports. Distinguish a historical claim, a proposed method, a local test, a live service and a prospective result.

[AGENTS.md](AGENTS.md) supplies repository guardrails. It does not replace the map, authorize a deployment, or grant permission to send an order.

## First useful actions

With a local checkout and Python3, these read-only commands avoid loading a large index or archive into context:

```sh
python3 tools/repo_navigator.py route "explain a strategy"
python3 tools/repo_navigator.py search "tensor"
python3 tools/repo_navigator.py packet explain-strategy --max-chars 18000
python3 tools/repo_navigator.py check
```

A route gives reading order, source roles, relevant checks and an evidence boundary. A search finds candidates; it does not prove they answer the question. A bounded packet is a selected reading aid, not a claim to contain every relevant file. The navigator does not run the commands described by a route or activate any system. Browser-only readers can follow the same paths in ROADMAP and the area entrypoints below.

| Your first question | Route or starting evidence | Useful result |
| --- | --- | --- |
| What is one strategy, and where does its rule come from? | `explain-strategy`; card → accounting → exact implementation | A sourced rule explanation with unresolved differences named. |
| How would I reconstruct it? | `recreate-strategy`; algorithm/recreation notes → dependencies → tests | A reproducible plan and an explicit missing-dependency list. |
| Why do the strategy counts differ? | `reconcile-strategy-catalogs` | Separate denominators for cards, distinct accounting entries, aliases and roster IDs. |
| Where is Tensor? | `trace-tensor` | The cross-directory source, adapter, document and package trail. |
| How can I improve an LLM's working method? | `study-agent-methods`, `study-enhancement-history`, `study-second-brain` | Independent research findings and their actual adoption status. |
| Can I try something without credentials or a running desk? | `build-offline-desk`, `forecast-numeric-kernels`, `psychology-research` | A documented offline example with its exact claim boundary. |
| What does a public terminal snapshot establish? | `inspect-published-snapshot` | Its producer, recorded clocks, files and limits; not inferred live health. |
| Is a named file or capability missing? | `find-missing-material`; search exact paths and aliases | A searched/excluded/unavailable record rather than an unsupported absence claim. |

## Evidence rules that prevent wrong answers

- **Inventory is not interpretation.** INDEX.json proves what files and bytes were captured. CATALOG.json describes cards. ALL-SLEEVES.json records a broader deduplicated accounting. SLEEVES.json describes a roster snapshot. None substitutes for another.
- **A snapshot is not “running today.”** A committed roster, a mirrored terminal, an old install receipt and a status word such as `live` retain their captured context. Check source clocks and a permitted current runtime before claiming present operation.
- **Independent studies stay independent.** The agent-methods handbook, LLM-enhancement extraction, second-brain sweep, two chart studies and two psychology engines have different sources, purposes and limits. Compare them; do not invent a common lineage or merge their evidence.
- **Preserve the source trail.** Read code copies with their original provenance, version and representation notes. Historical packages are not automatically the current implementation. A similar filename is not an equivalent algorithm.
- **Search before declaring absence.** Search INDEX.json or the navigator by exact path fragment, then aliases, neighboring collections and archive manifests. State when content is unexamined, inaccessible, inside a container, or outside this repository.
- **Keep the execution boundary explicit.** This library does not authorize an account, service, schedule, network source, manual order or live trading. Paper/synthetic examples and historical engineering checks do not establish profitability or live readiness.
- **Current navigation must not rewrite historical evidence.** Improve maps and current guides; preserve frozen studies, vendor code, source records and scientific receipts. Reconcile contradictions in a new, sourced note rather than silently changing the record.

## Areas and their entrypoints

The complete current area set, exact counts and package breakdowns are generated in INDEX.md. This orientation table preserves the major routes; newly added areas remain discoverable through the complete index even before an explanation is curated.

| Area | What it supplies | First read |
| --- | --- | --- |
| Root | Entry protocol, maps, full strategy listing and family build records | [INDEX.md](INDEX.md), [ROADMAP.md](ROADMAP.md) |
| `adapters/` | Standalone sleeve adapters | [AREA.md](adapters/AREA.md) |
| `adapters3/` | Aster adapter collection | [AREA.md](adapters3/AREA.md) |
| `agentic-trade-desk/` | Paper-desk guide, offline skeleton and templates | [README.md](agentic-trade-desk/README.md), nested [AGENTS.md](agentic-trade-desk/AGENTS.md) |
| `aster_sleeves/` | Thin Aster entrypoints | [AREA.md](aster_sleeves/AREA.md) |
| `config/` | Versioned paper-only roster | [AREA.md](config/AREA.md) |
| `desk3/` | Desk engine, sleeve and portfolio source copies | [AREA.md](desk3/AREA.md) |
| `docs/` | Catalogs, accounting, reconstruction notes, guides and research | [AREA.md](docs/AREA.md) |
| `educational/` | Standalone educational math/engine packages | [AREA.md](educational/AREA.md) |
| `engines/` | Shared engine copies and bridges | [AREA.md](engines/AREA.md), [sanitization note](engines/SANITIZATION-NOTE.md) |
| `indicator/` | Indicator algorithm contract | [AREA.md](indicator/AREA.md) |
| `integration/` | Sleeve integration adapters and wiring guide | [AREA.md](integration/AREA.md) |
| `laz_sleeves/` | Thin Lazarus entrypoints | [AREA.md](laz_sleeves/AREA.md) |
| `master/` | Externally mirrored terminal assets and dated data | [Terminal route](ROADMAP.md#the-terminal); the mirror can replace this directory wholesale |
| `packages/` | Whole contributed packages with distinct versions | [AREA.md](packages/AREA.md), then the chosen package's own entry doc |
| `pine/` | Pine indicator source | [AREA.md](pine/AREA.md) |
| `proof/` | Historical install receipts | [AREA.md](proof/AREA.md) |
| `psychology-engine/` | Standalone research/reference engine | [README.md](psychology-engine/README.md), [public validation](psychology-engine/PUBLIC_VALIDATION.md) |
| `research/` | Standalone studies and practice archives | [AREA.md](research/AREA.md) |
| `sleeves/` | Strategy implementation copies | [AREA.md](sleeves/AREA.md) |
| `strategies/` | The strategy-card collection | [AREA.md](strategies/AREA.md) |
| `terminal-lineup/` | Tool snapshots, forecast research and build records | [AREA.md](terminal-lineup/AREA.md) |
| `tests/` | Repository test sources | [AREA.md](tests/AREA.md) |
| `tools/` | Offline navigation and inventory maintenance | [AREA.md](tools/AREA.md) |

## Dispersed collection: Tensor

Tensor has no single source directory here. Its trail spans sleeves, adapters, integration, documents, cards and retained packages. Search `tensor`, then follow [ROADMAP's Tensor route](ROADMAP.md#tensor-where-the-tensor-material-lives): a roster row → its exact sleeve → `adapters3/` and `integration/` wiring → algorithm/recreation documents → package provenance where relevant. The D20 pair is `sleeves/aster_tensor_d20_tensor.py` and `sleeves/aster_tensor_d20_pv.py`; the feed library is under `sleeves/tensor_research/`, and another implementation is `sleeves/midna/midna_tensor.py`. Presence of these files does not imply the external Tensor engine or all required feeds are bundled.

## Leave the next reader something verifiable

A useful answer records: the question; selected route; exact paths and revision; source dates; what was read or run; the supported conclusion; competing evidence or missing dependencies; and the next observation that would change the conclusion. Use the worked workflows in [the LLM operating guide](docs/LLM-OPERATING-GUIDE.md). This is how the library becomes reusable knowledge rather than a list of impressive filenames.

## Enhancement research and acceptance record

The [2026-11-07 research record](docs/research/repository-enhancement-2026-11-07/README.md) documents the external research and source-backed design choices behind this navigation layer. The [repository upgrade report](docs/REPOSITORY-UPGRADE-2026-11-07.md) records implemented improvements, preservation checks and acceptance evidence, with their limits. These dated records complement the current source inventory; they do not replace it.
