"""Milkman intraday study — v3-native port (MILKMAN-0DTE-PORT-20261116).

Provenance: a logic-identical port of Femto-lean
desk/sleeves/milkman/intraday.py at branch milkman-0dte, commit
8c64cd5cc53a (blob d6339131541cc460b7650d468d99cd691606f6f8, sha256
77034c9fc88edea81fa304e2bd7cbe13b952b739a4b8fd9accf1c873b7785362),
vendored byte-exact beside this module as intraday.py. That module
is itself the study port of milkman-study/v2 21_intraday.py /
22_intraday2.py (quant-research-critical@0be4c57569e363d052bd2356
4cf0664697439927, blobs 9ea632d0 / 410af17e, engine ilib.py@47753cf8;
SOURCE below is the source's own pin, kept verbatim). Its parity
receipt (Femto-lean docs/receipts/parity/milkman_intraday.json,
sha256 ee0eed2759350cd030a2d1bb7b399da57fbcbfc87a12c81922211a47
cc2c8fd6): 1,778 cases identical, 26,854 lane trades, live replay
417 entries / 342 exits matched, 0 mismatches.

What this port changes, and nothing else:
  * the framework surface is dropped: the femto Sleeve class, its
    feed_spy Yahoo feed and sleeves() registry have no v3
    counterpart and are not ported; detection (Panel, detect21,
    detect10, detect_cdc, the LEMA / MDL / PMATH / GUPN engines,
    step_exit / run_exit, lane_trades) is the source's code,
    line for line apart from the dependency shims below.
  * M() returns the study's own mlib, vendored byte-exact beside
    this module as mlib.py (blob 0e488ae7ad34c37197b7141afb3ba5d1
    483892f6, sha256 0c6823c0c1a55ca8520f5121c8660ff46170813a67fb
    24a2c5e51adb16a536b9), instead of the femto vendored loader.
  * the calendar is a shim over v3's canonical calendar
    (core.data.is_trading_day + core.early_close.session_close_dt)
    with the source's own _as_date / next_trading_day /
    trading_days_between arithmetic kept; the holiday table is
    therefore v3's, not femto's (femto also closes Good Friday and
    named special closures; v3's table does not — the difference
    can only move full_day() on those named days).
  * the panel is built by adapters/milkman_0dte.py from the v3
    snapshot's SPY bars (Alpaca SIP 1Min, 18 days; 1Hour, 200 days;
    1Day, 500 days) instead of the source's Yahoo tapes. This is
    the source's named divergences 3/4 in v3 dress: daily history
    is the desk's daily bars, history depth is the warm windows
    above, and the indicators run on those depths.

Named data-depth limitation (LEMA): lema_threshold() reads the
train-period (2000-2012) body/range quantile from the panel's
daily table. The v3 snapshot's daily history (500 days) contains
no 2000-2012 sessions, so the threshold is None and the LEMA lane
produces no signals on the live snapshot — exactly the source's
own fail-closed behaviour when the train years are absent. The
rule itself is ported and proven on train-era fixtures in the
blocker tests; the lane stays dark until a daily source carrying
2000-2012 SPY sessions is served to the panel. Every other lane
runs on the served depths.

ESMON and OPX4 stay excluded from mk_zerodte_spx by the authored
sleeve (sleeves/milkman_0dte.py EXCLUDED); their detection helpers
(esmon_window, opx4_rows) are ported with the rest, but
lane_trades has no ESMON/OPX4 lane in the source either (the femto
sleeve handled them outside lane_trades), and the 0dte wiring in
adapters/milkman_0dte.py never asks for them.
"""
import math
from datetime import date, datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from . import mlib as _mlib

_ET = ZoneInfo("America/New_York")


# --------------------------------------------------------------- calendar shim
class _Cal:
    """The source's desk.calendar surface, over v3's canonical
    calendar (see the module docstring for the one named
    difference: the holiday table)."""

    @staticmethod
    def _as_date(d):
        if isinstance(d, datetime):
            return (d.astimezone(_ET) if d.tzinfo else d).date()
        if isinstance(d, (int, float)):
            return datetime.fromtimestamp(float(d), tz=_ET).date()
        if isinstance(d, str):
            return date.fromisoformat(d[:10])
        return d

    @staticmethod
    def is_trading_day(d):
        from core.data import is_trading_day
        return is_trading_day(_Cal._as_date(d))

    @staticmethod
    def close_minutes(d):
        from core.early_close import session_close_dt
        close = session_close_dt(_Cal._as_date(d).isoformat())
        return close.hour * 60 + close.minute

    @staticmethod
    def session_close(d):
        from core.early_close import session_close_dt
        return session_close_dt(_Cal._as_date(d).isoformat()).timestamp()

    @staticmethod
    def next_trading_day(d, k=1):
        d = _Cal._as_date(d)
        while k > 0:
            d += timedelta(days=1)
            if _Cal.is_trading_day(d):
                k -= 1
        return d

    @staticmethod
    def trading_days_between(a, b):
        a, b = _Cal._as_date(a), _Cal._as_date(b)
        n, d = 0, a
        while d < b:
            d += timedelta(days=1)
            if _Cal.is_trading_day(d):
                n += 1
        return n


cal = _Cal()

SOURCE = {"repo": "quant-research-critical", "ref": "main", "commit": "0be4c57569e363d052bd23564cf0664697439927",
          "path": "milkman-study/v2/code/21_intraday.py", "blob": "9ea632d0b65cebcd7f4bbd4adcf4537c1b5c2a3c",
          "path2": "milkman-study/v2/code/22_intraday2.py", "blob2": "410af17efea5b359fb4197ae3bad5903bc152ae5",
          "engine": "milkman-study/v2/code/ilib.py@47753cf8", "cells": "milkman-study/v2/out/tab_primary.md"}
NOTIONAL = 10_000.0
CAPITAL = 1_000_000.0
SYM = "SPY"
INST = "EQ:SPY"
COST = 0.015                    # the study's % per side (its reported returns; parity only)
LIVE_LAST = 10 ** 9             # a live session's last bar is not known yet: its close is the MOC exit
LATE = 2                        # bars a new trade may be seen after its deciding bar and still enter
TZ = "America/New_York"
LV = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.236]

