Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE06 - Sector leadership diffusion - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE06; it does not duplicate the shared code.
- **Family:** Breadth/rotation
- **Target:** relative sector return (target unit: forward_return_fraction)
- **Horizon:** 5-20 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CORE-RESEARCH
- **Formula key:** `sector` in `catalog.py`; scorer `f_sector` in `scorers.py`; edge card `FE06` in `edge_cards.py`

## Inputs

- `sector_momentum_rank_z` (unit: z, max age 172800s, min quality 0.2)
- `leadership_breadth` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))
- `sector_dispersion_z` (unit: z, max age 172800s, min quality 0.2)
- `sector_flow_z` (unit: z, max age 172800s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_sector(x: Mapping[str, float]) -> Signal:
    breadth = _clip(x["leadership_breadth"], 0.0, 1.0)
    dispersion = _clip(x["sector_dispersion_z"], 0.0, 3.0)
    concentration_penalty = 1.0 / (1.0 + 0.20 * dispersion)
    score = (0.55 * x["sector_momentum_rank_z"] + 0.25 * x["sector_flow_z"] + 0.20 * (2.0 * breadth - 1.0)) * concentration_penalty
    return _signed(score, breadth=breadth, dispersion=dispersion, concentration_penalty=concentration_penalty)
```

Catalog formula note: REA synthesis: Breadth/rotation / sector family; vendor report inventory is traceability, not validation.

## Assumptions

- Sector ranks use contemporaneous membership and neutralization.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Membership/survivorship uncertainty or sector dispersion regime break.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE06
- **edge_source:** accuracy
- **novel_mechanism:** Combine sector momentum rank, sector flow, and leadership breadth; attenuate the score when cross-sector dispersion is elevated.
- **target_definition:** Sector return relative to the predeclared benchmark from as_of to the selected fixed session close.
- **price_aware_baseline:** Sector momentum rank and market beta with point-in-time sector membership.
- **payer_hypothesis:** Hypothesis: benchmark managers and thematic allocators trade the lag between leadership evidence and scheduled review.
- **scarcity_or_transfer:** Potential accuracy from transition timing and diffusion breadth beyond a sector momentum score.
- **bad_state:** One-stock sector concentration, macro shock, classification change, or common-factor reversal.
- **holdability_and_co_losses:** Track sector overlap and joint drawdowns; cap concentration and count each issuer once.
- **execution_net:** Net long/short basket returns at next executable marks with turnover, borrow, and rebalance costs.
- **decisive_test:** Freeze sector membership, benchmark, and return endpoint; compare sector-relative return forecasts to momentum-only and equal-weight sector baselines. Score handoff events separately.
- **kill_rule:** Retire if transition forecasts do not improve rank/log score and net spreads in the untouched era.
- **source_refs:** ('research/rea_teardowns/targets/finviz-screener.md', 'research/rea_teardowns/targets/stock-rover.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
