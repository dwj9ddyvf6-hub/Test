"""The market strip and each card's options block (PLAN.md Phase 2, stream s3): the session's positioning, range,
day type, fear and index agreement in one calm line, and a priced way to express a listed long.

Inputs are the desk's own: the session's options gather (desk/terminal/optnews.py: Alpaca's indicative chains with
greeks, contracts with open interest; never CBOE options data; SqueezeMetrics and FINRA are allowed since 2026-10-27
but not read here), Cboe's daily VIX closes (market.vix_doc, approved 2026-10-21) and the hub's daily bars. Nothing here fetches; every block carries
status ok / stale / no_data with a reason, an as-of and its method, and never a currency sign (the page refuses one).

  gex      net dealer gamma per 1% move, SpotGamma's published convention: gamma x OI x 100 x S^2 x 0.01, calls +,
           puts - (dealers long the calls, short the puts: a convention, said once on How it works). Walls: the strike
           with the most call gamma and the most put gamma. Flip: the price where the re-priced net gamma (Black-Scholes
           gamma from each contract's IV) crosses zero, nearest the spot within +-10%. Regime word: Dampening (net > 0),
           Amplifying (net < 0); the shown word changes only after two consecutive gathers agree (hysteresis).
  move     the expected one-day move: VIX / 15.87 (sqrt 252) for the S&P (about 81% of days stay inside it) beside the
           68% band, the HAR forecast x 0.88; the 30-day ATM IV / 15.87 for a name; the
           funded range at minute t of 390 is EM x sqrt(t/390).
  day      Pin / Grind / Volatile from the gamma sign, the gap and the range so far against the expected move; logged
           once a session (state/terminal/daytype.jsonl) and graded on the closed session.
  fear     Calm / Normal / Stressed from the VIX's band (<15, 15-18.5, >18.5) and a HAR forecast of the S&P's realized
           volatility against the VIX; the "stress" word, never called a fear day. The fear-day flag is the Buy List's
           (desk/picker/fearday.market_state: SPY -1% or under its 50-day), the same one the page header reads.
  agree    SPY and QQQ today: both up / both down / split / quiet (a move under a quarter of the expected move).
  options  per listed long: IV rank (a year of stored IV30), IV / RV20, put/call by volume and OI with its change
           since the last stored session, the at-the-money spread, a T1 beyond two expected moves flagged, and two
           priced structures from the chain's own quotes (long call, call debit spread): debit, max loss, max gain,
           breakeven and the MEASURED share of past windows that touched T1 (touch_rate; not measured without enough bars)."""
import json
import math
import os
from datetime import date

from .. import calendar as cal
from ..morgue import bs as _bs
from ..util import read_json, write_json_atomic
from . import vendor_ext as vx
from .engine import HAR_STOP                # HAR x0.9: the scale for a stop or range taken from a HAR volatility

FUNDS = ("SPY", "QQQ", "IWM")
SQRT252 = 15.874507866387544
HAR_BAND = 0.88                             # HAR x0.88 is a 68% one-day band (docs/research/EVIDENCE.md AD-56)
# the one place the 81 lives: VIX / 15.87 is an ~81% band, not 68% (docs/research/EVIDENCE.md AD-55, SPY and QQQ daily 2010
# to 2026-10, holdout 2020+). A fixed study result, shipped as em_inside_pct and quoted in the method text below.
EM_INSIDE = 81
TOUCH_MIN_N = 60                            # fewest past windows behind a touch rate before it is shown
VIX_BANDS = (15.0, 18.5)                    # calm below, stressed above
GRID = 0.10                                 # the flip is looked for within +-10% of the spot
STEP = 0.0025
HOLD_READS = 2                              # the regime word changes after two consecutive gathers agree
QUIET = 0.25                                # an index move under a quarter of the expected move is quiet
STATE_PATH = os.path.join("state", "terminal", "strip.json")
DAY_LOG = os.path.join("state", "terminal", "daytype.jsonl")
RATE = 0.04
IVR_N = 252                                 # IV rank waits for a year of stored IV30 (read/optnews.py IV_RANK_N)


