Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE14 - Options-implied downside tail state - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE14; it does not duplicate the shared code.
- **Family:** Options
- **Target:** physical left-tail event (target unit: binary_left_tail_event)
- **Horizon:** 1-20 sessions
- **Forecast unit:** risk_score_heuristic
- **Score kind:** risk (uncalibrated_risk_rank_only)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `option_tail` in `catalog.py`; scorer `f_option_tail` in `scorers.py`; edge card `FE14` in `edge_cards.py`

## Inputs

- `put_skew_z` (unit: z, max age 172800s, min quality 0.2)
- `term_inversion_z` (unit: z, max age 172800s, min quality 0.2)
- `downside_var_z` (unit: z, max age 172800s, min quality 0.2)
- `surface_quality` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_option_tail(x: Mapping[str, float]) -> Signal:
    surface_quality = _clip(x["surface_quality"], 0.0, 1.0)
    logit = -0.50 + surface_quality * (0.55 * x["put_skew_z"] + 0.35 * x["term_inversion_z"] + 0.35 * x["downside_var_z"])
    return _risk(logit, surface_quality=surface_quality, put_skew_z=x["put_skew_z"], term_inversion_z=x["term_inversion_z"])
```

Catalog formula note: REA synthesis: Options / option_tail family; vendor report inventory is traceability, not validation.

## Assumptions

- Risk-neutral surface is not a physical probability forecast.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Stale/missing quotes, crossed market, or no-arbitrage surface failure.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE14
- **edge_source:** accuracy
- **novel_mechanism:** Rank downside-tail conditions from put skew, term inversion, and downside variance, gated by surface quality; the score is not a physical probability.
- **target_definition:** One if the underlying realizes the predeclared left-tail barrier within the selected window; otherwise zero.
- **price_aware_baseline:** Same-name realized tail rate, volatility baseline, and index tail state.
- **payer_hypothesis:** Hypothesis: protection buyers pay a premium for convexity; a better physical-vs-priced tail estimate may identify relative richness.
- **scarcity_or_transfer:** The candidate edge is better tail calibration, not interpreting option-implied probabilities as physical probabilities.
- **bad_state:** Surface arbitrage, stale quote, jump, event timing, or a sudden correlation spike.
- **holdability_and_co_losses:** Measure portfolio tail loss, hedge basis, and cost drag; co-losses with short-vol and correlation sleeves.
- **execution_net:** Include option bid/ask, skew, hedge slippage, theta, borrow, and capital usage before any payoff claim.
- **decisive_test:** Freeze surface construction and labels; score physical tail calibration by underlying, tenor, and regime against realized history.
- **kill_rule:** Kill if surface quality fails or physical tail calibration does not improve versus realized-history baseline.
- **source_refs:** ('research/rea_teardowns/targets/optionstrat.md', 'research/rea_teardowns/targets/squeezemetrics.md', 'research/rea_teardowns/targets/quant-data.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
