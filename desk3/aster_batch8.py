"""Aster batch 8 engine — TSV 76-85 (ASTER-BUILD-MAP batch 8).

Crypto (7): negative_funding_squeeze ENJUSDT, ported from archive
r19_crypto.py::_signal/evaluate + crypto_rules.json. Entry: completed
4h close > highest high of prior 20 bars AND an actually available
funding observation < 0 (funding feed is a v3 producer input; no v3
funding producer exists yet, so these sleeves declare "funding" and
land visibly UNFED — never fake-fed, map §4). Exits (archive):
fixed96 = 96h deadline only; lost_breakout = close < stored breakout
level; normalization = funding >= 0; normalization_failure = funding
>= 0 AND close < lowest low of prior 3 bars, executed +4h after the
trigger bar; every structural policy keeps the installed 96h maximum
deadline, which fires even when bars/funding are missing. Sizing:
fullcash = slice cash less 10bp fee; volume1pct = min(fullcash, 1% of
the preceding 4h bar's volume). Reading (shared with batches 6/13):
the archive's 4h entry delay / quote-receipt machinery is the source
runtime's execution layer; the v3 sleeve evaluates the completed bar
and the dispatcher takes the next print.

ETF (3): from archive r19_etf.py::select/_evaluate + etf_rules.json.
Monthly, 09:35-09:40 ET only, whole shares floor(gross*NAV*w/ask),
sells before buys, no price stop/target. Leader = best 126-session
return over the 14-fund basket, ties alphabetical. CORE25: 75% QQQ +
25% leader (combined when QQQ leads). DRIFT1: 100% leader, and when
the selected leader is the held incumbent its existing share count is
retained unchanged. NAV reading (shared with batch 10): slice capital
/ extra account_value. gross 1.5 rows keep the >slice target — the
dispatcher buying-power check governs, never silently capped here.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# --- ENH-ETWIN8 (Edge pass batch 3, 2026-10-24): binding leak = the
# ETF execution window was read off the raw clock hour. The desk cycle
# stamps view["now"] in UTC (desk3/cycle.py: datetime.now(timezone.utc)),
# so the 09:35-09:40 ET window fired 05:35-05:40 ET premarket and NEVER
# during RTH — aster_etf_core25_c098/m150 + aster_etf_drift1_c098 were
# dead in live cycles (fixture tests used naive ET stamps, masking it;
# same class as ENH-ETWIN on the batch-10/11 engine). Cure: aware
# stamps are converted to America/New_York before the window check
# (the reading the b9 engine already uses); naive stamps read as ET.
# Switch: extra["aster_batch8_enh"] {"et_window": bool}, default ON;
# OFF restores the pre-change raw-hour rule exactly. Shadow control:
# the legacy raw-hour gate is evaluated on every call (never emits)
# and a paired record is appended to
# extra["aster_batch8_exp_journal"]["records"] when served.
# Exp: ENH-ETWIN8-20261024, proof/enhance/<sleeve>.json.
EXP_ID_ETWIN8 = "ENH-ETWIN8-20261024"


def _etwin8_enabled(extra):
    ov = (extra or {}).get("aster_batch8_enh")
    if isinstance(ov, dict) and "et_window" in ov:
        return bool(ov["et_window"])
    return True


def _etwin8_paired(extra, record):
    j = (extra or {}).get("aster_batch8_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)

SYM="ENJUSDT"
CRYPTO_SPECS={
 "aster_enj_nfs_fixed96_vol": dict(exit_policy="fixed96", capacity="volume1pct"),
 "aster_enj_nfs_lost_full": dict(exit_policy="lost_breakout", capacity="fullcash"),
 "aster_enj_nfs_lost_vol": dict(exit_policy="lost_breakout", capacity="volume1pct"),
 "aster_enj_nfs_normfail_full": dict(exit_policy="normalization_failure", capacity="fullcash"),
 "aster_enj_nfs_normfail_vol": dict(exit_policy="normalization_failure", capacity="volume1pct"),
 "aster_enj_nfs_norm_full": dict(exit_policy="normalization", capacity="fullcash"),
 "aster_enj_nfs_norm_vol": dict(exit_policy="normalization", capacity="volume1pct"),
}
ETF_SPECS={
 "aster_etf_core25_c098": dict(policy="CORE25", gross=0.98),
 "aster_etf_core25_m150": dict(policy="CORE25", gross=1.5),
 "aster_etf_drift1_c098": dict(policy="DRIFT1", gross=0.98),
}
SPECS={**CRYPTO_SPECS, **ETF_SPECS}
BASKET=["QQQ","SPY","SMH","XLB","XLC","XLE","XLF","XLI","XLK","XLP","XLRE","XLU","XLV","XLY"]
INPUTS_CRYPTO=("bars","funding","positions")
INPUTS_ETF=("bars","positions","quotes")
PRODUCERS=({"name":"bars","outputs":("bars",),"freshness_sla_s":900},
 {"name":"broker_readback","outputs":("positions",),"freshness_sla_s":900},
 {"name":"quotes","outputs":("quotes",),"freshness_sla_s":60})
# NOTE: no "funding" producer is registered in v3 yet -> crypto sleeves
# are visibly UNFED in the registry until the funding producer lands.

# ENH edge-batch2 (2026-10-24): per-sleeve switch + paired shadow records.
def _enh_on(view, ctx, sid, key):
    for src in ((ctx or {}), (view or {}).get("extra") or {}):
        if isinstance(src, dict):
            ov = src.get(f"{sid}_enhance")
            if isinstance(ov, dict) and key in ov:
                return bool(ov[key])
    return True


def _paired(view, ctx, rec):
    if isinstance(ctx, dict):
        ctx.setdefault("enhance_paired", []).append(rec)
    ex = (view or {}).get("extra")
    if isinstance(ex, dict):
        ex.setdefault("enhance_paired", []).append(rec)


ENTRY_FRESH_S = 3600  # one cadence hour after the 4h bar closes


def _now(view,ctx):
    n=view.get("now") or (ctx or {}).get("now") or "2026-10-24T15:00:00"
    if isinstance(n,datetime): return n if n.tzinfo else n.replace(tzinfo=timezone.utc)
    try: return datetime.fromisoformat(str(n).replace("Z","+00:00"))
    except Exception: return datetime(2026,10,24,tzinfo=timezone.utc)
def _bars4(view):
    m=view.get("bars") or {}
    for k in (f"{SYM}|4Hour",f"{SYM}|4H",SYM):
        if m.get(k): return m[k]
    return []
def _bars(view,sym):
    m=view.get("bars") or {}
    for k in (f"{sym}|1Day",f"{sym}|1D",sym):
        if m.get(k): return m[k]
    return []
def _funding(view):
    f=view.get("funding")
    if isinstance(f,dict):
        if SYM in f: return f[SYM]
        if "rate" in f: return f["rate"]
        if f and all(isinstance(v,(int,float)) for v in f.values()): return None
    if isinstance(f,(int,float)): return f
    if isinstance(f,list) and f: 
        last=f[-1]; return last.get("rate") if isinstance(last,dict) else last
    e=view.get("extra") or {}
    return e.get("funding_rate", e.get("funding"))
def _hours_held(p,now):
    for k in ("hours_held","age_hours"):
        if p.get(k) is not None: return float(p[k])
    if p.get("bars_held") is not None: return float(p["bars_held"])*4
    op=p.get("opened_at") or p.get("entry_at") or p.get("opened") 
    if op:
        try:
            t=datetime.fromisoformat(str(op).replace("Z","+00:00"))
            if t.tzinfo is None: t=t.replace(tzinfo=timezone.utc)
            return (now-t).total_seconds()/3600.0
        except Exception: return 0.0
    return 0.0

def evaluate(sleeve_id, view, ctx=None):
    view=view or {}; ctx=ctx or {}
    if sleeve_id in CRYPTO_SPECS: return _crypto(sleeve_id,view,ctx)
    return _etf(sleeve_id,view,ctx)

def _crypto(sid,view,ctx):
    spec=CRYPTO_SPECS[sid]; now=_now(view,ctx); stamp=now.strftime("%Y%m%dT%H%M%S")
    bars=_bars4(view); funding=_funding(view)
    positions=[p for p in (view.get("positions") or []) if float(p.get("qty") or 0)!=0 and p.get("symbol")==SYM]
    n=0; out=[]
    def intent(kind,side,qty,reason,price):
        nonlocal n; n+=1
        return {"intent_id":f"{sid}-{stamp}-{n}","kind":kind,"symbol":SYM,"side":side,"qty":qty,"order_type":"market","limit_price":None,"stop_price":None,"reason":reason,"time_in_force":"day","position_intent":"buy_to_open" if kind=="entry" else "sell_to_close","price_hint":float(price) if price else None}
    for p in positions:
        qty=abs(float(p["qty"])); price=float(bars[-1]["c"]) if bars else float(p.get("avg_price") or 0)
        age=_hours_held(p,now)
        if age>=96:
            out.append(intent("exit","sell",qty,f"{sid} exit: deadline_96h age_h={age:.0f} policy={spec['exit_policy']}",price)); continue
        pol=spec["exit_policy"]
        if pol=="fixed96": continue
        if pol=="lost_breakout":
            lvl=p.get("breakout_level")
            if bars and lvl is not None and float(bars[-1]["c"])<float(lvl):
                out.append(intent("exit","sell",qty,f"{sid} exit: lost_breakout close={float(bars[-1]['c'])} < level={lvl}",price))
        elif pol=="normalization":
            if funding is not None and float(funding)>=0:
                out.append(intent("exit","sell",qty,f"{sid} exit: funding_normalization rate={float(funding)}",price))
        elif pol=="normalization_failure":
            if funding is not None and float(funding)>=0 and len(bars)>=4:
                last=bars[-1]
                if float(last["c"])<min(float(b["l"]) for b in bars[-4:-1]):
                    try:
                        t=datetime.fromisoformat(str(last["t"]).replace("Z","+00:00"))
                        if t.tzinfo is None: t=t.replace(tzinfo=timezone.utc)
                        execute_at=t+timedelta(hours=8)  # bar end (+4h) + 4h execution delay
                    except Exception: execute_at=None
                    if execute_at is not None and now>=execute_at:
                        out.append(intent("exit","sell",qty,f"{sid} exit: normalization_failure rate={float(funding)} close={float(last['c'])}",price))
    if out or positions: return out
    # Entry
    if funding is None or float(funding)>=0: return []
    if len(bars)<21: return []
    last=bars[-1]; prior=bars[-21:-1]
    if not float(last["c"])>max(float(b["h"]) for b in prior): return []
    # ENH: this engine has NO entry window (unlike the ADA engine's 300s):
    # a stale snapshot would enter hours after the breakout. Refuse stale.
    if spec["exit_policy"] in ("lost_breakout", "normalization", "normalization_failure") and \
            _enh_on(view, ctx, sid, "entry_freshness"):
        try:
            bt=datetime.fromisoformat(str(last["t"]).replace("Z","+00:00"))
            if bt.tzinfo is None: bt=bt.replace(tzinfo=timezone.utc)
            lag_s=(now-(bt+timedelta(hours=4))).total_seconds()
        except Exception:
            lag_s=None
        if lag_s is not None and lag_s>ENTRY_FRESH_S:
            _paired(view, ctx, {"exp_id": "ENH-EDGE-B2-" + sid, "sleeve": sid,
                                "control": "enter", "treatment": "refuse_stale_entry",
                                "lag_s": lag_s, "enhance_switch": True})
            return []
    price=float(last["c"])
    cash=float((view.get("slice") or {}).get("cash_usd") or (ctx.get("slice") or {}).get("cash_usd") or 10000.0)
    qty=cash*0.999/price  # 10bp fee each side (crypto_rules fee_bps=10)
    if spec["capacity"]=="volume1pct":
        qty=min(qty, 0.01*float(prior[-1].get("v") or 0))
        if sid=="aster_enj_nfs_fixed96_vol" and _enh_on(view, ctx, sid, "entry_volume_cap"):
            # ENH: cap by the ENTRY bar's volume too — the signal bar's
            # volume is 4h stale and overstates executable liquidity.
            capped=min(qty, 0.01*float(last.get("v") or 0))
            if capped!=qty:
                _paired(view, ctx, {"exp_id": "ENH-EDGE-B2-" + sid, "sleeve": sid,
                                    "control": f"enter_qty={qty:.6f}", "treatment": f"enter_qty={capped:.6f}",
                                    "enhance_switch": True})
            qty=capped
    qty=round(qty,6)
    if qty<=0: return []
    return [intent("entry","buy",qty,f"{sid} entry: 4h_breakout20 close={price} funding={float(funding)} capacity={spec['capacity']}",price)]

def _etf(sid,view,ctx):
    spec=ETF_SPECS[sid]; now=_now(view,ctx)
    _extra0={}; _extra0.update(ctx.get("extra") or {} if isinstance(ctx,dict) else {}); _extra0.update(view.get("extra") or {})
    _enh=_etwin8_enabled(_extra0)
    _legacy_mins=now.hour*60+now.minute
    _et_now=now.astimezone(ET) if now.tzinfo is not None else now
    _et_mins=_et_now.hour*60+_et_now.minute
    _mins=_et_mins if _enh else _legacy_mins
    _control_in=9*60+35 <= _legacy_mins < 9*60+40  # shadow: pre-change gate, never emits
    if not (9*60+35 <= _mins < 9*60+40): return []
    _etwin8_paired(_extra0, {"exp_id": EXP_ID_ETWIN8, "sleeve": sid,
        "treatment": "et_window" if _enh else "legacy_raw_hour",
        "treatment_window_open": True, "control_window_open": _control_in})
    sess=now.date().isoformat(); stamp=now.strftime("%Y%m%dT%H%M%S")
    extra={}; extra.update(ctx.get("extra") or {} if isinstance(ctx,dict) else {}); extra.update(view.get("extra") or {})
    sl=(ctx.get("slice") or {}) if isinstance(ctx,dict) else {}
    equity=float(extra.get("account_value") or extra.get("net_value") or (view.get("slice") or {}).get("capital_usd") or sl.get("capital_usd") or 10000.0)
    positions={p["symbol"]:p for p in (view.get("positions") or []) if float(p.get("qty") or 0)!=0}
    if positions and not extra.get("rebalance_due"):
        months={str(p.get("entry_date") or p.get("opened_at") or "")[:7] for p in positions.values()}
        if months=={sess[:7]}: return []
    scored=[]
    for sym in BASKET:
        b=_bars(view,sym)
        if len(b)>=127 and float(b[-127]["c"])>0:
            scored.append((-(float(b[-1]["c"])/float(b[-127]["c"])-1), sym))
    if not scored: return []
    leader=sorted(scored)[0][1]
    if spec["policy"]=="CORE25":
        weights={leader:0.25}; weights["QQQ"]=weights.get("QQQ",0.0)+0.75
    else:
        weights={leader:1.0}
    targets={}
    for sym,w in weights.items():
        b=_bars(view,sym); px=float(b[-1]["c"]) if b else 0.0
        if px<=0: return []
        targets[sym]=int(spec["gross"]*equity*w//px)
    if spec["policy"]=="DRIFT1" and leader in positions:
        targets[leader]=int(float(positions[leader]["qty"]))  # unchanged shares for the held incumbent leader
    out=[]; n=0
    def intent(kind,sym,side,qty,reason,price):
        nonlocal n; n+=1
        return {"intent_id":f"{sid}-{stamp}-{n}","kind":kind,"symbol":sym,"side":side,"qty":int(qty),"order_type":"market","limit_price":None,"stop_price":None,"reason":reason,"time_in_force":"day","position_intent":"buy_to_open" if kind=="entry" else "sell_to_close","price_hint":float(price)}
    for sym in sorted(positions):
        held=int(float(positions[sym]["qty"])); tgt=targets.get(sym,0)
        if held>tgt:
            px=float(_bars(view,sym)[-1]["c"]) if _bars(view,sym) else float(positions[sym].get("avg_price") or 0)
            kind="exit" if tgt==0 else "rebalance"
            out.append(intent(kind,sym,"sell",held-tgt,f"{sid} {kind}: monthly target {tgt} vs held {held} policy={spec['policy']} leader={leader}",px))
    for sym in sorted(targets):
        held=int(float(positions.get(sym,{}).get("qty") or 0)); tgt=targets[sym]
        if tgt>held:
            out.append(intent("entry",sym,"buy",tgt-held,f"{sid} entry: monthly target {tgt} gross={spec['gross']} policy={spec['policy']} leader={leader}",float(_bars(view,sym)[-1]["c"])))
    return out

def config_rows():
    rows=[]
    for sid in CRYPTO_SPECS:
        rows.append({"id":sid,"module":f"adapters3.{sid}","cadence_s":3600,"session":"24h","slice":{"capital_usd":10000.0,"cash_usd":10000.0},"bp_buffer_frac":0.02,"flat_by_close":False,"flatten_time_et":None,"params":{},"inputs":list(INPUTS_CRYPTO),"parked":False})
    for sid in ETF_SPECS:
        rows.append({"id":sid,"module":f"adapters3.{sid}","cadence_s":300,"session":"rth","slice":{"capital_usd":10000.0,"cash_usd":10000.0},"bp_buffer_frac":0.02,"flat_by_close":False,"flatten_time_et":None,"params":{},"inputs":list(INPUTS_ETF),"parked":False})
    return rows
