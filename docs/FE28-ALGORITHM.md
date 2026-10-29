Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE28 - Yield-curve and credit regime transition - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE28; it does not duplicate the shared code.
- **Family:** Macro/rates
- **Target:** market stress transition risk (target unit: binary_stress_event)
- **Horizon:** 1-4 quarters
- **Forecast unit:** risk_score_heuristic
- **Score kind:** risk (uncalibrated_risk_rank_only)
- **Maturity:** CORE-RESEARCH
- **Formula key:** `rates_credit` in `catalog.py`; scorer `f_rates_credit` in `scorers.py`; edge card `FE28` in `edge_cards.py`

## Inputs

- `curve_slope_z` (unit: z, max age 172800s, min quality 0.2)
- `curve_change_z` (unit: z, max age 172800s, min quality 0.2)
- `credit_impulse_z` (unit: z, max age 7776000s, min quality 0.2)
- `macro_transition_score` (unit: ratio, max age 7776000s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_rates_credit(x: Mapping[str, float]) -> Signal:
    transition = _clip(x["macro_transition_score"], 0.0, 1.0)
    curve_signal = _clip((-x["curve_slope_z"] + 0.25 * x["curve_change_z"]), -4.0, 4.0)
    credit_stress = max(0.0, -x["credit_impulse_z"])
    return _risk(-0.70 + 0.55 * curve_signal + 0.60 * credit_stress + 0.65 * transition,
                 curve_signal=curve_signal, credit_stress=credit_stress, transition=transition)
```

Catalog formula note: REA synthesis: Macro/rates / rates_credit family; vendor report inventory is traceability, not validation.

## Assumptions

- Macro observations use their historical availability dates and vintages; no revised-data leakage. Positive curve_slope_z means a steeper/less inverted curve; positive curve_change_z means a move toward deeper inversion; positive credit_impulse_z means easing credit conditions (negative values mean deterioration).
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Vintage history missing or abrupt policy/market-structure break.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE28
- **edge_source:** accuracy
- **novel_mechanism:** Rank stress transition from curve slope, curve-change direction, credit impulse, and the declared macro-transition feature rather than curve level alone.
- **target_definition:** One if the predeclared market-stress transition criterion is met by the selected quarter end; otherwise zero.
- **price_aware_baseline:** Curve slope alone, credit spread alone, and a base-rate macro hazard.
- **payer_hypothesis:** Hypothesis: risk committees pay for earlier de-risking evidence before growth and funding stress become obvious.
- **scarcity_or_transfer:** Potential accuracy is transition timing after point-in-time macro vintages, not a precise recession date claim.
- **bad_state:** Policy regime change, fiscal shock, benchmark discontinuity, or revised macro history.
- **holdability_and_co_losses:** Portfolio co-loss in equities, credit, rates, and FX; assess collateral and mark-to-market path.
- **execution_net:** Value any overlay as avoided portfolio loss less hedge carry, slippage, and rebalance churn.
- **decisive_test:** Lock vintages at release; use expanding/rolling origins and compare to single-curve and base-rate models.
- **kill_rule:** Kill if point-in-time vintages fail or conditional transition skill does not persist across eras.
- **source_refs:** ('research/rea_teardowns/targets/market-chameleon.md', 'research/rea_teardowns/targets/stock-rover.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
