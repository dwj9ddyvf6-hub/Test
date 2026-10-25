"""Lazarus Midna fire-consumer engine (batch 9).

Sources: CSV row producer=sleeve_midna, fire file
shadow/paper_sleeve/live/midna/midna_fires_v1.json (research-archive,
UNREACHABLE from this box per V3-SCOPE 3.4); catalog 4.2 rule sketches.
Substitution recorded in FIDELITY-LEDGER.md: fires are consumed via the
desk's Tensor bundle producer channel (view["tensor"] / view["extra"]
midna_fires / view["midna_fires"]) using the same validated fire schema
{sleeve_id,symbol,family,timeframe,date,price}. Fail-closed if absent/stale.
Position management is desk code here; signal generation stays upstream.
"""
from __future__ import annotations
from datetime import datetime, timezone, date

SPECS={
 "s_mn_w_cyan_breadth": dict(family="cyan", tf="1W", hold_sessions=126, stop=None, gate="breadth", budget=1000.0),
 "s_mn_w_cyan_vix": dict(family="cyan", tf="1W", hold_sessions=252, stop=None, gate="vix_mid", budget=1000.0),
 "s_mn_d_green_band": dict(family="green", tf="1D", hold_sessions=21, stop=None, gate="band", budget=1000.0),
 "s_mn_w_green_smh": dict(family="green", tf="1W", hold_sessions=126, stop=None, gate="smh_calm", budget=1000.0),
 "s_mn_hourly_1w": dict(family=None, tf="1W", hold_sessions=260, stop=0.15, gate=None, budget=1000.0),
}
INPUTS=("tensor","bars","positions")
EXP_ID_MN19 = "ENH19-MN-GREENBAND-REPRICE-20261024"
EXP_ID_MN20 = "ENH20-MN-XSTALE-20261024"


def _mn20_last_date(b):
    if not b:
        return None
    t = b[-1].get("t")
    try:
        if isinstance(t, (int, float)):
            return datetime.fromtimestamp(float(t) + 4 * 3600, tz=timezone.utc).date()
        return date.fromisoformat(str(t)[:10])
    except (TypeError, ValueError, OSError):
        return None


def _mn20_refused(extra, sid, view, sym, bars):
    """ENH20 (second look; ENH19 repriced off the fresh close): the
    'fresh' close is whatever bar the snapshot last carried -- a
    symbol whose feed stopped days before the rest of the snapshot
    still entered, gated/sized off that dead close. ON (default):
    refuse when sym's last bar lags the universe's latest bar by
    >4 days. OFF: extra {sid}_enh20.xstale_gate=False."""
    cfg = extra.get(f"{sid}_enh20") or {}
    if cfg.get("xstale_gate", True) is False:
        return False
    mine = _mn20_last_date(bars)
    if mine is None:
        return False
    dates = []
    for v in (view.get("bars") or {}).values():
        d = _mn20_last_date(v)
        if d is not None:
            dates.append(d)
    if len(dates) < 2:
        return False
    lag = (max(dates) - mine).days
    if lag <= 4:
        return False
    j = extra.get("enh20_journal")
    if isinstance(j, list):
        j.append({"exp_id": EXP_ID_MN20, "sleeve": sid, "symbol": sym,
                  "enhanced": "refuse_xstale_entry",
                  "shadow_faithful": "enter", "lag_days": lag})
    return True


def _reprice_on(extra, sid):
    for src in (extra.get(f"{sid}_enh19"), extra.get(f"{sid}_improve")):
        if isinstance(src, dict) and "fresh_price" in src:
            return bool(src["fresh_price"])
    return True
PRODUCERS=({"name":"tensor_bundle","outputs":("tensor",),"freshness_sla_s":86400},
 {"name":"bars","outputs":("bars",),"freshness_sla_s":900},
 {"name":"broker_readback","outputs":("positions",),"freshness_sla_s":900})