def _n(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _r(x, k=4):
    return None if x is None else round(x, k)


def no(reason, **kw):
    return dict({"status": "no_data", "reason": reason}, **kw)


# ---- Black-Scholes ---------------------------------------------------------------------------------------------------

def _N(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _d1(S, K, T, iv, r=RATE):
    return (math.log(S / K) + (r + 0.5 * iv * iv) * T) / (iv * math.sqrt(T))


def bs_gamma(S, K, T, iv, r=RATE):
    """Black-Scholes gamma at no dividend yield: the Morgue Engine's (desk/morgue/bs.py), one gamma for the strip and the Map"""
    return _bs.gamma(S, K, T, iv, r, 0.0)


def bs_call(S, K, T, iv, r=RATE):
    if T <= 0 or iv <= 0:
        return max(S - K, 0.0)
    d1 = _d1(S, K, T, iv, r)
    return S * _N(d1) - K * math.exp(-r * T) * _N(d1 - iv * math.sqrt(T))


def touch_rate(bars, up_pct, days, min_n=TOUCH_MIN_N):
    """the MEASURED chance a name's high reaches `up_pct`% above a close inside the next `days` sessions, over every
    window of its own daily bars (the formula 2 N(-z) it replaces overstated it): {"rate", "n", "days"}, or None
    ("not measured") with no bars, no target or fewer than min_n windows"""
    up, days = _n(up_pct), int(days or 0)
    if up is None or days < 1 or not bars:
        return None
    rows = [(_n(b.get("c")), _n(b.get("h"))) for b in bars if isinstance(b, dict)]
    rows = [(c, h) for c, h in rows if c and h]
    n = len(rows) - days
    if n < max(min_n, 1):
        return None
    hit = sum(1 for i in range(n) if max(h for _, h in rows[i + 1:i + 1 + days]) >= rows[i][0] * (1 + up / 100.0))
    return {"rate": round(hit / n, 3), "n": n, "days": days}


# ---- gamma exposure --------------------------------------------------------------------------------------------------

def contract_gex(gamma, oi, spot, kind):
    """one contract's dollar gamma per 1% move (SpotGamma's worked example: spot 200, gamma 0.02, 1,000 contracts ->
    800,000): gamma x OI x 100 x S^2 x 0.01, calls +, puts -"""
    return (1.0 if kind == "call" else -1.0) * gamma * oi * 100.0 * spot * spot * 0.01


def _net(rows, S):
    return sum(contract_gex(bs_gamma(S, r["k"], r["t"], r["iv"]), r["oi"], S, r["type"]) for r in rows)


def profile(rows, spot):
    """rows: [{type, k, t (years), oi, iv}] -> {net, call_wall, put_wall, flip, n} (net at the spot from the
    contracts' IVs, so walls, net and flip use one gamma); None without a usable row"""
    rows = [r for r in rows if r.get("oi") and r["oi"] > 0 and r.get("iv") and 0 < r["iv"] <= 5 and r.get("t", 0) > 0
            and r.get("k") and r["k"] > 0 and r.get("type") in ("call", "put")]
    if not rows or not spot or spot <= 0:
        return None
    by = {}
    for r in rows:
        g = contract_gex(bs_gamma(spot, r["k"], r["t"], r["iv"]), r["oi"], spot, r["type"])
        e = by.setdefault(r["k"], [0.0, 0.0])
        e[0 if r["type"] == "call" else 1] += g
    call_wall = max(by, key=lambda k: by[k][0]) if any(v[0] > 0 for v in by.values()) else None
    put_wall = min(by, key=lambda k: by[k][1]) if any(v[1] < 0 for v in by.values()) else None
    net = sum(v[0] + v[1] for v in by.values())
    steps = int(round(GRID / STEP))
    grid = [spot * (1 + i * STEP) for i in range(-steps, steps + 1)]
    vals = [_net(rows, s) for s in grid]
    flips = []
    for i in range(len(grid) - 1):
        a, b = vals[i], vals[i + 1]
        if a == 0:
            flips.append(grid[i])
        elif a * b < 0:
            flips.append(grid[i] + (grid[i + 1] - grid[i]) * (-a) / (b - a))
    flip = min(flips, key=lambda x: abs(x - spot)) if flips else None
    return {"net": net, "call_wall": call_wall, "put_wall": put_wall, "flip": flip, "n": len(rows)}


NO_READ = "no options chain read yet today"


def morgue_gex(root, fund, now):
    """the fund's gamma block from the Morgue Engine's Map (desk/morgue: Alpaca's chain and prior-close open interest read at
    about 08:46 ET, before the day's options gather), or None without a card of the current session: the strip's own gather
    runs once a session at 14:00 ET, so until then, and on any day it fails, the Map answers. No hysteresis: one read."""
    from ..morgue import edition as me
    card = me.gex_card(root, fund, now)
    if not isinstance(card, dict) or card.get("status") != "ok" or card.get("net_gex_b") is None:
        return None
    net = card["net_gex_b"]
    out = {"status": "ok", "word": "Dampening" if net > 0 else "Amplifying", "raw": "Dampening" if net > 0 else "Amplifying",
            "net": _r(net, 3), "flip_pct": card.get("flip_distance_pct"), "flip_sigma": None,
            "call_wall_pct": card.get("call_wall_pct"), "put_wall_pct": card.get("put_wall_pct"),
            "as_of": card.get("as_of"), "contracts": card.get("contracts_used"), "oi_date": card.get("oi_date"),
            "method": "Morgue Map: SpotGamma convention, Alpaca greeks, open interest from the prior close, read before the open"}
    if card.get("flip") is None:
        out["flip_reason"] = card.get("flip_reason") or "no zero crossing within 20% of the price"
    return out


def squeeze_gex(root, fund, now):
    """SPY only: SqueezeMetrics' SPX dealer gamma of the prior close, the last link of the gamma chain (chain read, Morgue Map,
    this). The S&P 500's measure stands for SPY alone; QQQ and IWM have none. Positive = dealers long gamma (Dampening);
    net is the file's gex in $B per 1% move. No walls or flip: the file has neither."""
    if fund != "SPY":
        return None
    from ..data import squeezemetrics as sq
    r = sq.latest(root, now)
    if r.get("status") not in ("ok", "stale"):
        return None
    word = "Dampening" if r["gex"] > 0 else "Amplifying"
    out = {"status": r["status"], "word": word, "raw": word, "net": _r(r["gex"] / 1e9, 3), "flip_pct": None, "flip_sigma": None,
           "call_wall_pct": None, "put_wall_pct": None, "as_of": r["as_of"], "contracts": None, "oi_date": None,
           "label": sq.LABEL, "source": sq.SOURCE, "delay": sq.DELAY, "dix": _r(r["dix"], 4),
           "method": sq.LABEL + ": dealer gamma of the S&P 500 options, a day behind", "flip_reason": "the SqueezeMetrics file has no strikes"}
    if r.get("reason"):
        out["reason"] = r["reason"]
    return out


def no_chain(root, fund, now, why):
    """a fund with no chain read of its own and no Map card: SPY's SqueezeMetrics read, else an honest no_data"""
    return squeeze_gex(root, fund, now) or no(why)


def settle(prev, raw, need=HOLD_READS):
    """hysteresis: {word, pending, count} -> the next state for a raw word; the shown word changes only after `need`
    consecutive reads of a new word"""
    prev = prev if isinstance(prev, dict) else {}
    word = prev.get("word")
    if word is None:
        return {"word": raw, "pending": None, "count": 0}
    if raw == word:
        return {"word": word, "pending": None, "count": 0}
    count = prev.get("count", 0) + 1 if prev.get("pending") == raw else 1
    if count >= need:
        return {"word": raw, "pending": None, "count": 0}
    return {"word": word, "pending": raw, "count": count}


# ---- expected move, day type, fear, agreement -------------------------------------------------------------------------

def em_pct(vol, frac=False):
    """the expected one-day move in % from an annualized vol in points (the VIX) or, frac, a fraction (an IV30):
    vol / sqrt 252"""
    v = _n(vol)
    if v is None or v <= 0:
        return None
    return (v * 100.0 if frac else v) / SQRT252


def funded(em, minute):
    """the share of the day's expected move funded by minute `minute` of 390"""
    if em is None or minute is None:
        return None
    return em * math.sqrt(max(0.0, min(390.0, minute)) / 390.0)


def day_type(net, em, gap, rng):
    """Pin / Grind / Volatile: amplifying gamma with a gap or range of most of a day's expected move is Volatile;
    dampening gamma with a small gap and range is Pin; the rest Grind (all in %)"""
    if em is None or em <= 0 or gap is None or rng is None:
        return None
    if (net is not None and net < 0 and (abs(gap) >= 0.5 * em or rng >= 0.8 * em)) or rng >= 1.2 * em:
        return "Volatile"
    if net is not None and net > 0 and abs(gap) < 0.25 * em and rng < 0.5 * em:
        return "Pin"
    return "Grind"


def grade_day(em, o, h, l, c):
    """the closed session's own type, for grading a logged call: Pin (range under 0.6 EM, open-to-close under 0.3
    EM), Volatile (range over 1.2 EM), else Grind"""
    if not em or not o or not h or not l or not c:
        return None
    rng, oc = (h - l) / o * 100, abs(c - o) / o * 100
    return "Volatile" if rng > 1.2 * em else "Pin" if rng < 0.6 * em and oc < 0.3 * em else "Grind"


def har_forecast(closes):
    """next-day realized vol (annualized %) from a HAR-RV fit (Corsi 2009) on daily squared log returns: RV_d,
    5-day and 22-day means, least squares over the last 500 days; None with under 300 closes"""
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a and b and a > 0 and b > 0]
    if len(rets) < 300:
        return None
    rv = [x * x for x in rets[-523:]]
    X, y = [], []
    for i in range(22, len(rv) - 1):
        X.append((1.0, rv[i], sum(rv[i - 4:i + 1]) / 5, sum(rv[i - 21:i + 1]) / 22))
        y.append(rv[i + 1])
    b = _ols(X, y)
    if b is None:
        return None
    i = len(rv) - 1
    f = b[0] + b[1] * rv[i] + b[2] * sum(rv[i - 4:i + 1]) / 5 + b[3] * sum(rv[i - 21:i + 1]) / 22
    return math.sqrt(max(f, 1e-12) * 252) * 100


def _ols(X, y):
    k = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) for j in range(k)] for i in range(k)]
    v = [sum(r[i] * t for r, t in zip(X, y)) for i in range(k)]
    for c in range(k):                                    # Gauss-Jordan with partial pivoting
        p = max(range(c, k), key=lambda i: abs(A[i][c]))
        if abs(A[p][c]) < 1e-300:
            return None
        A[c], A[p], v[c], v[p] = A[p], A[c], v[p], v[c]
        for i in range(k):
            if i != c:
                f = A[i][c] / A[c][c]
                A[i] = [a - f * b for a, b in zip(A[i], A[c])]
                v[i] -= f * v[c]
    return [v[i] / A[i][i] for i in range(k)]


