# t_kz_sweep: Algorithm

Created by GrokBot. Packaged into Test on 2026-10-29 (packaging pass 2026-10-29) from the source at dwj9ddyvf6-hub/master-desk, path mdesk/engines/kz_sweep.py, to sleeves/t_kz_sweep.py in this repo.

This copy was sanitized at 2 point(s) to pass the public-repo privacy gate; the private original in dwj9ddyvf6-hub/master-desk (mdesk/engines/kz_sweep.py) is the verbatim source.

## What it is

An ICT killzone liquidity-sweep reversal sleeve. It fades a sweep of known liquidity levels when price reclaims the level on a 15-minute close inside the morning killzone.

## Rules (from the creation's own specification)

- Instruments: QQQ and SPY (levels derived from NQ and ES futures) and BTC-USD, long-only.
- Levels: prior Globex day high/low, plus untouched day-minus-2 and day-minus-3 highs/lows, and Asia session extremes.
- Window: only the 09:45 to 10:30 ET killzone is traded.
- Trigger: price sweeps a level, then closes back through it (reclaim) on a 15-minute bar.
- Risk: reward-to-risk floor of 1.5; hard time exit at 12:00 ET.
- Lane: shadow Test lane, 3 slots of $1k.
- The kz-v2 edge fixes from the source repo are included in the copied code.

## Source

Code: sleeves/t_kz_sweep.py in this repo, sanitized copy (non-verbatim, 2 point(s) sanitized) of mdesk/engines/kz_sweep.py in dwj9ddyvf6-hub/master-desk (main).
