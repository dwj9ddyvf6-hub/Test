# Strategy catalog

**651 distinct trading strategies** have been built across our desks, and this repository is the public library that holds them: the strategy cards, the code, the recreation notes that let anyone rebuild a strategy from its recorded rules, the desk software that runs the current roster, and the guides that teach an agent (or a person) how to build a desk like this. It holds **4,865 files** in total. Everything below is a map of the whole repository, not just the catalog.

## The three views of the strategies

- [The full accounting](docs/ALL-SLEEVES.md): all **651** distinct strategies, deduplicated from **1,562 recorded ids** across every desk, arranged by type, each with its recorded algorithm and every distinct variant. The by-type listing further down this page mirrors it. Its machine-readable twin is [docs/ALL-SLEEVES.json](docs/ALL-SLEEVES.json): 651 strategy entries, **104 flagged unresolved** (kept separate, never force-merged), plus 3 monitors listed apart from the strategies.
- [The current desk](docs/SLEEVES.md): the **336** sleeves installed on the desk today, one row each with its code file in this repo. Machine-readable twin: [docs/SLEEVES.json](docs/SLEEVES.json) (336 rows, all 336 with code present in this repo). The roster it mirrors lives at [config/sleeves.json](config/sleeves.json), a byte copy of the desk roster config (336 sleeves, paper trading only).
- [The catalog](docs/CATALOG.json): **269** strategy cards, variants folded into one card each, across **15 families** (APEX, Ausar, Femto-lean, Galath / GrokBot, Griffith, Lazarus, Midna, Milkman, Muse, Quant research, Qullamaggie, Sable, SPAN, Tensor research, and the killed studies). The cards are also listed by family at the bottom of this page, and one card per strategy lives under `strategies/<family>/` (269 card files).

Monitors and research recorders are not listed as strategies in any of the three views.

## Guides for agents and builders

<!-- BEGIN FIXED SECTION: agent guides. The README generator should emit this block verbatim (source text: docs/README_FIXED_SECTION.md). Checked by agentic-trade-desk/skeleton/tools/check_root_readme_links.py -->
> **Guides for LLM agents: three guides, one desk.** Start with the [three-guide reconciliation](docs/THREE-GUIDES-RECONCILIATION.md): the map between the three guides, covering what all three agree on, what only one teaches, and the differences to decide consciously.
> **Field guide:** [How to build an agentic trade desk](docs/AGENTIC-TRADE-DESK-GUIDE.md): judgment under operation, scoping and evidence grading, the cross-desk sleeve accounting standard, forecast grading machinery, and 60 catalogued pitfalls.
> **Operational kit:** [`agentic-trade-desk/`](agentic-trade-desk/README.md): the running machine, one order path, reconciliation, reliability and failover operations, 130 catalogued pitfalls, and a runnable skeleton with tests. Paper trading only.
> **Companion build guide:** [Agentic Trade Desk Build Guide](docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md): architecture before code, product modes, layers and data contracts, build phases, and acceptance checklists.
<!-- END FIXED SECTION -->

> **Day-to-day use:** [Run this desk as your own alert system](docs/YOUR-OWN-ALERT-SYSTEM.md): how to put the terminal on a phone home screen and use this library as a working alert system and a replacement for a stack of vendor services.

## Layout: every part of the repository

