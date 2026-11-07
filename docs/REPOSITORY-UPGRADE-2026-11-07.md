# Repository upgrade: changes and acceptance evidence

Date: 2026-11-07 UTC. This upgrade makes Test easier to navigate, reproduce and
use accurately while preserving its source library. Test supplies domain
knowledge, code, research and historical evidence; the companion
[InfinityBlade Engineering Doctrine](https://github.com/dwj9ddyvf6-hub/InfinityBlade-Engineering-Doctrine)
supplies a distinct operating discipline.

This is a targeted semantic audit with mechanical inventory and regression
checks. It is not a claim that every file in the repository received a complete
semantic review, that every archived system is deployable, or that a measured
improvement has been demonstrated for every LLM.

## What a reader can do now

- Follow [START-HERE](../START-HERE.md) and the [topic roadmap](../ROADMAP.md)
  into the appropriate collection, with source roles and snapshot boundaries
  stated explicitly.
- Use the [task map](REPOSITORY-MAP.json): 25 curated routes across 25 areas at
  this audit. Routes provide reading order, relevant checks, evidence boundaries
  and related questions. Current-checkout reading targets were checked to exist.
- Use the [navigator](../tools/repo_navigator.py) to search a selected revision,
  read exact passages or build a bounded source packet. Results carry hashes,
  line ranges and explicit omissions. Search is lexical; a ranked match is a
  candidate source, not a semantic verdict.
- Follow [the LLM operating guide](LLM-OPERATING-GUIDE.md) through worked
  examples: reproduce the offline desk, trace Teddy ORB rules, distinguish
  forecast and psychology implementations, and turn agent research into a
  testable workflow improvement.
- Generate or check an exact inventory with
  [build_repo_index.py](../tools/build_repo_index.py). Counts and research
  collections are derived from the selected source tree; curated explanations
  come from the task map. The generator is itself hashed. Only INDEX.md and
  INDEX.json have self-excluded hashes.

The research basis is documented separately in the
[external research synthesis](research/repository-enhancement-2026-11-07/README.md)
and [source ledger](research/repository-enhancement-2026-11-07/SOURCES.json).
That ledger records 15 source groups, inspected portions and five external
repository pins. It distinguishes empirical evidence, specifications, provider
guidance and proposed applications; it does not claim a controlled LLM trial.

## Concrete discrepancies corrected

| Before | Correction and evidence |
|---|---|
| Root navigation maintained competing stale file totals and described copied roster data as what runs “today.” | Exact inventory belongs to [INDEX.md](../INDEX.md)/[INDEX.json](../INDEX.json); the entry documents distinguish captured configuration from present operation. |
| The roadmap implied that the enhancement-extraction archive supplied the primary records for the separate agent-methods study. | The routes preserve their independent sources and coverage. Compare [agent-methods](research/agent-methods/2026-10-31/README.md) with [enhancement extraction](research/llm-enhancement-extraction-20261031/REPORT.md). The previously omitted [second-brain study](research/obsidian-second-brain-sweep-20261102/SYNTHESIS.md) also has an explicit route. |
| README's accounting table omitted three BTA strategies already present in the accounting. | Three links were added, bringing the listing from 651 to 654. All 651 prior strategy rows remain unchanged; the entire 269-card family section is byte-identical to the pre-upgrade section. |
| Setup copied `deskkit` below `engine/` although imports expected it at the root, and nested `tests/` inside an existing `tests/`. | [Setup Step 3](../agentic-trade-desk/docs/03_setup_step_by_step.md#step-3--copy-the-skeleton-and-run-its-tests) now copies the usable layout. The clean-export check requires a nonzero, complete passing suite. |
| The quote fallback test still passed a callback after the API changed to fetched observations. | [The test](../agentic-trade-desk/skeleton/tests/test_deskkit.py) now uses the existing `(price, provider_timestamp)`/None contract and checks stale, future and nonfinite secondary observations. Production quote logic is unchanged. |
| The toy's “restarted process” label and config prose implied capabilities beyond its implementation. | [The worked example](../agentic-trade-desk/docs/13_worked_example.md) explains same-process object reconstruction and distinguishes the proposed config-loader contract from the supplied Python-constructed lanes. Existing extension drills remain. |
| Teddy's card said its stop was beyond the pullback extreme. | [The card](../strategies/muse/muse-teddy-orb-spy.md) now agrees with the [frozen spec](TEDDY-ORB-SPY-SPEC-2026-10-28.md) and [source](../sleeves/teddy_orb_spy.py): inside the broken opening-range edge, long OR high minus $0.10 or short OR low plus $0.10. Executable strategy and frozen specs are unchanged. |
| The README guide-block check could pass despite changed block text or a missing guide. | [The checker](../agentic-trade-desk/skeleton/tools/check_root_readme_links.py) now compares the complete canonical block, requires one marker pair and checks all three guide targets plus the reconciliation. |

The preservation check found no tracked file deletions in the upgrade working
tree. Corrections improve current summaries and tooling; they do not replace
historical studies, contributed packages or frozen receipts with shortened
summaries.

## Acceptance checks observed

These are dated local observations. Rerun them against the revision you use;
the results do not establish a remote publication or a running service.

| Command, from repository root | Observed result | Boundary |
|---|---|---|
| `python3 -B -m unittest discover -s tests -p 'test_repo_*.py' -v` | 32 tests passed: 21 navigator and 11 inventory/guide-block tests. | Temporary fixture repositories; includes source pinning, bounded packets, omission reporting, invalid paths, missing sources, SHA-256 Git repositories, batch-reader cleanup, bounded search output and inventory/provenance drift. |
| `python3 agentic-trade-desk/skeleton/tools/check_onboarding.py` | 23 tests discovered and executed; zero failures, errors or skips. Twelve toy passes, two total orders, zero orders on six simulated restarts, flat final book and valid ledger chain. | Clean temporary export of the supplied toy; no account credentials, real feed, broker lifecycle or OS failover proof. |
| `python3 agentic-trade-desk/skeleton/tools/check_root_readme_links.py README.md` | Exact canonical block and all four local targets passed. | This fixed block; it is not a complete semantic review of README. |

The clean-export receipt hashes the exact copied sources and the verifier. At
this check its source-manifest SHA-256 was
`da79d6a17960f41108695d17aa980dfd075c89e3079af72810070b528dfc1ec7`;
the verifier SHA-256 was
`47cc2e71f4886257698c2960077495054230cebd472370d584e37d17c498a8ef`.
The verifier rejects zero-test discovery and incorrect toy outcomes. Its audit
guard blocks socket creation and child-process activity inside the reviewed
test/example process; it is not a sandbox for arbitrary untrusted code.

The strategy correction was also checked with independently calculated long
and short examples against the isolated `_stop_target` function. For entry
101, OR high 100 and OR low 98, the long stop/target is 99.90/102. For entry 97
with the same range, the short stop/target is 98.10/96. This checks arithmetic
on synthetic inputs, not trading performance.

For a committed checkout, the navigation and saved-inventory checks are:

```sh
python3 tools/repo_navigator.py check
python3 tools/build_repo_index.py --local-repo . --ref HEAD --check --out-dir .
```

The navigator defaults to committed HEAD. During editing, global `--worktree`
reads tracked/staged files; untracked files are excluded. An inventory records
its own selected source revision, so changes after that snapshot require a
fresh inventory rather than an edited headline count.

## Branches and archives remain distinct

The map records three publication contexts: main, the broader historical
`educational/shipyard-components-2026-10-31` branch, and the historical
`research/agent-methods-2026-10-31-public` branch. Their entrypoints and observed
revisions are in [the branch records](REPOSITORY-MAP.json). Branch-relative
paths are not promises that those paths exist in the main checkout. The broader
components collection and main's narrower numeric-kernel package retain their
different purposes.

The navigator performs no network fetch. If those remote-tracking refs are
needed locally, this separate command fetches them without changing the
checkout:

```sh
git fetch --no-tags origin \
  '+refs/heads/main:refs/remotes/origin/main' \
  '+refs/heads/educational/shipyard-components-2026-10-31:refs/remotes/origin/educational/shipyard-components-2026-10-31' \
  '+refs/heads/research/agent-methods-2026-10-31-public:refs/remotes/origin/research/agent-methods-2026-10-31-public'
```

Use global `--ref` to inspect a locally available revision. Record the resolved
commit when comparing findings. A main-branch inventory is not all-branch
coverage, and an archive's implementation receipt is not proof of a capability
installed on a new host.

## What still needs separate evidence

The semantic review concentrated on entry documents, source relationships,
navigation/tooling contracts, the offline desk and selected strategy and
research discrepancies. The full archive was preserved, not exhaustively
executed or independently revalidated. No market-data refresh, broker action,
schedule, private memory migration or service deployment forms part of these
acceptance results.

Actual LLM improvement should be tested with matched before/after tasks: locate
the correct Teddy stop contract, reproduce the desk, distinguish forecast
layers, separate the agent-research collections and interpret a historical
receipt correctly. Hold model, tools and budget constant; retain failures and
measure task success, source correctness and cost separately. The new library
provides concrete routes and reproducible checks for that evaluation without
claiming a gain that has not been measured.
