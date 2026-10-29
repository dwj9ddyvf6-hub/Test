"""Options and news for the Best Setups page: the owner's list, rows 47-50 and 58
(docs/research/2026-10-19-every-factor/SCOPE.md). The owner, 2026-10-20: options and news facts derived from Alpaca
may appear on the public page (free, non-commercial, about 50 viewers). Alpaca alone: never CBOE (desk/data/options.py
falls back to CBOE's page, so it is not used here). SqueezeMetrics and FINRA are allowed by the owner (2026-10-27)
but are not read here.

Job `terminal_optnews` (desk/jobs.py), once a session, 14:00-15:00 ET: in the regular session, while the chains carry
live quotes, and never in the desk's hot windows (hot(): 09:25-10:05 and 15:25-16:15 ET, the close's 12:25-13:15 on an
early close), when the live passes need the network budget. The gate is asked before every request, and a run that
meets a hot window stops there. It reads the board's names (the last edition's setups, at most MAX_NAMES) and the funds
SPY, QQQ and IWM through the desk's Alpaca client (its rate bucket, the desk-wide pacing of desk/data/http.py, the
jobs' bulk lane):
  spot        each name's last IEX trade (one request; the cached close when it has none)
  contracts   each contract's open interest, the prior session's (/v2/options/contracts on the trading host: a fund
              alone, the names BATCH a request; expirations today to WINDOW_DAYS out, Alpaca's default being "the next
              weekend")
  chain       each name's indicative snapshots (/v1beta1/options/snapshots/{name}, the same expirations; a name's
              strikes within STRIKES of its price, a fund's every strike): IV, gamma, the session's volume
  news        the board names' articles of the last NEWS_DAYS days (/v1beta1/news: one request for every name, 50 a
              page, every page)
From them (pure functions, proven on a chain with a known answer, tests/test_terminal_optnews.py):
  iv30        the 30-day at-the-money implied volatility: at each expiry a day or more out, the call and put IVs
              averaged at each strike that has both (a row without a bid or an IV is no reading), linear in strike
              between the strikes on either side of the price; then total variance linear in time between the expiries
              on either side of 30 days (with none on one side, no IV30)
  put/call    the puts' volume over the calls' (each contract's daily bar of the session), and their open interest
  gex         net dealer gamma in dollars per 1% move: the sum of gamma x OI x 100 x S^2 x 0.01, calls +, puts - (the
              usual convention, that dealers are long the calls and short the puts: a convention, not a fact)
  news        each name's count in 24 hours and in 7 days, and its latest HEADLINES headlines that clean() keeps
Written to PATH (cache/terminal/optnews.json: the session's numbers, replaced each session; internal, never published)
and IV_PATH (cache/terminal/iv30.json: one IV30 per name per session, the last IV_KEEP of IV_NAMES names; IV rank needs
252, so tools/state_sync.py records it). Nothing here raises past a name: no keys, a refusal, an empty chain or the hot
window leave that name's lines unanswered for the session (desk/terminal/read/optnews.py reads a session's own
numbers only)."""
import html
import math
import os
import re
import time
import unicodedata
import urllib.parse
from datetime import date, datetime, timedelta, timezone

from .. import calendar as cal
from ..data.options import occ_parse
from ..util import ET, parse_ts, read_json, write_json_atomic
from ..venues.alpaca import DATA
from .read.optnews import FUNDS, link, refused