def _bars(view,sym):
    m=view.get("bars") or {}
    for k in (f"{sym}|1Day",f"{sym}|1D",sym,f"{sym}|1Week",f"{sym}|1W"):
        if m.get(k): return m[k]
    return []
def _extra(view,ctx):
    e={}
    e.update((ctx or {}).get("extra") or {} if isinstance(ctx,dict) else {})
    e.update(view.get("extra") or {})
    # ctx params extra
    if isinstance(ctx,dict) and isinstance(ctx.get("params"),dict):
        e.update(ctx["params"].get("extra") or {})
    return e
def _fires(view,extra):
    for src in (view.get("midna_fires"), view.get("fires"), extra.get("midna_fires"), extra.get("fires")):
        if isinstance(src,list): return src
        if isinstance(src,dict) and isinstance(src.get("fires"),list): return src["fires"]
    t=view.get("tensor") or view.get("tensor_bundle") or {}
    if isinstance(t,list): return t
    if isinstance(t,dict):
        for k in ("fires","midna_fires"):
            if isinstance(t.get(k),list): return t[k]
        # bundle sleeves dict
        sv=t.get("sleeves") or {}
        for sid,v in sv.items():
            if isinstance(v,dict) and isinstance(v.get("fires"),list): return v["fires"]
            if isinstance(v,list): return v
    return []
def _now(view,ctx):
    n=(view.get("now") or (ctx or {}).get("now") or (ctx or {}).get("session") or "2026-10-24")
    if isinstance(n,datetime): return n
    try: return datetime.fromisoformat(str(n).replace("Z","+00:00"))
    except Exception: return datetime(2026,10,24,tzinfo=timezone.utc)
def _sess(view,ctx):
    s=(ctx or {}).get("session") if isinstance(ctx,dict) else None
    return str(s or _now(view,ctx).date().isoformat())[:10]
def _age(pos,bars):
    for k in ("sessions_held","age_sessions","held_sessions","bars_held"):
        if pos.get(k) is not None: return int(pos[k])
    if pos.get("age_weeks") is not None: return int(pos["age_weeks"])*5
    if pos.get("held_weeks") is not None: return int(pos["held_weeks"])*5
    ed=str(pos.get("entry_date") or pos.get("opened_at") or "")[:10]
    if ed and bars:
        return sum(1 for b in bars if str(b.get("t",""))[:10]>ed or (isinstance(b.get("t"),(int,float)) and datetime.fromtimestamp(float(b["t"]),tz=timezone.utc).date().isoformat()>ed))
    return 0

