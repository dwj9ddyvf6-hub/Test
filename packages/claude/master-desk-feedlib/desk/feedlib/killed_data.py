"""Producers for the killed-study sleeves (desk/sleeves/killed): the free public inputs each study read from paid or
local research files, rebuilt forward and cached under cache/killed/.

  listings     NASDAQ Trader symbol directories (nasdaqlisted.txt + otherlisted.txt) - the free stand-in for the
               Alpaca /v2/assets list the pairs and PEAD universes were cut from (named divergence)
  calendars    Nasdaq's public earnings and dividend calendars by date (api.nasdaq.com/api/calendar/...) - the PEAD
               studies' own event source (pead/code/01_nasdaq_backfill.py)
  pead         S = (P[t+1]/P[t-1]-1) - (SPY[t+1]/SPY[t-1]-1) on adjusted daily closes for every calendar event, and
               the cohort cut: the 80th percentile of the previous calendar quarter's S (the study cut each quarter's
               own quintiles after the fact; forward, the last complete quarter's cut is the PIT stand-in)
  spillover    the day's earnings events with c_{t-1} and the live price late in the session
  pairs        the 12-month formation of the half-year trading window: liquidity filters, bad-tick cleaning, the
               SSD top-20 (Gram trick) and the Engle-Granger ADF(1) top-20 on the top-200 (record only)
  pairs news   firm-specific news per pair leg over the prior 5 trading days: Alpaca news (/v1beta1/news, the source
               the T3-18 probe found) when keyed, else Yahoo Finance RSS headlines; earnings and ex-dividend dates
               from the Nasdaq calendars
  smcap        the M2 qualifier week's BEAT / SMALL / HIBETA features (the study's per-qualifier block, verbatim)"""
import json
import math
import os
import re
import statistics
from datetime import date, datetime, timedelta, timezone

from .. import calendar as cal
from ..data.http import get
from ..util import ET, read_json, write_json_atomic
from .earnings import HEADERS                   # the desk's Nasdaq request headers (its own User-Agent)

NT = "https://www.nasdaqtrader.com/dynamic/SymDir/"
NASDAQ_CAL = "https://api.nasdaq.com/api/calendar/"
OTHER_EXCH = {"N": "NYSE", "A": "AMEX", "P": "ARCA", "Z": "BATS", "V": "IEX"}


def cdir_engine(engine):
    d = os.path.join(engine.root, "cache", "killed")
    os.makedirs(d, exist_ok=True)
    return d


def cdir_feeds(feeds):
    root = os.path.dirname(feeds.hub.cache.root) if feeds is not None and feeds.hub is not None else "cache"
    return os.path.join(root, "killed")


def et_today(now):
    return datetime.fromtimestamp(now, tz=ET).date().isoformat()


def _adj(b):
    """the total-return adjusted close (Yahoo 'ac'; Alpaca adjustment=all bars carry it in 'c')."""
    v = b.get("ac")
    return float(v) if v is not None else float(b["c"])


def _day(b):
    return datetime.fromtimestamp(float(b["t"]) + 4 * 3600, tz=timezone.utc).date().isoformat()


# -- listings ------------------------------------------------------------------------------------------------------
def parse_listings(nasdaq_txt, other_txt):
    out = {}
    for ln in (nasdaq_txt or "").splitlines()[1:]:
        p = ln.split("|")
        if len(p) < 8 or ln.startswith("File Creation Time"):
            continue
        if p[3] == "Y":
            continue
        out[p[0].strip()] = {"exchange": "NASDAQ", "etf": p[6] == "Y"}
    for ln in (other_txt or "").splitlines()[1:]:
        p = ln.split("|")
        if len(p) < 8 or ln.startswith("File Creation Time"):
            continue
        if p[6] == "Y":
            continue
        out[p[0].strip()] = {"exchange": OTHER_EXCH.get(p[2], p[2]), "etf": p[4] == "Y"}
    return {s: v for s, v in out.items() if s and "$" not in s and " " not in s}


