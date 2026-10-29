Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE07 - Cross-asset lead-lag graph - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE07; it does not duplicate the shared code.
- **Family:** Cross-asset
- **Target:** follower residual return (target unit: forward_return_fraction)
- **Horizon:** intraday-5 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** EXPERIMENTAL
- **Formula key:** `leadlag` in `catalog.py`; scorer `f_leadlag` in `scorers.py`; edge card `FE07` in `edge_cards.py`

## Inputs

- `leader_return_z` (unit: z, max age 172800s, min quality 0.2)
- `lag_beta` (unit: beta, max age 172800s, min quality 0.2)
- `lag_stability` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))
- `relationship_r2` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_leadlag(x: Mapping[str, float]) -> Signal:
    stability = _clip(x["lag_stability"], 0.0, 1.0)
    r2 = _clip(x["relationship_r2"], 0.0, 1.0)
    score = x["leader_return_z"] * x["lag_beta"] * stability * _clip((r2 - 0.15) / 0.65, 0.0, 1.0)
    return _signed(score, lag_stability=stability, relationship_r2=r2, lag_beta=x["lag_beta"])
```

Catalog formula note: REA synthesis: Cross-asset / leadlag family; vendor report inventory is traceability, not validation.

## Assumptions

- Graph edges must be trained only on prior windows and revalidated; lag_beta is a signed, unbounded regression coefficient.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Rolling fit deterioration, clock mismatch, or relationship sign flip.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE07
- **edge_source:** speed
- **novel_mechanism:** Treat cross-asset links as expiring edges: a leader matters only when its impulse reaches the follower before the follower's own price absorbs it.
- **target_definition:** Follower residual return at the single selected lag endpoint, using a predeclared leader/follower pair.
- **price_aware_baseline:** Follower's own lagged return, common-index return, and a no-edge model.
- **payer_hypothesis:** Hypothesis: slower-market hedgers and cross-market rebalancers transfer information with measurable delay.
- **scarcity_or_transfer:** Speed is only present if lead time exceeds data-arrival, compute, and order latency; public co-movement alone is not access.
- **bad_state:** Clock skew, venue outage, macro release, or a correlation break that reverses the edge.
- **holdability_and_co_losses:** Shared macro/market beta creates co-loss with trend, rates, and crypto sleeves; measure cluster loss.
- **execution_net:** Replay deliberate delays and next-executable marks; include feed latency, spread, market impact, and missed fills.
- **decisive_test:** Freeze one leader/follower pair and lag endpoint; compare follower residual-return loss to follower-only and zero-lag baselines with block-bootstrap uncertainty.
- **kill_rule:** Kill at rolling sign instability, no improvement over follower-only baseline, or edge capture erased by realistic delay.
- **source_refs:** ('research/rea_teardowns/targets/quant-data.md', 'research/rea_teardowns/targets/unusual-whales-original.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