PATH = os.path.join("cache", "terminal", "optnews.json")
IV_PATH = os.path.join("cache", "terminal", "iv30.json")
MAX_NAMES = 30                  # the page's setups (five on the board today)
WINDOW_DAYS = 95                # expirations read: today to 95 days out (options.md: D+1 to D+95, and today's volume)
STRIKES = 0.3                   # a name's strikes within 30% of its price; a fund's every strike
BATCH = 20                      # underlyings a contracts request (options.md: about 20)
MAX_CHAIN_PAGES = 60            # 1,000 contracts a page; SPY to 95 days holds about 20,000
MAX_CONTRACT_PAGES = 20         # 10,000 contracts a page
MAX_NEWS_PAGES = 40             # 50 articles a page: 2,000, the week of 30 busy names
NEWS_DAYS = 7
HEADLINES = 3
HEADLINE_MAX, SOURCE_MAX = 200, 40
IV_KEEP, IV_NAMES = 260, 400    # IV rank needs 252 sessions; the names read most recently
MAX_IV = 5.0                    # an implied volatility over 500% is no reading
FAILS_IN_A_ROW = 3              # failed requests in a row (each with the client's three tries) that end a run
FAILS = f"{FAILS_IN_A_ROW} requests failed"
HOT = ((-5, 35), (-35, 15))     # minutes from the open, and from the close: 09:25-10:05 and 15:25-16:15 ET


def _hm(ts):
    return datetime.fromtimestamp(ts, tz=ET).strftime("%H:%M")


def hot(ts):
    """the desk's hot window ts falls in, as text ("the close, 15:25-16:15 ET"), or None: the open's and the close's
    (the close's moves with an early close), on trading days only"""
    d = cal._as_date(ts)
    if not cal.is_trading_day(d):
        return None
    for name, base, (a, b) in (("the open", cal.session_open(d), HOT[0]), ("the close", cal.session_close(d), HOT[1])):
        lo, hi = base + a * 60, base + b * 60
        if lo <= ts < hi:
            return "%s, %s-%s ET" % (name, _hm(lo), _hm(hi))
    return None


def why_not(ts):
    """why the gather may not send a request at ts, or None: no session that day, a hot window, or outside the regular
    session (the chains' quotes are not live)"""
    if not cal.is_trading_day(cal._as_date(ts)):
        return "no session today"
    return hot(ts) or (None if cal.is_rth(ts) else "outside the regular session")


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _ts(v):
    """an RFC-3339 time -> epoch seconds, or None"""
    if not isinstance(v, str) or not v:
        return None
    try:
        t = parse_ts(v)
    except (TypeError, ValueError, OverflowError):
        return None
    return t if t is not None and math.isfinite(t) else None


def _root(sym):
    return sym.replace(".", "")                 # an OCC root carries no class dot (BRK.B's options are BRKB's)


# ---- the readings ---------------------------------------------------------------------------------------------------

def rows_of(sym, snaps):
    """the name's own contracts (its standard root: an adjusted contract delivers something else) from Alpaca's
    snapshots {OCC: snapshot} -> [{"symbol", "root", "expiration", "type", "strike", "iv", "bid", "gamma", "volume",
    "day"}]; "day": the UTC date its daily bar is stamped with (the session's: midnight New York)"""
    out = []
    for occ, sn in (snaps or {}).items():
        try:
            root, exp, cp, k = occ_parse(occ)
            date.fromisoformat(exp)                  # a symbol whose date is no date (month 13) is no contract
        except (ValueError, IndexError, TypeError, AttributeError):
            continue
        if root != _root(sym) or not isinstance(sn, dict):
            continue
        q, g, b = (sn.get(k_) if isinstance(sn.get(k_), dict) else {} for k_ in ("latestQuote", "greeks", "dailyBar"))
        out.append({"symbol": occ, "root": root, "expiration": exp, "type": cp, "strike": k,
                    "iv": _num(sn.get("impliedVolatility")), "bid": _num(q.get("bp")), "ask": _num(q.get("ap")), "gamma": _num(g.get("gamma")),
                    "volume": _num(b.get("v")), "day": str(b.get("t") or "")[:10]})
    return out


