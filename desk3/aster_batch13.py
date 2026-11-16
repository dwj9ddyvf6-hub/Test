"""Aster batch 13 engine (TSV-as-spec; archive staged tree absent on this box).

Rows (ASTER-BUILD-MAP batch 13, TSV 126-135):
- aster_link_nfs_norm_vol: negative_funding_squeeze LINKUSDT, exit_policy
  normalization (funding >= 0), capacity volume1pct, fee 10bp (TSV params).
  Entry: completed 4h close > highest high of prior 20 bars AND an actually
  available funding observation < 0. Exit: funding >= 0, or the installed
  maximum deadline (ASSUMPTION 96h, FIDELITY-LEDGER ASTER-B13); the deadline
  fires even when funding is missing (TSV current_exit_rule).
- BETA / C1 Tensor sleeves: consume canonical Tensor v698 products at the
  sleeve layer via the Tensor bundle fire channel (Tensor ENGINE untouched).
  C1 entry: buy-cyan event, price<=5, ret60>=31, vol20>=0.07, avg dollar
  volume>=2M; cool/hot split source-exact per r19_tensor.passes:
  (atr_ratio<=1)==cool (HARDEN batch-1 fidelity cure; was cool<1/hot>=1).
  BETA entry: M2-qualified relative-market cohort fire.
  Ticket $4,000 source book -> $400 on the $10k slice; 25 slots; distinct
  symbols. Exit: 52nd-calendar-week deadline (modelled 260 sessions), no
  price stop / profit cap (TSV). capital_mode delay/reserve wait one extra
  session; reserve sleeves fund entries by selling the QQQ reserve leg.
"""

# CONSTANTS-PROVENANCE-20261116: the 96h deadline (hold_h/deadline_h=96, non-fixed16 policies) is source-confirmed in the archive source/backend/r19_crypto.py exit_due_at rule (due + 96h unless fixed16), diffed in HARDEN batch-1 2026-10-24 and recorded in FIDELITY-LEDGER ("source code, not an assumption").
from __future__ import annotations
from datetime import datetime, timezone, date


def _frac_qty(dollars, per_unit):
    """SILENT-SKIP-SIZING-20261116 (owner price ruling 2026-11-14,
    WS4-FRACTIONAL shape, as in desk3/aster_batch1.py): a positive
    dollar budget expressed as a fractional quantity, rounded DOWN
    to 6dp, never up past the budget; 0.0 only when the budget or
    the per-unit price is not positive."""
    if dollars <= 0 or per_unit <= 0:
        return 0.0
    import math as _m
    return _m.floor((dollars / per_unit) * 1_000_000) / 1_000_000

CRYPTO_ID="aster_link_nfs_norm_vol"
SPECS={
 CRYPTO_ID: dict(kind="crypto", family="negative_funding_squeeze", symbol="LINKUSDT", exit_policy="normalization", capacity="volume1pct", deadline_h=96, ticket=None),
 "aster_tensor_beta_cash_all_25": dict(kind="tensor", family="BETA", capital_mode="cash", volatility="all"),
 "aster_tensor_c1_cash_all_25": dict(kind="tensor", family="C1", capital_mode="cash", volatility="all"),
 "aster_tensor_c1_delay_all_25": dict(kind="tensor", family="C1", capital_mode="delay", volatility="all"),
 "aster_tensor_c1_reserve_all_25": dict(kind="tensor", family="C1", capital_mode="reserve", volatility="all"),
 "aster_tensor_c1_cash_cool_25": dict(kind="tensor", family="C1", capital_mode="cash", volatility="cool"),
 "aster_tensor_c1_delay_cool_25": dict(kind="tensor", family="C1", capital_mode="delay", volatility="cool"),
 "aster_tensor_c1_reserve_cool_25": dict(kind="tensor", family="C1", capital_mode="reserve", volatility="cool"),
 "aster_tensor_c1_cash_hot_25": dict(kind="tensor", family="C1", capital_mode="cash", volatility="hot"),
 "aster_tensor_c1_delay_hot_25": dict(kind="tensor", family="C1", capital_mode="delay", volatility="hot"),
 # VARIATION-ROSTERING-20261115 (2026-11-15): the two F4 _varpx C1
 # variations, rostered as first-class sleeves. They are their parents
 # in every field except ret60_min=0 (the registered PARAM_EXTREME
 # form: ret60 floor 31 -> 0; vol20>=0.07, adv>=2e6, atr and marker
 # conjuncts unchanged). Parent entries above omit ret60_min and keep
 # the floor at 31 via the .get default in _tensor. Falsifier (uniform
 # F4): retire if, over its first 20 resolved forward fires, the mean
 # fwd5 excess vs QQQ is below 0bp. Rollback: delete these two entries.
 "aster_tensor_c1_cash_all_25_varpx": dict(kind="tensor", family="C1", capital_mode="cash", volatility="all", ret60_min=0),
 "aster_tensor_c1_cash_hot_25_varpx": dict(kind="tensor", family="C1", capital_mode="cash", volatility="hot", ret60_min=0),
}
TICKET=400.0; SLOTS=25; HOLD_SESSIONS=260
INPUTS_CRYPTO=("bars","funding","positions")
INPUTS_TENSOR=("tensor","bars","positions")
PRODUCERS=({"name":"bars","outputs":("bars",),"freshness_sla_s":900},
 {"name":"tensor_bundle","outputs":("tensor",),"freshness_sla_s":86400},
 {"name":"broker_readback","outputs":("positions",),"freshness_sla_s":900})
