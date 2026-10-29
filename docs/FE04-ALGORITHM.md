Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE04 - Overnight gap decomposition - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE04; it does not duplicate the shared code.
- **Family:** Price/events
- **Target:** gap continuation vs fade (target unit: forward_return_fraction)
- **Horizon:** intraday-2 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `gap` in `catalog.py`; scorer `f_gap` in `scorers.py`; edge card `FE04` in `edge_cards.py`

## Inputs

- `gap_z` (unit: z, max age 172800s, min quality 0.2)
- `fair_gap_z` (unit: z, max age 172800s, min quality 0.2)
- `open_acceptance` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))
- `premarket_liquidity` (unit: ratio, max age 21600s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_gap(x: Mapping[str, float]) -> Signal:
    residual = x["gap_z"] - x["fair_gap_z"]
    acceptance = _clip(x["open_acceptance"], 0.0, 1.0)
    acceptance_state = 2.0 * acceptance - 1.0
    liquidity = _clip(x["premarket_liquidity"], 0.0, 1.0)
    score = residual * acceptance_state * (0.4 + 0.6 * liquidity)
    return _signed(score, gap_residual_z=residual, open_acceptance=acceptance,
                   acceptance_state=acceptance_state, liquidity=liquidity)
```

Catalog formula note: REA synthesis: Price/events / gap family; vendor report inventory is traceability, not validation.

## Assumptions

- Fair-gap estimate uses only information published by as_of. open_acceptance is bounded [0, 1]: 0 means rejected, 0.5 indeterminate, and 1 accepted; the score fades rejected residual gaps and follows accepted ones.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- News revision, halt, or unresolved daily-open/kicking-open trigger.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE04
- **edge_source:** accuracy
- **novel_mechanism:** Decompose the opening gap into market, sector, after-hours, and issuer residual components, then forecast the residual's auction-to-open resolution path.
- **target_definition:** Opening-gap residual return from the declared open reference to the selected intraday/session endpoint.
- **price_aware_baseline:** Index/sector gap, same-name overnight volatility, and a plain opening-gap reversal baseline.
- **payer_hypothesis:** Hypothesis: overnight risk transfer and scheduled opening orders create a temporary price concession.
- **scarcity_or_transfer:** Potential edge is a correct information decomposition before the first liquid price discovery, not gap size alone.
- **bad_state:** Material news revision, halt, stale premarket quote, or ambiguous session anchor.
- **holdability_and_co_losses:** Bound gap-tail loss and overnight inventory; co-loss with index-flow and event sleeves.
- **execution_net:** Use first executable post-open quote; include auction slippage, spread widening, halts, and no-fill cash.
- **decisive_test:** Pre-register event clocks and gap decomposition; next-open replay with matched index/sector controls.
- **kill_rule:** Retire if the residual fails to beat the market-plus-sector baseline or trigger semantics are unresolved.
- **source_refs:** ('research/rea_teardowns/targets/saty-ecosystem.md', 'research/rea_teardowns/targets/trade-ideas.md', 'research/forecast_engines/CORPUS_AUDIT.md', 'research/forecast_engines/TRACEABILITY.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
