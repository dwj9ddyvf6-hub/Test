"""The market read: measured statements from caches the desk already fills. No index values, no composite labels.

  Participation  share of the genome roster (~1,838 names) whose last close is above its 50-day average, beside the 20-
                 and 200-day shares and advancers/decliners; omitted until 90% of the roster reports the session
  S&P 500        SPY's % from its 50- and 200-day averages, and the 200-day's direction over 20 sessions
  Volatility     the VIX's 1-year percentile in words (calm < 20, normal < 60, elevated < 90, high); never its value.
                 The closes are Cboe's own daily file (cache/cboe_daily/VIX_History.csv, which lazarus.refresh_cboe keeps
                 current), or the IDX_VIX record (cache/aurelia) when that file is missing or more than 5 days behind
  Leading        the 11 sector funds, semiconductors, small caps and the equal-weight S&P 500: 20-session return minus
                 SPY's, in points; the top three and the bottom three, named only when all 14 report
  Calendar       the next three scheduled releases (Fed decision, jobs report, CPI) from cache/release_calendar.json
  Badge          the market's state in one word (Risk-on, Mixed, Risk-off) from four checks on the chips and sectors
                 above, with its one most important fact and the checks themselves (badge(); composed per edition)
Computed once per completed session (cache/terminal/market.json, keyed by SPY's last daily bar): the roster read takes
seconds. Worded without expectation verbs (docs/research/2026-10-18-terminal/extract-context.md section 4); the badge
is the one composite label (the owner's ruling of 2026-10-26 allows them)."""
import json
import os
from collections import Counter
from datetime import date, datetime

from .. import calendar as cal
from ..util import ET, read_json, write_json_atomic

SECTORS = (("XLE", "Energy"), ("XLF", "Financials"), ("XLV", "Health care"), ("XLI", "Industrials"),
           ("XLB", "Materials"), ("XLP", "Staples"), ("XLU", "Utilities"), ("XLY", "Discretionary"), ("XLK", "Tech"),
           ("XLC", "Communication"), ("XLRE", "Real estate"), ("SMH", "Semis"), ("IWM", "Small caps"),
           ("RSP", "Equal weight"))
RELEASES = {"FOMC statement": "Fed decision", "Employment Situation": "Jobs report", "CPI": "CPI"}
ROSTER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor", "universes",
                      "old_desk", "genome_universe_1838.txt")
MIN_REPORTING = 200
REPRESENTATIVE = 0.9               # the share of the roster that must report before participation is shown or kept
CHANGE_SESSIONS = 5                # the participation chip's change: its share against the share 5 sessions before
OFFENSIVE = ("Tech", "Semis", "Discretionary", "Communication")   # the risk-on funds of SECTORS (the badge's 4th check)
BADGE_ORDER = ("trend", "participation", "volatility", "sectors")  # the checks, most important first (the badge's line)
BADGE_MIN_CHECKS = 3               # fewer checks than this: no badge
CBOE_VIX = os.path.join("cache", "cboe_daily", "VIX_History.csv")   # Cboe's official daily VIX (lazarus.refresh_cboe)
IDX_VIX = os.path.join("cache", "aurelia", "IDX_VIX.json")          # the older record, read when Cboe's is stale
VIX_STALE_DAYS = 5                 # the chip's own rule (volatility): a last close more than 5 days old is not used


def _date(t):
    return cal._as_date(float(t))


def _mean(xs):
    return sum(xs) / len(xs)


def _pct(x):
    return ("+" if x > 0.05 else "−" if x < -0.05 else "") + f"{abs(x):.1f}%"


def participation(bars_by_sym, as_of):
    """{n, above50, above20, above200, adv, dec} over the names whose last bar is the as_of session, or None"""
    n = a50 = a20 = a200 = n200 = adv = dec = 0
    for bars in bars_by_sym.values():
        if len(bars) < 51 or _date(bars[-1]["t"]) != as_of:
            continue
        c = [float(b["c"]) for b in bars]
        n += 1
        a50 += c[-1] > _mean(c[-50:])
        a20 += c[-1] > _mean(c[-20:])
        if len(c) >= 200:
            n200 += 1
            a200 += c[-1] > _mean(c[-200:])
        adv += c[-1] > c[-2]
        dec += c[-1] < c[-2]
    if n < MIN_REPORTING:
        return None
    return {"n": n, "above50": a50 / n, "above20": a20 / n, "above200": (a200 / n200) if n200 else None,
            "adv": adv, "dec": dec}


