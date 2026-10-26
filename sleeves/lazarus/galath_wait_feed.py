"""galath_wait_feed: the producer of the six Lazarus WAIT lanes (s_wait_*), on the rules Research Lab froze for them
(galath-research DESK_INTEGRATION/sleeve_specs/<lane>/README.md, 2026-10-05/06; vendored byte-exact under
desk/vendor/galath_research/DESK_INTEGRATION/sleeve_specs). The source never composed these lanes: sleeve_feed 1.0.4 kept them as
WAIT placeholders (Lazarus state dead) and the specs say the desk wiring was still to be done. This is that wiring, written for this
desk. It reads the research producers' live outputs under the research root (<root>/inputs/lazarus) and writes
shadow/paper_sleeve/live/wait_fires_v1.json in the sleeve_fires_v1 fire schema; the WAIT lanes read that file
(lazarus.LIVE_RULES, key "fires_wait").

Run as a script by the research venv (the galath_wait_feed job, desk/sleeves/families/galath_wait.py) so it can import the vendored
research modules it relies on (shadow/paper_sleeve/sleeve_band.py + shadow/addons_sc.py: the PIT SEC band; shadow/addons_sources_st.py:
the trading calendar). Its rule functions are pure and import with the desk's own Python (tests/test_galath_wait.py).

Rules (each README's "Rule" section). The entry / hold mechanics on the engine are in lazarus.live_row:
  s_wait_q14        a tracker 1W Cyan or 1W Green fire (lane 1w) with addons_ue tier A (the ue_tag tier, = research tier_c1) and
                    close_D <= $5.00 -> entry at the next open with the limit capped at $5.00 (the README's OPG limit at 5.00);
                    exit W78 (the close of the 78th weekly bar), no stop.
  s_wait_flow       a tracker 1D Green fire, dv20 >= $100k and close_D from its lc2_tag (ue_tag, then the fire record, when absent),
                    PIT band small (sleeve_band; unknown fails closed), $5 <= close_D < $20, svr5 >= 0.447678 (FINRA Reg SHO consolidated
                    short volume: the mean of ShortVolume / TotalVolume over the 5 files through D's file, min 3; no fire when the newest
                    file <= D is more than 7 days old) -> entry D+1 open, exit the close of D+60, no stop.
  s_wait_chase      a tracker 1W Cyan fire whose mom126 rank at t (the last session <= the fire Friday) against the liquid
                    cross-section LQ is >= 0.90 (paper_families mom126_top10: Cf[t] / Cf[t-126] - 1, searchsorted right / n, >= 50 LQ
                    names; LQ = bar present, dv20 >= $0.5M (UC rule), SIC operating company and not an ETF, close >= $5, dv20 >= $1M;
                    params and lists from paper_families_v1_frozen.json) and Cf[t] / max(Cf over the last 63 sessions, min 40) - 1 > -0.05
                    -> entry at the next open, exit W52, no stop.
  s_wait_olx_books  the 29 live-loadable OLX R1/R2 clean-support frozen rules (olx_r12_other.ids) scored by the live lab producer
                    (lab_live.mjs --frozen-ids --no-books, frozen rules only, on the lab_live panel; DESK_INTEGRATION/lab_live/out/olx)
                    -> entry at the next session, exit entry + H sessions (H + 1 from the fill: the s_rules mechanics), no stop.
  s_wait_r2_dcyan   the R2 Daily Cyan book the readout found clearing the gate (1D Cyan covered, the rule-search book), scored live by
                    lab_live's 1D-cyan-covered job on the tracker universe (the README's second option: "run it on the tracker universe and
                    accept the rate gap") -> entry at the next session, hold the job's 1D horizon (21 sessions) from the fill, no stop.
  s_wait_intraweek  Mon-Thu after the close (day k = 1..4, never the week's last session): a provisional 1W Cyan or Green marker on the
                    developing week (galath_intraweek.mjs: the unchanged engine library on the tracker's completed Yahoo weeks + the
                    research builder's partial bar) -> entry at the next session's open, exit the close of the fire Friday + 52 weeks
                    (W52 from the fire week), no stop; one fire per symbol-week, keyed and dated by its first day k.

Named divergences (inputs; each is also written into the output's lanes.<lane>.divergences):
  q14     none in the rule; the desk's next-open DAY limit (capped at $5.00) stands in for the OPG order.
  flow    svr5 from ALTDATA_LIVE out/finra_svr_history.parquet (the input the README maps) when it is present and covers D; else from
          FINRA's public CNMS daily files directly (the same files the ALTDATA finra_flow plug-in reads), cached in the job's cache.
          --no-finra-fetch WHY (the job passes it while galath_producers.OFF holds altdata_nightly, FEED-04a): no FINRA file is
          requested, only cached ones are read, and the lane records WHY.
  chase   the LQ cross-section is computed on the tracker engine store's own closes and volumes: UNIVERSE_CANON (universe_canon_v1.npz)
          is not on this desk. After the canon's last day (2026-09-30) the source's live cross-section also uses the engine's bars, and
          canon membership is taken from the frozen spec's SIC stock list.
  olx     the ids are olx_r12_other.ids (vendored with the frozen spec.json files; equal to the README rule table's 29 live-loadable
          rows, every one present in the vendored frozen strategy files); the README table is only the fallback when the file is absent.
  r2      the R2_ext1k training panel (canon_variants/R2_ext1k, pending the fetch) and live bars for the extension names are not on
          this desk, so the book is the lab_live 1D-cyan-covered search book on the tracker-universe panel.
  intraweek  the completed weeks are the tracker's Yahoo 1wk rows (g04a built every week from daily bars and kept 156 weeks; research:
          156 vs 260 weeks -> markers 100% agree), and the partial week comes from the tracker's closed daily bars.

A lane whose input is missing in a run (the tracker ledger; CHASE's engine daily store; the OLX or R2 lab output; the intraweek
detector output) keeps its fires of the previous file instead of losing them: carry_forward takes those whose fire day is inside the
5-session window and whose evidence is at most 80 h old (Lazarus' window and freshness rules), stamped with carried_from, and the
lane's status reads "input missing" with what is missing (FEED-03: the 10-19 08:50 run found no engine daily bars, reported CHASE
"ok" and erased its 9 fires 40 minutes before their only window). A lane whose input is present is recomputed as before.
usage: python galath_wait_feed.py --research <root>/inputs/lazarus --scratch <root>/cache/galath/scratch [--cache dir] [--now epoch]"""
import argparse
import glob
import gzip
import io
import json
import math
import os
import re
import sys
import time
import urllib.request

