"""Lazarus fire-consumer engine (batch 1).

research-archive is unreachable from this box (V3-SCOPE 3.4), so these
sleeves consume ONLY ingested fires via the snapshot: view["lazarus_fires"]
(or view["extra"]["lazarus_fires"] / view["tensor_fires"]) — a list of
{sleeve_id, symbol, fired_at, price, target_price?, horizon_sessions?,
 horizon_hours?, cap_tier?, signal_tier?, color/family?, ml_pick?,
 qqq_red?, stock_red?}. For 1h/1d/1w this substitutes the desk's Tensor
bundle producer for the unreachable tracker latest_fires_v3.json —
recorded in FIDELITY-LEDGER.md. Position management is desk code here.
Fail-closed: no fresh matching fire => no entry; missing QQQ-red data
for QQQ-down sleeves => no entry.
"""
from __future__ import annotations
import json, os
from datetime import datetime, timezone, timedelta

SPECS = {
 "1h": dict(slots=30, capital=51750.0, cadence_s=300, session="rth",
   max_age_min=30, qqq_down=True, both_red=True, stop_pct=None,
   target_pct=None, horizon_sessions=5, horizon_from_fire=True),
 "1d": dict(slots=6, capital=10350.0, cadence_s=300, session="rth",
   max_age_min=60*48, qqq_down=True, stop_pct=0.15, target_pct=0.20,
   partial_pct=0.30, horizon_sessions=40),
 "1w": dict(slots=15, capital=19287.0, cadence_s=3600, session="rth",
   max_age_min=60*24*8, qqq_down=True, stop_pct=0.15,
   horizon_sessions=252),
 "1dc": dict(slots=68, capital=12500.0, cadence_s=300, session="rth",
   max_age_min=60*48, qqq_down=True, stop_pct=None,
   horizon_sessions=21, horizon_from_fire=True, family="cyan", tf="1D"),
 "1wa": dict(slots=17, capital=17250.0, cadence_s=3600, session="rth",
   max_age_min=60*24*8, qqq_down=True, stop_pct=0.15,
   horizon_sessions=252, family="cyan", tf="1W", cap_tier="small", signal_tier="A"),
 "s_1dg": dict(slots=17, capital=17000.0, cadence_s=300, session="rth",
   max_age_min=60*48, stop_pct=None, horizon_sessions=21,
   family="green", tf="1D", ml_pick=True),
 "s_1wlab": dict(slots=22, capital=22000.0, cadence_s=3600, session="rth",
   max_age_min=60*24*8, stop_pct=0.15, horizon_sessions=126,
   family="cyan", tf="1W"),
 "s_1wsw": dict(slots=1, capital=1000.0, cadence_s=3600, session="rth",
   max_age_min=60*24*8, qqq_down=True, stop_pct=0.15,
   horizon_sessions=126, family="swing", tf="1W"),
 "s_1wc_micro": dict(slots=1, capital=1000.0, cadence_s=3600, session="rth",
   max_age_min=60*24*8, stop_pct=0.15, horizon_sessions=252,
   family="cyan", tf="1W", cap_tier="micro", signal_tier="A"),
 "s_1wc_ml": dict(slots=4, capital=4000.0, cadence_s=3600, session="rth",
   max_age_min=60*24*8, stop_pct=0.15, horizon_sessions=252,
   family="cyan", tf="1W", cap_tiers=("mid","large","midlarge","mid/large"), signal_tier="A"),
 # ---- batch 2 (catalog inventory / frozen-rules; FIDELITY-LEDGER LAZ2) ----
 "s_1dgp5": dict(slots=1, capital=1000.0, cadence_s=300, session="rth",
   max_age_min=60*48, qqq_down=True, stop_pct=None, horizon_sessions=40,
   family="green", tf="1D", max_price=5.0),
 "s_rules_1d": dict(slots=44, capital=44000.0, cadence_s=300, session="rth",
   max_age_min=60*48, stop_pct=None, horizon_sessions=22,
   horizon_from_fire=True, horizon_plus_one=True),
 "s_rules_1w": dict(slots=6, capital=6000.0, cadence_s=3600, session="rth",
   max_age_min=60*24*8, qqq_down=True, stop_pct=0.15, horizon_sessions=27,
   horizon_from_fire=True, horizon_plus_one=True),
 "s_1wg_small": dict(slots=2, capital=2696.0, cadence_s=3600, session="rth",
   max_age_min=60*24*8, stop_pct=0.15, horizon_sessions=252,
   family="green", tf="1W", cap_tier="small", signal_tier="A"),
 "s_moonshot": dict(slots=10, capital=2581.0, cadence_s=3600, session="rth",
   max_age_min=60*24*8, stop_pct=0.15, horizon_sessions=252,
   family="cyan", tf="1W", max_price=14.94, max_price_inclusive=True,
   deep60=True),
 "s_1wsw_stress": dict(slots=1, capital=1335.0, cadence_s=3600, session="rth",
   max_age_min=60*24*8, stop_pct=0.15, horizon_sessions=252,
   family="swing", tf="1W", max_price=5.0, deep=True, min_vix=20.0),
}
INPUTS = ("lazarus_fires", "bars", "positions")

