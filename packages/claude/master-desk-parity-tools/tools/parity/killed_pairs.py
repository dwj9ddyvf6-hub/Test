"""killed_pairs_distance_coint: the study's run_fold (vendored 05_backtest_dev.py, unmodified, emit_trades=True) vs
the desk's formation (killed_data.form_pairs) and the sleeve stepped session by session through its trading window.

Per case: a synthetic universe (48-70 names on real trading days: one fold's 12-month formation + 6-month trading
window) driven by a few common factors so close pairs exist, with cheap, thin, incomplete names and bad ticks (huge
moves on tiny volume). The 03 liquidity filters and 04 bad-tick cleaning are applied (killed_data's restatement,
unit-tested) to build run_fold's inputs (the cleaned adjusted frame and the fold's filter list). Compared exactly:
the formed-on count, the top-20 SSD pairs (order included), the Engle-Granger top-20, and every round trip of the
top-20 (entry date, exit date, direction, outcome: converge / adverse_stop / force_close) against the sleeve's state
transitions (it reads z on the session's close as its live price; the trade is that close's market-on-close).

killed_pairs_news_filtered (V1, pair-trading/IMPROVEMENTS.md section C, blob da13866b; it died at feasibility, so no
runner exists - v1_feasibility_death_2026-10-02.md, blob 31334e35): on the first N_V1 cases, the same fold, universe and
formation. Source: run_fold itself, its trade_pair calls for the top-20 recorded (each pair's formation-normalised
trading-window series, formation mean / sigma, trading dates), and the vendored trade_pair's loop with the
pre-registration's three rule changes, restated (trade_pair_v1): entry |z| > 2.5 only when neither leg had
firm-specific news (earnings, dividend, abnormal news) in the prior 5 trading days, exit |z| < 0.5 or 10 trading days
after entry (the time stop replacing the 4-sigma stop), force close at the window end, pairs may reopen. Per leg
random news items (any hour, weekends too), earnings and ex-dividend dates. Sleeve: PairsNewsFiltered stepped twice a
session (50 and 25 minutes before the close) on Views whose news gate is the family's own producer: the
killed_pairs_news job (killed_data.pairs_news_job / news_gate, unmodified) run on its family schedule
(killed_studies.JOBS) against stubbed sources - Alpaca /v1beta1/news, or Yahoo RSS headlines in a quarter of the
cases - and the Nasdaq calendars pre-cached, read back through feed_pairs_news; positions filled from the sleeve's own
intents. Compared exactly: every tranche field (both legs of every round trip: id, side, units, entry / exit session,
moment, pass, reference price, return, reasons) and every pass's intents (the z observations, and the source's trades
through common.TrancheBook.intents). The source's gate is the producer's window (named divergence: the 5 sessions
before today through the job's last run before the decision); the pre-registered window (the prior 5 trading days,
the decision day excluded) is measured against it (v1.literal_*). Temp files: a per-case directory under
.parity_tmp/ in the worktree, removed after the case."""
import json
import os
import random
import shutil
import sys
from bisect import bisect_left
from datetime import date, datetime, time as dtime, timedelta, timezone
from email.utils import format_datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd

from desk import calendar as cal
from desk import schedule
from desk.contract import View
from desk.feedlib import killed_data as KD
from desk.sleeves.families import killed_studies as FAM
from desk.sleeves.killed import common as K
from desk.sleeves.killed import pairs as PR
from desk.util import ET, write_json_atomic

from . import ROOT, write_receipt

N_CASES = 1000
N_V1 = 400
FOLDS = [("2024-07-01", "2025-06-30", "2025-07-01", "2025-12-31"),
         ("2025-01-01", "2025-12-31", "2026-01-01", "2026-06-30")]