import numpy as np
import pandas as pd

VERSION = "wait_feed 1.2.0 (2026-10-26)"
TZ = "America/New_York"
OUT_REL = "shadow/paper_sleeve/live/wait_fires_v1.json"
SPEC_REL = "DESK_INTEGRATION/sleeve_specs"
LANES = ("s_wait_q14", "s_wait_flow", "s_wait_chase", "s_wait_olx_books", "s_wait_r2_dcyan", "s_wait_intraweek")
WINDOW_SESSIONS = 5                                  # Lazarus / sleeve_feed fire window
FEED_MAX_AGE_H = 80                                  # Lazarus' producer-file freshness (lazarus.FEED_MAX_AGE_HOURS)

Q14 = dict(px_cap=5.0, tier="A", sigs=("cyan", "green"), hold_weeks=78)
FLOW = dict(min_dv20=100_000.0, band="small", px_lo=5.0, px_hi=20.0, svr5_min=0.447678, stale_days=7, hold_sessions=60,
            svr_window=5, svr_min_periods=3)
CHASE = dict(rk_min=0.90, dd_min=-0.05, dd_window=63, dd_min_periods=40, hold_weeks=52, tail_rows=200)
INTRAWEEK = dict(markers=("buy-cyan", "buy-green"), hold_weeks=52)
R2 = dict(job="1D-cyan-covered", book="search")
SV_URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{:%Y%m%d}.txt"
UA = {"User-Agent": "master-desk galath wait_feed (public FINRA Reg SHO files)"}


# ------------------------------------------------------------------------------------------------------------- helpers
def ts_et(x):
    t = pd.Timestamp(x)
    return t.tz_convert(TZ) if t.tzinfo else t.tz_localize(TZ)


def day_of(fire_bar):
    return str(fire_bar)[:10]


def plan(max_bars, unit):
    return {"scheme": f"no stop / time exit {int(max_bars)} {unit}", "stop_pct": 99.0, "first_target_pct": None, "sell_fraction": 1.0,
            "rest": "time", "max_bars": int(max_bars), "exit_on_engine_sell": False}


def fire(lane, key, sym, fire_bar, close, unit, plan_, strategy, why, tags, **extra):
    return dict({"key": key, "sym": sym, "lane": lane, "fire_bar": str(fire_bar), "D": day_of(fire_bar), "close": close,
                 "tradeable": True, "cal_units": [unit], "cal_plans": {unit: plan_}, "strategy": strategy, "strategies": why,
                 "size_class": "test", "bar_source": "yahoo:canonical (wait_feed)", "feed": VERSION, "tags": tags}, **extra)


def window_start(today, is_td, n=WINDOW_SESSIONS):
    """the earliest of the last n trading sessions up to today (Lazarus oldest_fire_day)."""
    d, out = pd.Timestamp(today).normalize(), []
    while len(out) < n:
        if is_td(d):
            out.append(d)
        d -= pd.Timedelta(days=1)
    return str(out[-1].date())