def atm_by_expiry(rows, spot, today):
    """{days to expiry: at-the-money IV} for each expiry a day or more out (Alpaca computes no greeks on an expiry's
    last day): the call and put IVs averaged at each strike that has both, a row without a bid or an IV dropped, then
    linear in strike between the strikes on either side of the price"""
    if not spot or spot <= 0:
        return {}
    by = {}
    for r in rows:
        if r["iv"] is None or not 0 < r["iv"] <= MAX_IV or not r["bid"] or r["bid"] <= 0:
            continue
        by.setdefault(r["expiration"], {}).setdefault(r["strike"], {})[r["type"]] = r["iv"]
    out = {}
    for exp, ks in by.items():
        t = (date.fromisoformat(exp) - today).days
        if t < 1:
            continue
        mid = sorted((k, (v["call"] + v["put"]) / 2.0) for k, v in ks.items() if "call" in v and "put" in v)
        lo, hi = [kv for kv in mid if kv[0] <= spot], [kv for kv in mid if kv[0] >= spot]
        if not lo or not hi:
            continue
        (k1, v1), (k2, v2) = lo[-1], hi[0]
        out[t] = v1 if k2 == k1 else v1 + (v2 - v1) * (spot - k1) / (k2 - k1)
    return out


def iv30(rows, spot, today, days=30):
    """the 30-day at-the-money IV: an expiry exactly `days` out gives its own; else the expiries on either side of it,
    total variance linear in time: sqrt([s1^2 T1 + (s2^2 T2 - s1^2 T1)(30 - T1)/(T2 - T1)] / 30); None without one on
    each side"""
    at = atm_by_expiry(rows, spot, today)
    if days in at:
        return at[days]
    below, above = [t for t in at if t < days], [t for t in at if t > days]
    if not below or not above:
        return None
    t1, t2 = max(below), min(above)
    v1, v2 = at[t1] ** 2 * t1, at[t2] ** 2 * t2
    var = (v1 + (v2 - v1) * (days - t1) / (t2 - t1)) / days
    return math.sqrt(var) if var > 0 else None


def put_call_volume(rows, session):
    """(the puts' volume / the calls', the calls', the puts'): each contract's daily bar of the session only (one that
    has not traded today carries an older day's bar); the ratio None without a call traded"""
    c = sum(r["volume"] or 0.0 for r in rows if r["type"] == "call" and r["day"] == session)
    p = sum(r["volume"] or 0.0 for r in rows if r["type"] == "put" and r["day"] == session)
    return (p / c if c > 0 else None), c, p


def oi_of(contracts):
    """{OCC: {"symbol", "underlying", "root", "type", "strike", "oi", "date"}} from Alpaca's contracts, whose strike
    and open interest are strings"""
    out = {}
    for c in contracts or ():
        if isinstance(c, dict) and isinstance(c.get("symbol"), str):
            out[c["symbol"]] = {"symbol": c["symbol"], "underlying": c.get("underlying_symbol"),
                                "root": c.get("root_symbol"), "type": c.get("type"),
                                "strike": _num(c.get("strike_price")), "oi": _num(c.get("open_interest")),
                                "date": c.get("open_interest_date")}
    return out


def put_call_oi(oi):
    """(the puts' open interest / the calls', the calls', the puts', the latest open-interest date the rows carry)"""
    rows = list(oi.values()) if isinstance(oi, dict) else list(oi)
    c = sum(r["oi"] for r in rows if r["type"] == "call" and r["oi"])
    p = sum(r["oi"] for r in rows if r["type"] == "put" and r["oi"])
    days = [r["date"] for r in rows if r["oi"] and isinstance(r.get("date"), str)]
    return (p / c if c > 0 else None), c, p, (max(days) if days else None)


def gex(rows, spot):
    """(net dealer gamma in dollars per 1% move, the share of open interest that carries a gamma): the sum of gamma x
    OI x 100 x S^2 x 0.01, calls +, puts -, by the usual convention that dealers are long the calls and short the puts
    (a convention, not a fact: public open interest does not say who holds it, Perfiliev 2022). (None, None) without
    a contract carrying both"""
    total = covered = g = 0.0
    n = 0
    for r in rows:
        oi = r.get("oi")
        if not oi or oi <= 0:
            continue
        total += oi
        if r.get("gamma") is None:
            continue
        covered += oi
        n += 1
        g += (1.0 if r["type"] == "call" else -1.0) * r["gamma"] * oi * 100.0 * spot * spot * 0.01
    return (g, covered / total) if n else (None, None)


