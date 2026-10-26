"""Milkman-family rows built on Galath's Tensor lane fires — the production engine (FolioTend v698: anna-replica +
enrichment + swing rule) replayed over Yahoo payloads exactly as galath-research did (real_engine/run_engine_live.mjs,
vendored byte-exact with its lib in desk/vendor/galath_engine/), with the lanes defined as the research's event builder
defines them (winners/code/build_events_real.py: 1W Cyan / Green = a closed weekly bar with buy-cyan / buy-green,
bar index >= 60; 1D Green = a closed daily bar with buy-green, index >= 250; 1D Swing = consensus-buy with a
monitor-buy square on it or the 3 prior bars, keyed per setup bar, daily_swing/build.py).

The producer (run_weekly / run_daily, desk jobs `milkman_galath_weekly` and `milkman_galath_daily`) fetches Yahoo's
own payloads for the store_v1 survivors (as the research's fetch_wk.py: 1wk and 1d, the last 10 years), runs the
engine in parallel node processes and writes cache/galath_weekly.json and cache/galath_daily.json: the fires of the
recent weeks / sessions with their at-fire features, the weekly vote breadth since 2016 and the ratio-chart fires. The
sleeves read those files through the `galath` feed and trade from the next regular session.

Rows:
  mk_creativetensorbreadthtiming        TENSOR_CREATIVE c04_breadth.py / c04b_book.py: IWM when the share of names
                                        whose closed weekly bar has >= 5 bullish votes is at or below its train median
                                        (weeks to 2023-09-29), else cash; weekly at the Friday close, from the next open
  mk_creativetensorratiochartsignals    c03_ratio.py: the unchanged weekly engine on stock/SPY ratio bars (daily ratio
                                        OHLC of adjusted prices, H = max, L = min, the stock's volume, W-FRI weeks);
                                        a ratio Cyan / Green fire buys the STOCK at the next open, held 252 sessions
  mk_creativetensoroptionexpressionproxy  c01_options.py: tier-A 1W Cyan / Green fires expressed with calls — the
                                        study's default expression (strike = spot, expiry = the 52-week hold, all of the
                                        trade's capital in calls, premium >= 2% of spot), sold after 52 weeks
  mk_bigwinnersmanysmallpositionssleeve bigwinners s1_sleeve.py, config W52S-CAL (proposal_weekly_sleeve.md): every
                                        1W fire of the CAL_NAV stream (liquid, not avoided, calib-matched), $1,000
                                        whole shares at the next open, one per name, desk-score order, W52 close
                                        exit, $50,000 cap on open basis less realised losses (sweep)
  mk_bigwinnerspacedtokenbucketvariant  s1b_paced.py: the same stream and cap with a weekly token bucket (start 1,
                                        refill budget / (52 x size) a week, cap 3, one token per entry)
  mk_milkmanlaneaddonfilters            milkman-study 40_addons.py's REAL rules on their lanes (v2 REPORT.md §4): 1W Cyan
                                        without a 13/48 ribbon cross in the last 10 days and 1W Green without exactly 3
                                        lower closes (W78 holds), 1D Green without PO >= 61.8 (60 sessions), 1D Swing at
                                        double size after a compression -> expansion up in the last 5 days (40 sessions)
Sizing: per fire as each study (one equal unit per fire); the units are dollars as each module states.
Gone under the cutover doctrine: the paper desk's slot caps, gross caps and red-day gates (desk-wide) are not ported;
the studies' own avoid rules, liquidity floors and budgets are.
Named divergences:
  1. universe: the store_v1 survivors (1,822 names, the research's canonical survivor store); the research's frames
     also held delisted / extension names;
  2. data: Yahoo's payloads as of each scan (later revisions included); a symbol Yahoo does not serve is skipped;
  3. META / responsiveness / genome flags (meta_bot20, meta deciles, f_resp_hit, RET-QUIET, WG08) are not computed:
     every fire takes the research's own missing-value convention (no veto, meta decile 5.5, no score bonus);
  4. tier A (option expression) is the study's own labelled proxy (c_eng.tierA_proxy), not the META-boosted tier;
  5. options: real listed calls (the expiry nearest a year, the strike nearest spot) bought at the ask within a limit,
     in place of the study's Black-Scholes value from realised volatility;
  6. execution: entries at the market in the first minutes of the next session, sized on the live quote there (the
     study used that session's open; with no quote, the fire bar's close); time exits by market-on-close on the
     planned session; the bigwinners realised P&L is s1_sleeve's (proc - basis at desk_cost) on the book's fills;
  7. breadth threshold: the train median of this universe's own breadth series (the study's 3,587 names);
  8. ratio bars: Yahoo's adjusted daily bars (adjclose factor on O/H/L/C) for the stock and SPY."""
import csv
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import MARGIN_RATE
from . import vendored as V

TZ = "America/New_York"
ET = ZoneInfo(TZ)
ENGINE_DIR = os.path.join(os.path.dirname(V.VENDOR), "galath_engine")
RUNNER = os.path.join(ENGINE_DIR, "run_engine_live.mjs")
SOURCE = {"repo": "quant-research-critical", "ref": "main", "commit": "0be4c57569e363d052bd23564cf0664697439927",
          "engine": "galath-research/real_engine/run_engine_live.mjs (5fc41630) + lib v698",
          "events": "galath-research/winners/code/build_events_real.py",
          "mirror": "quant-research-backup@d170596b4d3f24712da933683ceb6d9ee95d6937 (the same blobs; engine vendored "
                    "from there)"}
WEEKLY_CACHE = "galath_weekly.json"
DAILY_CACHE = "galath_daily.json"
TEN_Y = 3652.5 * 86400
SPY = "SPY"
TRAIN_END = "2023-09-29"
FLOOR = 1e5                      # the WEEKLY_GAPS house liquidity floor (dv20 >= $100k)


def universe():
    return tuple(s for s in V.univ_symbols())


def sector_map():
    path = os.path.join(V.VENDOR, "sector_proxy_map.csv")
    out = {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path)):
            out[r[""] if "" in r else list(r.values())[0]] = r.get("sector_etf")
    return out