def read_prev(path):
    """the previous output file (None: absent, unreadable or not a file of this composer)."""
    try:
        with open(path) as fh:
            o = json.load(fh)
    except (OSError, ValueError):
        return None
    return o if isinstance(o, dict) else None


def carry_forward(prev, lane, fires, since, until, now, max_age_h=FEED_MAX_AGE_H):
    """FEED-03: the fires of `lane` in the previous file that this run did not produce (`fires`), for a lane whose input is missing:
    those with a fire day inside the window [since, until] whose evidence, the generated time of the run that computed them
    (carried_from, else the previous file's generated), is at most max_age_h old at `now`. A previous file generated after `now`
    (a replay) or undated gives nothing. -> the kept fires, unchanged but for carried_from."""
    try:
        gen = ts_et(prev["generated"])
    except (TypeError, KeyError, ValueError):
        return []
    if pd.isna(gen) or gen > now:
        return []
    have, out = {x["key"] for x in fires}, []
    for x in prev.get("fires") or []:
        if x.get("lane") != lane or x.get("key") in have or not since <= str(x.get("D")) <= until:
            continue
        src = x.get("carried_from") or prev["generated"]
        try:
            age_h = (now - ts_et(src)).total_seconds() / 3600
        except (TypeError, ValueError):
            continue
        if 0 <= age_h <= max_age_h:
            out.append(dict(x, carried_from=src))
    return out


# ------------------------------------------------------------------------------------------------------------- ledger
TYPES = ('"type":"fire"', '"type":"ue_tag"', '"type":"lc2_tag"')


def read_ledger(path, since, lanes=("1w", "1d"), until="9999-12-31"):
    """tracker fires of `lanes` whose fire day is in [since, until], with their ue / lc2 tags: {fire key: dict(fire=, ue=, lc2=)}."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not any(t in line for t in TYPES):
                continue
            r = json.loads(line)
            if r["type"] == "fire":
                if r.get("lane") in lanes and since <= day_of(r.get("fire_bar")) <= until:
                    out[r["key"]] = dict(fire=r)
            else:
                k, _, kind = r.get("key", "").rpartition("|")
                if k in out:
                    out[k][kind] = r
    return out


def tag_values(x):
    for k in ("lc2", "ue"):
        v = (x.get(k) or {}).get("values") or {}
        if v.get("close_D") is not None or v.get("dv20") is not None:
            return v
    return {}


# ------------------------------------------------------------------------------------------------------------- q14
def q14(L):
    out, seen = [], []
    for k, x in sorted(L.items()):
        f = x["fire"]
        sym, lane, sig = k.split(":")[:3]
        if lane != "1w" or sig not in Q14["sigs"]:
            continue
        ue = x.get("ue") or {}
        v = ue.get("values") or {}
        c = v.get("close_D") if v.get("close_D") is not None else f.get("close")
        row = dict(key=k, tier=ue.get("tier"), close_D=c)
        seen.append(row)
        if ue.get("tier") != Q14["tier"] or c is None or float(c) > Q14["px_cap"]:
            continue
        out.append(fire("s_wait_q14", f"{k}|s_wait_q14", sym, f["fire_bar"], float(c), "wait-q14-W78", plan(Q14["hold_weeks"], "weeks"),
                        "Q14 cheap-stock book (test)", [f"1W {sig} tier A, close_D {float(c):.2f} <= 5.00"],
                        dict(tier=ue.get("tier"), close_D=float(c), ue_lane=ue.get("ue_lane")), limit_cap=Q14["px_cap"]))
    return out, seen


# ------------------------------------------------------------------------------------------------------------- flow
def svr5_table(files):
    """{date: {sym: svr}} -> function (sym, D) -> (svr5, sv_date): the finra_flow producer's rule on the files at hand: svr = short / total
    per file row; svr5 = the mean of the symbol's 5 newest rows <= D (min 3); sv_date = the date of its newest row <= D (None: no row)."""
    days = sorted(files)

    def fn(sym, D):
        vals, sv_date = [], None
        for d in reversed([d for d in days if d <= pd.Timestamp(D)]):
            s = files[d].get(sym)
            if s is None or not np.isfinite(s):
                continue
            sv_date = sv_date or d
            vals.append(float(s))
            if len(vals) == FLOW["svr_window"]:
                break
        if len(vals) < FLOW["svr_min_periods"]:
            return None, sv_date
        return float(np.mean(vals)), sv_date
    return fn


def norm(sym):
    """the finra_flow producer's ticker rule (ALTDATA_LIVE/plugins/feedlib.norm): FINRA BRK.B -> BRK-B."""
    return str(sym).strip().upper().replace(".", "-").replace("/", "-")


