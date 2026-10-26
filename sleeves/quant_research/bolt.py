"""qr_bracketedoptionlawtransport -- BOLT, Bracketed Option-Law Transport (quant-research-backup@d170596b
research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/bolt: transport_kernel.py, admission.py,
vendored byte-exact under desk/vendor/quant_research/r10/bolt/, and PRACTICAL_PLAYBOOK.md).

The book is the playbook's funded SPY / QQQ account: 50 / 50 by default (no cash target, no leverage, long only),
tilted to 25 / 75 or 75 / 25 around an FOMC announcement or a CPI release when the physical model admits it, from the
first quote at or after 09:35 of the session after the observation until 09:35 of the fifth session after the event,
then restored to 50 / 50. No event stacking; an event whose window holds another FOMC / CPI / Employment Situation
release is excluded.

Information, as the playbook's clock: at 15:45 ET on the fifth session before the event (and the session before, the
same contracts) each index's bracketing expiries -- the latest strictly before the event and the earliest strictly
after it, within four sessions -- give quote boxes; transport_kernel.quote_bounds() bounds the event-spanning
crossing payoff 1{x<=1, y>=1+theta} - 1{x>=1, y<=1-theta} over martingale laws inside the boxes for theta = 0.5%,
1% and 2%: L, U, U - L and their changes since the prior snapshot, both indexes -- the 36 primary features.
Physical model: ridge (penalty 100) on the target QQQ - SPY return over the identical entry / exit clocks, refit on
matured events; admission needs 80 training, 40 calibration and 24 development events (admission.physical_admission)
and an incremental benefit 0.25 x forecast above 50 bp under the 15 / 30 / 45 bp cost scenarios, signs agreeing. Until
the event history holds that support the account holds 50 / 50 and records every event's features and outcome
(the playbook's abstention: "adequate unique event training/calibration/development support"). A 25% drawdown
disables the tilt.

Named divergences:
  1. options: CME E-mini ES / NQ European weekly options and their futures (licensed CME data) are not available --
     SPX (SPXW, PM-settled) and NDX (NDXP) European cash-index options from CBOE's free delayed quotes (about 15
     minutes delayed), each expiry normalised by its put-call-parity forward in place of the fixed futures mid (the
     cash index carries to each expiry; the futures do not); the native-feed gate (admission.native_gate) is
     therefore not applied;
  2. calendars: the BLS CPI and Employment Situation release schedules (bls.gov, fetched by the job `qr_macro_cal`)
     and the desk's FOMC list (14:00 ET statements) as the official calendar snapshot;
  3. grid: each expiry's quoted strikes within +-10% of spot, thinned to at most 41 (spacing >= 0.5% of spot), with
     outer states at 0.5 and 2.0 -- the original state grid is not in the kernel;
  4. the physical model's training events accumulate from the sleeve's own snapshots (no historical CME books);
  5. execution: market orders from the first pass at or after 09:35, sells before buys, on the desk's quotes."""
import json
import math
import os
import re
import time
from datetime import date, datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from ... import calendar as cal
from ...contract import Sleeve, SleeveConfig
from . import common as C

SID = "qr_bracketedoptionlawtransport"
ET = ZoneInfo("America/New_York")
SOURCE = {"repo": "quant-research-backup", "ref": "main", "commit": "d170596b4d3f24712da933683ceb6d9ee95d6937",
          "path": "research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/bolt/code/transport_kernel.py",
          "playbook": "research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/bolt/PRACTICAL_PLAYBOOK.md"}
THETAS = (0.005, 0.01, 0.02)


def _th(th):
    """a theta's key in a snapshot: a string, as sleeve state is JSON (a float key beside "exp" cannot be sorted)"""
    return f"{float(th):g}"


INDEXES = (("SPX", "SPXW"), ("NDX", "NDXP"))
CAL_CACHE = "qr_macro_calendar.json"
BLS = {"CPI_RELEASE": "https://www.bls.gov/schedule/news_release/cpi.htm",
       "EMPLOYMENT_SITUATION": "https://www.bls.gov/schedule/news_release/empsit.htm"}
UA = "Mozilla/5.0 (compatible; master-desk paper research)"
MONTHS = {m: i + 1 for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
                                          "Dec"])}
RIDGE, EXIT_SESSIONS, OBS_SESSIONS = 100.0, 5, 5
SUPPORT = (80, 40, 24)
COSTS_BP = (15, 30, 45)