def sessions(a, b):
    out, d = [], date.fromisoformat(a)
    while d <= date.fromisoformat(b):
        if cal.is_trading_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def gen_case(rnd, fold):
    fs, fe, ts, te = fold
    days = sessions(fs, te)
    nf = rnd.randint(2, 4)
    factors = [[rnd.gauss(0, 0.012) for _ in days] for _ in range(nf)]
    series = {}
    for k in range(rnd.randint(48, 70)):
        f = rnd.randrange(nf)
        idio = rnd.choice([0.001, 0.002, 0.004, 0.008, 0.015])
        px = rnd.uniform(3, 300)
        vol = rnd.uniform(4e4, 5e5)
        rows, skip = [], rnd.random() < 0.08
        for i, d in enumerate(days):
            px *= 1 + factors[f][i] + rnd.gauss(0, idio)
            v = vol * rnd.uniform(0.5, 1.5)
            adj = px
            if rnd.random() < 0.0003 and d <= fe:                         # bad prints: formation only
                adj, v = px * rnd.choice([0.3, 2.5]), v * 0.001          # a bad tick
            if skip and fs <= d <= fe and rnd.random() < 0.08:
                continue                                                 # an incomplete name
            rows.append((d, round(adj, 4), round(adj * v, 2), round(v, 2)))
        series[f"P{k:02d}"] = rows
    return days, series


def source(P, series, fold, doc):
    fs, fe, ts, te = fold
    names = doc["universe"]
    rows = []
    for s in names:
        w = [r for r in series[s] if fs <= r[0] <= fe]
        med_v = float(np.median([r[3] for r in w]))
        sr = [r for r in series[s] if fs <= r[0] <= te]
        adj = KD.clean_bad_ticks([r[1] for r in sr], [r[3] for r in sr], med_v)
        rows += [(s, r[0], a if a is not None else np.nan) for r, a in zip(sr, adj)]
    adj = pd.DataFrame(rows, columns=["symbol", "date", "c_adj"]).pivot(index="date", columns="symbol",
                                                                        values="c_adj").sort_index()
    adj.index = adj.index.astype(str)
    filt = {"symbols": names, "expected_days": doc["expected_days"]}
    return P.run_fold(1, fs, fe, ts, te, adj, filt, emit_trades=True)


def sleeve_trades(series, fold, doc, days):
    fs, fe, ts, te = fold
    sl = PR.PairsDistance()
    st, trades, prev = {}, [], {}
    tdays = [d for d in days if ts <= d <= te]
    legs = {p["a"] for p in doc["pairs"]} | {p["b"] for p in doc["pairs"]}
    by = {s: {r[0]: r for r in series[s]} for s in legs}
    full = {s: [{"t": datetime.fromisoformat(r[0]).replace(hour=9, minute=30, tzinfo=ET).timestamp(),
                 "o": r[1], "h": r[1], "l": r[1], "c": r[1], "v": r[3]} for r in series[s]] for s in legs}
    days_of = {s: [r[0] for r in series[s]] for s in legs}
    import bisect
    for d in tdays:
        now = cal.session_close(d) - 25 * 60                   # inside the auction window (early closes too)
        bars = {s: full[s][:bisect.bisect_left(days_of[s], d)] for s in legs}
        quotes = {s: {"last": by[s][d][1], "t": now} for s in legs if d in by[s]}
        v = View(now=now, session=d, bars={"1d": bars}, quotes=quotes, state=st,
                 extra={"killed_pairs": doc, "pending_orders": [], "closed_trades": []})
        sl.signal(v)
        st = sl._st
        for p in doc["pairs"]:
            key = f"{p['a']}/{p['b']}"
            cur = (st.get("pairs") or {}).get(key) or {}
            s0, s1 = prev.get(key, 0), cur.get("state", 0)
            if s0 != 0 and s1 == 0:                      # one step per session: a close never reopens the same day
                tr = next(t for t in reversed(trades) if t["pair"] == key and t["exit_date"] is None)
                tr["exit_date"], tr["outcome"] = d, cur.get("event")
            elif s0 == 0 and s1 != 0:
                trades.append({"pair": key, "direction": s1, "entry_date": d, "exit_date": None, "outcome": None})
            prev[key] = s1
    return trades


# -- V1: the news-filtered entry / exit path -----------------------------------------------------------------------
SID_V1 = "killed_pairs_news_filtered"
V1_FIELDS = ("id", "sym", "arm", "side", "notional", "units", "enter_day", "enter_at", "exit_day", "exit_at", "status",
             "entry_ref", "exit_ref", "entered_at", "exited_at", "ret_ref", "event", "why", "exit_why", "void_why")