def fear_word(vix):
    v = _n(vix)
    if v is None:
        return None
    return "Calm" if v < VIX_BANDS[0] else "Normal" if v <= VIX_BANDS[1] else "Stressed"


def _picker_state(daily, vix_doc):
    """the picker's market state on SPY's closed bars (desk/picker/fearday.market_state), or None without history"""
    from ..picker import fearday
    spy = (daily or {}).get("SPY")
    if not spy:
        return None
    m = fearday.market_state(spy, vix=vix_doc)
    return m if m.get("as_of") else None


def agree(spy, qqq, em):
    """today's SPY and QQQ moves in % -> both up / both down / split / quiet"""
    if spy is None or qqq is None:
        return None
    q = QUIET * (em or 1.0)
    if abs(spy) < q and abs(qqq) < q:
        return "quiet"
    if spy > 0 and qqq > 0:
        return "both up"
    if spy < 0 and qqq < 0:
        return "both down"
    return "split"


# ---- the per-card options read and structures ------------------------------------------------------------------------

def iv_rank(hist, iv):
    """(rank 0-1, sessions) over the last IVR_N stored IV30s; rank None with fewer"""
    xs = [_n(e[1]) for e in hist or () if isinstance(e, (list, tuple)) and len(e) == 2 and _n(e[1])]
    if iv is None or len(xs) < IVR_N:
        return None, len(xs)
    xs = xs[-IVR_N:]
    lo, hi = min(xs), max(xs)
    return ((iv - lo) / (hi - lo) if hi > lo else None), len(xs)


