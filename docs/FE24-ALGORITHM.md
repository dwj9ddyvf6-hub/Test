Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE24 - 13F crowding-unwind hazard - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE24; it does not duplicate the shared code.
- **Family:** Ownership
- **Target:** crowded-position unwind risk (target unit: binary_unwind_event)
- **Horizon:** 1-3 quarters
- **Forecast unit:** risk_score_heuristic
- **Score kind:** risk (uncalibrated_risk_rank_only)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `13f` in `catalog.py`; scorer `f_13f` in `scorers.py`; edge card `FE24` in `edge_cards.py`

## Inputs

- `ownership_crowding_z` (unit: z, max age 12960000s, min quality 0.2)
- `fundamental_deterioration_z` (unit: z, max age 7776000s, min quality 0.2)
- `liquidity_stress_z` (unit: z, max age 172800s, min quality 0.2)
- `filing_staleness` (unit: ratio, max age 12960000s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_13f(x: Mapping[str, float]) -> Signal:
    staleness = _clip(x["filing_staleness"], 0.0, 1.0)
    crowding = max(0.0, x["ownership_crowding_z"])
    crowding_freshness = 1.0 - staleness
    logit = (-0.25 + 0.40 * crowding * crowding_freshness
             + 0.40 * max(0.0, x["fundamental_deterioration_z"])
             + 0.35 * max(0.0, x["liquidity_stress_z"]))
    return _risk(logit, staleness=staleness, crowding_freshness=crowding_freshness,
                 crowding_z=x["ownership_crowding_z"],
                 fundamental_deterioration_z=x["fundamental_deterioration_z"])
```

Catalog formula note: REA synthesis: Ownership / 13f family; vendor report inventory is traceability, not validation.

## Assumptions

- 13F is delayed and incomplete; holdings are not current position truth. Filing staleness is an uncertainty haircut on reported crowding, not evidence of an unwind; preserve report-period and filing-availability timestamps.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Filing vintage too stale or position/issuer mapping changes.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE24
- **edge_source:** access
- **novel_mechanism:** Treat 13F as a lagged crowd inventory, not current holdings: forecast forced-unwind vulnerability when stale crowding meets deteriorating fundamentals and poor exit depth.
- **target_definition:** One if the predeclared crowded-position unwind event occurs by the selected quarter end; otherwise zero.
- **price_aware_baseline:** Filing-age baseline, issuer liquidity, own volatility, and known filing-date schedule.
- **payer_hypothesis:** Hypothesis: market makers and liquidity providers price the risk of crowded holders needing to exit.
- **scarcity_or_transfer:** No speed edge for public 13F unless filing processing is faster; value could be risk triage, not prediction.
- **bad_state:** Holdings changed after report date, options/short exposure omitted, issuer mapping error, or crowded exits.
- **holdability_and_co_losses:** Stress gap and depth loss jointly with all ownership and small-cap sleeves; inventory may be unholdable.
- **execution_net:** Any implementation needs realistic borrow/exit depth and no assumption that filing shares remain current.
- **decisive_test:** Replay only from filing availability; test unwind hazard against stale-holdings and liquidity-only baselines.
- **kill_rule:** Kill if stale holdings do not incrementally predict stress or if position ownership is described as current.
- **source_refs:** ('research/rea_teardowns/targets/unusual-whales-original.md', 'research/rea_teardowns/targets/altindex.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
