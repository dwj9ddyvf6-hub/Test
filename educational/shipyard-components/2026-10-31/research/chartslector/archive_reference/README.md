# ChartsLector owner-supplied archive references

This is an **educational archive reference**, not a live adapter, production integration, or a claim of readiness. The archive source came from an owner-supplied project subtree. Private repository identities and machine-local paths are intentionally templated. No blanket reuse license is granted by this handoff; this is not a finding that owner-controlled publication is forbidden.

## Included modules and references

| Reference | What it contains | Include/hold and limitations |
|---|---|---|
| `ship/sleeve_cl/chartslector/cl_core.py` | Pure array math: SMA/EMA/RMA/ATR, a technical screen, VMR scoring and composite. | Included unchanged as archival code. NumPy and Pandas required. No bars/provider data or live wiring. |
| `systems/ranker_feats.py` | OHLCV panel features, cross-sectional percentiles and component/combined ranker scoring. | Included after replacing the owner-workspace import with a relative sibling-library path and removing local research-path references from comments. NumPy/Pandas plus `ind.py` are required; `ind.py` imports Numba. The `score()` component-coefficient map and underlying fit data/results are absent; static mixture weights are source values, not calibrated claims. |
| `systems/screens.py` | TradingView-style and custom panel screen masks, including weekly-to-daily mapping. | Included after converting one absolute import to the local archive sibling indicator. Requires NumPy/Pandas and `ind.py` (which imports Numba). It consumes caller-provided panels; no symbol feed or sector/float dataset is provided. |
| `systems/s03_market.py.reference.txt` | Breadth counts, rolling ratios, moving-average breadth, screener counts, risk-appetite ratios and timing-research wiring. | Source text only: it reads a panel at module import and writes cache/output files. The data panel, `data`, `timing`, `bt`, and other runtime modules are not included. Do not import or execute this reference. |
| `tests/pine_ref.py` | Literal series-by-series reference functions for indicators, stages, relative strength, ratio/momentum, gap counts, LoD entry math and a risk-size formula. | Included unchanged as pure reference code. NumPy required. The entry/risk-size formulas are historical research examples, not advice, eligibility or execution authority. |
| `tests/cl_parity_research.py.reference.txt` | Research-vs-generator recall/precision comparison harness. | Source text only; absolute archive/interpreter/engine-bar paths are templates. It requires omitted raw bars, captured candidates and generator code and writes result files. Not executed. |
| `tests/test_cl_sleeve.py.reference.txt` | Archive integration test source describing parity, stale-input fail-closed checks, package build/rollback rehearsal. | Source text only; private path bindings are templates. It requires the omitted staged app tree, raw bars, proof fixtures and build/ship/rollback scripts. Not executed or wired. |
| `tests/run_tests.py.reference.txt` | Historical research test runner for screens, ranker, breadth/rotation grids and result sanity checks. | Source text only. Its datasets, fitted caches, generated result tables and referenced modules are not included; no result report is copied and it was not run. |

## Dependency and data boundary

The algorithms require NumPy/Pandas; the shared archive indicator implementation imports Numba. No Python dependency lock or exact upstream environment is supplied. The local synthetic tests below used the environment’s NumPy 2.3.5 and Pandas 2.2.3; because Numba is unavailable here, the test-only harness substitutes only an identity `njit` decorator. This does not validate JIT behavior and is not a product fallback. The private project’s fitted coefficients, raw provider captures, market panels, research outputs and any live/staged tree are excluded.

`python3 scripts/test-chartslector-archive.py` runs only the synthetic analytical checks. It does not run the archival `.reference.txt` harnesses.
