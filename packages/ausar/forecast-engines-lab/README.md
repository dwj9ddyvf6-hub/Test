# Forecast Engines Lab — 30 Research Hypotheses

**Status:** research-only implementation, version `0.9.2-hypothesis`
**Runtime:** Python standard library, Python 3.10+
**Scope:** point-in-time forecasts, uncertainty-aware risk scores, abstentions, and forecast evaluation. This package does not connect to Silicon's terminal, Morgue Engine, Ausar Desk, Alpaca, or any other broker/order system.

The source reconciliation and successive design passes are recorded in [CORPUS_AUDIT.md](CORPUS_AUDIT.md), [SECOND_PASS_AUDIT.md](SECOND_PASS_AUDIT.md), [THIRD_PASS_AUDIT.md](THIRD_PASS_AUDIT.md), [FOURTH_PASS_AUDIT.md](FOURTH_PASS_AUDIT.md), [FIFTH_PASS_AUDIT.md](FIFTH_PASS_AUDIT.md), [SIXTH_PASS_AUDIT.md](SIXTH_PASS_AUDIT.md), [SEVENTH_PASS_AUDIT.md](SEVENTH_PASS_AUDIT.md), [EIGHTH_PASS_AUDIT.md](EIGHTH_PASS_AUDIT.md), [NINTH_PASS_AUDIT.md](NINTH_PASS_AUDIT.md), [TENTH_PASS_PRECISION.md](TENTH_PASS_PRECISION.md), and this [semantic audit](SEMANTIC_AUDIT.md). [TRACEABILITY.md](TRACEABILITY.md) maps engine families to Silicon research; [SOURCES.md](SOURCES.md) links the primary source material.

The REA corpus describes many scanners, ranking models, flow products, options surfaces, event systems, and risk workflows. Those products are useful design evidence; their vendor claims do not establish predictive validity. This package combines those motifs into 30 explicit forecast hypotheses and adds a forecast/outcome evidence loop. It deliberately does not implement 30 “profitable strategies.” The coefficients in `scorers.py` are transparent starter transforms, not learned parameters, not production settings, and not evidence of an edge.

## The 30 engines

| ID | Forecast engine | Target and horizon | Status |
|---|---|---|---|
| FE01 | Multi-horizon trend persistence | Forward excess return, 5–20 sessions | Core research |
| FE02 | Regime-gated residual reversion | Residual return, 1–5 sessions | Core research |
| FE03 | Breakout acceptance and survival | Underlying return after a pre-cutoff level, 1–5 sessions | Core research |
| FE04 | Overnight gap decomposition | Opening-gap residual return, intraday–next session | Conditional data |
| FE05 | Breadth participation impulse | Index return relative to a fixed benchmark, 1–5 sessions | Core research |
| FE06 | Sector leadership diffusion | Relative sector return, 5–20 sessions | Core research |
| FE07 | Cross-asset lead-lag graph | Follower residual return, intraday–5 sessions | Experimental |
| FE08 | HAR-style realized-volatility forecast | Realized variance, 1–5 sessions | Core research |
| FE09 | Jump and overnight-tail hazard | Absolute-return barrier event, 1–5 sessions | Conditional data |
| FE10 | Volatility/correlation regime transition | Binary regime-transition event, 5–20 sessions | Experimental |
| FE11 | Closing-auction imbalance pressure | Close-to-next-open return | Conditional data |
| FE12 | Liquidity fragility / halt hazard | Persistent liquidity deterioration event, intraday–1 session | Conditional data |
| FE13 | Order-flow-imbalance adverse selection | Midquote return after flow, seconds–30 minutes | Conditional data |
| FE14 | Options-implied downside tail state | Physical left-tail barrier event, 1–20 sessions | Conditional data |
| FE15 | Dealer-gamma scenario map | Conditional scenario sensitivity; no realized-return label | Experimental |
| FE16 | Options-flow response with intent uncertainty | Conditional underlying residual return, intraday–5 sessions | Experimental |
| FE17 | Earnings absolute-move forecast | Absolute event return through next-session close | Conditional data |
| FE18 | Post-earnings drift after controls | Sector-adjusted drift, 5–20 sessions | Core research |
| FE19 | Consensus revision diffusion | Forward residual return, 20–60 sessions | Conditional data |
| FE20 | Alternative-data nowcast with panel drift | Next-period fundamental surprise, 1–3 months | Experimental |
| FE21 | XBRL cash-conversion inflection | Change in cash-conversion measure, next comparable filing | Conditional data |
| FE22 | Filing/guidance semantic delta | Section-matched disclosure delta, next comparable filing | Conditional data |
| FE23 | Insider activity adjusted for plan status | Forward residual return, 20–60 sessions | Conditional data |
| FE24 | 13F crowding-unwind hazard | Binary crowded-position unwind event, 1–3 quarters | Conditional data |
| FE25 | Executed buyback support | Issuer residual return after reported executed pace, 5–20 sessions | Conditional data |
| FE26 | Index rebalance/basket flow pressure | Constituent return relative to frozen index, through effective date | Conditional data |
| FE27 | Macro surprise reaction by data vintage | Cross-asset return at 30 minutes post-release | Conditional data |
| FE28 | Yield-curve/credit regime transition | Binary market-stress transition, 1–4 quarters | Core research |
| FE29 | Commodity positioning/inventory/supply shock | Commodity excess return, 1–8 weeks | Conditional data |
| FE30 | Crypto liquidity/crowding squeeze risk | Venue-specific liquidation/depth event, intraday–5 sessions | Conditional data |

