Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE26 - Index rebalance and basket flow pressure - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE26; it does not duplicate the shared code.
- **Family:** Flows/events
- **Target:** event-window relative return (target unit: forward_return_fraction)
- **Horizon:** 1-10 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `index_flow` in `catalog.py`; scorer `f_index_flow` in `scorers.py`; edge card `FE26` in `edge_cards.py`

## Inputs

- `flow_estimate_z` (unit: z, max age 172800s, min quality 0.2)
- `flow_model_confidence` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))
- `days_to_effective` (unit: days, max age 172800s, min quality 0.2)
- `crowding_z` (unit: z, max age 172800s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_index_flow(x: Mapping[str, float]) -> Signal:
    confidence = _clip(x["flow_model_confidence"], 0.0, 1.0)
    if x["days_to_effective"] < 0.0:
        return _signed(0.0, flow_confidence=confidence, time_weight=0.0,
                       crowding=_clip(x["crowding_z"], 0.0, 4.0), event_passed=1.0)
    days = x["days_to_effective"]
    time_weight = exp(-days / 10.0)
    crowding = _clip(x["crowding_z"], 0.0, 4.0)
    return _signed(x["flow_estimate_z"] * confidence * time_weight / (1.0 + 0.15 * crowding),
                   flow_confidence=confidence, time_weight=time_weight, crowding=crowding, event_passed=0.0)
```

Catalog formula note: REA synthesis: Flows/events / index_flow family; vendor report inventory is traceability, not validation.

## Assumptions

- Separate announced index rules from inferred pre-announcement flow; positive flow_estimate_z means net expected buying. A passed effective date produces a zero score.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Rule change, stale constituent set, or crowded estimate.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE26
- **edge_source:** access
- **novel_mechanism:** Decay an estimated index-flow score by confidence, time to effective date, and crowding; the starter does not separately identify forced and anticipated flow.
- **target_definition:** Constituent return relative to the frozen index benchmark from announcement to the selected effective-date close.
- **price_aware_baseline:** Index return, ordinary volume, known announcement response, no-flow baseline, and announced-flow-only baseline.
- **payer_hypothesis:** Hypothesis: passive funds with fixed benchmark deadlines shed liquidity to earlier, capacity-limited event traders.
- **scarcity_or_transfer:** Access is constrained capacity or timing; widely anticipated rebalance flow is not automatically mispriced.
- **bad_state:** Rule change, stale constituents, crowded front-run, or order-flow estimate already embedded in price.
- **holdability_and_co_losses:** Stress correlated basket holdings and stock-borrow concentration; cross-sleeve loss can be simultaneous.
- **execution_net:** Use basket constituents and real market impact; report missed or cancelled event trades as cash.
- **decisive_test:** Freeze event calendar, flow model, consensus/crowding snapshot, and effective-date close; compare constituent-relative return forecasts with announced-flow-only and no-flow baselines. Score post-effective reversal separately.
- **kill_rule:** Kill if rule revisions, crowding, or actual net flow erase the price effect.
- **source_refs:** ('research/rea_teardowns/targets/trade-ideas.md', 'research/rea_teardowns/targets/finviz-screener.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