def parse_cnms(text):
    """one CNMS file -> {ticker: svr}; short / total volume as float32, as the producer stores them."""
    x = pd.read_csv(io.StringIO(text), sep="|", dtype={"Date": str, "Symbol": str})
    x = x[x.Date.str.fullmatch(r"\d{8}", na=False)]
    x = x.assign(sym=x.Symbol.map(norm)).groupby("sym")[["ShortVolume", "TotalVolume"]].sum()
    s, t = x.ShortVolume.astype("float32"), x.TotalVolume.astype("float32")
    ok = t > 0
    return (s[ok] / t[ok]).astype(float).to_dict()


def flow(L, band_fn, svr5_fn):
    out, seen = [], []
    for k, x in sorted(L.items()):
        f = x["fire"]
        sym, lane, sig = k.split(":")[:3]
        if lane != "1d" or sig != "green":
            continue
        v = tag_values(x)
        D = day_of(f["fire_bar"])
        c = v.get("close_D") if v.get("close_D") is not None else f.get("close")
        dv = v.get("dv20")
        row = dict(key=k, close_D=c, dv20=dv)
        seen.append(row)
        if c is None or dv is None or float(dv) < FLOW["min_dv20"] or not (FLOW["px_lo"] <= float(c) < FLOW["px_hi"]):
            continue
        b = band_fn(sym, D, float(c))
        row["band"] = b
        if b != FLOW["band"]:
            continue
        s5, sv_date = svr5_fn(sym, D)
        row.update(svr5=s5, sv_date=None if sv_date is None else str(pd.Timestamp(sv_date).date()))
        if sv_date is None or (pd.Timestamp(D) - pd.Timestamp(sv_date)).days > FLOW["stale_days"]:
            row["stale"] = True
            continue
        if s5 is None or s5 < FLOW["svr5_min"]:
            continue
        out.append(fire("s_wait_flow", f"{k}|s_wait_flow", sym, f["fire_bar"], float(c), "wait-flow-D60", plan(FLOW["hold_sessions"], "sessions"),
                        "FLOW short-volume cell (test)", [f"1D green small ${float(c):.2f} svr5 {s5:.3f} >= {FLOW['svr5_min']}"],
                        dict(close_D=float(c), dv20=float(dv), band=b, svr5=round(s5, 6), sv_date=row["sv_date"])))
    return out, seen


# ------------------------------------------------------------------------------------------------------------- chase
def _tail_csv(p, n):
    """paper_families._tail_csv: the last n closed bars (timestamp, close, volume) of an engine store csv."""
    with open(p, "rb") as fh:
        head = fh.readline()
        fh.seek(0, 2)
        sz = fh.tell()
        blk = 2048 * (n + 2)
        while True:
            b = min(sz, blk)
            fh.seek(sz - b)
            raw = fh.read().splitlines()
            if b >= sz or len(raw) > n + 1:
                break
            blk *= 2
    rows = raw[1:]
    rows = rows[-n:] if len(rows) > n else rows
    cols = head.decode().strip().split(",")
    ix = [cols.index(c) for c in ("timestamp", "close", "volume", "barFinality")]
    out = []
    for r in rows:
        x = r.decode(errors="replace").split(",")
        if len(x) <= max(ix) or x[ix[3]] != "closed":
            continue
        try:
            out.append((int(float(x[ix[0]])), float(x[ix[1]]), float(x[ix[2]] or 0)))
        except ValueError:
            continue
    return out


def engine_panel(eng_1d, n):
    """closes / volumes of every engine store name (paper_families build_xs: the engine part, stray non-session rows dropped)."""
    Cd, Vd = {}, {}
    for p in sorted(glob.glob(os.path.join(eng_1d, "*.csv"))):
        rows = _tail_csv(p, n)
        if not rows:
            continue
        d = pd.to_datetime([r[0] for r in rows], unit="s", utc=True).tz_convert(TZ).tz_localize(None).normalize()
        s = os.path.basename(p)[:-4]
        c, v = pd.Series([r[1] for r in rows], index=d), pd.Series([r[2] for r in rows], index=d)
        Cd[s], Vd[s] = c[~c.index.duplicated(keep="last")], v[~v.index.duplicated(keep="last")]
    if not Cd:
        return None, None
    C = pd.DataFrame(Cd).sort_index()
    cov = C.notna().sum(axis=1)
    C = C[cov >= 0.5 * cov.median()]
    return C, pd.DataFrame(Vd).reindex(C.index)


