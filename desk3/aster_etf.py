"""Aster ETF sleeves — batch 10 (TSV-as-spec; staged archive absent on this box at build time, see FIDELITY-LEDGER ASTER-B10).
Spec source: sleeve-catalog.tsv education_* fields + ASTER-BUILD-MAP.md §6 etf rows.
Common rules (all 10): entry/rebalance only 09:35-09:40 ET; whole shares floor(gross*equity/price);
sells before buys; no price stop/target; cost_bps 15 is source-book accounting, not an order field.
Monthly sleeves act on initial allocation (flat) or when a holding's entry month != session month
(documented reading of 'monthly'); buy-and-hold sleeves never rebalance/exit by design.
LEADER1: rank basket by 126-session log return log(close[-1]/close[-127])
(source r19_etf._scores, HARDEN batch-1 fidelity cure), ties alphabetical.
Eligibility is source-exact: _scores requires the full 252-session history
window — a symbol with <252 bars is ineligible (pre-inception) or the
evaluation is unqualified; it is never ranked on a shorter history.
Inputs must come from v3 producers (bars/positions/quotes) — absent bars => no intents (UNFED upstream)."""
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# --- ENH-ETWIN (Edge pass batch 4, 2026-10-24): binding leak = the
# execution window was read off the raw clock hour. The desk cycle
# stamps view["now"] in UTC (desk3/cycle.py: datetime.now(timezone.utc)),
# so the 09:35-09:40 window fired 05:35-05:40 ET premarket and NEVER
# during RTH — all batch-10/11 ETF sleeves were dead in live cycles
# (fixture tests used naive ET stamps, masking it). Cure: aware stamps
# are converted to America/New_York before the window check (the exact
# reading the archive/b9 engine already uses); naive stamps read as ET.
# Switch: extra["aster_etf_enh"] {"et_window": bool}, default ON; OFF
# restores the pre-change raw-hour rule exactly. Shadow control: the
# legacy raw-hour gate is evaluated on every call (never emits) and a
# paired record is appended to extra["aster_etf_exp_journal"]["records"]
# when served. Exp: ENH-ETWIN-20261024, proof/enhance/<sleeve>.json.
EXP_ID_ETWIN = "ENH-ETWIN-20261024"


def _etwin_enabled(extra):
    ov = (extra or {}).get("aster_etf_enh")
    if isinstance(ov, dict) and "et_window" in ov:
        return bool(ov["et_window"])
    return True


