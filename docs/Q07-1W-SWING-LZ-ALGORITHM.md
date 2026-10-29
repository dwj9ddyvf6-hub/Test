# Q07 / 1W-Swing LZ Sleeves (x21) Algorithm

Created by GrokBot (enabled by GrokBot in the stage-2 enable; the sleeves are pre-existing Research Lab / Lazarus sleeves, not authored by GrokBot).

Algorithm derived from the code on 2026-10-29 (source: dwj9ddyvf6-hub/master-desk, commit 8526a50, lz_engine/config/sleeves.json).

## What it is
The stage-2 enable that turned on 21 research-backed Lazarus (lz) sleeves after the w_swing_heal job restored their input (the Research Lab w_swing feed): 20 s_q07w_s* cells whose status text marks them as research CONFIRMED cells, plus s_1wsw_stress. All 21 entries carry enabled=true and state=live in the packaged config. The sleeves are entries in lz_engine/config/sleeves.json (the full book file at this commit, 100 entries, is included verbatim) and are executed by the Lazarus engine that reads this config; evidence/load_800_stage2.json is the synthetic load record added in the same commit. This package records the enable state; it is not a separate engine.

## Entry and exit rules (from the packaged config entries)
- Kind: weekly (1w). Entry policy: fear_day.
- Entry window: max delay 65 minutes, window 5 sessions, capped limit day orders with a 5.0% limit band and 1.0% limit buffer, no-chase multiplier 1.02; both the stock and QQQ must be red.
- Exit: the sleeve feed fire's plan: 15% disaster stop / time exit, with the hold period stated per entry (for example 52 weeks for the s_q07w_s* cells).
- Sizing and per-cell research records are carried in each entry in the packaged config.

## The 21 sleeves
- s_q07w_s52_ml_deep70_ins2_vix20: Q07 w_swing H52 midlarge deep70+insider2+stress_vix20 (test)
- s_q07w_s52_ml_deep70_vix20_wlow: Q07 w_swing H52 midlarge deep70+stress_vix20+wiki_low (test)
- s_q07w_s52_ml_deep70_wlow: Q07 w_swing H52 midlarge deep70+wiki_low (test)
- s_q07w_s52_ml_ins2_mom6_vix20: Q07 w_swing H52 midlarge insider2+mom6+stress_vix20 (test)
- s_q07w_s52_ml_ins2_mom6_wlow: Q07 w_swing H52 midlarge insider2+mom6+wiki_low (test)
- s_q07w_s52_sm_cheap5_deep70_ins2: Q07 w_swing H52 small cheap5+deep70+insider2 (test)
- s_q07w_s52_sm_cheap5_ins2_vix20: Q07 w_swing H52 small cheap5+insider2+stress_vix20 (test)
- s_q07w_s52_sm_cheap5_wcov: Q07 w_swing H52 small cheap5+wiki_cov (test)
- s_q07w_s52_sm_deep70_wcov: Q07 w_swing H52 small deep70+wiki_cov (test)
- s_q07w_s78_mi_ats_z1_cheap5: Q07 w_swing H78 micro ats_z1+cheap5 (test)
- s_q07w_s78_mi_ats_z1_mom6: Q07 w_swing H78 micro ats_z1+mom6 (test)
- s_q07w_s78_mi_cheap5_ins2_mom6: Q07 w_swing H78 micro cheap5+insider2+mom6 (test)
- s_q07w_s78_ml_deep70_glow_ins2: Q07 w_swing H78 midlarge deep70+gamma_low+insider2 (test)
- s_q07w_s78_ml_deep70_ins2_vix20: Q07 w_swing H78 midlarge deep70+insider2+stress_vix20 (test)
- s_q07w_s78_ml_deep70_mom6_wlow: Q07 w_swing H78 midlarge deep70+mom6+wiki_low (test)
- s_q07w_s78_ml_deep70_wcov: Q07 w_swing H78 midlarge deep70+wiki_cov (test)
- s_q07w_s78_sm_cheap5_ins2_vix20: Q07 w_swing H78 small cheap5+insider2+stress_vix20 (test)
- s_q07w_s78_sm_cheap5_wcov: Q07 w_swing H78 small cheap5+wiki_cov (test)
- s_q07w_s78_sm_deep70_ins2: Q07 w_swing H78 small deep70+insider2 (test)
- s_q07w_s78_sm_deep70_wcov: Q07 w_swing H78 small deep70+wiki_cov (test)
- s_1wsw_stress: 1W Swing stress pockets (test)

## Files in this package
- packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json
- packages/grokbot/q07-1w-swing-lz/evidence/load_800_stage2.json
- docs/Q07-1W-SWING-LZ-ALGORITHM.md (this file)

## Sanitization note
This copy was sanitized at 29 point(s) to pass the public-repo privacy gate; the private original in the source repo named in this doc is the verbatim source.
Sanitized files in this package:
- packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json: 29 occurrence(s) replaced