The status labels describe research/data readiness only. They are not performance grades. Options OPRA, exchange auction/depth, alternative-data, ownership, and crypto venue coverage remain entitlement- and source-dependent. The package has no data connector and will not circumvent feed rights.

The third pass adds one detailed Edge hypothesis card per engine in `edge_cards.py`. Each card declares the mechanism, exact outcome, price-aware baseline, hypothesized payer, scarcity/transfer, bad state, holdability and co-losses, execution net, decisive test, kill rule, and source references. `HYPOTHESIS` is the only allowed card status until evidence is reviewed.

## Fourth-pass provenance and fragility tools

The fourth pass closes a reproducibility gap between raw-source hashes and executable forecasts. Forecast records now carry a model fingerprint over the engine spec, validation/scoring and Edge-card code, and Python runtime. Each feature can carry its own transform ID/hash; inferred and reproduced inputs abstain if that transform lineage is missing. The boundary-map command performs caller-bounded one-feature, pairwise-interaction, and joint-corner stress analysis for any of the 30 engines without inventing probabilities.

The fifth pass makes abstention outcomes observable. `append_abstention_audit_outcome` records a mature target label under a separate audit role, and `coverage-audit` compares outcome coverage and tail incidence for answered versus abstained attempts. Those labels never enter forecast-skill metrics. Each attempt accepts at most one final outcome; labels must have ordered observation/publication/ingestion times, cutoff-valid source provenance, and a complete target horizon.

The sixth pass measures target-window dependence. `horizon-overlap` builds actual frozen target-window intervals (with a legacy `[forecast as_of, outcome observed_at]` fallback), counts overlapping windows within each symbol, finds the largest connected overlap component and maximum non-overlapping window set, and reports exact-cutoff cross-symbol cohorts. These are geometric dependence warnings, not corrected standard errors or effective sample sizes.

## Full-code audit repairs

The next audit pass closed a historical-cutoff leak: ledger snapshots now require the forecast/outcome event itself to have been written by the requested cutoff, in addition to checking claimed issue, publication, and ingestion times. The verified read path rejects malformed legacy labels (including missing rights attestation, incomplete horizons, wrong units/roles, invalid values, and bad source hashes) and excludes malformed forecast envelopes. Target-provenance reports independently recheck label validity and cutoff availability. Numerical scorer failures now become explicit forecast abstentions, and non-directional diagnostics reject malformed score records. Numeric diagnostics also reject booleans masquerading as labels or measurements.

## Why this architecture is different from the current desk tools

