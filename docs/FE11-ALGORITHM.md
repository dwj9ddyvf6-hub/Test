Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE11 - Closing-auction imbalance pressure - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE11; it does not duplicate the shared code.
- **Family:** Microstructure
- **Target:** close-to-next-open pressure (target unit: forward_return_fraction)
- **Horizon:** closing auction
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `auction` in `catalog.py`; scorer `f_auction` in `scorers.py`; edge card `FE11` in `edge_cards.py`

## Inputs

- `auction_imbalance_z` (unit: z, max age 60s, min quality 0.2)
- `auction_imbalance_reliability` (unit: ratio, max age 60s, min quality 0.2, range (0.0, 1.0))
- `close_depth_z` (unit: z, max age 60s, min quality 0.2)
- `index_rebalance_flow_z` (unit: z, max age 3600s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_auction(x: Mapping[str, float]) -> Signal:
    reliability = _clip(x["auction_imbalance_reliability"], 0.0, 1.0)
    depth_damp = 1.0 / (1.0 + max(0.0, x["close_depth_z"]) * 0.20)
    score = (x["auction_imbalance_z"] + 0.20 * x["index_rebalance_flow_z"]) * reliability * depth_damp
    return _signed(score, imbalance_reliability=reliability, depth_damp=depth_damp)
```

Catalog formula note: REA synthesis: Microstructure / auction family; vendor report inventory is traceability, not validation.

## Assumptions

- Requires entitled exchange auction data with actual timestamps; positive imbalance and rebalance flow mean net buying, and positive score means a higher next-open return relative to the auction close.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Auction feed gap, stale imbalance, or venue-specific rules change.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE11
- **edge_source:** speed
- **novel_mechanism:** Orient the close-to-next-open score with auction imbalance and rebalance flow, then shrink it for unreliable imbalance data or unusually deep closing liquidity.
- **target_definition:** Close-to-next-open return for the declared instrument and venue session.
- **price_aware_baseline:** Closing price, prior auction imbalance, index-flow calendar, and simple close-to-open drift.
- **payer_hypothesis:** Hypothesis: benchmark funds with fixed closing deadlines transfer a temporary liquidity premium.
- **scarcity_or_transfer:** The imbalance snapshot must arrive before the venue cutoff; this scorer uses a snapshot and does not estimate revision velocity.
- **bad_state:** Auction imbalance cancellation, venue-specific rule change, stale feed, or index rebalance.
- **holdability_and_co_losses:** Inventory is overnight and can gap; aggregate with index flow and gap exposure.
- **execution_net:** Auction order type, queue priority, imbalance cutoff, partial fill, and next-open exit all enter net value.
- **decisive_test:** Use entitled timestamped auction data; compare next-open return error for the weighted imbalance/rebalance score against an imbalance-only baseline at the actual decision cutoff.
- **kill_rule:** Kill if late-arriving data, adverse auction fills, or realistic cutoffs erase incremental value.
- **source_refs:** ('research/rea_teardowns/targets/trade-ideas.md', 'research/rea_teardowns/targets/quant-data.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
