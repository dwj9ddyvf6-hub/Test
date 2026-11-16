# Wave 3 Lane B2: FIT-PROXY-v1 Across Every Universe the Box Can Score

Measurement deliverable only. No exam, no find claim. Label stays FIT-PROXY-v1; it is not Coval-Stafford FIT (true build needs per-fund flows and lagged fund holdings, not on the box; dated 2026-12-12 in the H3 record). Machine record in lane_b_b2.json.

## What was run

The exact FIT-PROXY-v1 definition from hunt/work/compute_fit_proxy.py (pressure day: volume at least 1.5x prior-20 ADV, absolute excess return vs SPY at least 2.0 percent, and at least 1.0x the prior-60-session sigma of the name's own returns; contribution = |excess percent| x (volume ratio minus 1); sell and buy sums over gated days), recomputed on the widest universe honestly supported by on-box split-adjusted inputs: the B2K folder. The original builder fetches SIP bars live per symbol; no new live fetch was made, so the window ends at the last local session, 2026-11-06, not 2026-11-13. That window difference is named here and in the JSON, not hidden.

## Scored counts per universe

| Universe | Scored | Of | Window |
|---|---|---|---|
| Original Focus 30 (SIP fetch, hunt/fit_proxy_v1.json) | 29 | 30 (SIVE unscored, SIP serves zero bars) | 2026-10-01 to 2026-11-13 |
| B2K local split-adjusted folder (this run) | 98 | 98 stock files present (folder also holds SPY and QQQ benchmark files, not scored) | 2026-10-01 to 2026-11-06 |
| Focus 30 overlap inside B2K | 4 | NVDA, AVGO, AMD, XLE are the only Focus names in the B2K folder | same |

The other 26 Focus names (SMH, SOXX, MRVL, ARM, TSM, AMAT, MU, SNDK, WDC, AAOI, SIVE, COHR, LITE, CRDO, ALAB, AXTI, CRWV, PLTR, RKLB, FLNC, EOSE, FCEL, BE, OKLO, VST, CEG) have no local split-adjusted file and keep their original SIP-run scores as their current readings.

## Data quality: one fabrication caught and voided

CTVA printed a sell score of 1471.74 from a single day, 2026-10-01, close 77.65 to 12.57 (-83.81 percent) with volume ratio 18.52: a split-scale discontinuity inside the local file, the same defect class the original run caught on raw SOXX. Scan of all 98 names for in-quarter single-day moves above 40 percent flagged CTVA only. Cure applied as in the original: the flagged-day contribution is voided and the name re-ranked (CTVA sell 0.0, buy 13.04, rank 57 of 98). Raw score recorded in the JSON data_quality_record; the voided figure must not be cited.

## Wide-universe pressure ranking (B2K, current quarter to 2026-11-06)

Top 10 by FIT-PROXY sell pressure: BA 58.57, GOOGL 54.43, T 44.94, AMD 39.34, TMUS 37.19, VZ 33.57, CAT 22.54, SRE 13.75, XLK 13.63, ORCL 13.06 (sell / net in the JSON per name).

Bottom 10 by sell pressure (all zero sell pressure days in the window): the tail is a tie at 0.0 across the sector SPDRs XLP, XLRE, XLU, XLV, XLY and others including WMT, XEL, XLB, XLC, XLF (full bottom-10 list in the JSON). Zero here means no gated sell-pressure day printed in the quarter window, not safety.

Original Focus 30 reading, for beside-comparison (SIP window to 2026-11-13): top 5 sell pressure MRVL, CRWV, SNDK, NVDA, LITE; bottom 5 AVGO, CEG, XLE, PLTR at the tail of its ranking. The two rankings are on different windows and universes and are not merged.

STATUS: GREEN for the measurement as scoped (98 of 98 locally scoreable names recomputed, defect caught and voided with the raw figure preserved). Evidence pointer: lane_b_b2.json in this folder.
