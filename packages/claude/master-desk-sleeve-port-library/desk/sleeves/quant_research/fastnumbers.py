"""qr_fastnumbersslowwordseventreconstruct -- Fast Numbers / Slow Words: the six-strategy reconstruction's principal
numeric ledger (variant numeric_sue_canonical_raw_error): canonical SUE, the monthly frozen market-wide CDF, the
90th / 10th-percentile tails and the Appendix C.2 weights G/N x 2 x (p - 0.5), held from the open to the close of the
first session that can trade the release.

SOURCE: quant-research-critical@0be4c575 research/2026-10-08-six-strategy-reconstruction/source.zip.parts ::
fastnumbers/run_reconstruction.py (cdf_scores, actual_session, weights; the pnl() ledger's sizing) and
fastnumbers/prepare_events.py (historical_sue), vendored byte-exact under desk/vendor/quant_research/fastnumbers/ and
EXECUTED here, never restated; the event history fastnumbers/data/numeric-events.csv.gz (79,924 Yahoo retrospective
EPS releases 2016-01 .. 2025-11, availability = the release timestamp) vendored with them.
Parity: tools/parity/qr_fastnumbers.py -> docs/receipts/parity/qr_fastnumbers.json.

Each session D, at the first pass from 09:31 ET (the open plus the source's one minute):
  events  = the vendored history, then Nasdaq's earnings calendar after its last day (desk/feedlib/griffith_earnings:
            reported EPS, consensus EPS, the release-time tag), every release with both numbers;
  SUE     = prepare_events.historical_sue(events): forecast error over the sample SD of the issuer's previous eight
            errors (at least four) -- the canonical raw-error SUE;
  p       = run_reconstruction.cdf_scores(SUE, mode='expanding', from 2022-01-01, >= 30): every release of a month
            ranked against all earlier months' SUEs (midpoint ties), frozen for the month;
  session = run_reconstruction.actual_session: the first regular-session open at or after availability + 1 minute;
  N       = D's whole cohort with a finite SUE and p (before any price filter: missing prices stay unexecuted, their
            capital is never redistributed);
  weight  = run_reconstruction.weights: (2 / N) x 2 x (p - 0.5) where |p - 0.5| >= 0.4, else 0.
Orders: NAV x weight / price shares, long the top tail and short the bottom tail, at the market; every position
closes market-on-close (submitted from 15:45 ET). A position the close did not take is closed at the next pass.

Removed gates: none (the source has no desk-wide gates; its 0-60 bps cost stresses, the 3% borrow and 5% financing
charges are its accounting, not decisions).

Named divergences:
  1. live events: Nasdaq's earnings calendar (the desk's archived pages) after the vendored Yahoo snapshot ends;
     availability from its release tag -- pre-market 08:00 ET of the date, after-hours 16:30 ET, untimed end of day
     (the next session) -- in place of Yahoo's release timestamps; SUE denominators mix the two sources' consensus
     figures across the seam;
  2. execution: market orders from the first pass at or after 09:31 ET at the desk's quotes in place of the daily
     open price (a name still unquoted at 09:45 stays unexecuted, as an unpriced event does in the source); the exit
     is a market-on-close order (the source's close price). The executed set is therefore the cohort tails the desk
     quotes, not the ones the source's price_events() priced from its daily panel (the all-adjusted proxy outside
     2024-25, which priced 329 of 2022-23's 3,407 tails; the Alpaca raw1Day extension in 2024-25, which missed 9 of
     3,853): such a tail keeps the source's weight here and trades when quoted;
  3. shorts are whole shares (the broker refuses fractional shorts);
  4. NAV: the sleeve's equity at the decision pass in place of the prior session's closing NAV;
  5. SUE inputs: the snapshot's releases keep the source's stored forecast errors and SDs; releases after it get
     prepare_events.historical_sue under the desk's pandas 3 (the source ran pandas 2.2: the rolling SD can differ in
     the last bits, which can move a CDF midpoint tie by one rank)."""
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as C

