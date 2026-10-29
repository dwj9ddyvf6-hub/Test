Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE02 - Regime-gated residual reversion - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE02; it does not duplicate the shared code.
- **Family:** Price/technical
- **Target:** residual return (target unit: forward_return_fraction)
- **Horizon:** 1-5 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CORE-RESEARCH
- **Formula key:** `mean_reversion` in `catalog.py`; scorer `f_mean_reversion` in `scorers.py`; edge card `FE02` in `edge_cards.py`

## Inputs

- `residual_z` (unit: z, max age 172800s, min quality 0.2)
- `hurst` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))
- `trend_z` (unit: z, max age 172800s, min quality 0.2)
- `vol_regime` (unit: z, max age 172800s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_mean_reversion(x: Mapping[str, float]) -> Signal:
    chop = _clip((0.58 - x["hurst"]) / 0.25, 0.0, 1.0)
    trend_gate = _clip(1.0 - abs(x["trend_z"]) / 3.0, 0.0, 1.0)
    score = -x["residual_z"] * chop * trend_gate / (1.0 + 0.15 * abs(x["vol_regime"]))
    return _signed(score, chop_gate=chop, trend_gate=trend_gate, residual_z=x["residual_z"])
```

Catalog formula note: REA synthesis: Price/technical / mean_reversion family; vendor report inventory is traceability, not validation.

## Assumptions

- Fade only when supplied Hurst and trend features indicate a range.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Hurst/trend gate invalidates; residual exceeds the historical support window.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE02
- **edge_source:** accuracy
- **novel_mechanism:** Fade a residual only when supplied Hurst and trend features indicate a range; suppress the reversion score as trend strength or volatility rises.
- **target_definition:** Residual spread return from as_of to the selected fixed session close.
- **price_aware_baseline:** Same-name residual history, sector-adjusted return, and a no-trade rule during trend acceleration.
- **payer_hypothesis:** Hypothesis: liquidity providers and benchmark rebalancers supply the opposing flow.
- **scarcity_or_transfer:** Potential accuracy only when residual dislocation remains after common-factor and event information.
- **bad_state:** A genuine repricing, constituent event, borrow squeeze, or trend regime that makes the old mean irrelevant.
- **holdability_and_co_losses:** Require borrow and exit-depth stress; count correlated pair/sleeve losses as one book risk.
- **execution_net:** Enter at next executable mark; charge both legs, borrow, turnover, impact, and failed convergence.
- **decisive_test:** Freeze the residual-return endpoint and benchmark; compare its forecast to AR(1), sector-adjusted, and no-trade baselines. Score convergence-before-break separately.
- **kill_rule:** Retire after two consecutive out-of-sample windows with no incremental residual-return value over the frozen AR(1)/sector baselines or with persistent sign instability.
- **source_refs:** ('research/rea_teardowns/targets/market-chameleon.md', 'research/rea_teardowns/targets/stock-rover.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