def participation_then(bars_by_sym, as_of, k=CHANGE_SESSIONS):
    """participation() on the session k sessions before as_of, each name's bars cut at that session's close"""
    d = as_of
    for _ in range(k):
        d = cal.prev_trading_day(d)
    cut = {}
    for sym, bars in bars_by_sym.items():
        i = len(bars)
        while i and _date(bars[i - 1]["t"]) > d:
            i -= 1
        cut[sym] = bars[:i]
    return participation(cut, d)


def trend(spy):
    """SPY vs its 50- and 200-day averages, and the 200-day's 20-session direction, or None"""
    if len(spy) < 221:
        return None
    c = [float(b["c"]) for b in spy]
    m50, m200, m200_then = _mean(c[-50:]), _mean(c[-200:]), _mean(c[-220:-20])
    return {"vs50": (c[-1] / m50 - 1) * 100, "vs200": (c[-1] / m200 - 1) * 100, "rising200": m200 > m200_then}


def cboe_vix(path):
    """{"dates", "close"} from a Cboe daily-prices CSV (DATE,OPEN,HIGH,LOW,CLOSE, its dates MM/DD/YYYY), or None"""
    try:
        with open(path) as f:
            lines = f.read().splitlines()
        j = [h.strip().upper() for h in lines[0].split(",")].index("CLOSE")
    except (OSError, IndexError, ValueError):
        return None
    rows = {}
    for line in lines[1:]:
        parts = line.split(",")
        try:
            m, d, y = parts[0].strip().split("/")
            rows[f"{int(y):04d}-{int(m):02d}-{int(d):02d}"] = float(parts[j])
        except (ValueError, IndexError):
            continue
    days = sorted(rows)
    return {"dates": days, "close": [rows[k] for k in days]} if days else None


def vix_doc(root, as_of):
    """the volatility chip's closes: Cboe's own file, unless it is missing, unreadable or its last close on or before
    as_of is more than VIX_STALE_DAYS old; then the IDX_VIX record (None without either)"""
    doc = cboe_vix(os.path.join(root, CBOE_VIX))
    upto = [d for d in (doc or {}).get("dates") or () if d <= as_of.isoformat()]
    if upto and (as_of - date.fromisoformat(upto[-1])).days <= VIX_STALE_DAYS:
        return doc
    return read_json(os.path.join(root, IDX_VIX), None)


def volatility(vix_doc, as_of):
    """{pct, word} from the VIX's closes over the past year (252 sessions), when its last date is within 5 days"""
    dates, closes = (vix_doc or {}).get("dates") or [], (vix_doc or {}).get("close") or []
    pairs = [(d, c) for d, c in zip(dates, closes) if c is not None and d <= as_of.isoformat()]
    if len(pairs) < 252 or (as_of - datetime.fromisoformat(pairs[-1][0]).date()).days > 5:
        return None
    last = pairs[-1][1]
    year = [c for _, c in pairs[-252:]]
    pct = sum(1 for c in year if c <= last) / len(year)
    word = "Calm" if pct < 0.2 else "Normal" if pct < 0.6 else "Elevated" if pct < 0.9 else "High"
    return {"pct": pct, "word": word}


def leadership(bars_by_sym, spy):
    """[(name, points)] sorted high to low: 20-session return minus SPY's"""
    if len(spy) < 21:
        return []
    base = float(spy[-1]["c"]) / float(spy[-21]["c"]) - 1
    out = []
    for sym, name in SECTORS:
        b = bars_by_sym.get(sym) or []
        if len(b) >= 21 and _date(b[-1]["t"]) == _date(spy[-1]["t"]):
            out.append((name, (float(b[-1]["c"]) / float(b[-21]["c"]) - 1 - base) * 100))
    return sorted(out, key=lambda x: -x[1])