# NOTE (FUNDING-OKX-20261115): the funding producer has landed:
# desk3.producers.OkxFunding is registered for the "funding" key
# and serves the record form this module's _funding unwraps.

def _now(view,ctx):
    n=(view.get("now") or (ctx or {}).get("now") or "2026-10-24T15:00:00")
    if isinstance(n,datetime): return n
    try: return datetime.fromisoformat(str(n).replace("Z","+00:00"))
    except Exception: return datetime(2026,10,24,tzinfo=timezone.utc)
def _sess(view,ctx):
    s=(ctx or {}).get("session") if isinstance(ctx,dict) else None
    return str(s or _now(view,ctx).date().isoformat())[:10]
def _bars(view,sym):
    # F4-CRYPTO-BARKEY-20261114: archive USDT keys resolve via desk3.crypto_bars (served BASE/USD spot forms; see that module) (non-USDT symbols pass through untouched)
    from .crypto_bars import resolve_bars
    return resolve_bars(view.get("bars") or {},sym,
                        ("4Hour","4H","1Day","1D"))
def _funding(view,sym):
    f=view.get("funding")
    if isinstance(f,dict):
        if sym in f:
            # FUNDING-OKX-20261115: unwrap the served funding record
            # ({SYM: {"rate": x, ...}}) like every other funding
            # reader (b11/aster_crypto/batch7); returning the record
            # raw made float() raise on the record form. Scalars
            # pass through unchanged.
            v=f[sym]
            if isinstance(v,dict): v=v.get("rate", v.get("funding_rate"))
            return v
        if "rate" in f: return f["rate"]
    if isinstance(f,(int,float)): return f
    e=view.get("extra") or {}
    return e.get("funding_rate", e.get("funding"))
def _fires(view):
    for src in (view.get("fires"),):
        if isinstance(src,list): return src
    t=view.get("tensor") or {}
    if isinstance(t,list): return t
    if isinstance(t,dict):
        if isinstance(t.get("fires"),list): return t["fires"]
    e=view.get("extra") or {}
    if isinstance(e.get("fires"),list): return e["fires"]
    return []

def evaluate(sleeve_id, view, ctx=None):
    view=view or {}; ctx=ctx or {}
    spec=SPECS[sleeve_id]; now=_now(view,ctx); stamp=now.strftime("%Y%m%dT%H%M%S")
    positions=[p for p in (view.get("positions") or []) if float(p.get("qty") or 0)!=0]
    out=[]; n=0
    def intent(kind,sym,side,qty,reason,price):
        nonlocal n; n+=1
        return {"intent_id":f"{sleeve_id}-{stamp}-{n}","kind":kind,"symbol":sym,"side":side,"qty":qty,"order_type":"market","limit_price":None,"stop_price":None,"reason":reason,"time_in_force":"day","position_intent":"buy_to_open" if kind=="entry" else "sell_to_close","price_hint":float(price) if price else None}
    if spec["kind"]=="crypto": return _crypto(spec,view,positions,intent,now,ctx)
    return _tensor(sleeve_id,spec,view,ctx,positions,intent)

