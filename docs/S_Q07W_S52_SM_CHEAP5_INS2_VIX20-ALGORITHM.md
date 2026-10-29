Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_q07w_s52_sm_cheap5_ins2_vix20: Algorithm

## What it trades

Lazarus lane s_q07w_s52_sm_cheap5_ins2_vix20. Family: swing (Tensor 1W swing signal). Cap band: sm (small cap band, as named in SPEC['band']='sm'). Horizon: 52 weeks.
It is a fire-consumer sleeve: it does not generate its own primary signal in this module.
The module file is `adapters3/s_q07w_s52_sm_cheap5_ins2_vix20.py` in the desk (muse-desk-v3), packaged here as `sleeves/s_q07w_s52_sm_cheap5_ins2_vix20.py`.

## Engine and delegation

This module declares its sleeve id and parameters and delegates evaluation to desk3.q07_engine.evaluate_q07 with an inline SPEC in the module.
`evaluate(view, ctx)` is the only entry point in the module. Any rule not stated in the
module itself is implemented in that shared engine, not duplicated here.

## Indicators and parameters

- Filters: cheap5, ins2, vix20.
- Horizon: 52 weeks.
- Band: sm (small cap band, as named in SPEC['band']='sm').
- Sizing: 1 slot at $1,000 (module docstring; config slice capital_usd 1000.0).
- Session / cadence (from its config row in config/sleeves.json): 300 s, session rth, parked True (config row).
- Flat by close: False in the config row for this lane (no flatten_time_et set).

## Entry rules

Buy only on a QQQ-down day within 5 sessions of the signal (module docstring, catalog section 4.1 family rule). The detailed filter evaluation lives in desk3/q07_engine.py, not in this module; this module only declares the SPEC and delegates.

## Exit rules

Exit on a 15% stop or at the 52-week horizon (module docstring).

## Data inputs

Declared inputs: sleeve_fires, bars_1day, vix, positions.

## Ambiguity note

Where the module delegates to a shared engine or a SPECS table, the exact filter
arithmetic lives in that engine, not in this module. This doc states only what the
module, its config row, and the named engine's own header / SPECS entry state, and
flags anything those sources do not specify, rather than inventing a rule.
