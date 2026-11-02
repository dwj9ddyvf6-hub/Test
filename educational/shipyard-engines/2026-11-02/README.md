# Shipyard engine-only research package — local candidate

**Scope:** this is an offline collection of selected, caller-input math kernels and synthetic tests. It is not the former broad component package, a deployable app, or a source-acquisition service. This directory is a local review candidate; this package-writing task did not publish or push it anywhere.

## What is here

- **30 numeric forecast scorers** with manual feature contracts. They return uncalibrated research scores and keep `decision_eligible: false`; they are not 30 live or source-bound engines, forecasts, or evidence of trading edge.
- **ChartsLector bounded calculator** (`calculateChartslector`): the reviewed standalone Pine-subset port only. It is not the full ChartsLector archive, full live-Lector, a data feed, a ranker, or an order interface.
- **Eight explicit-input math labs**: static GEX, supplied-print activity summaries, screener filtering, factor ranking, confluence aggregation, hypothetical portfolio construction, SMA replay, and daily-change calculation; two shared parsing/validation helpers support these modules. A module name can describe an input format, not access to that vendor or a proprietary model. Inputs and CSVs must be supplied by the caller.
- **Saty research kernels** and **RRE** core/policy kernels: bounded in-memory research calculations and model state. These can produce hypotheses or candidate signals; they do not connect to a broker, hold real account data, or submit orders.
- **Lector chart-math subset**: a newly named module formed only from three reviewed math-script bodies plus an export boundary. It is not the full Lector bundle, desk read, setup plan, or an operational product.

The tests use fabricated values only. The parity suite checks 30 scorer implementations against 344 deterministic algebra/contract vectors; these checks are not market backtests, alpha tests, live integrations, or performance evidence.

## Deliberately not included

No UI, server, service, authentication, database, recovery flow, initiative or operations layer, private config, account/credential data, provider client, network fetch, raw market/licensed data, full Lector bundle, full Aperture system, FE06 source transform, or FE12 provider transforms are included. The **11 source bindings shown in historical implementation metadata were not copied or verified here**; they must not be read as active feeds or current availability. The numeric scorer catalog does not acquire its own features. The separately public [Psychology v0.4.1 calculator (verified Test path at main commit `346dd1f`)](https://github.com/dwj9ddyvf6-hub/Test/tree/346dd1f/psychology-engine) is outside this package; its private operational bridge was not copied. Full Lector, Aperture, FE06/FE12 provider transforms, and private operations remain deferred.

`SOURCES` and explanatory comments retained in the Saty source are attribution, not claims that this package reproduces a discretionary author's complete method. Some source metadata was previously redacted in a reviewed export. `SOURCE-MANIFEST.json` records content hashes and representation types without publishing private repository identifiers or local source locations.

## Local, offline checks

Requires a recent local Node.js runtime and Python 3. No project dependencies are installed or downloaded. The commands only execute files in this tree:

```sh
npm test
python -B scripts/build_forecast_parity_vectors.py --check
```

`npm test` runs the exact-path/hash verifier, the direct JavaScript tests, and Python kernel tests. The Python parity command independently checks the 30-engine/344-vector fixture against its included canonical scorer. An expected known-answer or contract test is not evidence of calibration, reliability on provider data, or production readiness.

The Python sources are not installed as a wheel. From the package root, add the relative `python/saty` directory to `sys.path` before importing Saty modules (as the direct test does); for example:

```python
import sys
sys.path.insert(0, 'python/saty')
from saty_reference import Indicators
from saty_system.strategies import StrategyEngine
```

RRE imports are tested from the package root as `from python.rre.raschke_core import Core`. No private host package is required.

A small scorer example using a caller-supplied synthetic feature object:

```js
import { evaluateForecastEngine } from './dist/forecast-engines.mjs';
const result = evaluateForecastEngine('FE01', {
  ret_21d_z: 0, ret_63d_z: 0, ret_252d_z: 0,
  trend_efficiency: 0.5, vol_regime: 0
});
// Research-only score; result.decision_eligible is false.
```

For every engine, consult `ENGINE-CATALOG.json`, the module's exports, and its caller-input requirements. No default network or filesystem data source is supplied.