SID = "qr_fastnumbersslowwordseventreconstruct"
ET = ZoneInfo("America/New_York")
VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                      "quant_research", "fastnumbers")
HISTORY = os.path.join(VENDOR, "data", "numeric-events.csv.gz")
SIGNAL = "sue_canonical_raw_error"
SOURCE = {"repo": C.SOURCE_REPO, "ref": "main", "commit": C.SOURCE_COMMIT,
          "path": C.SIXAI + "fastnumbers/run_reconstruction.py",
          "inputs": C.SIXAI + "fastnumbers/data/numeric-events.csv.gz"}
TIME_OF = {"time-pre-market": (8, 0), "time-after-hours": (16, 30)}
ENTRY_HM, PRICE_WAIT_HM, EXIT_HM = "09:31", "09:45", "15:45"
COLS = ["symbol", "available_at", "estimate_eps", "actual_eps", "origin", "stored_fe", "stored_sd"]
_MOD = {}
_MEMO = {}


def source():
    """the vendored run_reconstruction / prepare_events modules (the calendar shim stands in for
    pandas_market_calendars; load_arrays resolves from the vendored finrlx folder, the source's own layout)."""
    if "rr" not in _MOD:
        C.install_calendar_shim()
        before = list(sys.path)
        try:
            from ...vendor.quant_research.fastnumbers import prepare_events as pe
            from ...vendor.quant_research.fastnumbers import run_reconstruction as rr
        finally:
            sys.path[:] = before                          # the module's sys.path insert stays local to its import
        _MOD.update(rr=rr, pe=pe)
    return _MOD["rr"], _MOD["pe"]


def history():
    if "hist" not in _MOD:
        h = pd.read_csv(HISTORY, usecols=["symbol", "available_at", "estimate_eps", "actual_eps", "forecast_error",
                                          "historical_error_std"])
        h["available_at"] = pd.to_datetime(h["available_at"], utc=True)
        h["origin"] = "yahoo"
        h = h.rename(columns={"forecast_error": "stored_fe", "historical_error_std": "stored_sd"})
        _MOD["hist"] = h[COLS]
    return _MOD["hist"]


def history_end():
    return history()["available_at"].max().tz_convert(ET).date().isoformat()


def nasdaq_events(root, after_day, until_day):
    """the cached Nasdaq calendar pages (after_day, until_day] -> rows with availability from the release tag."""
    from ...feedlib import griffith_earnings as ge
    rows = []
    d = (pd.Timestamp(after_day) + pd.Timedelta(days=1)).date()
    end = pd.Timestamp(until_day).date()
    while root and d <= end:
        page = ge.load_page(root, d.isoformat()) if d.weekday() < 5 else None
        for r in (page or {}).get("rows") or []:
            if r.get("eps") is None or r.get("consensus") is None:
                continue
            hh, mm = TIME_OF.get(r.get("time"), (23, 59))
            at = pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=ET).tz_convert("UTC")
            rows.append({"symbol": str(r["symbol"]), "available_at": at, "estimate_eps": float(r["consensus"]),
                         "actual_eps": float(r["eps"]), "origin": "nasdaq", "stored_fe": np.nan,
                         "stored_sd": np.nan})
        d += timedelta(days=1)
    return pd.DataFrame(rows, columns=COLS)


