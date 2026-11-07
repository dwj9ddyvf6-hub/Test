# Fixed README section (generator source)

The root `README.md` contains listings derived from `docs/CATALOG.json` and `docs/ALL-SLEEVES.json`. The historical README producer is external to this repository; the local inventory generator builds only INDEX.md and INDEX.json.
That regeneration has dropped the agent-guide links before. Whatever produces the README must emit the block
below verbatim, including its `BEGIN FIXED SECTION` / `END FIXED SECTION` markers, under the
"Guides for agents and builders" heading after the three strategy views. Preserve the substantive
front matter and both full listings when regenerating; this block is only one preservation contract.

The check compares the exact block with this source, requires exactly one marker pair, and resolves
all three guide targets plus the reconciliation relative to the selected README. Verify with:

    python3 agentic-trade-desk/skeleton/tools/check_root_readme_links.py README.md

```markdown
<!-- BEGIN FIXED SECTION: agent guides. The README generator should emit this block verbatim (source text: docs/README_FIXED_SECTION.md). Checked by agentic-trade-desk/skeleton/tools/check_root_readme_links.py -->
> **Guides for LLM agents: three guides, one desk.** Start with the [three-guide reconciliation](docs/THREE-GUIDES-RECONCILIATION.md): the map between the three guides, covering what all three agree on, what only one teaches, and the differences to decide consciously.
> **Field guide:** [How to build an agentic trade desk](docs/AGENTIC-TRADE-DESK-GUIDE.md): judgment under operation, scoping and evidence grading, the cross-desk sleeve accounting standard, forecast grading machinery, and 60 catalogued pitfalls.
> **Operational kit:** [`agentic-trade-desk/`](agentic-trade-desk/README.md): the running machine, one order path, reconciliation, reliability and failover operations, 130 catalogued pitfalls, and a runnable skeleton with tests. Paper trading only.
> **Companion build guide:** [Agentic Trade Desk Build Guide](docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md): architecture before code, product modes, layers and data contracts, build phases, and acceptance checklists.
<!-- END FIXED SECTION -->
```
