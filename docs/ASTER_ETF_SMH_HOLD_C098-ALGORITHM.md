Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_etf_smh_hold_c098 algorithm

What it trades: SMH only, at weight 1.0, policy SMH_HOLD, frequency BUY_HOLD, gross exposure 0.98 of equity. The local sleeve file is a thin wrapper that delegates to desk3/aster_etf.py with SLEEVE_ID aster_etf_smh_hold_c098.

Common engine rules (desk3/aster_etf.py): evaluations emit nothing outside the 09:35-09:40 ET execution window (timezone-aware stamps are converted to America/New_York before the window check). Targets are whole shares: floor(gross * equity * weight / price), where equity is the view/ctx account or net value when supplied, otherwise the slice capital. Sells (non-target symbols in full, over-target symbols down to target) are emitted before buys. There is no price stop and no profit target. If a target leg has no usable bar price, the whole rebalance is refused rather than partially emitted. Absent bars therefore produce no intents.

Entry rules: on the initial allocation (no open position), inside the execution window, buy SMH up to the whole-share target floor(0.98 * equity / SMH price).
Exit rules: none by design. If any position is already held, evaluate returns no intents, so the sleeve never rebalances and never exits on its own; closing the position would be an operator action outside this code.
Sizing: 0.98 gross on a $10,000 slice (config capital_usd 10000, cash_usd 10000, bp_buffer_frac 0.02).
Session and cadence: session rth, cadence_s 300 (5 minutes), flat_by_close False.
Data inputs: bars, positions, quotes (config row and engine INPUTS). Bar lookup accepts keys SMH|1Day, SMH|1D, or SMH, and uses the last close.
Ambiguity: none material in this sleeve's own spec row; the gross 1.5 sibling differs only in gross.