# --------------------------------------------------------------------------------------------- the engine
def yahoo_payload(sym, bars, gran):
    """Yahoo chart JSON as the research's payloads (fetch_wk.py / c_eng.payload)."""
    ts = [int(b["t"]) for b in bars]
    q = {k: [float(b[s]) for b in bars] for k, s in (("open", "o"), ("high", "h"), ("low", "l"), ("close", "c"))}
    q["volume"] = [float(b.get("v") or 0.0) for b in bars]
    return {"chart": {"result": [{"meta": {"symbol": sym, "currency": "USD", "exchangeName": "NMS",
                                           "instrumentType": "EQUITY", "exchangeTimezoneName": TZ, "timezone": "EST",
                                           "dataGranularity": gran},
                                  "timestamp": ts, "indicators": {"quote": [q], "adjclose": [
                                      {"adjclose": [float(b.get("ac") or b["c"]) for b in bars]}]}}]}}


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float("nan")
    return v


def parse_rows(path):
    """the runner's CSV -> closed bars: dict of arrays t o h l c v bv bear slow pm enrich green black age rvol."""
    keep = {k: [] for k in ("t", "o", "h", "l", "c", "v", "bv", "bear", "slow", "pm", "enrich", "green", "black",
                            "age", "rvol")}
    with open(path) as f:
        for r in csv.DictReader(f):
            if r.get("barFinality") != "closed":
                continue
            keep["t"].append(int(float(r["timestamp"])))
            for k, s in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("v", "volume"),
                         ("bv", "bullishVotes"), ("bear", "bearishVotes"), ("rvol", "rvol")):
                keep[k].append(_num(r.get(s)))
            keep["slow"].append(r.get("slowState") or "")
            keep["pm"].append(r.get("primaryMarkers") or "")
            keep["enrich"].append(r.get("enrich") or "")
            keep["green"].append(r.get("green") == "1")
            keep["black"].append(r.get("black") == "1")
            keep["age"].append(_num(r.get("swingAge")))
    out = {k: np.array(v) for k, v in keep.items()}
    if len(out["t"]):                                   # duplicates keep the last (load_real), file order kept
        _, last = np.unique(out["t"][::-1], return_index=True)
        idx = np.sort(len(out["t"]) - 1 - last)
        out = {k: v[idx] for k, v in out.items()}
    return out


def run_engine(interval, series, now, on_result, workers=4, per_proc=40, timeout=1800):
    """run the vendored runner over {sym: (bars, gran)}; on_result(sym, rows) for each symbol it produced."""
    tmp = tempfile.mkdtemp(prefix="galath_engine_")
    try:
        pdir, odir = os.path.join(tmp, "p"), os.path.join(tmp, "o")
        os.makedirs(pdir)
        os.makedirs(odir)
        syms = []
        for s, (bars, gran) in series.items():
            if len(bars) < 60:
                continue
            with open(os.path.join(pdir, s.replace("^", "_") + ".json"), "w") as f:
                json.dump(yahoo_payload(s, bars, gran), f)
            syms.append(s)
        chunks = [syms[i:i + per_proc] for i in range(0, len(syms), per_proc)]
        env = dict(os.environ, TENSOR_NOW=str(int(now) + 7 * 86400))   # payloads hold completed bars only

        def go(ch):
            subprocess.run(["node", "--max-old-space-size=1200", RUNNER, interval, pdir, odir] + ch,
                           capture_output=True, text=True, timeout=timeout, env=env)
            return ch
        with ThreadPoolExecutor(max(1, int(workers))) as ex:
            for ch in ex.map(go, chunks):
                for s in ch:
                    p = os.path.join(odir, s + ".csv")
                    if os.path.exists(p):
                        on_result(s, parse_rows(p))
                        os.remove(p)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------------------------- daily features
def daily_frame(bars):
    """Yahoo daily bars -> DataFrame (date-indexed, ET session dates) with o h l c v ac."""
    if not bars:
        return None
    d = pd.DataFrame(bars)
    d["date"] = [cal._as_date(float(t) + 6 * 3600).isoformat() for t in d.t.values]
    d = d.drop_duplicates("date", keep="last")
    d = d.set_index(pd.DatetimeIndex(pd.to_datetime(d.date)))          # the index of the de-duplicated rows
    for k in ("o", "h", "l", "c", "v"):
        d[k] = d[k].astype(float)
    d["ac"] = d["ac"].astype(float) if "ac" in d else d["c"]
    return d


def week_over(friday, asof):
    """a W-FRI week is a closed bar once its last session has closed (asof: the scan time)."""
    return cal.session_close(_week_last_session(friday)) <= asof


def weekly_from_daily(d, asof):
    """Yahoo's weekly rows from its daily bars: per W-FRI week the first open, max high, min low, last close and
    adjusted close, summed volume, stamped at the week's Monday 00:00 ET (Yahoo's 1wk stamp)."""
    if d is None or not len(d):
        return []
    k = d.index.to_period("W-FRI")
    a = d.groupby(k).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), v=("v", "sum"),
                         ac=("ac", "last"))
    out = []
    for per, (o, h, l, c, v, ac) in zip(a.index, a[["o", "h", "l", "c", "v", "ac"]].values):
        if not week_over(per.end_time.date(), asof):
            continue                                           # the week is not over: Yahoo's row is still forming
        monday = per.end_time.normalize() - pd.Timedelta(days=4)          # a W-FRI period starts on Saturday
        t = int(pd.Timestamp(monday).tz_localize(TZ).timestamp())
        out.append({"t": t, "o": float(o), "h": float(h), "l": float(l), "c": float(c), "v": float(v), "ac": float(ac)})
    return out