| Folder or file | What is there |
|---|---|
| `strategies/<family>/` | One card per strategy: **269 cards** in 15 family folders (femto 45, milkman 34, apex 33, ausar 24, griffith 23, lazarus 19, quant_research 18, midna 17, muse 17, tensor_research 13, galath 10, killed 10, qullamaggie 3, sable 2, span 1). Start from a card to learn what a strategy does. |
| `docs/` | **1,165 files.** The catalogs and indexes above, the guides, and the recreation library: **872 `-RECREATE.md` notes and 184 `-ALGORITHM.md` notes** that record a strategy's rules closely enough to rebuild it, plus `docs/research/` (62 files of research passes) and `docs/verify/` (15 pages; the index is `docs/VERIFY.md`, the code lines each card rule was read from). |
| `sleeves/` | Strategy code: **569 Python files**, 318 at the top level and the rest under family folders (`sleeves/<family>/`, each copied file listed in `docs/VERIFY.md`). |
| `desk3/`, `integration/` | The v3 desk: `desk3/` (50 files: the desk engine, sleeve modules and portfolio books) and `integration/` (327 adapter files wiring sleeves into the desk). |
| `adapters/`, `adapters3/` | Earlier adapter sets: 29 files in `adapters/`, 265 in `adapters3/`. |
| `aster_sleeves/`, `laz_sleeves/` | Two sleeve families kept as their own folders, 10 files each. |
| `engines/` | A compact copy of the engine layer (19 files: desk3 pieces, adapters, sleeve samples, config and universe files, with a sanitization note). |
| `config/sleeves.json` | The current desk roster of record: 336 sleeves, paper trading only. |
| `packages/` | **1,927 files** of complete packages posted by the peer desks, kept whole rather than cherry-picked: `packages/claude/` (1,105 files: the master desk's terminal builder and public app, sleeve port library, parity tools, feed library, forecast system and more), `packages/ausar/` (791 files: the Aster desk R13 baseline and R15 execution packages, the forecast-engines lab, research terminals and rulebooks), `packages/grokbot/` (31 files: the md2 master-desk package, Q07 and RL64 Lazarus engines, small tools). |
| `psychology-engine/` | One of this repo's two market-psychology engines, as a self-contained package (124 files): the research and reference implementation (Ausar), with the engine itself (67 files under `engine/`), its audit trail, research and 38-page report, plus `PUBLIC_VALIDATION.md` and a checksum file. The second psychology engine is the live nine-gauge build (Midna); its design, theory, measurement study and engine live under `docs/research/psychology-engine-2026-10-30/`. |
| `agentic-trade-desk/` | The operational kit behind the guides (55 files): a runnable skeleton with tests (paper trading only), operating documents and templates. Its own front page is [`agentic-trade-desk/README.md`](agentic-trade-desk/README.md). |
| `pine/`, `indicator/` | The BB/RSI divergence indicator: the TradingView Pine script and its algorithm contract. Its research note is `docs/BB_RSI_Divergence_Research.md`. |
| `proof/install/` | Install proof records (22 JSON files), one per installed sleeve package, recording what was installed and verified. |
| `tests/` | Regression blocker tests (8 files) for the one-bar, PRZM, Raschke, Teddy ORB, Trullas, CCI-correlation and VIX-hedge builds. |
| `research/`, `docs/research/` | The technical analysis and chart reading research. At the root, `research/technical-analysis-study-2026-10-30/` holds the 2026-10-30 technical-analysis study and practice atlas (Ausar): README, the atlas in Markdown, Word and PDF, the full archive zip, and checksums. Under `docs/research/`: the technical-analysis mastery study (`technical-analysis-mastery-20261030/`), a full census of the chart-reading canon and a working chart-reading method in sections (the eye, structure, patterns, waves, indicators, protocol) with drills and a demonstration; and the one-bar family study (`onebar-family-2026-10-30/`); and the second psychology engine's design, theory and measurement study (`psychology-engine-2026-10-30/`). |
| Root build notes | `BTA-ONEBAR-BUILD.md`, `TEDDY-ORB-SPY-BUILD.md` with `TEDDY-ORB-SPY-SPEC-2026-10-28.md`, `TRULLAS-VARIANTS-BUILD.md` with `TRULLAS-VARIANTS-SPEC-2026-10-29.md`, and `AGENTS.md`: the build records for the newest sleeve families and the working rules for agents in this repo. Matching spec/build pairs for other families sit in `docs/`. |
| `docs/CATALOG.json` | Every strategy card with its variants and row ids (269 cards). |
| `docs/SLEEVES.md` / `docs/SLEEVES.json` | Every sleeve on the current desk (336), one row each, with its code file in this repo. |
| `docs/ALL-SLEEVES.md` / `docs/ALL-SLEEVES.json` | The curated accounting: every strategy ever built across all desks (651), deduplicated, arranged by type, with its algorithm and variants. |
| `docs/THREE-GUIDES-RECONCILIATION.md` | The map between the three agent guides: shared invariants, unique lessons, and the differences to decide consciously. |
| `docs/YOUR-OWN-ALERT-SYSTEM.md` | How a reader actually uses all of this day to day: the terminal as a home-screen alert system. |
| `docs/VERIFY.md` | The code lines each card rule was read from (one page per family in `docs/verify/`), and where each copied file came from. |
| `terminal-lineup/` | The terminal lineup: **1,345 files** saved from the local terminal tree: `site/` (1,121 files, with **104 tool pages** across 105 tool folders, plus shared code and data), `forecast/` (**88 files** of forecast engine code, registry and tests for the **30 forecast engines** in `forecast/registry.json`), `specs/` (1 file), `oracle/` (4 files), `records/` (16 files), root design and build docs (10 Markdown files) and **105 workflow build scripts**. Start at `terminal-lineup/site/` for the tools and `terminal-lineup/forecast/` for the engines. |

## Start here, by what you came for

| You want to | Go to |
|---|---|
| Understand one strategy | Its card under `strategies/<family>/`, then its entry in [the accounting](docs/ALL-SLEEVES.md) for the full algorithm and variants. |
| Rebuild a strategy from its rules | The matching `-ALGORITHM.md` and `-RECREATE.md` notes in `docs/` (1,056 notes between them). |
| See what the desk runs today | [The current desk index](docs/SLEEVES.md) (336 sleeves) and `config/sleeves.json`. |
| Count or cross-check every strategy ever built | [The full accounting](docs/ALL-SLEEVES.md) and `docs/ALL-SLEEVES.json` (651 from 1,562 ids; 104 unresolved, kept separate). |
| Build or run an agentic trade desk | The three guides in the fixed section below, the reconciliation first, then the kit in `agentic-trade-desk/`. |
| Use the desk as an alert system | [Run this desk as your own alert system](docs/YOUR-OWN-ALERT-SYSTEM.md). |
| Run or study the terminal engines and tools | `terminal-lineup/` (1,345 files): the tool pages under `terminal-lineup/site/`, the forecast engine code and registry under `terminal-lineup/forecast/`, and the design docs at `terminal-lineup/THE-70-TOOLS.md` and `terminal-lineup/FORECAST-ENGINES-30.md`. |
| Study the psychology engines | Two independent builds: `psychology-engine/` (Ausar's research and reference implementation; start with its README and `PUBLIC_VALIDATION.md`) and `docs/research/psychology-engine-2026-10-30/` (Midna's live nine-gauge engine: ENGINE-DESIGN, STUDY-THEORY, STUDY-MEASUREMENT). |
| Take a whole peer-desk package | `packages/claude/`, `packages/ausar/` or `packages/grokbot/`. |
| Check where a rule or a copied file came from | `docs/VERIFY.md` and `docs/verify/`. |

The master desk runs these sleeves on the Femto-lean framework (branch master-desk). Not in this repo: the framework itself (trading engine, order handling, data hub) and the Tensor indicator engine.

## How this repository is maintained

- **Generated parts:** the two long listings on this page (strategies by type, and catalog cards by family) are generated from `docs/ALL-SLEEVES.json` and `docs/CATALOG.json`. The catalog and accounting files are the sources of truth; if a number on this page ever disagrees with them, the files win.
- **Hand-written parts:** the front matter above those listings, the layout map, the guides, the recreation notes and the package folders are maintained directly.
- **The fixed section:** the agent-guide block below is a fixed section. Its source text lives in `docs/README_FIXED_SECTION.md`, and `agentic-trade-desk/skeleton/tools/check_root_readme_links.py` checks that the guide links survive. The README generator is not in this repository, so whoever regenerates this page must emit the fixed section verbatim and keep the descriptive front matter: both have been dropped by regeneration before, which is why the fixed section exists.
- **Copied code:** files copied from another desk keep their provenance in `docs/VERIFY.md`; nothing is silently rewritten.

## Strategies by type (651)

Every distinct strategy ever built across all desks, deduplicated from 1,562 recorded ids, arranged by type. Each name links to its full entry in [the accounting](docs/ALL-SLEEVES.md): the recorded algorithm and every distinct variant. 104 entries are flagged unresolved in the accounting (kept separate, never force-merged); monitors and recorders sit in the accounting closing section, not in this list.

### Trend following (200)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [Q07 w_cyan H52 small cheap5+insider2+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-small-cheap5insider2mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 small cheap5+mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-small-cheap5mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 small cheap5+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-small-cheap5tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 small cheap5+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-small-cheap5wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 small deep70+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-small-deep70wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 small tierA+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-small-tierawiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 small cheap5+deep70+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-small-cheap5deep70tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 small cheap5+mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-small-cheap5mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 small cheap5+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-small-cheap5tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 small deep70+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-small-deep70wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 small tierA+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-small-tierawiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 small cheap5+deep70+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-small-cheap5deep70mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 small cheap5+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-small-cheap5tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 small deep70+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-small-deep70tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 small deep70+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-small-deep70wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 small insider2+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-small-insider2wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 small tierA+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-small-tierawiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 small cheap5+deep70 (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-small-cheap5deep70-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 small cheap5+deep70+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-small-cheap5deep70mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 small cheap5+insider2 (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-small-cheap5insider2-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 small deep70+insider2 (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-small-deep70insider2-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 small deep70+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-small-deep70wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 small tierA+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-small-tierawiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 small cheap5+deep70+insider2 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-small-cheap5deep70insider2-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 small cheap5+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-small-cheap5wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 small deep70+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-small-deep70wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 small cheap5+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-small-cheap5wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 small deep70+insider2 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-small-deep70insider2-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 small deep70+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-small-deep70wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Coinbase SMA200 crypto trend](docs/ALL-SLEEVES.md#coinbase-sma200-crypto-trend) | Crypto spot · 1d · BTC-USD, ETH-USD (Coinbase). Full recorded algorithm in the accounting entry. | 2 |
| [Auditable 20/50 trend (SPY)](docs/ALL-SLEEVES.md#auditable-2050-trend-spy) | US ETF (SPY) · 5m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Simple daily trend cohorts](docs/ALL-SLEEVES.md#simple-daily-trend-cohorts) | US equities · 1d (20-session cohorts) · SCOPE universe: 550 US names. Full recorded algorithm in the accounting entry. | 1 |
| [Golden cross (SPY)](docs/ALL-SLEEVES.md#golden-cross-spy) | US ETF · 1d · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Small-cap high-beta beaten-down (52 weeks)](docs/ALL-SLEEVES.md#small-cap-high-beta-beaten-down-52-weeks) | US equities · 1w · The weekly M2 qualifier list. Full recorded algorithm in the accounting entry. | 1 |
| [Faber ETF trend (10-month average)](docs/ALL-SLEEVES.md#faber-etf-trend-10-month-average) | US ETFs · 1d (monthly average) · SPY, EFA, BND, VNQ, GSG · Griffith: 13 ETFs. Full recorded algorithm in the accounting entry. | 1 |
| [Pivot Ribbon 13/48 cross](docs/ALL-SLEEVES.md#pivot-ribbon-1348-cross) | US equities, index ETFs and futures · 1d · 1,822 US stocks + 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 1 |
| [Daily SMA200 spot allocation](docs/ALL-SLEEVES.md#daily-sma200-spot-allocation) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Daily SMA200 spot allocation](docs/ALL-SLEEVES.md#daily-sma200-spot-allocation-1) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Daily SMA200 spot allocation](docs/ALL-SLEEVES.md#daily-sma200-spot-allocation-2) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Daily SMA200 spot allocation](docs/ALL-SLEEVES.md#daily-sma200-spot-allocation-3) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [TRADER_DONCHIAN55](docs/ALL-SLEEVES.md#trader_donchian55) | No strategy description recorded in consulted sources. | 1 |
| [Q07 w_cyan H52 small cheap5+mom6+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-small-cheap5mom6stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 small deep70+insider2+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-small-deep70insider2stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 small insider2+mom6+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-small-insider2mom6stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 midlarge stress_vix20+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-midlarge-stress_vix20tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 small deep70+insider2+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-small-deep70insider2stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 micro cheap5+deep70+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-micro-cheap5deep70stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 midlarge mom6+stress_vix20+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-midlarge-mom6stress_vix20tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 midlarge stress_vix20+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-midlarge-stress_vix20tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 small mom6+stress_vix20+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-small-mom6stress_vix20tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 small stress_vix20+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-small-stress_vix20tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 micro cheap5+deep70+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-micro-cheap5deep70stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 micro cheap5+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-micro-cheap5stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 midlarge cheap5+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-midlarge-cheap5stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 midlarge deep70+insider2+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-midlarge-deep70insider2stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 midlarge deep70+stress_vix20+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-midlarge-deep70stress_vix20wiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 midlarge insider2+mom6+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-midlarge-insider2mom6stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 small cheap5+deep70+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-small-cheap5deep70stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 small cheap5+insider2+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-small-cheap5insider2stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 small cheap5+mom6+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-small-cheap5mom6stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 small cheap5+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-small-cheap5stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 micro cheap5+mom6+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-micro-cheap5mom6stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 midlarge cheap5+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-midlarge-cheap5stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 midlarge deep70+insider2+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-midlarge-deep70insider2stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 small cheap5+deep70+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-small-cheap5deep70stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 small cheap5+insider2+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-small-cheap5insider2stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 small cheap5+mom6+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-small-cheap5mom6stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 small cheap5+stress_vix20 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-small-cheap5stress_vix20-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [s_q07w_c52_sm_cheap5_mom6_vix20](docs/ALL-SLEEVES.md#s_q07w_c52_sm_cheap5_mom6_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_mi_cheap5_deep70_vix20](docs/ALL-SLEEVES.md#s_q07w_g78_mi_cheap5_deep70_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_sm_mom6_vix20_tierA](docs/ALL-SLEEVES.md#s_q07w_g78_sm_mom6_vix20_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_sm_vix20_tierA](docs/ALL-SLEEVES.md#s_q07w_g78_sm_vix20_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_mi_cheap5_deep70_vix20](docs/ALL-SLEEVES.md#s_q07w_s52_mi_cheap5_deep70_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_mi_cheap5_vix20](docs/ALL-SLEEVES.md#s_q07w_s52_mi_cheap5_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_sm_cheap5_deep70_vix20](docs/ALL-SLEEVES.md#s_q07w_s52_sm_cheap5_deep70_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_sm_cheap5_mom6_vix20](docs/ALL-SLEEVES.md#s_q07w_s52_sm_cheap5_mom6_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_sm_cheap5_vix20](docs/ALL-SLEEVES.md#s_q07w_s52_sm_cheap5_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s78_mi_cheap5_mom6_vix20](docs/ALL-SLEEVES.md#s_q07w_s78_mi_cheap5_mom6_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s78_sm_cheap5_deep70_vix20](docs/ALL-SLEEVES.md#s_q07w_s78_sm_cheap5_deep70_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s78_sm_cheap5_mom6_vix20](docs/ALL-SLEEVES.md#s_q07w_s78_sm_cheap5_mom6_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s78_sm_cheap5_vix20](docs/ALL-SLEEVES.md#s_q07w_s78_sm_cheap5_vix20) | No strategy description recorded in consulted sources. | 1 |
| [Q07 Tensor alt-data confluence cells](docs/ALL-SLEEVES.md#q07-tensor-alt-data-confluence-cells) | US equities · 1w · Tracker universe by PIT SEC band. Full recorded algorithm in the accounting entry. | 2 |
| [s_q07w_g52_ml_cheap5](docs/ALL-SLEEVES.md#s_q07w_g52_ml_cheap5) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_ml_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_g52_ml_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_ml_vix20_tierA](docs/ALL-SLEEVES.md#s_q07w_g52_ml_vix20_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_ml_deep70_tierA](docs/ALL-SLEEVES.md#s_q07w_g78_ml_deep70_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_ml_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_g78_ml_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_ml_mom6_vix20_tierA](docs/ALL-SLEEVES.md#s_q07w_g78_ml_mom6_vix20_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_ml_vix20_tierA](docs/ALL-SLEEVES.md#s_q07w_g78_ml_vix20_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_ml_cheap5](docs/ALL-SLEEVES.md#s_q07w_s52_ml_cheap5) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_ml_cheap5_vix20](docs/ALL-SLEEVES.md#s_q07w_s52_ml_cheap5_vix20) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s78_ml_cheap5](docs/ALL-SLEEVES.md#s_q07w_s78_ml_cheap5) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s78_ml_cheap5_mom6](docs/ALL-SLEEVES.md#s_q07w_s78_ml_cheap5_mom6) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s78_ml_cheap5_vix20](docs/ALL-SLEEVES.md#s_q07w_s78_ml_cheap5_vix20) | No strategy description recorded in consulted sources. | 1 |
| [Midna Faber (Midna port)](docs/ALL-SLEEVES.md#midna-faber-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna VWAP (Midna port)](docs/ALL-SLEEVES.md#midna-vwap-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna W green calm SMH (Midna port)](docs/ALL-SLEEVES.md#midna-w-green-calm-smh-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 micro cheap5+deep70+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-micro-cheap5deep70tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 micro cheap5+mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-micro-cheap5mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 micro cheap5+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-micro-cheap5tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 micro deep70+mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-micro-deep70mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 micro deep70+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-micro-deep70tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 micro mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-micro-mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 midlarge mom6+tierA+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-midlarge-mom6tierawiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 midlarge mom6+wiki_spike2 (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-midlarge-mom6wiki_spike2-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 midlarge tierA+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-midlarge-tierawiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H52 midlarge tierA+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h52-midlarge-tierawiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 micro cheap5+deep70+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-micro-cheap5deep70tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 micro cheap5+mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-micro-cheap5mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 micro cheap5+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-micro-cheap5tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 micro deep70+mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-micro-deep70mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 micro mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-micro-mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 micro tierA (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-micro-tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 midlarge deep70+tierA+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-midlarge-deep70tierawiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 midlarge mom6+tierA+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-midlarge-mom6tierawiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 midlarge tierA+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-midlarge-tierawiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_cyan H78 midlarge tierA+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_cyan-h78-midlarge-tierawiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 micro cheap5+deep70 (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-micro-cheap5deep70-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 micro cheap5+deep70+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-micro-cheap5deep70mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 micro cheap5+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-micro-cheap5tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 micro deep70+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-micro-deep70tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 micro mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-micro-mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 micro tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-micro-tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 midlarge ats_z1+mom6+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-midlarge-ats_z1mom6wiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 midlarge cheap5 (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-midlarge-cheap5-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 midlarge insider2+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-midlarge-insider2wiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 midlarge mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-midlarge-mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H52 midlarge tierA+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_green-h52-midlarge-tierawiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 micro cheap5+deep70+insider2 (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-micro-cheap5deep70insider2-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 micro cheap5+deep70+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-micro-cheap5deep70mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 micro cheap5+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-micro-cheap5tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 micro deep70+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-micro-deep70tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 micro mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-micro-mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 micro tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-micro-tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 midlarge deep70+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-midlarge-deep70tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 midlarge mom6+tierA (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-midlarge-mom6tiera-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_green H78 midlarge tierA+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_green-h78-midlarge-tierawiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 micro cheap5 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-micro-cheap5-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 micro cheap5+deep70 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-micro-cheap5deep70-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 micro cheap5+deep70+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-micro-cheap5deep70mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 micro cheap5+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-micro-cheap5mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 midlarge cheap5 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-midlarge-cheap5-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 midlarge deep70+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-midlarge-deep70wiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H52 midlarge insider2+mom6+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_swing-h52-midlarge-insider2mom6wiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 micro ats_z1+cheap5 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-micro-ats_z1cheap5-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 micro ats_z1+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-micro-ats_z1mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 micro cheap5+deep70+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-micro-cheap5deep70mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 micro cheap5+insider2+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-micro-cheap5insider2mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 micro cheap5+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-micro-cheap5mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 midlarge cheap5 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-midlarge-cheap5-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 midlarge cheap5+mom6 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-midlarge-cheap5mom6-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 midlarge deep70+gamma_low+insider2 (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-midlarge-deep70gamma_lowinsider2-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 midlarge deep70+mom6+wiki_low (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-midlarge-deep70mom6wiki_low-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q07 w_swing H78 midlarge deep70+wiki_cov (test)](docs/ALL-SLEEVES.md#q07-w_swing-h78-midlarge-deep70wiki_cov-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Anna PhD location printer](docs/ALL-SLEEVES.md#anna-phd-location-printer) | US equities and ETFs · 1d · Anna's labeled census: 115 names. Full recorded algorithm in the accounting entry. | 1 |
| [Q14 under-$5 weekly book](docs/ALL-SLEEVES.md#q14-under-5-weekly-book) | US equities · 1w · Tracker universe. Full recorded algorithm in the accounting entry. | 1 |
| [Saty Magnum (SPY shares)](docs/ALL-SLEEVES.md#saty-magnum-spy-shares) | SPY shares, long and short · 3m · 10m · 1h · 1d · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Weekly cyan transition](docs/ALL-SLEEVES.md#weekly-cyan-transition) | US equities · 1wk · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 1 |
| [s_q07_ins2](docs/ALL-SLEEVES.md#s_q07_ins2) | No strategy description recorded in consulted sources. | 1 |
| [s_q07_wiki](docs/ALL-SLEEVES.md#s_q07_wiki) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c52_mi_cheap5_deep70_tierA](docs/ALL-SLEEVES.md#s_q07w_c52_mi_cheap5_deep70_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c52_mi_cheap5_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_c52_mi_cheap5_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c52_mi_cheap5_tierA](docs/ALL-SLEEVES.md#s_q07w_c52_mi_cheap5_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c52_mi_deep70_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_c52_mi_deep70_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c52_mi_deep70_tierA](docs/ALL-SLEEVES.md#s_q07w_c52_mi_deep70_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c52_mi_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_c52_mi_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c52_sm_cheap5_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_c52_sm_cheap5_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c52_sm_cheap5_tierA](docs/ALL-SLEEVES.md#s_q07w_c52_sm_cheap5_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c78_mi_cheap5_deep70_tierA](docs/ALL-SLEEVES.md#s_q07w_c78_mi_cheap5_deep70_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c78_mi_cheap5_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_c78_mi_cheap5_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c78_mi_cheap5_tierA](docs/ALL-SLEEVES.md#s_q07w_c78_mi_cheap5_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c78_mi_deep70_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_c78_mi_deep70_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c78_mi_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_c78_mi_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c78_mi_tierA](docs/ALL-SLEEVES.md#s_q07w_c78_mi_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c78_sm_cheap5_deep70_tierA](docs/ALL-SLEEVES.md#s_q07w_c78_sm_cheap5_deep70_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c78_sm_cheap5_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_c78_sm_cheap5_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_c78_sm_cheap5_tierA](docs/ALL-SLEEVES.md#s_q07w_c78_sm_cheap5_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_mi_cheap5_deep70](docs/ALL-SLEEVES.md#s_q07w_g52_mi_cheap5_deep70) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_mi_cheap5_deep70_mom6](docs/ALL-SLEEVES.md#s_q07w_g52_mi_cheap5_deep70_mom6) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_mi_cheap5_tierA](docs/ALL-SLEEVES.md#s_q07w_g52_mi_cheap5_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_mi_deep70_tierA](docs/ALL-SLEEVES.md#s_q07w_g52_mi_deep70_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_mi_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_g52_mi_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_mi_tierA](docs/ALL-SLEEVES.md#s_q07w_g52_mi_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_sm_cheap5_deep70_mom6](docs/ALL-SLEEVES.md#s_q07w_g52_sm_cheap5_deep70_mom6) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_sm_cheap5_tierA](docs/ALL-SLEEVES.md#s_q07w_g52_sm_cheap5_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g52_sm_deep70_tierA](docs/ALL-SLEEVES.md#s_q07w_g52_sm_deep70_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_mi_cheap5_deep70_mom6](docs/ALL-SLEEVES.md#s_q07w_g78_mi_cheap5_deep70_mom6) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_mi_cheap5_tierA](docs/ALL-SLEEVES.md#s_q07w_g78_mi_cheap5_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_mi_deep70_tierA](docs/ALL-SLEEVES.md#s_q07w_g78_mi_deep70_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_mi_mom6_tierA](docs/ALL-SLEEVES.md#s_q07w_g78_mi_mom6_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_mi_tierA](docs/ALL-SLEEVES.md#s_q07w_g78_mi_tiera) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_sm_cheap5_deep70](docs/ALL-SLEEVES.md#s_q07w_g78_sm_cheap5_deep70) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_g78_sm_cheap5_deep70_mom6](docs/ALL-SLEEVES.md#s_q07w_g78_sm_cheap5_deep70_mom6) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_mi_cheap5](docs/ALL-SLEEVES.md#s_q07w_s52_mi_cheap5) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_mi_cheap5_deep70](docs/ALL-SLEEVES.md#s_q07w_s52_mi_cheap5_deep70) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_mi_cheap5_deep70_mom6](docs/ALL-SLEEVES.md#s_q07w_s52_mi_cheap5_deep70_mom6) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s52_mi_cheap5_mom6](docs/ALL-SLEEVES.md#s_q07w_s52_mi_cheap5_mom6) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s78_mi_cheap5_deep70_mom6](docs/ALL-SLEEVES.md#s_q07w_s78_mi_cheap5_deep70_mom6) | No strategy description recorded in consulted sources. | 1 |
| [s_q07w_s78_mi_cheap5_mom6](docs/ALL-SLEEVES.md#s_q07w_s78_mi_cheap5_mom6) | No strategy description recorded in consulted sources. | 1 |
| [s_wait_intraweek](docs/ALL-SLEEVES.md#s_wait_intraweek) | No strategy description recorded in consulted sources. | 1 |

### Momentum (41)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [Midna CS momentum (Midna port)](docs/ALL-SLEEVES.md#midna-cs-momentum-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [IU big-body bar crypto (5m)](docs/ALL-SLEEVES.md#iu-big-body-bar-crypto-5m) | Crypto spot · 5m · ENJUSDT (Binance). Full recorded algorithm in the accounting entry. | 1 |
| [QQQ core with a momentum tilt · 150% exposure](docs/ALL-SLEEVES.md#qqq-core-with-a-momentum-tilt--150-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [QQQ core with a momentum tilt · 98% exposure](docs/ALL-SLEEVES.md#qqq-core-with-a-momentum-tilt--98-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [QQQ core with a two-source momentum tilt · 150% exposure](docs/ALL-SLEEVES.md#qqq-core-with-a-two-source-momentum-tilt--150-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [QQQ core with a two-source momentum tilt · 98% exposure](docs/ALL-SLEEVES.md#qqq-core-with-a-two-source-momentum-tilt--98-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [12-month momentum top decile (monthly)](docs/ALL-SLEEVES.md#12-month-momentum-top-decile-monthly) | US equities · 1d (monthly) · 1,838-name genome. Full recorded algorithm in the accounting entry. | 1 |
| [Leader-1d event](docs/ALL-SLEEVES.md#leader-1d-event) | US equities · 1d (one variant 1h) · 1,838-name genome · small-cap band · 41-name basket. Full recorded algorithm in the accounting entry. | 4 |
| [Six-month momentum leaders](docs/ALL-SLEEVES.md#six-month-momentum-leaders) | US equities · 1d · 114-name swing basket + SPY · Midna's swing basket. Full recorded algorithm in the accounting entry. | 1 |
| [52-week-high strength](docs/ALL-SLEEVES.md#52-week-high-strength) | US equities · 1d (monthly) · SCOPE universe: 550 US names. Full recorded algorithm in the accounting entry. | 1 |
| [Cross-sectional momentum (12-1 / 6-1)](docs/ALL-SLEEVES.md#cross-sectional-momentum-12-1--6-1) | US equities · 1d (monthly) · SCOPE universe: 550 US names. Full recorded algorithm in the accounting entry. | 1 |
| [ETF 12-month time-series momentum](docs/ALL-SLEEVES.md#etf-12-month-time-series-momentum) | US ETFs · 1d (monthly) · 13 ETFs on the tape of a frozen 17-ETF basket. Full recorded algorithm in the accounting entry. | 1 |
| [Liquid momentum trend cohorts](docs/ALL-SLEEVES.md#liquid-momentum-trend-cohorts) | US equities · 1d (20-session cohorts) · SCOPE universe: 550 US names. Full recorded algorithm in the accounting entry. | 1 |
| [Momentum plus earnings drift](docs/ALL-SLEEVES.md#momentum-plus-earnings-drift) | US equities · 1d (20-session hold) · SCOPE stocks (ETF basket excluded). Full recorded algorithm in the accounting entry. | 1 |
| [Intraday momentum (Gao et al.)](docs/ALL-SLEEVES.md#intraday-momentum-gao-et-al) | US ETFs · 5m · SPY, QQQ. Full recorded algorithm in the accounting entry. | 1 |
| [CHASE weekly lane](docs/ALL-SLEEVES.md#chase-weekly-lane) | US equities · 1w · Liquid cross-section (dv20 ≥ $1M, close ≥ $5, operating companies). Full recorded algorithm in the accounting entry. | 1 |
| [EMA4 rising VWAP](docs/ALL-SLEEVES.md#ema4-rising-vwap) | US equities · 1d · Midna's swing basket. Full recorded algorithm in the accounting entry. | 1 |
| [Hyperliquid momentum floor](docs/ALL-SLEEVES.md#hyperliquid-momentum-floor) | Crypto perps · intraday (10-min scan) · Hyperliquid perps with day notional ≥ $25M. Full recorded algorithm in the accounting entry. | 1 |
| [MACD-CCI](docs/ALL-SLEEVES.md#macd-cci) | US equities · 1d · Midna's swing basket. Full recorded algorithm in the accounting entry. | 1 |
| [TSMOM 12-1 ETF book](docs/ALL-SLEEVES.md#tsmom-12-1-etf-book) | US ETFs · 1d (every 21 sessions) · 30 diversified ETFs (equity, sector, bond, commodity, currency). Full recorded algorithm in the accounting entry. | 1 |
| [Gap-up pre-noon continuation (SPY)](docs/ALL-SLEEVES.md#gap-up-pre-noon-continuation-spy) | US ETF · 1m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [PO10 extreme (QQQ)](docs/ALL-SLEEVES.md#po10-extreme-qqq) | PO10 - QQQ 10-minute momentum | 1 |
| [Raschke PF3 momentum (SPY)](docs/ALL-SLEEVES.md#raschke-pf3-momentum-spy) | SPY shares, long and short · 5m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Leader genome](docs/ALL-SLEEVES.md#leader-genome) | US equities · 1h · 1d · 1wk · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 1 |
| [Midna MACD (Midna port)](docs/ALL-SLEEVES.md#midna-macd-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [CHASE (WAIT)](docs/ALL-SLEEVES.md#chase-wait) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Kraken ENJ order-book imbalance (spot)](docs/ALL-SLEEVES.md#kraken-enj-order-book-imbalance-spot) | Kraken ENJ order-book imbalance (spot) Adapter for free_kraken_enj_spot — interface glue ONLY (DESIGN §4). | 1 |
| [Gap continuation (legacy setup)](docs/ALL-SLEEVES.md#gap-continuation-legacy-setup) | US equities · 1m (15-minute cycle) · SPY, QQQ, IWM, the SCOPE radar's top 100, held names. Full recorded algorithm in the accounting entry. | 1 |
| [Positive earnings surprise drift](docs/ALL-SLEEVES.md#positive-earnings-surprise-drift) | US equities · 1d (20-session hold) · SCOPE stocks (ETF basket excluded). Full recorded algorithm in the accounting entry. | 1 |
| [Top-decile SUE drift](docs/ALL-SLEEVES.md#top-decile-sue-drift) | US equities · 1d (20-session hold) · SCOPE stocks (ETF basket excluded). Full recorded algorithm in the accounting entry. | 1 |
| [Earnings-day overnight scalp](docs/ALL-SLEEVES.md#earnings-day-overnight-scalp) | US equities · 1d (overnight) · Nasdaq earnings-calendar names. Full recorded algorithm in the accounting entry. | 1 |
| [PEAD price surprise](docs/ALL-SLEEVES.md#pead-price-surprise) | US equities · 1d (event) · Nasdaq earnings-calendar names. Full recorded algorithm in the accounting entry. | 1 |
| [Strong-afternoon continuation](docs/ALL-SLEEVES.md#strong-afternoon-continuation) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Strong-afternoon continuation](docs/ALL-SLEEVES.md#strong-afternoon-continuation-1) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Strong-afternoon continuation](docs/ALL-SLEEVES.md#strong-afternoon-continuation-2) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Strong-afternoon continuation](docs/ALL-SLEEVES.md#strong-afternoon-continuation-3) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Fast Numbers earnings surprise](docs/ALL-SLEEVES.md#fast-numbers-earnings-surprise) | US equities (long and short) · 1d (open to close) · US stocks with reported and consensus EPS. Full recorded algorithm in the accounting entry. | 1 |
| [Weekly green recovery](docs/ALL-SLEEVES.md#weekly-green-recovery) | US equities · 1wk · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 1 |
| [PUBLIC_AI_VOLUME_SPOT100](docs/ALL-SLEEVES.md#public_ai_volume_spot100) | No strategy description recorded in consulted sources. | 1 |
| [PUBLIC_IU_BODY_SPOT100](docs/ALL-SLEEVES.md#public_iu_body_spot100) | No strategy description recorded in consulted sources. | 1 |
| [s_mn_csmom](docs/ALL-SLEEVES.md#s_mn_csmom) | No strategy description recorded in consulted sources. | 1 |

### Mean reversion (67)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [Midna Reversal (Midna port)](docs/ALL-SLEEVES.md#midna-reversal-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Confirmed absorption control · ADAUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#confirmed-absorption-control--adausdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Confirmed absorption control · ADAUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#confirmed-absorption-control--adausdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Absorption with negative funding · ADAUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#absorption-with-negative-funding--adausdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Absorption with negative funding · ADAUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#absorption-with-negative-funding--adausdt-16-hour-hold-1-volume-cap-1) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with negative funding · ADAUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#absorption-with-negative-funding--adausdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with negative funding · ADAUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#absorption-with-negative-funding--adausdt-16-hour-hold-available-cash-sizing-1) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Absorption with negative funding · ENJUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#absorption-with-negative-funding--enjusdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with negative funding · ENJUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#absorption-with-negative-funding--enjusdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with negative funding · LINKUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#absorption-with-negative-funding--linkusdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with negative funding · LINKUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#absorption-with-negative-funding--linkusdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with nonnegative funding · ADAUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#absorption-with-nonnegative-funding--adausdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Absorption with nonnegative funding · ADAUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#absorption-with-nonnegative-funding--adausdt-16-hour-hold-1-volume-cap-1) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with nonnegative funding · ADAUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#absorption-with-nonnegative-funding--adausdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Absorption with nonnegative funding · ADAUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#absorption-with-nonnegative-funding--adausdt-16-hour-hold-available-cash-sizing-1) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with nonnegative funding · ENJUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#absorption-with-nonnegative-funding--enjusdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with nonnegative funding · ENJUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#absorption-with-nonnegative-funding--enjusdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with nonnegative funding · LINKUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#absorption-with-nonnegative-funding--linkusdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Absorption with nonnegative funding · LINKUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#absorption-with-nonnegative-funding--linkusdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Crypto confirmed absorption (4h)](docs/ALL-SLEEVES.md#crypto-confirmed-absorption-4h) | Crypto spot · 4h · ADAUSDT, ENJUSDT, LINKUSDT. Full recorded algorithm in the accounting entry. | 14 |
| [Opening gamma puts](docs/ALL-SLEEVES.md#opening-gamma-puts) | Equity options · 5m · 42-name R5 list. Full recorded algorithm in the accounting entry. | 1 |
| [R19 10-minute EMA cloud reclaim](docs/ALL-SLEEVES.md#r19-10-minute-ema-cloud-reclaim) | US equities · 10m (1h bias) · Frozen 42-name list. Full recorded algorithm in the accounting entry. | 2 |
| [RSI(2) pullback](docs/ALL-SLEEVES.md#rsi2-pullback) | US ETFs · US equities · crypto (ADA) · 1d · 1h · 15 liquid ETFs · 41-name old-desk basket · ADA. Full recorded algorithm in the accounting entry. | 2 |
| [Intraday EMA cloud reclaim](docs/ALL-SLEEVES.md#intraday-ema-cloud-reclaim) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Intraday EMA cloud reclaim](docs/ALL-SLEEVES.md#intraday-ema-cloud-reclaim-1) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Four-hour confirmed absorption · ENJUSDT](docs/ALL-SLEEVES.md#four-hour-confirmed-absorption--enjusdt) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Four-hour confirmed absorption · LINKUSDT](docs/ALL-SLEEVES.md#four-hour-confirmed-absorption--linkusdt) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [20-day VWAP reversion](docs/ALL-SLEEVES.md#20-day-vwap-reversion) | 20-day VWAP reversion Adapter for ema_vwap — interface glue ONLY (DESIGN §4). | 1 |
| [Capitulation reversal (hourly)](docs/ALL-SLEEVES.md#capitulation-reversal-hourly) | Capitulation reversal (hourly) Adapter for capitulation — v2 interface glue ONLY (DESIGN §4a). | 1 |
| [Legend's EMA (trend-day fade)](docs/ALL-SLEEVES.md#legends-ema-trend-day-fade) | US ETFs · 15m · 1d · QQQ · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Microcap snapback (weekly)](docs/ALL-SLEEVES.md#microcap-snapback-weekly) | US equities (microcaps) · 1w · 1d · Bottom tenth of the 1,838-name genome by weekly dollar volume. Full recorded algorithm in the accounting entry. | 1 |
| [Morning dip limit](docs/ALL-SLEEVES.md#morning-dip-limit) | US ETFs · 3m · QQQ · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Red-day washout reversal](docs/ALL-SLEEVES.md#red-day-washout-reversal) | US equities · 1d (hourly checks) · 41-name old-desk basket. Full recorded algorithm in the accounting entry. | 1 |
| [Next-support plan](docs/ALL-SLEEVES.md#next-support-plan) | US equities · 1d (1-minute passes) · 30-name Galath folio list. Full recorded algorithm in the accounting entry. | 1 |
| [Washout and PPC coil](docs/ALL-SLEEVES.md#washout-and-ppc-coil) | US equities · 1d (1-minute passes) · 411-stock Galath universe (Signal Prism US 413 without its two crypto pairs). Full recorded algorithm in the accounting entry. | 1 |
| [Leaders Rest](docs/ALL-SLEEVES.md#leaders-rest) | US equities · 1d · SCOPE universe: 550 US names (SPY, QQQ, IWM and the sector ETFs excluded). Full recorded algorithm in the accounting entry. | 1 |
| [VWAP pullback (legacy setup)](docs/ALL-SLEEVES.md#vwap-pullback-legacy-setup) | US equities · 1m (15-minute cycle) · SPY, QQQ, IWM, the SCOPE radar's top 100, held names. Full recorded algorithm in the accounting entry. | 1 |
| [ICT killzone sweep & reclaim (JadeCap via @OtherSideBJ)](docs/ALL-SLEEVES.md#ict-killzone-sweep--reclaim-jadecap-via-othersidebj) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Six short candidates](docs/ALL-SLEEVES.md#six-short-candidates) | US equities · 30m · 1d · 41-name old-desk basket. Full recorded algorithm in the accounting entry. | 1 |
| [Large-cap prior-month reversal](docs/ALL-SLEEVES.md#large-cap-prior-month-reversal) | US equities · 1d (monthly) · 40 large caps. Full recorded algorithm in the accounting entry. | 1 |
| [Weekly 8/20/50 pullback](docs/ALL-SLEEVES.md#weekly-82050-pullback) | US ETFs · 1w signal · 1d management · 19 ETFs (the funds of the public Portfolio T page). Full recorded algorithm in the accounting entry. | 1 |
| [Big down-day response](docs/ALL-SLEEVES.md#big-down-day-response) | US index ETFs and futures · 1d · 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 2 |
| [Call-to-put reversal (SPY)](docs/ALL-SLEEVES.md#call-to-put-reversal-spy) | US ETF · 1m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Connors Double 7](docs/ALL-SLEEVES.md#connors-double-7) | US equities, index ETFs and futures · 1d · 1,822 US stocks + 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 1 |
| [EMA21 deviation reversion](docs/ALL-SLEEVES.md#ema21-deviation-reversion) | US equities, index ETFs and futures · 1d · 1,822 US stocks + 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 1 |
| [Four-hour Phase Oscillator OpEx rollover (SPY)](docs/ALL-SLEEVES.md#four-hour-phase-oscillator-opex-rollover-spy) | US ETF · 4h · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Gap fade / momentum mirror (SPY)](docs/ALL-SLEEVES.md#gap-fade--momentum-mirror-spy) | US ETF · 1d gap · 1m exits · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Legend's Buy Day](docs/ALL-SLEEVES.md#legends-buy-day) | US equities, index ETFs and futures · 1d · 1,822 US stocks + 14 index ETFs and futures · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Phase Oscillator zone exit](docs/ALL-SLEEVES.md#phase-oscillator-zone-exit) | US equities, index ETFs and futures · 1d · 1,822 US stocks + 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 1 |
| [Premarket all-time-high fade (SPY)](docs/ALL-SLEEVES.md#premarket-all-time-high-fade-spy) | US ETF · 1m · 10m Phase Oscillator · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Vomy / iVomy (SPY)](docs/ALL-SLEEVES.md#vomy--ivomy-spy) | US ETF · 10m · SPY. Full recorded algorithm in the accounting entry. | 2 |
| [PRZM Fade Edges recreation (SPY)](docs/ALL-SLEEVES.md#przm-fade-edges-recreation-spy) | SPY shares, long and short · 1m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Raschke RRE adaptive desk (SPY)](docs/ALL-SLEEVES.md#raschke-rre-adaptive-desk-spy) | SPY shares · 5m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Saty opportunity engine v0.3 (SPY shares)](docs/ALL-SLEEVES.md#saty-opportunity-engine-v03-spy-shares) | SPY shares, long and short · 10m · 1h · SPY (QQQ and IWM as context). Full recorded algorithm in the accounting entry. | 1 |
| [Saty research system v0.2 (SPY shares)](docs/ALL-SLEEVES.md#saty-research-system-v02-spy-shares) | SPY shares, long and short · 10m · 1h · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Shen first-touch fade (SPY 0DTE)](docs/ALL-SLEEVES.md#shen-first-touch-fade-spy-0dte) | SPY options (0DTE) · 1m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [RSI2 dip rebound · 1d](docs/ALL-SLEEVES.md#rsi2-dip-rebound--1d) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [RSI2 dip rebound · 1d](docs/ALL-SLEEVES.md#rsi2-dip-rebound--1d-1) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Location-first repair](docs/ALL-SLEEVES.md#location-first-repair) | US equities · 1d (5-minute passes) · Sable catalog: 488 stocks (68 ETFs as context). Full recorded algorithm in the accounting entry. | 1 |
| [Support scanner (5-minute)](docs/ALL-SLEEVES.md#support-scanner-5-minute) | US equities · 5m · Sable catalog: 488 stocks. Full recorded algorithm in the accounting entry. | 1 |
| [SPAN Harvest](docs/ALL-SLEEVES.md#span-harvest) | Prediction markets · Trade prints (60 s passes) · Polymarket MLB, NPB, UFC and boxing moneylines. Full recorded algorithm in the accounting entry. | 1 |
| [Leaders Rest v1.1 on daily buy-greens](docs/ALL-SLEEVES.md#leaders-rest-v11-on-daily-buy-greens) | US equities · 1d · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 1 |
| [Beaten-down weekly qualifiers](docs/ALL-SLEEVES.md#beaten-down-weekly-qualifiers) | Beaten-down weekly qualifiers Adapter for beatendown — v2 interface glue ONLY (DESIGN §4a). | 1 |
| [Qullamaggie parabolic short](docs/ALL-SLEEVES.md#qullamaggie-parabolic-short) | US equities · 1d setup · 1m trigger · 1,838-name genome. Full recorded algorithm in the accounting entry. | 1 |
| [Deep Reset cross-scan](docs/ALL-SLEEVES.md#deep-reset-cross-scan) | US equities · 1d · 1wk · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 1 |
| [PUBLIC_TOMAZETTI_RSI2_SPOT100](docs/ALL-SLEEVES.md#public_tomazetti_rsi2_spot100) | No strategy description recorded in consulted sources. | 1 |
| [TRADER_RSI2](docs/ALL-SLEEVES.md#trader_rsi2) | No strategy description recorded in consulted sources. | 1 |

### Breakout (52)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [AI volume spike crypto (4h)](docs/ALL-SLEEVES.md#ai-volume-spike-crypto-4h) | Crypto spot · 4h · LINKUSDT (Binance); LINK/USD (Alpaca forward). Full recorded algorithm in the accounting entry. | 2 |
| [Public Donchian 55 trend (daily)](docs/ALL-SLEEVES.md#public-donchian-55-trend-daily) | US ETFs · 1d · 15 liquid ETFs (as RSI2). Full recorded algorithm in the accounting entry. | 1 |
| [Price-only breakout control · ADAUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#price-only-breakout-control--adausdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Price-only breakout control · ADAUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#price-only-breakout-control--adausdt-16-hour-hold-1-volume-cap-1) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Price-only breakout control · ADAUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#price-only-breakout-control--adausdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Price-only breakout control · ADAUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#price-only-breakout-control--adausdt-16-hour-hold-available-cash-sizing-1) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Price-only breakout control · ENJUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#price-only-breakout-control--enjusdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Price-only breakout control · ENJUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#price-only-breakout-control--enjusdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Price-only breakout control · LINKUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#price-only-breakout-control--linkusdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Price-only breakout control · LINKUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#price-only-breakout-control--linkusdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Donchian 20/10 breakout](docs/ALL-SLEEVES.md#donchian-2010-breakout) | Donchian 20/10 breakout Adapter for donchian — v2 interface glue ONLY (DESIGN §4a). | 1 |
| [Phoenix breakout (red-day entry)](docs/ALL-SLEEVES.md#phoenix-breakout-red-day-entry) | US equities and ETFs · 1d · 19 frozen names (with SPY and QQQ). Full recorded algorithm in the accounting entry. | 1 |
| [CCI correction pullback](docs/ALL-SLEEVES.md#cci-correction-pullback) | CCI correction pullback CCI correction pullback (Lowest(CCI27,18)<-100, @onlybreakouts) | 1 |
| [Komar momentum breakout](docs/ALL-SLEEVES.md#komar-momentum-breakout) | US equities · 1d · 411-stock Galath universe (Signal Prism US 413 without its two crypto pairs). Full recorded algorithm in the accounting entry. | 1 |
| [20-minute opening range breakout](docs/ALL-SLEEVES.md#20-minute-opening-range-breakout) | US equities · 5m · SCOPE universe: 550 US names. Full recorded algorithm in the accounting entry. | 1 |
| [Momentum breakout (legacy setup)](docs/ALL-SLEEVES.md#momentum-breakout-legacy-setup) | US equities · 1m (15-minute cycle) · SPY, QQQ, IWM, the SCOPE radar's top 100, held names. Full recorded algorithm in the accounting entry. | 1 |
| [Naive 20-day breakout](docs/ALL-SLEEVES.md#naive-20-day-breakout) | US equities · 1d · 41-name old-desk basket. Full recorded algorithm in the accounting entry. | 1 |
| [ChartsLector breakout leaders (small caps)](docs/ALL-SLEEVES.md#chartslector-breakout-leaders-small-caps) | US equities · 1d · Tracker universe, small band ($300M-$2B). Full recorded algorithm in the accounting entry. | 1 |
| [Turtle System 1](docs/ALL-SLEEVES.md#turtle-system-1) | US equities · 1d · Midna's swing basket. Full recorded algorithm in the accounting entry. | 1 |
| [Directional trigger box (SPY)](docs/ALL-SLEEVES.md#directional-trigger-box-spy) | US ETF · 10m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Opening range breakout (SPY)](docs/ALL-SLEEVES.md#opening-range-breakout-spy) | US ETF · 1m (5-minute closes) · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Three-minute trigger confirmation (SPY)](docs/ALL-SLEEVES.md#three-minute-trigger-confirmation-spy) | US ETF · 3m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Grok support and resistance (SPY)](docs/ALL-SLEEVES.md#grok-support-and-resistance-spy) | SPY shares, long and short · 1m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Teddy opening range breakout (SPY)](docs/ALL-SLEEVES.md#teddy-opening-range-breakout-spy) | SPY shares, long and short · 5m (aggregated from 1m) · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Confirmed absorption control · LINKUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#confirmed-absorption-control--linkusdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 3 |
| [Four-hour confirmed absorption · ENJUSDT](docs/ALL-SLEEVES.md#four-hour-confirmed-absorption--enjusdt-1) | Recorded by name; the accounting entry carries what the sources hold. | 3 |
| [Negative-funding breakout · ADAUSDT, 16-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#negative-funding-breakout--adausdt-16-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Negative-funding breakout · ADAUSDT, 16-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#negative-funding-breakout--adausdt-16-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Negative-funding breakout · ADAUSDT, 96-hour hold, 1% volume cap](docs/ALL-SLEEVES.md#negative-funding-breakout--adausdt-96-hour-hold-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Negative-funding breakout · ADAUSDT, 96-hour hold, available-cash sizing](docs/ALL-SLEEVES.md#negative-funding-breakout--adausdt-96-hour-hold-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Negative-funding breakout · ADAUSDT, failed breakout exit, 1% volume cap](docs/ALL-SLEEVES.md#negative-funding-breakout--adausdt-failed-breakout-exit-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Negative-funding breakout · ADAUSDT, failed breakout exit, available-cash sizing](docs/ALL-SLEEVES.md#negative-funding-breakout--adausdt-failed-breakout-exit-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Negative-funding breakout · ADAUSDT, funding reset exit, 1% volume cap](docs/ALL-SLEEVES.md#negative-funding-breakout--adausdt-funding-reset-exit-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Negative-funding breakout · ADAUSDT, funding reset exit, available-cash sizing](docs/ALL-SLEEVES.md#negative-funding-breakout--adausdt-funding-reset-exit-available-cash-sizing) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Negative-funding breakout · ADAUSDT, funding reset plus price failure, 1% volume cap](docs/ALL-SLEEVES.md#negative-funding-breakout--adausdt-funding-reset-plus-price-failure-1-volume-cap) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Negative-funding breakout · ADAUSDT, funding reset plus price failure, available-cash sizi](docs/ALL-SLEEVES.md#negative-funding-breakout--adausdt-funding-reset-plus-price-failure-available-cash-sizi) | Negative-funding breakout · ADAUSDT, funding reset plus price failure, available-cash sizing | 2 |
| [55-bar trend breakout · 1d](docs/ALL-SLEEVES.md#55-bar-trend-breakout--1d) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [55-bar trend breakout · 1d](docs/ALL-SLEEVES.md#55-bar-trend-breakout--1d-1) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [TRACE residual accumulation (daily)](docs/ALL-SLEEVES.md#trace-residual-accumulation-daily) | US equities · 1d · The Tensor research roster's liquid operating companies. Full recorded algorithm in the accounting entry. | 1 |
| [Qullamaggie breakout](docs/ALL-SLEEVES.md#qullamaggie-breakout) | US equities · 1d setup · 5m / 1m trigger · 1,838-name genome · 20 mega-caps. Full recorded algorithm in the accounting entry. | 2 |
| [Qullamaggie episodic pivot](docs/ALL-SLEEVES.md#qullamaggie-episodic-pivot) | US equities · 1d setup · 1m trigger · 1,838-name genome. Full recorded algorithm in the accounting entry. | 1 |
| [Coiled Spring genome](docs/ALL-SLEEVES.md#coiled-spring-genome) | US equities · 1h · 1d · 1wk · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 1 |
| [Daily green base expansion](docs/ALL-SLEEVES.md#daily-green-base-expansion) | US equities · 1d · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 1 |
| [Weekly cyan accumulation](docs/ALL-SLEEVES.md#weekly-cyan-accumulation) | US equities · 1wk · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 1 |
| [Midna Turtle (Midna port)](docs/ALL-SLEEVES.md#midna-turtle-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Kraken breakdown short (ADA / LINK)](docs/ALL-SLEEVES.md#kraken-breakdown-short-ada--link) | Crypto perpetual · 4h · ADA, LINK (Kraken). Full recorded algorithm in the accounting entry. | 1 |
| [Kraken crowded-long failure short (ADA / LINK)](docs/ALL-SLEEVES.md#kraken-crowded-long-failure-short-ada--link) | Crypto perpetual · 4h · ADA, LINK (Kraken). Full recorded algorithm in the accounting entry. | 1 |
| [Bilbo Golden Gate (SPY)](docs/ALL-SLEEVES.md#bilbo-golden-gate-spy) | US ETF · 1m · 1h Phase Oscillator · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Day Golden Gate (SPY)](docs/ALL-SLEEVES.md#day-golden-gate-spy) | US ETF · 1m (daily ATR levels) · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Multi-day Golden Gate (weekly ATR)](docs/ALL-SLEEVES.md#multi-day-golden-gate-weekly-atr) | US equities, index ETFs and futures · 1d (weekly ATR levels) · 1,822 US stocks + 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 1 |
| [Swing Golden Gate (monthly ATR)](docs/ALL-SLEEVES.md#swing-golden-gate-monthly-atr) | US equities, index ETFs and futures · 1d (monthly ATR levels) · 1,822 US stocks + 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 1 |
| [s_mn_turtle](docs/ALL-SLEEVES.md#s_mn_turtle) | No strategy description recorded in consulted sources. | 1 |

### Divergence reversal (15)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [David Trullas MACD divergence + Fibonacci open scalp (QQQ 1m signals, QQQM)](docs/ALL-SLEEVES.md#david-trullas-macd-divergence--fibonacci-open-scalp-qqq-1m-signals-qqqm) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Trullas variant v06: textbook divergence only (divergence quality: regular only, MACD gap](docs/ALL-SLEEVES.md#trullas-variant-v06-textbook-divergence-only-divergence-quality-regular-only-macd-gap) | Trullas variant v06: textbook divergence only (divergence quality: regular only, MACD gap >= 0.10 ATR AND R) | 1 |
| [Trullas variant v07: hidden-divergence continuation (setup type + deeper entry: hidden div](docs/ALL-SLEEVES.md#trullas-variant-v07-hidden-divergence-continuation-setup-type--deeper-entry-hidden-div) | Trullas variant v07: hidden-divergence continuation (setup type + deeper entry: hidden divergence only (trend con) | 1 |
| [Trullas variant v09: triple divergence only (confluence: takes only the full 3-lot setups](docs/ALL-SLEEVES.md#trullas-variant-v09-triple-divergence-only-confluence-takes-only-the-full-3-lot-setups) | Trullas variant v09: triple divergence only (confluence: takes only the full 3-lot setups (MACD + RSI + v) | 1 |
| [RSI × OBV daily studies](docs/ALL-SLEEVES.md#rsi--obv-daily-studies) | US equities · 1d · 19 names (MU, WDC, ANF, CLS, FFIV, AAOI, AXTI, SOXL, AEHR, FCEL, TTMI, SIMO, VICR, AG, SILJ, SPY, QQQ, NVDA, AAPL). Full recorded algorithm in the accounting entry. | 1 |
| [RSI × OBV intraday (5-minute)](docs/ALL-SLEEVES.md#rsi--obv-intraday-5-minute) | US equities · 5m · MU, ARM, SNDK, WDC, CLS, ANF, CVNA, FFIV. Full recorded algorithm in the accounting entry. | 1 |
| [Band-touch RSI divergence](docs/ALL-SLEEVES.md#band-touch-rsi-divergence) | Band-touch RSI divergence Adapter for bb_rsi_divergence — v2 plumbing only, no strategy math. | 1 |
| [Trullas divergence (QQQ 1-minute)](docs/ALL-SLEEVES.md#trullas-divergence-qqq-1-minute) | QQQ shares, long and short · 1m · QQQ. Full recorded algorithm in the accounting entry. | 1 |
| [Trullas variant v01: 2m chart (timeframe: a slightly slower chart; fewer micro-pivots)](docs/ALL-SLEEVES.md#trullas-variant-v01-2m-chart-timeframe-a-slightly-slower-chart-fewer-micro-pivots) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Trullas variant v02: 3m chart, patient window (timeframe + patience: reads a 3m chart and](docs/ALL-SLEEVES.md#trullas-variant-v02-3m-chart-patient-window-timeframe--patience-reads-a-3m-chart-and) | Trullas variant v02: 3m chart, patient window (timeframe + patience: reads a 3m chart and keeps looking unt) | 1 |
| [Trullas variant v03: 5m chart, extended window (timeframe + session length: a 5m chart nee](docs/ALL-SLEEVES.md#trullas-variant-v03-5m-chart-extended-window-timeframe--session-length-a-5m-chart-nee) | Trullas variant v03: 5m chart, extended window (timeframe + session length: a 5m chart needs ~25 min to form) | 1 |
| [Trullas variant v04: strict swings, wide stop (pivot strictness: only a swing that stands](docs/ALL-SLEEVES.md#trullas-variant-v04-strict-swings-wide-stop-pivot-strictness-only-a-swing-that-stands) | Trullas variant v04: strict swings, wide stop (pivot strictness: only a swing that stands out (>=2 ATR prom) | 1 |
| [Trullas variant v05: loose fast eye, tight stop (pivot looseness + speed: 2-bar fractals,](docs/ALL-SLEEVES.md#trullas-variant-v05-loose-fast-eye-tight-stop-pivot-looseness--speed-2-bar-fractals) | Trullas variant v05: loose fast eye, tight stop (pivot looseness + speed: 2-bar fractals, no prominence test,) | 1 |
| [Trullas variant v08: key-level reader (visual level reading: P2 must sit within 2 ATR of p](docs/ALL-SLEEVES.md#trullas-variant-v08-key-level-reader-visual-level-reading-p2-must-sit-within-2-atr-of-p) | Trullas variant v08: key-level reader (visual level reading: P2 must sit within 2 ATR of prior-day ) | 1 |
| [Trullas variant v10: scale-out runner (trade management: half off at 38.2%, runner to 66%](docs/ALL-SLEEVES.md#trullas-variant-v10-scale-out-runner-trade-management-half-off-at-382-runner-to-66) | Trullas variant v10: scale-out runner (trade management: half off at 38.2%, runner to 66% with stop) | 1 |

### Pairs and statistical arbitrage (4)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [Midna Pairs (Midna port)](docs/ALL-SLEEVES.md#midna-pairs-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Distance pairs](docs/ALL-SLEEVES.md#distance-pairs) | US equities · 1d · NYSE, NASDAQ and AMEX listings. Full recorded algorithm in the accounting entry. | 1 |
| [Distance-pair shares](docs/ALL-SLEEVES.md#distance-pair-shares) | US equities · 1d · 40 large caps. Full recorded algorithm in the accounting entry. | 1 |
| [SPY put-call parity package](docs/ALL-SLEEVES.md#spy-put-call-parity-package) | ETF options · 1d (5-minute passes) · SPY (SPY / QQQ for the pair). Full recorded algorithm in the accounting entry. | 1 |

### Options income (10)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [APEX O3: regime put-write](docs/ALL-SLEEVES.md#apex-o3-regime-put-write) | US ETFs and ETF options · 1d (monthly puts) · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O5: CHOP HARVEST](docs/ALL-SLEEVES.md#apex-o5-chop-harvest) | US ETFs and ETF options · 1d (monthly options) · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O8: FEAR put spread](docs/ALL-SLEEVES.md#apex-o8-fear-put-spread) | US ETFs and ETF options · 1d (monthly options) · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [XSP weekly put credit spread](docs/ALL-SLEEVES.md#xsp-weekly-put-credit-spread) | Index options · 1w · XSP (mini-SPX). Full recorded algorithm in the accounting entry. | 5 |
| [Fear premium put spreads (red days)](docs/ALL-SLEEVES.md#fear-premium-put-spreads-red-days) | Fear premium put spreads (red days) Adapter for fear_premium — interface glue ONLY (DESIGN §4). | 1 |
| [High-IV iron condor](docs/ALL-SLEEVES.md#high-iv-iron-condor) | Equity options · 1d (hourly checks) · 13 high-volatility names. Full recorded algorithm in the accounting entry. | 1 |
| [LEAPS momentum with covered calls](docs/ALL-SLEEVES.md#leaps-momentum-with-covered-calls) | Equity options · 1d (hourly checks) · The momentum book's names (114-name swing basket). Full recorded algorithm in the accounting entry. | 1 |
| [QQQ weekly put ladder](docs/ALL-SLEEVES.md#qqq-weekly-put-ladder) | ETF options · 1d (weekly layers) · QQQ listed puts. Full recorded algorithm in the accounting entry. | 1 |
| [SPY 30-delta wheel](docs/ALL-SLEEVES.md#spy-30-delta-wheel) | ETF options · 1d (5-minute passes) · SPY (SPY / QQQ for the pair). Full recorded algorithm in the accounting entry. | 1 |
| [OPT_WHEEL_LIFECYCLE](docs/ALL-SLEEVES.md#opt_wheel_lifecycle) | No strategy description recorded in consulted sources. | 1 |

### Options directional (37)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [Midna Opt Pairs (Midna port)](docs/ALL-SLEEVES.md#midna-opt-pairs-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna Opt Reversal (Midna port)](docs/ALL-SLEEVES.md#midna-opt-reversal-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna Opt Turtle (Midna port)](docs/ALL-SLEEVES.md#midna-opt-turtle-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [APEX N7: OMNI](docs/ALL-SLEEVES.md#apex-n7-omni) | US ETFs and ETF options · 1d (monthly options) · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O1: CONVEX](docs/ALL-SLEEVES.md#apex-o1-convex) | US ETFs and ETF options · 1d · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O7: skew risk reversal](docs/ALL-SLEEVES.md#apex-o7-skew-risk-reversal) | US ETFs and ETF options · 1d (monthly options) · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O9: OMEGA](docs/ALL-SLEEVES.md#apex-o9-omega) | US ETFs and ETF options · 1d (monthly options) · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [Earnings-drift (PEAD) put options](docs/ALL-SLEEVES.md#earnings-drift-pead-put-options) | Equity options · 1d · Names with published earnings. Full recorded algorithm in the accounting entry. | 2 |
| [Index-ETF recovery options (RSI2 / VWAP20)](docs/ALL-SLEEVES.md#index-etf-recovery-options-rsi2--vwap20) | ETF options · 1d · IWM, QQQ, SPY. Full recorded algorithm in the accounting entry. | 10 |
| [QQQ 95% core with RSI2 options](docs/ALL-SLEEVES.md#qqq-95-core-with-rsi2-options) | ETF + ETF options · 1d · QQQ core; IWM, QQQ, SPY options. Full recorded algorithm in the accounting entry. | 2 |
| [Tensor LEAPS calls](docs/ALL-SLEEVES.md#tensor-leaps-calls) | Equity options · 1w · R19 G4 signals. Full recorded algorithm in the accounting entry. | 3 |
| [Core exposure plus option reserve · RSI2, long, 0.5% risk](docs/ALL-SLEEVES.md#core-exposure-plus-option-reserve--rsi2-long-05-risk) | Recorded by name; the accounting entry carries what the sources hold. | 3 |
| [Core exposure plus option reserve · RSI2, vertical, 0.5% risk](docs/ALL-SLEEVES.md#core-exposure-plus-option-reserve--rsi2-vertical-05-risk) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [20-day VWAP reversion call spreads](docs/ALL-SLEEVES.md#20-day-vwap-reversion-call-spreads) | 20-day VWAP reversion call spreads Adapter for ema_vwap_options — interface glue ONLY (DESIGN §4). | 1 |
| [Bilbo Box calls](docs/ALL-SLEEVES.md#bilbo-box-calls) | Bilbo Box calls Adapter for bilbo_options — v2 interface glue ONLY (DESIGN §4a). | 1 |
| [Buyback before earnings (call spreads)](docs/ALL-SLEEVES.md#buyback-before-earnings-call-spreads) | Buyback before earnings (call spreads) Adapter for earnings_buyback — interface glue ONLY (DESIGN §4). | 1 |
| [Capitulation reversal calls (0-7 DTE)](docs/ALL-SLEEVES.md#capitulation-reversal-calls-0-7-dte) | Capitulation reversal calls (0-7 DTE) Adapter for capitulation_options — v2 interface glue ONLY (DESIGN §4a). | 1 |
| [RSI(2) pullback call spreads](docs/ALL-SLEEVES.md#rsi2-pullback-call-spreads) | Equity options · 1d (hourly checks) · 41-name old-desk basket. Full recorded algorithm in the accounting entry. | 1 |
| [SPY / QQQ residual option pair](docs/ALL-SLEEVES.md#spy--qqq-residual-option-pair) | ETF options · 1d (5-minute passes) · SPY (SPY / QQQ for the pair). Full recorded algorithm in the accounting entry. | 1 |
| [Listed distance-pair package](docs/ALL-SLEEVES.md#listed-distance-pair-package) | Equity options · 1d · 40 large caps. Full recorded algorithm in the accounting entry. | 1 |
| [Listed reversal call spread](docs/ALL-SLEEVES.md#listed-reversal-call-spread) | Equity options · 1d (monthly) · 40 large caps. Full recorded algorithm in the accounting entry. | 1 |
| [Listed Turtle ATM call](docs/ALL-SLEEVES.md#listed-turtle-atm-call) | Equity options · 1d · Midna's listed surface set. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor fires as calls](docs/ALL-SLEEVES.md#tensor-fires-as-calls) | Equity options · 1w · 1,822 US stocks (the store_v1 survivors), their listed calls. Full recorded algorithm in the accounting entry. | 1 |
| [15.87 Rule (SPY 0DTE)](docs/ALL-SLEEVES.md#1587-rule-spy-0dte) | 15.87 Rule - SPY same-day options | 1 |
| [InvestAndBeFree double MACD (SPY and QQQ options)](docs/ALL-SLEEVES.md#investandbefree-double-macd-spy-and-qqq-options) | SPY and QQQ options (long premium) · 4H, daily, weekly stack · SPY, QQQ. Full recorded algorithm in the accounting entry. | 1 |
| [PRZM Zero recreation (SPY)](docs/ALL-SLEEVES.md#przm-zero-recreation-spy) | SPY shares (signal engine) · 1m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [SATY day system (SPY 0DTE)](docs/ALL-SLEEVES.md#saty-day-system-spy-0dte) | Saty Day - SPY same-day options | 1 |
| [Sol's Saty engine (SPY options)](docs/ALL-SLEEVES.md#sols-saty-engine-spy-options) | Saty Sol - SPY same-day options | 1 |
| [Opening-range options · long, 0.5% risk](docs/ALL-SLEEVES.md#opening-range-options--long-05-risk) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Opening-range options · long, 2.0% risk](docs/ALL-SLEEVES.md#opening-range-options--long-20-risk) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [BOLT event tilt (SPY / QQQ)](docs/ALL-SLEEVES.md#bolt-event-tilt-spy--qqq) | US ETFs (SPY, QQQ) · Event windows (about 10 sessions) · SPY, QQQ; SPX and NDX options as information. Full recorded algorithm in the accounting entry. | 1 |
| [Tail put after a -3% day](docs/ALL-SLEEVES.md#tail-put-after-a--3-day) | ETF options · 1d (5-minute passes) · SPY (SPY / QQQ for the pair). Full recorded algorithm in the accounting entry. | 1 |
| [Milkman 0DTE (SPX)](docs/ALL-SLEEVES.md#milkman-0dte-spx) | SPX index options (0DTE) · Intraday · SPX. Full recorded algorithm in the accounting entry. | 1 |
| [Post-earnings response · long, 0.5% risk](docs/ALL-SLEEVES.md#post-earnings-response--long-05-risk) | Recorded by name; the accounting entry carries what the sources hold. | 3 |
| [Post-earnings response · long, 2.0% risk](docs/ALL-SLEEVES.md#post-earnings-response--long-20-risk) | Recorded by name; the accounting entry carries what the sources hold. | 3 |
| [Post-earnings response · vertical, 0.5% risk](docs/ALL-SLEEVES.md#post-earnings-response--vertical-05-risk) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Post-earnings response · vertical, 2.0% risk](docs/ALL-SLEEVES.md#post-earnings-response--vertical-20-risk) | Recorded by name; the accounting entry carries what the sources hold. | 2 |

### Volatility (36)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [Midna W cyan mid-VIX (Midna port)](docs/ALL-SLEEVES.md#midna-w-cyan-mid-vix-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [APEX C3: Follow-through](docs/ALL-SLEEVES.md#apex-c3-follow-through) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX C4: Broken Hedge](docs/ALL-SLEEVES.md#apex-c4-broken-hedge) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, IEF, GLD, UUP, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX C6: SLINGSHOT](docs/ALL-SLEEVES.md#apex-c6-slingshot) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX E1: VIX term-structure gate](docs/ALL-SLEEVES.md#apex-e1-vix-term-structure-gate) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX E2: Double 7 dip overlay](docs/ALL-SLEEVES.md#apex-e2-double-7-dip-overlay) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX E3 / v1.1: defensive Treasuries](docs/ALL-SLEEVES.md#apex-e3--v11-defensive-treasuries) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, IEF, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX E4: rolling tail puts](docs/ALL-SLEEVES.md#apex-e4-rolling-tail-puts) | US ETFs and ETF options · 1d (monthly puts) · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX E5: semiconductor tilt](docs/ALL-SLEEVES.md#apex-e5-semiconductor-tilt) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, SMH, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX E6: overnight boost](docs/ALL-SLEEVES.md#apex-e6-overnight-boost) | US ETFs (incl. 3× leveraged) · 1d (overnight boost) · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX N1: Duration Shield](docs/ALL-SLEEVES.md#apex-n1-duration-shield) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX N2: Silicon Switch](docs/ALL-SLEEVES.md#apex-n2-silicon-switch) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, SMH, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX N3 / N4: PRISM multi-asset trend](docs/ALL-SLEEVES.md#apex-n3--n4-prism-multi-asset-trend) | US ETFs and Bitcoin · 1d · QQQ, TQQQ, IEF, GLD, USO, UUP, SMH, BTC/USD, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O10: LEAPS + Variance Value](docs/ALL-SLEEVES.md#apex-o10-leaps--variance-value) | US ETFs and ETF options · 1d (monthly options) · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O11: APEX + Variance Value](docs/ALL-SLEEVES.md#apex-o11-apex--variance-value) | US ETFs and ETF options · 1d (monthly options) · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O12: hybrid LEAPS + QQQ trim](docs/ALL-SLEEVES.md#apex-o12-hybrid-leaps--qqq-trim) | US ETFs and ETF options · 1d · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O2: LEAPS-APEX](docs/ALL-SLEEVES.md#apex-o2-leaps-apex) | US ETFs and ETF options · 1d · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O4: PHOENIX](docs/ALL-SLEEVES.md#apex-o4-phoenix) | US ETFs and ETF options · 1d · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX O6: Variance Value](docs/ALL-SLEEVES.md#apex-o6-variance-value) | US ETFs and ETF options · 1d (monthly options) · QQQ, TQQQ, BIL; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX-50F Nasdaq trend × volatility](docs/ALL-SLEEVES.md#apex-50f-nasdaq-trend--volatility) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [Public BB/KC squeeze (daily)](docs/ALL-SLEEVES.md#public-bbkc-squeeze-daily) | US ETFs · 1d · 15 liquid ETFs (as RSI2). Full recorded algorithm in the accounting entry. | 2 |
| [Aurelia Nasdaq + gold allocation](docs/ALL-SLEEVES.md#aurelia-nasdaq--gold-allocation) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, GLD, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [Own-IV straddle](docs/ALL-SLEEVES.md#own-iv-straddle) | ETF options · 1d (5-minute passes) · SPY (SPY / QQQ for the pair). Full recorded algorithm in the accounting entry. | 1 |
| [Phase compression breakout (daily)](docs/ALL-SLEEVES.md#phase-compression-breakout-daily) | US equities · 1d · 48-name phase universe. Full recorded algorithm in the accounting entry. | 1 |
| [Release straddle (CPI, jobs, FOMC)](docs/ALL-SLEEVES.md#release-straddle-cpi-jobs-fomc) | ETF options · 1d (5-minute passes) · SPY (SPY / QQQ for the pair). Full recorded algorithm in the accounting entry. | 1 |
| [VXX call tail hedge](docs/ALL-SLEEVES.md#vxx-call-tail-hedge) | ETP options · 1d (hourly checks) · VXX. Full recorded algorithm in the accounting entry. | 1 |
| [Daily Bilbo Box](docs/ALL-SLEEVES.md#daily-bilbo-box) | US equities, index ETFs and futures · 1d · 1,822 US stocks + 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 1 |
| [Daily compression expansion](docs/ALL-SLEEVES.md#daily-compression-expansion) | US equities, index ETFs and futures · 1d · 1,822 US stocks + 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 1 |
| [Ten-minute compression release (SPY)](docs/ALL-SLEEVES.md#ten-minute-compression-release-spy) | US ETF · 10m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Three-minute compression drift (SPY)](docs/ALL-SLEEVES.md#three-minute-compression-drift-spy) | US ETF · 3m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [Volatility-squeeze breakout · 1d](docs/ALL-SLEEVES.md#volatility-squeeze-breakout--1d) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Volatility-squeeze breakout · 1d](docs/ALL-SLEEVES.md#volatility-squeeze-breakout--1d-1) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [ChartsLector market-fear rebound (QQQ)](docs/ALL-SLEEVES.md#chartslector-market-fear-rebound-qqq) | US ETF · 1d · QQQ. Full recorded algorithm in the accounting entry. | 1 |
| [OPT_OWN_IV_RESIDUAL](docs/ALL-SLEEVES.md#opt_own_iv_residual) | No strategy description recorded in consulted sources. | 1 |
| [OPT_RELEASE_CONVEXITY](docs/ALL-SLEEVES.md#opt_release_convexity) | No strategy description recorded in consulted sources. | 1 |
| [TRADER_SQUEEZE20](docs/ALL-SLEEVES.md#trader_squeeze20) | No strategy description recorded in consulted sources. | 1 |

### Market timing and rotation (20)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [Midna W cyan breadth (Midna port)](docs/ALL-SLEEVES.md#midna-w-cyan-breadth-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [APEX C2: Sector Kings](docs/ALL-SLEEVES.md#apex-c2-sector-kings) | US ETFs · 1d (monthly picks) · XLK, XLF, XLE, XLV, XLP, XLI, XLB, XLU, XLY, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX E7: turn-of-month boost](docs/ALL-SLEEVES.md#apex-e7-turn-of-month-boost) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [R17 ETF ladder rules](docs/ALL-SLEEVES.md#r17-etf-ladder-rules) | US ETFs · 1d, monthly · QQQ, SPY, SMH and the 11 sector SPDRs. Full recorded algorithm in the accounting entry. | 2 |
| [R19 ETF books: momentum leader rotation](docs/ALL-SLEEVES.md#r19-etf-books-momentum-leader-rotation) | US ETFs · 1d, monthly rebalance · QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY; QLD for the 2x controls. Full recorded algorithm in the accounting entry. | 4 |
| [60-day momentum rotation](docs/ALL-SLEEVES.md#60-day-momentum-rotation) | US equities · 1d (weekly) · 41-name old-desk basket. Full recorded algorithm in the accounting entry. | 1 |
| [QLD weekly timing](docs/ALL-SLEEVES.md#qld-weekly-timing) | Leveraged ETF · 1w · QLD (QQQ signal). Full recorded algorithm in the accounting entry. | 1 |
| [ES Monday clock (SPY)](docs/ALL-SLEEVES.md#es-monday-clock-spy) | US ETF · 1m (06:00-16:00 ET) · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [O'Neil follow-through-day race](docs/ALL-SLEEVES.md#oneil-follow-through-day-race) | US index ETFs and futures · 1d · 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 2 |
| [Weekday open-to-close (Monday)](docs/ALL-SLEEVES.md#weekday-open-to-close-monday) | US index ETFs and futures · 1d · 14 index ETFs and futures. Full recorded algorithm in the accounting entry. | 2 |
| [FinRL-X adaptive rotation](docs/ALL-SLEEVES.md#finrl-x-adaptive-rotation) | US equities and ETFs · 1w · 21 stocks and ETFs in three groups, plus SPY and QQQ. Full recorded algorithm in the accounting entry. | 1 |
| [Midna QQQ→TZA hedge (Midna port)](docs/ALL-SLEEVES.md#midna-qqqtza-hedge-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [ETF leader confirmed across two sources · 150% exposure](docs/ALL-SLEEVES.md#etf-leader-confirmed-across-two-sources--150-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [ETF leader confirmed across two sources · 98% exposure](docs/ALL-SLEEVES.md#etf-leader-confirmed-across-two-sources--98-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [ETF leader excluding semiconductors · 150% exposure](docs/ALL-SLEEVES.md#etf-leader-excluding-semiconductors--150-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [ETF leader excluding semiconductors · 98% exposure](docs/ALL-SLEEVES.md#etf-leader-excluding-semiconductors--98-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [ETF leader with unchanged-share holding · 150% exposure](docs/ALL-SLEEVES.md#etf-leader-with-unchanged-share-holding--150-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [ETF leader with unchanged-share holding · 98% exposure](docs/ALL-SLEEVES.md#etf-leader-with-unchanged-share-holding--98-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Two-source ETF leader with unchanged-share holding · 150% exposure](docs/ALL-SLEEVES.md#two-source-etf-leader-with-unchanged-share-holding--150-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Two-source ETF leader with unchanged-share holding · 98% exposure](docs/ALL-SLEEVES.md#two-source-etf-leader-with-unchanged-share-holding--98-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |

### Crypto basis and funding (6)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [R19 crypto breakout and negative-funding squeeze](docs/ALL-SLEEVES.md#r19-crypto-breakout-and-negative-funding-squeeze) | Crypto spot · 4h · ADAUSDT, ENJUSDT, LINKUSDT. Full recorded algorithm in the accounting entry. | 22 |
| [Kraken basis repair (ADA / LINK)](docs/ALL-SLEEVES.md#kraken-basis-repair-ada--link) | Crypto spot + perpetual · 4h · ADA, LINK (Kraken). Full recorded algorithm in the accounting entry. | 1 |
| [Milkman daily rules on crypto-linked stocks](docs/ALL-SLEEVES.md#milkman-daily-rules-on-crypto-linked-stocks) | US equities · 1d · 134 crypto-linked US stocks. Full recorded algorithm in the accounting entry. | 1 |
| [R19_ADAUSDT_BASIS_REPAIR_COLLECTOR](docs/ALL-SLEEVES.md#r19_adausdt_basis_repair_collector) | No strategy description recorded in consulted sources. | 1 |
| [R19_ENJUSDT_BASIS_REPAIR_COLLECTOR](docs/ALL-SLEEVES.md#r19_enjusdt_basis_repair_collector) | No strategy description recorded in consulted sources. | 1 |
| [R19_LINKUSDT_BASIS_REPAIR_COLLECTOR](docs/ALL-SLEEVES.md#r19_linkusdt_basis_repair_collector) | No strategy description recorded in consulted sources. | 1 |

### Forecast and ML models (100)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [Tensor relative-market cohort · cash funded, all volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-relative-market-cohort--cash-funded-all-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor cyan expansion · cash funded, all volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-cyan-expansion--cash-funded-all-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor cyan expansion · cash funded, higher recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-cyan-expansion--cash-funded-higher-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor cyan expansion · cash funded, quieter recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-cyan-expansion--cash-funded-quieter-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor cyan expansion · one-session delay, all volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-cyan-expansion--one-session-delay-all-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor cyan expansion · one-session delay, higher recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-cyan-expansion--one-session-delay-higher-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor cyan expansion · one-session delay, quieter recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-cyan-expansion--one-session-delay-quieter-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor cyan expansion · QQQ reserve, all volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-cyan-expansion--qqq-reserve-all-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor cyan expansion · QQQ reserve, higher recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-cyan-expansion--qqq-reserve-higher-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor cyan expansion · QQQ reserve, quieter recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-cyan-expansion--qqq-reserve-quieter-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · cash funded, all volatility, 10 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--cash-funded-all-volatility-10-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · cash funded, all volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--cash-funded-all-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · cash funded, higher recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--cash-funded-higher-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · cash funded, quieter recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--cash-funded-quieter-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · dip-or-five-session wait, all volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--dip-or-five-session-wait-all-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · one-session delay, all volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--one-session-delay-all-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · one-session delay, higher recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--one-session-delay-higher-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · one-session delay, quieter recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--one-session-delay-quieter-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · QQQ reserve, all volatility, 10 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--qqq-reserve-all-volatility-10-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · QQQ reserve, all volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--qqq-reserve-all-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · QQQ reserve, higher recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--qqq-reserve-higher-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Tensor green value / recovery · QQQ reserve, quieter recent volatility, 25 positions](docs/ALL-SLEEVES.md#tensor-green-value--recovery--qqq-reserve-quieter-recent-volatility-25-positions) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [APEX C5: REFLEX](docs/ALL-SLEEVES.md#apex-c5-reflex) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX N5: GESTALT analog engine](docs/ALL-SLEEVES.md#apex-n5-gestalt-analog-engine) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [APEX N6: GESTALT × APEX](docs/ALL-SLEEVES.md#apex-n6-gestalt--apex) | US ETFs (incl. 3× leveraged) · 1d · QQQ, TQQQ, BIL. Full recorded algorithm in the accounting entry. | 1 |
| [Daily20 tree-model forecasts](docs/ALL-SLEEVES.md#daily20-tree-model-forecasts) | US equities · 1d · Fixed 1,815-name enrollment. Full recorded algorithm in the accounting entry. | 2 |
| [R19 weekly Tensor beta M2 52-week cohort](docs/ALL-SLEEVES.md#r19-weekly-tensor-beta-m2-52-week-cohort) | US equities · 1w · Frozen 1,838-name research cohort. Full recorded algorithm in the accounting entry. | 1 |
| [R19 weekly Tensor C1 cyan ownership](docs/ALL-SLEEVES.md#r19-weekly-tensor-c1-cyan-ownership) | US equities · 1w · Frozen 1,838-name research cohort. Full recorded algorithm in the accounting entry. | 1 |
| [R19 weekly Tensor G4 green ownership](docs/ALL-SLEEVES.md#r19-weekly-tensor-g4-green-ownership) | US equities · 1w · Frozen 1,838-name research cohort. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor state repair (hourly / weekly)](docs/ALL-SLEEVES.md#tensor-state-repair-hourly--weekly) | US equities · 1h · 1w · 1,820 hourly / 1,813 weekly names. Full recorded algorithm in the accounting entry. | 1 |
| [Daily Cyan GBM](docs/ALL-SLEEVES.md#daily-cyan-gbm) | Daily Cyan GBM Adapter for daily_cyan_gbm — v2 interface glue ONLY (DESIGN §4a). | 1 |
| [Daily Cyan small-cap rule](docs/ALL-SLEEVES.md#daily-cyan-small-cap-rule) | US equities · 1d · 1,838-name genome. Full recorded algorithm in the accounting entry. | 1 |
| [Daily Green turn-of-month rule](docs/ALL-SLEEVES.md#daily-green-turn-of-month-rule) | US equities · 1d · 1,838-name genome. Full recorded algorithm in the accounting entry. | 1 |
| [Hourly Cyan range-expansion rule](docs/ALL-SLEEVES.md#hourly-cyan-range-expansion-rule) | US equities · 1h · 41-name old-desk basket. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor 1H swing flagship](docs/ALL-SLEEVES.md#tensor-1h-swing-flagship) | US equities · 1h · 41-name old-desk basket. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor red-dip buys on fear days](docs/ALL-SLEEVES.md#tensor-red-dip-buys-on-fear-days) | US equities · Intraday · 1h signals · 41-name old-desk basket. Full recorded algorithm in the accounting entry. | 1 |
| [Weekly Cyan momentum ADX rule](docs/ALL-SLEEVES.md#weekly-cyan-momentum-adx-rule) | US equities · 1w · 1,838-name genome. Full recorded algorithm in the accounting entry. | 2 |
| [Weekly swing high-beta WaveTrend rule](docs/ALL-SLEEVES.md#weekly-swing-high-beta-wavetrend-rule) | US equities · 1w · 1,838-name genome. Full recorded algorithm in the accounting entry. | 1 |
| [Anna seven-vote printer](docs/ALL-SLEEVES.md#anna-seven-vote-printer) | US equities · 1d · 13-name dashboard watchlist (SATL, SKYQ, RDW, INDI, SPY, QQQ, NVDA, MU, AAPL, AMD, TSLA, WULF, POET). Full recorded algorithm in the accounting entry. | 1 |
| [Tensor 2 washout / reclaim printer](docs/ALL-SLEEVES.md#tensor-2-washout--reclaim-printer) | US equities and ETFs · 1h · Galath's 13-name default watch list. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor edge v0.1 (G1 / G2 / C1)](docs/ALL-SLEEVES.md#tensor-edge-v01-g1--g2--c1) | US equities · 1d · 1w · Tensor research roster: 1,838 US names. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor frozen phenotypes v4](docs/ALL-SLEEVES.md#tensor-frozen-phenotypes-v4) | US equities · 1d · 1w · Tensor research roster: 1,838 US names. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor HTF conditional holdout (H1-H8)](docs/ALL-SLEEVES.md#tensor-htf-conditional-holdout-h1-h8) | US equities · 1d · 1w · Tensor research roster's operating companies. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor HTF relay (T1-T7)](docs/ALL-SLEEVES.md#tensor-htf-relay-t1-t7) | US equities · 1d · 1w · Tensor research roster: 1,838 US names. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor phenotype experiment (HIGH_BREAK_4)](docs/ALL-SLEEVES.md#tensor-phenotype-experiment-high_break_4) | US equities · 1d · 1w · Tensor research roster: 1,838 US names. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor weekly color forward shadow (FG / FC)](docs/ALL-SLEEVES.md#tensor-weekly-color-forward-shadow-fg--fc) | US equities · 1w · Tensor research roster's operating companies. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor weekly cyan confirmation (CY01-CY18)](docs/ALL-SLEEVES.md#tensor-weekly-cyan-confirmation-cy01-cy18) | US equities · 1w · Tensor research roster's operating companies. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor weekly green / cyan deep confirmation (WG / WC)](docs/ALL-SLEEVES.md#tensor-weekly-green--cyan-deep-confirmation-wg--wc) | US equities · 1w · Tensor research roster's operating companies. Full recorded algorithm in the accounting entry. | 1 |
| [Daily Cyan desk feed](docs/ALL-SLEEVES.md#daily-cyan-desk-feed) | US equities · 1d · Lab panel names. Full recorded algorithm in the accounting entry. | 1 |
| [Daily Green under $5](docs/ALL-SLEEVES.md#daily-green-under-5) | US equities · 1d · Tracker universe. Full recorded algorithm in the accounting entry. | 1 |
| [Intraweek early entry](docs/ALL-SLEEVES.md#intraweek-early-entry) | Intraweek early entry (WAIT) | 1 |
| [Lab 1D Green trees](docs/ALL-SLEEVES.md#lab-1d-green-trees) | US equities · 1d · Lab panel names. Full recorded algorithm in the accounting entry. | 1 |
| [Lab 1W Cyan books](docs/ALL-SLEEVES.md#lab-1w-cyan-books) | US equities · 1w · Lab panel names. Full recorded algorithm in the accounting entry. | 1 |
| [Lab 1W Swing covered](docs/ALL-SLEEVES.md#lab-1w-swing-covered) | US equities · 1w · Lab panel names. Full recorded algorithm in the accounting entry. | 1 |
| [R2 Daily Cyan extended](docs/ALL-SLEEVES.md#r2-daily-cyan-extended) | R2 Daily Cyan extended (WAIT) | 1 |
| [Tensor tracker lanes (1H / 1D / 1W)](docs/ALL-SLEEVES.md#tensor-tracker-lanes-1h--1d--1w) | US equities · 1h · 1d · 1w · The tracker's canonical universe. Full recorded algorithm in the accounting entry. | 3 |
| [Weekly Cyan tier A](docs/ALL-SLEEVES.md#weekly-cyan-tier-a) | US equities · 1w · Tracker universe by PIT SEC band. Full recorded algorithm in the accounting entry. | 1 |
| [Weekly Green tier A small](docs/ALL-SLEEVES.md#weekly-green-tier-a-small) | US equities · 1w · Tracker universe, small band. Full recorded algorithm in the accounting entry. | 1 |
| [Forward lab accounts (Tensor scan)](docs/ALL-SLEEVES.md#forward-lab-accounts-tensor-scan) | US equities · 1d · 1w · Midna's daily panel. Full recorded algorithm in the accounting entry. | 1 |
| [Hourly Tensor playbook](docs/ALL-SLEEVES.md#hourly-tensor-playbook) | US equities · 1h · Midna's swing basket. Full recorded algorithm in the accounting entry. | 1 |
| [Kronos-base TopkDropout](docs/ALL-SLEEVES.md#kronos-base-topkdropout) | US equities · 1d (10-session cycle) · 24 frozen names. Full recorded algorithm in the accounting entry. | 2 |
| [Big Winners weekly Tensor sleeve](docs/ALL-SLEEVES.md#big-winners-weekly-tensor-sleeve) | US equities · 1w · 1,822 US stocks (the store_v1 survivors). Full recorded algorithm in the accounting entry. | 1 |
| [Milkman filters on Tensor lanes](docs/ALL-SLEEVES.md#milkman-filters-on-tensor-lanes) | US equities · 1w · 1d · 1,822 US stocks (the store_v1 survivors). Full recorded algorithm in the accounting entry. | 1 |
| [Tensor breadth timing (IWM)](docs/ALL-SLEEVES.md#tensor-breadth-timing-iwm) | US ETF · 1w · IWM. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor ratio-chart signals](docs/ALL-SLEEVES.md#tensor-ratio-chart-signals) | US equities · 1w · 1,822 US stocks (the store_v1 survivors). Full recorded algorithm in the accounting entry. | 1 |
| [AlphaMemo factor book](docs/ALL-SLEEVES.md#alphamemo-factor-book) | US equities · 1d · Frozen 640-name roster. Full recorded algorithm in the accounting entry. | 1 |
| [AlphaQCM factor rotation](docs/ALL-SLEEVES.md#alphaqcm-factor-rotation) | US equities · 1d (every 20 sessions) · Frozen 100-stock roster (the most traded of 2016-2020). Full recorded algorithm in the accounting entry. | 1 |
| [News-conditioned 12-1 leadership](docs/ALL-SLEEVES.md#news-conditioned-12-1-leadership) | US equities · 1mo ranking · 1h timing · S&P 500 (current members). Full recorded algorithm in the accounting entry. | 1 |
| [QuantaAlpha factor book](docs/ALL-SLEEVES.md#quantaalpha-factor-book) | US equities · 1d · Frozen 640-name roster. Full recorded algorithm in the accounting entry. | 1 |
| [Tensor rejection memory (MID21)](docs/ALL-SLEEVES.md#tensor-rejection-memory-mid21) | US equities · 1d · Frozen 21-stock basket. Full recorded algorithm in the accounting entry. | 1 |
| [Daily price and volume model · daily](docs/ALL-SLEEVES.md#daily-price-and-volume-model--daily) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Daily price, volume and trend model · daily](docs/ALL-SLEEVES.md#daily-price-volume-and-trend-model--daily) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Tensor 1H Swing (v615)](docs/ALL-SLEEVES.md#tensor-1h-swing-v615) | US equities · 1h · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 2 |
| [D20TENSOR](docs/ALL-SLEEVES.md#d20tensor) | No strategy description recorded in consulted sources. | 1 |
| [Lab 1D Green trees (test)](docs/ALL-SLEEVES.md#lab-1d-green-trees-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna D green $10-20 (Midna port)](docs/ALL-SLEEVES.md#midna-d-green-10-20-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna Daily cyan trees (Midna port)](docs/ALL-SLEEVES.md#midna-daily-cyan-trees-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna Hourly 1D (Midna port)](docs/ALL-SLEEVES.md#midna-hourly-1d-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna Kronos (Midna port)](docs/ALL-SLEEVES.md#midna-kronos-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna W cyan high ADX (Midna port)](docs/ALL-SLEEVES.md#midna-w-cyan-high-adx-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna Hourly (Midna port)](docs/ALL-SLEEVES.md#midna-hourly-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [1W Swing stress pockets (test)](docs/ALL-SLEEVES.md#1w-swing-stress-pockets-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Lab 1W Swing covered (test)](docs/ALL-SLEEVES.md#lab-1w-swing-covered-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [R19 hourly confirmed swing](docs/ALL-SLEEVES.md#r19-hourly-confirmed-swing) | US equities · 1h · Frozen 42-name list. Full recorded algorithm in the accounting entry. | 1 |
| [Confirmed hourly swing · minimum 1-ATR stop distance, no extra bar delay](docs/ALL-SLEEVES.md#confirmed-hourly-swing--minimum-1-atr-stop-distance-no-extra-bar-delay) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Confirmed hourly swing · minimum 1-ATR stop distance, one-bar delay](docs/ALL-SLEEVES.md#confirmed-hourly-swing--minimum-1-atr-stop-distance-one-bar-delay) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Confirmed hourly swing · native stop, no extra bar delay](docs/ALL-SLEEVES.md#confirmed-hourly-swing--native-stop-no-extra-bar-delay) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Confirmed hourly swing · native stop, one-bar delay](docs/ALL-SLEEVES.md#confirmed-hourly-swing--native-stop-one-bar-delay) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Lab rule books (1D / 1W)](docs/ALL-SLEEVES.md#lab-rule-books-1d--1w) | US equities · 1d · 1w · Lab panel names. Full recorded algorithm in the accounting entry. | 2 |
| [CRG own-stock filing surprise](docs/ALL-SLEEVES.md#crg-own-stock-filing-surprise) | US equities and ETFs · 1d (20-session hold) · CAT, DE, MSFT. Full recorded algorithm in the accounting entry. | 1 |
| [Hourly multi-indicator recovery · hourly](docs/ALL-SLEEVES.md#hourly-multi-indicator-recovery--hourly) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Weekly multi-indicator recovery · weekly](docs/ALL-SLEEVES.md#weekly-multi-indicator-recovery--weekly) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Swing Transition (1H)](docs/ALL-SLEEVES.md#swing-transition-1h) | US equities · 1h · AG, CMG, CRDO, FLY, LTBR, UAMY, VRT, XPEV. Full recorded algorithm in the accounting entry. | 1 |
| [D20PV](docs/ALL-SLEEVES.md#d20pv) | No strategy description recorded in consulted sources. | 1 |
| [H1STATE](docs/ALL-SLEEVES.md#h1state) | No strategy description recorded in consulted sources. | 1 |
| [s_mn_gbm_1d_cyan](docs/ALL-SLEEVES.md#s_mn_gbm_1d_cyan) | No strategy description recorded in consulted sources. | 1 |
| [s_mn_hourly_1d](docs/ALL-SLEEVES.md#s_mn_hourly_1d) | No strategy description recorded in consulted sources. | 1 |
| [s_mn_w_cyan_adx](docs/ALL-SLEEVES.md#s_mn_w_cyan_adx) | No strategy description recorded in consulted sources. | 1 |
| [s_wait_r2_dcyan](docs/ALL-SLEEVES.md#s_wait_r2_dcyan) | No strategy description recorded in consulted sources. | 1 |
| [WSTATE](docs/ALL-SLEEVES.md#wstate) | No strategy description recorded in consulted sources. | 1 |

### Buy and hold (12)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [QLD buy and hold · 100% exposure](docs/ALL-SLEEVES.md#qld-buy-and-hold--100-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [QLD monthly rebalance · 100% exposure](docs/ALL-SLEEVES.md#qld-monthly-rebalance--100-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [QQQ and QLD equal-weight buy and hold · 100% exposure](docs/ALL-SLEEVES.md#qqq-and-qld-equal-weight-buy-and-hold--100-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [QQQ and QLD equal-weight monthly rebalance · 100% exposure](docs/ALL-SLEEVES.md#qqq-and-qld-equal-weight-monthly-rebalance--100-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [QQQ buy and hold · 100% exposure](docs/ALL-SLEEVES.md#qqq-buy-and-hold--100-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 3 |
| [QQQ monthly rebalance · 150% exposure](docs/ALL-SLEEVES.md#qqq-monthly-rebalance--150-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [QQQ monthly rebalance · 98% exposure](docs/ALL-SLEEVES.md#qqq-monthly-rebalance--98-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [S&P 500 ETF buy and hold · 100% exposure](docs/ALL-SLEEVES.md#sp-500-etf-buy-and-hold--100-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 3 |
| [S&P 500 ETF monthly rebalance · 150% exposure](docs/ALL-SLEEVES.md#sp-500-etf-monthly-rebalance--150-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [S&P 500 ETF monthly rebalance · 98% exposure](docs/ALL-SLEEVES.md#sp-500-etf-monthly-rebalance--98-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Semiconductor ETF buy and hold · 150% exposure](docs/ALL-SLEEVES.md#semiconductor-etf-buy-and-hold--150-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |
| [Semiconductor ETF buy and hold · 98% exposure](docs/ALL-SLEEVES.md#semiconductor-etf-buy-and-hold--98-exposure) | Recorded by name; the accounting entry carries what the sources hold. | 2 |

### Other (51)

| Strategy | What the record shows | Variants |
|---|---|---:|
| [Lab rule 1D (test)](docs/ALL-SLEEVES.md#lab-rule-1d-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [legacy exit (hidden)](docs/ALL-SLEEVES.md#legacy-exit-hidden) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna Moonshot (Midna port)](docs/ALL-SLEEVES.md#midna-moonshot-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna QQQ Ladder (Midna port)](docs/ALL-SLEEVES.md#midna-qqq-ladder-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna Nostop (Midna port)](docs/ALL-SLEEVES.md#midna-nostop-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Lab rule 1W (test)](docs/ALL-SLEEVES.md#lab-rule-1w-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Midna Hourly 1W (Midna port)](docs/ALL-SLEEVES.md#midna-hourly-1w-midna-port) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Moonshot (test)](docs/ALL-SLEEVES.md#moonshot-test) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [OLX R1/R2 books for the other lanes (WAIT)](docs/ALL-SLEEVES.md#olx-r1r2-books-for-the-other-lanes-wait) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [Q14 pxcap5 book (WAIT)](docs/ALL-SLEEVES.md#q14-pxcap5-book-wait) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [APEX C7: COUNCIL](docs/ALL-SLEEVES.md#apex-c7-council) | US ETFs, ETF options and Bitcoin · 1d (monthly options) · QQQ, TQQQ, GLD, BIL, BTC/USD; QQQ listed options. Full recorded algorithm in the accounting entry. | 1 |
| [APEX QQQ benchmark](docs/ALL-SLEEVES.md#apex-qqq-benchmark) | US ETFs · 1d · QQQ. Full recorded algorithm in the accounting entry. | 1 |
| [R19 causal overnight hold](docs/ALL-SLEEVES.md#r19-causal-overnight-hold) | US equities · 30m · Frozen 42-name list. Full recorded algorithm in the accounting entry. | 1 |
| [R4 blowoff (daily / hourly)](docs/ALL-SLEEVES.md#r4-blowoff-daily--hourly) | US equities · 1d · 1h · 1,838-name research genome (daily) · 41-name old-desk basket (hourly). Full recorded algorithm in the accounting entry. | 2 |
| [Winner confluence (weekly qualifiers)](docs/ALL-SLEEVES.md#winner-confluence-weekly-qualifiers) | Winner confluence (weekly qualifiers) Adapter for confluence — v2 interface glue ONLY (DESIGN §4a). | 1 |
| [Echo swing](docs/ALL-SLEEVES.md#echo-swing) | US equities · Posts (3-minute sweeps) · 1d · Names in @EchoAnalysis's buy posts. Full recorded algorithm in the accounting entry. | 1 |
| [Scanner book swing](docs/ALL-SLEEVES.md#scanner-book-swing) | US equities · 1d · 5m session tape · 411-stock Galath universe (Signal Prism US 413 without its two crypto pairs). Full recorded algorithm in the accounting entry. | 1 |
| [Sector-first bottom](docs/ALL-SLEEVES.md#sector-first-bottom) | US equities · 1d · 5m session tape · 411-stock Galath universe (Signal Prism US 413 without its two crypto pairs). Full recorded algorithm in the accounting entry. | 1 |
| [Parallax](docs/ALL-SLEEVES.md#parallax) | US equities · 1d · SCOPE universe: 550 US names. Full recorded algorithm in the accounting entry. | 1 |
| [FLOW short volume / FTD / dark pool](docs/ALL-SLEEVES.md#flow-short-volume--ftd--dark-pool) | FLOW short volume / FTD / dark-pool (WAIT) | 1 |
| [Moonshot weekly lane](docs/ALL-SLEEVES.md#moonshot-weekly-lane) | US equities · 1w · Tracker universe · Midna's swing basket. Full recorded algorithm in the accounting entry. | 1 |
| [OLX R1/R2 books](docs/ALL-SLEEVES.md#olx-r1r2-books) | US equities · 1d · Lab panel names. Full recorded algorithm in the accounting entry. | 1 |
| [QQQ flip5 TZA hedge](docs/ALL-SLEEVES.md#qqq-flip5-tza-hedge) | Leveraged ETF · 1d · TZA (QQQ signal). Full recorded algorithm in the accounting entry. | 1 |
| [ATR level cascade (SPY)](docs/ALL-SLEEVES.md#atr-level-cascade-spy) | US ETF · 1m · SPY. Full recorded algorithm in the accounting entry. | 1 |
| [AIRT auction impulse](docs/ALL-SLEEVES.md#airt-auction-impulse) | US equities · Intraday (≤ 30 minutes) · Registered morning episodes. Full recorded algorithm in the accounting entry. | 1 |
| [CARM recovery memory](docs/ALL-SLEEVES.md#carm-recovery-memory) | US equities and QQQ · Intraday (≤ 30 minutes) · QQQ and registered episode stocks. Full recorded algorithm in the accounting entry. | 1 |
| [CER entitlement repricing](docs/ALL-SLEEVES.md#cer-entitlement-repricing) | US equities and ETFs · 1d (21- or 63-session hold) · QQQ, SPY and registered project issuers. Full recorded algorithm in the accounting entry. | 1 |
| [CQR contract queue revaluation](docs/ALL-SLEEVES.md#cqr-contract-queue-revaluation) | US equities · 1d (up to 63 sessions) · Registered contract issuers. Full recorded algorithm in the accounting entry. | 1 |
| [CRD capital release](docs/ALL-SLEEVES.md#crd-capital-release) | US equities · 1w decisions · Registered decision documents. Full recorded algorithm in the accounting entry. | 1 |
| [Spectral Echo Drift](docs/ALL-SLEEVES.md#spectral-echo-drift) | US equities · 1m (from IEX quotes) · 20 Nasdaq leaders. Full recorded algorithm in the accounting entry. | 1 |
| [TCFT index-flow swap](docs/ALL-SLEEVES.md#tcft-index-flow-swap) | US equities and QQQ · 1d (to the event's endpoint) · QQQ and registered index-event stocks. Full recorded algorithm in the accounting entry. | 1 |
| [UIR filing relay](docs/ALL-SLEEVES.md#uir-filing-relay) | US equities and ETFs · 1d (20-session hold) · Senders CAT, DE, MSFT; receivers DE, CAT, AAPL, AMZN, GOOGL, NVDA, AVGO, ORCL. Full recorded algorithm in the accounting entry. | 1 |
| [Saty Research v0.3 - SPY equity paper](docs/ALL-SLEEVES.md#saty-research-v03---spy-equity-paper) | Recorded by name; the accounting entry carries what the sources hold. | 1 |
| [OPT_STATIONARY_PAIR](docs/ALL-SLEEVES.md#opt_stationary_pair) | No strategy description recorded in consulted sources. | 1 |
| [OPT_TAIL_STATE](docs/ALL-SLEEVES.md#opt_tail_state) | No strategy description recorded in consulted sources. | 1 |
| [Comeback genome](docs/ALL-SLEEVES.md#comeback-genome) | US equities · 1h · 1d · 1wk · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 1 |
| [Edge paper hands (10 lineages)](docs/ALL-SLEEVES.md#edge-paper-hands-10-lineages) | US equities · 1h · AAPL, MSFT, NVDA, AMZN, JPM, XOM (SPY, QQQ, IWM, SMH as context). Full recorded algorithm in the accounting entry. | 1 |
| [Hourly Core / Burst transition](docs/ALL-SLEEVES.md#hourly-core--burst-transition) | US equities · 1h · 1,838-name genome roster. Full recorded algorithm in the accounting entry. | 1 |
| [aster_saty_research](docs/ALL-SLEEVES.md#aster_saty_research) | No strategy description recorded in consulted sources. | 1 |
| [legacy_exit](docs/ALL-SLEEVES.md#legacy_exit) | No strategy description recorded in consulted sources. | 1 |
| [R19_ADAUSDT_BREAKDOWN_BASE_COLLECTOR](docs/ALL-SLEEVES.md#r19_adausdt_breakdown_base_collector) | No strategy description recorded in consulted sources. | 1 |
| [R19_ADAUSDT_CROWDED_LONG_FAILURE_COLLECTOR](docs/ALL-SLEEVES.md#r19_adausdt_crowded_long_failure_collector) | No strategy description recorded in consulted sources. | 1 |
| [R19_ENJUSDT_BREAKDOWN_BASE_COLLECTOR](docs/ALL-SLEEVES.md#r19_enjusdt_breakdown_base_collector) | No strategy description recorded in consulted sources. | 1 |
| [R19_ENJUSDT_CROWDED_LONG_FAILURE_COLLECTOR](docs/ALL-SLEEVES.md#r19_enjusdt_crowded_long_failure_collector) | No strategy description recorded in consulted sources. | 1 |
| [R19_LINKUSDT_BREAKDOWN_BASE_COLLECTOR](docs/ALL-SLEEVES.md#r19_linkusdt_breakdown_base_collector) | No strategy description recorded in consulted sources. | 1 |
| [R19_LINKUSDT_CROWDED_LONG_FAILURE_COLLECTOR](docs/ALL-SLEEVES.md#r19_linkusdt_crowded_long_failure_collector) | No strategy description recorded in consulted sources. | 1 |
| [s_mn_qqq_ladder](docs/ALL-SLEEVES.md#s_mn_qqq_ladder) | No strategy description recorded in consulted sources. | 1 |
| [s_wait_chase](docs/ALL-SLEEVES.md#s_wait_chase) | No strategy description recorded in consulted sources. | 1 |
| [s_wait_flow](docs/ALL-SLEEVES.md#s_wait_flow) | No strategy description recorded in consulted sources. | 1 |
| [s_wait_olx_books](docs/ALL-SLEEVES.md#s_wait_olx_books) | No strategy description recorded in consulted sources. | 1 |
| [s_wait_q14](docs/ALL-SLEEVES.md#s_wait_q14) | No strategy description recorded in consulted sources. | 1 |

## Catalog cards by family (269)

| Family | Cards | Assets | Bars | Live | Waiting | Blocked | Off |
|---|---:|---|---|---:|---:|---:|---:|
| [Ausar](strategies/ausar/) | 24 | Stocks, ETFs, Options, Crypto | 5m to 1mo | 48 | 97 | 21 |  |
| [Lazarus](strategies/lazarus/) | 19 | Stocks, ETFs | 1h to 1w | 17 | 7 | 54 |  |
| [Femto-lean](strategies/femto/) | 45 (1 Midna only) | Stocks, ETFs, Options, Crypto | 3m to 1mo | 24 | 32 | 4 |  |
| [Midna](strategies/midna/) | 17 | Stocks, ETFs, Options, Crypto | 1h to 1mo | 13 | 11 |  |  |
| [Muse](strategies/muse/) | 17 (7 Midna only) | Stocks, ETFs, Options | 1m to 1w |  | 11 |  |  |
| [APEX](strategies/apex/) | 33 | ETFs, Options, Crypto | 1d to 1mo | 38 |  |  |  |
| [Galath / GrokBot](strategies/galath/) | 10 | Stocks, ETFs | 5m to 1d | 3 | 7 |  |  |
| [Griffith](strategies/griffith/) | 23 | Stocks, ETFs | 1m to 1mo | 15 | 6 | 3 |  |
| [Milkman](strategies/milkman/) | 34 (1 Midna only) | Stocks, ETFs, Options, Futures | 1m to 1mo | 18 | 20 |  | 1 |
| [Quant research](strategies/quant_research/) | 18 | Stocks, ETFs | 1m to 1mo | 7 | 6 | 5 |  |
| [Tensor research](strategies/tensor_research/) | 13 | Stocks | 1h to 1w | 8 | 6 |  |  |
| [Killed studies](strategies/killed/) | 10 | Stocks, ETFs | 5m to 1w | 10 | 1 |  |  |
| [Qullamaggie](strategies/qullamaggie/) | 3 | Stocks | 1m to 1d | 1 | 4 |  |  |
| [Sable](strategies/sable/) | 2 | Stocks | 5m to 1d | 2 |  |  |  |
| [SPAN](strategies/span/) | 1 | Prediction markets | trade prints |  | 1 |  |  |
| **All** | **269** | | | **204** | **209** | **87** | **1** |

Status counts are master-desk rows; one card can hold several rows (its variants).

<details><summary><b>Ausar</b> · 24</summary>

- [AI volume spike crypto (4h)](strategies/ausar/ai-volume.md) · Crypto spot · 4h
- [Coinbase SMA200 crypto trend](strategies/ausar/coinbase-sma200.md) · Crypto spot · 1d
- [Crypto confirmed absorption (4h)](strategies/ausar/crypto-absorption.md) · Crypto spot · 4h
- [Daily20 tree-model forecasts](strategies/ausar/daily20.md) · US equities · 1d
- [Earnings-drift (PEAD) put options](strategies/ausar/opt-pead.md) · Equity options · 1d
- [Index-ETF recovery options (RSI2 / VWAP20)](strategies/ausar/opt-recovery.md) · ETF options · 1d
- [IU big-body bar crypto (5m)](strategies/ausar/iu-body.md) · Crypto spot · 5m
- [Opening gamma puts](strategies/ausar/opt-opening-gamma.md) · Equity options · 5m
- [Public BB/KC squeeze (daily)](strategies/ausar/public-squeeze20.md) · US ETFs · 1d
- [Public Donchian 55 trend (daily)](strategies/ausar/public-donchian55.md) · US ETFs · 1d
- [QQQ 95% core with RSI2 options](strategies/ausar/opt-qqq95-rsi2.md) · ETF + ETF options · 1d
- [R17 ETF ladder rules](strategies/ausar/r17-etf-ladder.md) · US ETFs · 1d, monthly
- [R19 10-minute EMA cloud reclaim](strategies/ausar/r19-timing-cloud.md) · US equities · 10m (1h bias)
- [R19 causal overnight hold](strategies/ausar/r19-timing-overnight.md) · US equities · 30m
- [R19 crypto breakout and negative-funding squeeze](strategies/ausar/r19-crypto-breakout.md) · Crypto spot · 4h
- [R19 ETF books: momentum leader rotation](strategies/ausar/r19-etf.md) · US ETFs · 1d, monthly rebalance
- [R19 hourly confirmed swing](strategies/ausar/r19-timing-hourly.md) · US equities · 1h
- [R19 weekly Tensor beta M2 52-week cohort](strategies/ausar/r19-tensor-beta-m2.md) · US equities · 1w
- [R19 weekly Tensor C1 cyan ownership](strategies/ausar/r19-tensor-c1.md) · US equities · 1w
- [R19 weekly Tensor G4 green ownership](strategies/ausar/r19-tensor-g4.md) · US equities · 1w
- [RSI(2) pullback](strategies/ausar/public-rsi2.md) · US ETFs · US equities · crypto (ADA) · 1d · 1h
- [Tensor LEAPS calls](strategies/ausar/opt-tensor-leaps.md) · Equity options · 1w
- [Tensor state repair (hourly / weekly)](strategies/ausar/tensor-state-repair.md) · US equities · 1h · 1w
- [XSP weekly put credit spread](strategies/ausar/opt-xsp-pcs.md) · Index options · 1w

</details>

<details><summary><b>Lazarus</b> · 19</summary>

- [ChartsLector breakout leaders (small caps)](strategies/lazarus/cl-qm-small.md) · US equities · 1d
- [ChartsLector market-fear rebound (QQQ)](strategies/lazarus/cl-vmr-qqq.md) · US ETF · 1d
- [CHASE weekly lane](strategies/lazarus/lz-wait-chase.md) · US equities · 1w
- [Daily Cyan desk feed](strategies/lazarus/lz-daily-cyan.md) · US equities · 1d
- [Daily Green under $5](strategies/lazarus/lz-daily-green-under5.md) · US equities · 1d
- [FLOW short volume / FTD / dark pool](strategies/lazarus/lz-wait-flow.md) · US equities · 1d
- [Intraweek early entry](strategies/lazarus/lz-wait-intraweek.md) · US equities · 1w (daily entry)
- [Lab 1D Green trees](strategies/lazarus/lz-lab-1d-green-trees.md) · US equities · 1d
- [Lab 1W Cyan books](strategies/lazarus/lz-lab-1w-cyan-books.md) · US equities · 1w
- [Lab 1W Swing covered](strategies/lazarus/lz-lab-1w-swing.md) · US equities · 1w
- [Lab rule books (1D / 1W)](strategies/lazarus/lz-lab-rules.md) · US equities · 1d · 1w
- [Moonshot weekly lane](strategies/lazarus/lz-moonshot.md) · US equities · 1w
- [OLX R1/R2 books](strategies/lazarus/lz-wait-olx.md) · US equities · 1d
- [Q07 Tensor alt-data confluence cells](strategies/lazarus/lz-q07.md) · US equities · 1w
- [Q14 under-$5 weekly book](strategies/lazarus/lz-wait-q14.md) · US equities · 1w
- [R2 Daily Cyan extended](strategies/lazarus/lz-wait-r2-dcyan.md) · US equities · 1d
- [Tensor tracker lanes (1H / 1D / 1W)](strategies/lazarus/lz-tracker.md) · US equities · 1h · 1d · 1w
- [Weekly Cyan tier A](strategies/lazarus/lz-weekly-cyan-tier-a.md) · US equities · 1w
- [Weekly Green tier A small](strategies/lazarus/lz-weekly-green-small.md) · US equities · 1w

</details>

<details><summary><b>Femto-lean</b> · 45</summary>

- [12-month momentum top decile (monthly)](strategies/femto/femto-ts-momentum-decile.md) · US equities · 1d (monthly)
- [20-day VWAP reversion](strategies/femto/femto-ema-vwap.md) · US equities · 1d (hourly checks)
- [20-day VWAP reversion call spreads](strategies/femto/femto-ema-vwap-options.md) · Equity options · 1d (hourly checks)
- [60-day momentum rotation](strategies/femto/femto-momentum-rotation.md) · US equities · 1d (weekly)
- [Aurelia Nasdaq + gold allocation](strategies/femto/femto-aurelia.md) · US ETFs (incl. 3× leveraged) · 1d
- [Beaten-down weekly qualifiers](strategies/femto/femto-beatendown.md) · US equities · 1w
- [Bilbo Box calls](strategies/femto/femto-bilbo-options.md) · Equity options · 1h (5-minute exits)
- [Buyback before earnings (call spreads)](strategies/femto/femto-earnings-buyback.md) · Equity options · 1d (hourly checks)
- [Capitulation reversal (hourly)](strategies/femto/femto-capitulation.md) · US equities · 1h · 1d filters
- [Capitulation reversal calls (0-7 DTE)](strategies/femto/femto-capitulation-options.md) · Equity options · 1h · 1d filters
- [Daily Cyan GBM](strategies/femto/femto-daily-cyan-gbm.md) · US equities · 1d
- [Daily Cyan small-cap rule](strategies/femto/femto-rule-1d-cyan-smallcap.md) · US equities · 1d
- [Daily Green turn-of-month rule](strategies/femto/femto-rule-1d-green-tom.md) · US equities · 1d
- [Donchian 20/10 breakout](strategies/femto/femto-donchian.md) · US equities · crypto (SOL) · 1d · 15m
- [Fear premium put spreads (red days)](strategies/femto/femto-fear-premium.md) · Equity options · 1d (hourly checks)
- [High-IV iron condor](strategies/femto/femto-iron-condor.md) · Equity options · 1d (hourly checks)
- [Hourly Cyan range-expansion rule](strategies/femto/femto-rule-1h-cyan-raw.md) · US equities · 1h
- [Kraken basis repair (ADA / LINK)](strategies/femto/femto-kraken-basis.md) · Crypto spot + perpetual · 4h
- [Kraken breakdown short (ADA / LINK)](strategies/femto/femto-kraken-breakdown.md) · Crypto perpetual · 4h
- [Kraken crowded-long failure short (ADA / LINK)](strategies/femto/femto-kraken-crowded.md) · Crypto perpetual · 4h
- [Kraken ENJ order-book imbalance (spot)](strategies/femto/femto-free-kraken-enj-spot.md) · Crypto spot · 1h checks
- [Leader-1d event](strategies/femto/femto-leader-d.md) · US equities · 1d (one variant 1h)
- [LEAPS momentum with covered calls](strategies/femto/femto-leaps-momentum.md) · Equity options · 1d (hourly checks)
- [Legend's EMA (trend-day fade)](strategies/femto/femto-legends-ema.md) · US ETFs · 15m · 1d
- [Microcap snapback (weekly)](strategies/femto/femto-snapback.md) · US equities (microcaps) · 1w · 1d
- [Morning dip limit](strategies/femto/femto-morning-dip.md) · US ETFs · 3m
- [Own-IV straddle](strategies/femto/femto-free-opt-own-iv.md) · ETF options · 1d (5-minute passes)
- [Phase compression breakout (daily)](strategies/femto/femto-phase-daily.md) · US equities · 1d
- [Phoenix breakout (red-day entry)](strategies/femto/femto-phoenix.md) · US equities and ETFs · 1d
- [QQQ weekly put ladder](strategies/femto/femto-qqq-put-ladder.md) · ETF options · 1d (weekly layers)
- [R4 blowoff (daily / hourly)](strategies/femto/femto-blowoff.md) · US equities · 1d · 1h
- [Red-day washout reversal](strategies/femto/femto-red-day-reversal.md) · US equities · 1d (hourly checks)
- [Release straddle (CPI, jobs, FOMC)](strategies/femto/femto-free-opt-release.md) · ETF options · 1d (5-minute passes)
- [RSI(2) pullback call spreads](strategies/femto/femto-rsi-meanrev-options.md) · Equity options · 1d (hourly checks)
- [Six-month momentum leaders](strategies/femto/femto-momentum.md) · US equities · 1d
- [SPY / QQQ residual option pair](strategies/femto/femto-free-opt-pair.md) · ETF options · 1d (5-minute passes)
- [SPY 30-delta wheel](strategies/femto/femto-free-opt-wheel.md) · ETF options · 1d (5-minute passes)
- [SPY put-call parity package](strategies/femto/femto-free-opt-parity.md) · ETF options · 1d (5-minute passes)
- [Tail put after a -3% day](strategies/femto/femto-free-opt-tail.md) · ETF options · 1d (5-minute passes)
- [Tensor 1H swing flagship](strategies/femto/femto-tensor-swing.md) · US equities · 1h
- [Tensor red-dip buys on fear days](strategies/femto/femto-tensor-red-dip.md) · US equities · Intraday · 1h signals
- [VXX call tail hedge](strategies/femto/femto-vix-hedge.md) · ETP options · 1d (hourly checks)
- [Weekly Cyan momentum ADX rule](strategies/femto/femto-rule-1w-cyan-mom-adx.md) · US equities · 1w
- [Weekly swing high-beta WaveTrend rule](strategies/femto/femto-rule-1w-swing-beta-wt.md) · US equities · 1w
- [Winner confluence (weekly qualifiers)](strategies/femto/femto-confluence.md) · US equities · 1w

</details>

<details><summary><b>Midna</b> · 17</summary>

- [Distance-pair shares](strategies/midna/mn-distance-pair.md) · US equities · 1d
- [EMA4 rising VWAP](strategies/midna/mn-ema4-vwap.md) · US equities · 1d
- [Faber ETF trend (10-month average)](strategies/midna/mn-faber.md) · US ETFs · 1d (monthly average)
- [Forward lab accounts (Tensor scan)](strategies/midna/mn-forward-lab.md) · US equities · 1d · 1w
- [Hourly Tensor playbook](strategies/midna/mn-hourly-playbook.md) · US equities · 1h
- [Hyperliquid momentum floor](strategies/midna/mn-hyperliquid-floor.md) · Crypto perps · intraday (10-min scan)
- [Kronos-base TopkDropout](strategies/midna/mn-kronos-topk.md) · US equities · 1d (10-session cycle)
- [Large-cap prior-month reversal](strategies/midna/mn-prior-month-reversal.md) · US equities · 1d (monthly)
- [Listed distance-pair package](strategies/midna/mn-opt-distance-pair.md) · Equity options · 1d
- [Listed reversal call spread](strategies/midna/mn-opt-reversal.md) · Equity options · 1d (monthly)
- [Listed Turtle ATM call](strategies/midna/mn-opt-turtle.md) · Equity options · 1d
- [MACD-CCI](strategies/midna/mn-macd-cci.md) · US equities · 1d
- [QLD weekly timing](strategies/midna/mn-qld-weekly-timing.md) · Leveraged ETF · 1w
- [QQQ flip5 TZA hedge](strategies/midna/mn-qqq-flip5-tza.md) · Leveraged ETF · 1d
- [TSMOM 12-1 ETF book](strategies/midna/mn-tsmom-12-1-etf.md) · US ETFs · 1d (every 21 sessions)
- [Turtle System 1](strategies/midna/mn-turtle.md) · US equities · 1d
- [Weekly 8/20/50 pullback](strategies/midna/mn-weekly-8-20-50-pullback.md) · US ETFs · 1w signal · 1d management

</details>

<details><summary><b>Muse</b> · 17</summary>

- [15.87 Rule (SPY 0DTE)](strategies/muse/muse-em-1587.md) · SPY options (0DTE) · 5m
- [Band-touch RSI divergence](strategies/muse/muse-bb-rsi-divergence.md) · US ETFs and large caps · 1h
- [Grok support and resistance (SPY)](strategies/muse/muse-grok-sr-spy.md) · SPY shares, long and short · 1m
- [InvestAndBeFree double MACD (SPY and QQQ options)](strategies/muse/muse-investandbefree-dmac.md) · SPY and QQQ options (long premium) · 4H, daily, weekly stack
- [PO10 extreme (QQQ)](strategies/muse/muse-po10-qqq.md) · QQQ shares, long and short · 10m
- [PRZM Fade Edges recreation (SPY)](strategies/muse/muse-przm-fade-edges.md) · SPY shares, long and short · 1m
- [PRZM Zero recreation (SPY)](strategies/muse/muse-przm-zero.md) · SPY shares (signal engine) · 1m
- [Raschke PF3 momentum (SPY)](strategies/muse/muse-raschke-pf3.md) · SPY shares, long and short · 5m
- [Raschke RRE adaptive desk (SPY)](strategies/muse/muse-raschke-rre.md) · SPY shares · 5m
- [SATY day system (SPY 0DTE)](strategies/muse/muse-saty-day.md) · SPY options (0DTE) · 1m · 3m · 10m · 1h
- [Saty Magnum (SPY shares)](strategies/muse/muse-saty-magnum.md) · SPY shares, long and short · 3m · 10m · 1h · 1d
- [Saty opportunity engine v0.3 (SPY shares)](strategies/muse/muse-saty-gpt-v03.md) · SPY shares, long and short · 10m · 1h
- [Saty research system v0.2 (SPY shares)](strategies/muse/muse-saty-gpt-v02.md) · SPY shares, long and short · 10m · 1h
- [Shen first-touch fade (SPY 0DTE)](strategies/muse/muse-shen-fade.md) · SPY options (0DTE) · 1m
- [Sol's Saty engine (SPY options)](strategies/muse/muse-saty-sol.md) · SPY options · 1m · 3m · 10m
- [Teddy opening range breakout (SPY)](strategies/muse/muse-teddy-orb-spy.md) · SPY shares, long and short · 5m (aggregated from 1m)
- [Trullas divergence (QQQ 1-minute)](strategies/muse/muse-trullas-divergence.md) · QQQ shares, long and short · 1m

</details>

<details><summary><b>APEX</b> · 33</summary>

- [APEX C2: Sector Kings](strategies/apex/apex-c2-sector-kings.md) · US ETFs · 1d (monthly picks)
- [APEX C3: Follow-through](strategies/apex/apex-c3-follow-through.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX C4: Broken Hedge](strategies/apex/apex-c4-broken-hedge.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX C5: REFLEX](strategies/apex/apex-c5-reflex.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX C6: SLINGSHOT](strategies/apex/apex-c6-slingshot.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX C7: COUNCIL](strategies/apex/apex-c7-council.md) · US ETFs, ETF options and Bitcoin · 1d (monthly options)
- [APEX E1: VIX term-structure gate](strategies/apex/apex-e1-vix-term-gate.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX E2: Double 7 dip overlay](strategies/apex/apex-e2-double7-dip.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX E3 / v1.1: defensive Treasuries](strategies/apex/apex-e3-defensive-treasuries.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX E4: rolling tail puts](strategies/apex/apex-e4-rolling-tail-puts.md) · US ETFs and ETF options · 1d (monthly puts)
- [APEX E5: semiconductor tilt](strategies/apex/apex-e5-semis-rs-tilt.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX E6: overnight boost](strategies/apex/apex-e6-overnight-boost.md) · US ETFs (incl. 3× leveraged) · 1d (overnight boost)
- [APEX E7: turn-of-month boost](strategies/apex/apex-e7-turn-of-month.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX N1: Duration Shield](strategies/apex/apex-n1-duration-shield.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX N2: Silicon Switch](strategies/apex/apex-n2-silicon-switch.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX N3 / N4: PRISM multi-asset trend](strategies/apex/apex-n3-prism-classic.md) · US ETFs and Bitcoin · 1d
- [APEX N5: GESTALT analog engine](strategies/apex/apex-n5-gestalt.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX N6: GESTALT × APEX](strategies/apex/apex-n6-gestalt-apex.md) · US ETFs (incl. 3× leveraged) · 1d
- [APEX N7: OMNI](strategies/apex/apex-n7-omni.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O10: LEAPS + Variance Value](strategies/apex/apex-o10-leaps-vv.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O11: APEX + Variance Value](strategies/apex/apex-o11-apex-vv.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O12: hybrid LEAPS + QQQ trim](strategies/apex/apex-o12-hybrid-leaps.md) · US ETFs and ETF options · 1d
- [APEX O1: CONVEX](strategies/apex/apex-o1-convex.md) · US ETFs and ETF options · 1d
- [APEX O2: LEAPS-APEX](strategies/apex/apex-o2-leaps.md) · US ETFs and ETF options · 1d
- [APEX O3: regime put-write](strategies/apex/apex-o3-regime-putwrite.md) · US ETFs and ETF options · 1d (monthly puts)
- [APEX O4: PHOENIX](strategies/apex/apex-o4-phoenix.md) · US ETFs and ETF options · 1d
- [APEX O5: CHOP HARVEST](strategies/apex/apex-o5-chop-harvest.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O6: Variance Value](strategies/apex/apex-o6-variance-value.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O7: skew risk reversal](strategies/apex/apex-o7-skew-risk-reversal.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O8: FEAR put spread](strategies/apex/apex-o8-fear-put-spread.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX O9: OMEGA](strategies/apex/apex-o9-omega.md) · US ETFs and ETF options · 1d (monthly options)
- [APEX QQQ benchmark](strategies/apex/apex-benchmarks.md) · US ETFs · 1d
- [APEX-50F Nasdaq trend × volatility](strategies/apex/apex-trend-har-tiers.md) · US ETFs (incl. 3× leveraged) · 1d

</details>

<details><summary><b>Galath / GrokBot</b> · 10</summary>

- [Anna PhD location printer](strategies/galath/galath-anna-phd-printer.md) · US equities and ETFs · 1d
- [Anna seven-vote printer](strategies/galath/galath-anna-seven-vote-printer.md) · US equities · 1d
- [CCI correction pullback](strategies/galath/galath-cci-correction.md) · US equities · 1d
- [Echo swing](strategies/galath/galath-echo-swing.md) · US equities · Posts (3-minute sweeps) · 1d
- [Komar momentum breakout](strategies/galath/galath-komar-momentum.md) · US equities · 1d
- [Next-support plan](strategies/galath/galath-next-support-plan.md) · US equities · 1d (1-minute passes)
- [Scanner book swing](strategies/galath/galath-scanner-book-swing.md) · US equities · 1d · 5m session tape
- [Sector-first bottom](strategies/galath/galath-sector-first-bottom.md) · US equities · 1d · 5m session tape
- [Tensor 2 washout / reclaim printer](strategies/galath/galath-tensor2-washout-reclaim.md) · US equities and ETFs · 1h
- [Washout and PPC coil](strategies/galath/galath-washout-ppc-coil.md) · US equities · 1d (1-minute passes)

</details>

<details><summary><b>Griffith</b> · 23</summary>

- [20-minute opening range breakout](strategies/griffith/griffith-orb20.md) · US equities · 5m
- [52-week-high strength](strategies/griffith/griffith-52w-high-rs.md) · US equities · 1d (monthly)
- [Auditable 20/50 trend (SPY)](strategies/griffith/griffith-auditable-20-50-trend.md) · US ETF (SPY) · 5m
- [Cross-sectional momentum (12-1 / 6-1)](strategies/griffith/griffith-xs-momentum.md) · US equities · 1d (monthly)
- [ETF 12-month time-series momentum](strategies/griffith/griffith-etf-tsmom12.md) · US ETFs · 1d (monthly)
- [Gap continuation (legacy setup)](strategies/griffith/griffith-gap-continuation.md) · US equities · 1m (15-minute cycle)
- [Leaders Rest](strategies/griffith/griffith-leaders-rest.md) · US equities · 1d
- [Liquid momentum trend cohorts](strategies/griffith/griffith-liquid-momentum-trend.md) · US equities · 1d (20-session cohorts)
- [Momentum breakout (legacy setup)](strategies/griffith/griffith-momentum-breakout.md) · US equities · 1m (15-minute cycle)
- [Momentum plus earnings drift](strategies/griffith/griffith-momentum-pead.md) · US equities · 1d (20-session hold)
- [Parallax](strategies/griffith/griffith-parallax.md) · US equities · 1d
- [Positive earnings surprise drift](strategies/griffith/griffith-pead-sue.md) · US equities · 1d (20-session hold)
- [Simple daily trend cohorts](strategies/griffith/griffith-simple-daily-trend.md) · US equities · 1d (20-session cohorts)
- [Tensor edge v0.1 (G1 / G2 / C1)](strategies/griffith/griffith-tensor-edge-v01.md) · US equities · 1d · 1w
- [Tensor frozen phenotypes v4](strategies/griffith/griffith-frozen-phenotypes-v4.md) · US equities · 1d · 1w
- [Tensor HTF conditional holdout (H1-H8)](strategies/griffith/griffith-htf-conditional-h1-h8.md) · US equities · 1d · 1w
- [Tensor HTF relay (T1-T7)](strategies/griffith/griffith-htf-relay.md) · US equities · 1d · 1w
- [Tensor phenotype experiment (HIGH_BREAK_4)](strategies/griffith/griffith-tensor-phenotype-experiment.md) · US equities · 1d · 1w
- [Tensor weekly color forward shadow (FG / FC)](strategies/griffith/griffith-weekly-color-forward-shadow.md) · US equities · 1w
- [Tensor weekly cyan confirmation (CY01-CY18)](strategies/griffith/griffith-weekly-cyan-confirmation.md) · US equities · 1w
- [Tensor weekly green / cyan deep confirmation (WG / WC)](strategies/griffith/griffith-weekly-green-cyan-deep-confirmation.md) · US equities · 1w
- [Top-decile SUE drift](strategies/griffith/griffith-top-decile-sue.md) · US equities · 1d (20-session hold)
- [VWAP pullback (legacy setup)](strategies/griffith/griffith-vwap-pullback.md) · US equities · 1m (15-minute cycle)

</details>

<details><summary><b>Milkman</b> · 34</summary>

- [ATR level cascade (SPY)](strategies/milkman/mk-atrlevelcascade.md) · US ETF · 1m
- [Big down-day response](strategies/milkman/mk-bigdowndayresponse.md) · US index ETFs and futures · 1d
- [Big Winners weekly Tensor sleeve](strategies/milkman/mk-bigwinners.md) · US equities · 1w
- [Bilbo Golden Gate (SPY)](strategies/milkman/mk-bilbogoldengate.md) · US ETF · 1m · 1h Phase Oscillator
- [Call-to-put reversal (SPY)](strategies/milkman/mk-calltoputputtocallreversal.md) · US ETF · 1m
- [Connors Double 7](strategies/milkman/mk-connorsdouble7.md) · US equities, index ETFs and futures · 1d
- [Daily Bilbo Box](strategies/milkman/mk-dailybilbobox.md) · US equities, index ETFs and futures · 1d
- [Daily compression expansion](strategies/milkman/mk-dailycompressionexpansion.md) · US equities, index ETFs and futures · 1d
- [Day Golden Gate (SPY)](strategies/milkman/mk-daygoldengate.md) · US ETF · 1m (daily ATR levels)
- [Directional trigger box (SPY)](strategies/milkman/mk-directionaltriggerbox.md) · US ETF · 10m
- [EMA21 deviation reversion](strategies/milkman/mk-ema21deviationreversion.md) · US equities, index ETFs and futures · 1d
- [ES Monday clock (SPY)](strategies/milkman/mk-esmondayclockonspyproxy.md) · US ETF · 1m (06:00-16:00 ET)
- [Four-hour Phase Oscillator OpEx rollover (SPY)](strategies/milkman/mk-fourhourpoopexrollover.md) · US ETF · 4h
- [Gap fade / momentum mirror (SPY)](strategies/milkman/mk-gapfademomentummirror.md) · US ETF · 1d gap · 1m exits
- [Gap-up pre-noon continuation (SPY)](strategies/milkman/mk-gapupprenooncontinuation.md) · US ETF · 1m
- [Legend's Buy Day](strategies/milkman/mk-legendsbuyday.md) · US equities, index ETFs and futures · 1d
- [Milkman 0DTE (SPX)](strategies/milkman/mk-zerodte-spx.md) · SPX index options (0DTE) · Intraday
- [Milkman daily rules on crypto-linked stocks](strategies/milkman/mk-milkmancryptolinkedstockvariant.md) · US equities · 1d
- [Milkman filters on Tensor lanes](strategies/milkman/mk-milkmanlaneaddonfilters.md) · US equities · 1w · 1d
- [Multi-day Golden Gate (weekly ATR)](strategies/milkman/mk-multidaygoldengateweekly.md) · US equities, index ETFs and futures · 1d (weekly ATR levels)
- [O'Neil follow-through-day race](strategies/milkman/mk-oneilfollowthroughdayrace.md) · US index ETFs and futures · 1d
- [Opening range breakout (SPY)](strategies/milkman/mk-openingrangebreakout.md) · US ETF · 1m (5-minute closes)
- [Phase Oscillator zone exit](strategies/milkman/mk-phaseoscillatorzoneexit.md) · US equities, index ETFs and futures · 1d
- [Pivot Ribbon 13/48 cross](strategies/milkman/mk-pivotribbon1348cross.md) · US equities, index ETFs and futures · 1d
- [Premarket all-time-high fade (SPY)](strategies/milkman/mk-premarketathmorningfade.md) · US ETF · 1m · 10m Phase Oscillator
- [Swing Golden Gate (monthly ATR)](strategies/milkman/mk-swinggoldengatemonthly.md) · US equities, index ETFs and futures · 1d (monthly ATR levels)
- [Ten-minute compression release (SPY)](strategies/milkman/mk-tenminutecompressionrelease.md) · US ETF · 10m
- [Tensor breadth timing (IWM)](strategies/milkman/mk-creativetensorbreadthtiming.md) · US ETF · 1w
- [Tensor fires as calls](strategies/milkman/mk-creativetensoroptionexpressionproxy.md) · Equity options · 1w
- [Tensor ratio-chart signals](strategies/milkman/mk-creativetensorratiochartsignals.md) · US equities · 1w
- [Three-minute compression drift (SPY)](strategies/milkman/mk-threeminutecompressiondrift.md) · US ETF · 3m
- [Three-minute trigger confirmation (SPY)](strategies/milkman/mk-threeminutetriggerconfirmation.md) · US ETF · 3m
- [Vomy / iVomy (SPY)](strategies/milkman/mk-vomyivomy.md) · US ETF · 10m
- [Weekday open-to-close (Monday)](strategies/milkman/mk-weekdayopentocloseproxy.md) · US index ETFs and futures · 1d

</details>

<details><summary><b>Quant research</b> · 18</summary>

- [AIRT auction impulse](strategies/quant_research/qr-auctionimpulseresponsetrading.md) · US equities · Intraday (≤ 30 minutes)
- [AlphaMemo factor book](strategies/quant_research/qr-alphamemosourcepreservingfactorrecon.md) · US equities · 1d
- [AlphaQCM factor rotation](strategies/quant_research/qr-alphaqcmiqcmfactorpolicyreconstructi.md) · US equities · 1d (every 20 sessions)
- [BOLT event tilt (SPY / QQQ)](strategies/quant_research/qr-bracketedoptionlawtransport.md) · US ETFs (SPY, QQQ) · Event windows (about 10 sessions)
- [CARM recovery memory](strategies/quant_research/qr-commitmentadjustedrecoverymemory.md) · US equities and QQQ · Intraday (≤ 30 minutes)
- [CER entitlement repricing](strategies/quant_research/qr-conjunctiveentitlementrepricing.md) · US equities and ETFs · 1d (21- or 63-session hold)
- [CQR contract queue revaluation](strategies/quant_research/qr-contractqueuerevaluation.md) · US equities · 1d (up to 63 sessions)
- [CRD capital release](strategies/quant_research/qr-capitalreleasedynamics.md) · US equities · 1w decisions
- [CRG own-stock filing surprise](strategies/quant_research/qr-catalystresolutiongap.md) · US equities and ETFs · 1d (20-session hold)
- [Fast Numbers earnings surprise](strategies/quant_research/qr-fastnumbersslowwordseventreconstruct.md) · US equities (long and short) · 1d (open to close)
- [FinRL-X adaptive rotation](strategies/quant_research/qr-finrlxreleasedadaptiverotationrecons.md) · US equities and ETFs · 1w
- [News-conditioned 12-1 leadership](strategies/quant_research/qr-newsconditioned121leadership.md) · US equities · 1mo ranking · 1h timing
- [QuantaAlpha factor book](strategies/quant_research/qr-quantaalphadeterministicproposalreco.md) · US equities · 1d
- [Spectral Echo Drift](strategies/quant_research/qr-spectral-echo-drift.md) · US equities · 1m (from IEX quotes)
- [TCFT index-flow swap](strategies/quant_research/qr-timecutflowtransport.md) · US equities and QQQ · 1d (to the event's endpoint)
- [Tensor rejection memory (MID21)](strategies/quant_research/qr-tensor-rejection-memory.md) · US equities · 1d
- [TRACE residual accumulation (daily)](strategies/quant_research/qr-tensor-residual-accumulation.md) · US equities · 1d
- [UIR filing relay](strategies/quant_research/qr-unpricedinformationrelay.md) · US equities and ETFs · 1d (20-session hold)

</details>

<details><summary><b>Tensor research</b> · 13</summary>

- [Coiled Spring genome](strategies/tensor_research/tr-genome-coiled-spring.md) · US equities · 1h · 1d · 1wk
- [Comeback genome](strategies/tensor_research/tr-genome-comeback.md) · US equities · 1h · 1d · 1wk
- [Daily green base expansion](strategies/tensor_research/tr-genome-daily-green-base-expansion.md) · US equities · 1d
- [Deep Reset cross-scan](strategies/tensor_research/tr-ro-deep-reset-cross-scan.md) · US equities · 1d · 1wk
- [Edge paper hands (10 lineages)](strategies/tensor_research/tr-sable-edge-paper-hands.md) · US equities · 1h
- [Hourly Core / Burst transition](strategies/tensor_research/tr-ro-hourly-transition-core-burst.md) · US equities · 1h
- [Leader genome](strategies/tensor_research/tr-genome-leader.md) · US equities · 1h · 1d · 1wk
- [Leaders Rest v1.1 on daily buy-greens](strategies/tensor_research/tr-ro-leaders-rest-v11.md) · US equities · 1d
- [Swing Transition (1H)](strategies/tensor_research/tr-ro-swing-transition-1h-v1.md) · US equities · 1h
- [Tensor 1H Swing (v615)](strategies/tensor_research/tr-ro-tensor-1h-swing-v615.md) · US equities · 1h
- [Weekly cyan accumulation](strategies/tensor_research/tr-ro-weekly-cyan-accumulation.md) · US equities · 1wk
- [Weekly cyan transition](strategies/tensor_research/tr-ro-weekly-cyan-transition.md) · US equities · 1wk
- [Weekly green recovery](strategies/tensor_research/tr-ro-weekly-green-recovery.md) · US equities · 1wk

</details>

<details><summary><b>Killed studies</b> · 10</summary>

- [Distance pairs](strategies/killed/killed-pairs-distance-coint.md) · US equities · 1d
- [Earnings-day overnight scalp](strategies/killed/killed-pead-spillover-scalp.md) · US equities · 1d (overnight)
- [Golden cross (SPY)](strategies/killed/killed-golden-cross-spy.md) · US ETF · 1d
- [Intraday momentum (Gao et al.)](strategies/killed/killed-intraday-momentum-gao.md) · US ETFs · 5m
- [Naive 20-day breakout](strategies/killed/killed-naive-20d-breakout.md) · US equities · 1d
- [PEAD price surprise](strategies/killed/killed-pead-price-surprise.md) · US equities · 1d (event)
- [RSI × OBV daily studies](strategies/killed/killed-rsiobv-daily.md) · US equities · 1d
- [RSI × OBV intraday (5-minute)](strategies/killed/killed-rsiobv-intraday.md) · US equities · 5m
- [Six short candidates](strategies/killed/killed-short-candidates.md) · US equities · 30m · 1d
- [Small-cap high-beta beaten-down (52 weeks)](strategies/killed/killed-smcap-beta-52w.md) · US equities · 1w

</details>

<details><summary><b>Qullamaggie</b> · 3</summary>

- [Qullamaggie breakout](strategies/qullamaggie/qm-leader-breakout.md) · US equities · 1d setup · 5m / 1m trigger
- [Qullamaggie episodic pivot](strategies/qullamaggie/qm-episodic-pivot.md) · US equities · 1d setup · 1m trigger
- [Qullamaggie parabolic short](strategies/qullamaggie/qm-parabolic-short.md) · US equities · 1d setup · 1m trigger

</details>

<details><summary><b>Sable</b> · 2</summary>

- [Location-first repair](strategies/sable/sable-location-first.md) · US equities · 1d (5-minute passes)
- [Support scanner (5-minute)](strategies/sable/sable-support-scanner.md) · US equities · 5m

</details>

<details><summary><b>SPAN</b> · 1</summary>

- [SPAN Harvest](strategies/span/span-harvest.md) · Prediction markets · Trade prints (60 s passes)

</details>

## How to read a card

- **Header**: family, source, asset, bars, universe, style and status.
- **Entry / Exit / Sizing / Data**: the rules as the code runs them; `docs/VERIFY.md` gives the lines.
- **Variants**: rows that run the same rules on other symbols, bars, sizes or parameters.
- **Code**: each desk's implementation; paths marked *not in this repo* stay on the master desk.

## Status

| Status | Meaning |
|---|---|
| live | trading: holds a position or traded recently |
| waiting | on, waiting for its next signal or session |
| blocked | on, but an input or a defect stops it |
| off | switched off |
| Midna's desk only | not run on the master desk |

Status is the master desk's roll call of 2026-10-26.

## Credits

| Who | For |
|---|---|
| Midna | her TypeScript and Python v3 desks, and the strategies posted here |
| Femto-lean | the owner's Python desk; the master desk runs its framework |
| Desks and agents | Ausar, Lazarus, Galath / GrokBot, Griffith / Ledge, APEX (Cursor2), Aurelia (Agentic-Trading-Desk), Sable / Autopilot, SPAN, the quant research desk, the Milkman v2 study, FolioTend research, Sol (ChatGPT), Grok and Astra |
| Traders and authors | Larry Connors (RSI(2), Double 7), Kristjan Kullamägi (Qullamaggie), Milkman Trades, Saty Mahajan, Linda Raschke, Shen Lao (@shentrades), Azrael (15.87 Rule), David Trullas Vila, Echo (@EchoAnalysis), Julian Komar, ChartsLector, @PredictionAlgos, William O'Neil, Mebane Faber |
| Research and open code | Gatev (distance pairs); Gao, Han, Li and Zhou (intraday momentum); Amini and Singal (buybacks before earnings, via Quantpedia); QuantifiedStrat; trader.dev; StockCharts; LazyBear; Tomazetti; IU (TradingView); FinRL-X (AI4Finance), AlphaMemo, QuantaAlpha, AlphaQCM and Kronos; TimePortal (Polymarket tapes) |