# setup -> (sleeve_id, [(side, designated cell)])  — out/tab_primary.md
SETUPS = {
    "CASCADE": ("mk_atrlevelcascade", [(1, "window=all"), (-1, "window=all")]),
    "BGG": ("mk_bilbogoldengate", [(1, "cohort=live;filter=zone_rising"), (-1, "cohort=live;filter=zone_rising")]),
    "C2P": ("mk_calltoputputtocallreversal", [(1, "target=0.382"), (-1, "target=0.382")]),
    "DGG": ("mk_daygoldengate", [(1, "cohort=live;filter=none"), (-1, "cohort=live;filter=none")]),
    "TBOX": ("mk_directionaltriggerbox", [(1, "target=0.382"), (-1, "target=0.382")]),
    "GAP": ("mk_gapfademomentummirror", [(1, "bucket=0.0-0.1;stopATR=0.5;target=full"),
                                         (-1, "bucket=0.25-0.5;stopATR=0.5;target=full")]),
    "ORB": ("mk_openingrangebreakout", [(1, "or=5;filter=ribbon_vwap;stop=mid"), (-1, "or=10;filter=none;stop=mid")]),
    "COMP10": ("mk_tenminutecompressionrelease", [(1, "minbars=3;exit=eod"), (-1, "minbars=18;exit=eod")]),
    "CDC": ("mk_threeminutecompressiondrift", [(1, "atrgate=0.00045"), (-1, "atrgate=0.00045")]),
    "CT3": ("mk_threeminutetriggerconfirmation", [(1, "target=0.382"), (-1, "target=0.382")]),
    "VOMY": ("mk_vomyivomy", [(1, "flipwithin=3"), (-1, "flipwithin=3")]),
    "LEMA": ("mk_legendsemaintradayproxy", [(1, "ema=20;q=0.8"), (-1, "ema=20;q=0.8")]),
    "MDL": ("mk_morningdiplimitproxy", [(1, "er=0.35;k=1.0"), (-1, "er=0.35;k=1.0")]),
    "ESMON": ("mk_esmondayclockonspyproxy", [(1, "dow=0;entry=6;exit=16"), (-1, "dow=0;entry=6;exit=16")]),
    "PMATH": ("mk_premarketathmorningfade", [(-1, "filter=kill;exit=12:00;stopATR=0.0")]),
    "OPX4": ("mk_fourhourpoopexrollover", [(-1, "ext=0.618;H=10")]),
    "GUPN": ("mk_gapupprenooncontinuation", [(1, "X=1.0")]),
}
# One book per side, by the owner's split of 2026-10-19 (desk/sleeves/milkman/daily.py SPLIT: a rule whose long and
# short lanes net in one book runs one sleeve per side, as the study tested them). VOMY's lanes netted on 2026-10-20:
# two long trades held to the close while three short trades opened (roll call 2026-10-26). The long side keeps the
# id, the short side runs as <id>_short, each on the full virtual book; desk/migrations moved the short lane's record.
SPLIT = ("VOMY",)
SET21 = {"DGG", "BGG", "CT3", "TBOX", "C2P", "GAP", "ORB", "CASCADE"}
SET10 = {"VOMY", "COMP10"}


def M():
    return _mlib


def full_day(d):
    return cal.is_trading_day(d) and cal.close_minutes(d) == 16 * 60


def parse_cell(text):
    out = {}
    for kv in text.split(";"):
        k, v = kv.split("=")
        try:
            out[k] = float(v) if any(ch in v for ch in ".e") else int(v)
        except ValueError:
            out[k] = v
    return out


COLS = ["timestamp", "open", "high", "low", "close", "volume"]
STEP = {"3min": 3, "10min": 10, "1h": 60, "4h": 240}


def _empty():
    return pd.DataFrame({"timestamp": np.array([], dtype="datetime64[ns]"),
                         **{c: np.array([], dtype=float) for c in COLS[1:]}})


def _frame(bars):
    """bar dicts (epoch t) -> the vault's frame: naive ET timestamps, sorted, one row per stamp (the last)."""
    rows = [(b["t"], b["o"], b["h"], b["l"], b["c"], b.get("v") or 0.0) for b in (bars or ())
            if None not in (b.get("o"), b.get("h"), b.get("l"), b.get("c"))]
    if not rows:
        return _empty()
    a = np.array(rows, dtype=float)
    a = a[np.argsort(a[:, 0], kind="stable")]
    a = a[np.r_[a[1:, 0] != a[:-1, 0], True]]
    ts = pd.to_datetime(a[:, 0].astype(np.int64), unit="s", utc=True).tz_convert(TZ).tz_localize(None)
    return pd.DataFrame({"timestamp": ts.values.astype("datetime64[ns]"), "open": a[:, 1], "high": a[:, 2],
                         "low": a[:, 3], "close": a[:, 4], "volume": a[:, 5]})


def dnum(v):
    """day numbers of datetime values (any resolution): exact dictionary / comparison keys."""
    return np.asarray(v).astype("datetime64[D]").astype(np.int64)