TMP = os.path.join(ROOT, ".parity_tmp")


def source_recorded(P, series, fold, doc):
    """run_fold (as source() runs it) with trade_pair wrapped to record its inputs: the top-20 distance calls are the
    ones given trading dates, in top-20 order. -> (run_fold's result, [(na, nb, mu, sigma, tdates)])"""
    calls, real = [], P.trade_pair

    def rec(na, nb, mu, sigma, tdates=None, emit=False):
        if tdates is not None:
            calls.append((np.array(na, dtype=float), np.array(nb, dtype=float), mu, sigma, [str(d) for d in tdates]))
        return real(na, nb, mu, sigma, tdates=tdates, emit=emit)

    P.trade_pair = rec
    try:
        return source(P, series, fold, doc), calls
    finally:
        P.trade_pair = real


def trade_pair_v1(na, nb, mu, sigma, clean):
    """the vendored trade_pair's loop with IMPROVEMENTS.md section C's rule changes (V1): entry |z| > 2.5 only when
    clean[t]; exit |z| < 0.5, or 10 trading days after entry (the time stop replaces the 4-sigma stop); force close at
    the window end; pairs may reopen. -> (round trips [(t_entry, t_exit, direction, outcome)], z, state after day t)"""
    if not (np.isfinite(sigma) and sigma > 0) or not (np.all(np.isfinite(na)) and np.all(np.isfinite(nb))):
        return [], None, None
    z = (na - nb - mu) / sigma
    state, t_entry, log, after = 0, None, [], []
    for t in range(len(z) - 1):
        if state == 0:
            if z[t] > 2.5 and clean[t]:
                state, t_entry = -1, t
            elif z[t] < -2.5 and clean[t]:
                state, t_entry = 1, t
        elif abs(z[t]) < 0.5:
            log.append((t_entry, t, state, "converge"))
            state = 0
        elif t - t_entry >= 10:
            log.append((t_entry, t, state, "time_stop"))
            state = 0
        after.append(state)
    if state != 0:
        log.append((t_entry, len(z) - 1, state, "force_close"))
    return log, z, after


def gen_news(rnd, legs, ts, te):
    """per leg: news items (whole epoch seconds, any day and hour), earnings and ex-dividend dates (sessions)."""
    ev = {"news": [], "earnings": {}, "exdiv": {}}
    rate = {s: rnd.choice([0.0, 0.01, 0.02, 0.035]) for s in legs}
    d, end = date.fromisoformat(ts) - timedelta(days=14), date.fromisoformat(te)
    while d <= end:
        base = datetime.combine(d, dtime(0), ET).timestamp()
        for s in legs:
            if rnd.random() < rate[s] * (0.4 if d.weekday() >= 5 else 1.0):
                ev["news"].append((s, base + rnd.randint(0, 86399)))
            if cal.is_trading_day(d):
                if rnd.random() < 0.012:
                    ev["earnings"].setdefault(d.isoformat(), set()).add(s)
                if rnd.random() < 0.006:
                    ev["exdiv"].setdefault(d.isoformat(), set()).add(s)
        d += timedelta(days=1)
    return ev


def contaminated(ev, legs, d, end, literal):
    """firm-specific news on either leg in the window of the decision on session d. Pre-registered (literal): the prior
    5 trading days - items from 00:00 ET of session d-5 up to 00:00 ET of d, calendar events dated d-5 .. d-1. The
    producer's window (named divergence): items up to the job's last run on d (`end`), calendar events through d."""
    lo_day = cal.prev_trading_day(d, 5).isoformat()
    lo = datetime.combine(date.fromisoformat(lo_day), dtime(0), ET).timestamp()
    hi = datetime.combine(date.fromisoformat(d), dtime(0), ET).timestamp()
    for s, t in ev["news"]:
        if s in legs and lo <= t and (t < hi if literal else t <= end):
            return True
    x = date.fromisoformat(lo_day)
    while x.isoformat() < d or (not literal and x.isoformat() == d):
        for kind in ("earnings", "exdiv"):
            if ev[kind].get(x.isoformat(), set()) & legs:
                return True
        x += timedelta(days=1)
    return False


