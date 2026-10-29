Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE03 - Breakout acceptance and survival - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE03; it does not duplicate the shared code.
- **Family:** Price/technical
- **Target:** breakout continuation (target unit: forward_return_fraction)
- **Horizon:** 1-5 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CORE-RESEARCH
- **Formula key:** `breakout` in `catalog.py`; scorer `f_breakout` in `scorers.py`; edge card `FE03` in `edge_cards.py`

## Inputs

- `break_distance_z` (unit: z, max age 172800s, min quality 0.2)
- `acceptance` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))
- `volume_surprise_z` (unit: z, max age 172800s, min quality 0.2)
- `false_break_rate` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_breakout(x: Mapping[str, float]) -> Signal:
    acceptance = _clip(x["acceptance"], 0.0, 1.0)
    false_break = _clip(x["false_break_rate"], 0.0, 1.0)
    volume_confirm = _clip(1.0 + 0.12 * x["volume_surprise_z"], 0.5, 1.5)
    score = x["break_distance_z"] * acceptance * volume_confirm * (1.0 - false_break)
    return _signed(score, acceptance=acceptance, volume_confirm=volume_confirm, false_break_rate=false_break)
```

Catalog formula note: REA synthesis: Price/technical / breakout family; vendor report inventory is traceability, not validation.

## Assumptions

- Break level is defined from data available before the forecast cutoff.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- No executable liquidity, unconfirmed bar, or high false-break rate.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE03
- **edge_source:** accuracy
- **novel_mechanism:** Model acceptance as a dwell-time process: a level is accepted only if price remains beyond it while participation and depth survive.
- **target_definition:** Underlying return from the pre-cutoff breakout reference to the selected fixed session close.
- **price_aware_baseline:** A simple close-above-range rule conditioned on the same symbol's volatility and market direction.
- **payer_hypothesis:** Hypothesis: delayed discretionary entrants pay for evidence that the move has survived its first supply test.
- **scarcity_or_transfer:** Potential accuracy from the sequence after the trigger, not from another indicator label.
- **bad_state:** Thin-market wick, opening gap, scheduled news, or high-volume exhaustion.
- **holdability_and_co_losses:** Measure the adverse excursion before acceptance; overlap with trend, gap, and small-cap warning sleeves.
- **execution_net:** Score next-bar entry, unfilled opportunities, spread, adverse markouts, and capacity by dollar-volume tier.
- **decisive_test:** Freeze the pre-cutoff breakout reference and return endpoint; compare return forecasts to a level-only baseline under matched volatility/session controls. Keep acceptance/failure events separate.
- **kill_rule:** Kill if the return forecast adds no value over the level-only baseline or if apparent skill is confined to an illiquid size tier; score acceptance events separately.
- **source_refs:** ('research/rea_teardowns/targets/saty-ecosystem.md', 'research/rea_teardowns/targets/tradingview-desktop.md', 'research/forecast_engines/CORPUS_AUDIT.md', 'research/forecast_engines/TRACEABILITY.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
