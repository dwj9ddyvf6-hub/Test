Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE17 - Earnings absolute-move forecast - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE17; it does not duplicate the shared code.
- **Family:** Events
- **Target:** absolute event return (target unit: absolute_return_fraction)
- **Horizon:** event to next session
- **Forecast unit:** absolute_return
- **Score kind:** continuous (continuous_point_estimate_not_directional)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `earnings` in `catalog.py`; scorer `f_earnings` in `scorers.py`; edge card `FE17` in `edge_cards.py`

## Inputs

- `implied_move` (unit: return, max age 259200s, min quality 0.2)
- `historical_event_move` (unit: return, max age 31536000s, min quality 0.2)
- `estimate_dispersion_z` (unit: z, max age 259200s, min quality 0.2)
- `earnings_timing_quality` (unit: ratio, max age 259200s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_earnings(x: Mapping[str, float]) -> Signal:
    implied = max(0.0, x["implied_move"])
    historical = max(0.0, x["historical_event_move"])
    dispersion_adjustment = 1.0 + 0.08 * max(-2.0, min(2.0, x["estimate_dispersion_z"]))
    timing = _clip(x["earnings_timing_quality"], 0.0, 1.0)
    value = (0.60 * implied + 0.40 * historical) * dispersion_adjustment * timing
    return Signal(value, dispersion_adjustment - 1.0, {"implied_move": implied, "historical_event_move": historical, "dispersion_adjustment": dispersion_adjustment})
```

Catalog formula note: REA synthesis: Events / earnings family; vendor report inventory is traceability, not validation.

## Assumptions

- Estimate event-time labels without using post-event marks.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Event time/announcement type uncertain or option surface quality fails.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE17
- **edge_source:** accuracy
- **novel_mechanism:** Forecast the absolute underlying move from the timestamped release; use implied move as a comparator, not as a subtracted component of the primary target.
- **target_definition:** Absolute underlying return from the timestamped earnings release to the selected next-session close.
- **price_aware_baseline:** Option-implied move, same-name event history, and volatility-matched event base rate.
- **payer_hypothesis:** Hypothesis: event-risk hedgers pay for identifying names where priced convexity systematically misstates realized move.
- **scarcity_or_transfer:** Potential accuracy in the residual, not long-straddle direction or option seller profitability.
- **bad_state:** Wrong announcement time, stale surface, corporate action, or post-event quote used in the pre-event estimate.
- **holdability_and_co_losses:** Defined-risk event exposure only in any future economic test; co-loss across correlated sector earnings.
- **execution_net:** Measure fill at real option touch, IV crush, fees, spread, and max loss; report no-fill as cash.
- **decisive_test:** Use time-stamped earnings and pre-event option surface; compare absolute-return forecasts to implied-move-only and historical-event baselines.
- **kill_rule:** Kill if any event clock or pre-event surface is ambiguous or absolute-move skill fails against implied-move/history baselines; charge option costs only in a separate payoff test.
- **source_refs:** ('research/rea_teardowns/targets/optionstrat.md', 'research/rea_teardowns/targets/option-alpha.md', 'research/rea_teardowns/targets/trade-ideas.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