def chase_xs(C, V, spec):
    """mom126 rank vs LQ per session and the 63-session drawdown, on the engine panel (paper_families rk_lq; chase_live_week dd63)."""
    P, U = spec["families"]["mom126_top10"]["params"], spec["universe"]
    sic = set(U["sic_stock_syms"]) | set(U["keep_nosic"])
    stock_mc = np.array([(s in sic) and (s not in set(U["mc_etfs"])) for s in C.columns])
    Cf = C.ffill(limit=P["ffill_limit"])
    dv20 = (C * V).rolling(20, min_periods=20).mean()
    mc = pd.DataFrame(np.repeat(stock_mc[None, :], len(C), 0), index=C.index, columns=C.columns)
    LQ = C.notna() & (dv20 >= P["uc_min_dv20"]) & mc & (C.fillna(0) >= P["lq_min_close"]) & (dv20.fillna(0) >= P["lq_min_dv20"])
    mom = Cf / Cf.shift(P["L"]) - 1

    def rank(t):
        v = mom.loc[t].values.astype(float)
        a = LQ.loc[t].values & np.isfinite(v)
        if a.sum() < P["min_lq"]:
            return None, int(a.sum())
        srt = np.sort(v[a])
        r = np.full(len(v), np.nan)
        f = np.isfinite(v)
        r[f] = np.searchsorted(srt, v[f], side="right") / len(srt)
        return pd.Series(r, index=C.columns), int(a.sum())

    def dd63(sym, t):
        if sym not in C.columns:
            return None
        c = C[sym].loc[:t].dropna()
        c = c[~c.index.duplicated(keep="last")].ffill(limit=5)
        if len(c) < CHASE["dd_min_periods"]:
            return None
        return float(c.iloc[-1] / c.iloc[-CHASE["dd_window"]:].max() - 1)
    return rank, dd63, float(1 - P["q"])


def chase(L, C, V, spec):
    out, seen = [], []
    if C is None:
        return out, [dict(note="no engine daily bars")]
    rank, dd63, rk_min = chase_xs(C, V, spec)
    memo = {}
    for k, x in sorted(L.items()):
        f = x["fire"]
        sym, lane, sig = k.split(":")[:3]
        if lane != "1w" or sig != "cyan":
            continue
        fri = pd.Timestamp(day_of(f["fire_bar"]))
        ix = C.index[C.index <= fri]
        if not len(ix):
            continue
        t = ix[-1]
        if t not in memo:
            memo[t] = rank(t)
        rk, n_lq = memo[t]
        r = None if rk is None or sym not in rk.index or not np.isfinite(rk[sym]) else float(rk[sym])
        d = dd63(sym, t)
        row = dict(key=k, t=str(t.date()), rk126=r, dd63=d, n_lq=n_lq)
        seen.append(row)
        if r is None or d is None or r < rk_min or not d > CHASE["dd_min"]:
            continue
        out.append(fire("s_wait_chase", f"{k}|s_wait_chase", sym, f["fire_bar"], f.get("close"), "wait-chase-W52", plan(CHASE["hold_weeks"], "weeks"),
                        "CHASE momentum leader at its 63-day high (test)", [f"1W cyan rk126 {r:.3f} >= {rk_min:.2f}, dd63 {d:+.3f} > -0.05"],
                        dict(rk126=round(r, 4), dd63=round(d, 4), session=str(t.date()), n_lq=n_lq)))
    return out, seen


# ------------------------------------------------------------------------------------------------------------- lab books (olx, r2)
OLX_ROW = re.compile(r"^\| ((?:V\d|TNS)-[A-Za-z0-9-]+) \| (1[DW]) (\w+) \| (\d+) \| ([R12+]+) \| ([\d,]+) \| (True|False) \| (True|False) \|$", re.M)


def olx_rules_from_readme(text):
    """the README's rule table: [(id, lane, signal, hold, clean_in, live_loadable)]."""
    return [(m[0], m[1], m[2], int(m[3]), m[4], m[7] == "True") for m in OLX_ROW.findall(text)]


def olx_ids_from_readme(text):
    """the ids the README flags live-loadable (= its olx_r12_other.ids: 29 of the 30 rules)."""
    return [r[0] for r in olx_rules_from_readme(text) if r[5]]


def lab_fires(lane, books, since, select, hold, strategy, until="9999-12-31"):
    """lab_live job outputs -> fires (the s_rules / lab-book routing of sleeve_feed 1.0.4 Feed.lab, one lane)."""
    out = {}
    for name, J in sorted(books.items()):
        job = f"{J['lane']}-{J['signal']}-{J['universe']}"
        for x in J.get("fires") or []:
            if not since <= x["day"] <= until:
                continue
            for tag, H, why in select(job, J, x):
                k = f"{x['sym']}:{lane}:x:{x['day']}{tag}"
                if k in out:
                    out[k]["strategies"] = sorted(set(out[k]["strategies"]) | set(why))
                    continue
                out[k] = fire(lane, k, x["sym"], f"{x['day']} 09:30:00-04:00", None, f"{lane}-H{H}", plan(hold(H), "sessions"), strategy, why,
                              dict(job=job, asof=J.get("asof"), panel_last_day=J.get("panel_last_day")))
    return list(out.values())


