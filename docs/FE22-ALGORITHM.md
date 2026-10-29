Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE22 - Filing and guidance semantic delta - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE22; it does not duplicate the shared code.
- **Family:** Fundamentals/NLP
- **Target:** disclosure inflection (target unit: disclosure_delta_z)
- **Horizon:** 1-4 quarters
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `filing_nlp` in `catalog.py`; scorer `f_filing_nlp` in `scorers.py`; edge card `FE22` in `edge_cards.py`

## Inputs

- `semantic_delta_z` (unit: z, max age 15552000s, min quality 0.2)
- `parser_confidence` (unit: ratio, max age 15552000s, min quality 0.2, range (0.0, 1.0))
- `novelty_score` (unit: ratio, max age 15552000s, min quality 0.2, range (0.0, 1.0))
- `section_relevance` (unit: ratio, max age 15552000s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_filing_nlp(x: Mapping[str, float]) -> Signal:
    parser = _clip(x["parser_confidence"], 0.0, 1.0)
    novelty = _clip(x["novelty_score"], 0.0, 1.0)
    relevance = _clip(x["section_relevance"], 0.0, 1.0)
    return _signed(x["semantic_delta_z"] * parser * novelty * relevance,
                   parser_confidence=parser, novelty=novelty, relevance=relevance)
```

Catalog formula note: REA synthesis: Fundamentals/NLP / filing_nlp family; vendor report inventory is traceability, not validation.

## Assumptions

- Compare same document sections/types and preserve parser/model version and filing-availability timestamps.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Low parser confidence, document type mismatch, or model drift.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE22
- **edge_source:** accuracy
- **novel_mechanism:** Score same-section disclosure change only after multiplying by parser confidence, novelty, and section relevance; numeric contradiction is not yet an input.
- **target_definition:** Parser-normalized disclosure delta in the same predeclared filing section/type at the next comparable filing.
- **price_aware_baseline:** Prior same-section text, XBRL numeric changes, and an unchanged-boilerplate baseline.
- **payer_hypothesis:** Hypothesis: analysts pay for a reliable reconciliation of long filings before consensus catches up.
- **scarcity_or_transfer:** Potential accuracy from semantic-to-numeric disagreement and time saved; generic NLP sentiment is not an edge.
- **bad_state:** Parser drift, document-type mismatch, OCR error, boilerplate, or language-model memorization.
- **holdability_and_co_losses:** Co-loss with XBRL, revisions, and PEAD at the same issuer; cluster by filing event.
- **execution_net:** Subtract data/parser operations and, for any trade test, real liquidity and next-open costs.
- **decisive_test:** Blind parser versions to the outcome; compare to filing-count and simple numeric-delta baselines.
- **kill_rule:** Kill if parser quality, section alignment, or same-vintage replication fails.
- **source_refs:** ('research/rea_teardowns/targets/quantix.md', 'research/rea_teardowns/targets/danelfin.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