def listings(cdir, now, fetch=get, max_age=7 * 86400):
    path = os.path.join(cdir, "listings.json")
    doc = read_json(path, None)
    if doc and now - float(doc.get("at") or 0) < max_age and doc.get("symbols"):
        return doc
    a = fetch(NT + "nasdaqlisted.txt", as_text=True)
    b = fetch(NT + "otherlisted.txt", as_text=True)
    syms = parse_listings(a, b)
    if len(syms) < 3000:
        if doc:
            return doc
        raise RuntimeError(f"symbol directory too short ({len(syms)})")
    doc = {"at": now, "source": NT, "symbols": syms}
    os.makedirs(cdir, exist_ok=True)
    write_json_atomic(path, doc)
    return doc


# -- Nasdaq calendars -------------------------------------------------------------------------------------------
def calendar_rows(cdir, kind, day, now, fetch=get):
    """rows of Nasdaq's earnings / dividends calendar for `day` (cached once the day is in the past)."""
    path = os.path.join(cdir, f"nasdaq_{kind}", f"{day}.json")
    doc = read_json(path, None)
    if doc is not None:
        return doc["rows"]
    r = fetch(NASDAQ_CAL + kind, {"date": day}, headers=HEADERS)
    data = (r or {}).get("data") or {}
    if kind == "dividends":
        rows = ((data.get("calendar") or {}).get("rows")) or []
    else:
        rows = data.get("rows") or []
    if day < et_today(now):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_json_atomic(path, {"day": day, "fetched_at": now, "rows": rows})
    return rows


def earnings_symbols(rows):
    return sorted({(r.get("symbol") or "").strip().upper() for r in rows if (r.get("symbol") or "").strip()})


# -- PEAD price surprise ----------------------------------------------------------------------------------------------
def surprise(bars, spy, t):
    """the study's S for event date t (04_backtest.py: t must be a bar; t-1 and t+1 the adjacent bars, aligned with
    SPY's bars on those dates), or None."""
    days = [_day(b) for b in bars]
    if t not in days:
        return None
    i = days.index(t)
    if i == 0 or i + 1 >= len(days):
        return None
    sd = {_day(b): b for b in spy}
    a, z = days[i - 1], days[i + 1]
    if a not in sd or z not in sd:
        return None
    s_ret = _adj(bars[i + 1]) / _adj(bars[i - 1]) - 1.0
    m_ret = _adj(sd[z]) / _adj(sd[a]) - 1.0
    return s_ret - m_ret


def quarter_of(day):
    d = date.fromisoformat(day)
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def quarter_days(q):
    y, n = int(q[:4]), int(q[5])
    a = date(y, 3 * (n - 1) + 1, 1)
    b = date(y + (n == 4), (3 * n) % 12 + 1, 1) - timedelta(days=1)
    return a.isoformat(), b.isoformat()


def prev_quarter(q):
    y, n = int(q[:4]), int(q[5])
    return f"{y - 1}Q4" if n == 1 else f"{y}Q{n - 1}"


def q80(values):
    """the top-quintile cut of pd.qcut(x, 5): the linear 80th percentile; cohort = S > cut."""
    v = sorted(values)
    if len(v) < 5:
        return None
    pos = 0.8 * (len(v) - 1)
    lo = int(math.floor(pos))
    return v[lo] + (v[min(lo + 1, len(v) - 1)] - v[lo]) * (pos - lo)


def pead_dates_due(cdir, today, now):
    """event dates whose t+1 close is final and whose surprise file is missing: the previous quarter (the cut's
    population) and the current quarter to date."""
    q = quarter_of(today)
    a, _ = quarter_days(prev_quarter(q))
    out, d = [], date.fromisoformat(a)
    last = cal.prev_trading_day(today) if now < cal.session_close(today) + 900 or not cal.is_trading_day(today) \
        else date.fromisoformat(today)
    while d <= last:
        ds = d.isoformat()
        if cal.is_trading_day(d) and cal.next_trading_day(d) <= last and \
                not os.path.exists(os.path.join(cdir, "pead", f"{ds}.json")):
            out.append(ds)
        d += timedelta(days=1)
    return out