def _agg(x, rule):
    """resample a sorted 1m / 1h frame into bins from midnight (pandas resample: first / max / min / last / sum,
    empty bins dropped)."""
    if not len(x):
        return _empty()
    step = STEP[rule]
    tm = x.timestamp.values.astype("datetime64[m]").astype(np.int64)
    key = (tm // step) * step
    st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    en = np.r_[st[1:], len(key)] - 1
    return pd.DataFrame({"timestamp": key[st].astype("datetime64[m]").astype("datetime64[ns]"),
                         "open": x.open.values[st], "high": np.maximum.reduceat(x.high.values, st),
                         "low": np.minimum.reduceat(x.low.values, st), "close": x.close.values[en],
                         "volume": np.add.reduceat(x.volume.values, st)})


# --------------------------------------------------------------------------------------------- the panel
class Panel:
    """the study's objects over the bars available now (ilib.build_panel and the vault candles): RTH 1m arrays
    (o h l c mod ts vol di), the day table (start / end bar, prior close, prior ATR14), the full-session daily table,
    and the 3m / 10m / 1h / 4h candles with their indicators. `today` names a session still forming (live): its RTH
    bars so far form its panel day whatever their count."""

    def __init__(self, m1, d1=None, h1=None, today=None):
        self.today = today
        self.cache = {}
        m = _frame(m1)
        self.M = m[m.timestamp.dt.hour < 20].reset_index(drop=True)
        self._rth()
        self._daily(d1)
        self.I3 = self._htf("3min")
        self.I10 = self._htf("10min")
        self.H = self._hours(h1)
        self.I1h = self._ind(self.H) if len(self.H) else None
        F = self._four(self.H)
        self.I4 = self._ind(F) if len(F) else None

    def _rth(self):
        """ilib.build_panel: RTH bars (09:30-15:59), days with >= 300 of them (and the live day)."""
        m = self.M
        tm = m.timestamp.values.astype("datetime64[m]").astype(np.int64)
        mod_all = tm % 1440
        idx = np.flatnonzero((mod_all >= 570) & (mod_all < 960))
        dn = tm[idx] // 1440
        O, Hh, Ll, Cc = (m[k].values[idx].astype(float) for k in ("open", "high", "low", "close"))
        if len(idx):
            st = np.flatnonzero(np.r_[True, dn[1:] != dn[:-1]])
            en = np.r_[st[1:], len(dn)] - 1
            agg = dict(dn=dn[st], o=O[st], h=np.maximum.reduceat(Hh, st), l=np.minimum.reduceat(Ll, st), c=Cc[en],
                       n=en - st + 1)
        else:
            st = en = np.array([], np.int64)
            agg = dict(dn=np.array([], np.int64), o=np.array([]), h=np.array([]), l=np.array([]), c=np.array([]),
                       n=np.array([], np.int64))
        self.agg = agg
        tdn = int(dnum([np.datetime64(self.today)])[0]) if self.today else None
        keep = (agg["n"] >= 300) | ((agg["dn"] == tdn) if tdn is not None else False)
        kd = np.flatnonzero(keep)
        sel = np.concatenate([np.arange(st[k], en[k] + 1) for k in kd]) if len(kd) else np.array([], np.int64)
        lens = en[kd] - st[kd] + 1 if len(kd) else np.array([], np.int64)
        start = np.r_[0, np.cumsum(lens)[:-1]].astype(np.int64) if len(kd) else np.array([], np.int64)
        self.o, self.h, self.l, self.c = O[sel], Hh[sel], Ll[sel], Cc[sel]
        self.mod = (mod_all[idx][sel] - 570).astype(np.int64)
        self.di = np.repeat(np.arange(len(kd)), lens).astype(np.int64)
        self.ts = tm[idx][sel].astype("datetime64[m]")
        self.vol = m.volume.values[idx][sel].astype(float)
        self.n = len(sel)
        self.S0, self.E0 = start, (start + lens - 1).astype(np.int64)
        self.DN = agg["dn"][kd].astype(np.int64)
        self.DT = self.DN.astype("datetime64[D]").astype("datetime64[ns]")
        self.days = pd.DataFrame({"date": self.DT, "o": agg["o"][kd], "h": agg["h"][kd], "l": agg["l"][kd],
                                  "c": agg["c"][kd], "n": agg["n"][kd], "di": np.arange(len(kd)), "start": self.S0,
                                  "end": self.E0})
        self.live_di = len(kd) - 1 if (tdn is not None and len(kd) and self.DN[-1] == tdn) else None

    def _daily(self, d1):
        """full sessions' daily bars: Yahoo's before the 1m window, the 1m aggregates inside it (the study's panel
        days); the prior day's ATR14 and close per panel day."""
        rows = {}
        for b in d1 or ():
            d = cal._as_date(float(b["t"]) + 6 * 3600)
            if not full_day(d) or (self.today and d.isoformat() >= self.today):
                continue
            if None in (b.get("o"), b.get("h"), b.get("l"), b.get("c")):
                continue
            rows[d.isoformat()] = (float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]))
        A = self.agg
        for i in range(len(A["dn"])):
            key = str(np.datetime64(int(A["dn"][i]), "D"))
            if A["n"][i] >= 300 and key != self.today:
                rows[key] = (float(A["o"][i]), float(A["h"][i]), float(A["l"][i]), float(A["c"][i]))
        keys = sorted(rows)
        self.daily = pd.DataFrame({"date": pd.to_datetime(pd.Series(keys, dtype=object)),
                                   "o": [rows[k][0] for k in keys], "h": [rows[k][1] for k in keys],
                                   "l": [rows[k][2] for k in keys], "c": [rows[k][3] for k in keys]})
        self.ATR, self.PDC = {}, {}
        if not keys:
            return
        H, L, C = (self.daily[k].values.astype(float) for k in ("h", "l", "c"))
        a = M().atr(H, L, C, 14)
        dates = self.daily.date.values
        for di, dt in enumerate(self.DT):
            k = int(np.searchsorted(dates, dt))
            if k >= 1:
                self.ATR[di] = float(a[k - 1])
                self.PDC[di] = float(C[k - 1])

    def dates(self):
        """the panel's session list (full sessions, and the live one)."""
        d = list(self.daily.date.values)
        if self.live_di is not None:
            d.append(self.DT[self.live_di])
        return pd.DatetimeIndex(d)

    def day(self, di):
        return int(self.S0[di]), int(self.E0[di]), self.PDC.get(di, float("nan")), self.ATR.get(di, float("nan"))

    def is_live(self, di):
        return self.live_di is not None and di == self.live_di

    @staticmethod
    def _ind(x):
        C, H, L = x.close.values.astype(float), x.high.values.astype(float), x.low.values.astype(float)
        mm = M()
        return pd.DataFrame(dict(start=x.timestamp.values.astype("datetime64[m]"), e8=mm.ema(C, 8), e13=mm.ema(C, 13),
                                 e21=mm.ema(C, 21), e48=mm.ema(C, 48), po=mm.po(C, H, L), comp=mm.compression(C, H, L),
                                 atr=mm.atr(H, L, C, 14), h=H, l=L, c=C, o=x.open.values.astype(float)))

    def _complete(self, x, step):
        """candles whose span has ended within the bars present (the last 1m bar is at or past their last minute)."""
        if not len(self.M) or not len(x):
            return x.iloc[:0]
        last = self.M.timestamp.iloc[-1]
        return x[x.timestamp + pd.Timedelta(step) <= last + pd.Timedelta("1min")].reset_index(drop=True)

    def _htf(self, rule):
        if not len(self.M):
            return None
        x = self._complete(_agg(self.M, rule), rule)
        return self._ind(x) if len(x) else None

    def _hours(self, h1):
        """clock hours: the 1m bars' own hours (complete ones) and, before the 1m window, Yahoo's clock hours."""
        hm = self._complete(_agg(self.M, "1h"), "1h") if len(self.M) else _empty()
        if len(self.M):
            first = self.M.timestamp.iloc[0].ceil("h")
            hm = hm[hm.timestamp >= first]
        hy = _frame(h1)
        if len(hm):
            hy = hy[hy.timestamp < hm.timestamp.iloc[0]]
        x = pd.concat([f for f in (hy, hm) if len(f)], ignore_index=True) if (len(hy) or len(hm)) else _empty()
        return x.sort_values("timestamp").reset_index(drop=True) if len(x) else x

    @staticmethod
    def _four(H):
        if not len(H):
            return H
        x = _agg(H, "4h")
        return x[x.timestamp + pd.Timedelta("3h") <= H.timestamp.iloc[-1]].reset_index(drop=True)


def last_completed(I, minutes, when):
    """the study's last_completed: index of the last candle whose end (start + minutes) <= when."""
    if I is None:
        return -1
    ends = I.start.values + np.timedelta64(minutes, "m")
    return int(np.searchsorted(ends, np.datetime64(when, "m"), side="right") - 1)


def _trade(strat, cell, side, ent, ep, tgt, stp, smode, last, decide=None, **kw):
    t = dict(strat=strat, cell=cell, side=int(side), ent=int(ent), ep=float(ep), tgt=float(tgt), stp=float(stp),
             smode=int(smode), last=int(last), decide=int(ent if decide is None else decide), kind="eng")
    t.update(kw)
    return t


