"""qr_capitalreleasedynamics -- CRD, Capital Release Dynamics (quant-research-backup@d170596b
research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/crd: repair/crd_r10.py, the repaired CRD
kernels, vendored byte-exact under desk/vendor/quant_research/r10/crd/ and executed; PRACTICAL_PLAYBOOK.md).

The account (playbook "Actual risk and budget"): $1m, cash plus at most 30 names, 5% a name, 25% a sector, 20% a
positive-correlation cluster (0.7), gross <= 95%, cash >= 5%, forecast annualised volatility <= 20% on the 20-session
covariance, ordinary weekly buys + sells <= 30% NAV; idle cash stays cash (the canonical account -- R9's QQQ
opportunity is a different strategy).

Weekly decision (Friday 16:15 cutoff, frozen for the next session), over the registered decision document
(cache/qr_crd_registry.json: per decision session the optimisation domain -- names, then-known sectors, the cluster
partition, the 20-session covariance, the synchronized lower-mean gross scenarios and cash gross, each candidate's
frozen evidence: residual rank and rank 20 sessions earlier, the 10-session residual sum, the release flag, the
calibrated and rank-only forecasts with their SEs, the Kish origin ESS, the calibration origin dates, the round trip
cost -- and the trailing ADV; per session close the held names' monitoring evidence: rank, conservative forecast,
fundamental eligibility):
  entry     crd_r10.entry_allowed (release, rank 0.60-0.95 and +0.20 in 20 sessions, positive residual sum, ESS >= 30,
            >= 100 calibration dates, increment over rank-only - 1.645 SE > 0, forecast - 1.645 SE > round trip
            + 0.002); names neither admitted nor held leave the domain;
  plan      crd_r10.optimize_target over the held weights at the executable marks (the multistart SLSQP; the trade
            only when the robust log-wealth gain > log(1.0002) or holding is illegal), crd_r10.round_target to whole
            shares under the caps;
  execution the next session 09:35-10:05 ET, sells first, at most 0.5% of the trailing ADV per name and session;
            the unfilled remainder expires at 10:05.
Exits (crd_r10.exit_decision, at each session's first pass on the previous close): residual rank < 0.40, a
conservative forecast <= 0, lost fundamental eligibility, a hard cap breach (actual weights at the marks), an 8%
entry-to-close drawdown, a 20% peak-to-close account drawdown (liquidates everything); a drawdown exit starts a
five-session entry cooldown. Release expiry alone is no exit.

Removed gates: none beyond the playbook.

Named divergences:
  1. the canonical inputs -- point-in-time listings, permanent issuer ids and sectors, original-public SEC
     durability facts, interval quote / volume receipts -- have no free source, and the kernel's own interface takes
     the synchronized scenarios and the calibration ridge from its caller ("path/exit sampler is not specified
     here", "sealed design does not supply magnitude"): the decision documents are registered research inputs.
     With none registered the account stays in cash -- the playbook's own abstention ("Abstain on missing/unfinal
     data ... unsupported state/calibration");
  2. the 5%-of-interval-volume participation cap is not enforced (no consolidated interval volume on the desk's
     quotes); the 0.5% ADV cap is;
  3. monitoring evidence missing for a held name holds it (the drawdown and cap triggers still bind);
  4. execution: the desk's quotes and marketable limits inside the window (the native midpoint ledger's
     max(5 bp, half spread + impact + commission) cost model is the desk's fee model).

Parity: tools/parity/qr_r10_kernels.py -> docs/receipts/parity/qr_r10_kernels.json (entry gate, exit rule, plans; the
lane's 19 owner tests against the vendored kernel)."""
from datetime import datetime

import numpy as np

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as C
from . import r10

SID = "qr_capitalreleasedynamics"
SOURCE = r10.source("crd", "repair/crd_r10.py", "4d5abbd02788d5370e597e6f93bf1375fd8085e5", 773)
REGISTRY = "qr_crd_registry.json"
ENTRY_FROM, ENTRY_TO = "09:35", "10:05"
ADV_CAP, COOLDOWN = 0.005, 5
EVIDENCE = ("rank", "rank_then", "residual_sum", "release", "calibrated", "rank_only", "se", "incremental_se",
            "effective_origins", "calibration_dates", "round_trip_cost")


