"""APEX / Aurelia (Cursor2) research sleeves: their decisions, computed by the source's own code.

Source: cursor2 main @ca8ac1f650670e1d (desk/strategies.py, desk/round3.py, desk/inventions.py, desk/options/*, and
the research runners that called them: research/run_study.py, run_inventions.py, run_round3.py,
run_options_study.py / _v2 / _v3), vendored in desk/vendor/apex/ (byte-exact files and verbatim excerpts). This
module supplies their data; desk/feedlib/apex_rules.py reads their answer; neither decides anything itself.

  data ..... the daily frames the source's yahoo.get_daily returned: the Aurelia feed's full-history loader
             (desk/feedlib/aurelia.History: the same chart call, period1 1900, events div,split, adjusted closes,
             the source's parse), its cache shared with the Aurelia feed (^NDX, QQQ, GC=F, ^VIX are its files), cut
             at the last finished session t — the data the source desk's live runtime decided on.
  decision . apex_rules on those frames: each strategy as its research runner called it, the plan for the next
             close by the source desk's planned_position (the band and the one-day lag), the lag-shifted asset
             choices on t, the calendar's next sessions for E7's look-ahead and the multi-asset re-runs.
  cache .... one computation per finished session (the decisions JSON, keyed by every history's last date).

feed(): {"signal_id", "through", "as_of" (t), "exec" (the session whose close executes), "next", "signals",
         "sleeves": {sid: {"plan": {asset: exposure}, "idle", "books", "boost", "obs"} | {"error"}},
         "px": {symbol: close on t}, "status", "cached"} or {"error"} (the sleeves fail closed).
job(): the same, after each close in the family's job (bulk lane, beside the loop), so a pass finds it cached."""
import json
import os
import threading
from contextlib import contextmanager
from datetime import date, timedelta

from .. import calendar as cal
from ..util import write_json_atomic
from . import apex_rules as R
from . import aurelia as A

SIGNAL_ID = "apex-cursor2-ca8ac1f"
SECTORS = ("XLK", "XLF", "XLE", "XLV", "XLP", "XLI", "XLB", "XLU", "XLY")
SYMBOLS = ("^NDX", "QQQ", "^IRX", "^TNX", "^VIX", "^VIX3M", "^VIX9D", "^VIX6M", "^VXN", "IEF", "SMH", "^SOX", "GLD",
           "USO", "UUP", "BTC-USD", "GC=F", "DX-Y.NYB") + SECTORS + ("TQQQ", "BIL")
REQUIRED = ("^NDX", "QQQ", "^IRX")
# the instrument that carries each return series (its own total return is the series the source simulated)
INSTRUMENT = {"SOX": "SMH", "SMH": "SMH", "TSY": "IEF", "GOLD": "GLD", "OIL": "USO", "USD": "UUP", "BTC": "BTC/USD",
              "DXY": "UUP", "CASH": "BIL", **{s: s for s in SECTORS}}
PRICE_OF = {"BTC/USD": "BTC-USD"}
TRADED = ("QQQ", "TQQQ", "BIL", "IEF", "SMH", "GLD", "USO", "UUP", "BTC-USD") + SECTORS
_LOCK = threading.RLock()
call_with_locals, spy = R.call_with_locals, R.spy


# -- data ------------------------------------------------------------------------------------------------------
def cache_root(feeds):
    return os.path.join(os.path.dirname(feeds.hub.cache.root), "aurelia")


def load_records(root, now, symbols=SYMBOLS, getter=None):
    hist = A.History(root, getter)
    return {s: hist.load(s, now) for s in symbols}, hist.status


def future_sessions(t):
    """the desk calendar's sessions after `t` through the end of the month of the second one."""
    d1 = cal.next_trading_day(t)
    d2 = cal.next_trading_day(d1)
    out, d = [d1, d2], d2
    while True:
        n = cal.next_trading_day(d)
        if n.month != d2.month or n.year != d2.year:
            break
        out.append(n)
        d = n
    return out


def frames_for(recs, through):
    """each record -> the source's daily DataFrame, cut at `through`."""
    import pandas as pd
    out = {}
    cut = pd.Timestamp(through)
    for sym, rec in recs.items():
        if not rec or not rec.get("dates"):
            continue
        df = A.frame(rec)
        df = df[df.index <= cut]
        if not df.empty:
            out[sym] = df
    return out


@contextmanager
def bound(frames):
    """the vendored excerpts' `yahoo` module bound to these frames (one binding at a time)."""
    from ..vendor.apex import inventions as N, round3 as C, series as SER
    with _LOCK:
        y = A._Yahoo(frames)
        SER.yahoo = N.yahoo = C.yahoo = y
        try:
            yield y
        finally:
            SER.yahoo = N.yahoo = C.yahoo = None


