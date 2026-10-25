"""Aster batch 14 engine — C1 HOT_RESERVE_25 + G4 x9 (TSV 136-145).

Source read directly this pass (archive present at
~/workspace/.scratch-ausar-archive/handoff-20261024):
source/backend/r19_tensor.py passes()/evaluate() + tensor/RULES.json.
- G4 passes(): 'buy-green' in primary markers, native_close<=10,
  depth60>=70, ret60>=0, vol20>=0.09, dv20>=2e6; volatility gate
  (atr_ratio<=1)==(vol=='cool') -> cool atr<=1, hot atr>1, all any.
- C1 passes(): 'buy-cyan', close<=5, ret60>=31, vol20>=0.07, dv20>=2M
  (same vol gate).
- evaluate(): entry session = first session after signal_end, +1 when
  capital_mode in (delay, reserve); 52-week scheduled exit (exit_at
  deadline on the position, modelled here as 260 sessions_held);
  NO stop / profit cap (RULES risk text). Reserve mode sells the QQQ
  reserve leg to fund the ticket shortage before entry.
Fires consume canonical Tensor products via the v3 tensor bundle
channel (Tensor ENGINE untouched). Ticket: source $4,000/$10,000 on a
$100k book -> $400/$1,000 on the $10k v3 slice.
"""
from __future__ import annotations
from datetime import datetime, timezone, date

SPECS={
 "aster_tensor_c1_reserve_hot_25": dict(family="C1", capital_mode="reserve", volatility="hot", slots=25, ticket=400.0),
 "aster_tensor_g4_cash_all_10": dict(family="G4", capital_mode="cash", volatility="all", slots=10, ticket=1000.0),
 "aster_tensor_g4_cash_all_25": dict(family="G4", capital_mode="cash", volatility="all", slots=25, ticket=400.0),
 "aster_tensor_g4_delay_all_25": dict(family="G4", capital_mode="delay", volatility="all", slots=25, ticket=400.0),
 "aster_tensor_g4_reserve_all_10": dict(family="G4", capital_mode="reserve", volatility="all", slots=10, ticket=1000.0),
 "aster_tensor_g4_reserve_all_25": dict(family="G4", capital_mode="reserve", volatility="all", slots=25, ticket=400.0),
 "aster_tensor_g4_cash_cool_25": dict(family="G4", capital_mode="cash", volatility="cool", slots=25, ticket=400.0),
 "aster_tensor_g4_delay_cool_25": dict(family="G4", capital_mode="delay", volatility="cool", slots=25, ticket=400.0),
 "aster_tensor_g4_reserve_cool_25": dict(family="G4", capital_mode="reserve", volatility="cool", slots=25, ticket=400.0),
 "aster_tensor_g4_cash_hot_25": dict(family="G4", capital_mode="cash", volatility="hot", slots=25, ticket=400.0),
}
HOLD_SESSIONS=260
INPUTS=("tensor","bars","positions")
PRODUCERS=({"name":"tensor_bundle","outputs":("tensor",),"freshness_sla_s":86400},
 {"name":"bars","outputs":("bars",),"freshness_sla_s":900},
 {"name":"broker_readback","outputs":("positions",),"freshness_sla_s":900})

EXP_ID="ENH-TENSOR14-REPRICE-20261024"
def _reprice_on(view,ctx,sid):
    """ENH (Edge batch 12): execution-price revalidation switch.
    Default ON; OFF restores the pre-change fire-price rule exactly."""
    for src in ((ctx or {}).get("enhance"), (view.get("extra") or {}).get(f"{sid}_improve")):
        if isinstance(src,dict):
            per=src.get(sid) if isinstance(src.get(sid),dict) else src
            if isinstance(per,dict) and "exec_reprice" in per: return bool(per["exec_reprice"])
    return True

def _now(view,ctx):
    n=view.get("now") or (ctx or {}).get("now") or "2026-10-24T15:00:00"
    if isinstance(n,datetime): return n
    try: return datetime.fromisoformat(str(n).replace("Z","+00:00"))
    except Exception: return datetime(2026,10,24,tzinfo=timezone.utc)
def _sess(view,ctx):
    s=(ctx or {}).get("session") if isinstance(ctx,dict) else None
    return str(s or _now(view,ctx).date().isoformat())[:10]
def _bars(view,sym):
    m=view.get("bars") or {}
    for k in (f"{sym}|1Day",f"{sym}|1D",sym):
        if m.get(k): return m[k]
    return []
def _fires(view):
    t=view.get("tensor")
    if isinstance(t,list): return t
    if isinstance(t,dict) and isinstance(t.get("fires"),list): return t["fires"]
    if isinstance(view.get("fires"),list): return view["fires"]
    e=view.get("extra") or {}
    return e["fires"] if isinstance(e.get("fires"),list) else []
def _age(p):
    for k in ("sessions_held","age_sessions","held_sessions"):
        if p.get(k) is not None: return int(p[k])
    if p.get("weeks_held") is not None: return int(p["weeks_held"])*5
    return 0
def _vol_ok(spec,f):
    if spec["volatility"]=="all": return True
    ar=f.get("atr_ratio")
    if ar is None: return False
    return (float(ar)<=1)==(spec["volatility"]=="cool")  # source passes() exact