def kernel():
    from ...vendor.quant_research.r10.crd import crd_r10 as K
    return K


def admitted(candidate):
    """crd_r10.entry_allowed on a candidate's frozen evidence: (bool, reason)."""
    K = kernel()
    try:
        ev = {k: candidate[k] for k in EVIDENCE}
        ok = K.entry_allowed(ev["rank"], ev["rank_then"], ev["residual_sum"], ev["release"], ev["calibrated"],
                             ev["rank_only"], ev["se"], ev["incremental_se"], ev["effective_origins"],
                             ev["calibration_dates"], ev["round_trip_cost"])
    except (KeyError, TypeError, ValueError) as e:
        return False, "INVALID_EVIDENCE: " + str(e)[:80]
    return bool(ok), "ADMITTED" if ok else "ENTRY_GATE"


def restrict(doc, keep):
    """the decision document on the names `keep` (indices into doc['names']): scenarios, covariance, sectors and the
    cluster partition re-indexed (a partition restricted stays a partition)."""
    idx = list(keep)
    pos = {i: j for j, i in enumerate(idx)}
    gross = np.asarray(doc["lower_mean_gross"], dtype=float)[:, idx] if idx else np.zeros((len(doc["cash_gross"]), 0))
    cov = np.asarray(doc["covariance20"], dtype=float)[np.ix_(idx, idx)] if idx else np.zeros((0, 0))
    clusters = [[pos[i] for i in g if i in pos] for g in doc["clusters"]]
    return {"names": [doc["names"][i] for i in idx], "sectors": [doc["sectors"][i] for i in idx],
            "clusters": [g for g in clusters if g], "covariance20": cov, "lower_mean_gross": gross,
            "cash_gross": np.asarray(doc["cash_gross"], dtype=float)}


def plan(doc, held_shares, marks, cash):
    """(desired whole shares {name: n}, detail) or (None, reason): the frozen document's optimisation on the actual
    held account."""
    K = kernel()
    names = list(doc["names"])
    missing = [s for s, q in held_shares.items() if q > 0 and s not in names]
    if missing:
        return None, "HELD_OUTSIDE_RISK_CONTEXT: " + ",".join(sorted(missing))
    keep, gate = [], {}
    for i, s in enumerate(names):
        cand = (doc.get("candidates") or {}).get(s)
        ok, why = admitted(cand) if cand is not None else (False, "NOT_A_CANDIDATE")
        gate[s] = why
        if ok or held_shares.get(s, 0) > 0:
            keep.append(i)
    sub = restrict(doc, keep)
    if not sub["names"]:
        return {}, {"gate": gate, "trade": False, "reason": "NO_ADMITTED_OR_HELD_NAMES"}
    try:
        px = np.array([float(marks[s]) for s in sub["names"]])
    except (KeyError, TypeError, ValueError):
        return None, "MISSING_MARK"
    shares = np.array([float(held_shares.get(s, 0)) for s in sub["names"]])
    equity = float(shares @ px + cash)
    if equity <= 0:
        return None, "INSOLVENT"
    try:
        res = K.optimize_target(shares * px / equity, sub["lower_mean_gross"], sub["cash_gross"], sub["covariance20"],
                                sub["sectors"], sub["clusters"])
        if not res["trade"]:
            return {s: int(q) for s, q in zip(sub["names"], shares)}, {"gate": gate, "trade": False,
                                                                       "gain": res["objective_improvement"]}
        r = K.round_target(shares, res["plan"]["stocks"], px, cash, sectors=sub["sectors"], clusters=sub["clusters"],
                           covariance20=sub["covariance20"])
    except (K.DataGap, ValueError) as e:
        return None, "ABSTAIN: " + str(e)[:100]
    return ({s: int(q) for s, q in zip(sub["names"], r["shares"])},
            {"gate": gate, "trade": True, "gain": res["objective_improvement"], "log_gain":
             res["mean_logwealth_improvement"], "rounding_reductions": r["rounding_reductions"]})


