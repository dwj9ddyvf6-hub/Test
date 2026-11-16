import sys, json
root = sys.argv[1]  # tree containing core/
import os
_gi = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inputs")
sys.path.insert(0, root)
from core import setup_call, setups_curator
out = {}
out["fmt_r"] = [setup_call.fmt_r(x) for x in [0,0.5,1,1.234,2.0,-0.75,10.5]]
out["item_class"] = [setup_call.item_class(k) for k in ["agreement","structure","momentum","unknown_x"]]
out["scoring_method"] = setups_curator.scoring_method_table()
out["families"] = setups_curator.FAMILIES
setups_doc = json.load(open(_gi + "/setups_latest.json"))
briefs_doc = json.load(open(_gi + "/setup_briefs.json"))
calls, geo = {}, {}
for sym, brief in sorted(briefs_doc["briefs"].items()):
    setup = next((s for s in setups_doc["setups"]+setups_doc.get("entered",[])+setups_doc.get("completed",[]) if s.get("symbol")==sym), {"symbol": sym})
    try:
        c = setup_call.compose_call(setup, brief.get("plan"), brief.get("desk_read"), brief.get("levels"), bool(setup.get("entered")), elliott=brief.get("elliott"))
    except Exception as e:
        c = {"ERROR": f"{type(e).__name__}: {e}"}
    calls[sym] = c
    lv = brief.get("levels") or {}
    bars = [{"c": v, "h": v*1.01, "l": v*0.99, "o": v, "v": 1000} for v in (brief.get("spark_closes") or [])]
    atr = setups_curator._atr(bars) if len(bars) >= 15 else None
    geo[sym] = {
        "stop_prob": setups_curator.stop_geometry_problem(lv.get("entry"), lv.get("stop"), setup.get("side","long")),
        "target_prob": setups_curator.target_geometry_problem(lv.get("entry"), lv.get("target"), setup.get("side","long")),
        "underlying": setups_curator.underlying_of(sym),
        "atr": atr,
        "ran_past": setups_curator.ran_past_entry(lv.get("entry"), lv.get("stop"), atr, lv.get("last_close")) if atr else None,
        "market_ctx_partial": setups_curator.market_context(bars, bars, {"close": 20.0, "change_pct": 1.0}),
    }
out["calls"] = calls; out["geo"] = geo
# publish merge (the terminal integration path)
try:
    from core import setups_publish
    merged, *rest = setups_publish.merge_setups_into_snapshot({}, setups_doc, briefs_doc), None
    out["merged_keys"] = sorted(merged.keys())
    out["merged"] = merged
except Exception as e:
    out["merged_error"] = f"{type(e).__name__}: {e}"
sys.stdout.write(json.dumps(out, sort_keys=True, default=str))
