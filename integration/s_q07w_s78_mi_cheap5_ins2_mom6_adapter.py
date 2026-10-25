"""v3 sleeve module for s_q07w_s78_mi_cheap5_ins2_mom6 — Lazarus Q07 alt-data confluence lane
(batch 6, authored for v3; no v2 source exists).

Catalog (SLEEVE-CATALOG-CONSOLIDATED-2026-10-23.md section 4.1): Tensor
1W swing signal, mi cap band, filters ('cheap5', 'ins2', 'mom6'); buy only on a
QQQ-down day within 5 sessions of the signal; exit on a 15% stop or at
the 78-week horizon; 1 slot at $1,000. CSV status for this lane:
sleeve_feed composer (tracker ledger + alt-data tags). Logic lives in desk3/q07_engine.py (one engine, per-lane spec —
the lanes differ only in family/band/filters/horizon, exactly as the
catalog table does). INPUTS is the producer-registry declaration.
"""
from desk3.q07_engine import evaluate_q07

SLEEVE_ID = "s_q07w_s78_mi_cheap5_ins2_mom6"
SPEC = {"id": "s_q07w_s78_mi_cheap5_ins2_mom6", "family": "swing", "horizon_wk": 78,
        "band": "mi", "filters": ('cheap5', 'ins2', 'mom6')}
INPUTS = ["sleeve_fires", "bars_1day", "vix", "positions"]


def evaluate(view, ctx):
    return evaluate_q07(SPEC, view, ctx)