def pead_job(engine, max_dates=15):
    now = engine.clock()
    cdir = cdir_engine(engine)
    today = et_today(now)
    lst = listings(cdir, now)["symbols"]
    done = []
    for t in pead_dates_due(cdir, today, now)[:max_dates]:
        rows = calendar_rows(cdir, "earnings", t, now)
        syms = [s for s in earnings_symbols(rows) if s in lst]
        n = cal.trading_days_between(t, today) + 6
        spy = engine.hub.bars("equity", "1d", ["SPY"], n).get("SPY") or []
        ev, skipped = {}, 0
        for i in range(0, len(syms), 100):
            got = engine.hub.bars("equity", "1d", syms[i:i + 100], n)
            for s in syms[i:i + 100]:
                v = surprise(got.get(s) or [], spy, t)
                if v is None or not math.isfinite(v):
                    skipped += 1
                else:
                    ev[s] = round(v, 10)
        os.makedirs(os.path.join(cdir, "pead"), exist_ok=True)
        write_json_atomic(os.path.join(cdir, "pead", f"{t}.json"),
                          {"t": t, "quarter": quarter_of(t), "events": ev, "skipped": skipped, "n_rows": len(rows),
                           "computed_at": now})
        done.append(t)
    th = pead_threshold(cdir, today, write=True)
    return {"dates": done, "threshold": th}


def pead_threshold(cdir, today, write=False):
    """the cohort cut for events of today's quarter: q80 of the previous calendar quarter's S (complete only when
    every session of that quarter has its surprise file)."""
    q = quarter_of(today)
    pq = prev_quarter(q)
    a, b = quarter_days(pq)
    vals, missing, d = [], 0, date.fromisoformat(a)
    while d <= date.fromisoformat(b):
        if cal.is_trading_day(d):
            doc = read_json(os.path.join(cdir, "pead", f"{d.isoformat()}.json"), None)
            if doc is None:
                missing += 1
            else:
                vals += list(doc["events"].values())
        d += timedelta(days=1)
    th = {"quarter": q, "from_quarter": pq, "cut": q80(vals) if not missing else None, "n": len(vals),
          "missing_sessions": missing}
    if write:
        write_json_atomic(os.path.join(cdir, "pead", f"threshold_{q}.json"), th)
    return th


def feed_pead(feeds, sleeve, now, arg=None):
    """{"t": event date, "cut": ..., "cohort": {sym: S}} for the session that enters event t's cohort (t+2)."""
    cdir = cdir_feeds(feeds)
    today = et_today(now)
    if not cal.is_trading_day(today):
        return None
    t = cal.prev_trading_day(today, 2).isoformat()
    doc = read_json(os.path.join(cdir, "pead", f"{t}.json"), None)
    th = read_json(os.path.join(cdir, "pead", f"threshold_{quarter_of(t)}.json"), None)
    if doc is None or th is None or th.get("cut") is None:
        return {"t": t, "ready": False, "have_events": doc is not None, "threshold": th}
    cut = th["cut"]
    return {"t": t, "ready": True, "cut": cut, "from_quarter": th["from_quarter"],
            "cohort": {s: v for s, v in doc["events"].items() if v > cut}, "n_events": len(doc["events"])}


