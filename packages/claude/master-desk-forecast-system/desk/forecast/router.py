"""The router (FACTORY.md §6, BSF-09): a ticker's context today -> the promoted cells that match -> one label with the
evidence behind it. It proposes; it places nothing (propose-then-approve) and touches no sleeve, OMS or book.

Decision rule: act only if the LOWER confidence bound of the incremental utility of the action over the best
alternative (flat included) is above zero on every window the cell was scored on, the name is in the cell's domain,
its costs are measured, and every gate passes. Otherwise ABSTAIN (the default; an abstention is recorded and scored).

  Labels   not owned: BUY | WAIT | AVOID      owned: HOLD | TRIM | SELL      ownership unknown: ABSTAIN
           BUY / AVOID / SELL / TRIM / HOLD need evidence; WAIT is evidence for a buy that a non-evidence gate (a
           failed plan check, the kill switch) holds back today; ABSTAIN is "don't know".
  Today    {sym, as_of, bar_closed, owned (True | False | None), context {dim: value | None},
            values {fid: {x, pct}}, cost_side (this name's measured per-side cost), dv20, plan (optional)}
  Matches  a promoted-book cell matches when every dim it names equals today's (an unknown dim never matches) and its
           forecaster is on today: a flag is 1, a score is in the application set (pct above TOP for sign +1, at or
           below 1-TOP for sign -1; the percentile is of today's cross-section of the cell's group, from the host)
  Utility  per date, gross (the set's excess, or the excess a flag avoids) less the sides traded x this name's OWN
           measured cost: 2 for a buy, 1 for a sell or trim, 0 for an avoid or a hold
  Volatility cells (direction vol) never set a label: they are listed as risk_context (options routes are
           forward-only, FACTORY §4.10). Probation and demoted cells are shown in the book and never routed.
  Stacking one name is one bet: the cell with the highest bound speaks; the others are listed as supporting and are
           never added. Opposite directions among cells that pass = conflict = ABSTAIN.
  TRIM vs SELL  the same bound at the 99% level (Z_STRONG) positive: SELL; at the 95% level only: TRIM.
Every output carries the cell id, n, base rate, rate, lift and cost.

Also kept from P2: delta_u_lower_bound / precondition (the bound itself)."""
import math

import numpy as np

from . import cards as CD
from . import capacity as CP
from . import promoted as PM
from . import score as S
from . import search as SR

Z = 1.645                       # one-sided 95%
Z_STRONG = 2.326                # one-sided 99%
DONT_KNOW = "DON'T-KNOW"
ABSTAIN = "ABSTAIN"
LABELS = {True: ("HOLD", "TRIM", "SELL"), False: ("BUY", "WAIT", "AVOID"), None: (ABSTAIN,)}
SIDES = {"BUY": 2, "AVOID": 0, "SELL": 1, "TRIM": 1, "HOLD": 0}


def delta_u_lower_bound(u, alternatives=None, z=Z, lags=0):
    u = np.asarray(u, float)
    alts = {"flat": np.zeros_like(u)}
    alts.update({k: np.asarray(v, float) for k, v in (alternatives or {}).items()})
    best = max(alts, key=lambda k: float(np.nanmean(alts[k])))
    d = u - alts[best]
    d = d[np.isfinite(d)]
    r = S.nw_t(d, lags)
    if r["sd"] is None or r["T_eff"] is None:
        return None, best
    return r["mean"] - z * r["sd"] / math.sqrt(r["T_eff"]), best


def precondition(u, alternatives=None, z=Z, lags=0):
    lb, best = delta_u_lower_bound(u, alternatives, z, lags)
    return {"route": lb is not None and lb > 0, "lb": lb, "best_alternative": best}


# ---------------------------------------------------------------- matching
def _finite(x):
    return x is not None and isinstance(x, (int, float, np.floating)) and math.isfinite(x)