# --------------------------------------------------------------------------------------------- 21_intraday setups
def detect21(P, di):
    """21_intraday.py's per-day setups (Golden Gates, CT3, trigger box, C2P, gap, ORB, cascade) on panel day di, over
    the bars present (a live day: the session so far)."""
    key = ("21", di)
    if key in P.cache:
        return P.cache[key]
    out = []
    P.cache[key] = out
    s, e, PDC, A = P.day(di)
    if not (math.isfinite(A) and math.isfinite(PDC)):
        return out
    last = LIVE_LAST if P.is_live(di) else e
    o, c, mod = P.o, P.c, P.mod
    od = o[s]

    def Lv(x, sd):
        return PDC + sd * x * A

    def add(st, cell, side, ent, ep, tgt, stp, smode):
        out.append(_trade(st, cell, side, ent, ep, tgt, stp, smode, last))

    hh, ll, cc, mm = P.h[s:e + 1], P.l[s:e + 1], c[s:e + 1], mod[s:e + 1]
    po1h = P.I1h.po.values if P.I1h is not None else np.array([np.nan])
    for sd in (1, -1):                                         # day-mode Golden Gate and Bilbo GG
        g382, g236, g618 = Lv(0.382, sd), Lv(0.236, sd), Lv(0.618, sd)
        hit = np.flatnonzero(hh >= g382) if sd > 0 else np.flatnonzero(ll <= g382)
        if len(hit):
            j = hit[0]
            live = (od < g382) if sd > 0 else (od > g382)
            ep = (max(o[s + j], g382) if sd > 0 else min(o[s + j], g382)) if j > 0 else od
            k1 = last_completed(P.I1h, 60, P.ts[s + j])
            p1 = po1h[k1] if k1 >= 0 else np.nan
            p0 = po1h[k1 - 1] if k1 >= 1 else np.nan
            zone = (p1 > 61.8) if sd > 0 else (p1 < -61.8)
            rising = (p1 > p0) if sd > 0 else (p1 < p0)
            for coh in ("live", "all"):
                if coh == "live" and not live:
                    continue
                add("DGG", f"cohort={coh};filter=none", sd, s + j, ep, g618, g236, 10)
                if mm[j] <= 90:
                    add("DGG", f"cohort={coh};filter=before11", sd, s + j, ep, g618, g236, 10)
                if zone:
                    add("BGG", f"cohort={coh};filter=zone", sd, s + j, ep, g618, g236, 10)
                if zone and rising:
                    add("BGG", f"cohort={coh};filter=zone_rising", sd, s + j, ep, g618, g236, 10)
                if zone:
                    add("BGG", f"cohort={coh};filter=zone;target=1.0", sd, s + j, ep, Lv(1.0, sd), g236, 10)
    if Lv(0.236, -1) < od < Lv(0.236, 1):                      # 3-minute trigger confirmation
        for sd in (1, -1):
            tr = Lv(0.236, sd)
            q = np.flatnonzero(((mm + 1) % 3 == 0) & ((cc > tr) if sd > 0 else (cc < tr)))
            if len(q):
                j = q[0]
                add("CT3", "target=0.382", sd, s + j, cc[j], Lv(0.382, sd), tr, 3)
                add("CT3", "target=0.618", sd, s + j, cc[j], Lv(0.618, sd), tr, 3)
    for sd in (1, -1):                                         # trigger box
        tr = Lv(0.236, sd)
        inbox = (PDC < od < tr) if sd > 0 else (tr < od < PDC)
        if not inbox:
            continue
        first = (mm < 60) & ((mm + 1) % 10 == 0)
        lo_, hi_ = min(PDC, tr), max(PDC, tr)
        if np.all((cc[first] >= lo_) & (cc[first] <= hi_)):
            q = np.flatnonzero((mm >= 60) & ((mm + 1) % 10 == 0) & ((cc > tr) if sd > 0 else (cc < tr)))
            if len(q):
                j = q[0]
                add("TBOX", "target=0.382", sd, s + j, cc[j], Lv(0.382, sd), tr, 10)
                add("TBOX", "target=0.618", sd, s + j, cc[j], Lv(0.618, sd), tr, 10)
    idx = np.arange(len(cc))
    for sd in (-1, 1):                                         # call -> put morning reversal (and the mirror)
        first_tr, second_tr = Lv(0.236, -sd), Lv(0.236, sd)
        a1 = np.flatnonzero(((hh >= first_tr) if sd < 0 else (ll <= first_tr)) & (mm < 150))
        if not len(a1):
            continue
        j1 = a1[0]
        a2 = np.flatnonzero(((cc < PDC) if sd < 0 else (cc > PDC)) & (idx > j1) & (mm < 150))
        if not len(a2):
            continue
        j2 = a2[0]
        a3 = np.flatnonzero(((ll <= second_tr) if sd < 0 else (hh >= second_tr)) & (idx > j2) & (mm < 150))
        if not len(a3):
            continue
        j = a3[0]
        ep = min(o[s + j], second_tr) if sd < 0 else max(o[s + j], second_tr)
        add("C2P", "target=0.382", sd, s + j, ep, Lv(0.382, sd), PDC, 10)
        add("C2P", "target=0.618", sd, s + j, ep, Lv(0.618, sd), PDC, 10)
    gp = (od / PDC - 1) * 100                                  # gap fade / momentum mirror (decided at the open)
    for lo_b, hi_b in ((0.0, 0.1), (0.1, 0.25), (0.25, 0.5), (0.5, 1.0)):
        if lo_b < abs(gp) <= hi_b:
            fs = -np.sign(gp)
            for k_ in (0.25, 0.5, 1.0):
                for tg in ("full", "mid"):
                    T = PDC if tg == "full" else (od + PDC) / 2
                    Sx = od - fs * k_ * A
                    cell = f"bucket={lo_b}-{hi_b};stopATR={k_};target={tg}"
                    add("GAP", cell, fs, s, od, T, Sx, 0)
                    add("GAP", cell, -fs, s, od, Sx, T, 0)
    vol = P.vol[s:e + 1]                                       # opening range breakout
    vw = np.cumsum((hh + ll + cc) / 3 * vol) / np.maximum(np.cumsum(vol), 1)
    for m_ in (5, 10, 15, 30):
        if len(hh) < m_:                                       # a live day before its range is set: no close can
            continue                                           # break it yet
        orh, orl = hh[:m_].max(), ll[:m_].min()
        q = np.flatnonzero((mm >= m_) & ((mm + 1) % 5 == 0) & ((cc > orh) | (cc < orl)))
        if len(q):
            j = q[0]
            sd = 1 if cc[j] > orh else -1
            k10 = last_completed(P.I10, 10, P.ts[s + j] + np.timedelta64(1, "m"))
            e8, e21 = P.I10.e8.values, P.I10.e21.values         # (k10 = -1 reads the last candle, as the study did)
            rib = (e8[k10] > e21[k10]) if sd > 0 else (e8[k10] < e21[k10])
            vok = (cc[j] > vw[j]) if sd > 0 else (cc[j] < vw[j])
            for filt in ("none", "ribbon_vwap"):
                if filt == "ribbon_vwap" and not (rib and vok):
                    continue
                add("ORB", f"or={m_};filter={filt}", sd, s + j, cc[j], np.nan, orl if sd > 0 else orh, 0)
                add("ORB", f"or={m_};filter={filt};stop=mid", sd, s + j, cc[j], np.nan, (orh + orl) / 2, 0)
    for sd in (1, -1):                                         # ATR level cascade
        for i_ in range(1, 7):
            lv = Lv(LV[i_], sd)
            hit = np.flatnonzero(hh >= lv) if sd > 0 else np.flatnonzero(ll <= lv)
            if not len(hit) or hit[0] == 0:
                continue
            j = hit[0]
            ep = max(o[s + j], lv) if sd > 0 else min(o[s + j], lv)
            for win in ("pre10", "all"):
                if win == "pre10" and mm[j] >= 30:
                    continue
                add("CASCADE", f"window={win}", sd, s + j, ep, Lv(LV[i_ + 1], sd), Lv(LV[i_ - 1], sd), 0)
    return out


