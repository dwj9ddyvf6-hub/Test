"""Inputs the Aurelia source desk's free-paper option descendants read but never produced, built from the desk's own
data (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e: free_options.run() attached only {"hedge": ...} as the
package and called evaluate() with no traded quote, cash 0 and events [] — the descendants waited on inputs nothing
wrote: own_iv_forecast, the straddle and pair legs, wheel_contract, a release calendar).

Every contract comes from the desk's option chain (desk/data/options.py: CBOE's public delayed chain, or Alpaca's
indicative snapshots with keys) fetched for the decision (a receipt at most FRESH_S old). Each leg carries the
chain's own quote time as source_at and the fetch as received_at, so the source's freshness rules (vendored
quote_freshness: source <= 90 s, receipt <= 30 s, 2 s future tolerance, legs within 30 s of each other) judge it
unchanged; a producer offers a contract only when it passes them at the decision moment.

  forecast(closes, horizon)  the source's own causal realized-volatility forecaster, unchanged: desk/features.py
        har_vol_forecast (vendored byte-exact as desk/vendor/aurelia/features.py) — HAR-RV (Corsi 2009): OLS of the
        next `horizon` sessions' mean squared daily log return on its daily, 5-day and 22-day means, an expanding
        window refit every 21 sessions once 504 sessions exist (EWMA lambda 0.94 before the first fit), the
        annualized forecast clipped to 10%-150% — on the completed daily closes through the last finished session.
  straddle(rows, expiration, spot)  the ATM straddle: the call and the put of one expiry at the listed strike
        nearest the spot whose two quotes are both two-sided (bid > 0, ask >= bid).
  own_iv(...)     FREE_OPT_OWN_IV_V1's package: the straddle on the nearest 21-35 DTE expiry at least 7 calendar
        days past the ten-session exit (FWD_RESEARCH_OWN_IV_V1), bought when the forecast over the sessions to that
        expiry exceeds the straddle's indicative IV (the mean of its two legs' IV) by 2 points; exit_at 5 minutes
        before the close of the 10th session counting the entry's (R19 _exit_session); 1 package; max loss = the
        natural debit (both asks) x 100, also its risk cap (one open package per book).
  release(...)    FREE_OPT_RELEASE_V1's package: on a session with a verified public event (the release calendar,
        desk/feedlib/release_calendar.py), the ATM straddle on the nearest expiry after the session following the
        event's; exit_at 5 minutes after the open of that following session ("the session after the event").
  pair(...)       FREE_OPT_PAIR_V1's package on the frozen SPY/QQQ hedge (desk/feedlib/aurelia_options.py): when its
        residual z leaves the +-2 band, both exposures toward the residual's mean — z > 2 (QQQ rich): buy the QQQ ATM
        put and the SPY ATM call; z < -2: the QQQ ATM call and the SPY ATM put — on their nearest common 30-60 DTE
        expiry (the R17 pair's option window, FWD_RESEARCH_PAIR_V1) at least 7 days past the ten-session exit; 1 QQQ
        contract and round(beta x QQQ delta-dollars / SPY delta-dollars) SPY contracts (at least 1); one package per
        signal session; exit_at the 10th session, 5 minutes before the close.
  tail(...)       FREE_OPT_TAIL_V1's put: |delta| .50-.65, 21-35 DTE, expiry at least 7 calendar days past the
        five-session exit; the nearest expiry, then the delta nearest .575, then the strike nearest the spot (the
        R19 long-put selector, OPT_PEAD_* rule).
  wheel(..., right)  FREE_OPT_WHEEL_V1's cash-secured put / covered call: the corpus's 30-delta weekly SPY wheel —
        the nearest expiry 7-14 DTE, then |delta| nearest .30, then the strike nearest the spot.

Named divergences (the source defines none of these): every contract rule above; the forecast horizon is the
straddle's sessions to expiry (the source's own analyst forecast 5 sessions); the IV is the chain's per-contract
implied volatility (the source's probe read the indicative snapshot's impliedVolatility)."""
import math
from datetime import date, datetime, timedelta, timezone

from .. import calendar as cal
from ..util import ET
from ..vendor.aurelia.quote_freshness import assess

FRESH_S = 20.0                # a decision's chain receipt is at most this old (the source's receipt cap is 30 s)
GAP = 0.02                    # own-IV: the forecast exceeds indicative IV by 2 vol points
HOLD = {"own_iv": 10, "pair": 10, "tail": 5}
EXIT_BUFFER_DAYS = 7
OWN_IV_DTE, PAIR_DTE, TAIL_DTE, WHEEL_DTE = (21, 35), (30, 60), (21, 35), (7, 14)
TAIL_DELTA, WHEEL_DELTA = (0.50, 0.65), 0.30
EXIT_BEFORE_CLOSE_S, EXIT_AFTER_OPEN_S = 300, 300
RELEASE_DTE_MAX = 45
_MEMO = {}