def dv20(bars):
    """the 20-session average of close x volume (the read's own liquidity line is the median), or None"""
    b = [x for x in bars or () if isinstance(x, dict) and _num(x.get("c")) and _num(x.get("v")) is not None][-20:]
    return sum(float(x["c"]) * float(x["v"]) for x in b) / 20.0 if len(b) == 20 else None


def reading(sym, rows, oi, spot, today, dv=None, at=None):
    """one name's numbers from its chain's rows and the open interest by contract"""
    if not rows:
        return {"error": "no option chain"}
    fund = sym in FUNDS
    lo, hi = spot * (1 - STRIKES), spot * (1 + STRIKES)
    by = {r["symbol"]: r for r in rows}
    own = [r for r in oi.values() if r["underlying"] == sym and r["root"] == _root(sym) and
           (fund or (r["strike"] is not None and lo <= r["strike"] <= hi))]
    pv, cv, pvv = put_call_volume(rows, today.isoformat())
    po, co, poo, oi_day = put_call_oi(own)
    g, cover = gex([{"type": r["type"], "oi": r["oi"], "gamma": (by.get(r["symbol"]) or {}).get("gamma")}
                    for r in own], spot)
    return {"at": at, "spot": spot, "contracts": len(rows), "expiries": len({r["expiration"] for r in rows}),
            "iv30": iv30(rows, spot, today), "pc_volume": pv, "calls_volume": cv, "puts_volume": pvv,
            "pc_oi": po, "calls_oi": co, "puts_oi": poo, "oi_date": oi_day, "gex": g, "gex_cover": cover,
            "dv20": dv, **capture(sym, rows, own, spot, today)}


PROFILE_DAYS, PROFILE_BAND = 60, 0.15     # a fund's positioning rows: expiries to 60 days, strikes within 15%
QUOTE_DAYS = (21, 60)                     # a name's structures: the expiry nearest 30 days inside this band


def capture(sym, rows, own, spot, today):
    """the extra the strip reads (desk/terminal/strip.py): a fund's open-interest rows with their IVs (the flip and the
    walls); a name's call quotes at one expiry (its priced structures); the at-the-money spread as % of the mid"""
    out = {}
    by = {r["symbol"]: r for r in rows}
    if sym in FUNDS:
        prof = []
        for o in own:
            r = by.get(o["symbol"]) or {}
            try:
                t = (date.fromisoformat(r.get("expiration") or "") - today).days
            except ValueError:
                continue
            if 0 < t <= PROFILE_DAYS and o["oi"] and r.get("iv") and o["strike"] and \
                    abs(o["strike"] / spot - 1) <= PROFILE_BAND:
                prof.append({"type": o["type"], "k": o["strike"], "t": round(t / 365.0, 5), "oi": o["oi"],
                             "iv": round(r["iv"], 4)})
        out["profile"] = {"rows": prof}
    exps = {}
    for r in rows:
        try:
            exps.setdefault(r["expiration"], (date.fromisoformat(r["expiration"]) - today).days)
        except ValueError:
            continue
    band = [e for e, t in exps.items() if QUOTE_DAYS[0] <= t <= QUOTE_DAYS[1]]
    exp = min(band, key=lambda e: abs(exps[e] - 30)) if band else None
    if exp:
        at = [r for r in rows if r["expiration"] == exp]
        calls = sorted([[r["strike"], r["bid"], r["ask"], r["iv"]] for r in at if r["type"] == "call"
                        and r["bid"] is not None and r["ask"] and r["iv"] and 0.95 * spot <= r["strike"] <= 1.3 * spot])
        if calls and sym not in FUNDS:
            out["quotes"] = {"exp": exp, "t": round(exps[exp] / 365.0, 5), "calls": calls}
        near = [r for r in at if r["bid"] and r["ask"] and r["ask"] >= r["bid"]]
        if near:
            k = min(near, key=lambda r: abs(r["strike"] - spot))["strike"]
            sp = [(r["ask"] - r["bid"]) / ((r["ask"] + r["bid"]) / 2) * 100 for r in near if r["strike"] == k]
            if sp:
                out["atm_spread_pct"] = round(sum(sp) / len(sp), 2)
    return out


