# KZ Check Algorithm

Created by GrokBot.

Algorithm derived from the code on 2026-10-29 (source: dwj9ddyvf6-hub/master-desk, main, tools/kz_check.py).

## What it is
An alert-only health check for the t_kz_sweep sleeve. It prints alerts and never trades and never halts anything.

## Modes (from the code's own docstring and body)
- Default (health): checks feed freshness for every symbol in the sleeve universe and its sources, checks the sleeve is registered, and alerts if a t_kz_sweep position is held past 12:05 ET or overnight.
- dryrun: replays what the sleeve would have signalled on the cached/fetched recent 15-minute bars (signals only). It steps the md2 pass grid inside the entry window, applies the sleeve's signal function with the fresh-close rule (close no older than 20 minutes), recomputes risk/reward at the fill price, records an abstention when reward/risk at the fill is below the sleeve's minimum, and reports the would-be exit (stop, target, or the 12:00 ET time stop) evaluated on the source bars at the signal's absolute levels.

## Files in this package
- packages/grokbot/kz-check/tools/kz_check.py
- docs/KZ-CHECK-ALGORITHM.md (this file)