def iso(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


def two_sided(r):
    try:
        bid, ask = float(r.get("bid") or 0), float(r.get("ask") or 0)
    except (TypeError, ValueError):
        return False
    return bid > 0 and ask >= bid


def _delta(r):
    try:
        d = float(r.get("delta"))
    except (TypeError, ValueError):
        return None
    return abs(d) if math.isfinite(d) and d != 0 else None


def nth_session(session, n):
    """the n-th trading session counting `session` (or the next trading day) as the first."""
    d = cal._as_date(session)
    if not cal.is_trading_day(d):
        d = cal.next_trading_day(d)
    return cal.next_trading_day(d, n - 1) if n > 1 else d


def exit_before_close(session, n):
    """5 minutes before the close of the n-th session counting `session` as the first (R19 session exits)."""
    return iso(cal.session_close(nth_session(session, n)) - EXIT_BEFORE_CLOSE_S)


def sessions_through(session, expiration):
    """trading sessions from `session` through `expiration`, both counted."""
    d0, e = cal._as_date(session), cal._as_date(expiration)
    return (1 if cal.is_trading_day(d0) else 0) + cal.trading_days_between(d0, e)


def _dte(r, today):
    return (date.fromisoformat(r["expiration"]) - cal._as_date(today)).days


def pick_expiry(rows, today, dte, not_before=None):
    """the nearest expiration with dte[0] <= days <= dte[1] (calendar days from today), on or after not_before."""
    for e in sorted({r["expiration"] for r in rows or ()}):
        days = (date.fromisoformat(e) - cal._as_date(today)).days
        if dte[0] <= days <= dte[1] and (not not_before or e >= str(not_before)):
            return e
    return None


def straddle(rows, expiration, spot):
    """(call, put) of `expiration` at the listed strike nearest `spot` with both quotes two-sided; None."""
    if not spot:
        return None
    calls = {r["strike"]: r for r in rows or () if r["expiration"] == expiration and r["type"] == "call" and two_sided(r)}
    puts = {r["strike"]: r for r in rows or () if r["expiration"] == expiration and r["type"] == "put" and two_sided(r)}
    both = sorted(set(calls) & set(puts), key=lambda k: (abs(k - float(spot)), k))
    return (calls[both[0]], puts[both[0]]) if both else None


def leg(r, side, qty, received):
    """a package leg in the source's shape (option_packages: symbol, side, quantity, bid, ask, source_at,
    received_at; free_options: right, underlying)."""
    return {"symbol": r["symbol"], "right": r["type"], "side": side, "quantity": int(qty), "bid": float(r["bid"]),
            "ask": float(r["ask"]), "source_at": iso(r["t"]), "received_at": iso(received),
            "underlying": r.get("underlying") or r["symbol"][:-15], "strike": r["strike"],
            "expiration": r["expiration"], "iv": r.get("iv"), "delta": r.get("delta")}


def fresh(legs, moment):
    """the source's freshness verdict on the legs at the decision moment (quote_freshness.assess + the 30 s
    cross-leg skew): None when every leg may be used, else the first block."""
    m = datetime.fromtimestamp(float(moment), tz=timezone.utc)
    for x in legs:
        block = assess(m, x.get("source_at"), x.get("received_at"))["block"]
        if block:
            return block
    stamps = [datetime.fromisoformat(x["source_at"]).timestamp() for x in legs]
    if stamps and max(stamps) - min(stamps) > 30:
        return "cross-leg timestamp skew exceeds 30 seconds"
    return None


def forecast(closes, horizon):
    """the source's HAR-RV forecast (annualized) of the next `horizon` sessions after the last close; None with
    fewer than 30 closes."""
    c = [float(x) for x in closes or () if x]
    if len(c) < 30 or int(horizon) < 1:
        return None
    key = (len(c), c[0], c[-1], round(sum(c), 6), int(horizon))
    if key not in _MEMO:
        import pandas as pd
        from ..vendor.aurelia import features as F
        r = pd.Series(c).pct_change().dropna().reset_index(drop=True)
        v = float(F.har_vol_forecast(r, horizon=int(horizon)).iloc[-1])
        if len(_MEMO) > 64:
            _MEMO.clear()
        _MEMO[key] = v if math.isfinite(v) else None
    return _MEMO[key]


def _straddle_package(client, book, rows, expiration, spot, received, exit_at, moment, extra=None):
    pair = straddle(rows, expiration, spot)
    if pair is None:
        return None, "no two-sided ATM straddle on %s" % expiration
    legs = [leg(pair[0], "buy", 1, received), leg(pair[1], "buy", 1, received)]
    block = fresh(legs, moment)
    if block:
        return None, "chain quote: " + block
    debit = round((legs[0]["ask"] + legs[1]["ask"]) * 100, 2)
    pkg = dict({"client_order_id": client, "book_id": book, "execution": "broker_mleg", "shape": "straddle",
                "legs_required": 2, "result_series": "broker_paper", "max_loss": debit, "risk_cap": debit,
                "exit_at": exit_at, "legs": legs}, **(extra or {}))
    return pkg, None


def own_iv(rows, received, spot, session, closes, moment):
    """-> {"package" | None, "forecast", "iv", "expiration", "horizon", "reason"}."""
    out = {"package": None, "forecast": None, "iv": None, "expiration": None, "horizon": None}
    exit_s = nth_session(session, HOLD["own_iv"])
    exp = pick_expiry(rows, session, OWN_IV_DTE, (exit_s + timedelta(days=EXIT_BUFFER_DAYS)).isoformat())
    if exp is None:
        return dict(out, reason="no 21-35 DTE expiry 7 days past the ten-session exit")
    pair = straddle(rows, exp, spot)
    if pair is None:
        return dict(out, expiration=exp, reason="no two-sided ATM straddle on %s" % exp)
    ivs = [float(r["iv"]) for r in pair if r.get("iv") and float(r["iv"]) > 0]
    if len(ivs) < 2:
        return dict(out, expiration=exp, reason="the straddle's quotes carry no implied volatility")
    iv, h = sum(ivs) / 2.0, sessions_through(session, exp)
    f = forecast(closes, h)
    out.update(iv=round(iv, 6), expiration=exp, horizon=h, forecast=None if f is None else round(f, 6))
    if f is None:
        return dict(out, reason="fewer than 30 completed daily closes for the forecast")
    if f - iv < GAP:
        return dict(out, why="the forecast does not exceed indicative IV by 2 points",
                    reason="forecast %.2f%% does not exceed indicative IV %.2f%% by 2 points" % (100 * f, 100 * iv))
    pkg, why = _straddle_package("own-iv-%s" % session, "FREE_OPT_OWN_IV_V1", rows, exp, spot, received,
                                 exit_before_close(session, HOLD["own_iv"]), moment,
                                 {"forecast": round(f, 6), "iv": round(iv, 6), "horizon_sessions": h})
    return dict(out, package=pkg, why=why or "the forecast exceeds indicative IV by 2 points",
                reason=why or "forecast %.2f%% exceeds indicative IV %.2f%% by %.2f points"
                % (100 * f, 100 * iv, 100 * (f - iv)))


def todays_events(events, session):
    """the verified events whose trading session is `session` (the source's evaluate() matches event["session"]
    to the decision's date)."""
    return [e for e in events or () if e.get("session") == session and e.get("verified")]


def release(rows, received, spot, session, events, moment):
    """-> {"package" | None, "events", "expiration", "reason"}."""
    today = todays_events(events, session)
    out = {"package": None, "events": [e.get("name") for e in today], "expiration": None}
    if not today:
        return dict(out, reason="no verified public event is loaded for %s" % session)
    after = cal.next_trading_day(session)
    exp = pick_expiry(rows, session, (1, RELEASE_DTE_MAX), (after + timedelta(days=1)).isoformat())
    if exp is None:
        return dict(out, reason="no expiry after %s within %d days" % (after.isoformat(), RELEASE_DTE_MAX))
    exit_at = iso(cal.session_open(after) + EXIT_AFTER_OPEN_S)
    pkg, why = _straddle_package("release-%s" % session, "FREE_OPT_RELEASE_V1", rows, exp, spot, received, exit_at,
                                 moment, {"events": [{k: e.get(k) for k in ("name", "release_at", "source")}
                                                     for e in today]})
    return dict(out, package=pkg, expiration=exp,
                reason=why or "verified %s: straddle on %s" % (", ".join(out["events"]), exp))


def _atm(rows, expiration, spot, right):
    cand = [r for r in rows or () if r["expiration"] == expiration and r["type"] == right and two_sided(r)]
    return min(cand, key=lambda r: (abs(r["strike"] - float(spot)), r["strike"])) if cand and spot else None


def pair(chains, hedge, session, moment):
    """chains: {"SPY": (rows, received, spot), "QQQ": (...)}. -> {"package" | None, "reason"}."""
    if not hedge or not hedge.get("signal"):
        return {"package": None, "reason": (hedge or {}).get("reason") or "no frozen hedge"}
    z, beta = float(hedge["z"]), float(hedge["beta"])
    if any((chains.get(u) or (None,))[0] is None for u in ("SPY", "QQQ")):
        return {"package": None, "reason": "the SPY or QQQ chain was not fetched"}
    (rs, at_s, spot_s), (rq, at_q, spot_q) = chains["SPY"], chains["QQQ"]
    exit_s = nth_session(session, HOLD["pair"])
    common = sorted({r["expiration"] for r in rs} & {r["expiration"] for r in rq})
    exp = pick_expiry([{"expiration": e} for e in common], session, PAIR_DTE,
                      (exit_s + timedelta(days=EXIT_BUFFER_DAYS)).isoformat())
    if exp is None:
        return {"package": None, "reason": "no common 30-60 DTE expiry 7 days past the ten-session exit"}
    q_right, s_right = ("put", "call") if z > 0 else ("call", "put")
    q, s = _atm(rq, exp, spot_q, q_right), _atm(rs, exp, spot_s, s_right)
    if q is None or s is None:
        return {"package": None, "reason": "no two-sided ATM %s on QQQ or %s on SPY for %s" % (q_right, s_right, exp)}
    dq, ds = _delta(q) or 0.5, _delta(s) or 0.5
    n_spy = max(1, int(round(abs(beta) * float(spot_q) * dq / (float(spot_s) * ds))))
    legs = [leg(q, "buy", 1, at_q), leg(s, "buy", n_spy, at_s)]
    block = fresh(legs, moment)
    if block:
        return {"package": None, "reason": "chain quote: " + block}
    cost = round(sum(x["ask"] * x["quantity"] for x in legs) * 100, 2)
    sig = hedge.get("signal_session") or session
    pkg = {"client_order_id": "pair-%s" % sig, "book_id": "FREE_OPT_PAIR_V1", "execution": "broker_coordinated",
           "shape": "cross_underlying_pair", "legs_required": 2, "result_series": "broker_paper", "max_loss": cost,
           "risk_cap": cost, "exit_at": exit_before_close(session, HOLD["pair"]), "hedge": hedge,
           "hedge_frozen": True, "legs": legs}
    return {"package": pkg, "reason": "residual z %.2f outside +-2: buy QQQ %s x1, SPY %s x%d (beta %.3f) on %s"
            % (z, q_right, s_right, n_spy, beta, exp)}


def quote_of(r, received):
    """a contract's indicative quote in the shape evaluate() reads ({"symbol","bp","ap","t","received_at"}), with
    its strike."""
    return {"symbol": r["symbol"], "bp": float(r["bid"]), "ap": float(r["ask"]), "bid": float(r["bid"]),
            "ask": float(r["ask"]), "t": iso(r["t"]), "received_at": iso(received), "strike": r["strike"],
            "expiration": r["expiration"], "delta": r.get("delta"), "iv": r.get("iv")}


def _by_delta(cands, today, target, spot):
    return min(cands, key=lambda r: (r["expiration"], abs(_delta(r) - target), abs(r["strike"] - float(spot or 0)),
                                     r["symbol"]))


def tail(rows, received, spot, session):
    """FREE_OPT_TAIL_V1's put quote; None without a qualifying contract."""
    not_before = (nth_session(session, HOLD["tail"]) + timedelta(days=EXIT_BUFFER_DAYS)).isoformat()
    cand = [r for r in rows or () if r["type"] == "put" and two_sided(r) and _delta(r) is not None
            and TAIL_DELTA[0] <= _delta(r) <= TAIL_DELTA[1] and TAIL_DTE[0] <= _dte(r, session) <= TAIL_DTE[1]
            and r["expiration"] >= not_before]
    return quote_of(_by_delta(cand, session, sum(TAIL_DELTA) / 2, spot), received) if cand else None


def wheel(rows, received, spot, session, right):
    """FREE_OPT_WHEEL_V1's cash-secured put (right "put") or covered call ("call") quote; None without one."""
    cand = [r for r in rows or () if r["type"] == right and two_sided(r) and _delta(r) is not None
            and WHEEL_DTE[0] <= _dte(r, session) <= WHEEL_DTE[1]]
    return quote_of(_by_delta(cand, session, WHEEL_DELTA, spot), received) if cand else None