The eighth pass freezes instance-level label conventions—series, measurement basis, calendar, reference series, vintage policy, and corporate-action policy—so equal target names cannot silently pool unlike outcomes. Its content hash is checked by the ledger and included in evaluation groups. See [EIGHTH_PASS_AUDIT.md](EIGHTH_PASS_AUDIT.md).

Silicon's Convergence Engine already specifies 20 product kernels (S01–S20), including current-state snapshots, price/volatility state, factor matrices, options activity normalization, a static dealer-exposure map, replay, risk/action gating, and evidence provenance. FE01–FE30 add explicit future targets and a forecast outcome record; they do not replace those kernels or claim that a dashboard score predicts a return. See [traceability](TRACEABILITY.md).

The cross-branch research materially constrains what is worth trying:

- The Femto forecast searches produced candidates but no Grade-A independently replicated edge; multiple-testing, cost, walk-forward, and holdout gates removed many apparent winners. Some forecast sets were dominated by avoid/veto outputs.
- The visual/price research found a stronger and more consistent *risk/avoid* direction than a general stock-picking buy edge; some attractive gross momentum effects reversed by regime or after costs.
- The Gestalt work found model-error improvements that did not beat simple baselines after cost/validation controls. The desk's existing records also flag missing option quotes and crossing costs.
- Saty and TheStrat materials supply candidate rule shapes, not a complete profitable trade sample. TheStrat's gap trigger references conflict in places; Saty's public research explicitly separates descriptive market context from a calibrated return forecast.

These findings motivate risk, regime, event, and data-quality forecasts alongside signed-return hypotheses. They do not justify a “maximal profit” promise.

## Data contract and abstention

Each required feature is a `FeatureObservation` containing a numeric value and unit, observation/publication/ingestion times, source ID, SHA-256 data hash, evidence kind, independent-source group, quality score, and explicit use-rights approval. Derived inferred or reproduced features also require a transform ID and SHA-256 transform hash. Cataloged `ratio` inputs are constrained to `[0, 1]`; `signed_ratio` inputs are constrained to `[-1, 1]`; regression `beta` inputs are signed and unbounded. Out-of-range values abstain instead of being silently clipped into a plausible confidence score. Forecast records carry a model fingerprint and a separate target-contract fingerprint. The target contract pins the primary label definition and allowed window IDs; each forecast can freeze one window ID, exact start/end times, label-transform ID/hash, and a label-context fingerprint before its outcome exists. The context identifies the series, measurement basis, calendar, reference series, data-vintage policy, and corporate-action policy. The outcome must repeat that fingerprint, and audits keep unlike measurement contexts separate. For historical replay, all input timestamps must be at or before the requested `as_of`; otherwise the engine abstains. Missing values are not zero. Missing/stale/future data, rights not approved, unknown evidence kind, unit/range mismatch, weak quality, or absent provenance causes an explicit abstention with reasons.

The record keeps `forecast_unit` separate from `target_unit`: for example, a signed score can forecast a future return without pretending to estimate return magnitude. `direction_semantics` makes that distinction machine-readable. Signed direction values report score sign only; risk outputs carry `RISK_RANK_ONLY` and remain continuous heuristic ranks without a high/low cutoff. `input_quality_score` summarizes source quality, freshness, and an inference haircut. It is not model confidence, a probability, or a performance estimate. `calibrated_probability` is always `null` in this release. Risk outputs are labeled heuristics, not probabilities. `decision_eligible` is hard-coded false. `model_score` is an interpretable score; no coefficient has been estimated from future outcomes.

## Second-pass data and provenance refinements

Each feature record now exposes measurement age, publication age, and the lag from observation to publication separately. The engine also reports the Herfindahl concentration of valid features across caller-declared source-independence groups and the corresponding effective group count. Those fields reveal when several features depend on one declared source family; the labels are not verified independence claims and do not alter the forecast score.