# ---- the news -------------------------------------------------------------------------------------------------------

def _text(v, n):
    """untrusted text as one plain line: entities decoded, control and format characters out, whitespace collapsed,
    cut at n characters"""
    if not isinstance(v, str):
        return ""
    s = "".join(ch for ch in html.unescape(v) if ch.isspace() or not unicodedata.category(ch).startswith("C"))
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def clean(a):
    """one article as the page may show it, {"headline", "source", "at"[, "url"]}, or None. Its text is untrusted: a
    plain string only, never one the page would refuse (a currency sign: the edition holds no price) or the publisher
    would block (an address or a token's shape: publish.SECRET_SHAPES); its link only to http(s), else none"""
    if not isinstance(a, dict):
        return None
    h, src, t = _text(a.get("headline"), HEADLINE_MAX), _text(a.get("source"), SOURCE_MAX), _ts(a.get("created_at"))
    if not h or not src or t is None or refused(h) or refused(src):
        return None
    out = {"headline": h, "source": src, "at": datetime.fromtimestamp(t, tz=ET).isoformat(timespec="seconds")}
    if link(a.get("url")):
        out["url"] = a["url"]
    return out


def news_of(arts, names, now, whole):
    """{name: {"day", "week", "whole", "day_whole", "items"}}: the articles naming it created in the last 24 hours and
    NEWS_DAYS days (each once, by its id), and its latest HEADLINES headlines that clean() keeps (every article counts,
    shown or not). The pages come newest update first and an article is created before its last update, so a read
    stopped early (whole False) still has the 24 hours whole once the oldest update read is older than they are"""
    day0, week0 = now - 86400, now - NEWS_DAYS * 86400
    out = {s: {"day": 0, "week": 0, "whole": bool(whole), "items": []} for s in names}
    cands, seen, oldest = {s: [] for s in names}, set(), None
    for a in arts if isinstance(arts, list) else ():
        try:                                          # one malformed article costs only itself
            key = a.get("id") if a.get("id") is not None else id(a)
            hash(key)
            up = _ts(a.get("updated_at")) or _ts(a.get("created_at"))
            t = _ts(a.get("created_at"))
            syms = {s for s in a.get("symbols") or () if isinstance(s, str)}
        except (AttributeError, TypeError):
            continue
        if key in seen:
            continue
        seen.add(key)
        if up is not None:
            oldest = up if oldest is None else min(oldest, up)
        if t is None or t < week0 or t > now + 300:
            continue
        for s in names:
            if s in syms:
                out[s]["week"] += 1
                out[s]["day"] += t >= day0
                cands[s].append((t, a))
    for s in names:
        out[s]["day_whole"] = bool(whole) or (oldest is not None and oldest < day0)
        for t, a in sorted(cands[s], key=lambda ta: -ta[0]):
            it = clean(a)
            if it:
                out[s]["items"].append(it)
            if len(out[s]["items"]) == HEADLINES:
                break
    return out


# ---- the gather -----------------------------------------------------------------------------------------------------