def daily_features(d, day):
    """research features at the last session <= day: d_dist52, dv20, d_ret60, the tier-A proxy's px / r60 / dd252."""
    if d is None:
        return {}
    x = d[d.index <= pd.Timestamp(day)]
    if not len(x):
        return {}
    c, h, v = x.c.values, x.h.values, x.v.values
    i = len(c) - 1
    hi252 = np.nanmax(h[max(0, i - 251):i + 1]) if i + 1 >= 120 else np.nan
    dv20 = float(np.mean(c[max(0, i - 19):i + 1] * v[max(0, i - 19):i + 1])) if i + 1 >= 20 else np.nan
    r60 = (c[i] / c[i - 60] - 1) * 100 if i >= 60 else np.nan
    mx = np.nanmax(c[max(0, i - 251):i + 1])
    lr = np.diff(np.log(c[max(0, i - 60):i + 1]))
    rv60 = float(np.std(lr, ddof=1) * np.sqrt(252) * 100) if len(lr) == 60 else np.nan
    return {"date": str(x.index[-1].date()), "close": float(c[i]), "d_dist52": float((c[i] / hi252 - 1) * 100),
            "dv20": dv20, "d_ret60": float(r60), "dd252": float(100 * (1 - c[i] / mx)), "rvol60d": rv60}


def tier_a_proxy(px, r60, dd252, sector):
    """c_eng.tierA_proxy: >= 2 boosts (cheap <= $14.94, cheap & ret60 >= 31%, >= 70% below the 252d high, SMH) and no
    XLF / XLB / XLRE / XLU veto."""
    cheap = px <= 14.94
    boosts = int(cheap) + int(cheap and r60 >= 31) + int(dd252 >= 70) + int(sector == "SMH")
    return boosts >= 2 and sector not in ("XLF", "XLB", "XLRE", "XLU")


def _friday(t):
    """the Friday label of a weekly bar (Yahoo stamps the week's first session; load_real labels it at Friday)."""
    d = datetime.fromtimestamp(float(t), tz=ET).date()
    return d + timedelta(days=(4 - d.weekday()) % 7)


def _week_last_session(friday):
    d = friday
    while not cal.is_trading_day(d):
        d -= timedelta(days=1)
    return d


# --------------------------------------------------------------------------------------------- the weekly scan
def _bars(hub, interval, syms, n, since):
    """Yahoo payloads one symbol at a time (the hub drops a whole request when one symbol fails), last 10 years."""
    out = {}
    for s in syms:
        bl = hub.bars("yahoo", interval, [s], n).get(s) or []
        bl = [b for b in bl if float(b["t"]) >= since]
        if bl:
            out[s] = bl
    return out


def run_weekly(hub, root, now, syms=None, workers=4):
    """the weekly job: 1W fires with their features, the vote breadth, the stock/SPY ratio fires."""
    syms = list(syms or universe())
    sect = sector_map()
    dl = _bars(hub, "1d", syms + [SPY], 2600, now - TEN_Y)
    D = {s: daily_frame(b) for s, b in dl.items()}
    wk = {s: weekly_from_daily(D[s], now) for s in syms if D.get(s) is not None}
    breadth, fires, last_week = {}, [], {"t": 0}

    def on_week(s, r):
        n = len(r["t"])
        for i in range(n):
            k = str(_friday(r["t"][i]))
            b = breadth.setdefault(k, [0, 0, 0, 0, 0, 0])
            b[0] += 1
            for j, kk in enumerate((4, 5, 6, 7)):
                b[1 + j] += int(r["bv"][i] >= kk)
            b[5] += int(r["slow"][i] == "bullish")
        if n:
            last_week["t"] = max(last_week["t"], int(r["t"][-1]))
        logc = np.log(np.where(r["c"] > 0, r["c"], np.nan))
        ep, prev = 0, None
        for i in range(60, n):
            pm = r["pm"][i].split("|")
            cy, gr = "buy-cyan" in pm, "buy-green" in pm
            if not (cy or gr):
                continue
            wj = _friday(r["t"][i]).toordinal() // 7                 # build_frame's ep_own: 13-week links
            ep = ep + 1 if (prev is not None and 0 < wj - prev <= 13) else 1
            prev = wj
            if r["t"][i] < now - 140 * 7 * 86400:
                continue
            lo = max(0, i - 59)
            depth60 = (1 - np.nanmin(r["l"][lo:i + 1]) / np.nanmax(r["h"][lo:i + 1])) * 100 if i >= 59 else np.nan
            rv = np.diff(logc[max(0, i - 20):i + 1])
            rvol20 = float(np.std(rv, ddof=1)) if len(rv) == 20 and np.isfinite(rv).all() else np.nan
            fri = _friday(r["t"][i])
            f = {"sym": s, "t": int(r["t"][i]), "friday": str(fri), "last_session": str(_week_last_session(fri)),
                 "lane": "cyan" if cy else "green", "close": float(r["c"][i]), "bv": float(r["bv"][i]),
                 "ep": ep, "depth60": float(depth60), "rvol20": rvol20, "sector": sect.get(s)}
            f.update({k: v for k, v in daily_features(D.get(s), fri).items() if k != "close"})
            if r["t"][i] >= now - 6 * 7 * 86400:
                f.update(milkman_flags(D.get(s), fri))
            fires.append(f)
    run_engine("1wk", {s: (b, "1wk") for s, b in wk.items()}, now, on_week, workers=workers)
    ratio = ratio_fires(D, now, workers=workers, sect=sect)
    doc = {"asof": now, "last_week": last_week["t"], "n_syms": len(wk), "fires": fires, "ratio_fires": ratio,
           "breadth": {k: v for k, v in sorted(breadth.items())}}
    _write(root, WEEKLY_CACHE, doc)
    return {"syms": len(wk), "fires": len(fires), "ratio_fires": len(ratio), "weeks": len(breadth)}