Input maximum ages now reflect slower source families: alternative-data panels, quarterly filing features, 13F holdings, reported buyback pace, macro composites, and weekly COT/inventory inputs no longer inherit a two-day freshness cap. Their original observation, publication, and ingestion timestamps remain mandatory, so a longer cap never makes a not-yet-published value available. Source-specific schedules still need to be supplied by a licensed, dated connector. For COT, apply the schedule effective on that date; the CFTC's October 27, 2026 announcement describes a planned move to twice-weekly reports by year-end, not evidence that the new schedule is already live.

These are data-contract and observability improvements. They do not create a learned forecastability gate: there is no source-complete, strictly forward outcome panel here from which to estimate a model-error or abstention meta-model.

For vendor-derived options data:

- Open interest is matched long and short contracts; it does not identify the dealer's side.
- A flow print alone does not prove opening intent, buyer/seller initiation, or future direction.
- A risk-neutral option surface is not the physical distribution of future returns.
- FE15 is a scenario map whose sign is an assumption, not observed dealer positioning.

## Use

From the repository root:

```bash
python -m research.forecast_engines.cli list
python -m research.forecast_engines.cli forecast path/to/point_in_time_request.json
python -m research.forecast_engines.cli edge-ledger
python -m research.forecast_engines.cli collision-map path/to/forecasts.json
python -m research.forecast_engines.cli source-refresh path/to/source_refresh.json
python -m research.forecast_engines.cli boundary-map path/to/stress_request.json
python -m research.forecast_engines.cli coverage-audit path/to/coverage_request.json
python -m research.forecast_engines.cli horizon-overlap path/to/overlap_request.json
python -m research.forecast_engines.cli target-contracts
python -m research.forecast_engines.cli target-provenance path/to/coverage_request.json
```

The request JSON contains `engine_id`, `symbol`, `as_of`, and a `features` object keyed by the exact inputs listed in `catalog.py`. Each feature object matches the fields on `FeatureObservation`. The CLI writes one forecast or abstention JSON record to stdout. It never places, stages, or queues an order.

To preserve forecast and subsequently observed outcome records, use `ForecastLedger` from `ledger.py`. The SQLite ledger is append-only at the application layer, uses update/delete-blocking triggers, and hashes each canonical event against the prior hash. Current labelable forecasts accept outcomes only when the target-contract fingerprint, selected window ID/start/end, label-transform ID/hash, and label-context fingerprint match the frozen forecast; the outcome's observation timestamp must equal that exact window end. FE15 is marked scenario-only and cannot accept observed-return labels. Store outcomes as new events; never overwrite the original forecast. A hash chain detects accidental edits but is not a substitute for signed backups, database access controls, or external timestamping.

`collision-map` accepts either a JSON array of serialized forecasts or `{"forecasts": [...]}`. It partitions only forecasts with the same symbol, as-of cutoff, target, target unit, horizon, forecast unit, direction semantics, target-contract fingerprint, exact frozen target window, and label-context fingerprint. Target-window timestamps are normalized to UTC, so alternate timezone spellings of the same interval stay together. Exact source hashes, source IDs, and declared source groups expose *potential* evidence collisions; shared transform IDs/hashes are reported separately and do not merge source clusters on their own. None of these labels establishes measured correlation. Score-orientation entropy is descriptive, not direction accuracy; risk-rank-only panels have no directional entropy, and entropy is suppressed when an engine appears more than once in a panel so repeated records cannot cast extra disagreement votes. Output separates score-orientation categories from magnitude aggregation: unlike units can report orientation only, while risk ranks and non-directional point estimates explicitly report that no direction comparison is available. A median is emitted only when the forecast unit equals the target unit, is never an ensemble forecast, and is suppressed for duplicate engine records.

The boundary-map command accepts a request object in the usual forecast-request format plus stress_ranges, keyed by feature name with explicit low, high, and unit. It reports one-feature endpoint effects, the first sampled direction flip along each individual feature axis, pairwise score interactions with all other features held at baseline, and every joint hyperrectangle corner (at most eight dimensions). Ranges are supplied by the caller; corner counts are not probabilities and no stress surface is emitted when the baseline abstains.