def calendar_next(events, now, k=3):
    out = []
    for e in sorted(events or [], key=lambda e: e.get("release_at") or ""):
        try:
            t = datetime.fromisoformat(e["release_at"]).timestamp()
        except (KeyError, TypeError, ValueError):
            continue
        if t > now and e.get("name") in RELEASES:
            out.append({"what": RELEASES[e["name"]], "at": datetime.fromtimestamp(t, tz=ET).isoformat(timespec="minutes")})
        if len(out) >= k:
            break
    return out


def compose(as_of, part, tr, vol, lead, cal_next, ranked=True):
    """the public market block: a sentence, up to four chips, the sector list and the calendar; the leaders and
    laggards are named only when `ranked` (every fund reported)"""
    chips, clauses = [], []
    if part:
        p = part["above50"]
        word = "narrow" if p < 0.4 else "broad" if p > 0.6 else "mixed"
        clauses.append(f"Participation is {word}: {round(p * 100)}% of {part['n']:,} stocks closed above their 50-day average")
        chips.append({"id": "participation", "label": "Participation", "value": f"{round(p * 100)}%",
                      "tone": "up" if p > 0.5 else "down", "bar": round(p, 3),
                      "detail": f"of {part['n']:,} stocks above their 50-day · {part['adv']:,} rose, {part['dec']:,} fell"})
        if part.get("above50_then") is not None:      # its change, in points, over CHANGE_SESSIONS sessions
            chips[-1]["chg"] = round((p - part["above50_then"]) * 100, 1)
    if tr:
        chips.append({"id": "trend", "label": "S&P 500", "value": _pct(tr["vs50"]), "tone": "up" if tr["vs50"] > 0 else "down",
                      "detail": f"vs its 50-day · {_pct(tr['vs200'])} vs a {'rising' if tr['rising200'] else 'falling'} 200-day"})
    if vol:
        chips.append({"id": "volatility", "label": "Volatility", "value": vol["word"], "tone": "up" if vol["pct"] >= 0.6 else "neutral",
                      "bar": round(vol["pct"], 3), "detail": f"higher than {round(vol['pct'] * 100)}% of the past year"})
    if ranked and len(lead) >= 6:
        top, bottom = [n for n, _ in lead[:3]], [n for n, _ in lead[-3:][::-1]]
        chips.append({"id": "leadership", "label": "Leading", "value": " · ".join(top), "tone": "neutral",
                      "detail": "Lagging: " + " · ".join(bottom)})
        clauses.append(f"{_join([_lower(n) for n in top])} led while {_join([_lower(n) for n in bottom])} lagged over "
                       "20 sessions")
    peak = max((abs(p) for _, p in lead), default=0) or 1.0
    sectors = [{"name": n, "rs": round(p / peak, 3), "pts": round(p, 1)} for n, p in lead]
    sentence = ("; ".join(clauses) + ".") if clauses else ""
    return {"as_of": as_of.isoformat() if as_of else None, "sentence": sentence[:1].upper() + sentence[1:],
            "chips": chips, "sectors": sectors, "calendar": cal_next}


def _signed(x, unit=""):
    """+2.5 / −6 / 0, with the page's minus sign"""
    s = f"{abs(x):.1f}".rstrip("0").rstrip(".")
    return ("+" if x > 0 else "−" if x < 0 else "") + s + unit