def olx(books, since, until="9999-12-31"):
    def select(job, J, x):
        FH = {r["id"]: r.get("horizon") for r in J.get("frozen_rules") or []}
        return [(f":H{int(FH.get(rid) or 0)}", int(FH.get(rid) or 0), [f"olx rule {rid} ({job})"]) for rid in x.get("frozen") or [] if FH.get(rid)]
    return lab_fires("s_wait_olx_books", books, since, select, lambda H: H + 1, "OLX R1/R2 lab rule (test)", until)


def r2_dcyan(books, since, until="9999-12-31"):
    def select(job, J, x):
        if job != R2["job"] or not x.get(R2["book"]):
            return []
        H = int(J.get("hold_sessions") or 21)
        return [("", H, [f"lab {job} rule search (R2 Daily Cyan book, tracker universe)"])]
    return lab_fires("s_wait_r2_dcyan", books, since, select, lambda H: H, "R2 Daily Cyan covered search book (test)", until)


def read_books(d):
    out = {}
    for p in sorted(glob.glob(os.path.join(d, "*.json"))):
        try:
            out[os.path.basename(p)[:-5]] = json.load(open(p))
        except (OSError, ValueError):
            continue
    return out


# ------------------------------------------------------------------------------------------------------------- intraweek
def intraweek(rows, state, is_td):
    """detector rows (galath_intraweek.mjs) of days k = 1..4 (never the week's last session) -> state {monday: {sym: first}}, which keeps
    the first day k of each symbol-week; -> one fire per symbol-week, keyed and dated by that first day (a later vanish or re-show does
    not move it)."""
    for x in rows:
        mk = [m for m in x.get("markers") or [] if m in INTRAWEEK["markers"]]
        sess = pd.Timestamp(x["session"])
        nxt = sess + pd.Timedelta(days=1)
        while not is_td(nxt):
            nxt += pd.Timedelta(days=1)
        if not mk or sess.dayofweek > 3 or nxt.to_period("W-SUN") != sess.to_period("W-SUN"):
            continue
        state.setdefault(x["monday"], {}).setdefault(x["sym"], dict(session=x["session"], k=int(sess.dayofweek + 1), markers=mk,
                                                                    close=float(x["close"])))
    out = []
    for monday, wk in sorted(state.items()):
        fri = pd.Timestamp(monday) + pd.Timedelta(days=4)
        for sym, first in sorted(wk.items()):
            out.append(fire("s_wait_intraweek", f"{sym}:s_wait_intraweek:{monday}", sym, f"{first['session']} 09:30:00-04:00", first["close"],
                            "wait-intraweek-W52", plan(INTRAWEEK["hold_weeks"] + 1, "weeks"), "Intraweek early entry (test)",
                            [f"provisional 1W {first['markers'][0][4:]} on day k={first['k']} of the week of {monday}"],
                            dict(k=first["k"], markers=first["markers"], monday=monday, fire_friday=str(fri.date()))))
    return out


# ------------------------------------------------------------------------------------------------------------- main
def _fetch(url, tries=2):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                b = r.read()
                return gzip.decompress(b).decode() if r.headers.get("Content-Encoding") == "gzip" else b.decode()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            if i == tries - 1:
                raise
        time.sleep(2)
    return None


