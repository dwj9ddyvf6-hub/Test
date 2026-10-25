"""Aster R19 crypto engine (batch 6). Source: TSV spec (archive staged
tree absent on this box at build time; ASTER-BUILD-MAP §6 names
r19_crypto.py + crypto_rules.json). Rules implemented verbatim from TSV:
NFS entry: completed 4h close > highest high of prior 20 bars AND an
actually-observed funding rate < 0. Absorption entry (TSV book 5 logic):
shock bar vol > 2*EMA20(vol, incl.), close<open, close<EMA50(close,
incl.); next bar close>open and close > shock midpoint; >=300 bars.
Exits: fixed16/fixed96 saved deadline (survives missing inputs);
lost_breakout = close < stored breakout level; normalization = funding
>= 0; normalization_failure = funding >= 0 AND close < lowest low of
prior 3 bars, executable no earlier than 4h after that signal bar
closes; structural policies carry the installed 96h max deadline
(assumption recorded in FIDELITY-LEDGER ASTER-B6). Sizing: fullcash =
slice cash net of 10bp fee; volume1pct = min(fullcash, 1% of preceding
4h bar volume). Funding is a declared producer input: absent => no
entry and sleeve is UNFED in the registry, never fake-fed."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from desk3.contract import Intent
FEE=0.001
SPECS={
 "aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct": dict(sym="ADAUSDT",fam="nfs",exit="fixed16",cap="volume1pct",hold_h=16),
 "aster_r19_adausdt_negative_funding_squeeze_fixed96_fullcash": dict(sym="ADAUSDT",fam="nfs",exit="fixed96",cap="fullcash",hold_h=96),
 "aster_r19_adausdt_negative_funding_squeeze_fixed96_volume1pct": dict(sym="ADAUSDT",fam="nfs",exit="fixed96",cap="volume1pct",hold_h=96),
 "aster_r19_adausdt_negative_funding_squeeze_lost_breakout_fullcash": dict(sym="ADAUSDT",fam="nfs",exit="lost_breakout",cap="fullcash",hold_h=96),
 "aster_r19_adausdt_negative_funding_squeeze_lost_breakout_volume1pct": dict(sym="ADAUSDT",fam="nfs",exit="lost_breakout",cap="volume1pct",hold_h=96),
 "aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash": dict(sym="ADAUSDT",fam="nfs",exit="normalization_failure",cap="fullcash",hold_h=96),
 "aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct": dict(sym="ADAUSDT",fam="nfs",exit="normalization_failure",cap="volume1pct",hold_h=96),
 "aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash": dict(sym="ADAUSDT",fam="nfs",exit="normalization",cap="fullcash",hold_h=96),
 "aster_r19_adausdt_negative_funding_squeeze_normalization_volume1pct": dict(sym="ADAUSDT",fam="nfs",exit="normalization",cap="volume1pct",hold_h=96),
 "aster_r19_enjusdt_absorption_base_fixed16_fullcash": dict(sym="ENJUSDT",fam="absorption",exit="fixed16",cap="fullcash",hold_h=16),
}
INPUTS=("bars","funding","positions")
EXP_ID="ENH-B6-LATCH-20261024"
def _enh_on(sid,view,ctx):
    """EDGE batch 6 switch: enhance_trigger_latch, default ON. OFF
    (ctx/view params/extra naming the sleeve or flat) restores the
    pre-change latest-bar-only structural exit scan exactly."""
    for src in ((ctx or {}),(view or {}).get("params") or {},
                (view or {}).get("extra") or {}):
        if isinstance(src,dict):
            sub=src.get(sid) if isinstance(src.get(sid),dict) else src
            if isinstance(sub,dict) and "enhance_trigger_latch" in sub:
                return bool(sub["enhance_trigger_latch"])
    return True
def _shadow_journal(ctx,sid,rec):
    sd=(ctx or {}).get("state_dir") if isinstance(ctx,dict) else None
    if not sd: return
    try:
        import json as _j,os as _o
        _o.makedirs(sd,exist_ok=True)
        with open(_o.path.join(sd,"enhance_journal.jsonl"),"a") as fh:
            fh.write(_j.dumps({"sleeve":sid,**rec},sort_keys=True)+"\n")
    except Exception: pass
def _latched_trigger(spec,brs,fund,now,opened,lvl):
    """EDGE batch 6 binding leak: the pre-change structural exits
    inspected ONLY the latest bar, so a failure bar that a later bar
    recovered from never exited — the position rode to the 96h
    deadline. Latched scan: every post-entry bar is inspected;
    lost_breakout triggers on any post-entry close below the stored
    level; normalization_failure triggers on any post-entry bar
    closing below its prior-3 lowest low once that bar's archive
    execution delay has elapsed (now >= bar t + 8h) with funding
    currently normalized (only the current print is observable;
    recorded in proof/enhance). Returns the trigger bar index."""
    for j,b in enumerate(brs):
        t=_ts(b.get("t"))
        if t is None: continue
        if opened is not None and t+timedelta(hours=4)<=opened: continue
        if spec["exit"]=="lost_breakout" and lvl is not None:
            if float(b["c"])<float(lvl): return j
        elif spec["exit"]=="normalization_failure" and fund is not None \
                and fund>=0 and j>=3:
            if float(b["c"])<min(float(x["l"]) for x in brs[j-3:j]) \
                    and now>=t+timedelta(hours=8): return j
    return None
def _bars(view,sym):
    m=view.get("bars") or {}
    for k in (f"{sym}|4Hour",f"{sym}|4h",f"{sym}|240min",sym):
        if m.get(k): return sorted(m[k],key=lambda r:str(r.get("t")))
    return []
def _funding(view,sym):
    f=view.get("funding")
    if isinstance(f,dict):
        v=f.get(sym)
        if isinstance(v,dict): v=v.get("rate")
        if v is not None: return float(v)
    e=view.get("extra") or {}
    if e.get("funding_rate") is not None: return float(e["funding_rate"])
    return None
def _now(view,ctx):
    n=view.get("now") or (ctx or {}).get("now") or "2026-10-24T00:00:00+00:00"
    d=n if isinstance(n,datetime) else datetime.fromisoformat(str(n).replace("Z","+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
def _ts(s):
    try: return datetime.fromisoformat(str(s).replace("Z","+00:00"))
    except Exception: return None
def _ema(vals,n):
    k=2/(n+1); out=[]
    for i,v in enumerate(vals):
        out.append(v if i==0 else v*k+out[-1]*(1-k))
    return out
def _absorption(brs):
    if len(brs)<300: return False
    vols=[float(b["v"]) for b in brs]; closes=[float(b["c"]) for b in brs]
    ev=_ema(vols,20); ec=_ema(closes,50); s=brs[-2]; c=brs[-1]
    shock=float(s["v"])>2*ev[-2] and float(s["c"])<float(s["o"]) and float(s["c"])<ec[-2]
    mid=(float(s["h"])+float(s["l"]))/2
    return shock and float(c["c"])>float(c["o"]) and float(c["c"])>mid
def evaluate(sid,view,ctx=None):
    view=view or {}; spec=SPECS[sid]; sym=spec["sym"]; now=_now(view,ctx)
    brs=_bars(view,sym); fund=_funding(view,sym)
    poss=[p for p in (view.get("positions") or []) if float(p.get("qty") or 0)!=0]
    out=[]
    for p in poss:
        qty=abs(float(p["qty"])); opened=_ts(p.get("opened_at") or p.get("entry_time") or "")
        held=(now-opened).total_seconds()/3600 if opened else float(p.get("age_hours") or 0)
        reason=None
        if held>=spec["hold_h"]: reason=f"aster_deadline_{spec['exit']}_{spec['hold_h']}h held={held:.1f}h"
        elif spec["exit"]=="lost_breakout" and brs:
            lvl=p.get("breakout_level") or p.get("entry_breakout_level")
            if lvl is not None and float(brs[-1]["c"])<float(lvl): reason=f"aster_lost_breakout close={brs[-1]['c']} level={lvl}"
            elif lvl is not None and _enh_on(sid,view,ctx):
                j=_latched_trigger(spec,brs,fund,now,opened,lvl)
                if j is not None:
                    reason=f"aster_lost_breakout_latched bar={j} close={brs[j]['c']} level={lvl}"
                    _shadow_journal(ctx,sid,{"exp_id":EXP_ID,"kind":"exit",
                        "control_exit":False,"treatment_exit":True,
                        "trigger_bar":j,"rule":"lost_breakout_latch"})
        elif spec["exit"]=="normalization" and fund is not None and fund>=0:
            reason=f"aster_funding_normalized rate={fund}"
        elif spec["exit"]=="normalization_failure" and fund is not None and fund>=0 and len(brs)>=4:
            if float(brs[-1]["c"])<min(float(b["l"]) for b in brs[-4:-1]):
                end=_ts(brs[-1].get("t"))
                if end and now>=end+timedelta(hours=8): reason="aster_normalization_failure_delayed"
            if reason is None and _enh_on(sid,view,ctx):
                j=_latched_trigger(spec,brs,fund,now,opened,None)
                if j is not None:
                    reason=f"aster_normalization_failure_latched bar={j}"
                    _shadow_journal(ctx,sid,{"exp_id":EXP_ID,"kind":"exit",
                        "control_exit":False,"treatment_exit":True,
                        "trigger_bar":j,"rule":"normalization_failure_latch"})
        if reason: out.append(Intent(kind="exit",symbol=sym,qty=qty,price_hint=float(brs[-1]["c"]) if brs else None,reason=f"{sid} exit: {reason}",side="sell",position_intent="sell_to_close"))
    if out or poss: return out
    if spec["fam"]=="nfs":
        if fund is None or fund>=0 or len(brs)<21: return []
        if not float(brs[-1]["c"])>max(float(b["h"]) for b in brs[-21:-1]): return []
    else:
        if not _absorption(brs): return []
    price=float(brs[-1]["c"]); cash=float((view.get("slice") or {}).get("cash_usd") or 10000.0)
    qty=cash*(1-FEE)/price
    if spec["cap"]=="volume1pct": qty=min(qty,0.01*float(brs[-2]["v"]))
    if qty<=0: return []
    qty=int(qty)  # v3 dispatcher: ADAUSDT/ENJUSDT are not fractional symbols; whole-unit floor (ledger ASTER-B6)
    if qty<=0: return []
    return [Intent(kind="enter",symbol=sym,qty=qty,price_hint=price,reason=f"{sid} entry: {spec['fam']} breakout/absorption close={price} funding={fund} cap={spec['cap']}",side="buy",position_intent="buy_to_open")]
