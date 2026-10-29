Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE05 - Breadth participation impulse - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE05; it does not duplicate the shared code.
- **Family:** Breadth/rotation
- **Target:** index/market direction (target unit: forward_return_fraction)
- **Horizon:** 1-5 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CORE-RESEARCH
- **Formula key:** `breadth` in `catalog.py`; scorer `f_breadth` in `scorers.py`; edge card `FE05` in `edge_cards.py`

## Inputs

- `breadth_delta` (unit: signed_ratio, max age 172800s, min quality 0.2, range (-1.0, 1.0))
- `advance_decline_z` (unit: z, max age 172800s, min quality 0.2)
- `new_high_low_z` (unit: z, max age 172800s, min quality 0.2)
- `index_trend_z` (unit: z, max age 172800s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_breadth(x: Mapping[str, float]) -> Signal:
    participation = _clip(x["breadth_delta"], -1.0, 1.0)
    score = 0.50 * participation * 3.0 + 0.25 * x["advance_decline_z"] + 0.15 * x["new_high_low_z"] + 0.10 * x["index_trend_z"]
    return _signed(score, breadth_delta=participation, advance_decline_z=x["advance_decline_z"], new_high_low_z=x["new_high_low_z"])
```

Catalog formula note: REA synthesis: Breadth/rotation / breadth family; vendor report inventory is traceability, not validation.

## Assumptions

- Constituent set and breadth timestamps are point-in-time; breadth_delta is bounded [-1, 1], and positive breadth_delta and advance-decline/new-high-low z-scores mean broader positive participation.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Constituent coverage falls below its declared threshold.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE05
- **edge_source:** accuracy
- **novel_mechanism:** Combine point-in-time breadth participation, advance/decline, new-high/low, and index trend into a directional index-return score.
- **target_definition:** Index return relative to the predeclared market benchmark from as_of to the selected fixed session close.
- **price_aware_baseline:** Index return, volatility, and equal-weight/cap-weight spread without a breadth overlay.
- **payer_hypothesis:** Hypothesis: benchmark-tracking flows pay when leadership broadens or narrows faster than their rebalance schedule.
- **scarcity_or_transfer:** Potential accuracy from hidden concentration in the index move, not breadth indicators counted as independent votes.
- **bad_state:** Constituent changes, stale membership, mega-cap event, or breadth data with uneven timestamps.
- **holdability_and_co_losses:** Co-loss with trend and sector rotation; stress concentration in a few names and rebalance turnover.
- **execution_net:** Next-session marks with constituent spreads, index/basket basis, and rebalance impact.
- **decisive_test:** Use point-in-time membership and issuer-clustered dates; score benchmark-relative index return, with equal-weight/cap-weight spread as a predictor and baseline control.
- **kill_rule:** Kill if improvement disappears after membership, sector, and mega-cap controls or if the sign is era-specific.
- **source_refs:** ('research/rea_teardowns/targets/finviz-screener.md', 'research/rea_teardowns/targets/trendspider.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