def _kernel():
    from ...vendor.quant_research.r10.bolt import admission, transport_kernel
    return transport_kernel, admission


# --------------------------------------------------------------------------------------------- the calendar
def parse_bls(html):
    """the 'Schedule of Releases' table: [(release date ISO, 'HH:MM')]."""
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    out = []
    for m in re.finditer(r"([A-Z][a-z]{2})\.? (\d{1,2}), (\d{4}) (\d{2}):(\d{2}) (AM|PM)", text):
        mon, day, yr, hh, mm, ap = m.groups()
        if mon not in MONTHS:
            continue
        h = int(hh) % 12 + (12 if ap == "PM" else 0)
        out.append((date(int(yr), MONTHS[mon], int(day)).isoformat(), f"{h:02d}:{mm}"))
    return sorted(set(out))


def run_calendar(root, now, fetch=None):
    """the job `qr_macro_cal`: BLS CPI / Employment Situation release schedules -> cache (kept when a fetch fails)."""
    from ...data.http import get
    fetch = fetch or (lambda url: get(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"}, timeout=30,
                                      as_text=True))
    p = os.path.join(root, "cache", CAL_CACHE)
    try:
        doc = json.load(open(p))
    except (OSError, ValueError):
        doc = {}
    got = {}
    for k, url in BLS.items():
        try:
            body = fetch(url)
            body = body.decode("utf-8", "replace") if isinstance(body, bytes) else str(body)
            rows = parse_bls(body)
            if rows:
                got[k] = rows
        except Exception as e:                                        # keep the last snapshot
            got.setdefault("errors", []).append(f"{k}: {type(e).__name__}")
    for k in BLS:
        if k in got:
            known = {tuple(x) for x in doc.get(k, [])}
            doc[k] = sorted(known | {tuple(x) for x in got[k]})
    doc["fetched_at"] = now
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".tmp", "w") as f:
        json.dump(doc, f)
    os.replace(p + ".tmp", p)
    return {k: len(doc.get(k, [])) for k in BLS}


def events(cal_doc, fomc):
    """[(id, class, aware ET datetime)] -- FOMC statements 14:00, CPI 08:30 -- without the colliding ones."""
    from ...feeds import FOMC_2025_2027
    raw = [("FOMC_ANNOUNCEMENT", d, "14:00") for d in (fomc or FOMC_2025_2027)]
    raw += [("CPI_RELEASE", d, t) for d, t in (cal_doc or {}).get("CPI_RELEASE", [])]
    other = [("EMPLOYMENT_SITUATION", d, t) for d, t in (cal_doc or {}).get("EMPLOYMENT_SITUATION", [])]
    allev = [(k, datetime.combine(date.fromisoformat(d), dtime(*map(int, t.split(":"))), ET)) for k, d, t in raw + other]
    out = []
    for k, d, t in raw:
        e = datetime.combine(date.fromisoformat(d), dtime(*map(int, t.split(":"))), ET)
        obs = observation_session(e.date().isoformat())
        ex = exit_session(e.date().isoformat())
        if obs is None:
            continue
        lo = datetime.combine(date.fromisoformat(obs), dtime(15, 45), ET)
        hi = datetime.combine(date.fromisoformat(ex), dtime(9, 35), ET)
        if any(lo < e2 < hi for k2, e2 in allev if (k2, e2) != (k, e)):
            continue                                                  # collision: another release in the window
        out.append((f"{k}:{d}", k, e))
    return sorted(out, key=lambda x: x[2])


def observation_session(event_day):
    d = cal._as_date(event_day)
    k = 0
    while k < OBS_SESSIONS:
        d -= timedelta(days=1)
        if cal.is_trading_day(d):
            k += 1
    return d.isoformat()


def exit_session(event_day):
    d = cal._as_date(event_day)
    k = 0
    while k < EXIT_SESSIONS:
        d += timedelta(days=1)
        if cal.is_trading_day(d):
            k += 1
    return d.isoformat()


# --------------------------------------------------------------------------------------------- the bounds
def expiry_close(exp):
    return datetime.combine(date.fromisoformat(exp), dtime(16, 0), ET)


