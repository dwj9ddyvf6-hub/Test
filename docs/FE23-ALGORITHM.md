Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE23 - Insider activity adjusted for plan status - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE23; it does not duplicate the shared code.
- **Family:** Ownership/events
- **Target:** forward residual return (target unit: forward_return_fraction)
- **Horizon:** 20-60 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `insider` in `catalog.py`; scorer `f_insider` in `scorers.py`; edge card `FE23` in `edge_cards.py`

## Inputs

- `discretionary_net_flow_z` (unit: z, max age 2592000s, min quality 0.2)
- `non_10b5_1_confidence` (unit: ratio, max age 2592000s, min quality 0.2, range (0.0, 1.0))
- `insider_recency` (unit: ratio, max age 2592000s, min quality 0.2, range (0.0, 1.0))
- `issuer_illiquidity_z` (unit: z, max age 172800s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_insider(x: Mapping[str, float]) -> Signal:
    plan_conf = _clip(x["non_10b5_1_confidence"], 0.0, 1.0)
    recency = _clip(x["insider_recency"], 0.0, 1.0)
    liquidity = 1.0 / (1.0 + max(0.0, x["issuer_illiquidity_z"]) * 0.2)
    return _signed(x["discretionary_net_flow_z"] * plan_conf * recency * liquidity,
                   non_10b5_1_confidence=plan_conf, recency=recency, liquidity_factor=liquidity)
```

Catalog formula note: REA synthesis: Ownership/events / insider family; vendor report inventory is traceability, not validation.

## Assumptions

- Distinguish discretionary transactions, plans, grants, gifts, and tax sales; use filing-availability time rather than transaction time for point-in-time replay. Positive issuer_illiquidity_z means worse exit liquidity and attenuates the flow score.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Transaction coding or filing date is ambiguous.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE23
- **edge_source:** accuracy
- **novel_mechanism:** Estimate insider information content only after separating plan sales, grants, tax withholding, gifts, and discretionary open-market activity.
- **target_definition:** Issuer residual return from filing availability to the selected fixed session close.
- **price_aware_baseline:** Own-price drift, scheduled plan activity, insider role, and base-rate filing effect.
- **payer_hypothesis:** Hypothesis: slower investors pay for correctly classified discretionary conviction and may underweight administrative trades.
- **scarcity_or_transfer:** Public filing access is not scarce; only faster processing or materially better transaction classification could be.
- **bad_state:** Form coding error, late filing, 10b5-1 plan change, clustered selling, or liquidity squeeze.
- **holdability_and_co_losses:** Aggregate insider event risk with filing and PEAD sleeves; measure short-side squeeze.
- **execution_net:** Start from filing availability, not trade date; include next-open spread, borrow, and event gap.
- **decisive_test:** Use time-stamped forms and predeclared transaction taxonomy; score issuer residual return for class-aware versus raw-net-flow models on the same available-at cutoff.
- **kill_rule:** Kill if results depend on transaction dates unavailable at the cutoff or classification precision falls below its pre-set floor.
- **source_refs:** ('research/rea_teardowns/targets/insiderfinance.md', 'research/rea_teardowns/targets/unusual-whales-original.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