def cap_breach(doc, held_shares, marks, cash):
    """actual marked caps against the latest decision's risk context (crd_r10.Ledger.actual_cap_report)."""
    K = kernel()
    names = list(doc.get("names") or [])
    if any(s not in names for s, q in held_shares.items() if q > 0) or not names:
        return None
    try:
        p = np.array([float(marks.get(s) or 0.0) if held_shares.get(s, 0) > 0 else float(marks.get(s) or 1.0)
                      for s in names])
        led = K.Ledger(cash=float(cash), shares=np.array([float(held_shares.get(s, 0)) for s in names]))
        rep = led.actual_cap_report(p, np.asarray(doc["covariance20"], dtype=float), list(doc["sectors"]),
                                    [list(g) for g in doc["clusters"]])
    except (K.DataGap, ValueError):
        return None
    return bool(rep["risk_reduction_required"])


class CRD(Sleeve):
    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=300, universe=(), capital=1_000_000.0,
            schedule="rth", needs={"quotes": {"source": "equity"}},
            params={"entry": [ENTRY_FROM, ENTRY_TO], "adv_cap": ADV_CAP, "cooldown": COOLDOWN, "names": 30,
                    "name": 0.05, "sector": 0.25, "cluster": 0.20, "gross": 0.95, "cash": 0.05, "vol": 0.20,
                    "turnover": 0.30},
            source=SOURCE, state_schema={"executed": "str", "monitored": "str", "peak": "float",
                                         "cooldown_until": "str", "exits": "dict", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def _registry(self):
        return r10.read_registry(getattr(self.engine, "root", None), REGISTRY)

    def quote_universe(self, now, book):
        reg = self._registry()
        names = set()
        for d in reg.get("decisions") or []:
            names.update(d.get("names") or [])
        held = {i.split(":", 1)[1] for i in (book.positions or {}) if i.startswith("EQ:")}
        return sorted(names | held)

    def _log(self, st, **rec):
        st["log"] = (st["log"] + [rec])[-200:]

    def signal(self, view):
        K = kernel()
        st = dict(view.state or {})
        for k, v in (("exits", {}), ("log", [])):
            st.setdefault(k, v)
        self._st = st
        now, day = float(view.now), view.session
        if not r10.in_session(now, day):
            return []
        hm = r10.hm(now)
        if not ENTRY_FROM <= hm < ENTRY_TO:
            return []
        reg = self._registry()
        held = {s: q for s, q in C.held(view).items() if q > 0}
        quotes = view.quotes or {}
        marks = {s: (float(q["bid"]) + float(q["ask"])) / 2 for s, q in quotes.items()
                 if q.get("bid") and q.get("ask")}
        cash = float(view.cash)
        avg = {i.split(":", 1)[1]: float(p.get("avg") or 0.0) for i, p in (view.positions or {}).items()}
        prev = C.prev_session(day)
        decisions = sorted(reg.get("decisions") or [], key=lambda d: d.get("decision_session", ""))
        latest = next((d for d in reversed(decisions) if d.get("decision_session", "") <= prev), None)
        out = []
        # the previous close's monitoring -> this session's queued exits
        if st.get("monitored") != day:
            st["monitored"] = day
            closes = {s: (quotes.get(s) or {}).get("prev_close") or marks.get(s) for s in held}
            nav_close = cash + sum(q * float(closes.get(s) or marks.get(s, 0.0)) for s, q in held.items())
            st["peak"] = max(float(st.get("peak") or 0.0), nav_close)
            account_dd = max(0.0, 1 - nav_close / st["peak"]) if st["peak"] else 0.0
            mon = ((reg.get("monitor") or {}).get(prev) or {})
            breach = cap_breach(latest, held, dict(marks, **{k: v for k, v in closes.items() if v}), cash) \
                if latest else None
            for s, q in held.items():
                close = closes.get(s)
                entry_dd = max(0.0, 1 - float(close) / avg[s]) if close and avg.get(s) else 0.0
                ev = mon.get(s)
                if ev is None:
                    self._log(st, at=day, sym=s, decision="MONITOR_MISSING")
                try:
                    d = K.exit_decision(rank=float(ev["rank"]) if ev else 1.0,
                                        conservative_forecast=float(ev["conservative_forecast"]) if ev else 1.0,
                                        fundamental_eligible=bool(ev["fundamental_eligible"]) if ev else True,
                                        hard_cap_breach=bool(breach), entry_drawdown=entry_dd,
                                        account_drawdown=account_dd)
                except (KeyError, TypeError, ValueError) as e:
                    self._log(st, at=day, sym=s, decision="MONITOR_INVALID: " + str(e)[:60])
                    continue
                if d["queue_next_session"]:
                    st["exits"][s] = {"day": day, "reasons": d["reasons"], "all": d["liquidate_all"]}
                    if d["cooldown_sessions"]:
                        st["cooldown_until"] = C.sessions_between(day, cal.next_trading_day(day, 10).isoformat())[
                            d["cooldown_sessions"]]
                    if d["liquidate_all"]:
                        for o in held:
                            st["exits"][o] = {"day": day, "reasons": ["account drawdown"], "all": True}
        for s, ex in list(st["exits"].items()):
            if s not in held or ex["day"] != day:
                st["exits"].pop(s)
                continue
            out.append(Intent("exit", s, signal_key=f"crd:{day}:{s}:exit", reason=f"{SID} {','.join(ex['reasons'])}",
                              order=OrderSpec(type="market", window_s=self._window(now, day))))
        # the weekly plan, executed once in the next session's window
        if latest is None or st.get("executed") == latest["decision_session"] or any(
                e["all"] for e in st["exits"].values()):
            return out
        if C.prev_session(day) != latest["decision_session"]:
            return out                                          # only the next actual session executes a decision
        st["executed"] = latest["decision_session"]
        if day < (st.get("cooldown_until") or ""):
            self._log(st, at=day, decision="COOLDOWN")
            return out
        want, det = plan(latest, held, marks, cash)
        if want is None:
            self._log(st, at=day, decision=det)
            return out
        self._log(st, at=day, decision="TRADE" if det.get("trade") else "HOLD", gain=det.get("gain"),
                  gate={k: v for k, v in (det.get("gate") or {}).items() if v == "ADMITTED"})
        if not det.get("trade"):
            return out
        adv = latest.get("adv_shares") or {}
        sells = [(s, n) for s, n in want.items() if n < held.get(s, 0)]
        buys = [(s, n) for s, n in want.items() if n > held.get(s, 0)]
        for s, n in sells + buys:
            if s in st["exits"]:
                continue                                        # the queued exit takes precedence
            cur = held.get(s, 0)
            cap = int(np.floor(ADV_CAP * float(adv.get(s) or 0.0)))
            delta = max(-cap, min(cap, n - int(cur)))
            if delta == 0:
                self._log(st, at=day, sym=s, decision="ADV_CAP" if n != cur else "NO_CHANGE")
                continue
            q = quotes.get(s) or {}
            if delta > 0:
                out.append(Intent("enter", s, side="long", qty=float(delta), price_hint=q.get("ask"),
                                  signal_key=f"crd:{latest['decision_session']}:{s}:buy", reason=f"{SID} plan {n}",
                                  order=OrderSpec(window_s=self._window(now, day))))
            else:
                out.append(Intent("exit", s, qty=float(-delta), signal_key=f"crd:{latest['decision_session']}:{s}:sell",
                                  reason=f"{SID} plan {n}", order=OrderSpec(window_s=self._window(now, day))))
        return out

    @staticmethod
    def _window(now, day):
        end = datetime.combine(cal._as_date(day), datetime.strptime(ENTRY_TO, "%H:%M").time(), r10.ET).timestamp()
        return max(30.0, end - float(now))

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [CRD()]