# -- the decisions ---------------------------------------------------------------------------------------------
def mods():
    """the vendored source modules, for desk/feedlib/apex_rules."""
    from ..vendor.aurelia import features as F
    from ..vendor.apex import agents as AG, engine as E, inventions as N, round3 as C, series as SER, \
        strategies as S
    return R.Mods(S=S, N=N, C=C, SER=SER, F=F, E=E, AG=AG)


def decide_all(frames, t=None, sessions=(), only=None, series=False):
    """every sleeve's decision on the finished session t (frames through t; `sessions`: the calendar after it) or,
    series=True, on every date of the frames (the parity harness)."""
    with bound(frames):
        return R.decide_all(mods(), t, sessions, only=only, series=series)


def closes(frames, t):
    import pandas as pd
    out = {}
    for sym in TRADED:
        df = frames.get(sym)
        if df is None:
            continue
        s = df["close"][df.index <= pd.Timestamp(t)].dropna()
        if len(s):
            out[{v: k for k, v in PRICE_OF.items()}.get(sym, sym)] = float(s.iloc[-1])
    return out


def compute(recs, through, sessions=None):
    """the decisions on the last finished session (<= through) of the Nasdaq-100 total return. `sessions`: the
    sessions after it (default: the desk calendar's, through the end of the second one's month)."""
    import pandas as pd
    q = A.frame(recs["QQQ"])
    q = q[q.index <= pd.Timestamp(through)]
    if q.empty:
        raise RuntimeError("no QQQ history on or before %s" % through)
    t = q.index[-1].date()
    sessions = sessions or future_sessions(t)
    frames = frames_for(recs, t)
    dec = decide_all(frames, t, sessions)
    return {"signal_id": SIGNAL_ID, "through": str(through), "as_of": t.isoformat(),
            "exec": sessions[0].isoformat(), "next": sessions[1].isoformat(),
            "signals": dec.pop("_signals"), "sleeves": dec, "px": closes(frames, t)}


def feed(feeds, sleeve, now, arg=None):
    return decisions(cache_root(feeds), now)


def job(hub, now):
    """the family's job (desk/sleeves/families/apex.JOBS): after each close, the histories (fetched in the job's bulk
    lane) and the decisions of the session just finished, cached where feed() reads them, so the next session's
    passes find them; a later run the same evening finds them cached and returns."""
    out = decisions(os.path.join(os.path.dirname(hub.cache.root), "aurelia"), now)
    return {k: out.get(k) for k in ("as_of", "exec", "error", "cached")} | {
        "fetched": sorted(s for s, v in (out.get("status") or {}).items() if v == "fetch")}


def decisions(root, now):
    """the decisions of the last finished session on the histories at `root` (each refetched once a session
    finished after its fetch), computed once per finished session and cached beside them."""
    recs, status = load_records(root, now)
    missing = [s for s in REQUIRED if not recs.get(s)]
    if missing:
        return {"error": "no daily history for %s" % ", ".join(missing), "status": dict(status)}
    through = A.completed_through(now)
    key = "%s|%s|%s" % (SIGNAL_ID, through.isoformat(), "|".join(
        "%s:%s" % (s, (recs[s] or {}).get("dates", [""])[-1]) for s in SYMBOLS if recs.get(s)))
    cpath = os.path.join(os.path.dirname(root), "apex", "decisions.json")
    dec = None
    try:
        c = json.load(open(cpath))
        if c.get("key") == key:
            dec = c.get("dec")
    except (OSError, ValueError):
        pass
    cached = dec is not None
    if dec is None:
        try:
            dec = compute(recs, through)
        except Exception as e:
            return {"error": "%s: %s" % (type(e).__name__, str(e)[:200]), "status": dict(status)}
        os.makedirs(os.path.dirname(cpath), exist_ok=True)
        write_json_atomic(cpath, {"key": key, "dec": dec, "computed_at": float(now)})
    out = dict(dec)
    out["status"], out["cached"] = dict(status), cached
    return out


def session_of(d):
    return d if isinstance(d, date) else date.fromisoformat(str(d)[:10])


def last_session(d):
    """the newest trading session on or before `d`. completed_through returns a calendar date (the source's
    session.completed_through: the day before today while today's session runs), which is a weekend day or a holiday
    after a non-trading day: a Monday decision's history must end on Friday, not on Sunday (2026-10-19: 18 sleeves
    failed every pass with "history ends 2026-10-16; today's decision needs 2026-10-18")."""
    d = session_of(d)
    for _ in range(15):
        if cal.is_trading_day(d):
            return d
        d = d - timedelta(days=1)
    raise ValueError("no trading session in the 15 days before %s" % d.isoformat())