def ratio_bars(stock, bench, asof):
    """c03_ratio: daily ratio OHLC of adjusted prices (H = max, L = min of the four ratios, the stock's volume) -> W-FRI
    weekly bars stamped at the week's first session 09:30 ET (c_eng.payload)."""
    if stock is None or bench is None:
        return [], {}
    adj = lambda x: pd.DataFrame({k: x[k] * (x.ac / x.c) for k in "ohlc"} | {"v": x.v}, index=x.index)
    d, B = adj(stock), adj(bench)
    d = d.dropna(subset=["c"])
    B = B.reindex(d.index)
    ok = B.c.notna() & (d.c > 0)
    d, B = d[ok], B[ok]
    r = pd.DataFrame(dict(o=d.o / B.o, h=d.h / B.h, l=d.l / B.l, c=d.c / B.c, v=d.v))
    r["h"] = r[["o", "h", "l", "c"]].max(axis=1)
    r["l"] = r[["o", "h", "l", "c"]].min(axis=1)
    if not len(r):
        return [], {}
    k = r.index.to_period("W-FRI")
    a = r.groupby(k).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), v=("v", "sum"))
    st = r.index.to_series().groupby(k).first()
    en = r.index.to_series().groupby(k).last()
    over = np.array([week_over(p.end_time.date(), asof) for p in a.index], dtype=bool)
    a, st, en = a[over], st[over], en[over]                    # a week still in progress is not a bar yet
    a.index = pd.DatetimeIndex(st.values)
    keep = a[["o", "h", "l", "c"]].notna().all(axis=1).values & (a.c > 0).values     # c_eng.payload's row filter
    a, en = a[keep], en[keep]
    q = a[["o", "h", "l", "c"]].round(6)
    vol = a.v.fillna(0).astype(float)
    bars, bend = [], {}
    for s0, (o, h, l, c), v, e0 in zip(a.index, q.values, vol.values, en.values):
        t = int(pd.Timestamp(s0).tz_localize(TZ).timestamp()) + 9 * 3600 + 1800
        bars.append({"t": t, "o": float(o), "h": float(h), "l": float(l), "c": float(c), "v": float(v)})
        bend[t] = str(pd.Timestamp(e0).date())
    return bars, bend


def ratio_fires(D, now, workers=4, sect=None):
    bench = D.get(SPY)
    series, ends = {}, {}
    for s, d in D.items():
        if s == SPY or d is None:
            continue
        bars, bend = ratio_bars(d, bench, now)
        if len(bars) >= 60:
            series[s] = (bars, "1wk")
            ends[s] = bend
    out = []

    def on_ratio(s, r):
        for i in range(len(r["t"])):
            if r["t"][i] < now - 140 * 7 * 86400:
                continue
            pm = r["pm"][i].split("|")
            for ln in ("cyan", "green"):
                if f"buy-{ln}" in pm:
                    end = ends[s].get(int(r["t"][i]))
                    if end:
                        f = {"sym": s, "t": int(r["t"][i]), "lane": ln, "bend": end, "bv": float(r["bv"][i])}
                        f.update({k: v for k, v in daily_features(D.get(s), end).items()})
                        out.append(f)
    run_engine("1wk", series, now, on_ratio, workers=workers)
    return out


# --------------------------------------------------------------------------------------------- the daily scan
def milkman_flags(d, day):
    """40_addons.flags_for at the fire-date close: RIB_CROSS10, LBD3, PO_DIST, CEX_UP5 (dstrats on the daily bars)."""
    if d is None:
        return {}
    x = d[d.index <= pd.Timestamp(day)]
    n = len(x)
    if n < 60:
        return {}
    D = V.dstrats()
    # the study computed the flags over the full history: a bar's signal never depends on later bars, but buyday
    # blanks the series' last bar (it needs a next open) -- so the fire bar is followed by a copy of itself here
    pick = np.r_[np.arange(n), n - 1]
    dd = dict(date=np.r_[x.index.values.astype("datetime64[ns]"), x.index.values[-1:] + np.timedelta64(1, "D")],
              o=x.o.values[pick], h=x.h.values[pick], l=x.l.values[pick], c=x.c.values[pick], v=x.v.values[pick],
              kind="stock")
    C = D._cache(dd)
    t = n - 1

    def within(ent, k):
        return bool(any(e >= 0 and e <= t <= e + k for e in ent))
    out = {"RIB_CROSS10": within(D.ribbon(dd, 1)["ent"], 10),
           "LBD3": within(D.buyday(dd, 1, k=3, exact=True)["ent"], 0),
           "PO_DIST": bool(C["po"][t] >= 61.8),
           "CEX_UP5": within(D.comp_expansion(dd, 1, minbars=5, H=10)["ent"], 5)}
    dd.pop("_c", None)
    return out


def run_daily(hub, root, now, syms=None, workers=4):
    """the daily job: 1D Green and 1D Swing fires of the latest sessions with their Milkman flags."""
    syms = list(syms or universe())
    dl = _bars(hub, "1d", syms, 2600, now - TEN_Y)
    D = {s: daily_frame(b) for s, b in dl.items()}
    fires = []
    recent = now - 12 * 86400

    def on_day(s, r):
        n = len(r["t"])
        seen = set()
        for i in range(60, n):
            day = cal._as_date(float(r["t"][i]) + 6 * 3600).isoformat()
            pm = r["pm"][i].split("|")
            if i >= 250 and "buy-green" in pm and r["t"][i] >= recent:
                fires.append({"sym": s, "t": int(r["t"][i]), "day": day, "lane": "d_green", "close": float(r["c"][i])})
            if r["green"][i] and np.isfinite(r["age"][i]) and 0 <= r["age"][i] <= 3:
                key = i - int(r["age"][i])                 # the production key: the setup (black-square) bar
                if key in seen:
                    continue
                seen.add(key)
                if r["t"][i] >= recent:
                    fires.append({"sym": s, "t": int(r["t"][i]), "day": day, "lane": "d_swing",
                                  "close": float(r["c"][i]), "age": int(r["age"][i])})
    run_engine("1d", {s: (b, "1d") for s, b in dl.items()}, now, on_day, workers=workers)
    for f in fires:
        f.update(milkman_flags(D.get(f["sym"]), f["day"]))
        f.update({k: v for k, v in daily_features(D.get(f["sym"]), f["day"]).items() if k != "close"})
    doc = {"asof": now, "n_syms": len(dl), "fires": fires}
    _write(root, DAILY_CACHE, doc)
    return {"syms": len(dl), "fires": len(fires)}


