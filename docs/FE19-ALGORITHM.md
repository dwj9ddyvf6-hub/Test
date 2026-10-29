Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE19 - Consensus revision diffusion - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE19; it does not duplicate the shared code.
- **Family:** Fundamentals
- **Target:** forward residual return (target unit: forward_return_fraction)
- **Horizon:** 20-60 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `revision` in `catalog.py`; scorer `f_revision` in `scorers.py`; edge card `FE19` in `edge_cards.py`

## Inputs

- `revision_momentum_z` (unit: z, max age 172800s, min quality 0.2)
- `analyst_breadth` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))
- `revision_dispersion_z` (unit: z, max age 172800s, min quality 0.2)
- `revision_recency` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_revision(x: Mapping[str, float]) -> Signal:
    breadth = _clip(x["analyst_breadth"], 0.0, 1.0)
    recency = _clip(x["revision_recency"], 0.0, 1.0)
    dispersion_penalty = 1.0 / (1.0 + 0.20 * abs(x["revision_dispersion_z"]))
    return _signed(x["revision_momentum_z"] * breadth * recency * dispersion_penalty,
                   breadth=breadth, recency=recency, dispersion_penalty=dispersion_penalty)
```

Catalog formula note: REA synthesis: Fundamentals / revision family; vendor report inventory is traceability, not validation.

## Assumptions

- Analyst estimates are timestamped and point-in-time; coverage is explicit.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Estimate history is revised/backfilled or analyst panel coverage changes.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE19
- **edge_source:** accuracy
- **novel_mechanism:** Estimate revision breadth as a diffusion process: track analyst-level arrival times, disagreement, and whether revisions precede or merely follow price.
- **target_definition:** Issuer return less the frozen sector/market benchmark from revision availability to the selected fixed session close.
- **price_aware_baseline:** Price momentum, sector drift, and consensus level without revision timing.
- **payer_hypothesis:** Hypothesis: institutional investors with slow committee cycles pay for early and reliable estimate dispersion changes.
- **scarcity_or_transfer:** Potential accuracy requires estimate-vintage access before the price update; consensus snapshots alone are not an access edge.
- **bad_state:** Coverage turnover, stale/backfilled estimates, analyst departure, or price-led revisions.
- **holdability_and_co_losses:** Issuer and sector concentration; group with PEAD and fundamental-quality losses.
- **execution_net:** Next-open or next-session mark with short borrow, spread, turnover, and source subscription cost.
- **decisive_test:** Lock estimates by publication timestamp and compare revision arrival to the price's own response in each era.
- **kill_rule:** Kill if revisions follow price, point-in-time history is unavailable, or net value does not beat price momentum.
- **source_refs:** ('research/rea_teardowns/targets/tipranks.md', 'research/rea_teardowns/targets/quantix.md', 'research/rea_teardowns/targets/tickeron.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