# -- the live option context --------------------------------------------------------------------------------------
VOL_INDEXES = ("^VXN", "^VIX", "^VIX9D", "^VIX3M", "^VIX6M", "^IRX")
CBOE_VOL = ("^VXN", "^VIX", "^VIX9D", "^VIX3M", "^VIX6M")     # CBOE's own indices, quoted on Yahoo's scale
CBOE_QUOTE = "https://cdn.cboe.com/api/global/delayed_quotes/quotes/_%s.json"
DIV = 0.0055                                # the source's QQQ dividend yield (research/run_options_*.py)


def cboe_level(sym, today, fetch=None):
    """CBOE's public delayed quote (~15 minutes) of one of its volatility indices: today's level, else None (a
    quote whose last trade is not today's is yesterday's close)."""
    if fetch is None:
        from ..data.http import get as fetch
    try:
        d = fetch(CBOE_QUOTE % sym.lstrip("^"), timeout=30)
    except Exception:                                   # noqa: BLE001 -- the last close stands in
        return None
    q = (d or {}).get("data") or {}
    px = q.get("current_price")
    if px and float(px) > 0 and str(q.get("last_trade_time") or "")[:10] == today.isoformat():
        return float(px)
    return None


def third_friday(y, m):
    d = date(y, m, 1)
    return d + timedelta(days=(4 - d.weekday()) % 7 + 14)


def listing_of(rows, today):
    """the chain's monthly expirations (third Friday, or the session before it when that Friday is a holiday), keyed
    by their third Friday: {"expiries": [third Fridays], "actual": {tf: expiration}, "strikes": {(exp, type):
    [strikes]}, "occ": {(exp, type, strike): occ}, "quotes": {occ: (bid, ask)}}."""
    out = {"expiries": [], "actual": {}, "strikes": {}, "occ": {}, "quotes": {}}
    for r in rows or []:
        try:
            exp = date.fromisoformat(str(r["expiration"])[:10])
            k = float(r["strike"])
        except (KeyError, TypeError, ValueError):
            continue
        tf = third_friday(exp.year, exp.month)
        if not (exp == tf or (exp == tf - timedelta(days=1) and not cal.is_trading_day(tf))):
            continue
        if exp < today:
            continue
        typ = r.get("type")
        out["actual"][tf.isoformat()] = exp.isoformat()
        out["strikes"].setdefault((exp.isoformat(), typ), set()).add(k)
        out["occ"][(exp.isoformat(), typ, k)] = r["symbol"]
        out["quotes"][r["symbol"]] = (r.get("bid"), r.get("ask"))
    out["expiries"] = sorted(out["actual"])
    out["strikes"] = {kk: sorted(v) for kk, v in out["strikes"].items()}
    return out


def today_frames(frames, today, S, levels):
    """the finished frames + today's row: QQQ at the live price S (its adjusted close carried by the same ratio),
    the volatility indices / the T-bill rate at their live levels (Yahoo's today, else CBOE's delayed quote of its
    own indices; else their last close), everything else flat."""
    import pandas as pd
    ts = pd.Timestamp(today)
    out = {}
    for sym, df in frames.items():
        last = df.iloc[-1]
        c, a = float(last["close"]), float(last["adj_close"])
        if sym == "QQQ":
            c, a = float(S), a * float(S) / c
        elif levels.get(sym):
            c = a = float(levels[sym])
        row = pd.DataFrame({"open": c, "high": c, "low": c, "close": c, "volume": 0.0, "adj_close": a},
                           index=pd.DatetimeIndex([ts], name="date")).astype("float64")
        out[sym] = pd.concat([df[df.index < ts], row])
    return out


SIGNAL_FIELDS = ("trend", "vol", "L", "dd252", "vol30", "vol30_p80", "hi10_prior", "level", "apex_ret")


def _plan_of(calls, t):
    """planned_position on a strategy's last simulator run (the source desk's plan for the next close)."""
    from ..vendor.apex import agents as AG
    a, kw, out = calls[-1]
    tgt = a[0].reindex(out.index)
    return AG.planned_position(float(tgt.loc[t]), float(out["position"].loc[t]), kw.get("band", 0.20))


