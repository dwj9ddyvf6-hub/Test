"""The read's options and news lines: the owner's list, rows 47-50 and 58 (docs/research/2026-10-19-every-factor/
SCOPE.md), from the session's gather (desk/terminal/optnews.py: cache/terminal/optnews.json, Alpaca's chains and news
for the board's names and SPY, QQQ and IWM).

Every reading here is context (class "context", side 0, strength 0): it is read and shown, and votes nothing (the
desk's rule: a new reading never votes until a study shows it predicts). A read uses a gather of its own session or a
later one, never an older one as if fresh (current()); a name the gather did not read leaves its lines to the
registry's "none".
  options.iv      the 30-day at-the-money implied volatility; put/call by volume and by open interest (row 47)
  options.ivrv    realized volatility over 20 sessions (sqrt(252) x the sd of 20 daily log returns, from the read's own
                  bars) against the implied; IV rank waits for a year of stored IV30 (row 48)
  options.gex     net dealer gamma per 1% move, and its size against the name's 20-day average dollar volume (row 49;
                  the sign rests on the convention that dealers are long the calls and short the puts: the How it
                  works page's to say, not each card's, the owner's no-caveat rule of 2026-10-26)
  options.market  the same numbers for SPY, QQQ and IWM (row 50)
  news.count      the stories naming it in the last 24 hours and 7 days (row 58); its latest headlines go beside the
                  read as plain text (headlines()), never into a sentence
refresh() gives a listed card the session's lines: the card keeps the read it was listed with, so a card listed
before the session's gather would otherwise never show them (its listing's own options and news readings leave what
else it considered: the session's are on the sheet)."""
import math
import re
import urllib.parse
import unicodedata
from datetime import datetime

from ... import calendar as cal
from ...util import ET, parse_ts
from . import sheet
from .core import Fact
from .words import short_day

FUNDS = ("SPY", "QQQ", "IWM")
STALE = ("Options: ", "Realized volatility ", "Net dealer gamma ", "News: ") + tuple(f"{f} put/call" for f in FUNDS)
IV_RANK_N = 252                 # IV rank and percentile read a year of stored sessions (tastylive)
NEWS = "News: "                 # the news reading's lead: a listed card's row 58 keeps its other parts by it
OWN = ("options.iv", "options.ivrank", "options.gex", "options.market")   # the lines these facts alone answer
HEADLINES, URL_MAX = 3, 500
CURRENCY = re.compile("[$¢£¥€]")   # the page refuses an edition holding one (web/terminal/app.js)


def refused(text):
    """a string the page would refuse (a currency sign: the edition holds no price) or the publisher would block (an
    address, a token's shape: desk/terminal/publish.py SECRET_SHAPES)"""
    from ..publish import SECRET_SHAPES
    return bool(CURRENCY.search(text)) or any(p.search(text) for p in SECRET_SHAPES)


def link(url):
    """a plain http(s) URL the page may link and the publisher accepts"""
    if not isinstance(url, str) or not url or len(url) > URL_MAX or \
            any(ch.isspace() or unicodedata.category(ch).startswith("C") for ch in url):
        return False
    try:
        p = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc) and not refused(url)


def rv20(closes, n=20):
    """realized volatility: sqrt(252) x the sample standard deviation of the last n daily log returns; None under n
    returns or on a close that is not positive"""
    c = [float(x) for x in list(closes or [])[-(n + 1):]]
    if len(c) < n + 1 or min(c) <= 0:
        return None
    r = [math.log(b / a) for a, b in zip(c, c[1:])]
    m = sum(r) / n
    return math.sqrt(252.0 * sum((x - m) ** 2 for x in r) / (n - 1))


def current(doc, session):
    """the gather when it is of `session` (an ISO date) or later, else None"""
    if isinstance(doc, dict) and isinstance(doc.get("session"), str) and isinstance(session, str) and \
            doc["session"] >= session:
        return doc
    return None


