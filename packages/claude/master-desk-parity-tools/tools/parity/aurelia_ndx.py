"""aurelia_ndx (the Aurelia book): the SOURCE desk's own code (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e,
run in its own tree: AURELIA_SRC) vs the port, two ways.

  A. exposures  paper._aurelia(through) — the source parsing the same raw Yahoo chart payloads through its own
                yahoo._download (requests stubbed to serve them) — vs desk/feedlib/aurelia.exposures on the port's
                parse of those payloads: ndx, gold, apex_3x, trend, vol, as_of on every sampled session.
  B. plans      paper.run(execute=False) — the real run(): band against its saved plan, the brain's posture
                (team.brief stubbed to the real judgment.posture / apply_posture on the case tape), frozen
                targets, build_plan with its own _margin_requirements over the stub broker's asset rows, the
                submit block — vs aurelia_ndx.decide() on the same inputs, over multi-step sequences (a decision,
                a re-run the same day on moved marks, the next decision on filled or unfilled holdings, a stress
                tape). Compared per step: orders, book_ndx, book_gold, targets, submit_block, orders_scaled.
Stubbed in the source: the Alpaca account / positions / clock / asset rows (the case's), its exposure cache and
completed prices (the case's), the kill switch (off), the record-only shadows; its plan and ledger files go to a
scratch STATE_DIR."""
import json
import os
import random
from datetime import date, datetime, timedelta

from desk import calendar as cal
from desk.feedlib import aurelia as A
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("aurelia_ndx")
PORT = ("^NDX", "QQQ", "GC=F", "^VIX")
SHADOW = ("^IRX", "IEF", "^TNX", "GLD", "USO", "UUP", "^SOX", "SMH", "BTC-USD")
N_SEQS = 400

SRC = r'''
import json, pathlib, tempfile, types
import pandas as pd
import desk.data.yahoo as Y
RAW = PAYLOAD["raw"]
class Resp:
    status_code = 200
    def __init__(self, body): self.body = body
    def json(self): return self.body
    def raise_for_status(self): pass
Y.requests = types.SimpleNamespace(get=lambda url, params=None, headers=None, timeout=None: Resp(RAW[url.rsplit("/", 1)[1]]))
FR = {}
def get_daily(symbol, max_age_hours=12.0, refresh=False):
    if symbol not in FR:
        FR[symbol] = Y._download(symbol)
    return FR[symbol]
Y.get_daily = get_daily
import desk.paper as P
out_a = []
for d in PAYLOAD["dates"]:
    e = P._aurelia(pd.Timestamp(d), refresh=False)
    out_a.append({k: e[k] for k in ("as_of", "aurelia_ndx", "aurelia_gold", "apex_3x", "trend", "vol")})
import desk.config as CFG
tmp = pathlib.Path(tempfile.mkdtemp())
CFG.STATE_DIR = tmp
P.PLAN_PATH, P.EXPOSURE_CACHE = tmp / "paper_plan.json", tmp / "exposure_cache.json"
P.load_env = lambda: None
P._shadow = lambda through, refresh=False, exp=None: {"gestalt": None, "n6": None, "gestalt_error": "harness"}
P._variance_value = lambda through: {"action": "unavailable", "orders": False}
import desk.ausar_gate as AG
AG.kill_switch_on = lambda: False
import desk.brain.team as TEAM
from desk.brain.judgment import posture, apply_posture
ST = {}
def brief(clock, book_ndx, book_gold):
    v = posture(ST["tape"], [], [])
    n, g = apply_posture(book_ndx, book_gold, v["level"])
    return {"book_ndx": n, "book_gold": g, "level": v["level"], "reasons": v["reasons"], "public": {"level": v["level"]}}
TEAM.brief = brief
class Alp:
    def account(self): return dict(ST["account"])
    def positions(self): return [{"symbol": s, "qty": str(q), "side": "long"} for s, q in ST["held"].items() if q]
    def clock(self): return dict(ST["clock"])
    def asset(self, sym):
        m = ST["maint"].get(sym)
        if m is None:
            raise RuntimeError("no asset row")
        return {"maintenance_margin_requirement": m}
    def list_orders(self, status="all"): return []
P.alpaca = Alp()
P._cached_aurelia = lambda through, refresh=False: dict(ST["exp"])
P.completed_prices = lambda through, refresh=False: dict(ST["prices"])
out_b = []
for seq in PAYLOAD["seqs"]:
    if P.PLAN_PATH.exists():
        P.PLAN_PATH.unlink()
    res = []
    for step in seq:
        ST.clear(); ST.update(step)
        plan = P.run(execute=False)
        res.append({"orders": sorted([o["symbol"], o["side"], int(o["qty"])] for o in plan["orders"]),
                    "book_ndx": plan["book_ndx"], "book_gold": plan["book_gold"],
                    "targets": {k: int(v) for k, v in plan["targets"].items()}, "submit_block": plan["submit_block"],
                    "orders_scaled": bool(plan["orders_scaled"])})
    out_b.append(res)
print(json.dumps({"a": out_a, "b": out_b}))
'''