def matches(e, today):
    """(True, "") when the cell's dims all equal today's; else (False, why)"""
    ctx = today.get("context") or {}
    for k, v in e["dims"].items():
        have = ctx.get(k)
        if have is None:
            return False, f"{k} unknown today"
        if have != v:
            return False, f"{k} is {have}, the cell is {v}"
    return True, ""


def active(e, today):
    v = (today.get("values") or {}).get(e["fid"]) or {}
    x, pct = v.get("x"), v.get("pct")
    if not _finite(x):
        return False, f"{e['fid']} has no value today"
    if e["binary"]:
        return (x > 0.5), ("" if x > 0.5 else f"{e['fid']} is not flagged")
    if not _finite(pct):
        return False, f"{e['fid']} has no cross-section percentile today"
    if e["sign"] > 0:
        return (pct > SR.TOP), ("" if pct > SR.TOP else f"{e['fid']} is outside the top quintile")
    return (pct <= 1 - SR.TOP), ("" if pct <= 1 - SR.TOP else f"{e['fid']} is outside the bottom quintile")


def _card(e, w=None):
    w = w or (e["windows"][0] if e["windows"] else {})
    return {"id": e["id"], "fid": e["fid"], "target": e["target"], "cell": e["cell"], "grade": e["grade"],
            "h": e["h"], "direction": e["direction"], "n": w.get("n_obs"), "n_dates": w.get("n_dates"),
            "n_set": w.get("n_set"), "base_rate": w.get("base_rate"), "rate": w.get("rate"), "lift": w.get("lift"),
            "cost_side": w.get("cost_side"), "window": w.get("window")}


def bound(e, own_cost, sides, z=Z):
    """-> (lb, per-window {window start: lb}, best alternative); lb is the minimum over the cell's windows, None when
    any window cannot be bounded or the cell has none"""
    if not e["windows"]:
        return None, {}, "flat"
    per, best = {}, "flat"
    for w in e["windows"]:
        lb, best = delta_u_lower_bound(CD.utility(w, own_cost, sides), None, z, lags=max(0, e["h"] - 1))
        per[w["window"][0]] = lb
    vals = list(per.values())
    return (None if any(v is None for v in vals) else min(vals)), per, best


def _enough(e):
    return bool(e["windows"]) and all(w["n_dates"] >= SR.MIN_DATES for w in e["windows"])


def _gate(key, ok, label):
    return {"key": key, "ok": bool(ok), "label": label}


