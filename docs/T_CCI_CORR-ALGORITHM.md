# t_cci_corr: Algorithm

Created by GrokBot. Packaged into Test on 2026-10-29 (packaging pass 2026-10-29) from the source at dwj9ddyvf6-hub/master-desk, path mdesk/engines/cci_corr.py, to sleeves/t_cci_corr.py in this repo. A reference spec and code copy also live at dwj9ddyvf6-hub/quant-research-backup, path research/cci_correction/.

This copy was sanitized at 3 point(s) to pass the public-repo privacy gate; the private original in dwj9ddyvf6-hub/master-desk (mdesk/engines/cci_corr.py) is the verbatim source.

## What it is

A CCI correction pullback sleeve: it buys deep CCI washouts inside an established uptrend, long-only, on daily bars.

## Rules (from the creation's own specification)

- Setup: the lowest CCI(27) reading over the last 18 sessions falls below -100, while the regime filter shows an uptrend.
- Trigger: CCI crosses back above -100, or turns up from the washout.
- Stop: 2 ATR.
- Target: 3R, with a 3 ATR trailing stop.
- Lane: shadow Test lane, $1k split into 5 slots of $200.

## Source

Code: sleeves/t_cci_corr.py in this repo, sanitized copy (non-verbatim, 3 point(s) sanitized) of mdesk/engines/cci_corr.py in dwj9ddyvf6-hub/master-desk (main).