# -- PEAD V1 spillover -----------------------------------------------------------------------------------------------
def spillover_job(engine):
    """today's calendar events with c_{t-1} (the previous session's close) and the live price late in the session."""
    now = engine.clock()
    cdir = cdir_engine(engine)
    today = et_today(now)
    if not cal.is_trading_day(today):
        return {"skip": "no session"}
    lst = listings(cdir, now)["symbols"]
    rows = calendar_rows(cdir, "earnings", today, now)
    syms = [s for s in earnings_symbols(rows) if s in lst]
    prev = cal.prev_trading_day(today).isoformat()
    ev = {}
    for i in range(0, len(syms), 100):
        got = engine.hub.bars("equity", "1d", syms[i:i + 100], 5)
        for s in syms[i:i + 100]:
            bl = [b for b in got.get(s) or [] if _day(b) == prev]
            if bl and float(bl[-1]["c"]) > 0:
                ev[s] = {"prev_close": float(bl[-1]["c"])}
    src = engine.hub.equity_source()
    qs = engine.hub.quotes(src, sorted(ev)) if ev else {}
    for s, q in qs.items():
        if s in ev and q and q.get("last"):
            ev[s].update(last=float(q["last"]), last_t=q.get("t") or now)
    os.makedirs(os.path.join(cdir, "spillover"), exist_ok=True)
    write_json_atomic(os.path.join(cdir, "spillover", f"{today}.json"),
                      {"t": today, "computed_at": now, "events": ev, "n_rows": len(rows)})
    return {"events": len(ev), "priced": sum(1 for v in ev.values() if "last" in v)}


def feed_spillover(feeds, sleeve, now, arg=None):
    return read_json(os.path.join(cdir_feeds(feeds), "spillover", f"{et_today(now)}.json"), None)


# -- pairs formation -------------------------------------------------------------------------------------------------
def window_of(day):
    """(formation start, formation end, trading start, trading end) of the half-year window containing `day`."""
    d = date.fromisoformat(day)
    if d.month <= 6:
        return (f"{d.year - 1}-01-01", f"{d.year - 1}-12-31", f"{d.year}-01-01", f"{d.year}-06-30")
    return (f"{d.year - 1}-07-01", f"{d.year}-06-30", f"{d.year}-07-01", f"{d.year}-12-31")


def clean_bad_ticks(adj, vol, med_vol):
    """04_clean_adj.py: a bar is missing when |adjusted return| > 50% AND volume < 1% of the formation median."""
    out = list(adj)
    for i in range(1, len(adj)):
        a0, a1 = adj[i - 1], adj[i]
        if a0 is None or a1 is None or a0 == 0:
            continue
        if abs(a1 / a0 - 1.0) > 0.50 and vol[i] is not None and vol[i] < 0.01 * med_vol:
            out[i] = None
    return out


def form_pairs(series, fs, fe, n_pairs=20):
    """series: {sym: [(day, adj_close, raw_close_x_volume_ok, volume)]} -> the formation (03 filters + 04 cleaning
    + 05 run_fold's selection). Returns the doc minus the trading-window state."""
    import numpy as np
    from ..vendor.midna_research import pairs_backtest_dev as P
    days = sorted({d for rows in series.values() for d, *_ in rows if fs <= d <= fe})
    expected = len(days)
    need = expected * 240.0 / 252.0
    stage = {}
    for s, rows in series.items():
        w = [r for r in rows if fs <= r[0] <= fe]
        if len({r[0] for r in w}) < need:
            continue
        dvol = statistics.median([r[2] for r in w])
        if dvol < 1_000_000:
            continue
        stage[s] = w
    names = sorted(stage)
    idx = {d: i for i, d in enumerate(days)}
    keep = []
    mat = []
    for s in names:
        w = stage[s]
        med_v = statistics.median([r[3] for r in w])
        adj = [None] * expected
        vol = [None] * expected
        for d, a, _, v in w:
            if d in idx:
                adj[idx[d]] = a
                vol[idx[d]] = v
        adj = clean_bad_ticks(adj, vol, med_v)
        present = [a for a in adj if a is not None]
        if not present or statistics.median(present) < 5.0:
            continue
        if any(a is None for a in adj):
            continue                                        # formed-on set: every expected day present
        keep.append(s)
        mat.append(adj)
    if len(keep) < 2:
        return None
    X = np.array(mat, dtype=float).T
    Xn = X / X[0]
    G = Xn.T @ Xn
    d2 = np.diag(G)
    SSD = d2[:, None] + d2[None, :] - 2.0 * G
    np.fill_diagonal(SSD, np.inf)
    iu = np.triu_indices(len(keep), k=1)
    order = np.argsort(SSD[iu], kind="stable")
    top200 = [(int(iu[0][k]), int(iu[1][k])) for k in order[:200]]
    top = [(int(iu[0][k]), int(iu[1][k])) for k in order[:n_pairs]]
    adf = sorted(((P.adf1_tstat(Xn[:, i], Xn[:, j]), i, j) for i, j in top200),
                 key=lambda r: (np.inf if np.isnan(r[0]) else r[0]))
    pairs = []
    med_v = {s: statistics.median([r[3] for r in stage[s]]) for s in keep}
    for i, j in top:
        s = Xn[:, i] - Xn[:, j]
        pairs.append({"a": keep[i], "b": keep[j], "ssd": float(SSD[i, j]), "mu": float(s.mean()), "sd": float(s.std()),
                      "base_a": float(X[0, i]), "base_b": float(X[0, j]), "med_v_a": med_v[keep[i]],
                      "med_v_b": med_v[keep[j]]})
    return {"formation": [fs, fe], "expected_days": expected, "n_universe": len(names), "n_formed": len(keep),
            "pairs": pairs, "eg20": [[keep[i], keep[j]] for _, i, j in adf[:n_pairs]], "first_day": days[0],
            "universe": names}


