Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE18 - Post-earnings drift after controls - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE18; it does not duplicate the shared code.
- **Family:** Events/fundamentals
- **Target:** sector-adjusted drift (target unit: forward_return_fraction)
- **Horizon:** 5-20 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CORE-RESEARCH
- **Formula key:** `pead` in `catalog.py`; scorer `f_pead` in `scorers.py`; edge card `FE18` in `edge_cards.py`

## Inputs

- `standardized_surprise_z` (unit: z, max age 172800s, min quality 0.2)
- `revision_breadth` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))
- `post_event_drift_z` (unit: z, max age 172800s, min quality 0.2)
- `sector_residual_z` (unit: z, max age 172800s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_pead(x: Mapping[str, float]) -> Signal:
    persistence = _clip(x["revision_breadth"], 0.0, 1.0)
    score = (0.50 * x["standardized_surprise_z"] + 0.30 * x["post_event_drift_z"] + 0.20 * x["sector_residual_z"]) * (0.5 + 0.5 * persistence)
    return _signed(score, revision_breadth=persistence, surprise_z=x["standardized_surprise_z"])
```

Catalog formula note: REA synthesis: Events/fundamentals / pead family; vendor report inventory is traceability, not validation.

## Assumptions

- Surprise and consensus vintages are locked as available before release.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Restatement, stale consensus, confounded event, or reversal kill condition.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE18
- **edge_source:** accuracy
- **novel_mechanism:** Separate the announcement jump from post-event drift, then ask if revisions and price response disagree after sector and own-volatility controls.
- **target_definition:** Sector-residual return from the first executable post-release open to the selected fixed session close.
- **price_aware_baseline:** Price reaction, sector return, own volatility, and simple standardized surprise.
- **payer_hypothesis:** Hypothesis: slow analysts and mandate-constrained institutions under-adjust to a material earnings surprise.
- **scarcity_or_transfer:** Potential accuracy from delayed belief updating only after price-aware and event-time controls.
- **bad_state:** Restatement, confounded event, one-time special item, or initial price reaction already exhausts drift.
- **holdability_and_co_losses:** Sector overlap and short-side squeezes create co-loss with revisions and factor sleeves.
- **execution_net:** Next-open entry, spread, turnover, borrow, and overnight gaps; compare per opportunity, not filled trade only.
- **decisive_test:** Freeze surprise vintage and event cohort; use issuer-clustered walk-forward and an untouched era.
- **kill_rule:** Kill if post-event drift is not incremental to price reaction and sector/volatility controls.
- **source_refs:** ('research/rea_teardowns/targets/danelfin.md', 'research/rea_teardowns/targets/quantix.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
