# Forecast machinery (internal doc, not a reader surface)

Step 0 of the Forecast Engines 30 program (design:
`~/workspace/terminal-lineup/FORECAST-ENGINES-30.md`, 'Shared machinery:
build once, before Engine 1'). No engine logic and no reader page live
here; the engines build on these three components one at a time.

Design decision (from the inspect phase): the forecast ledger is its
own file with its own module, not an extension of the Morgue ledger
(`~/workspace/morgue/output/ledger.jsonl`). The Morgue ledger is a
proven, live as-was log with its own row shapes; forecast rows need
dedupe, a tamper-evident hash chain, registry validation and grade
linkage that the Morgue log does not carry. Bolting them on would fork
a verified path and risk the live daily cycle. This ledger follows the
same N1 append-only discipline in its own file.

## Files

- `ledger.py` — the append-only forecast ledger.
- `grading.py` — the grading runner and the registered scoring rules.
- `registry.py` + `registry.json` — the evidence-family registry.
- `ledger.jsonl` — the live ledger the engines write to (genesis row
  only at build time; chain-verified).
- `tests/test_forecast_machinery.py` — the corruption test suite.

## Ledger API (`ledger.py`)

- `Ledger(path, registry=None)`; `rows()`; `verify_chain()` — every row
  carries `prev_hash`/`row_hash` (sha256 over prev hash + canonical
  row). A rewritten, deleted or reordered row breaks the chain;
  appends to a broken ledger are refused.
- `append_forecast(engine_id, issued_ts, subject, quantity, value,
  horizon_open, horizon_close, lineage, families, outcome,
  absence_state="present") -> (row, created)`. Lineage must carry
  `source_artifacts` (each with `path` and `sha256`) and a five-clock
  `clocks` envelope: `event_time, publication_time,
  first_available_time, ingestion_time, decision_as_of` (the adopted
  evidence-contract form, matching `morgue/evidence.py` CLOCK_FIELDS).
  Families are validated against the registry. Dedupe key:
  engine + subject + horizon open/close + sha256(value); an identical
  republication returns the existing row with `created=False` and
  writes nothing. `absence_state` is one of `present, no_data,
  no_print, not_yet_available, defect_abstention` (absence is a named
  state, never a zero; C14 defect abstentions use the last).
- `append_grade(forecast_row, grade)` — grade rows reference
  `forecast_row_id`; a second grade for the same forecast is refused
  (re-grades are corrections).
- `append_correction(corrects_row_id, note, payload)` — corrections are
  new rows; history is never rewritten.
- `recompute_figures(rows)` — per-engine forecast/graded counts and
  mean scores, computed from ledger rows alone. A figure that cannot
  be recomputed this way does not ship.

Forecast `value` shapes by form: band `{"lower", "upper",
"stated_coverage"}`; probability `{"p"}`; point `{"estimate"}`;
distribution `{"quantiles": {"0.1": ..., "0.5": ..., "0.9": ...}}`;
bins `{"bins": [p, ...]}`; timing `{"resolved_by": {"5": p, ...}}`.
Outcome specs (`outcome`): `{"symbol", "kind", "at_date", ...}` with
kind `close | return | abs_return` (needs `base_date`), `close_above`
(needs `threshold`), `touch` (needs `level`, `window_open`,
`window_close`), or `binary_event` (needs `realised`).

## Grading runner API (`grading.py`)

- `PriceSource(path=~/workspace/morgue/data_cache/board_bt_bars.json)`
  — the shipped daily history the AI Chart Read uses (the source of
  `site/ai-chart-read/data.json`), shaped
  `{symbol: [[date, open, high, low, close, volume], ...]}`.
- `is_matured(row, prices, as_of=None)` — matured only when the
  horizon-close session exists in the price source.
- `grade_forecast(ledger, row, prices, registry)` — refuses before
  maturity; grades by the engine's registered rule; appends the grade.
- `run_grading(ledger, prices, registry)` — grades every matured,
  ungraded, present-state forecast.
- `abstention_coverage_audit(rows, prices)` — separate audit role
  (adopted abstention-coverage design): read-only; resolves refused
  (non-present absence-state) and taken outcomes with the same
  `resolve_outcome` and price source, publishes per-engine
  taken/refused counts and per-outcome-kind distributions beside
  each other (thin-cell rule: under 30 graded outcomes in a cell,
  counts only), and names per engine, with reasons, any abstention
  it cannot resolve. Audit outcomes never enter a grade. The Record
  page panel is fed by `site/refresh_record.py` from this function.
  Tests: `tests/test_abstention_audit.py`.
- Rules: `coverage` (band hit + width), `brier` (Brier + log loss),
  `pinball` (pinball per quantile + `crps_approx`, the CRPS-ready hook:
  2 x mean pinball over the quantile set), `abs_error`,
  `ranked_probability_score`, `survival_brier` (timing).

## Registry (`registry.json`, via `registry.py`)

Six families: `price`, `options_prints`, `modelled_inventory`,
`filings_positioning`, `events_calendar`, `distributional_volatility`.
Every input of every engine is assigned to exactly one family
(validated at load: duplicates or unregistered families raise).
Per engine: `id, number, name, forecast_form, horizons,
grading_rule_id, kill_criterion, proving_threshold, state`
(all 30 engines, all `proving`). Kill criteria and thresholds are
transcribed from FORECAST-ENGINES-30.md; the registry's
`registry_notes` records the one ambiguity (no separate per-engine
input inventory exists in the design, so inputs are the load-bearing
inputs named in each engine's Data route and Mechanism).
`defect_sources` carries the three C14 fail-open Femto functions
(`fear_ok_from_product`, Qullamaggie `accept()`,
`pattern_calibration.validate_product`), each defect-tagged: abstentions
they cause are `defect_abstention`, not market states, until cured.

## Tests

`python3 -m pytest tests/ -q` — 10 passed at build time (2026-10-28),
covering: rewrite attempt breaks the chain and blocks appends,
duplicate forecast counted once, grade before maturity refused,
unregistered family refused, missing clock/lineage hash refused,
grade append + figures recomputed from the ledger alone, Brier on a
touch probability, correction as a new row, registry completeness
(30 engines, 6 families, 3 defect sources), and the real price source.