def pairs_form_job(engine, force=False):
    now = engine.clock()
    cdir = cdir_engine(engine)
    today = et_today(now)
    fs, fe, ts, te = window_of(today)
    path = os.path.join(cdir, "pairs", f"{ts}.json")
    if os.path.exists(path) and not force:
        return {"window": ts, "skip": "formed"}
    lst = listings(cdir, now)["symbols"]
    cands = sorted(s for s, v in lst.items() if v["exchange"] in ("NASDAQ", "NYSE", "AMEX"))
    n = cal.trading_days_between(fs, today) + 10
    series = {}
    for i in range(0, len(cands), 200):
        got = engine.hub.bars("equity", "1d", cands[i:i + 200], n)
        for s, bl in got.items():
            rows = []
            for b in bl:
                d = _day(b)
                if fs <= d <= fe and b.get("v") is not None:
                    rows.append((d, _adj(b), float(b["c"]) * float(b["v"]), float(b["v"])))
            if rows:
                series[s] = rows
    doc = form_pairs(series, fs, fe)
    if doc is None:
        return {"window": ts, "error": "nothing formed", "candidates": len(cands), "with_bars": len(series)}
    doc.update(trading=[ts, te], computed_at=now, candidates=len(cands), with_bars=len(series),
               universe_source="NASDAQ Trader symbol directories (NYSE/NASDAQ/AMEX, test issues dropped)")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_json_atomic(path, doc)
    return {"window": ts, "n_formed": doc["n_formed"], "pairs": [[p["a"], p["b"]] for p in doc["pairs"]]}


def feed_pairs(feeds, sleeve, now, arg=None):
    fs, fe, ts, te = window_of(et_today(now))
    return read_json(os.path.join(cdir_feeds(feeds), "pairs", f"{ts}.json"), None)


# -- pairs news gate ---------------------------------------------------------------------------------------------
def _alpaca_news(hub, syms, start, end):
    from ..venues.alpaca import DATA
    out, token = [], None
    for _ in range(20):
        r = hub.alpaca.c._get("/v1beta1/news", {"symbols": ",".join(syms), "start": start, "end": end, "limit": 50,
                                                "sort": "asc", "include_content": "false", "page_token": token},
                              host=DATA) or {}
        out += r.get("news") or []
        token = r.get("next_page_token")
        if not token:
            break
    return out