def _write(root, name, doc):
    p = os.path.join(root, "cache", name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(doc, f, default=float)
    os.replace(tmp, p)


def docs(root):
    """the scans' latest output (cache files written by the galath jobs), re-read when a file changes."""
    out = {}
    for k, name in (("weekly", WEEKLY_CACHE), ("daily", DAILY_CACHE)):
        p = os.path.join(root, "cache", name)
        try:
            st = os.stat(p)
            key = (p, st.st_mtime_ns)
            if _CACHE.get(p, (None,))[0] != key:
                _CACHE[p] = (key, json.load(open(p)))
            out[k] = _CACHE[p][1]
        except (OSError, ValueError):
            out[k] = None
    return out


_CACHE = {}


def feed_galath(f, s, now, arg):
    root = getattr(getattr(s, "engine", None), "root", None)
    return docs(root) if root is not None else None


def feed_quotes(f, s, now, arg):
    """live quotes for the fires a sleeve enters this pass (its entry price, as the study's entry-session open)."""
    plan = s.quote_plan(now) if hasattr(s, "quote_plan") else []
    return f.hub.quotes(f.hub.resolve("equity"), plan) if plan else {}


# --------------------------------------------------------------------------------------------- shared sleeve machinery
def session_after(day, k):
    """the k-th trading session after `day` (k = 0: day itself)."""
    d = cal._as_date(day)
    while k > 0:
        d = cal.next_trading_day(d)
        k -= 1
    return d.isoformat()


def week_plus(friday, weeks):
    """the last session of the week `weeks` after the week ending `friday` (the W52 / W78 exit session)."""
    return _week_last_session(cal._as_date(friday) + timedelta(days=7 * weeks)).isoformat()


def desk_cost(px):
    """bigwinners common.desk_cost: % per side by price tier."""
    return 0.05 + (0.25 if px < 5 else (0.10 if px < 20 else 0.05))


class FireBook(Sleeve):
    """fire-driven positions: a ledger row per entered fire {sym, qty, asset, exit_on}. A fire enters on its entry session
    (the session after the fire week / fire day; one session later when the desk missed it) at the market in the first
    90 minutes; a row exits by market-on-close on its planned session (options: a marketable order that session)."""
    SID = ""
    STUDY = ""
    CAPITAL = 1_000_000.0
    NEEDS_QUOTES = ()
    ENTRY_QUOTES = True

    def __init__(self):
        self.engine = None
        needs = {"feeds": ["galath", "galath_quotes"] if self.ENTRY_QUOTES else ["galath"]}
        if self.NEEDS_QUOTES:
            needs["quotes"] = {"source": "equity", "symbols": list(self.NEEDS_QUOTES)}
        self.CONFIG = SleeveConfig(
            sleeve_id=self.SID, family="milkman", cadence_s=300, universe=tuple(self.NEEDS_QUOTES),
            capital=self.CAPITAL, schedule="rth", needs=needs, params=dict(self.params(), margin_rate=MARGIN_RATE),
            source=dict(SOURCE, study=self.STUDY),
            state_schema={"ledger": "dict", "seen": "dict", "log": "list", "extra": "dict"})

    def params(self):
        return {}

    def bind(self, engine):
        self.engine = engine

    def signal(self, view):
        now, session = float(view.now), view.session
        st = dict(view.state or {})
        for k, v in (("ledger", {}), ("seen", {}), ("log", []), ("extra", {})):
            st.setdefault(k, v)
        self._st = st
        if not cal.is_rth(now):
            return []
        out = []
        moc = now >= cal.session_close(session) - 12 * 60
        for key, x in list(st["ledger"].items()):
            due = x.get("exit_on")
            if due and (due < session or (due == session and (moc or x.get("asset") == "option"))):
                out.append(self._exit(view, st, key, x, moc=(due == session and x.get("asset") != "option")))
        if now <= cal.session_open(session) + 90 * 60:
            out += self.entries(view, st, view.extra.get("galath") or {}, session, now)
        if len(st["seen"]) > 4000:
            for k in sorted(st["seen"], key=lambda k: st["seen"][k])[:-3000]:
                st["seen"].pop(k)
        return out

    def due(self, st, key, entry_on, session):
        """a fire not seen yet whose entry session is today (or was yesterday): enter; later: missed."""
        if key in st["seen"]:
            return False
        if entry_on > session:
            return False
        st["seen"][key] = session
        late = cal.trading_days_between(entry_on, session)
        if late > 1:
            if late <= 5:
                st["log"] = (st["log"] + [{"key": key, "why": "missed (desk down)", "at": session}])[-300:]
            return False
        return True

    def _exit(self, view, st, key, x, moc):
        st["ledger"].pop(key, None)
        st["log"] = (st["log"] + [dict(x, key=key, why="planned exit" + (" (market-on-close)" if moc else ""),
                                       at=view.session)])[-300:]
        held = float((view.positions.get(("OPT:" if x.get("asset") == "option" else "EQ:") + x["sym"]) or {})
                     .get("qty") or 0.0)
        qty = min(float(x["qty"]), held) if held > 0 else float(x["qty"])
        return Intent("exit", x["sym"], side="long", qty=qty, asset=x.get("asset", "equity"),
                      signal_key=f"{key}:exit", reason=f"{self.SID} planned exit {x.get('exit_on')}",
                      order=OrderSpec(type="market", tif="cls") if moc else OrderSpec(window_s=1800))

    def enter(self, st, key, sym, qty, ref, exit_on, why, asset="equity", order=None, meta=None):
        st["ledger"][key] = {"sym": sym, "qty": float(qty), "ref": float(ref), "exit_on": exit_on, "asset": asset,
                             **(meta or {})}
        return Intent("enter", sym, side="long", qty=float(qty), asset=asset, price_hint=float(ref),
                      signal_key=key, reason=f"{self.SID} {why}", order=order or OrderSpec(window_s=1800))

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})

    def entries(self, view, st, G, session, now):
        return []

    @staticmethod
    def price(view, sym, ref):
        """the entry price: the live quote (ask, else last, else bid), else the fire bar's close."""
        q = ((view.extra or {}).get("galath_quotes") or {}).get(sym) or {}
        for k in ("ask", "last", "bid"):
            v = q.get(k)
            if v and float(v) > 0 and math.isfinite(float(v)):
                return float(v)
        return float(ref)

    def quote_plan(self, now):
        """the symbols this pass would enter (a dry run of entries() on an empty book), first 90 minutes only."""
        if self.engine is None or not cal.is_rth(now):
            return []
        session = cal._as_date(now).isoformat()
        if now > cal.session_open(session) + 90 * 60:
            return []
        from ...contract import View
        v = View(now=float(now), session=session, cash=self.CONFIG.capital, equity=self.CONFIG.capital)
        st = {"ledger": {}, "seen": {}, "log": [], "extra": {}}
        return sorted({it.symbol for it in self.entries(v, st, docs(self.engine.root), session, now)})


