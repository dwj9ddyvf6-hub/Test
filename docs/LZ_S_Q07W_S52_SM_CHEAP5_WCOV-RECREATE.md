# lz_s_q07w_s52_sm_cheap5_wcov - Recreation Package

## Provenance

- Canonical ID: `lz_s_q07w_s52_sm_cheap5_wcov`
- Canonical name: Q07 w_swing H52 small cheap5+wiki_cov (test)
- Aliases: lz_s_q07w_s52_sm_cheap5_wcov
- Type: trend following ; Family: 1w ; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Q07 w_swing H52 small cheap5+wiki_cov (test)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_swing H52 small cheap5+wiki_cov (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Existing Test doc: `docs/S_Q07W_S52_SM_CHEAP5_WCOV-ALGORITHM.md` in dwj9ddyvf6-hub/Test.
- Code search record: searched Test (tree at batch start; found, see Files below), dwj9ddyvf6-hub/Silicon (recursive tree; no path matching this canonical ID), dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path matching this canonical ID). Code is present in Test, so no vendoring was needed.
- Accounting algorithm record (verbatim fields): entry: ['[lz_s_q07w_s52_sm_cheap5_wcov] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}'] ; exit: ['[lz_s_q07w_s52_sm_cheap5_wcov] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}'] ; filters: ['[lz_s_q07w_s52_sm_cheap5_wcov] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json'] ; gaps: ['sizing not recorded in any consulted source']

## What this strategy is

Q07 w_swing H52 small cheap5+wiki_cov (test). Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

The full Test algorithm document / strategy card for this strategy is reproduced in the Full algorithm section below. Where the accounting graded the algorithm PARTIAL, gaps named in the accounting are preserved there and below as 'not in the record' rather than filled.

## Full algorithm

Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_q07w_s52_sm_cheap5_wcov: Algorithm

## What it trades

Lazarus lane s_q07w_s52_sm_cheap5_wcov. Family: swing. Cap band: small. Horizon: 52 weeks.
It is a fire-consumer sleeve: it does not generate its own primary signal in this module.
The module file is `adapters3/s_q07w_s52_sm_cheap5_wcov.py` in the desk (muse-desk-v3), packaged here as `sleeves/s_q07w_s52_sm_cheap5_wcov.py`.

## Engine and delegation

This module declares its sleeve id and parameters and delegates evaluation to desk3.lazarus_q07.evaluate_sleeve, with SPEC = SPECS[SLEEVE_ID] from desk3.lazarus_q07.
`evaluate(view, ctx)` is the only entry point in the module. Any rule not stated in the
module itself is implemented in that shared engine, not duplicated here.

## Indicators and parameters

- Filters: cheap5 (price < $5), wcov (wiki_cov tag true, or wiki_views > 0, per desk3/lazarus_q07.py filter readings).
- Horizon: 52 weeks.
- Band: small.
- Sizing: slots=1, budget $1,000 in desk3.lazarus_q07 SPECS; config slice capital_usd 1000.0.
- Session / cadence (from its config row in config/sleeves.json): 86400 s (daily), session rth, parked True (config row; module docstring: CSV off => parked, exits managed).
- Flat by close: False in the config row for this lane (no flatten_time_et set).

## Entry rules

Take the Tensor 1W swing signal in the small band, apply the named filters, buy only on a QQQ-down day within 5 sessions of the signal (desk3/lazarus_q07.py source rule, catalog section 4.1). A filter with no evidence fails closed.

## Exit rules

Exit on a 15% stop or at the 52-week horizon (desk3/lazarus_q07.py source rule).

## Data inputs

Declared inputs: fires, bars, positions (config row); producer inputs declared in INPUTS / PRODUCERS imported from desk3.lazarus_q07.

## Ambiguity note

Where the module delegates to a shared engine or a SPECS table, the exact filter
arithmetic lives in that engine, not in this module. This doc states only what the
module, its config row, and the named engine's own header / SPECS entry state, and
flags anything those sources do not specify, rather than inventing a rule.


Accounting gaps (not in the record): sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/LZ_S_Q07W_S52_SM_CHEAP5_WCOV-RECREATE.md`
- Algorithm doc / strategy card: `docs/S_Q07W_S52_SM_CHEAP5_WCOV-ALGORITHM.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code in Test:
- `sleeves/s_q07w_s52_sm_cheap5_wcov.py` (in Test)
- `adapters3/s_q07w_s52_sm_cheap5_wcov.py` (in Test)
- `integration/s_q07w_s52_sm_cheap5_wcov_adapter.py` (in Test)
- `desk3/lazarus_q07.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

Family swing, band small, horizon 52 weeks, filters cheap5 (price < $5) and wcov. Slots 1, budget $1,000 in SPECS; config slice capital_usd 1000.0. Cadence 86400 s (daily), session rth, parked True (CSV off, exits managed), flat by close False. Accounting entry policy as in Provenance; sizing in accounting: not in the record.

Other configuration (cadence, state, session) is as stated in the algorithm text above; anything not stated there is not in the record.

## Data inputs

As stated in the algorithm text above. For Q07 lanes: fires from the sleeve_feed composer, bars, and positions / broker readback, as named in that text. For other lanes: the data line in the strategy card reproduced above.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Open `docs/S_Q07W_S52_SM_CHEAP5_WCOV-ALGORITHM.md` and this doc for the parameter values.
3. Use the code files listed above as the runnable logic; for Q07 lanes the wrapper's `evaluate(view, ctx)` delegates to the shared engine named in the code list, with the SPEC for this sleeve ID.
4. Supply the data inputs named above in the view / ctx shape the code expects (fires, bars, positions, plus any extra keys the algorithm text names).
5. Call `evaluate(view, ctx)` on each cadence stated in Configuration; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm section.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm text above.
- Checklist: (a) with no qualifying fire / signal, no entry is emitted; (b) with a qualifying signal and all filters passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or beyond the stated stop exits in full; (d) a held position reaching the stated horizon / exit session exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation's outputs on identical view inputs against the Test code files listed above; matching intents / orders on those cases proves the recreation matches.