def scored(events, session_day):
    """the source's pipeline over `events` (symbol, available_at, estimate_eps, actual_eps) -> the rows whose
    session is `session_day`, with SUE, p, N and the weight."""
    rr, pe = source()
    x = events[events["estimate_eps"].notna() & events["actual_eps"].notna()].copy()
    x = x.sort_values(["symbol", "available_at"]).drop_duplicates(["symbol", "available_at"], keep="first")
    x["event_id"] = x["symbol"] + "|" + x["available_at"].astype(str)
    old = (x["origin"] == "yahoo").to_numpy()          # the snapshot's own stored inputs (pandas 2.2 rolling SDs)
    x["forecast_error"] = x["stored_fe"]
    x["historical_error_std"] = x["stored_sd"]
    if not old.all():                                  # later releases: historical_sue over their issuers' rows
        live_syms = set(x.loc[~old, "symbol"])
        part = pe.historical_sue(x[x["symbol"].isin(live_syms)].drop(columns=["forecast_error",
                                                                              "historical_error_std"]),
                                 "absolute_error")
        part = part[part["origin"] != "yahoo"]
        x.loc[part.index, "forecast_error"] = part["forecast_error"]
        x.loc[part.index, "historical_error_std"] = part["historical_error_std"]
    x[SIGNAL] = x["forecast_error"] / x["historical_error_std"].replace(0, np.nan)
    month_end = pd.Timestamp(session_day[:7] + "-01", tz="UTC") + pd.DateOffset(months=1)
    x = x[(x["available_at"] >= pd.Timestamp("2022-01-01", tz="UTC")) & (x["available_at"] < month_end)]
    x = rr.cdf_scores(x, SIGNAL, mode="expanding", min_history=30)
    x = x[np.isfinite(x[SIGNAL]) & np.isfinite(x.cdf_percentile)].copy()
    lo = (pd.Timestamp(session_day) - pd.Timedelta(days=45)).date().isoformat()
    days = pd.DatetimeIndex([pd.Timestamp(d) for d in C.sessions_between(
        lo, (pd.Timestamp(session_day) + pd.Timedelta(days=10)).date().isoformat())])
    first_open = pd.Timestamp(str(days[0].date()) + " 09:30:00", tz=ET).tz_convert("UTC")
    x = x[x.available_at_used + pd.Timedelta(minutes=1) > first_open]      # events before the window's first open
    if not len(x):
        return x.assign(session_N=0, weight=0.0)
    x = rr.actual_session(x, days)
    x = x[x.session_date == session_day].copy()
    x["session_N"] = x.groupby("session_date")["event_id"].transform("count")
    return rr.weights(x, SIGNAL)


def decide(root, session_day):
    """({symbol: weight}, N, {symbol: p}) of the session's cohort (memoised per session and calendar-cache rows). Two
    releases of one issuer in a session are two events of the source's ledger: the symbol's weight is their sum (the
    account's net), its p the later event's; decide_events() keeps them apart."""
    live = nasdaq_events(root, history_end(), session_day)
    key = (session_day, len(live), float(live["actual_eps"].sum()) if len(live) else 0.0)
    if _MEMO.get("key") != key:
        w = scored(pd.concat([history(), live], ignore_index=True) if len(live) else history(), session_day)
        weights = {}
        for r in w.itertuples():
            weights[str(r.symbol)] = weights.get(str(r.symbol), 0.0) + float(r.weight)
        _MEMO.update(key=key, weights=weights, n=int(w["session_N"].iloc[0]) if len(w) else 0,
                     p={str(r.symbol): float(r.cdf_percentile) for r in w.itertuples()},
                     events={str(r.event_id): (str(r.symbol), float(r.cdf_percentile), float(r.weight))
                             for r in w.itertuples()})
    return _MEMO["weights"], _MEMO["n"], _MEMO["p"]


def decide_events(root, session_day):
    """{event_id: (symbol, p, weight)} of the session's cohort (decide()'s memo)."""
    decide(root, session_day)
    return _MEMO["events"]


def feed_refresh(f, s, now, arg):
    """once per session in regular hours: today's and the previous session's Nasdaq calendar pages (the pre-market
    reporters' actuals), shared with the event_research sleeves' refresh memo."""
    root = getattr(getattr(s, "engine", None), "root", None)
    if root is None or not cal.is_rth(now):
        return None
    from ...feedlib import griffith_earnings as ge
    memo = f.__dict__.setdefault("_griffith_earn_refresh", {})
    day = cal._as_date(now).isoformat()
    if memo.get("day") != day:
        ge.refresh_today(root, now)
        memo["day"] = day
    return {"day": day}