def _yahoo_rss(sym, fetch=get):
    txt = fetch("https://feeds.finance.yahoo.com/rss/2.0/headline", {"s": sym, "region": "US", "lang": "en-US"},
                as_text=True) or ""
    out = []
    from email.utils import parsedate_to_datetime
    for m in re.finditer(r"<item>(.*?)</item>", txt, re.S):
        it = m.group(1)
        d = re.search(r"<pubDate>(.*?)</pubDate>", it)
        h = re.search(r"<title>(.*?)</title>", it, re.S)
        if d:
            try:
                out.append({"created_at": parsedate_to_datetime(d.group(1)).astimezone(timezone.utc).isoformat(),
                            "headline": (h.group(1) if h else "")[:200], "symbols": [sym]})
            except (TypeError, ValueError):
                pass
    return out


def news_gate(engine, syms, today, now, fetch=get):
    """{sym: {"news": n, "earnings": [days], "exdiv": [days], "source": ...}} over [today - 5 sessions, today]."""
    cdir = cdir_engine(engine)
    lo = cal.prev_trading_day(today, 5).isoformat()
    days, d = [], date.fromisoformat(lo)
    while d <= date.fromisoformat(today):
        if d.weekday() < 5:
            days.append(d.isoformat())
        d += timedelta(days=1)
    out = {s: {"news": 0, "earnings": [], "exdiv": []} for s in syms}
    for day in days:
        for r in calendar_rows(cdir, "earnings", day, now, fetch):
            s = (r.get("symbol") or "").upper()
            if s in out:
                out[s]["earnings"].append(day)
        for r in calendar_rows(cdir, "dividends", day, now, fetch):
            s = (r.get("symbol") or "").upper()
            if s in out:
                out[s]["exdiv"].append(day)
    start = datetime.combine(date.fromisoformat(lo), datetime.min.time(), ET).astimezone(timezone.utc)
    src = "alpaca /v1beta1/news"
    if engine.hub is not None and getattr(engine.hub, "alpaca", None) is not None:
        items = _alpaca_news(engine.hub, sorted(syms), start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                             datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        for it in items:
            for s in it.get("symbols") or []:
                if s in out:
                    out[s]["news"] += 1
    else:
        src = "yahoo rss headlines"
        for s in syms:
            for it in _yahoo_rss(s, fetch):
                if it["created_at"] >= start.isoformat():
                    out[s]["news"] += 1
    for v in out.values():
        v["source"] = src
    return out


def pairs_news_job(engine):
    now = engine.clock()
    cdir = cdir_engine(engine)
    today = et_today(now)
    if not cal.is_trading_day(today):
        return {"skip": "no session"}
    fs, fe, ts, te = window_of(today)
    doc = read_json(os.path.join(cdir, "pairs", f"{ts}.json"), None)
    if not doc:
        return {"skip": "no formation"}
    syms = sorted({p["a"] for p in doc["pairs"]} | {p["b"] for p in doc["pairs"]})
    gate = news_gate(engine, syms, today, now)
    os.makedirs(os.path.join(cdir, "pairs_news"), exist_ok=True)
    write_json_atomic(os.path.join(cdir, "pairs_news", f"{today}.json"), {"day": today, "computed_at": now, "legs": gate})
    return {"legs": len(gate), "contaminated": sum(1 for v in gate.values() if v["news"] or v["earnings"] or v["exdiv"])}


def feed_pairs_news(feeds, sleeve, now, arg=None):
    return read_json(os.path.join(cdir_feeds(feeds), "pairs_news", f"{et_today(now)}.json"), None)


# -- 52-week smcap / beta --------------------------------------------------------------------------------------------
def merged_weekly(root, syms):
    """the qualifier's own merged weekly series (dev + 2022plus + incremental, deduped by t, sorted)."""
    from . import m2
    dev = json.load(open(m2._research(root, "weekly_bars_dev")))
    plus = json.load(open(m2._research(root, "weekly_2022plus")))
    incr = read_json(os.path.join(m2.workdir(root), "weekly_incr.json"), {}) or {}
    out = {}
    for s in syms:
        seen = {}
        for src in (dev, plus, incr):
            for b in src.get(s) or []:
                seen[b["t"]] = b
        out[s] = sorted(seen.values(), key=lambda b: b["t"])
    return out


def smcap_features(quals, bars, spy_t2c, cost=0.0051):
    """run_smcap_beta_52w.main's per-qualifier block (no forward: the forward is the trade) + the week's SMALL cut."""
    from ..vendor.midna_research import run_smcap_beta_52w as S
    feats = []
    for q in quals:
        sym, i = q["symbol"], int(q["idx"])
        s = bars.get(sym) or []
        if i >= len(s) or i < 52:
            continue
        closes = [b["c"] for b in s]
        vols = [b["v"] for b in s]
        c = closes[i]
        hi52 = max(closes[i - 51:i + 1])
        beat_lo52 = c <= 0.80 * hi52
        beat_run13 = (c / closes[i - 13] - 1) <= -0.20
        beat = beat_lo52 or beat_run13
        dvol52 = sum(closes[j] * vols[j] for j in range(i - 51, i + 1)) / 52.0
        ts = [b["t"] for b in s[i - 52:i + 1]]
        sc = [closes[i - 52 + k] for k in range(53)]
        ok = [k for k in range(1, 53)
              if sc[k] > 0 and sc[k - 1] > 0 and spy_t2c.get(ts[k]) and spy_t2c.get(ts[k - 1])]
        rx_all = [math.log(sc[k] / sc[k - 1]) for k in ok]
        ry_all = [math.log(spy_t2c[ts[k]] / spy_t2c[ts[k - 1]]) for k in ok]
        beta = S.ols_beta(ry_all, rx_all) if len(rx_all) >= 40 else None
        hibeta = beta is not None and beta > 1.2
        feats.append({"friday": q["friday"], "symbol": sym, "i": i, "beat": beat, "beat_lo52": beat_lo52,
                      "beat_run13": beat_run13, "dvol52": dvol52, "beta": beta, "hibeta": hibeta, "close": c})
    by_week = {}
    for f in feats:
        by_week.setdefault(f["friday"], []).append(f)
    for fs in by_week.values():
        dvols = sorted(f["dvol52"] for f in fs)
        cut = statistics.quantiles(dvols, n=3, method="inclusive")[0]
        for f in fs:
            f["small"] = f["dvol52"] <= cut
    for f in feats:
        f["primary"] = bool(f["beat"] and f["small"] and f["hibeta"])
    return feats


def smcap_job(engine):
    from . import m2
    now = engine.clock()
    cdir = cdir_engine(engine)
    today = et_today(now)
    doc = m2.load_file(os.path.join(m2.workdir(engine.root), "qualifiers.json"), today)
    if not doc or doc.get("wait"):
        return {"skip": "no M2 qualifier file for today", "wait": (doc or {}).get("wait")}
    quals = doc.get("qualifiers") or []
    friday = quals[0]["friday"] if quals else None
    path = os.path.join(cdir, "smcap", f"{today}.json")
    if os.path.exists(path):
        return {"skip": "done", "friday": friday}
    bars = merged_weekly(engine.root, sorted({q["symbol"] for q in quals} | {"SPY"}))
    spy_t2c = {b["t"]: b["c"] for b in bars.get("SPY") or []}
    feats = smcap_features(quals, bars, spy_t2c) if quals else []
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_json_atomic(path, {"rank_date": today, "friday": friday, "computed_at": now, "n_qualifiers": len(quals),
                             "features": feats})
    return {"qualifiers": len(quals), "primary": sum(1 for f in feats if f["primary"]),
            "beat": sum(1 for f in feats if f["beat"]), "hibeta": sum(1 for f in feats if f["hibeta"])}


def feed_smcap(feeds, sleeve, now, arg=None):
    """the latest smcap feature file written on or before today (the sleeve enters on the next session)."""
    d = os.path.join(cdir_feeds(feeds), "smcap")
    if not os.path.isdir(d):
        return None
    names = sorted(n for n in os.listdir(d) if n.endswith(".json") and n[:10] <= et_today(now))
    return read_json(os.path.join(d, names[-1]), None) if names else None
