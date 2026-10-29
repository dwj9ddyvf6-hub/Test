Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE25 - Executed buyback support - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE25; it does not duplicate the shared code.
- **Family:** Corporate actions
- **Target:** forward issuer residual return after executed buyback activity (target unit: forward_return_fraction)
- **Horizon:** 5-20 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `buyback` in `catalog.py`; scorer `f_buyback` in `scorers.py`; edge card `FE25` in `edge_cards.py`

## Inputs

- `buyback_pace_float_z` (unit: z, max age 15552000s, min quality 0.2)
- `execution_confidence` (unit: ratio, max age 15552000s, min quality 0.2, range (0.0, 1.0))
- `blackout_risk` (unit: ratio, max age 604800s, min quality 0.2, range (0.0, 1.0))
- `liquidity_anomaly_z` (unit: z, max age 172800s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_buyback(x: Mapping[str, float]) -> Signal:
    execution = _clip(x["execution_confidence"], 0.0, 1.0)
    blackout = _clip(x["blackout_risk"], 0.0, 1.0)
    liquidity = 1.0 / (1.0 + 0.15 * abs(x["liquidity_anomaly_z"]))
    return _signed(x["buyback_pace_float_z"] * execution * (1.0 - blackout) * liquidity,
                   execution_confidence=execution, blackout_risk=blackout, liquidity_factor=liquidity)
```

Catalog formula note: REA synthesis: Corporate actions / buyback family; vendor report inventory is traceability, not validation.

## Assumptions

- Measure actual executed pace from reported repurchases; announcements alone are not flow. Preserve reporting-period and filing-availability timestamps. liquidity_anomaly_z is distance from normal liquidity in either direction, so its magnitude attenuates the score.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Pace unavailable, authorization suspended, or issuer report lag unresolved.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE25
- **edge_source:** accuracy
- **novel_mechanism:** Weight reported buyback pace by execution confidence and blackout risk, then damp it when liquidity is anomalous; announcements alone are not executed demand.
- **target_definition:** Issuer residual return from buyback-report availability to the selected fixed session close, conditional on verified executed pace.
- **price_aware_baseline:** Announcement size, issuer volume, own price trend, and no-execution-support baseline.
- **payer_hypothesis:** Hypothesis: issuers transfer a temporary bid to remaining holders while they actually repurchase.
- **scarcity_or_transfer:** Potential edge comes from observed execution pace versus the market's assumed pace.
- **bad_state:** Authorization suspended, blackout, missing reports, or a liquidity/price shock that overwhelms the bid.
- **holdability_and_co_losses:** Concentration in issuer beta and corporate-action risk; co-loss with index and event sleeves.
- **execution_net:** Use report-date timestamps, next-open price, spread, impact, and capacity; compare notional to ADV.
- **decisive_test:** Freeze filings by available_at; compare issuer residual-return forecasts using verified execution pace against announcement-only and price-trend baselines in matched issuers.
- **kill_rule:** Kill if actual pace cannot be observed or does not outperform announcement/price baselines.
- **source_refs:** ('research/rea_teardowns/targets/finviz-screener.md', 'research/rea_teardowns/targets/stock-rover.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