def _i10(P):
    if "i10" not in P.cache:
        I = P.I10
        st = pd.DatetimeIndex(I.start.values)
        bull = (I.e8.values > I.e13.values).astype(int)
        flip_up = np.r_[False, (bull[1:] == 1) & (bull[:-1] == 0)]
        flip_dn = np.r_[False, (bull[1:] == 0) & (bull[:-1] == 1)]
        comp = I.comp.values
        run = np.zeros(len(comp), int)
        for i in range(1, len(comp)):
            run[i] = run[i - 1] + 1 if comp[i] else 0
        P.cache["i10"] = dict(kmod=(st.hour * 60 + st.minute - 570).values, kday=dnum(st.normalize().values), bull=bull,
                              last_up=pd.Series(np.where(flip_up, np.arange(len(bull)), np.nan)).ffill().values,
                              last_dn=pd.Series(np.where(flip_dn, np.arange(len(bull)), np.nan)).ffill().values,
                              run=run)
    return P.cache["i10"]


def detect10(P, di):
    """VOMY / COMP10 (21_intraday.py's 10m setups) of panel day di from the 10m candles completed so far."""
    key = ("10", di)
    if key in P.cache:
        return P.cache[key]
    out = []
    P.cache[key] = out
    s, e, PDC, A = P.day(di)
    if not (math.isfinite(A) and math.isfinite(PDC)) or P.I10 is None:
        return out
    last = LIVE_LAST if P.is_live(di) else e
    I, G, mod, o = P.I10, _i10(P), P.mod, P.o
    e8, e13, e21, e48 = I.e8.values, I.e13.values, I.e21.values, I.e48.values
    hI, lI, cI, comp = I.h.values, I.l.values, I.c.values, I.comp.values
    bull, last_up, last_dn, run = G["bull"], G["last_up"], G["last_dn"], G["run"]
    for k in np.flatnonzero((G["kmod"] >= 0) & (G["kmod"] < 380) & (G["kday"] == P.DN[di])):
        mk = G["kmod"][k]
        j = s + mk + 9                                         # the 1m bar that closes this 10m candle
        if j > e or mod[j] != mk + 9:
            j = s + int(np.searchsorted(mod[s:e + 1], mk + 9))
            if j > e or mod[j] != mk + 9:
                continue
        for N in (3, 6):
            if bull[k] and k - last_up[k] <= N and lI[k] <= e13[k] and cI[k] > e8[k]:
                out.append(_trade("VOMY", f"flipwithin={N}", 1, j, cI[k], np.nan, e13[k], 10, last))
            if (not bull[k]) and k - last_dn[k] <= N and hI[k] >= e13[k] and cI[k] < e8[k]:
                out.append(_trade("VOMY", f"flipwithin={N}", -1, j, cI[k], np.nan, e13[k], 10, last))
        if comp[k] == 0 and k >= 1 and j + 1 <= e:            # (live: once the entry bar's open is in)
            for mb in (3, 6, 12, 18):
                if run[k - 1] >= mb:
                    lo_c = lI[k - run[k - 1]:k].min()
                    hi_c = hI[k - run[k - 1]:k].max()
                    sd = 1 if e21[k] > e48[k] else -1
                    ep = o[j + 1]
                    stp = lo_c if sd > 0 else hi_c
                    rk = abs(ep - stp)
                    if rk <= 0:
                        continue
                    out.append(_trade("COMP10", f"minbars={mb};exit=eod", sd, j + 1, ep, np.nan, stp, 0, last))
                    out.append(_trade("COMP10", f"minbars={mb};exit=1R", sd, j + 1, ep, ep + sd * rk, stp, 0, last))
    return out


def detect_cdc(P):
    """the 3m compression-drift continuation over every RTH 3m candle completed so far (the study's episode loop with
    its single-bar flicker rule and day-boundary skip); trades carry their panel day `di`."""
    if "cdc" in P.cache:
        return P.cache["cdc"]
    out = []
    P.cache["cdc"] = out
    I = P.I3
    if I is None or not len(P.days):
        return out
    st = pd.DatetimeIndex(I.start.values)
    m3 = (st.hour * 60 + st.minute - 570).values
    d3 = dnum(st.normalize().values)
    c3, H3, L3, C3, A3s = I.comp.values, I.h.values, I.l.values, I.c.values, I.atr.values
    idx3 = np.flatnonzero((m3 >= 0) & (m3 < 390))
    dmap = {int(v): i for i, v in enumerate(P.DN)}
    mod, o = P.mod, P.o
    k = 0
    while k < len(idx3):
        i = idx3[k]
        if c3[i] != 1:
            k += 1
            continue
        ep_bars = [i]
        kk = k + 1
        while kk < len(idx3) and d3[idx3[kk]] == d3[i]:
            b = idx3[kk]
            if c3[b] == 1:
                ep_bars.append(b)
                kk += 1
                continue
            nxt = idx3[kk + 1] if kk + 1 < len(idx3) else -1
            if len(ep_bars) >= 8:                              # candidate expansion candle b
                f5 = ep_bars[:5]
                r5h, r5l = H3[f5].max(), L3[f5].min()
                later = ep_bars[5:]
                A3 = A3s[ep_bars[-1]]
                lh, ll_ = H3[later].max(), L3[later].min()
                l5 = ep_bars[-5:]
                mid = (H3[l5].max() + L3[l5].min()) / 2
                up = (lh >= r5h + 0.5 * A3) and (ll_ >= r5l - 0.25 * A3)
                dn = (ll_ <= r5l - 0.5 * A3) and (lh <= r5h + 0.25 * A3)
                sd = 1 if (up and not dn) else (-1 if (dn and not up) else 0)
                if sd != 0 and ((C3[b] > mid) if sd > 0 else (C3[b] < mid)) and int(d3[b]) in dmap:
                    d = dmap[int(d3[b])]
                    s, e = int(P.S0[d]), int(P.E0[d])
                    jj = s + int(np.searchsorted(mod[s:e + 1], m3[b] + 3))
                    if jj <= e and np.isfinite(A3):            # (live: once the entry bar's open is in)
                        ep = o[jj]
                        A3c = A3s[b]
                        last = LIVE_LAST if P.is_live(d) else e
                        for g in (0.0, 0.0003, 0.00045, 0.0006):
                            if A3c >= g * ep:
                                out.append(_trade("CDC", f"atrgate={g}", sd, jj, ep, np.nan, ep - sd * A3c, 0, last,
                                                  di=d))
            if nxt >= 0 and c3[nxt] == 1 and d3[nxt] == d3[i]:
                kk += 1                                        # single-bar flicker: the episode continues
                continue
            break
        k = kk + 1
    return out