def _z(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _done(entry, sym=None):
    """a name read this session: its numbers, or an answer that holds for the session (no chain, no price). A fund's reading
    without its positioning rows ("profile") was made before the strip existed (2026-10-27 00:15 UTC): it is read again, not
    kept for the session, or the strip says "no open interest with an IV" for the rest of that session"""
    if not isinstance(entry, dict) or entry.get("retry"):
        return False
    return not (sym in FUNDS and "error" not in entry and "profile" not in entry)


def gather(client, names, now, clock=None, closes=None, dv=None, prev=None):
    """the session's doc for the board's `names` and FUNDS (module docstring) through `client` (the desk's Alpaca
    client). Every request asks the gate first (why_not at clock()); a name read already this session (prev: this
    session's doc) is not read again; a refusal (401, 403), or FAILS_IN_A_ROW failed requests in a row, stops the
    gather; a malformed answer costs only its own name, article or price. Never raises"""
    clock = clock or time.time
    today = cal._as_date(now)
    session = today.isoformat()
    prev = prev if isinstance(prev, dict) and prev.get("session") == session else {}
    pn, pw = prev.get("names"), prev.get("news")
    doc = {"v": 1, "session": session, "at": _num(prev.get("at")) or float(now), "funds": list(FUNDS),
           "names": {k: v for k, v in pn.items() if _done(v, k)} if isinstance(pn, dict) else {},
           "news": dict(pw) if isinstance(pw, dict) else {}, "stopped": None, "errors": {}}
    if _num(prev.get("news_at")):
        doc["news_at"] = prev["news_at"]
    closes, dv = closes or {}, dv or {}
    lte = (today + timedelta(days=WINDOW_DAYS)).isoformat()
    state = {"stop": None, "fails": 0}

    def go():
        if not state["stop"]:
            state["stop"] = why_not(clock())
        return not state["stop"]

    def ask(fn):
        """(True, fn()) or (False, why): a refusal stops the gather, and so do FAILS_IN_A_ROW failed requests in a
        row (each had the client's own three tries: a timing-out host never holds the job's slot)"""
        try:
            got = fn()
        except Exception as e:                       # noqa: BLE001  (a name's failure is the name's)
            st = getattr(e, "status", None)
            state["fails"] += 1
            if st in (401, 403):
                state["stop"] = f"refused: HTTP {st}"
            elif state["fails"] >= FAILS_IN_A_ROW and not state["stop"]:
                state["stop"] = f"{FAILS} in a row, the last {type(e).__name__}: {str(e)[:80]}"
            return False, {"error": f"{type(e).__name__}: {str(e)[:120]}", "retry": st not in (401, 403, 422)}
        state["fails"] = 0
        return True, got

    syms = list(dict.fromkeys(list(FUNDS) + list(names)))
    todo = [s for s in syms if not _done(doc["names"].get(s), s)]
    spot = {}
    if todo and go():
        ok, got = ask(lambda: client.stock_trades_latest(todo, feed="iex"))
        if ok and isinstance(got, dict):
            spot = {s: _num(v.get("p")) for s, v in got.items() if isinstance(v, dict)}
        else:                                         # a refusal or a malformed answer: the cached closes serve
            doc["errors"]["spot"] = got["error"] if not ok else "malformed answer"
    oi = {}
    names_ = [s for s in todo if s not in FUNDS]          # a fund's every strike on its own: one fund's chain at a time
    for batch in [[f] for f in todo if f in FUNDS] + [names_[i:i + BATCH] for i in range(0, len(names_), BATCH)]:
        if not go():
            break
        ok, got = ask(lambda: client.paged("/v2/options/contracts", {
            "underlying_symbols": ",".join(batch), "expiration_date_gte": session, "expiration_date_lte": lte,
            "limit": 10000}, "option_contracts", go=go, max_pages=MAX_CONTRACT_PAGES))
        if ok and got[1]:
            oi.update(oi_of(got[0]))
        else:
            doc["errors"]["contracts"] = got["error"] if not ok else "cut short"
    for s in todo:
        if not go():
            break
        px = spot.get(s) or _num(closes.get(s))
        if not px or px <= 0:
            doc["names"][s] = {"error": "no price"}
            continue
        p = {"feed": "indicative", "expiration_date_gte": session, "expiration_date_lte": lte, "limit": 1000}
        if s not in FUNDS:
            p.update(strike_price_gte=round(px * (1 - STRIKES), 2), strike_price_lte=round(px * (1 + STRIKES), 2))
        ok, got = ask(lambda: client.paged("/v1beta1/options/snapshots/" + urllib.parse.quote(s, safe=""), p,
                                           "snapshots", host=DATA, go=go, max_pages=MAX_CHAIN_PAGES))
        if not ok:
            if not state["stop"]:
                doc["names"][s] = got
            continue
        if not got[1]:                                # the gate closed mid-chain, or the page cap: not read
            if not state["stop"]:
                doc["names"][s] = {"error": "chain cut short", "retry": True}
            continue
        try:
            doc["names"][s] = reading(s, rows_of(s, got[0]), oi, px, today, dv.get(s), clock())
        except Exception as e:                        # noqa: BLE001  (a malformed chain costs only its name)
            doc["names"][s] = {"error": f"unreadable chain: {type(e).__name__}"}
    news_todo = [s for s in dict.fromkeys(names) if s not in doc["news"]]
    if news_todo and go():
        t = clock()
        ok, got = ask(lambda: client.news(news_todo, start=_z(t - NEWS_DAYS * 86400), go=go,
                                          max_pages=MAX_NEWS_PAGES))
        if not ok:
            doc["errors"]["news"] = got["error"]
        else:
            try:
                doc["news"].update(news_of(got[0], news_todo, t, got[1]))
                doc["news_at"] = t
            except Exception as e:                    # noqa: BLE001  (the options lines stand without the news)
                doc["errors"]["news"] = f"unreadable news: {type(e).__name__}"
    doc["stopped"] = state["stop"]
    return doc


def store_iv(hist, ivs, session, keep=IV_KEEP, names=IV_NAMES):
    """the IV30 history with this session's readings {name: IV30}: one per name per session (a second reading of the
    session replaces the first), each name's last `keep` sessions, the `names` names read most recently; a `names`
    that is not an object holds no reading and is passed over"""
    old = hist.get("names") if isinstance(hist, dict) else None
    out = {"v": 1, "names": {k: [list(e) for e in v if isinstance(e, (list, tuple)) and len(e) == 2]
                             for k, v in (old if isinstance(old, dict) else {}).items() if isinstance(v, list)}}
    for s, iv in ivs.items():
        rows = sorted([e for e in out["names"].get(s, []) if e[0] != session] + [[session, float(iv)]],
                      key=lambda e: str(e[0]))
        out["names"][s] = rows[-keep:]
    if len(out["names"]) > names:
        order = sorted(out["names"], key=lambda k: (str(out["names"][k][-1][0]) if out["names"][k] else "", k),
                       reverse=True)
        out["names"] = {k: out["names"][k] for k in order[:names]}
    return out


def _store(root, ivs, session):
    """({name: its stored sessions}, why not stored): an unreadable history is kept as it is, never overwritten"""
    path = os.path.join(root, IV_PATH)
    try:
        hist = read_json(path, {"v": 1, "names": {}})
    except (OSError, ValueError):
        hist = None
    if not isinstance(hist, dict):
        return {}, "the IV30 history is unreadable: kept as it is"
    if not ivs:
        return {}, None
    hist = store_iv(hist, ivs, session)
    write_json_atomic(path, hist)
    return {s: len(hist["names"].get(s) or []) for s in ivs}, None


def load(root):
    """the last gather's doc, or None when it cannot be read (the reads then answer none of its lines)"""
    try:
        doc = read_json(os.path.join(root, PATH), None)
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def board(root):
    """the page's setups, the last edition's, at most MAX_NAMES"""
    try:
        ed = read_json(os.path.join(root, "state", "terminal", "edition.json"), {}) or {}
    except (OSError, ValueError):
        return []
    out = []
    for s in (ed.get("setups") or []) if isinstance(ed, dict) else []:
        sym = s.get("symbol") if isinstance(s, dict) else None
        if isinstance(sym, str) and re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}", sym) and sym not in out:
            out.append(sym)
    return out[:MAX_NAMES]