def _weekly(G):
    return (G or {}).get("weekly") or {}


def _daily(G):
    return (G or {}).get("daily") or {}


# --------------------------------------------------------------------------------------------- c04: breadth timing
class BreadthTiming(Sleeve):
    """c04b's timing book: IN the index when the weekly vote breadth is at or below its train quantile, else cash."""
    METRIC, Q, INDEX = 5, 0.5, "IWM"

    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id="mk_creativetensorbreadthtiming", family="milkman", cadence_s=300, universe=(self.INDEX,),
            capital=100_000.0, schedule="rth", needs={"feeds": ["galath"], "quotes": {"source": "equity",
                                                                                       "symbols": [self.INDEX]}},
            params={"metric": f"share bullishVotes >= {self.METRIC}", "q": self.Q, "index": self.INDEX,
                    "off_exposure": 0.0, "train_end": TRAIN_END, "margin_rate": MARGIN_RATE},
            source=dict(SOURCE, study="galath-research/TENSOR_CREATIVE/code/c04_breadth.py + c04b_book.py "
                                      "(blobs 7a384066 / quant-research-backup)"),
            state_schema={"week": "str", "on": "bool", "thr": "float"})

    def bind(self, engine):
        self.engine = engine

    @staticmethod
    def series(breadth, k):
        """{friday: [n, bv4, bv5, bv6, bv7, slow]} -> [(friday, share)] for weeks with >= 500 names."""
        j = {4: 1, 5: 2, 6: 3, 7: 4, "slow": 5}[k]
        return [(w, v[j] / v[0]) for w, v in sorted(breadth.items()) if v[0] >= 500]

    def decide(self, breadth, upto):
        s = [(w, x) for w, x in self.series(breadth, self.METRIC) if w <= upto]
        tr = [x for w, x in s if w <= TRAIN_END]
        if not s or len(tr) < 20:
            return None
        th = float(np.nanquantile(tr, self.Q))
        w, x = s[-1]
        return {"week": w, "x": x, "thr": th, "on": bool(x <= th)}

    def signal(self, view):
        now, session = float(view.now), view.session
        st = dict(view.state or {})
        self._st = st
        W = _weekly(view.extra.get("galath"))
        if not cal.is_rth(now) or not W.get("breadth"):
            return []
        last_fri = (cal._as_date(session) - timedelta(days=(cal._as_date(session).weekday() - 4) % 7 or 7))
        d = self.decide(W["breadth"], str(last_fri))
        if d is None or d["week"] != str(last_fri):
            return []                                          # the week's scan is not in yet
        q = (view.quotes or {}).get(self.INDEX) or {}
        px = q.get("ask") or q.get("last") or q.get("bid")
        if not px:
            return []
        if st.get("week") == d["week"] and st.get("on") == d["on"]:
            held = float((view.positions.get("EQ:" + self.INDEX) or {}).get("qty") or 0.0)
            if (held > 0) == d["on"]:
                return []
        st.update(week=d["week"], on=d["on"], thr=d["thr"], x=d["x"])
        qty = (self.CONFIG.capital / float(px)) if d["on"] else 0.0
        return [Intent("target", self.INDEX, side="long", qty=qty, price_hint=float(px),
                       signal_key=f"{self.INDEX}:{d['week']}:{'in' if d['on'] else 'out'}",
                       reason=f"breadth bv>={self.METRIC} {d['x']:.4f} {'<=' if d['on'] else '>'} train q{self.Q} "
                              f"{d['thr']:.4f} (week {d['week']})", order=OrderSpec(window_s=1800))]

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


# --------------------------------------------------------------------------------------------- c03: ratio charts
class RatioSignals(FireBook):
    SID = "mk_creativetensorratiochartsignals"
    STUDY = "galath-research/TENSOR_CREATIVE/code/c03_ratio.py (83c8e7ac)"
    CAPITAL = 3_000_000.0
    H, SIZE = 252, 1_000.0

    def params(self):
        return {"bench": SPY, "hold_sessions": self.H, "per_fire_usd": self.SIZE, "floor_dv20": FLOOR}

    def entries(self, view, st, G, session, now):
        out = []
        for f in _weekly(G).get("ratio_fires") or []:
            key = f"ratio|{f['lane']}|{f['sym']}|{f['t']}"
            entry_on = session_after(f["bend"], 1)
            if not (f.get("dv20") or 0) >= FLOOR or not f.get("close"):
                continue
            if not self.due(st, key, entry_on, session):
                continue
            px = self.price(view, f["sym"], f["close"])
            out.append(self.enter(st, key, f["sym"], self.SIZE / px, px, session_after(f["bend"], self.H),
                                  f"ratio {f['lane']} fire week ending {f['bend']}"))
        return out


