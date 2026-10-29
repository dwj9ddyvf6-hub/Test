Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE08 - HAR-style realized-volatility forecast - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE08; it does not duplicate the shared code.
- **Family:** Volatility
- **Target:** realized variance (target unit: variance_fraction_squared)
- **Horizon:** 1-5 sessions
- **Forecast unit:** variance
- **Score kind:** continuous (continuous_point_estimate_not_directional)
- **Maturity:** CORE-RESEARCH
- **Formula key:** `har` in `catalog.py`; scorer `f_har` in `scorers.py`; edge card `FE08` in `edge_cards.py`

## Inputs

- `log_rv_1` (unit: log_variance, max age 172800s, min quality 0.2)
- `log_rv_5` (unit: log_variance, max age 172800s, min quality 0.2)
- `log_rv_22` (unit: log_variance, max age 172800s, min quality 0.2)
- `log_rv_baseline` (unit: log_variance, max age 172800s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_har(x: Mapping[str, float]) -> Signal:
    log_forecast = 0.50 * x["log_rv_1"] + 0.30 * x["log_rv_5"] + 0.20 * x["log_rv_22"]
    clipped_forecast = _clip(log_forecast, -40.0, 10.0)
    clipped_baseline = _clip(x["log_rv_baseline"], -40.0, 10.0)
    forecast_variance = exp(clipped_forecast)
    baseline = exp(clipped_baseline)
    ratio_log = clipped_forecast - clipped_baseline
    return Signal(forecast_variance, ratio_log, {"log_variance_ratio": ratio_log, "baseline_variance": baseline})
```

Catalog formula note: REA synthesis: Volatility / har family; vendor report inventory is traceability, not validation.

## Assumptions

- Forecast variance, not direction; variance inputs share a consistent sampling scheme.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Bad print, stale bar window, or sampling-definition change.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE08
- **edge_source:** accuracy
- **novel_mechanism:** Forecast realized variance as a scale-invariant surface across 1-, 5-, and 22-session components, then check if the forecast survives sampling-clock changes.
- **target_definition:** Realized variance accumulated over the selected fixed session window, with a frozen sampling and adjustment rule.
- **price_aware_baseline:** Symbol's own HAR(1,5,22) history, current implied variance, and unconditional variance.
- **payer_hypothesis:** Hypothesis: option sellers and risk-budget allocators pay for better second-moment estimates.
- **scarcity_or_transfer:** Accuracy about risk can improve sizing or pricing, but does not imply return direction or monetizable payoff.
- **bad_state:** Jump, bad print, corporate action, sampling change, or volatility regime transition.
- **holdability_and_co_losses:** Model portfolio variance and joint stress with every volatility and tail sleeve; assess funding path.
- **execution_net:** For any later payoff test, charge real option spread, hedge slippage, theta, and margin funding.
- **decisive_test:** Compare against the stock's own HAR baseline on a frozen next-open sample with QLIKE and interval coverage.
- **kill_rule:** Kill if no incremental variance skill over HAR or the apparent gain depends on a sampling definition.
- **source_refs:** ('research/rea_teardowns/targets/squeezemetrics.md', 'research/rea_teardowns/targets/spotgamma.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
