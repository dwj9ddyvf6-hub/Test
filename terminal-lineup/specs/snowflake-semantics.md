# Snowflake Semantics — Simply Wall St Public Model

Provenance: Adopted 2026-10-28 by the owner's order, evaluation 05-EVALUATION.md section 2 item 12.
Source: Codex review 04-TARGETS-REVIEW.md section 5 (Simply Wall St, lane commit a9d7da2ec3, target +51/-15, FSEM +340, scoped +28 rows, 28 numbered recheck items each with a source link), mining Simply Wall St's public Company Analysis Model.
Licence posture: the model specification is CC BY-NC-SA 4.0. Our terminal is free and non-commercial, which fits the NC term; attribution to Simply Wall St's public Company Analysis Model is required on any surface that uses these semantics, and share-alike applies to adaptations of the specification itself.
Design input for: One-Page Report (tool 67) and The Second Opinion's fundamentals leg (tool 18). This file is a design input, not a claim that either tool yet implements it, and not a claim of production parity with Simply Wall St (production routing/version of the model is, per the review, not independently observable).

## The mined semantics

- **Snowflake shape:** five axes times six binary checks (5x6). The Snowflake is explicitly not a probability.
- **Model selection:** selection among valuation model variants: two-stage FCF, DDM, excess-return, and REIT AFFO variants, chosen per company type.
- **No-estimates fallback:** when no analyst estimates exist, extrapolate from the last estimate at historical average growth.
- **Cost of equity:** from a five-year mean of the 10-year bond rate plus country ERP plus levered beta.
- **Data-latency table:** prices EOD plus up to 6h processing; earnings 1 to 3 days for English, 10 to 22 days for other languages.
- **Portfolio returns:** FIFO for transaction portfolios; returns divided by cumulative capital invested, not time-weighted; 90+ days required for IRR.

## Conflicts preserved (not resolved by fiat, per the source review)

- Plan matrix says 1 saved-screener slot vs the Oct-22 support article's 10/unlimited.
- "120K+ stocks" marketing vs "100k+ companies" in another source.

## Non-claims

- Peer membership and vintage are unknown.
- Charlie AI claims are untested.
- Nothing here is Simply Wall St's production score; it is the published model semantics, mined and sourced.
