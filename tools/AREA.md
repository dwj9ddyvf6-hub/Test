# tools/: use the library and maintain its map

These standard-library Python tools provide local navigation and reproducible inventories. They do not run a strategy, fetch market data, contact a broker, activate a service or publish a repository change.

- [repo_navigator.py](repo_navigator.py): search paths/content, select a curated task route, create a bounded reading packet, or check navigation integrity. The curated route and area definitions live once in [docs/REPOSITORY-MAP.json](../docs/REPOSITORY-MAP.json).
- [build_repo_index.py](build_repo_index.py): generate INDEX.json/INDEX.md from a selected local commit, the staged candidate, a saved tree or the GitHub API; `--check` compares saved outputs without rewriting them.

```sh
python3 tools/repo_navigator.py search tensor
python3 tools/repo_navigator.py route explain-strategy
python3 tools/repo_navigator.py packet explain-strategy --max-chars 18000
python3 tools/repo_navigator.py check
python3 tools/build_repo_index.py --local-repo . --ref HEAD --check --out-dir .
```

Run the commands from the repository root. For a published inventory, commit source updates first, generate the index from that exact commit, and then commit the two generated outputs. A staged inventory has an exact computed Git tree hash and no commit; label it as a candidate. Only the two index outputs have self-excluded hashes: the generator and every other source file remain hashed.

The exact tool inventory and captured revision are in [INDEX.md](../INDEX.md) and [INDEX.json](../INDEX.json). The [operating guide](../docs/LLM-OPERATING-GUIDE.md) explains how to use search results and packets as evidence without turning them into unsupported capability claims.