def structures(quotes, spot, t1_pct, out_pct, days, bars=None):
    """quotes: {"t": years to expiry, "exp": iso, "calls": [[strike, bid, ask, iv], ...]} -> up to two structures,
    every price from the chain's own quotes (buy at the ask, sell at the bid):
      long call     the strike nearest the spot
      debit spread  long the strike nearest the spot, short the strike at or under T1
    each {kind, legs [[side, strike]], debit, max_loss, max_gain, breakeven, touch_t1} (per share; x100 a contract)"""
    calls = [c for c in (quotes or {}).get("calls") or () if isinstance(c, (list, tuple)) and len(c) == 4
             and all(_n(x) is not None for x in c) and c[1] >= 0 and c[2] > 0 and c[2] >= c[1]]
    T = _n((quotes or {}).get("t"))
    if not calls or not T or T <= 0 or not spot or t1_pct is None:
        return []
    t1 = spot * (1 + t1_pct / 100.0)
    atm = min(calls, key=lambda c: abs(c[0] - spot))
    pt = touch_rate(bars, t1_pct, days)
    out = [{"kind": "Long call", "legs": [["buy", atm[0]]], "debit": _r(atm[2], 2), "max_loss": _r(atm[2], 2),
            "max_gain": None, "breakeven": _r(atm[0] + atm[2], 2), "touch_t1": pt}]
    shorts = [c for c in calls if atm[0] < c[0] <= t1]
    if shorts:
        sh = max(shorts, key=lambda c: c[0])
        debit = atm[2] - sh[1]
        width = sh[0] - atm[0]
        if 0 < debit < width:
            out.append({"kind": "Call debit spread", "legs": [["buy", atm[0]], ["sell", sh[0]]], "debit": _r(debit, 2),
                        "max_loss": _r(debit, 2), "max_gain": _r(width - debit, 2),
                        "breakeven": _r(atm[0] + debit, 2), "touch_t1": pt})
    return out