# --- ENH-B5-LINK-DEADLINE (Edge pass batch 5, 2026-10-24). Binding
# leak: the 96h deadline exit — the sleeve's ONLY exit when funding
# data is absent — read hours_held/bars_held, fields no desk position
# row carries (dispatcher/broker rows carry opened_at; cf. the
# aster_crypto engine, which derives age from opened_at). On real
# rows the deadline was dead code and a position could be held
# forever. Treatment: derive hours held from opened_at/entry_time
# against the evaluation clock. Switch: extra["enh_aster_link_nfs_norm_vol"]
# or ctx["enhance"][CRYPTO_ID] {"deadline_from_opened_at": bool},
# default ON; OFF restores the field-only rule exactly. Shadow
# control = the field-only decision, paired on the exit intent.
EXP_ID_LINK = "ENH-B5-LINK-DEADLINE-20261024"

def _link_deadline_on(view,ctx):
    for src in ((view or {}).get("extra") or {}, (ctx or {}).get("enhance") or {}):
        ov=src.get(f"enh_{CRYPTO_ID}") or src.get(CRYPTO_ID)
        if isinstance(ov,dict) and "deadline_from_opened_at" in ov:
            return bool(ov["deadline_from_opened_at"])
    return True

def _hours_from_opened(p,now):
    raw=p.get("opened_at") or p.get("entry_time")
    if raw is None: return None
    try:
        if isinstance(raw,(int,float)): opened=datetime.fromtimestamp(float(raw),tz=timezone.utc)
        else:
            opened=datetime.fromisoformat(str(raw).replace("Z","+00:00"))
            if opened.tzinfo is None: opened=opened.replace(tzinfo=timezone.utc)
        n=now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        return (n-opened).total_seconds()/3600.0
    except Exception: return None

def _crypto(spec,view,positions,intent,now=None,ctx=None):
    sym=spec["symbol"]; bars=_bars(view,sym); funding=_funding(view,sym)
    out=[]
    for p in positions:
        if p["symbol"]!=sym: continue
        hours=p.get("hours_held")
        if hours is None and p.get("bars_held") is not None: hours=float(p["bars_held"])*4
        derived=False
        if hours is None and now is not None and _link_deadline_on(view,ctx):
            hours=_hours_from_opened(p,now); derived=hours is not None
        if hours is not None and float(hours)>=spec["deadline_h"]:
            it=intent("exit",sym,"sell",abs(float(p["qty"])),f"{CRYPTO_ID} exit: deadline_96h hours_held={float(hours):.0f} (deadline fires without funding)",float(bars[-1]["c"]) if bars else float(p.get("avg_price") or 0))
            if derived:
                it["reason"]+=f" enh:{EXP_ID_LINK} hours_derived_from_opened_at"
                it["enhance_exp"]={"exp_id":EXP_ID_LINK,"sleeve":CRYPTO_ID,
                    "control_decision":"no_exit_hours_unknown",
                    "treatment_decision":"deadline_exit","hours_held":round(float(hours),2)}
            out.append(it); continue
        if funding is not None and float(funding)>=0:
            out.append(intent("exit",sym,"sell",abs(float(p["qty"])),f"{CRYPTO_ID} exit: funding_normalization rate={float(funding)}",float(bars[-1]["c"]) if bars else float(p.get("avg_price") or 0)))
    if out or positions: return out
    # GATE-CURE-CRYPTO-20261112 (STRICTNESS-CENSUS proposal 9):
    # the LINK squeeze entry funding leg relaxes < 0 -> < 0.00005;
    # the funding_normalization exit above (funding >= 0) is
    # unchanged. READINESS-ROUND2-20261112 (CADENCE-SWEEPS S4):
    # the leg relaxes further to < 0.00015 (1.42/wk priced past
    # the 0.0001 cap print). Rollback: restore >=0.00005 here
    # (round 2) or >=0 (original).
    if funding is None or float(funding)>=0.00015: return []
    if len(bars)<21: return []
    last=bars[-1]; prior=bars[-21:-1]
    if not float(last["c"])>max(float(b["h"]) for b in prior): return []
    price=float(last["c"]); prev_vol=float(prior[-1].get("v") or 0)
    cash=float((view.get("slice") or {}).get("cash_usd") or 10000.0)
    qty=min(0.01*prev_vol, cash/price)
    qty=round(qty,6)
    if qty<=0: return []
    return [intent("entry",sym,"buy",qty,f"{CRYPTO_ID} entry: 4h_breakout20 close={price:.2f} funding={float(funding)} qty=min(1%vol,cash) cap_vol={0.01*prev_vol:.4f}",price)]