def _client(engine):
    """the desk's Alpaca market-data client when this process holds keys, else None"""
    c = getattr(getattr(getattr(engine, "hub", None), "alpaca", None), "c", None)
    return c if c is not None and getattr(c, "available", False) else None


def _cached(engine, syms):
    """({name: its last cached close}, {name: its 20-session average dollar volume}) from the split-adjusted daily
    cache the reads use: never a fetch"""
    try:
        bars = engine.hub.bars("equity_split", "1d", syms, 25, cache_only=True) or {}
    except Exception:                                 # noqa: BLE001  (the chain's own price serves)
        return {}, {}
    return ({s: _num(b[-1].get("c")) for s, b in bars.items() if b},
            {s: dv20(b) for s, b in bars.items()})


def job(engine, now=None, client=None):
    """the job: the gate, the keys, the board, the gather, the two files (the session's doc written before the IV30
    store is touched) -> the job's info (counts and why; never a key). ok is False only when nothing was read and a
    retry may mend it (desk/jobs.py retries within the window): a name that failed alone has had the client's own
    three tries, and one name's failure never pages the owner (desk/learn/incidents.py); its line stays unanswered
    for the session"""
    root = engine.root
    now = float(engine.clock() if now is None else now)
    why = why_not(now)
    if why:
        return {"ok": True, "skipped": why}
    client = client or _client(engine)
    session = cal._as_date(now).isoformat()
    names = board(root)
    prev = load(root)
    path = os.path.join(root, PATH)
    if client is None:
        if not (prev and prev.get("session") == session):
            write_json_atomic(path, {"v": 1, "session": session, "at": now, "funds": list(FUNDS), "names": {},
                                     "news": {}, "stopped": "no Alpaca client with keys", "errors": {}})
        return {"ok": True, "skipped": "no Alpaca client with keys in this process", "names": len(names)}
    closes, dv = _cached(engine, list(dict.fromkeys(list(FUNDS) + names)))
    calls = getattr(client, "calls", 0)
    doc = gather(client, names, now, clock=getattr(engine, "clock", None) or time.time, closes=closes, dv=dv,
                 prev=prev)
    write_json_atomic(path, doc)                      # the session's numbers land first; the store only adds to them
    ivs = {s: n["iv30"] for s, n in doc["names"].items() if isinstance(n, dict) and n.get("iv30")}
    try:
        counts, why_not_stored = _store(root, ivs, session)
    except Exception as e:                            # noqa: BLE001  (the IV30 store never costs the session)
        counts, why_not_stored = {}, f"the IV30 store failed: {type(e).__name__}: {str(e)[:120]}"
    try:
        from . import strip as stripmod
        stripmod.store_pcoi(root, doc, session)
    except Exception as e:                            # noqa: BLE001  (the ratio's history never costs the session)
        doc["errors"]["pcoi"] = f"{type(e).__name__}: {str(e)[:80]}"
    for s, k in counts.items():
        doc["names"][s]["iv_sessions"] = k
    if why_not_stored:
        doc["errors"]["iv30"] = why_not_stored
    if counts or why_not_stored:
        write_json_atomic(path, doc)
    read = sorted(s for s, n in doc["names"].items() if "error" not in n)
    retry = sorted(s for s, n in doc["names"].items() if n.get("retry"))
    failed = str(doc["stopped"] or "").startswith(FAILS)
    return {"ok": bool(read) or not (retry or failed), "session": session, "names": len(names), "read": len(read),
            "no_chain": sorted(s for s, n in doc["names"].items() if "error" in n and not n.get("retry")),
            "retry": retry, "news": len(doc["news"]), "stopped": doc["stopped"], "errors": doc["errors"],
            "requests": getattr(client, "calls", 0) - calls}
