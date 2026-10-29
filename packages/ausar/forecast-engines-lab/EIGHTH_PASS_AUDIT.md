# Eighth-pass audit: freeze how the target is measured

**Date:** 2026-10-29

**Scope:** label construction and instance-level measurement provenance across FE01–FE30, the forecast contract, append-only ledger, and diagnostics that group or compare outcomes.

**Files changed:** confined to `research/forecast_engines/`.

## Finding: a stable target name can still describe different measurements

The seventh pass pinned a primary estimand, allowed horizon, exact UTC interval, and label-transform code hash. A further inspection found that those identities do not distinguish two label builds that use the same transform name and interval but different underlying conventions. Examples include price return versus total return, split-adjusted versus raw price, a regular-session close versus an extended-hours mark, a different benchmark series, a revised fundamental vintage, or a different corporate-action treatment.

Those are substantive differences, not cosmetic metadata. CRSP publishes explicit return and corporate-action calculation methodology; ALFRED exposes the vintage dates at which macro series changed; Nasdaq publishes exchange trading calendars including early closes. These examples show why a timestamp and transform hash alone do not identify a realized outcome convention.

## Change: an instance-level label context

Added `label_context.py` with a strict six-field schema:

| Field | What it freezes | Example identifier |
|---|---|---|
| `series_id` | Exact instrument or underlying observation series | `alpaca:us_equity:SPY` |
| `measurement_basis_id` | Return/variance/event measurement and adjustment basis | `total_return:split-dividend-adjusted:v1` |
| `calendar_id` | Exchange session or event-time convention | `XNYS:regular-session:v1` |
| `reference_series_id` | Benchmark/hedge/leader used in a relative target; `none` if not applicable | `benchmark:SP500-total-return:v1` |
| `vintage_policy_id` | Which published/corrected vintage may supply the realized value | `final-corrected-data-as-of-label:v1` |
| `corporate_action_policy_id` | Split/dividend/delist handling; `not_applicable` only when it truly does not apply | `splits-dividends-and-delisting:v1` |

Identifiers are caller-defined stable IDs, not provider-specific constants. Empty and placeholder values such as `unknown`, `TBD`, or `N/A` are rejected; non-applicable dimensions must be explicit. A canonical JSON SHA-256 fingerprint is placed on the forecast. A labelable forecast may be emitted without a label context for exploratory use, but it cannot accept an evaluated outcome until the context, exact target window, and transform are all frozen.

The forecast/abstention record carries the context object and hash. The outcome repeats the context hash. The ledger validates the object against its hash when appending forecasts and rechecks the binding during reads. A current outcome is rejected if it omits or changes the context fingerprint. `target_contract_fingerprint` includes the context schema and required-field names so a future schema revision changes the registered target identity.

`target-provenance`, `coverage-audit`, `horizon-overlap`, and `collision-map` partition by context identity. They do not pool different benchmark definitions, calendars, data-vintage policies, or adjustment conventions under one target label. The provenance audit counts bound attempts that did not freeze a valid context.

## Example request fragment

```json
{
  "target_window_id": "5-session",
  "target_window_start_at": "2026-10-01T20:00:00Z",
  "target_window_end_at": "2026-10-08T20:00:00Z",
  "label_transform_id": "benchmark-excess-return-v1",
  "label_transform_hash": "sha256:<64 lowercase hex>",
  "label_context": {
    "series_id": "alpaca:us_equity:SPY",
    "measurement_basis_id": "split-dividend-adjusted-total-return:v1",
    "calendar_id": "XNYS:regular-session:v1",
    "reference_series_id": "benchmark:SP500-total-return:v1",
    "vintage_policy_id": "final-corrected-data-as-of-label:v1",
    "corporate_action_policy_id": "splits-dividends-and-delisting:v1"
  }
}
```

The outcome append supplies the emitted `label_context_fingerprint` alongside the frozen target, window, and transform identities.

## Verification boundary

This is a measurement-identity control, not a data-authenticity system. The fingerprint proves only that the declared context stayed unchanged. It cannot prove that a source followed the declared adjustment, calendar, or vintage policy; that the transform actually ran; that use rights are valid; or that the target forecasts anything useful. The outcome source hash remains a caller-supplied digest of its source artifact. Historical rows without this context remain readable as legacy/unbound but are not silently upgraded.

## Primary sources

- Center for Research in Security Prices, [Calculations and Index Methodologies](https://www.crsp.org/wp-content/uploads/guides/CRSP_Calculations_and_Index_Methodologies.pdf), including return and distribution calculations.
- Federal Reserve Bank of St. Louis, [ALFRED overview](https://fred.stlouisfed.org/docs/api/fred/alfred.html) and [series observations API](https://fred.stlouisfed.org/docs/api/fred/series_observations.html), including vintage-date retrieval for historical availability.
- Nasdaq Trader, [Trading Calendar](https://nasdaqtrader.com/Trader.aspx?id=Calendar), including holidays and early-close notices.

These sources motivate the convention dimensions. The schema and hash protocol are local engineering choices.