class FastNumbers(Sleeve):
    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=60, universe=(), capital=1_000_000.0,
            schedule="rth", needs={"feeds": ["qr_fn_refresh"], "quotes": {"source": "equity"}},
            params={"signal": SIGNAL, "cdf": "monthly frozen, expanding from 2022-01-01, >= 30",
                    "tails": "|p - 0.5| >= 0.4", "weight": "(2/N) x 2 x (p - 0.5)", "hold": "open to close",
                    "entry_from": ENTRY_HM, "moc_from": EXIT_HM},
            source=SOURCE, state_schema={"day": "str", "weights": "dict", "n": "int", "entered": "dict",
                                         "moc": "str", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def _root(self):
        return getattr(self.engine, "root", None)

    def quote_universe(self, now, book):
        held = {i.split(":", 1)[1] for i, p in (book.positions or {}).items()
                if i.startswith("EQ:") and abs(float(p["qty"])) > 1e-12}
        day = cal._as_date(now).isoformat()
        hm = datetime.fromtimestamp(now, tz=ET).strftime("%H:%M")
        names = set()
        if C.is_session(day) and ENTRY_HM <= hm < EXIT_HM:
            try:
                w, _, _ = decide(self._root(), day)
                names = {s for s, v in w.items() if v}
            except Exception:
                names = set()
        return sorted(held | names)

    def signal(self, view):
        st = dict(view.state or {})
        for k, v in (("entered", {}), ("log", [])):
            st.setdefault(k, v)
        self._st = st
        now, day = float(view.now), view.session
        if not cal.is_rth(now) or not C.is_session(day):
            return []
        hm = datetime.fromtimestamp(now, tz=ET).strftime("%H:%M")
        held = C.held(view)
        out = []
        owed = sorted(s for s in held if st["entered"].get(s) != day)
        for s in owed:                                            # a position the close did not take
            out.append(Intent("target", s, side="long", qty=0.0, signal_key=f"fn:{day}:{s}:owed",
                              reason=f"{SID} owed exit", order=OrderSpec(type="market", window_s=600)))
        if hm >= EXIT_HM:
            if st.get("moc") != day:
                for s in sorted(set(held) - set(owed)):
                    out.append(Intent("target", s, side="long", qty=0.0, signal_key=f"fn:{day}:{s}:moc",
                                      reason=f"{SID} close", order=OrderSpec(type="market", tif="cls")))
                st["moc"] = day
            return out
        if hm < ENTRY_HM or st.get("day") == day:
            return out
        if self._root() and ((view.extra or {}).get("qr_fn_refresh") or {}).get("day") != day:
            return out                                            # today's calendar page not re-read yet
        try:
            w, n, p = decide(self._root(), day)
        except Exception as e:                                   # the calendar cache is unreadable: wait
            st["log"] = (st["log"] + [{"at": day, "why": f"events: {type(e).__name__}: {str(e)[:80]}"}])[-50:]
            return out
        tails = {s: v for s, v in w.items() if v}
        unpriced = [s for s, v in tails.items() if not ((view.quotes or {}).get(s) or {}).get("ask" if v > 0 else "bid")]
        if unpriced and hm < PRICE_WAIT_HM:
            return out                                            # quotes for this pass's new names: next pass
        nav = C.nav(view)
        orders = {}
        for s, wt in sorted(tails.items()):
            q = (view.quotes or {}).get(s) or {}
            px = q.get("ask") if wt > 0 else q.get("bid")
            if not px:
                continue                                          # unpriced: unexecuted, never redistributed
            qty = nav * wt / float(px)
            if wt < 0:
                qty = -float(int(-qty))                           # whole-share shorts
            if qty == 0:
                continue
            orders[s] = qty
            st["entered"][s] = day
            out.append(Intent("target", s, side="long" if qty > 0 else "short", qty=round(abs(qty), 6),
                              price_hint=float(px), signal_key=f"fn:{day}:{s}:open",
                              reason=f"{SID} p={p.get(s, 0):.4f} N={n} w={wt:.5f}",
                              order=OrderSpec(type="market", window_s=1800)))
        st.update(day=day, weights=tails, n=n)
        st["log"] = (st["log"] + [{"at": day, "N": n, "tails": len(tails), "orders": len(orders),
                                   "unpriced": unpriced[:10]}])[-50:]
        return [i for i in out if not (i.signal_key.endswith(":owed") and i.symbol in orders)]

    def update_state(self, view, intents):
        st = getattr(self, "_st", None) or dict(view.state or {})
        held = C.held(view)
        st["entered"] = {s: d for s, d in (st.get("entered") or {}).items() if s in held or d == view.session}
        return st


def sleeves():
    return [FastNumbers()]