def badge_checks(mk):
    """[{key, label, ok}] in BADGE_ORDER, one per measure the market block holds, each read from its own chip (or the
    sector list) exactly as published:
      trend          the S&P 500 above its 50-day average: the trend chip's tone is "up"
      participation  half the roster or more above its 50-day average (the chip's whole percent) and not falling over
                     CHANGE_SESSIONS sessions (its chg, when the chip carries one)
      volatility     neither Elevated nor High: the volatility chip's word
      sectors        the four offensive funds (OFFENSIVE) ahead of the S&P 500 on average: the mean of their published
                     20-session points; only when all four report"""
    chips = {c.get("id"): c for c in (mk or {}).get("chips") or ()}
    out = {}
    c = chips.get("trend")
    if c:
        v = str(c.get("value") or "")
        where = "above" if v.startswith("+") else "below" if v[:1] in "−-" else "at"
        out["trend"] = {"key": "trend", "label": f"S&P 500 {v.lstrip('+−-')} {where} its 50-day" if where != "at"
                        else "S&P 500 at its 50-day", "ok": c.get("tone") == "up"}
    c = chips.get("participation")
    if c:
        level, chg = int(str(c["value"]).rstrip("%")), c.get("chg")
        out["participation"] = {"key": "participation", "ok": level >= 50 and (chg is None or chg >= 0),
                                "label": f"{c['value']} of stocks above their 50-day" if chg is None else
                                f"{c['value']} of stocks above 50-day, {_signed(chg)} pts in {CHANGE_SESSIONS} sessions"}
    c = chips.get("volatility")
    if c:
        out["volatility"] = {"key": "volatility", "ok": c.get("value") not in ("Elevated", "High"),
                             "label": f"Volatility {str(c.get('value')).lower()}"
                                      + (f": {c['detail']}" if c.get("detail") else "")}
    pts = {s.get("name"): s.get("pts") for s in (mk or {}).get("sectors") or ()}
    if all(pts.get(n) is not None for n in OFFENSIVE):
        avg = round(sum(pts[n] for n in OFFENSIVE) / len(OFFENSIVE), 1)
        out["sectors"] = {"key": "sectors", "ok": avg > 0,
                          "label": f"Offensive sectors {_signed(avg)} pts vs the S&P 500"}
    return [out[k] for k in BADGE_ORDER if k in out]


def badge(mk, fear=None):
    """{word, tone, line, checks}: the market's state in one word, from badge_checks. Risk-on (tone up) when at least
    three quarters of the checks pass, Risk-off (down) when at most a quarter do, Mixed (warn) otherwise: with all four,
    3-4 pass Risk-on, 2 Mixed, 0-1 Risk-off. line: its single most important fact, the broad fear day when QQQ and SPY
    both closed red on the market's own session (fear: the edition's banner, fear.banner), else the label of the first
    check that agrees with the word (passing for Risk-on, failing otherwise). None with fewer than BADGE_MIN_CHECKS"""
    checks = badge_checks(mk)
    if len(checks) < BADGE_MIN_CHECKS:
        return None
    share = sum(1 for c in checks if c["ok"]) / len(checks)
    word, tone = ("Risk-on", "up") if share >= 0.75 else ("Risk-off", "down") if share <= 0.25 else ("Mixed", "warn")
    if fear and fear.get("both") and fear.get("date") and fear["date"] == (mk or {}).get("as_of"):
        line = "Broad fear day: QQQ and SPY red"
    else:
        line = next(c["label"] for c in checks if c["ok"] == (word == "Risk-on"))
    return {"word": word, "tone": tone, "line": line, "checks": checks}


def _lower(name):
    """a sector name inside a sentence: 'Health care' -> 'health care'; an acronym or a name like 'S&P' stays"""
    return name if len(name) < 2 or not name[1].islower() else name[0].lower() + name[1:]