def bracket(rows, root, event_dt, snap_dt):
    """(T-minus, T-plus): the latest expiry strictly before the event and the earliest strictly after, both after
    the snapshot and within four sessions of the event."""
    exps = sorted({r["expiration"] for r in rows if r.get("root") == root})
    before = [e for e in exps if snap_dt < expiry_close(e) < event_dt]
    after = [e for e in exps if expiry_close(e) > event_dt]
    if not before or not after:
        return None
    tm, tp = before[-1], after[0]
    ed = event_dt.date()
    if C.sessions_between(tm, ed.isoformat()).__len__() - 1 > 4 or len(C.sessions_between(ed.isoformat(), tp)) - 1 > 4:
        return None
    return tm, tp


def forward(rows, root, exp):
    """the expiry's put-call-parity forward at the strike where call and put mids are closest (the futures' role)."""
    calls, puts = {}, {}
    for r in rows:
        if r.get("root") != root or r["expiration"] != exp or not r.get("bid") or not r.get("ask"):
            continue
        (calls if r["type"] == "call" else puts)[float(r["strike"])] = (r["bid"] + r["ask"]) / 2
    common = sorted(set(calls) & set(puts))
    if not common:
        return None
    k = min(common, key=lambda x: (abs(calls[x] - puts[x]), x))
    return k + calls[k] - puts[k]


def quotes_for(rows, root, exp, spot):
    """normalised (strike, bid, ask) calls of one expiry -- prices over the expiry's forward `spot` -- two-sided,
    ordered, relative spread <= 20%, within +-10% of the forward, thinned to strikes >= 0.5% apart (at most 41)."""
    q = []
    for r in rows:
        if r.get("root") != root or r["expiration"] != exp or r["type"] != "call":
            continue
        b, a, k = r.get("bid"), r.get("ask"), float(r["strike"])
        if not b or not a or b <= 0 or a <= b:
            continue
        mid = (a + b) / 2
        if (a - b) / max(mid, 0.05) > 0.2 or not 0.9 <= k / spot <= 1.1:
            continue
        q.append((k / spot, b / spot, a / spot))
    q.sort()
    out, last = [], -1.0
    for x in q:
        if x[0] - last >= 0.005:
            out.append(x)
            last = x[0]
    return out[:41]


def snapshot(chains, spots, event_dt, snap_dt):
    """{index: {theta: (L, U), "exp": (tm, tp)}} at one snapshot; None for an index without a usable bracket."""
    TK, _ = _kernel()
    out = {}
    for idx, root in INDEXES:
        rows, spot = chains.get(idx) or [], spots.get(idx)
        br = bracket(rows, root, event_dt, snap_dt) if spot else None
        if br is None:
            out[idx] = None
            continue
        fb, fa = forward(rows, root, br[0]), forward(rows, root, br[1])
        if not fb or not fa:
            out[idx] = None
            continue
        qb, qa = quotes_for(rows, root, br[0], fb), quotes_for(rows, root, br[1], fa)
        if len(qb) < 9 or len(qa) < 9:                         # minimum usable distinct strikes per expiry
            out[idx] = None
            continue
        x = np.array(sorted({0.5, 2.0} | {k for k, _, _ in qb}))
        y = np.array(sorted({0.5, 2.0} | {k for k, _, _ in qa}))
        res = {"exp": br, "forward": (fb, fa), "spot": spot}
        try:
            for th in THETAS:
                b = TK.quote_bounds(x, y, qb, qa, TK.crossing_payoff(x, y, th), mean=1.0)
                res[_th(th)] = (float(b.lower), float(b.upper))
        except ValueError as e:                                  # infeasible / blocked law: no feature this event
            out[idx] = {"blocked": str(e)[:120]}
            continue
        out[idx] = res
    return out


def features(now_snap, prev_snap):
    """the 36 primary features: per index and theta L, U, U - L and their changes since the prior snapshot."""
    f = []
    for idx, _ in INDEXES:
        a, b = (now_snap or {}).get(idx), (prev_snap or {}).get(idx)
        for th in map(_th, THETAS):
            if not a or th not in a or not b or th not in b:
                return None
            L, U = a[th]
            L0, U0 = b[th]
            f += [L, U, U - L, L - L0, U - U0, (U - L) - (U0 - L0)]
    return f