# --------------------------------------------------------------------------------------------- the exit engines
def step_exit(P, tr, j):
    """ilib.eng for one trade at bar j: the exit price or None. An entry at or after the last bar exits at the last
    bar's close."""
    sd, i, T, S, smode, last = tr["side"], tr["ent"], tr["tgt"], tr["stp"], tr["smode"], tr["last"]
    o, h, l, c, mod = P.o, P.h, P.l, P.c, P.mod
    if i >= last:
        return float(c[last]) if j == last else None
    if j <= i or j > last:
        return None
    if np.isfinite(S) and smode == 0:
        if sd > 0 and l[j] <= S:
            return float(min(o[j], S))
        if sd < 0 and h[j] >= S:
            return float(max(o[j], S))
    if np.isfinite(T):
        if sd > 0 and h[j] >= T:
            return float(max(o[j], T))
        if sd < 0 and l[j] <= T:
            return float(min(o[j], T))
    if np.isfinite(S) and smode > 0 and (mod[j] + 1) % smode == 0:
        if (sd > 0 and c[j] < S) or (sd < 0 and c[j] > S):
            return float(c[j])
    if j == last:
        return float(c[j])
    return None


def run_exit(P, tr, upto):
    """step an engine trade through the bars after its entry up to `upto`: (exit bar, exit price) or None."""
    i, last = tr["ent"], tr["last"]
    if i >= last:
        return (last, float(P.c[last])) if upto >= last else None
    for j in range(i + 1, min(upto, last) + 1):
        x = step_exit(P, tr, j)
        if x is not None:
            return j, x
    return None


# --------------------------------------------------------------------------------------------- 22_intraday2 setups
def bar_at(P, d, m):
    """the study's bar_at: the first RTH 1m bar of day d with mod >= m, capped at the day's last bar."""
    s, e = int(P.S0[d]), int(P.E0[d])
    return min(s + int(np.searchsorted(P.mod[s:e + 1], m)), e)


def _noon(P, d):
    """(index of the first bar at/after 12:00 or None, whether the bars before noon are all in)."""
    s, e = int(P.S0[d]), int(P.E0[d])
    q = s + int(np.searchsorted(P.mod[s:e + 1], 150))
    if q <= e:
        return q, True
    return None, (not P.is_live(d)) or P.mod[e] >= 149


