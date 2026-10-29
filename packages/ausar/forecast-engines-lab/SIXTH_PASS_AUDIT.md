# Sixth-pass audit: forecast horizon geometry

**Date:** 2026-10-29
**Silicon base:** origin/main `aad9d2148752a6862ce7a6c44685311aa7310947`
**Feature branch before this pass:** `600d99e69835f89a2691bf6cdfa4eaae6d151874`
**Scope:** re-audit the FE01–FE30 forecast evidence design, the unresolved dependence item in the corpus audit, and primary research on forecast comparison with serially correlated errors and overlapping forecast intervals. Changes remain in `research/forecast_engines/`.

## The overlooked experimental unit

The fifth pass made every abstention outcome labelable, but its coverage comparison still counted forecast attempts as rows. A row is not necessarily a new market experiment. If a system emits a forecast every day for a 20-session target, the next nineteen rows can reuse most of the first row's future price path. Treating those as nineteen independent confirmations makes the evidence appear denser than the underlying information.

This is present in the local research itself: the open-experiment list calls for estimating conditional error dependence and horizon decay from matured pairs, while multiple FE cards explicitly require issuer clustering, non-overlapping horizons, or block-bootstrap uncertainty. Those constraints were in the prose but had no ledger diagnostic to show how much the actual labels overlap.

Diebold and Mariano allow forecast-loss differences to be serially and contemporaneously correlated; Hansen and Hodrick analyze inference when the sampling interval is shorter than the forecast interval. These papers motivate dependence-aware evaluation. This pass does not implement either paper's inference procedure.

## New horizon-geometry diagnostic

`horizon_overlap.py` constructs each observed target window as `[forecast.as_of, outcome.observed_at]` after checking the final label's role, rights, unit, timestamp order, cutoff, and source hash. It reports, by engine fingerprint, target, unit, and horizon:

- same-symbol overlapping window pairs and the share of possible same-symbol pairs that overlap;
- maximum number of concurrent labels and largest connected overlap component;
- the maximum non-overlapping interval set within each symbol, summed across symbols, as a design anchor;
- exact-cutoff cross-symbol pairs as a marker for shared forecast cohorts and possible common shocks;
- missing, ambiguous, and invalid labels, kept separate from usable intervals.

The CLI command is `python -m research.forecast_engines.cli horizon-overlap path/to/request.json`; the request contains `ledger_path` and `evaluation_as_of`. The tool reads the same verified, cutoff-filtered ledger view as `coverage-audit`.

## Interpretation boundary

The interval graph measures shared target-path exposure. It does not estimate serial correlation in forecast losses, cross-symbol residual dependence, an effective sample size, standard errors, p-values, predictive accuracy, or trading returns. Exact-cutoff co-occurrence flags candidate shared-shock clusters; it does not prove that a shock caused dependence. The non-overlap count helps choose blocked splits and embargoes before outcomes are analyzed, but it must not be used as a replacement sample size in a significance test.

Next empirical step: freeze one target and label endpoint per engine family, run the overlap audit on the licensed, rights-cleared matured ledger, then estimate paired loss dependence on untouched blocks with a method whose assumptions match the realized dependence. Keep repeated parameter variants inside one declared search family.

## Verification and source boundary

Focused checks covered interval arithmetic (overlap, touching/non-overlap, concurrent windows, connected components, and greedy maximum non-overlap), valid/invalid/missing labels, cutoff handling, JSON CLI output, all 30 catalog entries, and Edge-card source validation. No market outcomes or broker connections were used.

The prior corpus audits remain the source-by-source record for Silicon REA, the 6,315-file teardown tree, Femto research/desk branches, vendor repositories, supplied sleeves, Ausar, and TheStrat. This pass sharpens the evaluation unit in FE01–FE30; it does not rewrite upstream indexes or claim that all raw vault bytes or experimental CSV rows were manually read. The existing inventory records the raw-vault and generated-locator semantic-review boundaries.

Primary research:

- Diebold and Mariano, [Comparing Predictive Accuracy](https://doi.org/10.1080/07350015.1995.10524599).
- Hansen and Hodrick, [Forward Exchange Rates as Optimal Predictors of Future Spot Rates](https://www.journals.uchicago.edu/doi/pdf/10.1086/260910).