def _raw(sym, now):
    return A._fetch(sym, now)


def _dates(rec):
    """sampled decision sessions: the last 120 sessions of the history and every 20th session from 2005."""
    ds = [d for d in rec["dates"] if d >= "2005-01-03"]
    tail = ds[-121:-1]
    return sorted(set(tail) | set(ds[:-121:20]))


def _iso(ts):
    return datetime.fromtimestamp(ts, tz=ET).isoformat()


def _clock(rnd, as_of):
    """a moment in a session after `as_of` (usually the next one): open in the window, after the cutoff, before
    the open, a same-day bar or stale data."""
    u = rnd.random()
    sess = cal.next_trading_day(as_of)
    if u < 0.06:
        sess = date.fromisoformat(as_of)                          # the decision's own session: same_day_bar
    elif u < 0.10:
        sess = cal.next_trading_day(as_of, 5)                     # more than 5 calendar days later: stale_data
    op, cl = cal.session_open(sess), cal.session_close(sess)
    v = rnd.random()
    if v < 0.12:
        t = op - rnd.randint(60, 3000)                            # before the open
    elif v < 0.22:
        t = cl - rnd.randint(0, 899)                              # inside the 15-minute cutoff
    else:
        t = op + rnd.randint(0, int(cl - op - 901))
    is_open = op <= t < cl
    nc = cl if t < cl else cal.session_close(cal.next_trading_day(sess))
    return {"is_open": is_open, "timestamp": _iso(t), "next_close": _iso(nc), "next_open": _iso(op)}


def _exp(rnd, as_of, base=None):
    def pick(lo, hi, prev):
        u = rnd.random()
        if u < 0.08:
            return 0.0
        if prev is not None and u < 0.5:
            return max(0.0, prev + rnd.choice((-1, 1)) * rnd.choice((0.05, 0.15, 0.2, 0.25, 0.6)))
        return rnd.uniform(lo, hi)
    return {"as_of": as_of, "aurelia_ndx": pick(0.0, 3.6, (base or {}).get("aurelia_ndx")),
            "aurelia_gold": pick(0.0, 1.4, (base or {}).get("aurelia_gold")), "apex_3x": 2.0, "gestalt": None,
            "n6": None, "signal_id": A.SIGNAL_ID, "trend": 1.0, "vol": 0.2}


def _tape(rnd):
    u = rnd.random()
    if u < 0.12:
        return {"vix": rnd.uniform(40, 70), "ndx_day": rnd.uniform(-0.04, 0.02)}
    if u < 0.24:
        return {"vix": rnd.uniform(25, 40), "ndx_day": rnd.uniform(-0.04, 0.02)}
    if u < 0.32:
        return {"vix": rnd.uniform(12, 24), "ndx_day": rnd.uniform(-0.12, -0.05)}
    return {"vix": rnd.uniform(11, 24.9), "ndx_day": rnd.uniform(-0.049, 0.04)}


