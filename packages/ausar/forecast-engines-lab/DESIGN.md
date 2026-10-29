# Design notes and evidence contract

## Forecast record

One record represents one named hypothesis for one symbol, cutoff, and horizon. It preserves the feature values and source metadata used at issuance. A valid forecast records a scalar output and its unit, the future target and its distinct target unit, a model score, named drivers, evidence trace, and a separate input-quality summary. Schema 1.6 also labels the meaning of its direction field: signed engines report positive/negative/zero *score orientation*; risk engines report `RISK_RANK_ONLY`; continuous point forecasts are not directional. An invalid or unsupported computation records `status=abstain`, `direction=ABSTAIN`, and reason codes.

These labels do not claim a calibrated return sign or event probability. Risk models retain their continuous monotone score for ranking but receive no binary high/low label because no operating threshold has been selected on held-out outcomes. The signed-score deadband was removed because one fixed magnitude threshold had no common unit across engines. Output values and target units remain separate.

The record intentionally has no fields for an order, position, target weight, broker, execution venue, or stop. The forecast layer is not an execution system. Outcome events must be appended only after the target horizon is complete; intermediate marks are not final labels.

## Provenance at three levels

A source hash identifies the upstream record. A feature transform ID/hash identifies the code or rule that produced a derived input. A model fingerprint binds the engine spec, validators, scoring, Edge-card code, target-contract code, label-context code, and Python runtime. A separate target-contract fingerprint binds the primary label text, unit, and allowed windows. For an evaluable forecast, the request freezes one allowed window ID, exact UTC start/end, the expected label-transform ID/hash, and a canonical label context with series, measurement basis, calendar, reference series, data-vintage policy, and corporate-action policy. These identities answer different questions and are not interchangeable. Inputs marked inferred or reproduced must include transform provenance or the engine abstains.

The model and target fingerprints identify registered code and label semantics. The label-context fingerprint verifies that declared measurement conventions stayed unchanged; it does not prove a source followed those conventions. The label-transform hash is a caller attestation; it does not prove that the named code produced the supplied value. None of these hashes proves that source data are correct, that a vendor license permits use, or that a forecast is calibrated.

## Availability and revisions

`observed_at` is when the underlying observation applies; `available_at` is when the upstream source made it public/available; `ingested_at` is when the local pipeline received it. All must be at or before `as_of`. A corrected value is a new observation with a new availability timestamp and hash. Never replace the value that an old forecast consumed. This is essential for macro releases, estimates, filings, COT schedules, and corrected market data.

The emitted feature manifest keeps three separate clocks: `age_seconds` since the observation applies, `available_age_seconds` since the source published it, and `publication_lag_seconds` between those times. Slow reports need cadence-appropriate maximum ages, while `available_at` still gates whether the value could have been known. A schedule change is versioned by its effective date; an announcement alone does not change the historical or live schedule.

## Evidence labels

- `observed`: directly observed source record, still subject to feed quality and rights.
- `published`: statement or value published by a source; it is not independently verified.
- `reproduced`: locally recomputed from identified input artifacts and a versioned rule.
- `inferred`: model assumption, latent-label estimate, or indirect proxy.

The engine does not convert one evidence class into another. FE15 and several alternative-data features should be treated as inferred unless a direct source supports them. A source group is recorded for dependence review; correlated measures from the same OHLC tape do not count as independent votes.

The forecast records the Herfindahl concentration of accepted input features across caller-declared independence groups and its reciprocal (`declared_source_group_concentration`, `effective_declared_source_groups`). These are diagnostics about the supplied labels, not proof of statistical independence; they do not change a score or make a forecast decision-eligible.

`rights_approved` is an explicit caller attestation for the intended model use. The software cannot determine vendor contract rights. A public endpoint is not automatic permission to use, retain, redistribute, or train on its data.

## Novelty and boundaries

The designs extend the REA's vendor feature patterns into forward-looking *targets* rather than copying branded scores: price state → persistence/reversion; flow and options → conditional pressure/tail scenarios; company/event data → surprise/drift; portfolio context → transition risk. Novel combinations include:

- treating breadth as cross-sectional *participation* in an index move, not another correlated oscillator;
- modeling lower-timeframe leaders and follower residuals only when the edge remains stable across prior windows;
- separating the risk-neutral left tail from physical move forecasts;
- treating options flow and dealer gamma as conditional, assumption-bearing evidence;
- using actual data availability, panel drift, and filing-vintage controls as part of the forecast inputs, not as afterthoughts;
- forecasting abstention, fragility, and regime transition as first-class outputs.

These are architecture and hypothesis contributions. No claim is made that the combinations are unprecedented in the literature or predictively successful.

## Boundary-map interpretation

The boundary-map diagnostic starts from a valid baseline forecast and accepts only explicit feature ranges in catalog units. It samples each one-dimensional path, measures pairwise difference-in-differences with all other features held at baseline, and evaluates all corners of the caller-supplied hyperrectangle. The first sampled direction change is conditional on that path and resolution. Pairwise interactions are score geometry, not causal effects. Corner counts have no probability interpretation, and higher-order interior interactions are not exhaustively enumerated. No feature range is estimated from outcomes inside this tool.

## Abstention is a measurable state

Every forecast attempt—including an abstention—stays in the append-only ledger. A completed, rights-approved target label may be attached to an abstention only through the separate `abstention_audit` role. Those labels measure the outcomes hidden by the coverage gate; they are not forecast-skill examples. Each forecast ID accepts one final outcome. Current outcomes must match the frozen target contract, exact window start/end, expected label-transform hash, and label-context fingerprint; scenario-only contracts cannot receive realized-return labels. Legacy rows remain explicitly unbound. Audits exclude missing, immature, mismatched, or ambiguous labels and keep distinct target-contract/window/transform/context variants separate.

## Maturity meaning

- `CORE-RESEARCH`: can be evaluated with routinely available point-in-time data, but still has no edge certification here.
- `CONDITIONAL-DATA`: requires specific entitled, historical, or event data; default output should abstain when unavailable.
- `EXPERIMENTAL`: novel or especially assumption-sensitive; retain as a research question and require stronger independent validation.