def _lema_frame(P):
    if "lema" not in P.cache:
        R = pd.DataFrame(dict(di=P.di, b=P.mod // 15, o=P.o, h=P.h, l=P.l, c=P.c))
        B = R.groupby(["di", "b"]).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last")).reset_index()
        first = pd.Series(np.arange(len(B))).groupby(B.di.values).first()
        D = P.days
        ratio = np.abs(D.c.values - D.o.values) / np.maximum(D.h.values - D.l.values, 1e-9)
        P.cache["lema"] = (B, first, ratio)
    return P.cache["lema"]


def lema_threshold(P, q):
    """the study's train-period body/range quantile: full sessions 2000-01-01..2012-12-31 of the daily table."""
    D = P.daily
    m = (D.date >= pd.Timestamp("2000-01-01")) & (D.date < pd.Timestamp("2013-01-01"))
    if not m.any():
        return None
    r = np.abs(D.c.values[m] - D.o.values[m]) / np.maximum(D.h.values[m] - D.l.values[m], 1e-9)
    return float(np.quantile(r, q))


def lema_trades(P, EN, thr, q, days=None):
    """Legend's EMA: a setup day whose 15m RTH bars all stay on one side of the continuous RTH 15m EMA without
    touching it, with body/range >= thr, trades the next panel day at its open toward the EMA of the last completed
    15m bar (refreshed each bar), else to the close."""
    B, first, ratio = _lema_frame(P)
    if not len(B):
        return []
    if ("lema_em", EN) not in P.cache:
        em = M().ema(B.c.values, EN)
        touch = (B.l.values <= em) & (B.h.values >= em)
        dd = pd.DataFrame(dict(di=B.di.values, touch=touch, above=B.l.values > em, below=B.h.values < em)).groupby(
            "di").agg(t=("touch", "any"), a=("above", "all"), b=("below", "all"))
        notouch = np.zeros(len(P.days), bool)
        notouch[dd.index.values] = ~dd.t.values & (dd.a.values | dd.b.values)
        P.cache[("lema_em", EN)] = (em, notouch)
    em, notouch = P.cache[("lema_em", EN)]
    nd = len(P.days)
    out = []
    for d in (range(1, nd) if days is None else days):
        if d < 1 or not (notouch[d - 1] and ratio[d - 1] >= thr):
            continue
        s, e, pdc, A = P.day(d)
        if not (math.isfinite(A) and math.isfinite(pdc)):
            continue
        f0 = int(first[d])
        mods = P.mod[s:e + 1]
        bidx = np.where(mods < 15, f0 - 1, f0 + (mods // 15) - 1)
        T = em[np.clip(bidx, 0, len(em) - 1)]
        sd = 1 if P.o[s] < T[0] else -1
        out.append(dict(strat="LEMA", cell=f"ema={EN};q={q}", side=sd, ent=s, ep=float(P.o[s]), decide=s, kind="lema",
                        d=d, T=T, last=LIVE_LAST if P.is_live(d) else e))
    return out


def lema_exit(P, tr, upto):
    """the study's lema_trade: from the entry bar on, the first bar reaching the refreshed EMA exits at it (gap-honest),
    else the day's last bar's close."""
    s, sd, T = tr["ent"], tr["side"], tr["T"]
    e = int(P.E0[tr["d"]])
    o, h, l = P.o, P.h, P.l
    for j in range(s, min(upto, e) + 1):
        t = T[j - s]
        if np.isfinite(t):
            if sd > 0 and h[j] >= t:
                return j, float(max(o[j], t))
            if sd < 0 and l[j] <= t:
                return j, float(min(o[j], t))
    if tr["last"] != LIVE_LAST and upto >= e:
        return e, float(P.c[e])
    return None


def _mdl_frame(P):
    """the study's 3m ATR / efficiency ratio, warmed up inside each calendar day (all-hours 3m candles)."""
    if "mdl" not in P.cache:
        I = P.I3
        if I is None:
            P.cache["mdl"] = None
            return None
        st = pd.DatetimeIndex(I.start.values)
        H3, L3, C3 = I.h.values, I.l.values, I.c.values
        pc3 = np.r_[np.nan, C3[:-1]]
        TR3 = np.nanmax(np.vstack([H3 - L3, np.abs(H3 - pc3), np.abs(L3 - pc3)]), axis=0)
        d3 = dnum(st.normalize().values)
        newday = np.r_[True, d3[1:] != d3[:-1]]
        grp = np.cumsum(newday)
        s3 = pd.Series(TR3)
        s3[newday] = H3[newday] - L3[newday]
        ATR3 = s3.groupby(grp).transform(lambda x: x.rolling(14, min_periods=14).mean()).values
        ch = pd.Series(np.abs(np.r_[np.nan, np.diff(C3)]))
        ch[newday] = np.nan
        den = ch.groupby(grp).transform(lambda x: x.rolling(15, min_periods=15).sum()).values
        num = np.abs(pd.Series(C3).groupby(grp).diff(15).values)
        P.cache["mdl"] = dict(d3=d3, H3=H3, L3=L3, C3=C3, ATR3=ATR3, ER=num / den,
                              m3=(st.hour * 60 + st.minute - 570).values)
    return P.cache["mdl"]


def mdl_trades(P, erc, k, side, days=None):
    """Morning Dip Limit: closed 3m candles ending 10:00-12:00 with ER <= erc arm a limit k x ATR3 beyond the close for
    bars arm..arm+8 (it fills when a bar trades a cent through it); target the candle midpoint (>= 2 cents beyond),
    stop 1.5 x ATR3 (>= 4 cents); in the fill bar only the stop counts; then the stop (gap-honest), the target, a
    15-bar time stop, flat before 12:00; one order or position at a time. Trades: dict(arm, f (fill bar), xb (exit
    bar), px, ret, ...); f / xb None while undecided on a live day."""
    F = _mdl_frame(P)
    if F is None or not len(P.days):
        return []
    m3, ATR3, ER, d3 = F["m3"], F["ATR3"], F["ER"], F["d3"]
    dmap = {int(v): i for i, v in enumerate(P.DN)}
    sig = np.flatnonzero((m3 + 3 >= 30) & (m3 + 3 <= 150) & np.isfinite(ATR3) & np.isfinite(ER))
    o, h, l, c, mod = P.o, P.h, P.l, P.c, P.mod
    tick = 0.01
    out, busy, stop_day = [], -1, None
    cell = f"er={erc};k={k}"
    for i in sig:
        if not ER[i] <= erc:
            continue
        d = dmap.get(int(d3[i]))
        if d is None or (days is not None and d not in days) or d == stop_day:
            continue
        s, e, pdc, A_ = P.day(d)
        if not (math.isfinite(A_) and math.isfinite(pdc)):
            continue
        arm = s + int(np.searchsorted(mod[s:e + 1], m3[i] + 3))
        q, noon_known = _noon(P, d)
        lastb = (q - 1) if q is not None else (e if noon_known else LIVE_LAST)
        if arm <= busy:
            continue
        A = ATR3[i]
        Cl, mid = F["C3"][i], (F["H3"][i] + F["L3"][i]) / 2
        lim = Cl - side * k * A
        tgt = max(mid, lim + 0.02) if side > 0 else min(mid, lim - 0.02)
        stp = lim - side * max(1.5 * A, 0.04)
        rec = dict(strat="MDL", cell=cell, side=side, d=d, arm=arm, f=None, xb=None, px=None, ret=None, lim=lim, tgt=tgt,
                   stp=stp, kind="mdl")
        f = -1
        wend = min(arm + 8, lastb)
        for j in range(arm, min(wend, e) + 1):
            if (side > 0 and l[j] <= lim - tick) or (side < 0 and h[j] >= lim + tick):
                f = j
                break
        if f < 0:
            if wend <= e:                                      # the window is over unfilled
                busy = arm + 8
                continue
            out.append(rec)                                    # still armed (live): later candles wait for it
            stop_day = d
            continue
        rec["f"] = f
        ep = lim
        if (side > 0 and l[f] <= stp) or (side < 0 and h[f] >= stp):
            rec.update(xb=f, px=stp, ret=side * (stp / ep - 1) - tick / ep)
            out.append(rec)
            busy = f
            continue
        end = min(f + 15, lastb)
        for j in range(f + 1, min(end, e) + 1):
            if (side > 0 and l[j] <= stp) or (side < 0 and h[j] >= stp):
                px = min(o[j], stp) if side > 0 else max(o[j], stp)
                rec.update(xb=j, px=px, ret=side * (px / ep - 1) - tick / ep)
                break
            if (side > 0 and h[j] >= tgt) or (side < 0 and l[j] <= tgt):
                rec.update(xb=j, px=tgt, ret=side * (tgt / ep - 1))
                break
        if rec["xb"] is None and end <= e:
            rec.update(xb=end, px=c[end], ret=side * (c[end] / ep - 1) - tick / ep)
        out.append(rec)
        if rec["xb"] is None:
            stop_day = d                                       # the position is open (live)
            continue
        busy = rec["xb"]
    return out


def esmon_window(P, day, eh, xh):
    """the study's window_ret legs on all-hours 1m bars: for eh:00 and xh:00, the open of the first bar at/after it
    when that bar is on the same date and within 5 minutes; False when it is not (the study's NaN); None when no bar
    at/after it is in yet (the study, at its data end, read the last bar before it)."""
    ts = P.M.timestamp.values.astype("datetime64[m]")
    if not len(ts):
        return [None, None]
    op = P.M.open.values
    base = np.datetime64(pd.Timestamp(day), "m")
    out = []
    for hr in (eh, xh):
        t0 = base + np.timedelta64(int(round(hr * 60)), "m")
        a = int(np.searchsorted(ts, t0))
        if a >= len(ts):
            out.append(None)
            continue
        ok = (ts[a] - t0) <= np.timedelta64(5, "m") and ts[a].astype("datetime64[D]") == base.astype("datetime64[D]")
        out.append(float(op[a]) if ok else False)
    return out


def pm_high(P, day):
    """the 04:00-09:29 high of `day`'s all-hours bars, or None."""
    m = P.M
    ts = m.timestamp
    mins = (ts.dt.hour * 60 + ts.dt.minute).values
    sel = (ts.dt.normalize() == pd.Timestamp(day)).values & (mins >= 240) & (mins < 570)
    return float(m.high.values[sel].max()) if sel.any() else None


def ath_before(P, day):
    """the highest high of every session before `day`: the 1m bars' all-hours highs, the clock hours' and the daily
    table's (full sessions)."""
    t = pd.Timestamp(day)
    hi = []
    if len(P.M):
        x = P.M.high.values[(P.M.timestamp < t).values]
        if len(x):
            hi.append(float(x.max()))
    if len(P.H):
        x = P.H.high.values[(P.H.timestamp < t).values]
        if len(x):
            hi.append(float(x.max()))
    if len(P.daily):
        x = P.daily.h.values[(P.daily.date < t).values]
        if len(x):
            hi.append(float(x.max()))
    return max(hi) if hi else None


def po10_at_open(P, day):
    """the study's po_at_open: the 10m Phase Oscillator of the last candle finished by 09:30 of `day`."""
    I = P.I10
    if I is None:
        return np.nan
    end10 = I.start.values + np.timedelta64(10, "m")
    k = int(np.searchsorted(end10, np.datetime64(pd.Timestamp(day) + pd.Timedelta(minutes=570), "m"),
                            side="right") - 1)
    return I.po.values[k] if k >= 0 else np.nan


def pmath_trades(P, d, ath_prev=None):
    """Premarket ATH morning fade on panel day d, every cell: [(cell, trade)] — short the open when the 04:00-09:29
    high is above every prior session's high (kill: not when the 10m PO at 09:30 is >= 61.8); out at 12:00 (the last
    bar before it) or the close, with an optional stopA x ATR stop."""
    s, e, pdc, A = P.day(d)
    if not (math.isfinite(A) and math.isfinite(pdc)):
        return []
    day = P.DT[d]
    pmh = pm_high(P, day)
    ath = ath_before(P, day) if ath_prev is None else ath_prev
    if pmh is None or ath is None or not pmh > ath:
        return []
    po = po10_at_open(P, day)
    q, noon_known = _noon(P, d)
    out = []
    for filt in ("none", "kill"):
        if filt == "kill" and po >= 61.8:
            continue
        for xm in (150, 390):
            if xm == 390:
                last = LIVE_LAST if P.is_live(d) else e
            elif q is not None:
                last = min(q, e) - 1
            else:
                last = (e - 1) if not P.is_live(d) else (e if noon_known else LIVE_LAST)
            for stopA in (0.0, 0.5):
                ep = P.o[s]
                S = ep + stopA * A if stopA > 0 else np.nan
                cell = f"filter={filt};exit={'12:00' if xm == 150 else 'close'};stopATR={stopA}"
                out.append((cell, _trade("PMATH", cell, -1, s - 1 if s > 0 else s, ep, np.nan, S, 0, last,
                                         decide=s, xm=xm)))
    return out


def _htf_daily(P, freq):
    D = P.daily.set_index("date")
    X = pd.DataFrame(dict(h=D.h.resample(freq).max(), l=D.l.resample(freq).min(), c=D.c.resample(freq).last())).dropna()
    X["atr"] = M().atr(X.h.values, X.l.values, X.c.values, 14)
    return X


def _extpos(day, px, X):
    k = int(np.searchsorted(X.index.values, np.datetime64(day))) - 1
    if k < 0:
        return np.nan
    return (px - X.c.values[k]) / X.atr.values[k]


def opx4_rows(P, window=True):
    """4h PO rollovers (>= 80, then < 80) on panel days — inside the OpEx window (the panel day on or after the third
    Friday and the five after it) when `window` — the first per day, with the greater of the prior completed week's /
    month's ATR extension: [dict(d, day, px, ext, start, end)]."""
    I4 = P.I4
    if I4 is None or len(I4) < 2:
        return []
    DATES = P.dates()
    if not len(DATES):
        return []
    po4 = I4.po.values
    sig4 = np.flatnonzero((po4[:-1] >= 80) & (po4[1:] < 80)) + 1
    starts = pd.DatetimeIndex(I4.start.values)
    pos_of = {int(v): i for i, v in enumerate(dnum(DATES.values))}
    inwin = np.zeros(len(DATES), bool)
    for x in pd.date_range(DATES[0] - pd.Timedelta(days=40), DATES[-1] + pd.Timedelta(days=40), freq="WOM-3FRI"):
        kx = int(np.searchsorted(DATES.values, np.datetime64(x)))
        if kx < len(DATES):
            inwin[kx:kx + 6] = True
    WK, MO = _htf_daily(P, "W-FRI"), _htf_daily(P, "ME")
    out, seen = [], set()
    for k in sig4:
        dd_ = starts[k].normalize()
        d = pos_of.get(int(dnum([dd_.to_datetime64()])[0]))
        if d is None or (window and not inwin[d]) or d in seen:
            continue
        seen.add(d)
        px = float(I4.c.values[k])
        ext = max(_extpos(dd_, px, WK), _extpos(dd_, px, MO))
        out.append(dict(d=d, day=dd_, px=px, ext=float(ext), start=starts[k], end=starts[k] + pd.Timedelta(hours=4)))
    return out


def gupn_trade(P, d, X):
    """Gap-up pre-noon continuation: open above the prior close and a touch of prior close x (1 + X%) before 12:00 ->
    long at the next bar's open, out at the close."""
    s, e, pdc, A = P.day(d)
    if not (math.isfinite(A) and math.isfinite(pdc)) or P.o[s] <= pdc:
        return None
    lv = pdc * (1 + X / 100)
    q, _ = _noon(P, d)
    noon = min(q, e) if q is not None else (e if not P.is_live(d) else e + 1)
    hit = np.flatnonzero(P.h[s:noon] >= lv)
    if not len(hit):
        return None
    j = s + int(hit[0]) + 1
    live = P.is_live(d)
    if j > e and not live:
        return None
    ep = float(P.o[j]) if j <= e else float("nan")
    return _trade("GUPN", f"X={X}", 1, j, ep, np.nan, np.nan, 0, LIVE_LAST if live else e, decide=j - 1)


# --------------------------------------------------------------------------------------------- lanes' trades today
def lane_trades(setup, P, di, cell, side):
    """the trades of one lane on panel day di, each with its decide bar and its exit over the bars present:
    [dict(key, decide, exit=(bar, px) | None, ...)]."""
    e = int(P.E0[di])
    out = []
    if setup in SET21 or setup in SET10 or setup == "CDC":
        src = detect21(P, di) if setup in SET21 else (detect10(P, di) if setup in SET10 else
                                                      [t for t in detect_cdc(P) if t["di"] == di])
        for t in src:
            if t["strat"] == setup and t["cell"] == cell and t["side"] == side:
                out.append(dict(t, key=f"{t['ent']}|{t['tgt']:.6f}|{t['stp']:.6f}", exit=run_exit(P, t, e)))
    elif setup == "GUPN":
        t = gupn_trade(P, di, parse_cell(cell)["X"])
        if t is not None:
            out.append(dict(t, key=str(t["ent"]), exit=run_exit(P, t, e) if t["ent"] <= e else None))
    elif setup == "PMATH":
        for c_, t in pmath_trades(P, di):
            if c_ == cell:
                out.append(dict(t, key=str(t["decide"]), exit=run_exit(P, t, e)))
    elif setup == "LEMA":
        p = parse_cell(cell)
        thr = P.cache.get(("lema_thr", p["q"]))
        if thr is None:
            thr = P.cache[("lema_thr", p["q"])] = lema_threshold(P, p["q"])
        if thr is not None:
            for t in lema_trades(P, int(p["ema"]), thr, p["q"], days=[di]):
                if t["side"] == side:
                    out.append(dict(t, key=str(t["ent"]), exit=lema_exit(P, t, e)))
    elif setup == "MDL":
        p = parse_cell(cell)
        for t in mdl_trades(P, p["er"], p["k"], side, days={di}):
            if t["f"] is not None:
                out.append(dict(t, key=str(t["arm"]), decide=t["f"],
                                exit=(t["xb"], t["px"]) if t["xb"] is not None else None))
    return out


def _next_full_days(day, n):
    d = cal._as_date(day)
    while n > 0:
        d = cal.next_trading_day(d)
        if full_day(d):
            n -= 1
    return d.isoformat()