def route(today, book, grades=PM.GRADE_ROUTES, z=Z):
    """today + a promoted book (promoted.load) -> the routed proposal (see the module docstring)"""
    owned = today.get("owned")
    owned = owned if owned in (True, False) else None
    out = {"sym": today.get("sym"), "as_of": today.get("as_of"), "owned": owned, "label": ABSTAIN, "reason": "",
           "direction": None, "instrument": "flat", "cell": None, "supporting": [], "du": None, "cost": None,
           "capacity_usd": None, "gates": [], "propose_only": True, "plan_checked": False, "risk_context": []}
    gates = out["gates"]
    skipped = []
    live = []
    for e in book["entries"]:
        if e["grade"] not in grades or e["status"] not in PM.ACTED:
            continue
        ok, why = matches(e, today)
        if not ok:
            skipped.append((e["id"], why))
            continue
        if e["direction"] == "vol":                 # a volatility forecast sizes risk; it is not a stock direction
            if not any(x.startswith(f"{e['fid']}|{e['target']}|") for x in out["risk_context"]):
                out["risk_context"].append(e["id"])          # one id per forecaster x target, the first cell that matches
            continue
        on, why = active(e, today)
        if on:
            live.append(e)
    out["n_matched"] = len(live)
    own = today.get("cost_side")
    dv20 = today.get("dv20")
    closed = bool(today.get("bar_closed"))
    gates.append(_gate("bar_closed", closed, "the bars are closed sessions" if closed else "the last bar is not a closed session"))
    gates.append(_gate("cost_measured", _finite(own) and own >= 0, "this name's cost is measured"
                       if _finite(own) and own >= 0 else "this name's cost is not measured"))
    gates.append(_gate("in_domain", _finite(dv20) and dv20 > 0, "dollar volume is measured, the name is in the cell's domain"
                       if _finite(dv20) and dv20 > 0 else "no dollar volume: outside the domain"))
    if not live:
        out["reason"] = "no promoted cell matches today"
        return out
    if not all(g["ok"] for g in gates):
        out["reason"] = "; ".join(g["label"] for g in gates if not g["ok"])
        out["evidence"] = [_card(e) for e in live]
        return out
    # the bound per live cell, under the sides its direction trades for this ownership
    sides_for = {"up": 2 if owned is False else 0, "down": 0 if owned is False else 1}
    scored = []
    for e in live:
        lb, per, best = bound(e, own, sides_for[e["direction"]], z)
        scored.append((lb, e, per, best))
    passing = [x for x in scored if x[0] is not None and x[0] > 0 and _enough(x[1])]
    out["evidence"] = [dict(_card(e), lb=lb) for lb, e, _, _ in scored]
    if not passing:
        best = max((x for x in scored if x[0] is not None), key=lambda x: x[0], default=None)
        out["reason"] = ("the lower bound of the gain over the best alternative is not above zero"
                         + ("" if best is None else f" (best {best[0]:+.5f} on {best[1]['id']})"))
        gates.append(_gate("du_lb", False, out["reason"]))
        return out
    dirs = {x[1]["direction"] for x in passing}
    if len(dirs) > 1:
        out["reason"] = "conflict: promoted cells point both ways on this name"
        gates.append(_gate("no_conflict", False, out["reason"]))
        return out
    gates.append(_gate("du_lb", True, "the lower bound of the gain over the best alternative is above zero"))
    gates.append(_gate("no_conflict", True, "one direction"))
    lb, e, per, best = max(passing, key=lambda x: x[0])
    out["supporting"] = [_card(x[1]) for x in passing if x[1] is not e]
    out["direction"], out["cell"] = e["direction"], _card(e)
    out["du"] = {"lb": lb, "z": z, "best_alternative": best, "per_window": per, "dates": e["windows"][0]["n_dates"]}
    out["cost"] = {"own_side": own, "cell_side": e["windows"][0].get("cost_side")}
    out["capacity_usd"] = float(CP.cap(dv20, e["h"]))
    if owned is None:
        out["label"], out["reason"] = ABSTAIN, "ownership unknown: the label needs to know whether it is held"
        return out
    if e["direction"] == "up":
        if owned:
            out.update(label="HOLD", instrument="long", reason="a promoted cell supports holding")
        else:
            plan = today.get("plan")
            kill = _killed()
            gates.append(_gate("kill_switch", not kill, "kill switch off" if not kill else "kill switch on"))
            bad = []
            if plan is not None:
                from desk.ai import gates as AG
                cg = AG.consistency_gate(plan)
                out["plan_checked"] = True
                gates.append(_gate("plan", cg["ok"], "the plan is consistent" if cg["ok"] else "; ".join(cg["reasons"])))
                bad = [] if cg["ok"] else cg["reasons"]
            if kill or bad:
                out.update(label="WAIT", instrument="flat", reason="evidence supports a buy; held back: "
                           + ("kill switch on" if kill else "; ".join(bad)))
            else:
                out.update(label="BUY", instrument="long", reason="a promoted cell supports a buy")
    else:
        if not owned:
            out.update(label="AVOID", instrument="avoid", reason="a promoted avoid cell flags this name")
        else:
            kill = _killed()
            gates.append(_gate("kill_switch", not kill, "kill switch off" if not kill else "kill switch on"))
            if kill:
                out.update(label="WAIT", instrument="flat", reason="evidence supports an exit; held back: kill switch on")
            else:
                strong, _, _ = bound(e, own, 1, Z_STRONG)
                out.update(label="SELL" if strong is not None and strong > 0 else "TRIM", instrument="exit",
                           reason="a promoted avoid cell flags a held name")
    return out


def _killed():
    from desk.ai import gates as AG
    return AG.killed()
