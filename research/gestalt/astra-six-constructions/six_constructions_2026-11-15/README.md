# Six constructions: complete research and implementation handoff

Start with [LLM_BUILD_GUIDE.md](LLM_BUILD_GUIDE.md), then the [detailed report](SIX_CONSTRUCTIONS_DETAILED_REPORT.md). This standalone directory contains all 14 files from the local six-construction research folder, byte-exact originals, readable report copies, all 12 hedge policies at both horizons, initial and amended results, event-level outcomes, source snapshots, and the exact available public inputs needed for the historical replay.

The package also adds six implementation specifications, machine-readable contracts, standard-library payoff/timing kernels, synthetic examples, and tests. These additions turn the report into a build handoff. They do not turn the four untested strategy designs into empirically validated strategies.

## What is ready

| ID | Construction | Implemented here | Still needed for an empirical strategy |
|---|---|---|---|
| C1 | Buy panic; hedge reassurance | Original and portable historical replay; raw inputs; complete frozen outputs | Fresh universe/history, executable fills, collateral and portfolio evaluation |
| C2 | Sell the middle of a rebound | Payoff kernel, examples, specification | Actual chains, recovery definition, conditional band forecast, assignment-aware replay |
| C3 | Repair, then rotate | Repair and same-capital comparison kernels; specification | Point-in-time equity panel, leadership policy, full capital-path replay |
| C4 | Spend volatility forecasts on execution | Intent-level shortfall kernel; specification | Quote/order data, fill model, prospective evaluation |
| C5 | History-conditioned contract hedge | Original and expanded finite-state models; semantic checks | Verified real rules/history and executable quotes |
| C6 | Price the squeeze tail | Band-liability expectation and payoff kernels; specification | Physical tail forecast, executable options and capital/assignment model |

## Run the supplied-input examples immediately

Python 3.12 is the reference runtime. These two commands need no installed libraries, API key, market access, or network:

```bash
python reference.py
python run_request.py examples/C2.json
python -m unittest discover -s tests -p test_reference.py -v
```

The output is explicitly synthetic. It includes the bearish-mean/losing-call-spread counterexample, the adverse prediction-market state, partial-fill opportunity cost, and the recovery-rotation comparison.

Each construction has an input file `examples/C1.json` through `C6.json` and a matching expected output. `run_request.py` dispatches these supplied-input calculations. `schemas/offline_request.schema.json` documents the request envelope and field types; cross-field economic and time checks live in `reference.py` and the specifications.

## Reproduce the historical experiment from this directory

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-reproduction.txt
.venv/bin/python tools/verify_bundle.py
.venv/bin/python tools/restore_data.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python run_historical.py
.venv/bin/python tools/verify_reproduction.py
```

Package installation needs access to the pinned dependencies unless they are already installed. Data restoration and replay then use local files only. The exact raw archive includes 799 files: 633 spot archives, 164 perpetual/funding archives, and two source retrieval manifests. Unavailable source months remain recorded as unavailable. The replay must match all numerical leaves of `original/results.json` and `original/event_paths.json` within the documented floating-point tolerance; matching only three headline means is insufficient.

Outputs go under `runs/historical/`; restored data go under `data/`. Neither directory is part of the saved payload. The original prototype's absolute paths are retained only in `original/` as historical evidence. Use `run_historical.py` for portable execution. See [PORTABILITY.md](PORTABILITY.md).

## Read in this order

1. [Build guide](LLM_BUILD_GUIDE.md): executable starting point, exact deliverables, input/output boundaries.
2. [Detailed report](SIX_CONSTRUCTIONS_DETAILED_REPORT.md): economics, arithmetic, alternatives, and limitations.
3. [Construction contracts](contracts.json) and [data dictionary](DATA_CONTRACTS.md).
4. The relevant file in [specs](specs/).
5. [Research decision record](RESEARCH_DECISIONS.md), [experiment plan](EXPERIMENT_PLAN.md), and [coverage](COVERAGE.md).
6. [Prior research index](PRIOR_RESEARCH.md) for earlier corpus work and preserved strategy registers.

## Authority and evidence

The latest owner request explicitly authorizes saving this detailed handoff to GitHub, replacing the preceding read-only boundary for this save. It does not authorize live trading or production integration. No credential is included. No new Decisions API call was needed for packaging; prior recorded calls remain linked in the earlier research payload.

Historical returns are exploratory event returns per initial asset notional, not margin-account returns. Synthetic correctness is not market profitability. The full candidate family, original result sets, unresolved parameters, and unfavorable comparisons are preserved.

`MANIFEST.json` enumerates the save set. `tools/verify_bundle.py` verifies it from file bytes. Verification results in `verification/` state the exact code scope checked. A later remote receipt, when present beside the package, identifies the saved commit and its independent destination read-back.