# ENH-LAZ-REPRICE-20261024 (Edge batch 1, IMPROVE): binding leak —
# entries sized and stop-anchored off the FIRE's print, which is up
# to 48h old (1d/1dc) or 8d old (1w/1wa) at decision time, while the
# market order fills at the CURRENT price. Measured on fixture:
# fire $10 vs current $12.50 -> qty 172 = $2,150 notional against a
# $1,725 slot budget (+24.6%) and a stop 32% below current instead of
# the designed 15%. Treatment (switch ON, default): size, stop and
# price_hint off the freshest completed bar close in the same
# snapshot; the fire print is only the fallback when no bars exist.
# The fire-price decision is kept as the paired shadow control
# record on the entry intent (enhance_exp). OFF restores the
# pre-change rule exactly.
EXP_ID_LAZ = "ENH-LAZ-REPRICE-20261024"
EXP_ID_LAZ19 = "ENH19-LAZ-BOUND-20261024"


def _bound_guard_on(view, ctx, sid):
    for src in ((ctx or {}).get("enhance"),
                ((view or {}).get("extra") or {}).get(f"{sid}_enh19"),
                ((view or {}).get("extra") or {}).get(f"{sid}_improve")):
        if isinstance(src, dict):
            per = src.get(sid) if isinstance(src.get(sid), dict) else src
            if isinstance(per, dict) and "bound_guard" in per:
                return bool(per["bound_guard"])
    return True


def _journal19(view, rec):
    j = ((view or {}).get("extra") or {}).get("enh19_journal")
    if isinstance(j, list):
        j.append(rec)

EXP_ID_LAZ25 = "ENH25-RULES-FRESH-20261024"

def _fresh_first_on(view, ctx, sid):
    """ENH25-RULES-FRESH switch: extra.<sid>_enh25.fresh_first (or
    ctx['enhance']), default ON; OFF restores producer list order."""
    for src in ((ctx or {}).get("enhance"),
                ((view or {}).get("extra") or {}).get(f"{sid}_enh25")):
        if isinstance(src, dict):
            per = src.get(sid) if isinstance(src.get(sid), dict) else src
            if isinstance(per, dict) and "fresh_first" in per:
                return bool(per["fresh_first"])
    return True

def _journal25(view, rec):
    j = ((view or {}).get("extra") or {}).get("enh25_journal")
    if isinstance(j, list):
        j.append(rec)


def _fresh_price_on(view, ctx, sid):
    # Engine-wide (all Lazarus fire-consumers share this leak and
    # this cure; sibling Edge batches 19/21 rely on it and carry
    # their own per-sleeve switches in the same entry path).
    for src in ((ctx or {}).get("enhance"),
                ((view or {}).get("extra") or {}).get(f"{sid}_improve")):
        if isinstance(src, dict):
            per = src.get(sid) if isinstance(src.get(sid), dict) else src
            if isinstance(per, dict) and "fresh_price" in per:
                return bool(per["fresh_price"])
    return True