# --------------------------------------------------------------------------------------------- c01: option expression
class OptionExpression(FireBook):
    SID = "mk_creativetensoroptionexpressionproxy"
    STUDY = "galath-research/TENSOR_CREATIVE/code/c01_options.py (0500016c)"
    CAPITAL = 1_000_000.0
    PREMIUM, PMIN, WEEKS = 1_000.0, 0.02, 52
    ENTRY_QUOTES = False

    def __init__(self):
        super().__init__()
        self.CONFIG.needs["feeds"] = ["galath", "galath_chains"]

    def params(self):
        return {"tier": "A (c_eng.tierA_proxy)", "strike": "spot (k = 1.0)", "expiry": "nearest 52 weeks",
                "premium_usd": self.PREMIUM, "pmin": self.PMIN, "hold_weeks": self.WEEKS, "floor_dv20": FLOOR}

    def candidates(self, G, session):
        out = []
        for f in _weekly(G).get("fires") or []:
            if not f.get("close") or not (f.get("dv20") or 0) >= FLOOR:
                continue
            if not tier_a_proxy(float(f["close"]), float(f.get("d_ret60") or np.nan), float(f.get("dd252") or 0.0),
                                f.get("sector")):
                continue
            rv = f.get("rvol60d")
            if rv is not None and not (5 <= rv <= 400):
                continue
            out.append(f)
        return out

    def chain_plan(self, now):
        if self.engine is None:
            return []
        G = docs(self.engine.root)
        session = cal._as_date(now).isoformat()
        return sorted({f["sym"] for f in self.candidates(G, session)
                       if session_after(f["last_session"], 1) <= session <= session_after(f["last_session"], 2)})

    def entries(self, view, st, G, session, now):
        out = []
        chains = view.extra.get("galath_chains") or {}
        for f in self.candidates(G, session):
            key = f"opt|{f['lane']}|{f['sym']}|{f['t']}"
            entry_on = session_after(f["last_session"], 1)
            if key in st["seen"] or entry_on > session:
                continue
            rows = chains.get(f["sym"])
            if rows is None:
                continue                                       # no chain this pass: try again next pass
            if not self.due(st, key, entry_on, session):
                continue
            spot = float(f["close"])
            pick = pick_call(rows, spot, session, self.WEEKS)
            if pick is None:
                st["log"] = (st["log"] + [{"key": key, "why": "no listed call near a year", "at": session}])[-300:]
                continue
            ask = float(pick["ask"])
            if ask < self.PMIN * spot:
                st["log"] = (st["log"] + [{"key": key, "why": "premium under 2% of spot", "at": session}])[-300:]
                continue
            n = int(self.PREMIUM // (ask * 100))
            if n < 1:
                if ask * 100 > 2 * self.PREMIUM:
                    st["log"] = (st["log"] + [{"key": key, "why": "one contract over twice the budget",
                                               "at": session}])[-300:]
                    continue
                n = 1
            exit_on = min(week_plus(f["friday"], self.WEEKS), session_after(pick["expiration"], 0)
                          if cal.is_trading_day(pick["expiration"]) else cal.prev_trading_day(pick["expiration"]).isoformat())
            out.append(self.enter(st, key, pick["symbol"], n, ask, exit_on,
                                  f"call {pick['symbol']} on {f['lane']} fire of {f['sym']} ({f['friday']})",
                                  asset="option",
                                  order=OrderSpec(type="limit", limit_price=round(ask * 1.02, 2), window_s=3600),
                                  meta={"underlying": f["sym"]}))
        return out


def pick_call(rows, spot, session, weeks):
    """the listed call whose expiry is nearest `weeks` weeks out (at least 75% of it) and, there, the strike nearest
    spot, with a two-sided market."""
    d0 = cal._as_date(session)
    want = weeks * 7
    by_exp = {}
    for r in rows or ():
        if r.get("type") != "call" or not r.get("ask") or not r.get("bid"):
            continue
        dte = (date.fromisoformat(r["expiration"]) - d0).days
        if dte < 0.75 * want:
            continue
        by_exp.setdefault(r["expiration"], []).append(r)
    if not by_exp:
        return None
    exp = min(by_exp, key=lambda e: (abs((date.fromisoformat(e) - d0).days - want), e))
    return min(by_exp[exp], key=lambda r: (abs(float(r["strike"]) - spot), float(r["strike"])))


def feed_chains(f, s, now, arg):
    """the call chains (250+ days) of the option-expression sleeve's candidates this pass."""
    plan = s.chain_plan(now) if hasattr(s, "chain_plan") else []
    out = {}
    for u in plan:
        rows = f.chains(u, dte_min=250, dte_max=800, typ="call")
        if rows is not None:
            out[u] = rows
    return out


# --------------------------------------------------------------------------------------------- bigwinners S1 / S1b
def bw_stream(f):
    """build_frame.py's CAL_NAV for one 1W fire, with the missing-value convention for META / f_resp_hit / genome
    flags; returns (in_stream, score)."""
    px, dv20 = float(f.get("close") or np.nan), float(f.get("dv20") or 0.0)
    cy, gr = f["lane"] == "cyan", f["lane"] == "green"
    sect = f.get("sector") or ""
    d52 = f.get("d_dist52")
    d52 = float(d52) if d52 is not None else np.nan
    avoid = (px >= 100) or (cy and d52 >= -5) or sect in ("XLF", "XLB", "XLRE") or (cy and sect == "XLU") or \
        (gr and int(f.get("ep") or 1) >= 2)
    dp = float(f.get("depth60") if f.get("depth60") is not None else np.nan)
    rv = float(f.get("rvol20") if f.get("rvol20") is not None else np.nan)
    m60 = float(f.get("d_ret60") if f.get("d_ret60") is not None else np.nan)
    calib = (cy and (px <= 14.94 or dp >= 70.35)) or (gr and px <= 13.15 and rv >= 0.08896)
    liquid = dv20 >= 1e6
    B = 0.0
    for cond, b in ((cy and px < 5, 1.0), (cy and px <= 14.94 and m60 >= 31.03, 1.0), (cy and dp >= 70.35, 0.75),
                    (gr and px <= 13.15 and rv >= 0.08896, 0.75), (cy and px <= 14.94, 0.5)):
        if cond:
            B = max(B, b)
    score = 5.5 + (B if dv20 >= 2e6 else 0.0)
    return bool(liquid and not avoid and calib), score


class BigWinners(FireBook):
    SID = "mk_bigwinnersmanysmallpositionssleeve"
    STUDY = "galath-research/bigwinners/code/s1_sleeve.py (70cfa858), proposal_weekly_sleeve.md W52S-CAL"
    CAPITAL = 100_000.0
    SIZE, BUDGET, PACED = 1_000.0, 50_000.0, False

    def params(self):
        return {"stream": "CAL_NAV", "size_usd": self.SIZE, "budget_usd": self.BUDGET, "mode": "sweep",
                "paced": self.PACED, "hold": "W52 close"}

    def entries(self, view, st, G, session, now):
        cands = []
        for f in _weekly(G).get("fires") or []:
            ok, score = bw_stream(f)
            if not ok:
                continue
            key = f"bw|{f['sym']}|{f['t']}"
            entry_on = session_after(f["last_session"], 1)
            if key in st["seen"] or entry_on > session:
                continue
            cands.append((-score, -(f.get("dv20") or 0.0), f["sym"], int(f["t"]), key, entry_on, f))
        if not cands:
            return []
        held_syms = {x["sym"] for x in st["ledger"].values()}
        realised = self.realised(view, st)
        openb = sum(float(x["qty"]) * float(x["ref"]) * (1 + desk_cost(float(x["ref"])) / 100)
                    for x in st["ledger"].values())
        cap = self.BUDGET + min(0.0, realised)
        if self.PACED:
            ex = st["extra"]
            wk = int(now // (7 * 86400))
            tok = float(ex.get("tok", 1.0))
            if ex.get("wk") is not None:
                tok = min(3.0, tok + self.BUDGET / (52 * self.SIZE) * (wk - int(ex["wk"])))
            ex["wk"] = wk
        out = []
        for *_, key, entry_on, f in sorted(cands, key=lambda c: c[:4]):
            if not self.due(st, key, entry_on, session):
                continue
            if f["sym"] in held_syms:
                continue
            if self.PACED and tok < 1:
                continue
            E = self.price(view, f["sym"], f["close"])
            q = int(self.SIZE // E)
            if q < 1:
                continue
            basis = q * E * (1 + desk_cost(E) / 100)
            if openb + basis > cap:
                st["log"] = (st["log"] + [{"key": key, "why": "budget", "at": session}])[-300:]
                continue
            openb += basis
            held_syms.add(f["sym"])
            if self.PACED:
                tok -= 1
            out.append(self.enter(st, key, f["sym"], q, E, week_plus(f["friday"], 52),
                                  f"W52S-CAL {f['lane']} fire week {f['friday']}"))
        if self.PACED:
            st["extra"]["tok"] = tok
        return out

    @staticmethod
    def realised(view, st):
        """s1_sleeve's realised: proc - basis of every closed row (desk_cost on the entry price, both sides), from
        the book's closed trades (each counted once)."""
        ex = st["extra"]
        done = list(ex.get("acct") or [])
        seen = set(done)
        r = float(ex.get("realised", 0.0))
        for t in (view.extra or {}).get("closed_trades") or []:
            if not str(t.get("inst", "")).startswith("EQ:"):
                continue
            k = f"{t.get('inst')}|{t.get('closed_at')}|{t.get('qty')}|{t.get('exit')}"
            if k in seen:
                continue
            seen.add(k)
            done.append(k)
            q, e, x = abs(float(t["qty"])), float(t["entry"]), float(t["exit"])
            basis = q * e * (1 + desk_cost(e) / 100)
            proc = q * x * (1 - desk_cost(e) / 100)
            r += proc - basis
        ex["realised"] = r
        ex["acct"] = done[-1000:]
        return r


class BigWinnersPaced(BigWinners):
    SID = "mk_bigwinnerspacedtokenbucketvariant"
    STUDY = "galath-research/bigwinners/code/s1b_paced.py (41baeca8)"
    PACED = True


# --------------------------------------------------------------------------------------------- 40_addons REAL rules
class LaneAddons(FireBook):
    SID = "mk_milkmanlaneaddonfilters"
    STUDY = "milkman-study/v2/code/40_addons.py (dc25c9b9) + v2 REPORT.md §4 REAL rules"
    CAPITAL = 5_000_000.0
    SIZE = 1_000.0

    def params(self):
        return {"w_cyan": "avoid RIB_CROSS10, W78", "w_green": "avoid LBD3, W78", "d_green": "avoid PO_DIST, T60",
                "d_swing": "boost x2 on CEX_UP5, NS40", "per_fire_usd": self.SIZE, "floor_dv20": FLOOR}

    def entries(self, view, st, G, session, now):
        out = []
        for f in _weekly(G).get("fires") or []:
            ln = "w_" + f["lane"]
            key = f"{ln}|{f['sym']}|{f['t']}"
            flag = f.get("RIB_CROSS10") if ln == "w_cyan" else f.get("LBD3")
            if flag is None or flag or not (f.get("dv20") or 0) >= FLOOR or not f.get("close"):
                continue
            entry_on = session_after(f["last_session"], 1)
            if not self.due(st, key, entry_on, session):
                continue
            px = self.price(view, f["sym"], f["close"])
            out.append(self.enter(st, key, f["sym"], self.SIZE / px, px, week_plus(f["friday"], 78),
                                  f"{ln} fire week {f['friday']} (no {'RIB_CROSS10' if ln == 'w_cyan' else 'LBD3'})"))
        for f in _daily(G).get("fires") or []:
            ln = f["lane"]
            key = f"{ln}|{f['sym']}|{f['t']}"
            if not (f.get("dv20") or 0) >= FLOOR or not f.get("close"):
                continue
            if ln == "d_green":
                if f.get("PO_DIST") is None or f["PO_DIST"]:
                    continue
                size, hold, why = self.SIZE, 60, "d_green (PO below 61.8)"
            else:
                if f.get("CEX_UP5") is None:
                    continue
                size, hold = self.SIZE * (2 if f["CEX_UP5"] else 1), 40
                why = "d_swing" + (" boosted (CEX_UP5)" if f["CEX_UP5"] else "")
            entry_on = session_after(f["day"], 1)
            if not self.due(st, key, entry_on, session):
                continue
            px = self.price(view, f["sym"], f["close"])
            out.append(self.enter(st, key, f["sym"], size / px, px, session_after(f["day"], hold),
                                  f"{why} fire {f['day']}"))
        return out


def sleeves():
    return [BreadthTiming(), RatioSignals(), OptionExpression(), BigWinners(), BigWinnersPaced(), LaneAddons()]
