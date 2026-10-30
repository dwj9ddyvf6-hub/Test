# Fixed README section (generator source)

The root `README.md` is regenerated from `docs/CATALOG.json` by a generator that is **not in this repository**.
That regeneration has dropped the agent-guide links before. Whatever produces the README must emit the block
below verbatim, between the `BEGIN FIXED SECTION` / `END FIXED SECTION` markers, right after the line
"Monitors and research recorders are not listed."

Verify any regenerated README with:

    python3 agentic-trade-desk/skeleton/tools/check_root_readme_links.py README.md

```markdown
<!-- BEGIN FIXED SECTION: agent guides. The README generator should emit this block verbatim (source text: docs/README_FIXED_SECTION.md). Checked by agentic-trade-desk/skeleton/tools/check_root_readme_links.py -->
> **New: [How to build an agentic trade desk](agentic-trade-desk/README.md)** — a full guide, written for LLM agents, covering architecture, setup, order safety, reconciliation, reliability, research validation, multi-agent coordination, 130 catalogued pitfalls, checklists and generic reference code. Paper trading only; not financial advice. See also the shorter [build guide](docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md).
> **Guides for LLM agents:** [Agentic Trade Desk Build Guide](docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md) (architecture and phases) · [`agentic-trade-desk/`](agentic-trade-desk/README.md) (operational kit: invariants, 130 pitfalls, reference skeleton code with tests included).
<!-- END FIXED SECTION -->
```