def options_block(sym, plan, close, reading, iv_hist, oi_prev, rv20, session, horizon_days=None, bars=None):
    """a listed long's options block, or None for a name the gather did not read"""
    if not isinstance(reading, dict):
        return None
    if "error" in reading:
        return no(str(reading["error"])[:80], as_of=session)
    iv = _n(reading.get("iv30"))
    rank, n_iv = iv_rank(iv_hist, iv)
    pco, po_prev = _n(reading.get("pc_oi")), _n((oi_prev or {}).get("pc_oi"))
    em = em_pct(iv, frac=True)
    t1 = _n((plan or {}).get("t1"))
    days = horizon_days or (plan or {}).get("sessions") or 10
    move_h = em * math.sqrt(days) if em else None
    blk = {"status": "ok", "as_of": session, "method": "Alpaca indicative chain, OI from the prior close",
           "iv30": _r(iv), "iv_rank": _r(rank, 3), "iv_sessions": n_iv,
           "iv_rv": _r(iv / rv20, 2) if iv and rv20 else None,
           "pc_volume": _r(_n(reading.get("pc_volume")), 2), "pc_oi": _r(pco, 2),
           "pc_oi_change": _r(pco - po_prev, 2) if pco is not None and po_prev is not None else None,
           "spread_pct": _r(_n(reading.get("atm_spread_pct")), 2), "em_pct": _r(em, 2),
           "t1_beyond_2em": bool(t1 is not None and move_h and t1 > 2 * move_h)}
    q = reading.get("quotes")
    spot = _n(reading.get("spot")) or close
    express = structures(q, spot, t1, (plan or {}).get("out"), days, bars=bars)
    if express:                          # the vendor package: EV on the name's own measured finishes, and the P&L grid
        express = vx.ev_rank(express, spot, bars, max(1, round(float(q["t"]) * 252)))
        for st in express:
            st["pnl"] = vx.pnl_grid(st, spot, q)
    blk["express"] = express
    if q and q.get("exp"):
        blk["expiry"] = q["exp"]
    if not blk["express"]:
        blk["express_reason"] = "no usable call quotes" if q else "chain quotes not captured this session"
    return blk