def _join(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def with_today(hub, now, bars_by_sym):
    """(bars, live_at): during a trading day from the open, each name's daily history with today's forming bar
    appended from Alpaca's snapshots (200 names a request), so an edition opened mid-session reads the session it is
    in; (bars, None) before the open, on a closed day, without Alpaca, or when the history already holds today."""
    d = cal._as_date(float(now))
    if hub is None or not getattr(hub, "alpaca", None) or not cal.is_trading_day(d) or now < cal.session_open(d):
        return bars_by_sym, None
    need = [s for s, b in bars_by_sym.items() if b and _date(b[-1]["t"]) < d]
    if not need:
        return bars_by_sym, None
    try:
        q = hub.quotes("alpaca", need, max_age=600.0, full=True) or {}
    except Exception:
        return bars_by_sym, None
    out, t, added = dict(bars_by_sym), cal.session_open(d), 0
    for s in need:
        x = q.get(s) or {}
        c = x.get("last") or x.get("day_close")
        if x.get("day_date") != d.isoformat() or not c:
            continue
        o, h, l = x.get("day_open") or c, x.get("day_high") or c, x.get("day_low") or c
        out[s] = list(bars_by_sym[s]) + [{"t": t, "o": o, "h": max(h, c), "l": min(l, c), "c": c,
                                           "v": x.get("day_volume") or 0}]
        added += 1
    return out, (float(now) if added else None)


def read(root, hub, now, diag=None):
    """the market block for this edition: recomputed when SPY's last completed daily bar changes, else the cached one
    with a fresh calendar. diag (a dict) receives how much of the roster reported: internal, never in the edition"""
    diag = {} if diag is None else diag
    cache = os.path.join(root, "cache", "terminal", "market.json")
    events = (read_json(os.path.join(root, "cache", "release_calendar.json"), {}) or {}).get("events")
    if hub is None:
        return None
    spy = (hub.bars("equity_split", "1d", ["SPY"], 260, cache_only=True) or {}).get("SPY") or []
    if not spy:
        return None
    live, live_at = with_today(hub, now, {"SPY": spy})      # mid-session: today's forming bar (with_today)
    spy = live["SPY"]
    as_of = _date(spy[-1]["t"])
    doc = read_json(cache, None)
    if doc and doc.get("as_of") == as_of.isoformat() and (not live_at or doc.get("live_at", 0) > now - 1500):
        doc["calendar"] = calendar_next(events, now)
        diag.update(as_of=as_of.isoformat(), cached=True)
        return doc
    roster = [l.strip().upper() for l in open(ROSTER) if l.strip()]
    bars = {}
    for i in range(0, len(roster), 200):                   # cache-only: the genome job keeps these bars
        bars.update(hub.bars("equity_split", "1d", roster[i:i + 200], 210, cache_only=True) or {})
    etfs = hub.bars("equity_split", "1d", [s for s, _ in SECTORS], 30, cache_only=True) or {}
    if live_at:
        bars, _ = with_today(hub, now, bars)
        etfs, _ = with_today(hub, now, etfs)
    vix = vix_doc(root, as_of)              # Cboe's own closes first (the module docstring)
    part = participation(bars, as_of)
    diag["part"] = part                     # the very dict the chip is composed from (dash.py's last day equals it)
    if part:                                # the share CHANGE_SESSIONS sessions before, the same way (the chip's chg)
        then = participation_then(bars, as_of)
        part["above50_then"] = then["above50"] if then else None
    # after a close the roster's bars arrive over the genome job's run, and a part of the roster is not the market (the
    # first live edition read "19% of 389 stocks" where the whole roster read 31%): until most report, participation
    # is neither shown nor kept, and the next edition reads the roster again
    whole = bool(part) and part["n"] >= REPRESENTATIVE * len(roster)
    diag.update(as_of=as_of.isoformat(), cached=False, roster=len(roster), read=len(bars),
                reporting=part["n"] if part else sum(1 for b in bars.values() if len(b) >= 51 and _date(b[-1]["t"]) == as_of),
                short=sum(1 for b in bars.values() if 0 < len(b) < 51),
                last_dates=dict(Counter(_date(b[-1]["t"]).isoformat() for b in bars.values() if b).most_common(4)))
    lead = leadership(etfs, spy)            # a ranking over some of the funds is not the ranking: the first live edition
    vol = volatility(vix, as_of)            # named Utilities a leader from 8 of 14, with Health care missing and third
    diag.update(sectors=f"{len(lead)}/{len(SECTORS)}", volatility=bool(vol))
    doc = compose(as_of, part if whole else None, trend(spy), vol, lead, calendar_next(events, now),
                  ranked=len(lead) == len(SECTORS))
    if live_at:
        doc["live_at"] = live_at
    if whole and len(lead) == len(SECTORS):
        write_json_atomic(cache, doc)
    return doc


def roster_names():
    """the roster's symbols (ROSTER), [] when the file cannot be read"""
    try:
        return [l.strip().upper() for l in open(ROSTER) if l.strip()]
    except OSError:
        return []