EXP_ID="ENH-TENSOR13-REPRICE-20261024"
def _reprice_on(view,ctx,sid):
    """ENH (Edge batch 12): execution-price revalidation switch.
    Default ON; OFF (ctx['enhance'][sid]['exec_reprice']=False or
    view.extra[f'{sid}_improve']['exec_reprice']=False) restores the
    pre-change fire-price rule exactly."""
    for src in ((ctx or {}).get("enhance"), (view.get("extra") or {}).get(f"{sid}_improve")):
        if isinstance(src,dict):
            per=src.get(sid) if isinstance(src.get(sid),dict) else src
            if isinstance(per,dict) and "exec_reprice" in per: return bool(per["exec_reprice"])
    return True

EXP_ID_B11="ENH-B11-TENSOR-FIREAGE-20261024"
# VARIATION-ROSTERING-20261115 (2026-11-15): the two _varpx cash
# variations join ENH11_TENSOR so they inherit their parents' fire-age
# treatment exactly; parent membership is unchanged.
ENH11_TENSOR=("aster_tensor_beta_cash_all_25","aster_tensor_c1_cash_all_25",
              "aster_tensor_c1_cash_cool_25","aster_tensor_c1_cash_hot_25",
              "aster_tensor_c1_cash_all_25_varpx","aster_tensor_c1_cash_hot_25_varpx")
def _fire_age_on(view,ctx,sid):
    """ENH batch 11 switch: ctx['enhance'][sid]['fire_age'] or
    view.extra[f'{sid}_improve']['fire_age'], default ON; OFF restores
    the pre-change any-age rule exactly."""
    for src in ((ctx or {}).get("enhance"), (view.get("extra") or {}).get(f"{sid}_improve")):
        if isinstance(src,dict):
            per=src.get(sid) if isinstance(src.get(sid),dict) else src
            if isinstance(per,dict) and "fire_age" in per: return bool(per["fire_age"])
    return True

def _b11_paired(view,rec):
    j=((view or {}).get("extra") or {}).get("aster_enh_exp_journal")
    if isinstance(j,dict) and isinstance(j.get("records"),list):
        j["records"].append(rec)

def _opened_sessions(p,bars):
    # READINESS-D2-20261112 (ENTER-EXIT-CENSUS D2): real position
    # rows carry opened_at, never an age counter. Derive sessions
    # held as the count of distinct bar dates after the opened
    # date, over the sleeve's own bars (the aster_batch1._held_bars
    # pattern). Only date-shaped stamps count; label stamps in
    # fixtures contribute nothing.
    od=str(p.get("opened_at") or p.get("entry_date") or "")[:10]
    if len(od)!=10 or od[4]!="-" or od[7]!="-": return 0
    days=set()
    for b in bars or []:
        if not isinstance(b,dict): continue
        t=b.get("t") or b.get("date") or b.get("timestamp")
        d=None
        if isinstance(t,(int,float)) and t>1e11:
            d=datetime.fromtimestamp(t/1000,tz=timezone.utc).date().isoformat()
        elif isinstance(t,str) and len(t)>=10 and t[4]=="-" and t[7]=="-":
            d=t[:10]
        if d and d>od: days.add(d)
    return len(days)

def _age_sessions(p,bars):
    for k in ("sessions_held","age_sessions","held_sessions"):
        if p.get(k) is not None: return int(p[k])
    if p.get("weeks_held") is not None: return int(p["weeks_held"])*5
    if p.get("age_weeks") is not None: return int(p["age_weeks"])*5
    return _opened_sessions(p,bars)