# ---- the strip ------------------------------------------------------------------------------------------------------

def _closes(bars):
    return [float(b["c"]) for b in bars or () if isinstance(b, dict) and _n(b.get("c"))]


def _today_bar(bars, d):
    if not bars:
        return None
    b = bars[-1]
    try:
        return b if cal._as_date(float(b["t"])) == d else None
    except (KeyError, TypeError, ValueError):
        return None


def _vix_last(vix_doc, d):
    dates, closes = (vix_doc or {}).get("dates") or [], (vix_doc or {}).get("close") or []
    pairs = [(x, c) for x, c in zip(dates, closes) if c is not None and x <= d.isoformat()]
    if not pairs or (d - date.fromisoformat(pairs[-1][0])).days > 5:
        return None, None
    return pairs[-1][1], pairs[-1][0]


def build(root, opt, daily, live_daily, vix_doc, banner, now):
    """the edition's strip block; reads and updates the hysteresis state and the day-type log (state/terminal)"""
    d = cal._as_date(now)
    st_path = os.path.join(root, STATE_PATH)
    try:
        st = read_json(st_path, {}) or {}
    except (OSError, ValueError):
        st = {}
    vix, vix_d = _vix_last(vix_doc, d)
    em = em_pct(vix)
    out = {"as_of": d.isoformat()}
    # positioning
    names = (opt or {}).get("names") or {}
    gex = {}
    seen = st.setdefault("gex", {})
    for f in FUNDS:
        r = names.get(f)
        p = (r or {}).get("profile") if isinstance(r, dict) else None
        if not isinstance(r, dict) or "error" in (r or {}):
            gex[f] = morgue_gex(root, f, now) or no_chain(root, f, now, NO_READ + (f": {r['error']}" if isinstance(r, dict) and r.get("error") else ""))
            continue
        spot = _n(r.get("spot"))
        prof = profile(p.get("rows") or [], spot) if isinstance(p, dict) else None
        if prof is None:
            alt = morgue_gex(root, f, now)       # the Morgue Map's prior-close read of the same chain (08:46 ET), if current
            gex[f] = alt or no_chain(root, f, now, "no open interest with an IV in the chain" if isinstance(p, dict) else
                               "this session's options read predates the positioning rows; the next read supplies them")
            continue
        raw = "Dampening" if prof["net"] > 0 else "Amplifying"
        key = str((opt or {}).get("session")) + "@" + str(_n(r.get("at")))
        s0 = seen.get(f) or {}
        if s0.get("read") != key:                          # one step per gather, never per edition
            s0 = dict(settle(s0, raw), read=key)
            seen[f] = s0
        f_em = em_pct(r.get("iv30"), frac=True)
        flip = prof["flip"]
        gex[f] = {"status": "ok" if (opt or {}).get("session") == d.isoformat() else "stale",
                  "word": s0["word"], "raw": raw, "net": _r(prof["net"] / 1e9, 3),
                  "flip_pct": _r((flip / spot - 1) * 100, 2) if flip else None,
                  "flip_sigma": _r((flip / spot - 1) * 100 / f_em, 2) if flip and f_em else None,
                  "call_wall_pct": _r((prof["call_wall"] / spot - 1) * 100, 2) if prof["call_wall"] else None,
                  "put_wall_pct": _r((prof["put_wall"] / spot - 1) * 100, 2) if prof["put_wall"] else None,
                  "as_of": (opt or {}).get("session"), "contracts": prof["n"],
                  "oi_date": r.get("oi_date"),
                  "method": "SpotGamma convention, Black-Scholes gamma from Alpaca IVs, open interest from the prior close"}
        if not flip:
            gex[f]["flip_reason"] = "no zero crossing within 10% of the price"
    out["gex"] = gex
    spy_c = _closes((daily or {}).get("SPY"))
    har = har_forecast(spy_c)
    # expected move
    minute = (now - cal.session_open(d)) / 60.0 if cal.is_trading_day(d) and now >= cal.session_open(d) else None
    out["move"] = ({"status": "ok", "em_pct": _r(em, 2), "funded_pct": _r(funded(em, minute), 2) if minute else None,
                    "minute": int(minute) if minute and minute <= 390 else None, "as_of": vix_d,
                    "em_inside_pct": EM_INSIDE,
                    "band68_pct": _r(har * HAR_BAND / SQRT252, 2) if har else None,
                    "method": f"VIX close / 15.87: about {EM_INSIDE}% of days stay inside this move (not 68%). The 68% band is "
                              "the HAR forecast of the S&P's volatility x 0.88."}
                   if em else no("no VIX close within 5 days"))
    # fear
    pk = _picker_state(daily, vix_doc)                    # the ONE fear-day truth: the picker's (desk/picker/fearday.py)
    if vix is not None and pk is not None:
        out["fear"] = {"status": "ok", "stress": fear_word(vix), "as_of": vix_d,
                       "vix_vs_forecast": _r(vix / har, 2) if har else None,
                       "fear_day": pk["fear"], "fear_day_date": pk["as_of"], "as_of_session": pk["as_of"],
                       "fear_why": pk["why"], "picker_state": pk["state"],
                       "method": "Fear day = the Buy List's rule: SPY fell 1% or more on the day, or closed under its "
                                 "50-day average (or a volatility spike). Stress is a separate word from the VIX "
                                 "(under 15 calm, 15 to 18.5 normal, over 18.5 stressed) beside a HAR forecast of the "
                                 "S&P's realized volatility."}
    elif vix is not None:
        out["fear"] = no("no SPY history for the fear-day rule")
    else:
        out["fear"] = no("no VIX close within 5 days")
    # SPX / NQ agreement and day type, from today's bars
    moves = {}
    for f in ("SPY", "QQQ"):
        b = _today_bar((live_daily or {}).get(f), d)
        done = [x for x in (daily or {}).get(f) or () if not _today_bar([x], d)]   # completed sessions before today
        hist = _closes(done)
        prev = hist[-1] if hist else None
        if b and prev:
            moves[f] = (float(b["c"]) / prev - 1) * 100, float(b["o"]) / prev - 1, b, prev
    if "SPY" in moves and "QQQ" in moves:
        out["agree"] = {"status": "ok", "word": agree(moves["SPY"][0], moves["QQQ"][0], em),
                        "spy_pct": _r(moves["SPY"][0], 2), "qqq_pct": _r(moves["QQQ"][0], 2), "as_of": d.isoformat()}
    else:
        out["agree"] = no("no session bar yet today")
    if "SPY" in moves and em:
        b, prev = moves["SPY"][2], moves["SPY"][3]
        gap = moves["SPY"][1] * 100
        rng = (float(b["h"]) - float(b["l"])) / prev * 100
        net = (gex.get("SPY") or {}).get("net")
        word = day_type(net, em, gap, rng)
        out["day"] = {"status": "ok", "word": word, "gap_pct": _r(gap, 2), "range_pct": _r(rng, 2),
                      "as_of": d.isoformat(), "method": "gamma sign, gap and range so far against the expected move"}
        _log_day(root, d.isoformat(), word, em, minute)
    else:
        out["day"] = no("the session has not opened" if "SPY" not in moves else "no expected move")
    _grade_days(root, (daily or {}).get("SPY"))
    try:
        write_json_atomic(st_path, st)
    except OSError:
        pass
    return out


