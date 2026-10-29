Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE09 - Jump and overnight-tail hazard - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE09; it does not duplicate the shared code.
- **Family:** Volatility
- **Target:** large-move event risk (target unit: binary_large_move_event)
- **Horizon:** 1-5 sessions
- **Forecast unit:** risk_score_heuristic
- **Score kind:** risk (uncalibrated_risk_rank_only)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `tail` in `catalog.py`; scorer `f_tail` in `scorers.py`; edge card `FE09` in `edge_cards.py`

## Inputs

- `jump_intensity_z` (unit: z, max age 172800s, min quality 0.2)
- `overnight_gap_z` (unit: z, max age 172800s, min quality 0.2)
- `left_tail_asymmetry_z` (unit: z, max age 172800s, min quality 0.2)
- `event_density` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_tail(x: Mapping[str, float]) -> Signal:
    risk = _risk(-0.15 + 0.48 * x["jump_intensity_z"] + 0.36 * abs(x["overnight_gap_z"]) + 0.30 * x["left_tail_asymmetry_z"] + 0.45 * _clip(x["event_density"], 0.0, 1.0),
                 jump_intensity_z=x["jump_intensity_z"], overnight_gap_z=abs(x["overnight_gap_z"]), event_density=x["event_density"])
    return risk
```

Catalog formula note: REA synthesis: Volatility / tail family; vendor report inventory is traceability, not validation.

## Assumptions

- Score is a ranking heuristic until event labels are calibrated OOS.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Corporate action/event calendar missing or tail labels leak future data.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE09
- **edge_source:** accuracy
- **novel_mechanism:** Rank large-move risk from jump intensity, absolute overnight gap, left-tail asymmetry, and event density; the starter score does not separate event causes.
- **target_definition:** One if absolute return exceeds the predeclared volatility-scaled barrier by the selected window end; otherwise zero.
- **price_aware_baseline:** Same-name overnight gap history, realized-volatility hazard, and event-calendar base rates.
- **payer_hypothesis:** Hypothesis: protection buyers and overnight inventory holders pay to identify concentrated jump windows.
- **scarcity_or_transfer:** Value is lower tail forecast error or avoided loss beyond the known event schedule, not high AUC alone.
- **bad_state:** Unannounced news, halt, event-time error, and fat-tail clustering.
- **holdability_and_co_losses:** Stress overnight liquidation and cross-sleeve gap co-loss; cash/margin must survive the gap.
- **execution_net:** Score actual next-open liquidation values with wide spreads, halted-name marks, and hedge basis.
- **decisive_test:** Lock the absolute-return barrier and window before cutoff; compare binary event scores to HAR and public-calendar base-rate hazards. Keep cause-specific jump labels separate.
- **kill_rule:** Kill if no calibrated tail-loss reduction versus baseline or labels leak post-event timing.
- **source_refs:** ('research/rea_teardowns/targets/optionstrat.md', 'research/rea_teardowns/targets/squeezemetrics.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