class _Alpaca:
    """the /v1beta1/news endpoint over the case's items: the symbols filter, [start, end] inclusive, one page."""

    def __init__(self, items):
        self.c, self.items = self, items

    def _get(self, path, params=None, host=None):
        if path != "/v1beta1/news":
            raise RuntimeError("unexpected Alpaca call " + path)
        syms = set(params["symbols"].split(","))
        lo, hi = (datetime.strptime(params[k], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
                  for k in ("start", "end"))
        return {"news": [{"id": i, "headline": f"{s} item {i}", "symbols": [s],
                          "created_at": datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
                         for i, (s, t) in enumerate(self.items) if s in syms and lo <= t <= hi],
                "next_page_token": None}


def rss_fetch(items, clock):
    """Yahoo Finance RSS headlines up to the job's clock; anything else fetched is an error (the calendars are cached)."""
    def fetch(url, params=None, as_text=False, headers=None, **kw):
        if not url.startswith("https://feeds.finance.yahoo.com/rss/2.0/headline"):
            raise RuntimeError("unexpected fetch " + url)
        s, now = params["s"], clock()
        return "<rss><channel>" + "".join(
            f"<item><title>{s} item {i}</title><pubDate>{format_datetime(datetime.fromtimestamp(t, tz=timezone.utc))}"
            f"</pubDate></item>" for i, (sym, t) in enumerate(items) if sym == s and t <= now) + "</channel></rss>"
    return fetch


_RUNS = {}


def job_runs(d, until):
    """the family job's run times on session d up to `until`: due when its window is open and its cadence has passed
    (desk/jobs.due) on a one-minute loop (the windows are hours apart: each session starts afresh)."""
    sched, cadence = FAM.JOBS["killed_pairs_news"][:2]
    key = (d, until, sched, cadence)
    if key not in _RUNS:
        t, last, out = datetime.combine(date.fromisoformat(d), dtime(0), ET).timestamp(), -1e18, []
        while t <= until:
            if t - last >= cadence and schedule.is_open(sched, t):
                out.append(t)
                last = t
            t += 60
        _RUNS[key] = out
    return _RUNS[key]


def norm_v1(i):
    o = i.order
    return [i.kind, i.symbol, i.side, i.qty, i.price_hint, o.type if o else None, o.tif if o else None,
            o.window_s if o else None, i.signal_key, i.reason, i.meta]


def v1_sleeve(series, fold, doc, days, ev, root, rss):
    """PairsNewsFiltered stepped twice a session; the gate's doc from the family job on its schedule, read back through
    the family feed. -> (tranches by id, [(session, pass time, the ledger's view, intents)], job runs by session)"""
    fs, fe, ts, te = fold
    tdays = [d for d in days if ts <= d <= te]
    legs = sorted({p["a"] for p in doc["pairs"]} | {p["b"] for p in doc["pairs"]})
    cdir = os.path.join(root, "cache", "killed")
    for sub in ("pairs", "nasdaq_earnings", "nasdaq_dividends"):
        os.makedirs(os.path.join(cdir, sub), exist_ok=True)
    write_json_atomic(os.path.join(cdir, "pairs", f"{ts}.json"), doc)     # the formation, as pairs_form_job writes it
    d = date.fromisoformat(ts) - timedelta(days=14)
    while d <= date.fromisoformat(te):                 # the Nasdaq calendars, as calendar_rows caches them
        if d.weekday() < 5:
            for kind, k in (("earnings", "earnings"), ("dividends", "exdiv")):
                with open(os.path.join(cdir, f"nasdaq_{kind}", f"{d.isoformat()}.json"), "w") as f:
                    json.dump({"day": d.isoformat(), "fetched_at": 0.0,
                               "rows": [{"symbol": s} for s in sorted(ev[k].get(d.isoformat(), ()))]}, f)
        d += timedelta(days=1)
    eng = SimpleNamespace(root=root, t=0.0, hub=SimpleNamespace(alpaca=None if rss else _Alpaca(ev["news"])))
    eng.clock = lambda: eng.t
    feeds = SimpleNamespace(hub=SimpleNamespace(cache=SimpleNamespace(root=os.path.join(root, "cache", "bars"))))
    by = {s: {r[0]: r for r in series[s]} for s in legs}
    full = {s: [{"t": datetime.fromisoformat(r[0]).replace(hour=9, minute=30, tzinfo=ET).timestamp(),
                 "o": r[1], "h": r[1], "l": r[1], "c": r[1], "v": r[3]} for r in series[s]] for s in legs}
    days_of = {s: [r[0] for r in series[s]] for s in legs}
    sl = PR.PairsNewsFiltered()
    st, seen, book, log, runs = {}, {}, {}, [], {}
    real_defaults = KD.news_gate.__defaults__
    KD.news_gate.__defaults__ = (rss_fetch(ev["news"], eng.clock),)
    try:
        for d in tdays:
            close = cal.session_close(d)
            runs[d] = list(job_runs(d, close - 25 * 60))
            pending = list(runs[d])
            for now in (close - 50 * 60, close - 25 * 60):
                while pending and pending[0] <= now:
                    eng.t = pending.pop(0)
                    KD.pairs_news_job(eng)
                news = KD.feed_pairs_news(feeds, sl, now)
                bars = {s: full[s][:bisect_left(days_of[s], d)] for s in legs}
                quotes = {s: {"last": by[s][d][1], "t": now} for s in legs}
                pos = {"EQ:" + s: {"qty": q, "avg": 0.0, "opened_at": 0.0, "meta": {}, "mark": quotes[s]["last"]}
                       for s, q in book.items() if abs(q) > 1e-9}
                v = View(now=now, session=d, bars={"1d": bars}, quotes=quotes, state=st, positions=pos,
                         extra={"killed_pairs": doc, "killed_pairs_news": news, "pending_orders": [],
                                "closed_trades": []})
                out = sl.signal(v)
                st = sl._st
                for t in st.get("tranches", []):
                    seen[t["id"]] = dict(t)
                log.append((d, now, View(now=now, session=d, quotes=quotes, positions=pos,
                                         extra={"pending_orders": [], "closed_trades": []}),
                            [norm_v1(i) for i in out]))
                for i in out:
                    if i.kind in ("enter", "exit"):
                        cur = book.get(i.symbol, 0.0)
                        if i.kind == "enter":
                            cur += i.qty if i.side == "long" else -i.qty
                        else:
                            cur = cur - i.qty if cur > 0 else cur + i.qty
                        book[i.symbol] = cur
    finally:
        KD.news_gate.__defaults__ = real_defaults
    return seen, log, runs


def v1_source(src, calls, doc, ev, runs, tdays):
    """the restated V1 rule over run_fold's own top-20 series. -> ({pass: [expected tranche events]}, per-pass obs,
    round trips (producer window), round trips (pre-registered window), entries the gate blocked)"""
    last_day = tdays[-1]
    out, blocked = {"named": [], "literal": []}, 0
    zs = {}
    for (a, b), (na, nb, mu, sigma, td) in zip(src["top20_pairs"], calls):
        for variant in ("named", "literal"):
            clean = [not contaminated(ev, {a, b}, d, (runs.get(d) or [cal.session_close(d) - 25 * 60])[-1],
                                      variant == "literal") for d in td]
            log, z, after = trade_pair_v1(na, nb, mu, sigma, clean)
            if variant == "named":
                zs[(a, b)] = (z, after, td)
                if z is not None:
                    st = 0
                    for t in range(len(z) - 1):
                        if st == 0 and abs(z[t]) > 2.5 and not clean[t]:
                            blocked += 1
                        st = after[t]
            for te_, tx, dirc, outcome in log:
                out[variant].append({"pair": f"{a}/{b}", "a": a, "b": b, "direction": dirc, "entry": td[te_],
                                     "exit": td[tx], "outcome": outcome,
                                     "z_entry": float(z[te_]), "z_exit": float(z[tx])})
    return out, zs, blocked


def v1_expected(trips, zs, doc, tdays, log, by):
    """the sleeve's records and per-pass intents implied by the source's round trips: each trip opens both legs at the
    market-on-close of its entry session and closes them at the market-on-close of its exit session."""
    n = PR.PAIR_CAPITAL / 2
    moc = {d: now for d, now, v, mine in log if now == cal.session_close(d) - 25 * 60}
    order = {f"{p['a']}/{p['b']}": k for k, p in enumerate(doc["pairs"])}
    trs = []
    for tr in trips:
        key, d0 = tr["pair"], tr["entry"]
        for leg, sym, side in (("a", tr["a"], tr["direction"]), ("b", tr["b"], -tr["direction"])):
            arm = f"pair:{key}"
            px = by[sym][d0][1]
            u = n / px
            units = float(max(1, int(np.floor(u)))) if side < 0 else round(u, 4)
            why = ("window end (force close)" if tr["outcome"] == "force_close"
                   else f"{tr['outcome']} at z {tr['z_exit']:+.3f}")
            xp = by[sym][tr["exit"]][1]
            trs.append({"id": K.stable_id(SID_V1, arm, sym, d0, "close", f"{d0}:{leg}"), "sym": sym, "arm": arm,
                        "side": side, "notional": n, "units": units, "enter_day": d0, "enter_at": "close",
                        "exit_day": tr["exit"], "exit_at": "close", "status": "closed", "entry_ref": px,
                        "exit_ref": xp, "entered_at": moc.get(d0), "exited_at": moc.get(tr["exit"]),
                        "ret_ref": round(side * (xp / px - 1.0), 6), "event": f"{d0}:{leg}",
                        "why": f"z {tr['z_entry']:+.3f}", "exit_why": why,
                        "_key": (d0, order[key], leg), "_exit": tr["exit"]})
    trs.sort(key=lambda r: r["_key"])

    def at(d):
        """records after the market-on-close pass of d, and that pass's ledger changes"""
        recs, changes = [], []
        for r in trs:
            if r["enter_day"] > d:
                continue
            x = {k: v for k, v in r.items() if not k.startswith("_")}
            if r["enter_day"] == d:
                changes.append((r["sym"], r["side"] * r["units"], "cls", r["id"]))
            if r["_exit"] == d:
                changes.append((r["sym"], -r["side"] * r["units"], "cls", r["id"]))
            if r["_exit"] > d:
                x.update(status="held", exit_day=None, exit_at=None, exit_ref=None, exited_at=None)
                x.pop("ret_ref")
                x.pop("exit_why")
            recs.append(x)
        return recs, changes

    obs = {}
    for d in tdays[:-1]:
        rows = []
        for p in doc["pairs"]:
            key = f"{p['a']}/{p['b']}"
            z, after, td = zs[(p["a"], p["b"])]
            t = td.index(d)
            rows.append(["signal", p["a"], "long", None, None, None, None, None, f"pz:{d}:{key}",
                         f"{key} z {z[t]:+.3f} state {after[t]}", {"z": round(float(z[t]), 6)}])
        obs[d] = rows
    return trs, at, obs


def v1_case(seed, case, fold, days, series, doc, src, calls):
    rnd = random.Random(f"{seed}:v1:{case}")
    fs, fe, ts, te = fold
    tdays = [d for d in days if ts <= d <= te]
    legs = sorted({p["a"] for p in doc["pairs"]} | {p["b"] for p in doc["pairs"]})
    ev = gen_news(rnd, legs, ts, te)
    rss = rnd.random() < 0.25
    root = os.path.join(TMP, f"killed_pairs_{os.getpid()}_{case}")
    shutil.rmtree(root, ignore_errors=True)
    try:
        seen, log, runs = v1_sleeve(series, fold, doc, days, ev, root, rss)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    trips, zs, blocked = v1_source(src, calls, doc, ev, runs, tdays)
    by = {s: {r[0]: r for r in series[s]} for s in legs}
    trs, at, obs = v1_expected(trips["named"], zs, doc, tdays, log, by)
    bad = []
    for d, now, v, mine in log:
        want = []
        if now == cal.session_close(d) - 25 * 60:
            recs, changes = at(d)
            tb = K.TrancheBook({"tranches": recs}, v, SID_V1, whole_short=True)
            tb.changes = changes
            want = obs.get(d, []) + [norm_v1(i) for i in tb.intents()]
        if mine != want and len(bad) < 4:
            bad.append({"day": d, "at": K.et_hm(now), "sleeve": mine[:3], "source": want[:3]})
    mine = {tid: [t.get(f) for f in V1_FIELDS] for tid, t in seen.items()}
    want = {r["id"]: [r.get(f) for f in V1_FIELDS] for r in at(tdays[-1])[0]}
    bad_tr = [{"sleeve": mine.get(t), "source": want.get(t)} for t in sorted(set(mine) | set(want))
              if mine.get(t) != want.get(t)]
    key = lambda t: (t["pair"], t["entry"], t["exit"], t["direction"], t["outcome"])
    named, lit = {key(t) for t in trips["named"]}, {key(t) for t in trips["literal"]}
    stats = {"round_trips": len(trips["named"]), "legs": len(trs),
             "converge": sum(t["outcome"] == "converge" for t in trips["named"]),
             "time_stop": sum(t["outcome"] == "time_stop" for t in trips["named"]),
             "force_close": sum(t["outcome"] == "force_close" for t in trips["named"]),
             "entries_blocked_by_news": blocked, "sessions_without_gate_doc": sum(1 for d in tdays if not runs[d]),
             "rss_cases": int(rss), "literal_round_trips": len(lit), "literal_only": len(lit - named),
             "producer_window_only": len(named - lit)}
    return {"bad_intents": bad, "bad_tranches": bad_tr[:4], "n_bad_tranches": len(bad_tr), "stats": stats}


def one_case(job):
    seed, case, fold, days, series, doc, with_v1 = job
    from desk.vendor.midna_research import pairs_backtest_dev as P
    bad, stats = [], {}
    src, calls = source_recorded(P, series, fold, doc)
    stats["formed"] = doc["n_formed"]
    if src["n_formed"] != doc["n_formed"]:
        bad.append(f"n_formed {src['n_formed']} vs {doc['n_formed']}")
    mine_top = [[p["a"], p["b"]] for p in doc["pairs"]]
    if src["top20_pairs"] != mine_top:
        bad.append("top20")
    if src["eg20_pairs"] != doc["eg20"]:
        bad.append("eg20")
    v1 = None
    if not bad:
        st = [{"pair": f"{t['leg_a']}/{t['leg_b']}", "direction": t["direction"], "entry_date": t["entry_date"],
               "exit_date": t["exit_date"], "outcome": t["outcome"]} for t in src["trade_log"]]
        mt = sleeve_trades(series, fold, doc, days)
        key = lambda t: (t["pair"], t["entry_date"])
        if sorted(st, key=key) != sorted(mt, key=key):
            only_s = [t for t in st if t not in mt]
            only_m = [t for t in mt if t not in st]
            bad.append({"only_source": only_s[:4], "only_sleeve": only_m[:4]})
        stats["round_trips"] = len(st)
        stats["adverse_stops"] = sum(t["outcome"] == "adverse_stop" for t in st)
        stats["force_closes"] = sum(t["outcome"] == "force_close" for t in st)
        if with_v1:
            v1 = v1_case(seed, case, fold, days, series, doc, src, calls)
    return {"case": case, "bad": bad, "stats": stats, "v1": v1, "v1_run": bool(with_v1 and not bad)}


def cases(n, n_v1, seed):
    """the distance cases, drawn in order from one stream (the corpus of the earlier receipt), V1 on the first n_v1."""
    rnd = random.Random(seed)
    for case in range(n):
        fold = FOLDS[case % len(FOLDS)]
        days, series = gen_case(rnd, fold)
        doc = KD.form_pairs(series, fold[0], fold[1])
        while doc is None or doc["n_formed"] < 40:      # run_fold's random-pair control draws 40 formed names
            days, series = gen_case(rnd, fold)
            doc = KD.form_pairs(series, fold[0], fold[1])
        doc["trading"] = [fold[2], fold[3]]              # pairs_form_job stamps the window it formed for
        yield (seed, case, fold, days, series, doc, case < n_v1)


def run(n=N_CASES, n_v1=N_V1, seed=20261016):
    workers = int(os.environ.get("PARITY_JOBS") or 1)
    results, batch = [], []
    pool = None
    if workers > 1:
        from concurrent.futures import ProcessPoolExecutor
        pool = ProcessPoolExecutor(workers)
    try:
        for job in cases(n, n_v1, seed):
            batch.append(job)
            if len(batch) == max(1, 4 * workers) or job[1] == n - 1:
                results += list(pool.map(one_case, batch)) if pool else [one_case(j) for j in batch]
                batch = []
                if len(results) % 50 < max(1, 4 * workers):
                    print(f"case {len(results)}/{n} diffs={sum(1 for r in results if r['bad'])} "
                          f"v1_diffs={sum(1 for r in results if r['v1'] and (r['v1']['bad_intents'] or r['v1']['n_bad_tranches']))}",
                          file=sys.stderr, flush=True)
    finally:
        if pool:
            pool.shutdown()
        if os.path.isdir(TMP) and not os.listdir(TMP):
            os.rmdir(TMP)
    stats = {"formed": 0, "round_trips": 0, "adverse_stops": 0, "force_closes": 0, "cases_formed": 0}
    v1s = {}
    diffs, v1_diffs = [], []
    for r in results:
        stats["cases_formed"] += 1
        for k, v in r["stats"].items():
            stats[k] += v
        if r["bad"]:
            diffs.append({"case": r["case"], "bad": r["bad"]})
        if r["v1"]:
            for k, v in r["v1"]["stats"].items():
                v1s[k] = v1s.get(k, 0) + v
            if r["v1"]["bad_intents"] or r["v1"]["n_bad_tranches"]:
                v1_diffs.append({"case": r["case"], "intents": r["v1"]["bad_intents"],
                                 "tranches": r["v1"]["bad_tranches"], "n_bad_tranches": r["v1"]["n_bad_tranches"]})
    n_v1_run = sum(1 for r in results if r["v1_run"])
    bad_cases = {d["case"] for d in diffs} | {d["case"] for d in v1_diffs}
    res = {"cases": n, "identical": n - len(bad_cases), "diffs": diffs[:6], "n_diffs": len(bad_cases), "stats": stats,
           "v1": {"cases": n_v1_run, "identical": n_v1_run - len(v1_diffs), "n_diffs": len(v1_diffs),
                  "diffs": v1_diffs[:6], "stats": v1s,
                  "source": {"repo": "midna@7969b5229c46403a92290d16da23228e59e7b064",
                             "spec": "workspace/alpaca-swing-desk/desk/research/pair-trading/IMPROVEMENTS.md section C "
                                     "(blob da13866bcbfcaf3d99f89ef5049864cf97009903)",
                             "death": "pair-trading/v1_feasibility_death_2026-10-02.md (blob "
                                      "31334e3522772c234fecb4d8ccffb3e5d44e4dcb)",
                             "inventory": "resurrection/KILL_INVENTORY.md section B2 (blob "
                                          "a799c4f1e069d6e45d908d8a456a3b7c345dbd5a)",
                             "base": "desk/vendor/midna_research/pairs_backtest_dev.py (05_backtest_dev.py, blob "
                                     "b308b58eda6864f07cdc79242fb3d36feb4b51a0): run_fold and trade_pair's loop"}},
           "sleeves": ["killed_pairs_distance_coint", "killed_pairs_news_filtered"],
           "method": "vendored 05_backtest_dev.run_fold (emit_trades) on the 03/04-filtered synthetic universe vs "
                     "killed_data.form_pairs + the PairsDistance sleeve stepped through the trading window on Views "
                     "(live price = the session close); formed count, top-20 SSD, EG top-20 and every round trip "
                     "(entry, exit, direction, outcome) exact. V1 (no runner exists: it died at feasibility): "
                     "run_fold's own top-20 series through the vendored trade_pair loop with the pre-registered "
                     "changes restated (|z| > 2.5 news-clean entry, |z| < 0.5 or 10-session time stop, window-end "
                     "force close) vs the PairsNewsFiltered sleeve stepped twice a session on Views, its news gate "
                     "the family's killed_pairs_news job on its schedule over stubbed news sources; every tranche "
                     "field and every pass's intents exact"}
    write_receipt("killed_pairs", res)
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    r = run(int(a[0]) if a else N_CASES, int(a[1]) if len(a) > 1 else N_V1)
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
    print(json.dumps({k: r["v1"][k] for k in ("cases", "identical", "n_diffs", "stats")}))