def _log_day(root, session, word, em, minute):
    """the session's first day type after 10:00 ET is the one graded (once per session, append-only)"""
    if not word or minute is None or minute < 30:
        return
    path = os.path.join(root, DAY_LOG)
    try:
        with open(path) as f:
            if any(json.loads(x).get("session") == session for x in f if x.strip()):
                return
    except (OSError, ValueError):
        pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps({"session": session, "call": word, "em_pct": _r(em, 3), "minute": int(minute)}) + "\n")


def _grade_days(root, spy_bars):
    """append a grade row for each logged call whose session has closed in the bars and has no grade yet"""
    path = os.path.join(root, DAY_LOG)
    try:
        with open(path) as f:
            rows = [json.loads(x) for x in f if x.strip()]
    except (OSError, ValueError):
        return
    graded = {r["session"] for r in rows if r.get("grade")}
    bars = {}
    for b in spy_bars or ():
        try:
            bars[cal._as_date(float(b["t"])).isoformat()] = b
        except (KeyError, TypeError, ValueError):
            continue
    new = []
    for r in rows:
        s = r.get("session")
        if r.get("call") and s not in graded and s in bars:
            b = bars[s]
            g = grade_day(r.get("em_pct"), _n(b.get("o")), _n(b.get("h")), _n(b.get("l")), _n(b.get("c")))
            if g:
                new.append({"session": s, "grade": g, "hit": g == r["call"]})
                graded.add(s)
    if new:
        with open(path, "a") as f:
            for r in new:
                f.write(json.dumps(r) + "\n")


PCOI_PATH = os.path.join("cache", "terminal", "pcoi.json")


def store_pcoi(root, doc, session, keep=5):
    """each read name's put/call open-interest ratio for the session (its change on the card needs the last one)"""
    path = os.path.join(root, PCOI_PATH)
    try:
        h = read_json(path, {}) or {}
    except (OSError, ValueError):
        return
    for s, n in ((doc or {}).get("names") or {}).items():
        v = _n((n or {}).get("pc_oi")) if isinstance(n, dict) else None
        if v is None:
            continue
        rows = [e for e in h.get(s) or () if isinstance(e, list) and len(e) == 2 and e[0] != session]
        h[s] = sorted(rows + [[session, v]])[-keep:]
    write_json_atomic(path, h)


def prev_pcoi(root, session):
    """{name: {"pc_oi", "session"}}: each name's last stored ratio before `session`"""
    try:
        h = read_json(os.path.join(root, PCOI_PATH), {}) or {}
    except (OSError, ValueError):
        return {}
    out = {}
    for s, rows in h.items():
        old = [e for e in rows or () if isinstance(e, list) and len(e) == 2 and str(e[0]) < session]
        if old:
            out[s] = {"pc_oi": old[-1][1], "session": old[-1][0]}
    return out