def _tensor(sid,spec,view,ctx,positions,intent):
    sess=_sess(view,ctx); out=[]
    reserve = spec["capital_mode"]=="reserve"
    for p in positions:
        sym=p["symbol"]
        if reserve and sym=="QQQ": continue  # reserve leg exits only to fund a ticket
        bars=_bars(view,sym); price=float(bars[-1]["c"]) if bars else float(p.get("avg_price") or 0)
        if _age_sessions(p,bars)>=HOLD_SESSIONS:
            out.append(intent("exit",sym,"sell",abs(float(p["qty"])),f"{sid} exit: week52_deadline sessions_held={_age_sessions(p,bars)}",price))
    if out: return out
    held={p["symbol"] for p in positions if not (reserve and p["symbol"]=="QQQ")}
    if len(held)>=SLOTS: return []
    exp_records=[]
    for f in _fires(view):
        if not isinstance(f,dict): continue
        if f.get("sleeve_id") and f["sleeve_id"]!=sid: continue
        sym=f.get("symbol"); 
        if not sym or sym in held: continue
        sig=str(f.get("signal") or f.get("event") or f.get("family") or "").lower()
        price=float(f.get("price") or 0)
        if price<=0: continue
        if spec["family"]=="C1":
            # GATE-CURE-20261112 (STRICTNESS-CENSUS proposals 4-6):
            # all variants take the registered marker-kept pair:
            # the close cap is removed entirely and ret60 relaxes
            # 31 -> 0, buy-cyan kept (0 -> 3 qualifications: TEM,
            # AXTI, CLS). Hot variants drop the marker requirement
            # and keep the numeric profile (proposal 5, 0 -> 3).
            # Cool variants are UNCHANGED: proposal 6 is skipped
            # as identity-erasing (its registered atr move
            # 1.0 -> 1.75 erases the cool variant's distinction).
            vol=spec["volatility"]
            # STRICTNESS-ROUND2-COMPLETION-20261114 (CADENCE-AUDIT
            # R2, priced in CADENCE-SWEEPS S3): the ALL trio takes
            # the swept registered form — the buy-cyan marker
            # requirement is REMOVED for "all" (the marker-kept
            # ceiling is 3 symbol-weeks, 0.30/wk, at every cap and
            # ret60) and its ret60 floor is restored 0 -> 31, so
            # the gate is the (off, removed, 31) cell: 31
            # symbol-weeks, 3.10/wk, MEETS-WEEKLY. Only "cool"
            # still requires the marker (proposal 6 skipped; the
            # cool trio's disposition is the identity decision
            # named in CALIBRATION-ROUND2-2026-11-14.md).
            # Rollback: restore the marker
            # line for "all" and ret60_min 0 for "all".
            if vol=="cool" and "cyan" not in sig: continue
            # READINESS-ROUND2-20261112 (CADENCE-SWEEPS S3 R3):
            # the C1 HOT trio's $5 close cap is removed (ret60
            # kept at 31; 2.90/wk priced). Cool keeps its cap.
            # Rollback: cap 5.0 for hot again.
            cap=None if vol in ("all","hot") else 5.0
            if cap is not None and price>cap: continue
            # VARIATION-ROSTERING-20261115 (2026-11-15): the floor is
            # read from the sleeve's own SPECS entry; every parent
            # omits ret60_min and keeps 31 exactly, the two _varpx
            # variations carry ret60_min=0 (registered PARAM_EXTREME).
            ret60_min=spec.get("ret60_min", 31)
            if f.get("ret60") is None or float(f["ret60"])<ret60_min: continue
            if f.get("vol20") is None or float(f["vol20"])<0.07: continue
            adv=f.get("adv_usd", f.get("avg_dollar_volume"))
            if adv is None or float(adv)<2_000_000: continue
            if spec["volatility"] in ("cool","hot"):
                ar=f.get("atr_ratio")
                if ar is None: continue
                # FIDELITY cure (HARDEN batch-1, source r19_tensor.passes):
                # (atr_ratio<=1)==(vol=='cool') — cool includes atr==1.0,
                # hot is atr>1. The TSV assumption cool<1/hot>=1 was wrong
                # at exactly 1.0; batch 14 already follows the source.
                if (float(ar)<=1) != (spec["volatility"]=="cool"): continue
        else:  # BETA
            if not ("beta" in sig or "m2" in sig or f.get("m2_qualified")): continue
            if f.get("m2_qualified") is False: continue
        fdate=str(f.get("date") or f.get("fire_date") or "")[:10]
        if spec["capital_mode"] in ("delay","reserve") and fdate:
            try:
                if (date.fromisoformat(sess)-date.fromisoformat(fdate)).days<1: continue
            except Exception: continue
        # ENH batch 11 (binding leak: unbounded fire age): batch 12
        # repriced the entry, but a cash-mode sleeve still acted on a
        # Tensor fire of ANY age — a stale bundle file (SLA 86400s is
        # the producer's, nothing bounded the fire's own date) could
        # deploy $400 tickets days after the signal died. Treatment:
        # for the batch-11 cash sleeves, refuse fires older than the
        # delay mode's own 1-session constant (or future-dated); the
        # accepted-any-age decision is the paired shadow control.
        if sid in ENH11_TENSOR and _fire_age_on(view,ctx,sid) and fdate:
            try: age=(date.fromisoformat(sess)-date.fromisoformat(fdate)).days
            except Exception: age=None
            if age is not None and (age<0 or age>1):
                rec11={"exp_id":EXP_ID_B11,"sleeve":sid,"symbol":sym,
                       "fire_date":fdate,"session":sess,"age_days":age,
                       "control_enter":True,"treatment_enter":False,
                       "refusal":"stale_fire_age","switch_on":True}
                exp_records.append(rec11); _b11_paired(view,rec11)
                continue
        # ENH batch 12 (binding leak: stale-fire pricing): gates and
        # sizing used the signal-time fire price, but the market order
        # fills at the CURRENT price — delay/reserve sleeves execute
        # >=1 session later, so the design price cap (C1 <=5) could be
        # violated at execution and qty could overshoot the $400
        # ticket. With the switch ON and a current bar available,
        # revalidate the cap and size off the latest close; the fire-
        # price decision is kept as the paired shadow control record.
        eprice=price; rec=None
        if _reprice_on(view,ctx,sid):
            fb=_bars(view,sym); cur=float(fb[-1]["c"]) if fb else None
            if cur and cur>0:
                rec={"exp_id":EXP_ID,"symbol":sym,"fire_price":price,
                     "current_price":cur,"control_enter":True,
                     "control_qty":int(TICKET//price),"switch_on":True}
                # GATE-CURE-20261112: the revalidation cap follows
                # the entry gate's registered cap (None for the C1
                # all variants after proposal 4 removed it).
                c1_cap=None if spec["volatility"]=="all" else 5.0
                if spec["family"]=="C1" and c1_cap is not None and cur>c1_cap:
                    rec["treatment_enter"]=False; rec["treatment_qty"]=0
                    rec["refusal"]="current_price>5_cap"
                    exp_records.append(rec); continue
                eprice=cur; rec["treatment_enter"]=True
                rec["treatment_qty"]=int(TICKET//cur)
        qty=int(TICKET//eprice)
        if qty<1:
            # SILENT-SKIP-SIZING-20261116: the floor reaching 0
            # silently killed the fire for price; same $400 ticket
            # expressed fractionally (see _frac_qty).
            qty=_frac_qty(TICKET,eprice)
            if qty<=0: continue
        if reserve:
            for p in positions:
                if p["symbol"]=="QQQ":
                    qb=_bars(view,"QQQ"); qp=float(qb[-1]["c"]) if qb else float(p.get("avg_price") or 0)
                    if qp>0:
                        sq=min(abs(float(p["qty"])), int(TICKET//qp) or 1)
                        out.append(intent("exit","QQQ","sell",sq,f"{sid} exit: qqq_reserve_funding ticket={TICKET:.0f}",qp))
                    break
        ent=intent("entry",sym,"buy",qty,f"{sid} entry: tensor_{spec['family'].lower()} mode={spec['capital_mode']} vol={spec['volatility']} ticket=400 price={eprice:.2f} fire={fdate or sess}" + (f" reprice fire={price:.2f} cur={eprice:.2f}" if rec else ""),eprice)
        if rec: exp_records.append(rec)
        if exp_records: ent["enhance_exp"]={"exp_id":EXP_ID,"records":exp_records}
        out.append(ent)
        return out
    return out