def _passes(spec,f,price):
    markers=f.get("markers") or f.get("primary_markers") or []
    sig=str(f.get("signal") or f.get("event") or "").lower()
    adv=f.get("adv_usd", f.get("avg_dollar_volume", f.get("dv20")))
    if adv is None or float(adv)<2_000_000: return False
    if not _vol_ok(spec,f): return False
    if spec["family"]=="G4":
        if not ("buy-green" in markers or "green" in sig): return False
        if price>10: return False
        d=f.get("depth60", f.get("depth"))
        if d is None or float(d)<70: return False
        if f.get("ret60") is None or float(f["ret60"])<0: return False
        if f.get("vol20") is None or float(f["vol20"])<0.09: return False
        return True
    # C1
    if not ("buy-cyan" in markers or "cyan" in sig): return False
    if price>5: return False
    if f.get("ret60") is None or float(f["ret60"])<31: return False
    if f.get("vol20") is None or float(f["vol20"])<0.07: return False
    return True

def evaluate(sleeve_id, view, ctx=None):
    view=view or {}; ctx=ctx or {}
    spec=SPECS[sleeve_id]; now=_now(view,ctx); sess=_sess(view,ctx)
    stamp=now.strftime("%Y%m%dT%H%M%S")
    positions=[p for p in (view.get("positions") or []) if float(p.get("qty") or 0)!=0]
    out=[]; n=0
    def intent(kind,sym,side,qty,reason,price):
        nonlocal n; n+=1
        return {"intent_id":f"{sleeve_id}-{stamp}-{n}","kind":kind,"symbol":sym,"side":side,"qty":qty,"order_type":"market","limit_price":None,"stop_price":None,"reason":reason,"time_in_force":"day","position_intent":"buy_to_open" if kind=="entry" else "sell_to_close","price_hint":float(price) if price else None}
    reserve=spec["capital_mode"]=="reserve"
    # Designed exit ONLY: 52-week scheduled deadline. No stop/target.
    for p in positions:
        sym=p["symbol"]
        if reserve and sym=="QQQ": continue
        bars=_bars(view,sym); price=float(bars[-1]["c"]) if bars else float(p.get("avg_price") or 0)
        due=_age(p)>=HOLD_SESSIONS
        ea=p.get("exit_at") or p.get("exit_deadline")
        if ea and sess>=str(ea)[:10]: due=True
        if due:
            out.append(intent("exit",sym,"sell",abs(float(p["qty"])),f"{sleeve_id} exit: week52_deadline sessions_held={_age(p)}",price))
    if out: return out
    held={p["symbol"] for p in positions if not (reserve and p["symbol"]=="QQQ")}
    if len(held)>=spec["slots"]: return []
    exp_records=[]
    for f in _fires(view):
        if not isinstance(f,dict): continue
        if f.get("sleeve_id") and f["sleeve_id"]!=sleeve_id: continue
        sym=f.get("symbol")
        if not sym or sym in held: continue
        price=float(f.get("price") or 0)
        if price<=0 or not _passes(spec,f,price): continue
        fdate=str(f.get("date") or f.get("fire_date") or f.get("signal_end") or "")[:10]
        if spec["capital_mode"] in ("delay","reserve") and fdate:
            try:
                if (date.fromisoformat(sess)-date.fromisoformat(fdate)).days<1: continue
            except Exception: continue
        # ENH batch 12: same stale-fire pricing leak as batch 13 —
        # revalidate the family cap (C1 <=5, G4 <=10) and size off the
        # latest close when a current bar is available (switch ON).
        eprice=price; rec=None
        if _reprice_on(view,ctx,sleeve_id):
            fb=_bars(view,sym); cur=float(fb[-1]["c"]) if fb else None
            if cur and cur>0:
                cap=5.0 if spec["family"]=="C1" else 10.0
                rec={"exp_id":EXP_ID,"symbol":sym,"fire_price":price,
                     "current_price":cur,"control_enter":True,
                     "control_qty":int(spec["ticket"]//price),"switch_on":True}
                if cur>cap:
                    rec["treatment_enter"]=False; rec["treatment_qty"]=0
                    rec["refusal"]=f"current_price>{cap:g}_cap"
                    exp_records.append(rec); continue
                eprice=cur; rec["treatment_enter"]=True
                rec["treatment_qty"]=int(spec["ticket"]//cur)
        qty=int(spec["ticket"]//eprice)
        if qty<1: continue
        if reserve:
            for p in positions:
                if p["symbol"]=="QQQ":
                    qb=_bars(view,"QQQ"); qp=float(qb[-1]["c"]) if qb else float(p.get("avg_price") or 0)
                    if qp>0:
                        sq=min(abs(float(p["qty"])), int(spec["ticket"]//qp) or 1)
                        out.append(intent("exit","QQQ","sell",sq,f"{sleeve_id} exit: qqq_reserve_funding ticket={spec['ticket']:.0f}",qp))
                    break
        ent=intent("entry",sym,"buy",qty,f"{sleeve_id} entry: tensor_{spec['family'].lower()} mode={spec['capital_mode']} vol={spec['volatility']} ticket={spec['ticket']:.0f} price={eprice:.2f} fire={fdate or sess}" + (f" reprice fire={price:.2f} cur={eprice:.2f}" if rec else ""),eprice)
        if rec: exp_records.append(rec)
        if exp_records: ent["enhance_exp"]={"exp_id":EXP_ID,"records":exp_records}
        out.append(ent)
        return out
    return out
