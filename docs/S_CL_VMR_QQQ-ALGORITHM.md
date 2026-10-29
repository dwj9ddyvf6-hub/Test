Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_cl_vmr_qqq: Algorithm

## What it trades
Long QQQ only, 1 slot. A ChartsLector study lane, v3-native in
laz_sleeves/s_cl_vmr_qqq.py. Source status in the code: Live.

## Indicators and parameters
- VIX reading from view["vix"] (a scalar close; a non-scalar payload
  fails closed with no reading, per the CURE2-2 guard in the code).
- VIX_MAX = 35.0. SLOT_USD = 1000.0. HOLD_SESSIONS = 5.
- QQQ daily bars from view["bars"] key QQQ|1Day.
- No stop loss is implemented.

## Entry rules
- No session date in the view: emit nothing.
- If a position is already held: emit no new entry.
- Require QQQ daily bars and a VIX reading at or below 35.0.
- ENH19 stale-bar gate (on by default): refuse the entry when the
  last QQQ bar is more than 4 calendar days before the session.
- Quantity is whole shares: int(1000.0 // last QQQ close).
- Entry intent is a market, day order priced (hint) at the last close,
  reason cl_vmr_vix_le35.

## Exit rules
- For a held position, exit QQQ when sessions held, counted as bars
  after the open date, reach 5. Reason cl_vmr_time5. No stop exit.

## Sizing, session and cadence
- 1 slot x $1,000. Config row: cadence_s 86400, session rth,
  capital_usd 1000, flat_by_close false.

## Data inputs
bars_1day, positions, vix. Declared INPUTS in the code match.
