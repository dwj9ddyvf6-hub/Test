# Original evidence and portable code

All 14 source files from `/workspace/alpha-invention-local` are preserved byte-for-byte under `original/`, enumerated in `provenance/source_inventory.json`. The original report records the then-current read-only boundary; the later explicit save request authorizes this GitHub package. Preserve that history instead of rewriting the original account.

The root copies of the two reports change local absolute citation targets into relative links for GitHub readability. Their originals remain unchanged. `run_historical.py` adapts only the source import root, data paths, parent-event path, output directory, and corresponding descriptive path string from `original/two_clocks.py`. It writes `runs/historical/`. The numerical code is preserved. `tests/test_historical_kernel.py` adapts only the import from the original six tests.

The four vendored source modules are copied from the existing master-desk research revision. `perp_expression_lab.py` includes an inherited public-data fetching function, but portable replay calls only its local loader. No download or API request is needed during replay. `requests` remains a pinned import dependency because that source is preserved unchanged.

The new `reference.py` is a separate standard-library implementation of supplied-input kernels. It is intentionally narrower than a production strategy engine. Its outputs neither authenticate facts nor establish profitable forecasts. Its semantic restrictions define the finite model's supported domain; expanding the domain requires additional state logic and tests.

Python 3.12.14 and the exact scientific-library versions in `requirements-reproduction.txt` were observed in the research environment. These are reproduction pins, not a promise that every future package index retains every wheel. If rebuilding with a different environment, record the change and compare full outputs before interpreting numerical differences.