# --------------------------------------------------------------------------------------------- the physical model
def ridge_fit(X, y, penalty=RIDGE):
    """train-only standardisation, intercept unpenalised."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    A = Z.T @ Z + penalty * np.eye(Z.shape[1])
    beta = np.linalg.solve(A, Z.T @ (y - y.mean()))
    return {"mu": mu.tolist(), "sd": sd.tolist(), "beta": beta.tolist(), "b0": float(y.mean())}


def ridge_predict(m, x):
    z = (np.asarray(x, float) - np.asarray(m["mu"])) / np.asarray(m["sd"])
    return float(m["b0"] + z @ np.asarray(m["beta"]))


def decide_tilt(history, feats, drawdown):
    """the requested weights for the event: (spy, qqq). Matured events in time order split train / calibration /
    development (oldest first); admission per admission.physical_admission over the cost scenarios."""
    _, AD = _kernel()
    done = [h for h in history if h.get("label") is not None and h.get("features")]
    n = len(done)
    tr_n = max(0, n - SUPPORT[1] - SUPPORT[2])
    status = AD.physical_admission([], 0.0, tr_n, min(SUPPORT[1], max(0, n - tr_n)), max(0, n - tr_n - SUPPORT[1]),
                                   "INPUT_SCHEMA_VALID_PHYSICAL_MODEL_STILL_REQUIRED")
    if feats is None or drawdown >= 0.25 or status == "NO_TRADE_INSUFFICIENT_PHYSICAL_SUPPORT":
        return (0.5, 0.5), status if feats is not None else "NO_FEATURES"
    train = done[:tr_n]
    cal_ = done[tr_n:tr_n + SUPPORT[1]]
    model = ridge_fit([h["features"] for h in train], [h["label"] for h in train])
    resid = [h["label"] - ridge_predict(model, h["features"]) for h in cal_]
    f = ridge_predict(model, feats)
    lcb = f - 1.645 * (np.std(resid, ddof=1) / math.sqrt(len(resid)) if len(resid) > 1 else 0.0)
    sign = 1.0 if f > 0 else -1.0
    incr = [0.25 * abs(f) - 2 * c / 10000 * 0.25 for c in COSTS_BP]
    status = AD.physical_admission(incr, sign * lcb, tr_n, len(cal_), n - tr_n - len(cal_),
                                   "INPUT_SCHEMA_VALID_PHYSICAL_MODEL_STILL_REQUIRED")
    if status != "RESEARCH_ADMISSION_ONLY_NO_EXECUTION_AUTHORIZATION":
        return (0.5, 0.5), status
    return ((0.25, 0.75) if f > 0 else (0.75, 0.25)), status


# --------------------------------------------------------------------------------------------- the sleeve
def feed_chains(f, s, now, arg):
    """SPX / NDX chains (calls, 0-12 days) and spot levels on the snapshot passes only."""
    if not (hasattr(s, "snapshot_due") and s.snapshot_due(now)):
        return None
    out = {"chains": {}, "spots": {}, "t": now}
    for idx, _ in INDEXES:
        rows = f.chains(idx, dte_min=0, dte_max=12)
        if rows:
            out["chains"][idx] = rows
            out["spots"][idx] = f.hub.options.spot(idx)
    return out


class Bolt(Sleeve):
    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=300, universe=("SPY", "QQQ"), capital=1_000_000.0,
            schedule="rth", needs={"feeds": ["qr_macro_cal", "qr_bolt_chains"],
                                   "quotes": {"source": "equity", "symbols": ["SPY", "QQQ"]}},
            params={"default": {"SPY": 0.5, "QQQ": 0.5}, "tilts": [[0.25, 0.75], [0.75, 0.25]],
                    "thetas": list(THETAS), "ridge": RIDGE, "exit_sessions": EXIT_SESSIONS, "support": SUPPORT,
                    "margin_bp": 50, "cost_scenarios_bp": COSTS_BP, "drawdown_disable": 0.25},
            source=SOURCE, state_schema={"snaps": "dict", "events": "dict", "active": "dict",
                                         "target": "dict|None",           # None: decided, not yet sized
                                         "peak": "float", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def _events(self):
        doc = None
        if self.engine is not None:
            try:
                doc = json.load(open(os.path.join(self.engine.root, "cache", CAL_CACHE)))
            except (OSError, ValueError):
                doc = None
        return events(doc, None)

    def snapshot_due(self, now):
        """15:45 ET passes on an observation session or the session before it."""
        d = cal._as_date(now).isoformat()
        hm = datetime.fromtimestamp(now, tz=ET).strftime("%H:%M")
        if not ("15:45" <= hm < "15:55"):
            return False
        for _, _, e in self._events():
            obs = observation_session(e.date().isoformat())
            if d in (obs, cal.prev_trading_day(obs).isoformat()):
                return True
        return False

    def signal(self, view):
        st = dict(view.state or {})
        for k, v in (("snaps", {}), ("events", {}), ("active", {}), ("log", [])):
            st.setdefault(k, v)
        self._st = st
        now, session = float(view.now), view.session
        if not cal.is_rth(now):
            return []
        evs = events((view.extra or {}).get("qr_macro_cal"), None)
        ch = (view.extra or {}).get("qr_bolt_chains")
        if ch:                                                     # the 15:45 snapshots
            snap_dt = datetime.fromtimestamp(now, tz=ET)
            for eid, kind, e in evs:
                obs = observation_session(e.date().isoformat())
                if session in (obs, cal.prev_trading_day(obs).isoformat()) and f"{eid}@{session}" not in st["snaps"]:
                    st["snaps"][f"{eid}@{session}"] = snapshot(ch["chains"], ch["spots"], e, snap_dt)
        nav = C.nav(view)
        st["peak"] = max(float(st.get("peak") or 0.0), nav)
        dd = 1 - nav / st["peak"] if st["peak"] > 0 else 0.0
        hm = datetime.fromtimestamp(now, tz=ET).strftime("%H:%M")
        weights = st.get("weights") or {"SPY": 0.5, "QQQ": 0.5}
        act = st.get("active") or {}
        if act and session >= act["exit_on"] and hm >= "09:35":    # restore 50 / 50 at the frozen exit
            ev = st["events"].setdefault(act["id"], {})
            ev["exit"] = {"day": session, "spy": _px(view, "SPY"), "qqq": _px(view, "QQQ")}
            st["active"] = {}
            weights = {"SPY": 0.5, "QQQ": 0.5}
            st["target"] = None
        for eid, kind, e in evs:                                   # a new event: decide at the entry session
            obs = observation_session(e.date().isoformat())
            entry = cal.next_trading_day(obs).isoformat()
            if session != entry or hm < "09:35" or eid in st["events"] or st.get("active"):
                continue
            feats = features(st["snaps"].get(f"{eid}@{obs}"), st["snaps"].get(f"{eid}@{cal.prev_trading_day(obs)}"))
            hist = [dict(v, id=k) for k, v in sorted(st["events"].items())]
            w, status = decide_tilt(hist, feats, dd)
            st["events"][eid] = {"features": feats, "status": status, "weights": list(w),
                                 "entry": {"day": session, "spy": _px(view, "SPY"), "qqq": _px(view, "QQQ")}}
            if w != (0.5, 0.5):
                st["active"] = {"id": eid, "exit_on": exit_session(e.date().isoformat())}
                weights = {"SPY": w[0], "QQQ": w[1]}
                st["target"] = None
            st["log"] = (st["log"] + [{"at": session, "event": eid, "status": status}])[-100:]
        for eid, ev in st["events"].items():                       # labels: QQQ - SPY over the frozen clocks
            if ev.get("label") is None and ev.get("exit") and ev.get("entry"):
                a, b = ev["entry"], ev["exit"]
                if a.get("spy") and a.get("qqq") and b.get("spy") and b.get("qqq"):
                    ev["label"] = (b["qqq"] / a["qqq"] - 1) - (b["spy"] / a["spy"] - 1)
        for eid, kind, e in evs:                                   # exits of untilted events still label the event
            ev = st["events"].get(eid)
            if ev and not ev.get("exit") and session >= exit_session(e.date().isoformat()) and hm >= "09:35":
                ev["exit"] = {"day": session, "spy": _px(view, "SPY"), "qqq": _px(view, "QQQ")}
        st["weights"] = weights
        if not st.get("target"):
            t = C.target_shares(view, weights)
            if t is None:
                return []
            st["target"] = t
        out, _ = C.rebalance(view, st["target"], f"bolt:{weights['SPY']}:{session}",
                             f"{SID} SPY / QQQ {weights['SPY']:.2f} / {weights['QQQ']:.2f}")
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def _px(view, s):
    q = (view.quotes or {}).get(s) or {}
    return q.get("last") or q.get("ask") or q.get("bid")


def feed_calendar(f, s, now, arg):
    root = getattr(getattr(s, "engine", None), "root", None)
    if not root:
        return None
    try:
        return json.load(open(os.path.join(root, "cache", CAL_CACHE)))
    except (OSError, ValueError):
        return None


def sleeves():
    return [Bolt()]
