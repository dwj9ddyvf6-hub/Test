Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE15 - Dealer-gamma scenario map - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE15; it does not duplicate the shared code.
- **Family:** Options
- **Target:** scenario sensitivity (target unit: forward_return_fraction)
- **Horizon:** intraday-5 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** EXPERIMENTAL
- **Formula key:** `gamma` in `catalog.py`; scorer `f_gamma` in `scorers.py`; edge card `FE15` in `edge_cards.py`

## Inputs

- `gamma_assumption_z` (unit: z, max age 172800s, min quality 0.2)
- `spot_move_z` (unit: z, max age 172800s, min quality 0.2)
- `oi_concentration_z` (unit: z, max age 172800s, min quality 0.2)
- `gamma_input_quality` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_gamma(x: Mapping[str, float]) -> Signal:
    quality = _clip(x["gamma_input_quality"], 0.0, 1.0)
    # Positive assumed dealer gamma implies counter-trend delta hedging.
    score = -x["gamma_assumption_z"] * x["spot_move_z"] * (1.0 + 0.20 * abs(x["oi_concentration_z"])) * quality
    return _signed(score, gamma_assumption_z=x["gamma_assumption_z"], spot_move_z=x["spot_move_z"], inferred_input_quality=quality)
```

Catalog formula note: REA synthesis: Options / gamma family; vendor report inventory is traceability, not validation.

## Assumptions

- Dealer position sign is an explicit scenario assumption: positive means dealers are modeled long gamma and therefore hedge counter-trend; negative means short gamma and hedge with trend. The score is conditional hedge-flow sensitivity, never observed positioning.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Open-interest age or sign assumption changes; inferred inputs never become observed facts.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE15
- **edge_source:** accuracy
- **novel_mechanism:** Turn dealer-gamma displays into a scenario fan with sign uncertainty: calculate the path under long-, short-, and unknown-dealer exposure assumptions.
- **target_definition:** Conditional price/hedge-flow sensitivity under a caller-specified spot path; no unconditional realized outcome label is defined.
- **price_aware_baseline:** Underlying realized volatility, open-interest distribution, and a no-dealer-feedback scenario.
- **payer_hypothesis:** Hypothesis: users of option structure pay for a better conditional map of hedging pressure.
- **scarcity_or_transfer:** No edge unless one sign scenario predicts incremental outcomes and the sign is independently observable or robust.
- **bad_state:** Wrong dealer-side sign, OI staleness, expiration pin, or surface/contract-multiplier error.
- **holdability_and_co_losses:** Scenario outputs are not netted as positions; correlate with all options-tail/flow exposures.
- **execution_net:** Any future trade test prices the actual option/underlying legs and rejects unavailable quote depth.
- **decisive_test:** Replay caller-specified spot paths under positive, negative, and unknown dealer-gamma assumptions; validate the conditional hedge-flow arithmetic and units. A realized-outcome skill test requires a separate label contract.
- **kill_rule:** Kill directional language when sign is latent; retire if results depend on the chosen sign assumption.
- **source_refs:** ('research/rea_teardowns/targets/spotgamma.md', 'research/rea_teardowns/targets/menthorq.md', 'research/rea_teardowns/targets/gammaedge.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