def option_context(recs, through, today, S, levels, chain_rows):
    """the source's option inputs for a decision today (build_inputs, as research/run_options_*.py built them):
    the signals on the finished data through `through` (what the source desk's live runtime read), today's row —
    the QQQ price, the T-bill rate, the month start — and the surface at today's live levels from build_inputs on
    the frames with today's row; the cores' plans for today's close. {"x", "m" (finished), "surface" (today's),
    "price", "frames" (with today), "sig", "plans", "listing"}."""
    import dataclasses
    import numpy as np
    import pandas as pd
    from ..vendor.apex import opt_strategies as O, series as SER, strategies as S_, surface as SURF
    fin = frames_for(recs, through)
    now_frames = today_frames(fin, today, S, levels)
    prm = SURF.SurfaceParams.load()
    need = last_session(through)
    with bound(fin):
        m = SER.ndx_market()
        if m.index[-1] != pd.Timestamp(need):
            raise RuntimeError("the Nasdaq-100 history ends %s; today's decision needs %s" % (m.index[-1].date(),
                                                                                               need))
        t = m.index[-1]
        surf_c = SURF.Surface(m.index, "^VXN", prm)
        with spy((S_,), "simulate") as (calls, _):
            x_c, loc = call_with_locals(O.build_inputs, m, fin["QQQ"]["close"], surf_c, DIV)
        sig = loc["sig"]
        apex50 = _plan_of(calls, t)                                    # S.run(L, m, APEX_50F)
        with spy((S_,), "simulate") as (calls, _):
            S_.run(S_.apex_target(sig), m)                             # APEX-30 (E4's core)
        apex30 = _plan_of(calls, t)
    with bound(now_frames):
        m_t = SER.ndx_market()
        surf_t = SURF.Surface(m_t.index, "^VXN", prm)
        x_t = O.build_inputs(m_t, now_frames["QQQ"]["close"], surf_t, DIV)
    x = dataclasses.replace(x_t, **{f: np.concatenate([getattr(x_c, f), getattr(x_t, f)[-1:]]) for f in SIGNAL_FIELDS})
    return {"x": x, "m": m, "price": now_frames["QQQ"]["close"], "surface": surf_t, "frames": now_frames, "sig": sig,
            "plans": {"apex50f": apex50, "apex30": apex30}, "listing": listing_of(chain_rows, today),
            "chain": chain_rows, "px": closes(fin, through)}


def live_context(feeds, sleeve, now, arg=None):
    today = cal._as_date(now)
    if not cal.is_trading_day(today) or now >= cal.session_close(today) or now < cal.session_open(today):
        return {"error": "no open session"}
    root = cache_root(feeds)
    recs, status = load_records(root, now)
    missing = [s for s in REQUIRED + ("^VXN",) if not recs.get(s)]
    if missing:
        return {"error": "no daily history for %s" % ", ".join(missing), "status": dict(status)}
    hub = feeds.hub
    levels = {}
    try:
        yq = hub.quotes("yahoo", list(VOL_INDEXES)) or {}
    except Exception:
        yq = {}
    for s in VOL_INDEXES:
        q = yq.get(s) or {}
        if s not in CBOE_VOL and q.get("src") == "cboe_delayed":
            continue                    # the hub's fallback for a quote Yahoo did not serve: Cboe quotes the T-bill yield
                                        # x 10 (IRX 40.7 for 4.07%; the 2026-10-16 decision priced at 40.7%): last close
        if q.get("last") and str(q.get("session") or "")[:10] == today.isoformat():
            levels[s] = float(q["last"])
    for s in CBOE_VOL:                                  # Yahoo serves some of CBOE's indices only after the close
        if s not in levels:
            v = cboe_level(s, today)
            if v:
                levels[s] = v
    q = (hub.quotes(hub.equity_source(), ["QQQ"]) or {}).get("QQQ") or {}
    bid, ask, last = q.get("bid"), q.get("ask"), q.get("last")
    S = (float(bid) + float(ask)) / 2 if bid and ask and float(ask) >= float(bid) > 0 else (float(last) if last else None)
    if not S:
        return {"error": "no live QQQ quote", "status": dict(status)}
    rows = hub.options.chain("QQQ") if getattr(hub, "options", None) is not None else None
    if not rows:
        return {"error": "no QQQ option chain", "status": dict(status)}
    through = A.completed_through(now)
    try:
        ctx = option_context(recs, through, today, S, levels, rows)
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, str(e)[:200]), "status": dict(status)}
    ctx.update(session=today.isoformat(), as_of=through.isoformat(), S=S, levels=levels, status=dict(status))
    return ctx


__all__ = ["feed", "compute", "decide_all", "frames_for", "future_sessions", "bound", "spy", "call_with_locals",
           "INSTRUMENT", "PRICE_OF", "SYMBOLS", "SIGNAL_ID"]
