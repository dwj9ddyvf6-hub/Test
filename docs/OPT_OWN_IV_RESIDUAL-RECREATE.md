# OPT_OWN_IV_RESIDUAL: Recreation package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Canonical id: `OPT_OWN_IV_RESIDUAL`; canonical name: OPT_OWN_IV_RESIDUAL; aliases: OPT_OWN_IV_RESIDUAL.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type volatility, family own_iv_residual, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "OPT_OWN_IV_RESIDUAL" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: femto land-wt config params; alias record sources: ausar_deployed, femto_land_wt
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; matching material only as noted in Provenance); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/free_opt_own_iv.py + desk3/sleeves/free_opt_own_iv.py. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

Own-IV residual volatility sleeve: buys a producer-supplied at-the-money straddle package (one call and one put, always together) when the package's causal realized-volatility forecast exceeds its implied volatility by at least 2 points. Accounting grade PARTIAL and UNRESOLVED: the accounting recorded no entry or exit rule and no description; the code cited above does record them, and the code is the truth here. The unresolved note in the accounting says the case would be settled by the sleeve module docstring or a catalog description; the module header in `sleeves/free_opt_own_iv.py` is that docstring.

## Full algorithm

From `sleeves/free_opt_own_iv.py` `signal()` (account "free_options", BUDGET_USD 100000.0 pool, CONFIG cadence_s=300), in evaluation order:

1. Exits first (`_exit_intents`): held legs grouped by entry date; a group exits together when sessions since entry >= 10 (session dates strictly after the entry date, from extra[session_dates]) or the session is at or past the earliest leg expiry parsed from the OCC symbols. Before expiry every held leg needs a two-sided quote in extra[quotes] (ask > 0, bid >= 0, ask >= bid) or the group is retained; at or past expiry that gate is bypassed. Long legs exit sell_to_close at the bid, short legs buy_to_close at the ask. Each leg intent carries ExitRule time_bars=10.
2. One package per session: if any held record was entered this session, or last_exit_date equals this session, no new entry is evaluated.
3. Freshness gate on extra[quote]: source age at most 90 s (SOURCE_MAX_SECONDS), receipt age at most 30 s (RECEIPT_MAX_SECONDS), future tolerance 2 s, receipt not earlier than source, and a non-crossed positive quote (ap >= bp > 0).
4. Package shape (`straddle_legs`): extra[package] must carry exactly 2 legs with rights {call, put} and pass `package_skew`: consecutive leg source stamps at most 30 s apart (SKEW_MAX_SECONDS), with source stamps present.
5. Forecast/IV gate (enhancement, on by default; extra["free_opt_own_iv_improve"]["forecast_iv_gate"]): the package must carry forecast and iv values (aliases forecast_vol / implied_iv) with forecast - iv >= 2.0 points (FORECAST_IV_MIN_SPREAD); missing or unparseable values fail closed.
6. Leg tradability: every leg needs a symbol, a finite ask > 0, and its own source stamp fresh under the same 90 s / 2 s windows.
7. Entry: one intent per leg, qty_hint 1, buy_to_open at the leg ask (price_hint rounded to 2 dp), both legs sharing the reason tag "package FREE_OPT_OWN_IV_V1" with forecast, iv and spread stamped in. One leg is never submitted alone.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Strategy module (already in Test): `sleeves/free_opt_own_iv.py` (repo copy of the desk strategy module `desk3/strategies/free_opt_own_iv.py`; header: "FREE_OPT_OWN_IV").
- v3 adapter (already in Test): `desk3/sleeves/free_opt_own_iv.py` (also `integration/free_opt_own_iv_adapter.py`); it preserves the mapping free_opt_own_iv -> OPT_OWN_IV_RESIDUAL noted in the classification evidence.
- Existing recreation doc for the free id (already in Test): `docs/FREE_OPT_OWN_IV-RECREATE.md`; existing strategy doc: `strategies/femto/femto-free-opt-own-iv.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry "OPT_OWN_IV_RESIDUAL" (UNRESOLVED, PARTIAL).

## Configuration

- Module CONFIG: sleeve_id "free_opt_own_iv", cadence_s 300, universe (), risk_pct None. Account "free_options", pool BUDGET_USD 100000.0.
- Roster reading in the existing free-id recreation doc: module desk3.sleeves.free_opt_own_iv, cadence_s 300, session 24h, slice capital_usd 10000.0 / cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close false, params {}, inputs [options], parked false.
- Accounting parameters for OPT_OWN_IV_RESIDUAL itself: only {"symbols": []} was recorded; every other value above comes from the code, not the accounting.

## Data inputs

The options producer supplies extra[package] {legs (2, with symbol, right, ask, source_at), forecast, iv}, the freshness quote via extra[quote] {t or source_at, received_at, ap, bp}, and for exits extra[quotes] and extra[session_dates]; sleeve_state held records from the desk. Snapshot input: options.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (cash, core, or no intent), never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- Fixture A: a fresh quote, a 2-leg call+put package with stamps within 30 s and forecast - iv = 2.5: two entry intents of qty 1, one per leg, each with time_bars 10. Fixture B: forecast - iv = 1.0, or a package with only a call leg: no entry. Fixture C: a held group at 10 sessions with two-sided quotes: both legs exit together.
- No intent when a required input is missing, stale, crossed or malformed: the code fails closed.
- The config row used matches the roster reading in the Configuration section.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