def _etwin_paired(extra, record):
    j = (extra or {}).get("aster_etf_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)

# --- ENH-B5-CATCHUP (Edge pass batch 5, 2026-10-24) — SECOND look at
# the monthly sleeves (first look: ENH-ETWIN above). Binding leak: the
# rebalance window is 5 minutes wide and the sleeve cadence is 300s,
# so exactly ONE evaluation per month can ever fire; a wedged, late,
# or unfed 09:35 cycle loses the entire month's rebalance (the desk's
# own history is 21 watchdog kills in a day). Treatment: a MONTHLY
# sleeve whose rebalance is due may still execute the SAME targets
# later the same session (09:40-15:55 ET) — the monthly horizon makes
# the intraday delay immaterial vs a month of wrong exposure.
# Switch: extra["aster_etf_enh"] {"catchup": bool}, default ON; OFF
# restores the window-only rule exactly. Shadow control: the legacy
# window gate is evaluated on every call (never emits) and paired
# records are appended when the catch-up path serves.
EXP_ID_CATCHUP = "ENH-B5-ETF-CATCHUP-20261024"


def _catchup_enabled(extra):
    ov = (extra or {}).get("aster_etf_enh")
    if isinstance(ov, dict) and "catchup" in ov:
        return bool(ov["catchup"])
    return True


def _in_catchup(now, legacy=False):
    if now is None: return False
    if not legacy and now.tzinfo is not None:
        now = now.astimezone(ET)
    mins = now.hour * 60 + now.minute
    return 9 * 60 + 40 <= mins < 15 * 60 + 55

BASKET=["QQQ","SPY","SMH","XLB","XLC","XLE","XLF","XLI","XLK","XLP","XLRE","XLU","XLV","XLY"]
SPECS={
 "aster_etf_leader1_m150": dict(policy="LEADER1", freq="MONTHLY", gross=1.5, weights=None),
 "aster_etf_qld_buy_hold": dict(policy="QLD_ONLY_BUY_HOLD", freq="BUY_HOLD", gross=1.0, weights={"QLD":1.0}),
 "aster_etf_qld_monthly": dict(policy="QLD_ONLY_MONTHLY", freq="MONTHLY", gross=1.0, weights={"QLD":1.0}),
 "aster_etf_qqq_buy_hold": dict(policy="QQQ_HOLD_FULL", freq="BUY_HOLD", gross=1.0, weights={"QQQ":1.0}),
 "aster_etf_qqq_monthly_c098": dict(policy="QQQ_MONTHLY", freq="MONTHLY", gross=0.98, weights={"QQQ":1.0}),
 "aster_etf_qqq_monthly_m150": dict(policy="QQQ_MONTHLY", freq="MONTHLY", gross=1.5, weights={"QQQ":1.0}),
 "aster_etf_qqq_qld_buy_hold": dict(policy="QQQ_QLD_50_50_BUY_HOLD", freq="BUY_HOLD", gross=1.0, weights={"QQQ":0.5,"QLD":0.5}),
 "aster_etf_qqq_qld_monthly": dict(policy="QQQ_QLD_50_50_MONTHLY", freq="MONTHLY", gross=1.0, weights={"QQQ":0.5,"QLD":0.5}),
 "aster_etf_smh_hold_c098": dict(policy="SMH_HOLD", freq="BUY_HOLD", gross=0.98, weights={"SMH":1.0}),
 "aster_etf_smh_hold_m150": dict(policy="SMH_HOLD", freq="BUY_HOLD", gross=1.5, weights={"SMH":1.0}),
}
INPUTS=("bars","positions","quotes")
PRODUCERS=({"name":"bars","outputs":("bars",),"freshness_sla_s":900},
 {"name":"broker_readback","outputs":("positions",),"freshness_sla_s":900},
 {"name":"quotes","outputs":("quotes",),"freshness_sla_s":60})

def _bars(view,sym):
    m=view.get("bars") or {}
    for k in (f"{sym}|1Day",f"{sym}|1D",sym):
        if m.get(k): return m[k]
    return []
def _close(bars): return float(bars[-1]["c"]) if bars else 0.0
def _now(view,ctx):
    n=view.get("now") or (ctx or {}).get("now") or (ctx or {}).get("session") or ""
    if isinstance(n,datetime): return n
    try: return datetime.fromisoformat(str(n).replace("Z","+00:00"))
    except Exception: return None
def _in_window(now, legacy=False):
    if now is None: return False
    if not legacy and now.tzinfo is not None:
        now = now.astimezone(ET)
    mins=now.hour*60+now.minute
    return 9*60+35 <= mins < 9*60+40

def evaluate(sleeve_id, view, ctx=None):
    view=view or {}; ctx=ctx or {}
    spec=SPECS[sleeve_id]; now=_now(view,ctx)
    _extra0={}; _extra0.update(ctx.get("extra") or {} if isinstance(ctx,dict) else {}); _extra0.update(view.get("extra") or {})
    _enh=_etwin_enabled(_extra0)
    _control_in=_in_window(now, legacy=True)  # shadow: pre-change gate, never emits
    _catch=(spec["freq"]=="MONTHLY" and _catchup_enabled(_extra0)
            and not _in_window(now, legacy=not _enh)
            and _in_catchup(now, legacy=not _enh))
    if not _in_window(now, legacy=not _enh) and not _catch: return []
    _etwin_paired(_extra0, {"exp_id": EXP_ID_ETWIN, "sleeve": sleeve_id,
        "treatment": "et_window" if _enh else "legacy_raw_hour",
        "treatment_window_open": True, "control_window_open": _control_in})
    sess=now.date().isoformat(); stamp=now.strftime("%Y%m%dT%H%M%S")
    extra={}; extra.update(ctx.get("extra") or {} if isinstance(ctx,dict) else {}); extra.update(view.get("extra") or {})
    sl=(ctx.get("slice") or {}) if isinstance(ctx,dict) else {}
    equity=float(extra.get("account_value") or extra.get("net_value") or sl.get("capital_usd") or 10000.0)
    positions={p["symbol"]:p for p in (view.get("positions") or []) if float(p.get("qty") or 0)!=0}
    # BUY_HOLD: once allocated, hold fixed shares forever (designed: no exit/rebalance)
    if spec["freq"]=="BUY_HOLD" and positions: return []
    # MONTHLY: only on initial allocation or a new month vs holdings' entry month
    if spec["freq"]=="MONTHLY" and positions and not extra.get("rebalance_due"):
        months={str(p.get("entry_date") or p.get("opened_at") or "")[:7] for p in positions.values()}
        if months=={sess[:7]}: return []
    # targets
    if spec["policy"]=="LEADER1":
        import math
        scored=[]
        for sym in BASKET:
            b=_bars(view,sym)
            if len(b)>=252:  # source _scores 252-session eligibility window
                scored.append((-math.log(_close(b)/float(b[-127]["c"])), sym))
        if not scored: return []
        scored.sort()  # highest return first; ties alphabetical (sym asc within equal score via tuple on -ret? use stable)
        # sort by return desc, ticker asc:
        scored=sorted(scored, key=lambda x:(x[0], x[1]))
        leader=scored[0][1]; weights={leader:1.0}
    else:
        weights=spec["weights"]
    targets={}
    for sym,w in weights.items():
        b=_bars(view,sym); px=_close(b)
        if px<=0: return []  # missing price for a target leg: refuse whole rebalance
        targets[sym]=int(spec["gross"]*equity*w//px)
    out=[]; n=0
    def intent(kind,sym,side,qty,reason,price):
        nonlocal n; n+=1
        return {"intent_id":f"{sleeve_id}-{stamp}-{n}","kind":kind,"symbol":sym,"side":side,"qty":int(qty),"order_type":"market","limit_price":None,"stop_price":None,"reason":reason,"time_in_force":"day","position_intent":"buy_to_open" if kind=="entry" else "sell_to_close","price_hint":float(price)}
    # sells first: non-target symbols fully; over-target reduced
    for sym in sorted(positions):
        held=int(float(positions[sym]["qty"])); tgt=targets.get(sym,0)
        if held>tgt:
            px=_close(_bars(view,sym)) or float(positions[sym].get("avg_price") or 0)
            kind="exit" if tgt==0 else "rebalance"
            out.append(intent(kind,sym,"sell",held-tgt,f"{sleeve_id} {kind}: monthly target {tgt} vs held {held} policy={spec['policy']}",px))
    for sym in sorted(targets):
        held=int(float(positions.get(sym,{}).get("qty") or 0)); tgt=targets[sym]
        if tgt>held:
            out.append(intent("entry",sym,"buy",tgt-held,f"{sleeve_id} entry: monthly target {tgt} gross={spec['gross']} policy={spec['policy']}",_close(_bars(view,sym))))
    if _catch and out:
        rec={"exp_id": EXP_ID_CATCHUP, "sleeve": sleeve_id,
             "treatment": "same_session_catchup", "control_intents": 0,
             "treatment_intents": len(out), "control_window_open": False}
        _etwin_paired(_extra0, rec)
        for o in out:
            o["reason"] += f" enh:{EXP_ID_CATCHUP} catchup_after_missed_window"
            o["enhance_exp"] = rec
    return out