def _fresh_px(view, sym):
    rows = _bars(view, sym)
    if rows:
        try: return float(rows[-1]["c"])
        except Exception: return None
    return None

def _now(view, ctx):
    raw = (view or {}).get("now") or (ctx or {}).get("now")
    if raw:
        d = datetime.fromisoformat(str(raw).replace("Z","+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def _parse_ts(raw):
    if not raw: return None
    try:
        d = datetime.fromisoformat(str(raw).replace("Z","+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception: return None

def _fires(view):
    v = view or {}
    for src in (v.get("lazarus_fires"), (v.get("extra") or {}).get("lazarus_fires"),
                v.get("tensor_fires"), (v.get("extra") or {}).get("fires")):
        if isinstance(src, list): return src
    return []

def _bars(view, sym, tf="1Day"):
    return ((view or {}).get("bars") or {}).get(f"{sym}|{tf}") or \
           ((view or {}).get("bars") or {}).get(sym) or []

def _red(view, sym):
    rows = _bars(view, sym)
    if len(rows) >= 2:
        try: return float(rows[-1]["c"]) < float(rows[-2]["c"])
        except Exception: return None
    if len(rows) == 1:
        try: return float(rows[-1]["c"]) < float(rows[-1]["o"])
        except Exception: return None
    return None

def _price(view, sym, fire=None):
    if fire and fire.get("price"):
        try: return float(fire["price"])
        except Exception: pass
    rows = _bars(view, sym)
    if rows:
        try: return float(rows[-1]["c"])
        except Exception: return None
    return None

def _sessions_held(view, opened, now):
    dates = ((view or {}).get("extra") or {}).get("session_dates") or []
    if not dates:
        rows = _bars(view, "SPY")
        dates = sorted({str(r.get("t",""))[:10] for r in rows if r.get("t")})
    od = opened.date().isoformat()
    if dates:
        return sum(1 for d in dates if od < d <= now.date().isoformat())
    # fallback: business days
    n, d = 0, opened.date()
    while d < now.date():
        d += timedelta(days=1)
        if d.weekday() < 5: n += 1
    return n

def _state_path(ctx):
    sd = (ctx or {}).get("state_dir")
    return os.path.join(sd, "laz_state.json") if sd else None

def _load_state(ctx):
    p = _state_path(ctx)
    if p and os.path.exists(p):
        try: return json.load(open(p))
        except Exception: return {}
    return {}

def _save_state(ctx, st):
    p = _state_path(ctx)
    if p:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh: json.dump(st, fh, sort_keys=True)

def evaluate(sleeve_id, view, ctx):
    spec = SPECS[sleeve_id]; view = view or {}
    now = _now(view, ctx)
    positions = view.get("positions") or []
    state = _load_state(ctx)
    out = []
    stamp = now.strftime("%Y%m%dT%H%M%S")
    # ---- exits first ----
    for p in positions:
        sym = p.get("symbol"); qty = p.get("qty")
        if not sym or not qty: continue
        entry_px = p.get("avg_price")
        cur = _price(view, sym)
        opened = _parse_ts(p.get("opened_at")) or now
        meta = state.get(sym) or {}
        horizon = int(meta.get("horizon_sessions") or spec["horizon_sessions"])
        target_px = meta.get("target_price")
        held = _sessions_held(view, opened, now)
        reason = None; exit_qty = qty
        if spec.get("stop_pct") and entry_px and cur and cur <= float(entry_px)*(1-spec["stop_pct"]):
            reason = f"{sleeve_id}_stop15"
        elif target_px and cur and cur >= float(target_px):
            reason = f"{sleeve_id}_target"
        elif spec.get("partial_pct") and entry_px and cur and cur >= float(entry_px)*(1+spec["partial_pct"]) and qty > 1:
            reason = f"{sleeve_id}_partial30_trail"; exit_qty = int(qty)//2
        elif spec.get("target_pct") and entry_px and cur and cur >= float(entry_px)*(1+spec["target_pct"]):
            reason = f"{sleeve_id}_target20"
        elif held >= horizon:
            reason = f"{sleeve_id}_time_exit_{horizon}s"
        if reason:
            out.append({"intent_id": f"{sleeve_id}-{stamp}-x{sym}",
                "kind":"exit","symbol":sym,"side":"sell","qty":exit_qty,
                "order_type":"market","limit_price":None,"stop_price":None,
                "reason":reason,"time_in_force":"day"})
            if exit_qty >= qty and sym in state:
                del state[sym]
    if out:
        _save_state(ctx, state); return out
    # ---- entries ----
    if len(positions) >= spec["slots"]: return []
    held_syms = {p.get("symbol") for p in positions}
    per_slot = spec["capital"]/spec["slots"]
    # ENH25-RULES-FRESH-20261024 (batch 25, rules lanes): slot
    # allocation iterated fires in PRODUCER LIST ORDER — a 48h-old
    # (1d) / 8d-old (1w) fire listed first crowded out a same-day
    # fire for the last slot (the Q07FRESH class, never applied to
    # this engine). ON (default): freshest fired_at first (stable).
    # OFF: producer list order exactly (pre-change).
    _fires_in = _fires(view)
    if sleeve_id in ("s_rules_1d", "s_rules_1w") and _fresh_first_on(view, ctx, sleeve_id):
        def _fk(f):
            if not isinstance(f, dict): return None
            if f.get("sleeve_id") and f["sleeve_id"] != sleeve_id: return None
            return _parse_ts(f.get("fired_at") or f.get("ts"))
        _cand = [f for f in _fires_in if _fk(f) is not None]
        if len(_cand) >= 2:
            _ordered = sorted(_cand, key=lambda f: _fk(f), reverse=True)
            _journal25(view, {"exp_id": EXP_ID_LAZ25, "sleeve": sleeve_id,
                "control_first": _cand[0].get("symbol"),
                "treatment_first": _ordered[0].get("symbol")})
            _ids = {id(f) for f in _cand}
            _fires_in = _ordered + [f for f in _fires_in if id(f) not in _ids]
    for fire in _fires_in:
        if not isinstance(fire, dict): continue
        if fire.get("sleeve_id") and fire["sleeve_id"] != sleeve_id: continue
        sym = fire.get("symbol")
        if not sym or sym in held_syms: continue
        if str(fire.get("side","buy")).lower() not in ("buy","long"): continue
        ft = _parse_ts(fire.get("fired_at") or fire.get("ts"))
        if ft is None: continue
        age_min = (now-ft).total_seconds()/60.0
        if age_min < 0 or age_min > spec["max_age_min"]: continue
        # family/tier/cap filters: enforce when the fire carries the field
        fam = str(fire.get("family") or fire.get("color") or "").lower()
        if spec.get("family") and fam and spec["family"] not in fam: continue
        tier = str(fire.get("signal_tier") or fire.get("tier") or "").upper()
        if spec.get("signal_tier") and tier and tier != spec["signal_tier"]: continue
        cap = str(fire.get("cap_tier") or "").lower()
        if cap:
            allowed = spec.get("cap_tiers") or ((spec["cap_tier"],) if spec.get("cap_tier") else ())
            if allowed and cap not in allowed: continue
        if spec.get("ml_pick") and fire.get("ml_pick") is False: continue
        # batch-2 additive filters (only when the spec names them;
        # batch-1 specs carry none of these keys => unchanged behavior)
        _tags = fire.get("tags") or {}
        def _tg(k, _f=fire, _t=_tags):
            return _f.get(k, _t.get(k))
        if spec.get("max_price") is not None:
            _px = _price(view, sym, fire)
            if _px is None: continue
            if spec.get("max_price_inclusive"):
                if _px > spec["max_price"]: continue
            elif _px >= spec["max_price"]: continue
        if spec.get("deep60") and not (_tg("deep60") or _tg("deep_pullback60")): continue
        if spec.get("deep") and not (_tg("deep") or _tg("deep70")): continue
        if spec.get("min_vix") is not None:
            _vix = _tg("vix")
            if _vix is None or float(_vix) < spec["min_vix"]: continue
        if spec.get("qqq_down"):
            qred = fire.get("qqq_red", fire.get("qqq_down"))
            if qred is None: qred = _red(view, "QQQ")
            if qred is not True: continue
        if spec.get("both_red"):
            sred = fire.get("stock_red")
            if sred is None: sred = _red(view, sym)
            if sred is not True: continue
        base_px = _price(view, sym, fire)
        if not base_px or base_px <= 0: continue
        px = base_px; rec = None; fresh = None
        if _fresh_price_on(view, ctx, sleeve_id):
            fresh = _fresh_px(view, sym)
            if fresh and fresh > 0 and fresh != base_px:
                px = fresh
                rec = {"exp_id": EXP_ID_LAZ, "sleeve": sleeve_id,
                       "symbol": sym, "control_price": base_px,
                       "treatment_price": fresh,
                       "control_qty": int(per_slot // base_px),
                       "treatment_qty": int(per_slot // fresh),
                       "control_stop": (round(base_px*(1-spec["stop_pct"]),4)
                                        if spec.get("stop_pct") else None),
                       "treatment_stop": (round(fresh*(1-spec["stop_pct"]),4)
                                          if spec.get("stop_pct") else None)}
        # ENH19: revalidate designed entry bounds at the EXECUTION
        # (fresh) price. Pre-change, max_price was checked on the fire
        # print and target_price never on entry: a fire at $10 with a
        # $11 target entered at a $12.50 fresh close (already past its
        # own target -> guaranteed immediate target-exit churn), and
        # s_1wsw_stress's <$5 gate passed on the fire print while the
        # fill printed >=$5. ON (default): refuse; OFF: pre-change.
        if _bound_guard_on(view, ctx, sleeve_id):
            _tgt = fire.get("target_price")
            _bound = None
            if _tgt and px >= float(_tgt):
                _bound = f"fresh {px} >= target {float(_tgt)}"
            if spec.get("max_price") is not None and fresh is not None:
                if spec.get("max_price_inclusive"):
                    if px > spec["max_price"]: _bound = f"fresh {px} > max {spec['max_price']}"
                elif px >= spec["max_price"]:
                    _bound = f"fresh {px} >= max {spec['max_price']}"
            if _bound:
                _journal19(view, {"exp_id": EXP_ID_LAZ19, "sleeve": sleeve_id,
                    "symbol": sym, "enhanced": "refuse_bound",
                    "shadow_faithful": "enter", "bound": _bound,
                    "control_price": base_px, "treatment_price": px})
                continue
        qty = int(per_slot // px)
        if qty < 1: continue
        horizon = int(fire.get("horizon_sessions") or spec["horizon_sessions"]) \
            if spec.get("horizon_from_fire") or fire.get("horizon_sessions") else spec["horizon_sessions"]
        if spec.get("horizon_plus_one") and fire.get("horizon_sessions"):
            horizon += 1  # frozen-rules books: exit at rule horizon + 1
        state[sym] = {"horizon_sessions": horizon,
                      "target_price": fire.get("target_price"),
                      "entry_at": now.isoformat()}
        _ent = {"intent_id": f"{sleeve_id}-{stamp}-{sym}",
            "kind":"entry","symbol":sym,"side":"buy","qty":qty,
            "order_type":"market","limit_price":None,
            "stop_price": (round(px*(1-spec["stop_pct"]),4) if spec.get("stop_pct") else None),
            "reason": f"{sleeve_id}_tensor_fire","time_in_force":"day",
            "price_hint": px}
        if rec:
            rec["treatment_qty"] = qty
            _ent["enhance_exp"] = {"exp_id": EXP_ID_LAZ, "records": [rec]}
        out.append(_ent)
        held_syms.add(sym)
        if len(positions)+len(out) >= spec["slots"]: break
    if out: _save_state(ctx, state)
    return out