def _n(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if math.isfinite(v) else None


def _count(v):
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else None


def _vol(v):
    v = _n(v)
    return v if v is not None and 0 < v <= 5 else None


def _p(x):
    return f"{x * 100:.0f}%"


def _r(x):
    return f"{x:.2f}"


def _dollars(v):
    a = abs(v)
    s = f"{a / 1e9:.1f} billion" if a >= 1e9 else f"{a / 1e6:.0f} million" if a >= 1e6 else \
        f"{a / 1e3:.0f} thousand" if a >= 1e3 else f"{a:.0f}"
    return ("+" if v > 0 else "−" if v < 0 else "") + s + " dollars"


def _share(x):
    return f"{x * 100:.1f}%" if x * 100 >= 0.1 else "under 0.1%"


def _when(ts):
    t = _n(ts)
    if t is None:
        return ""
    d = datetime.fromtimestamp(t, tz=ET)
    return f"{short_day(d.date())} at {d:%H:%M} ET"


def _day(v):
    try:
        return short_day(v) if isinstance(v, str) else ""
    except ValueError:
        return ""


def _iso(v):
    """a time as the page reads one (ISO 8601 with its offset, New York time) from any form parse_ts reads, or
    None: the page refuses an edition holding a time it cannot parse"""
    if not isinstance(v, str) or not v.strip():
        return None
    try:
        return datetime.fromtimestamp(parse_ts(v.strip()), tz=ET).isoformat(timespec="seconds")
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _stories(k):
    return "no stories" if k == 0 else "1 story" if k == 1 else f"{k} stories"


def _fact(key, family, head, text, reading, data):
    return Fact(key, family, "context", 0, 0.0, head, text, reading, "", 0.0, data)


def _iv(sym, closes, g, names, me):
    iv, pv, po = _vol(me.get("iv30")), _n(me.get("pc_volume")), _n(me.get("pc_oi"))
    if iv is None and pv is None and po is None:
        return None
    when = _when(me.get("at") or g.get("at"))
    pcs = [w for w in (f"{_r(pv)} by volume" if pv is not None else "",
                       f"{_r(po)} by open interest" if po is not None else "") if w]
    bits = ([f"implied volatility {_p(iv)} (30 days, at the money)"] if iv is not None else []) + \
        (["put/call " + ", ".join(pcs)] if pcs else [])
    said = ([f"options at the money price {_p(iv)} a year over the next 30 days"] if iv is not None else []) + \
        ([f"puts traded {_r(pv)} to each call in the session"] if pv is not None else []) + \
        ([f"open interest holds {_r(po)} puts to each call" + (f" (at the {_day(me.get('oi_date'))} close)"
                                                             if _day(me.get("oi_date")) else "")]
         if po is not None else [])
    text = "; ".join(said) + (f", read {when}" if when else "") + "."
    head = f"Implied volatility {_p(iv)}" if iv is not None else "Options positioning"
    return _fact("options.iv", "Options", head, text[0].upper() + text[1:],
                 "Options: " + "; ".join(bits + ([when] if when else [])),
                 {"iv30": iv, "pc_volume": pv, "pc_oi": po})


def _ivrv(sym, closes, g, names, me):
    rv = rv20(closes)
    if rv is None:
        return None
    iv = _vol(me.get("iv30"))
    if iv is None:                                    # what the read has, with no word on what it has not
        return _fact("options.ivrv", "Options", f"Realized volatility {_p(rv)}",
                     f"Its realized volatility over the last 20 sessions is {_p(rv)} a year.",
                     f"Realized volatility {_p(rv)} over 20 sessions", {"rv20": rv})
    d = (iv - rv) * 100
    gap = "level with realized" if abs(d) < 0.5 else f"{abs(d):.0f} points {'over' if d > 0 else 'under'} realized"
    k = _count(me.get("iv_sessions"))               # the IV rank's store (a year of readings: IV_RANK_N), kept in data
    return _fact("options.ivrv", "Options", f"Implied {_p(iv)}, realized {_p(rv)}",
                 f"Options price {_p(iv)} a year over 30 days against {_p(rv)} realized over the last 20 sessions: "
                 f"implied {gap}.",
                 f"Realized volatility {_p(rv)} over 20 sessions, implied {_p(iv)}: {gap}",
                 {"rv20": rv, "iv30": iv, "iv_sessions": k})


def _gex(sym, closes, g, names, me):
    v = _n(me.get("gex"))
    if v is None:
        return None
    dv, cov = _n(me.get("dv20")), _n(me.get("gex_cover"))
    size = f", as large as {_share(abs(v) / dv)} of an average day's dollar volume (20 sessions)" \
        if dv and dv > 0 else ""
    reading = f"Net dealer gamma {_dollars(v)} per 1% move{size}"      # its coverage stays in data (gex_cover)
    return _fact("options.gex", "Options", f"Dealer gamma {_dollars(v)} per 1% move", reading + ".", reading,
                 {"gex": v, "dv20": dv, "gex_cover": cov})


def _market(sym, closes, g, names, me):
    parts, any_gex = [], False
    for f in FUNDS:
        n = names.get(f) if isinstance(names.get(f), dict) else {}
        pv, po, gx = _n(n.get("pc_volume")), _n(n.get("pc_oi")), _n(n.get("gex"))
        pcs = [w for w in (f"{_r(pv)} by volume" if pv is not None else "",
                           f"{_r(po)} by open interest" if po is not None else "") if w]
        seg = (["put/call " + ", ".join(pcs)] if pcs else []) + \
            ([f"dealer gamma {_dollars(gx)}"] if gx is not None else [])
        any_gex = any_gex or gx is not None
        if seg:
            parts.append(f"{f} " + ", ".join(seg))
    if not parts:
        return None
    when = _when(g.get("at"))
    reading = "; ".join(parts + (["dealer gamma per 1% move"] if any_gex else []) + ([when] if when else []))
    return _fact("options.market", "Market", "The market's put/call and dealer gamma", reading + ".", reading,
                 {f: {k: _n((names.get(f) or {}).get(k)) for k in ("pc_volume", "pc_oi", "gex")}
                  for f in FUNDS if isinstance(names.get(f), dict)})


def _news(sym, closes, g, names, me):
    nw = g.get("news") if isinstance(g.get("news"), dict) else {}
    n = nw.get(sym) if isinstance(nw.get(sym), dict) else None
    if n is None:
        return None
    day, week = _count(n.get("day")), _count(n.get("week"))
    d_ok = day is not None and (n.get("day_whole") is True or n.get("whole") is True)
    w_ok = week is not None and n.get("whole") is True
    if not d_ok and not w_ok:
        return None
    if d_ok and w_ok:
        body = "no stories in the last 7 days" if week == 0 else \
            f"{_stories(day)} in the last 24 hours, {week} in 7 days"
    elif d_ok:
        body = f"{_stories(day)} in the last 24 hours"
    else:
        body = f"{_stories(week)} in the last 7 days"
    when = _when(g.get("news_at") or g.get("at"))
    reading = NEWS + body + (f" ({when})" if when else "")
    return _fact("news.count", "News", "News: " + body, f"Alpaca's news: {body}" + (f", read {when}" if when else "")
                 + ".", reading, {"day": day if d_ok else None, "week": week if w_ok else None})


def facts(sym, closes, session, doc):
    """the read's options and news facts (module docstring), each built on its own: a part it cannot read is left
    out, never raised"""
    g = current(doc, session) or {}
    names = g.get("names") if isinstance(g.get("names"), dict) else {}
    me = names.get(sym) if isinstance(names.get(sym), dict) else {}
    out = []
    for build in (_iv, _ivrv, _gex, _market, _news):
        try:
            f = build(sym, closes, g, names, me)
        except Exception:                                 # noqa: BLE001  (a bad number costs its own line)
            f = None
        if f is not None:
            out.append(f)
    return out


def facts_of(x, extra):
    """facts() for a read: its Ctx and its extra (the gather at extra["optnews"]); [] on anything it cannot read"""
    try:
        session = cal._as_date(float(x.bars[-1]["t"])).isoformat()
        return facts(x.sym, x.c, session, (extra or {}).get("optnews"))
    except Exception:                                     # noqa: BLE001  (never the read's failure)
        return []


def headlines(sym, session, doc):
    """the name's latest headlines as the gather kept them (desk/terminal/optnews.clean), checked again as plain
    strings: [{"headline", "source", "at"[, "url"]}], at most three; [] without a current gather"""
    try:
        g = current(doc, session)
        nw = g.get("news") if g and isinstance(g.get("news"), dict) else {}
        n = nw.get(sym) if isinstance(nw.get(sym), dict) else {}
        out = []
        for it in n.get("items") or ():
            if not isinstance(it, dict):
                continue
            h, src, at = it.get("headline"), it.get("source"), _iso(it.get("at"))
            if not all(isinstance(v, str) and v.strip() for v in (h, src)) or not at or refused(h) or refused(src):
                continue                               # a time the page cannot parse would refuse the whole edition
            item = {"headline": h[:200], "source": src[:40], "at": at}
            if link(it.get("url")):
                item["url"] = it["url"]
            out.append(item)
            if len(out) == HEADLINES:
                break
        return out
    except Exception:                                     # noqa: BLE001
        return []


def refresh(entry, closes, session, doc):
    """a listed card with the session's options and news: it keeps the read it was listed with (its call is scored
    on that read); these lines are context. Rows 47-50 are the session's or none; row 58 keeps its other parts and
    takes the session's news count; the headlines are the session's. A new dict (the stored listing never changes);
    never raises"""
    try:
        got = sheet.found(facts(entry["symbol"], closes, session, doc))
        sh = {k: v for k, v in (entry.get("sheet") or {}).items() if k not in OWN}
        sh.update({k: got[k] for k in OWN if got.get(k)})
        parts = [p for p in str(sh.pop("company", "") or "").split("; ") if p and not p.startswith(NEWS)] + \
            [p for p in str(got.get("company") or "").split("; ") if p.startswith(NEWS)]
        if parts:
            sh["company"] = "; ".join(parts)
        out = dict(entry, sheet=sh, considered=[c for c in entry.get("considered") or () if not c.startswith(STALE)])
        items = headlines(entry["symbol"], session, doc)
        if items:
            out["news"] = items
        else:
            out.pop("news", None)
        return out
    except Exception:                                     # noqa: BLE001  (the card as it was)
        return entry