def evaluate(sleeve_id, view, ctx=None):
    view=view or {}; ctx=ctx or {}
    spec=SPECS[sleeve_id]; extra=_extra(view,ctx); sess=_sess(view,ctx)
    now=_now(view,ctx); stamp=now.strftime("%Y%m%dT%H%M%S")
    positions=[p for p in (view.get("positions") or []) if float(p.get("qty") or 0)!=0]
    out=[]; n=0
    def intent(kind,sym,side,qty,reason,price):
        nonlocal n; n+=1
        return {"intent_id":f"{sleeve_id}-{stamp}-{n}","kind":kind,"symbol":sym,"side":side,"qty":int(qty),"order_type":"market","limit_price":None,"stop_price":None,"reason":reason,"time_in_force":"day","position_intent":"buy_to_open" if kind=="entry" else "sell_to_close","price_hint":float(price) if price else None}
    # Exits first
    for p in positions:
        sym=p["symbol"]; bars=_bars(view,sym); price=float(bars[-1]["c"]) if bars else float(p.get("avg_price") or 0)
        entry=float(p.get("avg_price") or p.get("entry_px") or price or 0); age=_age(p,bars)
        if spec["stop"] and entry>0 and price<=entry*(1-spec["stop"]):
            out.append(intent("exit",sym,"sell",abs(float(p["qty"])),f"{sleeve_id} exit: stop_15pct entry={entry:.2f} price={price:.2f}",price)); continue
        if age>=spec["hold_sessions"]:
            label="52_weeks" if sleeve_id=="s_mn_hourly_1w" else f"{spec['hold_sessions']}_sessions"
            out.append(intent("exit",sym,"sell",abs(float(p["qty"])),f"{sleeve_id} exit: time_{label} age_sessions={age}",price)); continue
    if out: return out
    if positions: return []  # max 1 slot
    # Entry gates
    fires=_fires(view,extra)
    if not fires: return []
    for f in fires:
        if not isinstance(f,dict): continue
        if f.get("sleeve_id") and f["sleeve_id"]!=sleeve_id: continue
        fam=str(f.get("family") or f.get("kind") or f.get("signal") or "").lower()
        if spec["family"] and spec["family"] not in fam: continue
        tf=str(f.get("timeframe") or f.get("tf") or "").upper()
        if tf and tf not in (spec["tf"], "1W" if spec["tf"]=="1W" else "1D", "WEEKLY" if spec["tf"]=="1W" else "DAILY"): 
            # normalize: accept 1W/W, 1D/D
            if not ((spec["tf"]=="1W" and tf in ("W","WEEK")) or (spec["tf"]=="1D" and tf in ("D","DAY"))): continue
        sym=f.get("symbol"); 
        if not sym: continue
        fdate=str(f.get("date") or f.get("fire_date") or f.get("ts") or "")[:10]
        if fdate:
            try:
                age_d=(date.fromisoformat(sess)-date.fromisoformat(fdate)).days
                if age_d<0 or age_d>10: continue
            except Exception: continue
        bars=_bars(view,sym)
        if _mn20_refused(extra,sleeve_id,view,sym,bars): continue
        fire_px=float(f.get("price") or 0)
        fresh_px=float(bars[-1]["c"]) if bars else 0.0
        # ENH19: this engine priced + band-gated entries off the FIRE
        # print (up to 10 days old) while fills print at the current
        # close -- the lazarus.py reprice cure never reached it. ON
        # (default): gate + size off the fresh close; OFF: fire print.
        if _reprice_on(extra,sleeve_id) and fresh_px>0:
            price=fresh_px
        else:
            price=fire_px or fresh_px
        if price<=0: continue
        gate=spec["gate"]
        if gate=="band" and not (10.0<=price<=20.0): continue
        if gate=="breadth":
            b=extra.get("breadth_pct", extra.get("market_breadth_pct"))
            if b is None:
                # derive from extra breadth dict
                b=(extra.get("breadth") or {}).get("pct") if isinstance(extra.get("breadth"),dict) else None
            if b is None or float(b)<0.50: continue
        if gate=="vix_mid":
            v=extra.get("vix_close", extra.get("vix"))
            if v is None:
                vb=_bars(view,"VIX") or _bars(view,"^VIX")
                v=float(vb[-1]["c"]) if vb else None
            if v is None or not (12.0<=float(v)<=25.0): continue
        if gate=="smh_calm":
            smh=_bars(view,"SMH")
            calm=extra.get("smh_calm")
            if calm is not None:
                if not calm: continue
            elif len(smh)>=21:
                r=smh[-1]["c"]/smh[-21]["c"]-1
                if abs(r)>0.05: continue
            else: continue
        qty=int(spec["budget"]//price)
        if qty<1: continue
        _ent=intent("entry",sym,"buy",qty,f"{sleeve_id} entry: tensor_{spec['family'] or 'weekly'}_{spec['tf']} fire={fdate or sess} price={price:.2f} gate={gate or 'none'}",price)
        if fire_px>0 and price!=fire_px:
            _ent["enhance_exp"]={"exp_id":EXP_ID_MN19,"records":[{"exp_id":EXP_ID_MN19,"sleeve":sleeve_id,"symbol":sym,"control_price":fire_px,"treatment_price":price,"control_qty":int(spec["budget"]//fire_px),"treatment_qty":qty}]}
        out.append(_ent)
        break
    return out
