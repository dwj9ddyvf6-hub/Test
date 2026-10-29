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
