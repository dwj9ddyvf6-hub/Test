# Fifth-pass audit: forecast silence as evidence

**Date:** 2026-10-29
**Silicon base:** origin/main `aad9d2148752a6862ce7a6c44685311aa7310947`
**Feature branch before this pass:** `1b800b3b0c0372476ab4e8e145c2bdf0d3fddc64`
**Scope:** re-audit the 30-engine evaluation and ledger path, the existing REA/sleeve/Femto synthesis, and current primary literature on selective forecasting and coverage. Changes remain in `research/forecast_engines/`.

## The uncovered failure mode

The fourth pass made forecast inputs and model code traceable, and mapped forecast sensitivity to caller-supplied ranges. This pass found that the outcome ledger recorded abstained forecasts but refused to attach an outcome to them. That creates a measurement blind spot: an engine could appear accurate on emitted forecasts while it abstains disproportionately during large moves, bad data conditions, or precisely the regimes where a user most needs a warning. Coverage and error are coupled; counting abstentions without labeling them cannot show what the model excluded.

Selective-prediction research formalizes the accuracy/coverage tradeoff and risk-coverage curve. The new audit takes a market-research view of that problem: it separately measures the realized target distribution during answered and abstained forecast attempts, with labels available only after their publication cutoff. It does not turn abstention into a hidden forecast or add abstention outcomes to forecast-skill scores.

## Implementation

1. `append_abstention_audit_outcome` writes a rights-approved, horizon-complete label for an abstained forecast under the distinct role `abstention_audit`.
2. `append_outcome` remains reserved for emitted forecasts and tags labels `forecast_skill`.
3. Both routes permit one final outcome per forecast ID. The uniqueness check runs inside the same immediate SQLite write transaction, so concurrent labelers cannot attach competing final labels.
4. `coverage_records(as_of)` verifies the ledger hash chain, includes forecast attempts issued by the cutoff, and joins only outcomes whose observation, publication, and ingestion times are ordered and valid at that cutoff. It preserves unlabeled attempts in the denominator and separately surfaces orphaned, invalid, immature, and out-of-scope outcomes.
5. `abstention_coverage_audit` groups by engine, model fingerprint, target, target unit, and horizon. It reports attempt coverage, label coverage, selective coverage among labeled attempts, realized outcomes for answered vs abstained attempts, caller-thresholded tail incidence in the target's own unit, and abstention-reason outcome profiles.
6. The legacy outcome index is backfilled once under a serialized schema migration rather than rescanning the full ledger on every open. The `coverage-audit` CLI reads a ledger and emits a research-only report. All records remain `decision_eligible=false`.

## Reading the output

- `attempt_coverage` is the fraction of recorded attempts that produced a forecast.
- `label_coverage` is the fraction of attempts with a final outcome published by the evaluation cutoff.
- `selective_coverage_on_labeled_attempts` is the answered fraction among attempts whose labels are mature. It may differ from attempt coverage when labels are missing.
- A positive `abstention_minus_forecast_tail_rate` means labeled abstentions coincided with more threshold-sized absolute outcomes in that sample. It does not prove the model predicted those outcomes, establish causal value, or estimate net trading returns.
- Tail thresholds are supplied separately for each target unit. No threshold or outcome distribution is inferred by the tool.
- Abstention-reason profiles may overlap because a single abstention can have several reasons.
- Missing or multiple final labels are reported and excluded from the answered/abstained outcome comparison; the audit never picks the most favorable label.

Example request:

```json
{
  "ledger_path": "data/forecast-ledger.sqlite",
  "evaluation_as_of": "2026-10-29T16:00:00Z",
  "tail_thresholds": {
    "forward_return_fraction": 0.03,
    "binary_large_move_event": 0.5
  }
}
```

Run with `python -m research.forecast_engines.cli coverage-audit path/to/request.json`. To add a label for an abstained attempt, call `ForecastLedger.append_abstention_audit_outcome` only after its declared target horizon is complete and the outcome is rights-cleared.

## Why this changes the research design

Vendor dashboards, backtests, and agent ensembles often emphasize records where a score exists. The existing Silicon/Ausar/Sleeve research also contains explicit avoid, veto, missing-feed, quality-gate, and no-trade states. Those states are part of the forecast mechanism: if they systematically coincide with high realized risk, the abstention policy has measurable value; if they hide difficult cases without detecting them, the validation sample is selected. The new label role makes that difference observable while preserving the forecast/outcome boundary.

The primary selective-prediction literature defines coverage as the fraction of examples on which the system answers and analyzes error among answered cases. This implementation adds an outcome audit of the excluded cases so coverage is paired with the target distribution rather than reported alone. See El-Yaniv and Wiener, [On the Foundations of Noise-free Selective Classification](https://jmlr.org/papers/v11/el-yaniv10a.html), and Gangrade, Kag, and Saligrama, [Selective Classification via One-Sided Prediction](https://proceedings.mlr.press/v130/gangrade21a.html).

## Verification and source boundary

The implementation was checked with temporary SQLite ledgers containing emitted and abstained forecasts: hash-chain verification, cutoff filtering, role separation, coverage and tail summaries, and duplicate-final-label rejection. The catalog's 30 forecasts and 30 boundary maps were also smoke-checked in the prior pass. No live market data or desk connection was used.

The pinned REA and upstream repository inventory remains the one recorded in `CORPUS_AUDIT.md` and `FOURTH_PASS_AUDIT.md`. This pass re-read the local ledger/evaluation implementation and the relevant synthesis/validation records; it did not semantically re-read the 4.19 GB vault streams, all 557 generated locators, every row of all Femto experiment files, or private/sign-in-only vendor surfaces. Those remain explicitly indexed follow-up work, not completed evidence claims.
