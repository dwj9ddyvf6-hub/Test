Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE01 - Multi-horizon trend persistence - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE01; it does not duplicate the shared code.
- **Family:** Price/technical
- **Target:** forward excess return (target unit: forward_return_fraction)
- **Horizon:** 5-20 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CORE-RESEARCH
- **Formula key:** `trend` in `catalog.py`; scorer `f_trend` in `scorers.py`; edge card `FE01` in `edge_cards.py`

## Inputs

- `ret_21d_z` (unit: z, max age 172800s, min quality 0.2)
- `ret_63d_z` (unit: z, max age 172800s, min quality 0.2)
- `ret_252d_z` (unit: z, max age 172800s, min quality 0.2)
- `trend_efficiency` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))
- `vol_regime` (unit: z, max age 172800s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_trend(x: Mapping[str, float]) -> Signal:
    agreement = 0.45 * x["ret_21d_z"] + 0.35 * x["ret_63d_z"] + 0.20 * x["ret_252d_z"]
    path_quality = _clip(x["trend_efficiency"], 0.0, 1.0)
    vol_damp = 1.0 / (1.0 + 0.20 * abs(x["vol_regime"]))
    return _signed(agreement * (0.35 + 0.65 * path_quality) * vol_damp,
                   horizon_agreement=agreement, path_quality=path_quality, vol_damp=vol_damp)
```

Catalog formula note: REA synthesis: Price/technical / trend family; vendor report inventory is traceability, not validation.

## Assumptions

- Combine non-overlapping horizons; attenuate noisy paths.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Signal disagreement, corporate-action/data break, or volatility shock.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE01
- **edge_source:** accuracy
- **novel_mechanism:** Blend 21-, 63-, and 252-session return orientation, then shrink the signed return score when path efficiency is weak or volatility is elevated.
- **target_definition:** Benchmark-adjusted return from as_of to the selected fixed session close.
- **price_aware_baseline:** Same-name drift, ATR-matched names, and a frozen 21/63/252-day trend rule.
- **payer_hypothesis:** Hypothesis: scheduled allocators and late rebalancers pay for continuation that survives pullbacks.
- **scarcity_or_transfer:** No access edge claimed; value must come from path geometry beyond price trend and realized volatility.
- **bad_state:** Gap reversal, bear-rally failure, or volatility expansion that crosses the invalidation barrier first.
- **holdability_and_co_losses:** Record maximum adverse excursion and time-to-exit; aggregate loss with every trend sleeve.
- **execution_net:** Next-open marks, actual spread/impact at intended size, borrow, fees, and delay capture.
- **decisive_test:** Freeze the benchmark-adjusted return window; issuer-clustered walk-forward against drift and trend baselines. Score first-passage barriers only as a separately named secondary outcome.
- **kill_rule:** Retire if the holdout adds no net decision value over the simple trend baseline or reverses sign.
- **source_refs:** ('research/rea_teardowns/targets/saty-ecosystem.md', 'research/rea_teardowns/targets/trendspider.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
