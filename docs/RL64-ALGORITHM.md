# RL64 Algorithm

Created by GrokBot (installed by GrokBot; the cells are pre-existing Research Lab cells, not authored by GrokBot).

Algorithm derived from the code on 2026-10-29 (source: dwj9ddyvf6-hub/master-desk, commit dc2aa7c, tools/install_rl64.py, evidence/rl64_install.json, lz_engine/config/sleeves.json).

## What it is
The install of 64 Research Lab Q07 price-family weekly cells as paper sleeves on the TEST_MWJW book. The installer (tools/install_rl64.py) is additive only: it refuses any cell whose lane id or cell id already exists, never modifies existing rows, writes undo copies of the playbook and sleeve config first, and records the result in evidence/rl64_install.json (64 added, 0 skipped at this commit). The sleeves themselves are entries in lz_engine/config/sleeves.json (the full book file at this commit, 164 entries, is included verbatim); the 64 RL64 entries are listed below. Their fires are emitted by the sleeve feed composer through the same generic Q07 cell path as the pre-existing s_q07w_* cells, and they are executed by the Lazarus engine that reads this config.

## Entry and exit rules (from the packaged config entries)
- Kind: weekly (1w). Entry policy: fear_day.
- Entry window: max delay 65 minutes, window 5 sessions, capped limit day orders with a 5.0% limit band and 1.0% limit buffer, no-chase multiplier 1.02; both the stock and QQQ must be red (stock_red and qqq_red true).
- Exit: the sleeve feed fire's plan: 15% disaster stop / time exit; hold = 52 weeks (calendar weeks after the fire week, desk weekly time exit).
- Sizing: budget 1000 USD, 1 slot, position 1000 USD, cap 1.0% of DV20, minimum DV20 100000 USD.
- Per-cell parameters (horizon, family tags such as tierA, deep70, cheap5, mom6, stress_vix20, and the CONFIRMED research record with its sample size and edge interval) are carried in each entry's label and research fields in the packaged config, sourced from DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS and the corpus audit cited inside the entries. This doc does not restate per-cell numbers beyond the shared rules above.

## The 64 sleeves
- s_q07w_g52_mi_cheap5_tierA
- s_q07w_g78_mi_cheap5_tierA
- s_q07w_c78_mi_cheap5_mom6_tierA
- s_q07w_c78_mi_cheap5_tierA
- s_q07w_c52_mi_cheap5_deep70_tierA
- s_q07w_c78_sm_cheap5_tierA
- s_q07w_c52_mi_cheap5_tierA
- s_q07w_c52_sm_cheap5_mom6_tierA
- s_q07w_s78_sm_cheap5_deep70_vix20
- s_q07w_c52_mi_cheap5_mom6_tierA
- s_q07w_c78_mi_mom6_tierA
- s_q07w_c78_sm_cheap5_mom6_tierA
- s_q07w_c78_mi_tierA
- s_q07w_c78_mi_cheap5_deep70_tierA
- s_q07w_c52_mi_deep70_tierA
- s_q07w_c52_sm_cheap5_tierA
- s_q07w_s78_sm_cheap5_mom6_vix20
- s_q07w_g52_mi_tierA
- s_q07w_c78_mi_deep70_mom6_tierA
- s_q07w_c52_mi_deep70_mom6_tierA
- s_q07w_s78_sm_cheap5_vix20
- s_q07w_c52_sm_cheap5_mom6_vix20
- s_q07w_g52_mi_deep70_tierA
- s_q07w_g78_sm_mom6_vix20_tierA
- s_q07w_g78_mi_tierA
- s_q07w_c52_mi_mom6_tierA
- s_q07w_c78_sm_cheap5_deep70_tierA
- s_q07w_g52_mi_mom6_tierA
- s_q07w_g78_mi_cheap5_deep70_vix20
- s_q07w_s78_mi_cheap5_deep70_mom6
- s_q07w_g78_sm_cheap5_deep70
- s_q07w_g78_sm_vix20_tierA
- s_q07w_g78_sm_cheap5_deep70_mom6
- s_q07w_s78_mi_cheap5_mom6_vix20
- s_q07w_s78_mi_cheap5_mom6
- s_q07w_g78_mi_mom6_tierA
- s_q07w_g78_mi_cheap5_deep70_mom6
- s_q07w_g52_sm_cheap5_tierA
- s_q07w_g78_mi_deep70_tierA
- s_q07w_s52_sm_cheap5_deep70_vix20
- s_q07w_s52_mi_cheap5_deep70_vix20
- s_q07w_s52_sm_cheap5_mom6_vix20
- s_q07w_s52_sm_cheap5_vix20
- s_q07w_s52_mi_cheap5_deep70
- s_q07w_s52_mi_cheap5_vix20
- s_q07w_s52_mi_cheap5_deep70_mom6
- s_q07w_g52_sm_cheap5_deep70_mom6
- s_q07w_g52_sm_deep70_tierA
- s_q07w_s78_ml_cheap5
- s_q07w_g52_mi_cheap5_deep70
- s_q07w_s52_mi_cheap5
- s_q07w_s52_mi_cheap5_mom6
- s_q07w_g78_ml_mom6_tierA
- s_q07w_g52_mi_cheap5_deep70_mom6
- s_q07w_s78_ml_cheap5_vix20
- s_q07w_s78_ml_cheap5_mom6
- s_q07w_g52_ml_mom6_tierA
- s_q07w_g78_ml_mom6_vix20_tierA
- s_q07w_g78_ml_vix20_tierA
- s_q07w_g78_ml_deep70_tierA
- s_q07w_s52_ml_cheap5_vix20
- s_q07w_s52_ml_cheap5
- s_q07w_g52_ml_vix20_tierA
- s_q07w_g52_ml_cheap5

## Files in this package
- packages/grokbot/rl64/tools/install_rl64.py
- packages/grokbot/rl64/evidence/rl64_install.json
- packages/grokbot/rl64/lz_engine/config/sleeves.json
- docs/RL64-ALGORITHM.md (this file)

## Sanitization note
This copy was sanitized at 164 point(s) to pass the public-repo privacy gate; the private original in dwj9ddyvf6-hub/master-desk (or dwj9ddyvf6-hub/quant-research-backup for the backup sync package) is the verbatim source.
Sanitized files in this package:
- packages/grokbot/rl64/tools/install_rl64.py: 7 occurrence(s) replaced
- packages/grokbot/rl64/lz_engine/config/sleeves.json: 157 occurrence(s) replaced