def finra_files(cache, sessions, notes, fetch=True):
    """CNMS daily files for `sessions` (cached text, <= 1 request/s); fetch False: the cached files only, never a request."""
    os.makedirs(cache, exist_ok=True)
    files = {}
    for d in sessions:
        p = os.path.join(cache, f"CNMSshvol{d:%Y%m%d}.txt.gz")
        if not os.path.exists(p):
            if not fetch:
                continue
            try:
                t = _fetch(SV_URL.format(d))
            except Exception as e:                       # network trouble: that file is missing (fail closed on staleness)
                notes.append(f"FINRA {d.date()}: {str(e)[:80]}")
                t = None
            time.sleep(1.0)
            if not t or not t.startswith("Date|"):
                notes.append(f"FINRA CNMS {d.date()} not published / unavailable")
                continue
            with gzip.open(p + ".tmp", "wt") as fh:
                fh.write(t)
            os.replace(p + ".tmp", p)
        with gzip.open(p, "rt") as fh:
            files[d] = parse_cnms(fh.read())
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--research", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--now", type=float, default=None)
    ap.add_argument("--intraweek", default=None, help="detector output (galath_intraweek.mjs jsonl) of this run")
    ap.add_argument("--no-finra-fetch", default=None, metavar="WHY",
                    help="request no FINRA CDN file (the owner's OFF switch on the alt-data sources); WHY is recorded")
    a = ap.parse_args(argv)
    R, S = a.research, a.scratch
    cache = a.cache or os.path.join(os.path.dirname(S), "wait")
    sys.path.insert(0, os.path.join(R, "shadow"))
    import addons_sources_st as X                      # the research calendar (run_lab_live.sh uses it)
    now = pd.Timestamp(a.now, unit="s", tz="UTC").tz_convert(TZ) if a.now else pd.Timestamp.now(tz=TZ)
    today = now.normalize().tz_localize(None)
    since = window_start(today, X.is_trading_day)
    lanes = {ln: dict(status="ok", n=0, notes=[], divergences=[]) for ln in LANES}
    missing = {}                                      # lane -> the input this run lacks (its fires are carried forward)
    fires = []
    t0 = time.time()
    led = os.path.join(R, "shadow", "log", "ledger.jsonl")
    until = str(today.date())                         # a replay (--now in the past) never reads a later record
    L = read_ledger(led, since, until=until) if os.path.exists(led) else {}
    if not os.path.exists(led):
        for ln in ("s_wait_q14", "s_wait_flow", "s_wait_chase"):
            missing[ln] = f"missing {led}"
    # q14
    f, seen = q14(L)
    fires += f
    lanes["s_wait_q14"].update(n=len(f), evaluated=len(seen), sample=seen[:20])
    # flow
    sys.path.insert(0, os.path.join(R, "shadow", "paper_sleeve"))
    band_note = []
    try:
        import addons_sc as SC
        import sleeve_band as SB

        def band_fn(sym, D, c):
            try:
                return SB.band(sym, D, c, SC, str(today.date()))["band"]
            except Exception as e:                       # the source's own fail-closed rule: no band -> no fire
                band_note.append(f"band {sym}: {str(e)[:60]}")
                return "unknown"
    except Exception as e:
        band_note.append(f"sleeve_band / addons_sc import failed: {str(e)[:100]} -> band unknown (fail closed)")

        def band_fn(sym, D, c):
            return "unknown"
    svr_src, svr_notes = None, []
    hist = os.path.join(R, "ALTDATA_LIVE", "out", "finra_svr_history.parquet")
    cand = [x for x in L.values() if x["fire"].get("lane") == "1d" and ":1d:green:" in x["fire"]["key"]]
    days_needed = sorted({day_of(x["fire"]["fire_bar"]) for x in cand})
    svr5_fn = None
    if os.path.exists(hist):
        try:
            H = pd.read_parquet(hist, columns=["sv_date", "ticker", "svr5"])
            H["sv_date"] = pd.to_datetime(H.sv_date)
            if days_needed and H.sv_date.max() >= pd.Timestamp(days_needed[0]) - pd.Timedelta(days=FLOW["stale_days"]):
                by = {s: g.sort_values("sv_date") for s, g in H.groupby("ticker")}

                def svr5_fn(sym, D):
                    g = by.get(sym)
                    if g is None:
                        return None, None
                    g = g[g.sv_date <= pd.Timestamp(D)]
                    return (None, None) if not len(g) else (float(g.svr5.iloc[-1]) if np.isfinite(g.svr5.iloc[-1]) else None, g.sv_date.iloc[-1])
                svr_src = "ALTDATA_LIVE out/finra_svr_history.parquet"
        except Exception as e:
            svr_notes.append(f"finra_svr_history unreadable: {str(e)[:80]}")
    if svr5_fn is None:
        if days_needed:
            lo = pd.Timestamp(days_needed[0]) - pd.Timedelta(days=30)        # ~20 files: 5 rows for all but the sparsest names
            sess = [d for d in pd.bdate_range(lo, today) if X.is_trading_day(d)]
            off = a.no_finra_fetch                    # FEED-04a: the owner's OFF switch on the alt-data sources holds here too
            if off:
                svr_notes.insert(0, f"FINRA CNMS files not fetched: {off}")
            files = finra_files(os.path.join(cache, "finra_cnms"), sess, svr_notes, fetch=not off)
            svr5_fn = svr5_table(files)
            svr_src = (f"FINRA CNMS daily files ({len(files)} of {len(sess)} sessions {sess[0].date()}..{sess[-1].date()}"
                       + (", cached only: fetch off)" if off else ")"))
            if not files:
                missing.setdefault("s_wait_flow", "no svr5 data: finra_svr_history.parquet does not cover the window and no FINRA "
                                                  "CNMS file is at hand" + (" (fetch off)" if off else ""))
        else:
            def svr5_fn(sym, D):
                return None, None
            svr_src = "not needed (no 1D Green fire in the window)"
        lanes["s_wait_flow"]["divergences"].append("svr5 from FINRA's public CNMS daily files (ALTDATA_LIVE finra_svr_history.parquet absent)")
    f, seen = flow(L, band_fn, svr5_fn)
    fires += f
    lanes["s_wait_flow"].update(n=len(f), evaluated=len(seen), sample=seen[:20], svr5_source=svr_src, notes=(svr_notes + band_note)[:12])
    # chase
    spec_p = os.path.join(R, "shadow", "paper_desk", "paper_families_v1_frozen.json")
    spec = json.load(open(spec_p))
    eng_1d = os.path.join(S, "shadow", "engine", "1d")
    C, V = engine_panel(eng_1d, CHASE["tail_rows"])
    if C is None:
        missing.setdefault("s_wait_chase", f"no engine daily bars under {eng_1d}")
    f, seen = chase(L, C, V, spec)
    fires += f
    lanes["s_wait_chase"].update(n=len(f), evaluated=len(seen), sample=seen[:20], engine_names=0 if C is None else int(C.shape[1]),
                                 divergences=["LQ cross-section on the tracker engine store (UNIVERSE_CANON npz not on this desk)"])
    # olx
    olx_dir = os.path.join(R, "DESK_INTEGRATION", "lab_live", "out", "olx")
    ob = read_books(olx_dir)
    f = olx(ob, since, until)
    fires += f
    lanes["s_wait_olx_books"].update(n=len(f), jobs={k: dict(asof=v.get("asof"), frozen=len(v.get("frozen_rules") or []), fires=len(v.get("fires") or []))
                                                     for k, v in ob.items()})
    if not ob:
        missing["s_wait_olx_books"] = f"no OLX lab output yet under {olx_dir}"
    # r2
    lb_dir = os.path.join(R, "DESK_INTEGRATION", "lab_live", "out", "latest")
    lb = read_books(lb_dir)
    f = r2_dcyan(lb, since, until)
    fires += f
    lanes["s_wait_r2_dcyan"].update(n=len(f),
                                    divergences=["R2_ext1k panel not on this desk: the lab_live 1D-cyan-covered search book on the tracker universe"])
    if R2["job"] not in lb:
        missing["s_wait_r2_dcyan"] = f"no {R2['job']} lab output under {lb_dir}"
    # intraweek
    st_p = os.path.join(cache, "intraweek_first.json")
    try:
        state = json.load(open(st_p))
    except (OSError, ValueError):
        state = {}
    det = a.intraweek or (sorted(glob.glob(os.path.join(cache, "intraweek_*.jsonl"))) or [None])[-1]
    rows = [json.loads(x) for x in open(det) if x.strip()] if det and os.path.exists(det) else []
    f = [x for x in intraweek([r for r in rows if r["session"] <= until], state, X.is_trading_day) if since <= x["D"] <= until]
    state = {k: state[k] for k in sorted(state)[-3:]}
    os.makedirs(cache, exist_ok=True)
    with open(st_p + ".tmp", "w") as fh:
        json.dump(state, fh)
    os.replace(st_p + ".tmp", st_p)
    fires += f
    lanes["s_wait_intraweek"].update(n=len(f), detector=det, detector_rows=len(rows), provisional_today=sum(1 for x in rows if x.get("markers")))
    if not rows:
        missing["s_wait_intraweek"] = "no detector output"
    # FEED-03: a lane whose input is missing keeps its in-window, fresh fires of the previous file and says so
    out = os.path.join(R, OUT_REL)
    prev = read_prev(out) if missing else None
    for ln, why in missing.items():
        kept = carry_forward(prev, ln, [x for x in fires if x["lane"] == ln], since, until, now)
        fires += kept
        note = (f"kept {len(kept)} in-window fires of the previous file (generated {prev.get('generated')})" if prev is not None
                else "no previous file to keep fires from")
        lanes[ln].update(status="input missing", missing=why, carried=len(kept), n=lanes[ln]["n"] + len(kept),
                         notes=[why, note] + lanes[ln]["notes"])
    doc = {"version": "wait_fires v1", "feed": VERSION, "generated": str(pd.Timestamp.now(tz=TZ)), "asof": str(now), "oldest_fire_day": since,
           "lanes": lanes, "fires": fires, "counts": {ln: sum(1 for x in fires if x["lane"] == ln) for ln in LANES},
           "secs": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out + ".tmp", "w") as fh:
        json.dump(doc, fh, indent=1, default=str)
    os.replace(out + ".tmp", out)
    print(json.dumps(dict(out=out, fires=len(fires), counts=doc["counts"], oldest_fire_day=since, secs=doc["secs"],
                          status={k: v["status"] for k, v in lanes.items()},
                          carried={k: v["carried"] for k, v in lanes.items() if "carried" in v}), default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