def _sequences(rnd, n):
    days = []
    d = date(2025, 1, 2)
    while d <= date(2026, 9, 30):
        if cal.is_trading_day(d):
            days.append(d.isoformat())
        d += timedelta(days=1)
    seqs = []
    for _ in range(n):
        as_of = rnd.choice(days)
        prices = {"QQQ": rnd.uniform(300, 650), "TQQQ": rnd.uniform(25, 130), "GLD": rnd.uniform(150, 420),
                  "BIL": rnd.uniform(91.0, 92.0)}
        held = {s: (rnd.randint(0, 2500) if rnd.random() < 0.5 else 0) for s in prices}
        maint = {s: rnd.choice((None, 30, 50, 75, 100)) for s in prices}
        equity = rnd.uniform(40_000, 2_000_000)
        exp = _exp(rnd, as_of)
        steps = []
        for k in range(4):
            if k == 1:                                          # a re-run the same day on moved marks
                equity *= rnd.uniform(0.97, 1.03)
            elif k >= 2:                                        # the next decision: fills landed (or not)
                last = steps[-1]
                if rnd.random() < 0.8:
                    held = dict(last["_targets"]) if last.get("_targets") is not None else held
                as_of = cal.next_trading_day(as_of).isoformat()
                prices = {s: p * rnd.uniform(0.96, 1.04) for s, p in prices.items()}
                equity *= rnd.uniform(0.95, 1.05)
                exp = _exp(rnd, as_of, exp)
            tape = _tape(rnd) if k == 3 else {"vix": rnd.uniform(11, 24), "ndx_day": rnd.uniform(-0.03, 0.03)}
            lmv = sum(abs(q) * prices[s] for s, q in held.items())
            bp = max(0.0, 2.0 * equity - lmv)
            steps.append({"exp": dict(exp), "prices": dict(prices), "held": dict(held), "maint": dict(maint),
                          "tape": tape, "clock": _clock(rnd, as_of), "equity": equity,
                          "account": {"equity": str(equity), "regt_buying_power": str(bp), "buying_power": str(bp)},
                          "_targets": None})
            # the port's targets after this step decide the simulated fills of the next decision (both sides share)
            port = F.decide(dict(exp, vix=tape["vix"], ndx_day=tape["ndx_day"], requirements=_req(maint)),
                            steps[-2]["_plan"] if k else None, {s: q for s, q in held.items() if q}, prices, equity,
                            steps[-1]["clock"])
            steps[-1]["_plan"] = port
            steps[-1]["_targets"] = {s: int(port["targets"].get(s, 0)) for s in prices}
        seqs.append(steps)
    return seqs


def _req(maint):
    out = dict(A.FALLBACK_REQ)
    for s, m in maint.items():
        if m is not None:
            out[s] = max(A.FALLBACK_REQ[s], float(m) / 100.0, 0.50)
    return out


def run():
    import time
    now = time.time()
    raw = {s: _raw(s, now) for s in PORT + SHADOW}
    recs = {s: A.parse(raw[s], s) for s in PORT}
    frames = {s: A.frame(r) for s, r in recs.items()}
    dates = _dates(recs["^NDX"])
    rnd = random.Random(20261016)
    seqs = _sequences(rnd, N_SEQS)
    payload = {"raw": raw, "dates": dates,
               "seqs": [[{k: v for k, v in st.items() if not k.startswith("_")} for st in seq] for seq in seqs]}
    src = old_run(SRC, payload, timeout=3600, tree=os.environ.get("AURELIA_SRC"))
    diffs = []
    for d, o in zip(dates, src["a"]):
        p = A.exposures(frames, date.fromisoformat(d))
        p = {k: p[k] for k in ("as_of", "aurelia_ndx", "aurelia_gold", "apex_3x", "trend", "vol")}
        if p != o:
            diffs.append({"part": "A", "through": d, "source": o, "port": p})
    stats = {"steps": 0, "orders": 0, "frozen_reruns": 0, "scaled": 0, "blocks": {}, "postures": {}, "in_band": 0}
    for seq, so in zip(seqs, src["b"]):
        for st, o in zip(seq, so):
            pl = st["_plan"]
            p = {"orders": sorted([x["symbol"], x["side"], int(x["qty"])] for x in pl["orders"]),
                 "book_ndx": pl["book_ndx"], "book_gold": pl["book_gold"],
                 "targets": {k: int(v) for k, v in pl["targets"].items()}, "submit_block": pl["submit_block"],
                 "orders_scaled": bool(pl["orders_scaled"])}
            if p != o:
                diffs.append({"part": "B", "step": {k: v for k, v in st.items() if not k.startswith("_")},
                              "source": o, "port": p})
            stats["steps"] += 1
            stats["orders"] += len(o["orders"])
            stats["scaled"] += o["orders_scaled"]
            stats["in_band"] += not o["orders"]
            b = o["submit_block"] or "sendable"
            stats["blocks"][b] = stats["blocks"].get(b, 0) + 1
            lv = pl["posture"]["level"]
            stats["postures"][lv] = stats["postures"].get(lv, 0) + 1
        stats["frozen_reruns"] += sum(1 for k in (1,) if seq[k]["exp"]["as_of"] == seq[0]["exp"]["as_of"])
    res = {"sleeve": "aurelia_ndx", "cases": len(dates) + stats["steps"], "identical": len(dates) + stats["steps"] - len(diffs),
           "diffs": diffs[:10], "n_diffs": len(diffs), "exposure_dates": len(dates),
           "exposure_span": [dates[0], dates[-1]], "payload_last_dates": {s: recs[s]["dates"][-1] for s in PORT},
           "plan_stats": stats,
           "method": "source paper._aurelia / paper.run(execute=False) in its own tree vs feedlib.aurelia.exposures "
                     "/ aurelia_ndx.decide"}
    write_receipt("aurelia_ndx", res)
    return res
