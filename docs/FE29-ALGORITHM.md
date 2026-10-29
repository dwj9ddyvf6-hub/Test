Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE29 - Commodity positioning, inventory, and supply shock - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE29; it does not duplicate the shared code.
- **Family:** Commodities
- **Target:** commodity excess return (target unit: forward_return_fraction)
- **Horizon:** 1-8 weeks
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `cot` in `catalog.py`; scorer `f_cot` in `scorers.py`; edge card `FE29` in `edge_cards.py`

## Inputs

- `cot_positioning_z` (unit: z, max age 1209600s, min quality 0.2)
- `inventory_deviation_z` (unit: z, max age 691200s, min quality 0.2)
- `roll_yield_z` (unit: z, max age 172800s, min quality 0.2)
- `supply_shock_score` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_cot(x: Mapping[str, float]) -> Signal:
    supply_shock = _clip(x["supply_shock_score"], 0.0, 1.0)
    crowding_fade = -x["cot_positioning_z"] * _clip(abs(x["cot_positioning_z"]) / 2.0, 0.0, 1.5)
    inventory = -0.60 * x["inventory_deviation_z"] + 0.25 * x["roll_yield_z"]
    return _signed((0.60 * crowding_fade + 0.40 * inventory) * (1.0 - supply_shock),
                   crowding_fade=crowding_fade, inventory_carry=inventory, supply_shock=supply_shock)
```

Catalog formula note: REA synthesis: Commodities / cot family; vendor report inventory is traceability, not validation.

## Assumptions

- COT and inventory freshness use source-specific measurement and publication times. Positive COT positioning means crowded long exposure (faded); positive inventory deviation means above-normal supply (bearish); positive roll yield means backwardation (bullish). supply_shock_score is bounded [0, 1] and suppresses the signal. Apply only the release schedule effective on each date.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Supply shock, delayed release, benchmark/contract roll discontinuity.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE29
- **edge_source:** access
- **novel_mechanism:** Forecast a positioning/physical-flow squeeze when trader crowding diverges from inventory scarcity, while honoring the release schedule actually in force.
- **target_definition:** Commodity excess return from the selected publication-time reference to the fixed week endpoint.
- **price_aware_baseline:** Roll yield, seasonality, own volatility, and publication-calendar base rates.
- **payer_hypothesis:** Hypothesis: physical-market users and futures intermediaries pay for earlier synthesis of public positioning and inventory.
- **scarcity_or_transfer:** Public data creates no access by itself; value requires faster synthesis or capacity to warehouse the resulting risk.
- **bad_state:** Supply shock, benchmark roll, delayed release, revised seasonal factor, or crowd already on one side.
- **holdability_and_co_losses:** Stress margin, delivery/roll mechanics, and correlated commodity exposures; assume no easy exit in the squeeze.
- **execution_net:** Use point-in-time contract rolls, fees, margin, slippage, and delayed COT availability.
- **decisive_test:** Use as-of release dates and compare the joint model with roll-yield-only and inventory-only baselines.
- **kill_rule:** Kill if publication vintage is wrong, supply shocks dominate the relationship, or holdout value is not net of roll and margin.
- **source_refs:** ('research/rea_teardowns/targets/quant-data.md', 'research/rea_teardowns/targets/squeezemetrics.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