`source-refresh` accepts `{"as_of": "...Z", "current": {"source_id": "...", "source_family": "...", "age_seconds": 120, "horizon_seconds": 600}, "history": [...], "min_samples": 30}`. History rows carry unique `observation_id`, source identity/family, historical age and horizon, `observation_cutoff_at`, `first_refresh_at` (null when no refresh was observed), `label_available_at`, SHA-256 `source_hash`, and explicit boolean `refreshed_within_horizon` and `rights_approved` fields. Positive labels require the first refresh inside the declared horizon and before label availability; negative labels mature once the full horizon elapses, even if a later refresh is eventually recorded. Only matured approved records are eligible; source-specific history is preferred, with same-family pooling only at the sample floor. The history fingerprint binds selected labels, as-of-known timing, and source hashes; refresh timestamps after the evaluation cutoff are omitted. Thin samples return no rate. This estimates source refresh frequency, not price movement.

`evaluation.py` provides Brier/log-loss/reliability-bin metrics for explicitly calibrated OOS probabilities, QLIKE for variance forecasts, AUC for uncalibrated risk rankings, sign-hit rate for direction scores, paired loss deltas versus a declared baseline, and Benjamini–Hochberg correction across a declared test family. Probability scoring refuses uncalibrated inputs. Sign-hit rate is not profitability. All evaluations should retain abstentions, compare to simple baselines, use time-blocked splits, count every tried variant, and report costs separately if a future strategy layer is ever evaluated.

`coverage-audit` joins the append-only forecast ledger as of a caller cutoff and compares mature target outcomes for emitted forecasts and separately labeled abstentions. The request contains a ledger path, `evaluation_as_of`, and optional `tail_thresholds` keyed by target unit. It reports attempt coverage separately from label coverage, so late or missing outcome data cannot quietly shrink the denominator. It also separates immature, invalid, orphaned, and out-of-scope labels. Tail rates and reason profiles are descriptive; no significance test or trading conclusion is emitted.

`horizon-overlap` uses the same request shape (`ledger_path`, `evaluation_as_of`). It requires one valid final label per attempt to construct each realized interval. Same-symbol interval overlaps show how often observations reuse future-path segments; exact-cutoff cross-symbol pairs identify shared forecast cohorts. Distinct target contracts, selected windows, label transforms, and label contexts stay in separate groups. Its maximum non-overlapping-window count is a geometric anchor for experimental design, not an inferential effective sample size.

`target-contracts` prints all 30 primary label contracts and hashes. `target-provenance` reports bound versus legacy-unbound records, exact-window, transform, and label-context coverage, and transform versions without scoring outcomes. Scenario-only attempts are reported separately and excluded from missing label-binding totals. Current contract hashes are checked against their target identity and label status; absence remains distinct from literal field values. For an evaluable forecast, provide `target_window_id`, `target_window_start_at`, `target_window_end_at`, `label_transform_id`, canonical `label_transform_hash`, and all six `label_context` identifiers in the request. Window IDs must be registered for that engine (FE01, for example, allows `5-session`, `10-session`, or `20-session`). The outcome append repeats the target/window/transform/context fingerprints, and its observation time must equal the frozen window end. These hashes identify caller-declared code and measurement conventions; they cannot prove that the code produced the value correctly or that the source followed the declared conventions. Legacy rows remain readable and explicitly unbound; no retrospective hash is fabricated.

## Research gates before any decision use

1. Lock the target definition, one allowed window ID and exact start/end times, label-transform hash, six-field label context, instrument universe, feature timestamps, and data rights before looking at outcomes.
2. Fit parameters only on train data; preserve a development period and an untouched final holdout. Purge overlapping labels and use date-blocked validation.
3. Compare to persistence, unconditional/base-rate, and simple market/sector baselines. Report Brier/log-loss for calibrated events, QLIKE for variance, and paired uncertainty intervals; report coverage and abstention rates.
4. Count all engines, horizons, universes, filters, and parameter variants in multiple-testing control. Do not select the best backtest and call it the expected result.
5. Require independent data and an untouched forward paper forecast period before considering any future integration. That future integration is outside this package and needs a separately reviewed change.

No tests or historical backtest are included in this initial research implementation. The formulas are executable hypotheses, not validated production models.
