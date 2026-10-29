"""The terminal's dashboards, published beside the edition and fetched lazily by the page.

  charts.json  every board card's and watching name's daily bars (126 sessions) with the read's own simple averages
               (20, 50 and 200-day: read/core.Ctx's, over the same bars), its weekly bars over two years and a 30-close
               spark, plus SPY's and QQQ's
  market.json  the market tab: the sector and theme heatmap, participation, big movers, ChartsLector's breadth score,
               Market Action Pulse, risk appetite and rotation, and his VIX Mood Ring with the edition's volatility

Both read the bars the edition reads, cache-only (hub "equity_split", "1d"): nothing here fetches. Each document is
checked against its allow-list (CHARTS_ALLOWED, MARKET_ALLOWED) before it is written to cache/terminal/dash/, where the
publisher (publish.py) ships it with the edition. Compact JSON; prices in cents, volumes whole."""
import gzip
import json
import math
import os
import tempfile
import time

from .. import calendar as cal
from . import market
from .read import ta

BARS = 1300                     # the depth the edition reads (terminal.BARS): five years, cache-only
CHART_DAYS = 126                # daily bars on a card's chart
CHART_WEEKS = 104               # weekly bars: two years
SPARK = 30                      # closes in a spark
CHART_EXTRA = ("SPY", "QQQ")    # the index charts beside the board's names
CHARTS_MAX_GZ = 80_000          # charts.json's budget, gzipped (5 cards + 6 watching + 2 index funds)

# every key a dashboard may carry, by path ("x.*" = each value of the map x, "x[]" = each object of the list x; any
# other list holds plain values only)
CHARTS_ALLOWED = {
    "": {"v", "as_of", "generated_at", "syms", "spark"},
    "syms.*": {"d", "o", "h", "l", "c", "v", "sma20", "sma50", "sma200", "w"},
    "syms.*.w": {"d", "o", "h", "l", "c", "v"},
    "spark.*": None,
}


def validate(doc, allowed, path=""):
    """raise ValueError on any key outside `allowed`: nothing reaches the public site that its contract does not name"""
    if isinstance(doc, dict):
        keys = allowed.get(path)
        if keys is None and path + ".*" in allowed:          # a map of named entries (a symbol, say)
            for v in doc.values():
                validate(v, allowed, path + ".*")
            return doc
        if not isinstance(keys, (set, frozenset)):
            raise ValueError(f"unexpected object at {path or 'top'}")
        for k, v in doc.items():
            child = f"{path}.{k}" if path else k
            if k not in keys:
                raise ValueError(f"key not in the contract: {child}")
            validate(v, allowed, child)
    elif isinstance(doc, list):
        if path + "[]" in allowed:
            for x in doc:
                if not isinstance(x, dict):
                    raise ValueError(f"{path} must hold objects")
                validate(x, allowed, path + "[]")
        elif any(isinstance(x, (dict, list)) for x in doc):
            raise ValueError(f"{path} must hold plain values")
    return doc


def _iso(t):
    return cal._as_date(float(t)).isoformat()


def _cents(x):
    return None if x is None else round(float(x), 2)


def _whole(x):
    return int(round(float(x or 0)))


# ---------------------------------------------------------------------------------------------------- charts.json

def chart_symbols(edition):
    """the board's cards, then its watching names, then SPY and QQQ: each once, in that order"""
    out = [s.get("symbol") for s in (edition or {}).get("setups") or ()]
    out += [w.get("symbol") for w in (edition or {}).get("watching") or ()]
    return list(dict.fromkeys(s for s in out + list(CHART_EXTRA) if s))


def spark_of(bars, n=SPARK):
    return [_cents(b["c"]) for b in bars[-n:]]


def chart_one(bars, days=CHART_DAYS, weeks=CHART_WEEKS):
    """{d, o, h, l, c, v, sma20, sma50, sma200, w: {d, o, h, l, c, v}} of ascending daily bars, or None. The simple
    averages are the read's (read/core.Ctx: ta.sma over the bars that have a close), cut to the chart's sessions, so
    each last value is the one the card's words cite; a week (Monday to Friday, read/ta.weekly) is dated by its first
    session, the current week to date"""
    bars = [b for b in bars or () if b.get("c") is not None]
    if not bars:
        return None
    closes = ta.closes(bars)
    tail = bars[-days:]
    k = len(bars) - len(tail)
    avgs = {"sma20": ta.sma(closes, 20), "sma50": ta.sma(closes, 50), "sma200": ta.sma(closes, 200)}
    out = {"d": [_iso(b["t"]) for b in tail]}
    for f in ("o", "h", "l", "c"):
        out[f] = [_cents(b[f]) for b in tail]
    out["v"] = [_whole(b.get("v")) for b in tail]
    for name, xs in avgs.items():
        out[name] = [_cents(x) for x in xs[k:]]
    wk = ta.weekly(bars)[-weeks:]
    out["w"] = {"d": [_iso(w["t"]) for w in wk], "o": [_cents(w["o"]) for w in wk], "h": [_cents(w["h"]) for w in wk],
                "l": [_cents(w["l"]) for w in wk], "c": [_cents(w["c"]) for w in wk], "v": [_whole(w["v"]) for w in wk]}
    return out


def charts(hub, edition, now):
    """charts.json for this edition: the bars the edition reads, cache-only; a name the cache does not hold is left
    out (the card draws no chart)"""
    syms = chart_symbols(edition)
    got = (hub.bars("equity_split", "1d", syms, BARS, cache_only=True) or {}) if hub is not None and syms else {}
    got, _ = market.with_today(hub, now, got)          # mid-session: today's forming bar (market.with_today)
    out, spark = {}, {}
    for s in syms:
        ch = chart_one(got.get(s) or [])
        if ch:
            out[s], spark[s] = ch, spark_of(_closes(got[s]))
    spy = got.get("SPY") or []
    as_of = _iso(spy[-1]["t"]) if spy else max((ch["d"][-1] for ch in out.values()), default=None)
    return validate({"v": 1, "as_of": as_of, "generated_at": int(now), "syms": out, "spark": spark}, CHARTS_ALLOWED)


# ---------------------------------------------------------------------------------------------------- market.json: heat
# The heatmap's funds: the desk's sector funds (market.SECTORS, the edition's sector strength) and ChartsLector's theme
# funds, the 35 tickers of his "Relative Strength & Relative Volume Table" (github.com/ChartsLector/TV-Indicators, after
# @oratnek_ill's RS Table), XLF and SMH shown once, as sectors. Each tile: the returns over 1, 5, 21 and 63 sessions,
# his RS rank (Pine ta.percentrank(close / SPY, 21): the share of the previous 21 sessions whose price relative to SPY
# was at or below today's, 0-100) and his RVol (today's volume over its 50-session simple average, today included).

CL_RS_TABLE = ("XLF", "SMH", "IGV", "BAI", "AIQ", "DRAM", "QTUM", "EUV", "IYZ", "CIBR", "WGMI", "DTCR", "IGPT", "ICLN",
               "TAN", "PBW", "BOTZ", "DRIV", "IDRV", "SNSR", "JEDI", "JETS", "SHLD", "DXYZ", "UFO", "NASA", "LIT", "BATT",
               "REMX", "URA", "AIPO", "ARKG", "PPH", "USO", "XRT")          # his table's tickers, in his order
THEME_NAMES = {"IGV": "Software", "BAI": "AI and tech", "AIQ": "AI and technology", "DRAM": "Memory",
               "QTUM": "Quantum computing", "EUV": "Lithography", "IYZ": "Telecom", "CIBR": "Cybersecurity",
               "WGMI": "Bitcoin miners", "DTCR": "Data centers", "IGPT": "AI and software", "ICLN": "Clean energy",
               "TAN": "Solar", "PBW": "Clean tech", "BOTZ": "Robotics and AI", "DRIV": "Autonomous and EVs",
               "IDRV": "Self-driving and EVs", "SNSR": "Internet of things", "JEDI": "Drones", "JETS": "Airlines",
               "SHLD": "Defense tech", "DXYZ": "Private tech", "UFO": "Space", "NASA": "Space innovators",
               "LIT": "Lithium and batteries", "BATT": "Battery tech", "REMX": "Rare earths", "URA": "Uranium",
               "AIPO": "AI power", "ARKG": "Genomics", "PPH": "Pharma", "USO": "Oil", "XRT": "Retail"}
CREDIT_SECTOR = "ChartsLector's RS rank and RVol"
CREDIT_THEME = "ChartsLector's theme list, RS rank and RVol"
_SECTOR_SYMS = {s for s, _ in market.SECTORS}
HEAT_FUNDS = tuple((s, n, "sector", CREDIT_SECTOR) for s, n in market.SECTORS) + tuple(
    (s, THEME_NAMES[s], "theme", CREDIT_THEME) for s in CL_RS_TABLE if s not in _SECTOR_SYMS)
HEAT_MIN = 64                   # sessions a tile needs: every field defined (the 63-session return)
RET_SESSIONS = (("d1", 1), ("w1", 5), ("m1", 21), ("m3", 63))
RS_N, RVOL_N = 21, 50           # his RS period 2 (the table's default sort) and his RVol average


def _closes(bars):
    return [b for b in bars or () if b.get("c") is not None]


def prank(xs, n):
    """Pine ta.percentrank(x, n): 100 x the share of the previous n values at or below the current one; None short"""
    if len(xs) < n + 1:
        return None
    cur = xs[-1]
    return 100.0 * sum(1 for x in xs[-1 - n:-1] if x <= cur) / n


def heat(bars_by_sym, as_of, funds=HEAT_FUNDS):
    """([tile], {sym: why it was left out}): a tile for each fund whose cached bars reach the as_of session with
    HEAT_MIN sessions: {sym, name, group, close, ret: {d1, w1, m1, m3} in %, rs 0-100, rvol (x its average), credit}"""
    spy = {_iso(b["t"]): float(b["c"]) for b in _closes(bars_by_sym.get("SPY"))}
    rows, out = [], {}
    for sym, name, group, credit in funds:
        bars = _closes(bars_by_sym.get(sym))
        if not bars:
            out[sym] = "not cached"
            continue
        last = _iso(bars[-1]["t"])
        if last != as_of:
            out[sym] = f"last bar {last}, not {as_of}"
            continue
        if len(bars) < HEAT_MIN:
            out[sym] = f"{len(bars)} sessions, needs {HEAT_MIN}"
            continue
        c = [float(b["c"]) for b in bars]
        rel = [x / spy[d] for d, x in ((_iso(b["t"]), x) for b, x in zip(bars, c)) if spy.get(d)]
        rs = prank(rel, RS_N)
        v = [float(b.get("v") or 0) for b in bars[-RVOL_N:]]
        avg = sum(v) / len(v)
        rows.append({"sym": sym, "name": name, "group": group, "close": _cents(c[-1]),
                     "ret": {k: round((c[-1] / c[-1 - n] - 1) * 100, 2) for k, n in RET_SESSIONS},
                     "rs": None if rs is None else round(rs), "rvol": round(v[-1] / avg, 2) if avg > 0 else None,
                     "credit": credit})
    return rows, out


# ---------------------------------------------------------------------------------------------------- market.json
PULSE_FUNDS = ("QQQE", "RSP")   # his Market Action Pulse's health symbols
RISK_PAIRS = (("IEF", "LQD"), ("HYG", "SHY"), ("RPG", "RPV"), ("IWO", "IWN"), ("IJK", "IJJ"), ("QQQ", "QQQE"))
# every fund market.json reads, cache-only: the genome job (desk/jobs.py) keeps them at BARS after each close
FUNDS = tuple(dict.fromkeys([f[0] for f in HEAT_FUNDS] + list(PULSE_FUNDS) + [s for p in RISK_PAIRS for s in p]
                            + ["SPY"]))

MARKET_MAX_GZ = 60_000          # market.json's budget, gzipped
HIST = 130                      # sessions of history in the participation, movers, breadth, Pulse and risk lines
MOOD_DAYS = 252                 # the Mood Ring's and the volatility percentile's history: a year
# the Mood Ring (Cboe's VIX, VIX3M, VVIX and SKEW) is the one Cboe-derived block: every value it yields lives in "mood",
# and MOOD = False drops it, the Pulse's risk model then reading without its volatility family (the owner allowed Cboe
# data on 2026-10-26; the switch stays)
MOOD = True
# its words say how big moves have been after such readings, never which way: in the program's 10-year test (Addendum
# 2-21, scratchpad/eyes/DEEP/out2/vmr.md) the CONFIRMED effects are all next-20-session realized volatility - bigger
# moves after Backwardation (VIX at or above VIX3M) and in the score's lowest quintile, smaller ones in its top two
# (cut on the discovery era: 59.58 and 76.99) - and no return effect is
MOOD_CUTS = {"bigger_below": 59.58, "smaller_from": 76.99}
MOOD_WORDS = {"bigger": "Stressed · bigger moves likely", "usual": "Normal · usual-size moves",
              "smaller": "Calm · smaller moves likely"}
MOOD_BASIS = "10-year test: predicts move size, not direction"

MARKET_ALLOWED = {
    "": {"v", "as_of", "generated_at", "n_roster", "heat", "participation", "movers", "breadth", "pulse", "risk",
         "rotation", "mood"},
    "heat[]": {"sym", "name", "group", "close", "ret", "rs", "rvol", "credit"},
    "heat[].ret": {"d1", "w1", "m1", "m3"},
    "participation": {"days"},
    "participation.days[]": {"d", "a20", "a50", "a200", "n"},
    "movers": {"days"},
    "movers.days[]": {"d", "up4", "dn4", "n"},
    "breadth": {"credit", "score", "of", "up4", "dn4", "up13", "dn13", "up25", "dn25", "up25_ma20", "adv", "dec",
                "days"},
    "breadth.days[]": {"d", "sc"},
    "pulse": {"credit", "states", "funds"},
    "pulse.funds[]": {"sym", "state", "score", "ram", "ram_level", "checks", "days"},
    "pulse.funds[].checks": {"above_rising_5ema", "daily_buy", "weekly_buy", "breadth_uptrend", "breadth_attempt"},
    "pulse.funds[].days[]": {"d", "sc", "ram"},
    "risk": {"credit", "on", "of", "pairs", "days"},
    "risk.pairs[]": {"pair", "above", "on", "chg_1m", "rising"},
    "risk.days[]": {"d", "n"},
    "rotation": {"freq", "credit", "funds", "left_out"},
    "rotation.left_out[]": {"sym", "why"},
    "rotation.funds[]": {"sym", "name", "group", "ratio", "mom", "quad", "tail"},
    "rotation.funds[].tail[]": {"d", "ratio", "mom"},
    "mood": {"credit", "source", "as_of", "basis", "score", "band", "word", "backwardation", "cuts", "inputs", "parts",
             "weights", "bands", "days", "vol"},
    "mood.cuts": {"bigger_below", "smaller_from"},
    "mood.inputs": {"vix", "vix3m", "term", "vvix", "skew"},
    "mood.parts": {"vix", "term", "skew", "vvix"},
    "mood.weights": {"vix", "term", "skew", "vvix"},
    "mood.bands[]": {"lo", "band"},
    "mood.days[]": {"d", "v"},
    "mood.vol": {"def", "as_of", "word", "pct", "bands", "days"},
    "mood.vol.bands[]": {"lo", "hi", "word"},
    "mood.vol.days[]": {"d", "pct"},
}


def _roster():
    try:
        return [l.strip().upper() for l in open(market.ROSTER) if l.strip()]
    except OSError:
        return []


# ---------------------------------------------------------------------------------------------------- market.json: roster
# One pass over the roster's cached bars (market.ROSTER, the 1,838-name genome) gives every roster block. A name
# reports a session when it has a bar dated that session and MIN_BARS bars up to it: market.participation's rule, so
# the participation, movers and breadth counts share one universe, the chip's.

MIN_BARS = 51                   # market.participation: a name counts with 51 bars or more
ROSTER_DEPTH = 420              # bars per name: 200 for the 200-day share, HIST sessions of history, the Pulse's warm-up
CREDIT_BREADTH = "Breadth score, after ChartsLector"


def roster_pass(bars_by_sym, days, hist=HIST):
    """a row per session of `days` (ascending ISO dates) over the names reporting it: n; adv and dec (closes above and
    below the name's previous close); up4 and dn4 (a day's change of +4% or more, -4% or less); up13 and dn13 (over 34
    sessions, 13%); up25 and dn25 (over 63 sessions, 25%); and for the last `hist` sessions a20, a50 and a200, the
    shares market.participation() gives that session (None under its MIN_REPORTING): the same slices summed the same
    way, so each share is the chip's float exactly"""
    pos = {d: k for k, d in enumerate(days)}
    want = set(days[-hist:])
    acc = [{"d": d, "n": 0, "adv": 0, "dec": 0, "up4": 0, "dn4": 0, "up13": 0, "dn13": 0, "up25": 0, "dn25": 0,
            "k20": 0, "k50": 0, "k200": 0, "n200": 0} for d in days]
    isos = {}
    for bars in (bars_by_sym.values() if isinstance(bars_by_sym, dict) else bars_by_sym):   # a dict, or a stream
        bars = _closes(bars)
        c = [float(b["c"]) for b in bars]
        for i in range(MIN_BARS - 1, len(bars)):
            t = bars[i]["t"]
            d = isos.get(t)
            if d is None:
                d = isos[t] = _iso(t)
            k = pos.get(d)
            if k is None:
                continue
            r, x, prev = acc[k], c[i], c[i - 1]
            r["n"] += 1
            r["adv"] += x > prev
            r["dec"] += x < prev
            r1 = x / prev - 1
            r["up4"] += r1 >= 0.04
            r["dn4"] += r1 <= -0.04
            if i >= 34:
                r34 = x / c[i - 34] - 1
                r["up13"] += r34 >= 0.13
                r["dn13"] += r34 <= -0.13
            if i >= 63:
                r63 = x / c[i - 63] - 1
                r["up25"] += r63 >= 0.25
                r["dn25"] += r63 <= -0.25
            if d in want:                                  # market.participation: c[-1] > _mean(c[-n:]), sum / len
                r["k50"] += x > sum(c[i - 49:i + 1]) / 50
                r["k20"] += x > sum(c[i - 19:i + 1]) / 20
                if i >= 199:
                    r["n200"] += 1
                    r["k200"] += x > sum(c[i - 199:i + 1]) / 200
    out = []
    for r in acc:
        n = r["n"]
        ok = r["d"] in want and n >= market.MIN_REPORTING
        out.append({k: r[k] for k in ("d", "n", "adv", "dec", "up4", "dn4", "up13", "dn13", "up25", "dn25")})
        out[-1].update(a20=r["k20"] / n if ok else None, a50=r["k50"] / n if ok else None,
                       a200=(r["k200"] / r["n200"] if r["n200"] else None) if ok else None)
    return out


def breadth_scores(rows):
    """ChartsLector's breadth score per row, 0-12 (None before 21 rows): each of up4, up13 above its 5, 10 and
    21-session averages and each of dn4, dn13 below them, today included in each average"""
    out = []
    for i, row in enumerate(rows):
        if i < 20:
            out.append(None)
            continue
        s = 0
        for up, dn in (("up4", "dn4"), ("up13", "dn13")):
            for k in (5, 10, 21):
                w = rows[i - k + 1:i + 1]
                s += row[up] > sum(r[up] for r in w) / k
                s += row[dn] < sum(r[dn] for r in w) / k
        out.append(s)
    return out


def breadth_block(rows, hist=HIST):
    """{credit, score, of, the last session's counts, up25_ma20 (up25 above its 20-session average), days: [{d, sc}]}"""
    sc = breadth_scores(rows)
    last = rows[-1]
    out = {"credit": CREDIT_BREADTH, "score": sc[-1], "of": 12}
    out.update({k: last[k] for k in ("up4", "dn4", "up13", "dn13", "up25", "dn25")})
    out["up25_ma20"] = len(rows) >= 20 and last["up25"] > sum(r["up25"] for r in rows[-20:]) / 20
    out.update(adv=last["adv"], dec=last["dec"], days=[{"d": r["d"], "sc": v} for r, v in zip(rows, sc)
                                                       if v is not None][-hist:])
    return out


def participation_block(rows, hist=HIST):
    return {"days": [{"d": r["d"], "a20": r["a20"], "a50": r["a50"], "a200": r["a200"], "n": r["n"]}
                     for r in rows[-hist:] if r["a50"] is not None]}


def movers_block(rows, hist=HIST):
    return {"days": [{"d": r["d"], "up4": r["up4"], "dn4": r["dn4"], "n": r["n"]} for r in rows[-hist:] if r["n"]]}


# ---------------------------------------------------------------------------------------------------- market.json: Pulse
# ChartsLector's Market Action Pulse and Risk Assessment Model ("Market Action Pulse & VIX Mood Ring", HEAD 34ec657 of
# github.com/ChartsLector/TV-Indicators), as the owner's GrokBot tab computes them (CHARTSLECTOR/systems/map_vmr_ram.py,
# variant "live", trap "as written", version "latest"), on QQQE and RSP. His breadth feed (Nasdaq advances and
# declines) is stood in for by the roster's: the names reporting each session, as the chip counts them.

PULSE_STATES = ("RED", "PURPLE", "AMBER", "YELLOW", "BLUE", "GREEN")    # by score, 0..5
CREDIT_PULSE = "ChartsLector's Market Action Pulse"
OSC_LIMIT = 50.0                # the oscillator ceiling of a BLUE break attempt (his 2026-09-21 version)
RAM_LEVELS = ((20, "LOW"), (40, "NORMAL"), (60, "ELEVATED"), (80, "HIGH"))
MAP_RISK = {5: 10.0, 4: 20.0, 3: 40.0, 2: 60.0, 1: 80.0, 0: 95.0}
DIV_FLOOR = {"Backwardation": 95.0, "Complacency Trap": 75.0, "Whipsaw Risk": 80.0, "Panic Easing": 40.0,
             "All Clear": 10.0}


def ema_pine(xs, n):
    """the Pulse's EMA (map_vmr_ram.ema_pine, pandas ewm(span=n, adjust=False)): the first value, then 2/(n+1)"""
    a, y, out = 2.0 / (n + 1), None, []
    for x in xs:
        y = x if y is None else (1 - a) * y + a * x
        out.append(y)
    return out


def weekly_buys(days, closes):
    """his weekly buy per session, live: the closes of the completed weeks (Monday to Friday) and this week's close to
    date, above their 10- and 20-week simple averages with the 10 over the 20; False before 19 completed weeks"""
    keys = [cal._as_date(d).isocalendar()[:2] for d in days]
    last, order = {}, []
    for k, c in zip(keys, closes):
        if k not in last:
            order.append(k)
        last[k] = c
    idx = {k: i for i, k in enumerate(order)}
    wvals = [last[k] for k in order]
    out = []
    for k, c in zip(keys, closes):
        i = idx[k]
        if i < 19:
            out.append(False)
            continue
        cl = wvals[:i] + [c]
        s10, s20 = sum(cl[-10:]) / 10, sum(cl[-20:]) / 20
        out.append(c > s10 and c > s20 and s10 > s20)
    return out


def mcclellan(net, fast=19, slow=39, msi=10, zlen=63):
    """map_vmr_ram.mcclellan over net advances (None: a session without them, which carries the sum and its average):
    {osc, summ, msi, msi_prev, summ_prev, z} per session, None where undefined"""
    af, aslow, am = 2 / (fast + 1), 2 / (slow + 1), 2 / (msi + 1)
    n = len(net)
    out = {k: [None] * n for k in ("osc", "summ", "msi", "msi_prev", "summ_prev", "z")}
    ef = es = summ = msie = None
    win = []
    for t, x in enumerate(net):
        if x is None:
            out["summ"][t], out["msi"][t] = summ, msie
            continue
        old_s, old_m = summ, msie
        ef = x if ef is None else ef + af * (x - ef)
        es = x if es is None else es + aslow * (x - es)
        osc = ef - es
        summ = osc if old_s is None else old_s + osc
        msie = summ if old_m is None else old_m + am * (summ - old_m)
        win = (win + [osc])[-zlen:]
        if len(win) == zlen:
            m = sum(win) / zlen
            sd = max(sum(w * w for w in win) / zlen - m * m, 0.0) ** 0.5
            out["z"][t] = (osc - m) / sd if sd > 0 else None
        out["osc"][t], out["summ"][t], out["msi"][t] = osc, summ, msie
        out["msi_prev"][t], out["summ_prev"][t] = old_m, old_s
    return out


def pulse_score(up, att, oscok, ar5, dbuy, wb, brk, crush):
    """his state, first true: 5 GREEN, 4 BLUE, 3 YELLOW, 2 AMBER, 1 PURPLE, else 0 RED (brk and crush: the break
    attempts, counted in a weekly buy)"""
    allyes, anyyes = ar5 and dbuy and wb, ar5 or dbuy or wb
    if up and allyes:
        return 5
    if oscok and wb and (brk or crush):
        return 4
    if up:
        return 3
    if att and anyyes:
        return 2
    if not att and anyyes:
        return 1
    return 0


def _clip(x, lo=0.0, hi=100.0):
    return min(hi, max(lo, x))


def score_vix(x):
    s = (100.0 if x < 13 else 100 - (x - 13) * 15 / 4 if x < 17 else 85 - (x - 17) * 15 / 3 if x < 20 else
         70 - (x - 20) * 10 / 5 if x < 25 else 60 - (x - 25) * 40 / 7 if x < 32 else 20 - min(20, (x - 32) * 2.5))
    return _clip(s)


def score_term(r):
    s = (80 + min(20, (0.85 - r) * 100) if r < 0.85 else 80 - (r - 0.85) * 22 / 0.10 if r < 0.95 else
         58 - (r - 0.95) * 28 / 0.05 if r < 1.0 else 30 - min(30, (r - 1) * 300))
    return _clip(s)


def score_vvix(x):
    s = (100.0 if x < 85 else 90 - (x - 85) * 20 / 15 if x < 100 else 70 - (x - 100) * 15 / 15 if x < 115 else
         55 - (x - 115) * 20 / 15 if x < 130 else 35 - min(35, (x - 130) * 2))
    return _clip(s)


def score_skew(x):
    s = (100.0 if x < 115 else 82 - (x - 115) * 16 / 15 if x < 130 else 66 - (x - 130) * 25 / 15 if x < 145 else
         41 - min(41, (x - 145) * 2))
    return _clip(s)


def vmr(vix, vix3m, vvix, skew):
    """his VIX Mood Ring, 0-100 (higher is calmer): 35% VIX, 25% VIX / VIX3M, 25% SKEW, 15% VVIX"""
    return 0.35 * score_vix(vix) + 0.25 * score_term(vix / vix3m) + 0.25 * score_skew(skew) + 0.15 * score_vvix(vvix)


def mood_band(score):
    return next((w for lo, w in ((75, "GREEN"), (65, "BLUE"), (55, "YELLOW"), (45, "AMBER"), (30, "PURPLE"))
                 if score >= lo), "RED")


def divergence(vix, v3, vv, sk, vix_1, vix_2, sk_2, tr_1):
    """his divergence (as written; used only for the risk model's volatility floor, never published: its names imply
    a direction the 10-year test did not show)"""
    tr = vix / v3 if None not in (vix, v3) and v3 > 0 else None
    if None not in (vix, sk) and ((vix < 17 and sk > 145) or (None not in (vix_2, sk_2) and vix_2 < vix and sk_2 > sk)):
        return "Complacency Trap"
    if tr is not None and tr >= 1:
        return "Backwardation"
    if tr is not None and tr_1 is not None and tr < 1 <= tr_1:
        return "Panic Easing"
    if None not in (vix, vix_1, vv) and vix < vix_1 and vv >= 101:
        return "Whipsaw Risk"
    if None not in (vix, tr, vv, sk) and vix < 17 and tr < 0.95 and vv < 100 and sk < 130:
        return "All Clear"
    return None


def ram(map_risk, breadth_risk, vol_risk, target_risk):
    """his Risk Assessment Model, 0-100: the weighted mean of the families present (map 0.35, breadth 0.30,
    volatility 0.20, target 0.15); a family that is missing is left out, never counted as no risk"""
    parts = [(0.35, map_risk), (0.30, breadth_risk), (0.20, vol_risk), (0.15, target_risk)]
    den = sum(w for w, x in parts if x is not None)
    return _clip(sum(w * x for w, x in parts if x is not None) / den) if den > 0 else None


def ram_level(x):
    if x is None:
        return "WARMING UP"
    return next((w for hi, w in RAM_LEVELS if x < hi), "EXTREME")


def _aligned(series, days, limit=3):
    """{date: value} on `days`, a missing session carrying the last value up to `limit` sessions (pandas
    reindex().ffill(limit))"""
    out, last, gap = [], None, 0
    for d in days:
        v = series.get(d)
        if v is not None:
            last, gap = v, 0
        else:
            gap += 1
            v = last if last is not None and gap <= limit else None
        out.append(v)
    return out


def pulse_series(days, bars, net, vol=None):
    """the Pulse and its risk model per session of `days` that the fund has a bar for: [{d, sc, ram, checks...}].
    net: {date: net advances}; vol: {name: {date: close}} of the VIX family (None: the risk model without it)"""
    by = {_iso(b["t"]): b for b in _closes(bars)}
    dd = [d for d in days if d in by]
    if not dd:
        return []
    c, hh = [float(by[d]["c"]) for d in dd], [float(by[d]["h"]) for d in dd]
    e3, e5, e10, e20 = (ema_pine(c, k) for k in (3, 5, 10, 20))
    wb = weekly_buys(dd, c)
    m = mcclellan([net.get(d) for d in dd])
    v = {k: _aligned(vol[k], dd) for k in ("vix", "vix3m", "vvix", "skew")} if vol else None
    out = []
    for t, d in enumerate(dd):
        x = c[t]
        ar5 = t > 0 and x > e5[t] and e5[t] > e5[t - 1]
        dbuy = x > e10[t] and x > e20[t] and e10[t] > e20[t]
        brk = t > 0 and c[t - 1] < e3[t - 1] < e5[t - 1] and x > e5[t] and e3[t] < e5[t] < e10[t]
        crush = t > 0 and c[t - 1] < x and x > e5[t] and e5[t] > e20[t] and e20[t] < e10[t]
        sm, mi, mp, sp, osc = m["summ"][t], m["msi"][t], m["msi_prev"][t], m["summ_prev"][t], m["osc"][t]
        up = None not in (sm, mi, mp) and sm > mi and mi > mp
        att = not up and None not in (sm, sp, osc) and sm > sp and osc > 0
        sc = pulse_score(up, att, osc is not None and osc < OSC_LIMIT, ar5, dbuy, wb[t], brk, crush)
        z = m["z"][t]
        vrisk = None
        if v:
            vx, v3, vv, sk = (v[k][t] for k in ("vix", "vix3m", "vvix", "skew"))
            if None not in (vx, v3, vv, sk) and v3 > 0:
                tr_1 = (v["vix"][t - 1] / v["vix3m"][t - 1] if t > 0 and None not in (v["vix"][t - 1], v["vix3m"][t - 1])
                        and v["vix3m"][t - 1] > 0 else None)
                div = divergence(vx, v3, vv, sk, v["vix"][t - 1] if t > 0 else None,
                                 v["vix"][t - 2] if t > 1 else None, v["skew"][t - 2] if t > 1 else None, tr_1)
                vrisk = max(_clip(100 - vmr(vx, v3, vv, sk)), DIV_FLOOR.get(div, 0.0))
        trisk = None
        if t >= 251:
            h252 = max(hh[t - 251:t + 1])
            if h252 > 0:
                prox = _clip(100 - max(0.0, 100 * (h252 - x) / h252) * (100 / 15))
                trd = 25.0 * (x < e5[t]) + 30.0 * (x < e10[t]) + 45.0 * (x < e20[t])
                trisk = _clip(0.55 * prox + 0.45 * trd)
        r = ram(MAP_RISK[sc], _clip(50 - 22.5 * z) if z is not None else None, vrisk, trisk)
        out.append({"d": d, "sc": sc, "ram": r, "checks": {"above_rising_5ema": bool(ar5), "daily_buy": bool(dbuy),
                                                          "weekly_buy": bool(wb[t]), "breadth_uptrend": bool(up),
                                                          "breadth_attempt": bool(att)}})
    return out


def pulse_block(funds_bars, days, net, vol=None, hist=HIST):
    out = []
    for sym in PULSE_FUNDS:
        ps = pulse_series(days, funds_bars.get(sym) or [], net, vol)
        if not ps:
            continue
        last = ps[-1]
        out.append({"sym": sym, "state": PULSE_STATES[last["sc"]], "score": last["sc"],
                    "ram": None if last["ram"] is None else round(last["ram"], 1), "ram_level": ram_level(last["ram"]),
                    "checks": last["checks"],
                    "days": [{"d": p["d"], "sc": p["sc"], "ram": None if p["ram"] is None else round(p["ram"], 1)}
                             for p in ps[-hist:]]})
    return {"credit": CREDIT_PULSE, "states": list(PULSE_STATES), "funds": out} if out else None


# ---------------------------------------------------------------------------------------------------- market.json: risk
CREDIT_RISK = "Risk appetite ratios, after ChartsLector (QQQ/QQQE stands in for his growth/value pair)"


def risk_block(funds_bars, days, hist=HIST, diag=None):
    """his six risk-appetite ratios (QQQ/QQQE standing in for his Nasdaq growth/value pair, as GrokBot's): each
    ratio above its 20-session average reads risk-on (IEF/LQD below it); chg_1m its change over 21 sessions in %"""
    def px(sym):
        return _aligned({_iso(b["t"]): float(b["c"]) for b in _closes(funds_bars.get(sym))}, days)
    pairs, n_on = [], [0] * len(days)
    for a, b in RISK_PAIRS:
        pa, pb = px(a), px(b)
        r = [x / y if x is not None and y else None for x, y in zip(pa, pb)]
        if r[-1] is None:
            if diag is not None:
                diag.setdefault("risk_left_out", []).append(f"{a}/{b}")
            continue
        off = (a, b) == ("IEF", "LQD")                      # a rising IEF/LQD is risk-off
        for t in range(len(days)):
            w = r[t - 19:t + 1] if t >= 19 else []
            above = len(w) == 20 and None not in w and r[t] > sum(w) / 20
            n_on[t] += (not above) if off else above
        w = r[-20:]
        above = None not in w and len(w) == 20 and r[-1] > sum(w) / 20
        pairs.append({"pair": f"{a}/{b}", "above": above, "on": (not above) if off else above,
                      "chg_1m": round(100 * (r[-1] / r[-22] - 1), 2) if len(r) > 21 and r[-22] else None,
                      "rising": "off" if off else "on"})
    if not pairs:
        return None
    return {"credit": CREDIT_RISK, "on": sum(1 for p in pairs if p["on"]), "of": len(pairs), "pairs": pairs,
            "days": [{"d": d, "n": k} for d, k in zip(days, n_on)][-hist:]}


# ---------------------------------------------------------------------------------------------------- market.json: rotation
# ChartsLector's Relative Robustness Rotation ("Relative Robustness Rotation.txt", RRR Blended) against SPY on weekly
# closes (his calcTimeframe input set to W; useCompletedBarsOnly false, so the week in progress reads its close to
# date), with Pine's semantics as the owner's exporter reproduces them: ta.ema seeded on its first simple average,
# ta.stdev the population deviation. RS-Ratio = 0.6 R(15, 21) + 0.4 R(26, 34); RS-Momentum the same blend of M(8, 15)
# and M(15, 26) on the ratio, plus 0.10 tanh of the ratio's 1-week change against its 5-week pace, over the 20-week
# deviation of its changes. Quadrants: Leading (both >= 100), Weakening, Lagging, Improving. The tail: the last 5 weeks.
CREDIT_ROTATION = "ChartsLector's Relative Robustness Rotation"
TAIL = 5


def p_ema(xs, n):
    a, prev, out = 2.0 / (n + 1), None, []
    for i, x in enumerate(xs):
        if prev is None:
            w = xs[i - n + 1:i + 1] if i >= n - 1 else []
            if w and None not in w:
                prev = sum(w) / n
        elif x is not None:
            prev = a * x + (1 - a) * prev
        else:
            prev = None
        out.append(prev)
    return out


def rrr(c, ref):
    """(RS-Ratio, RS-Momentum) per bar of the closes c against ref (None where undefined)"""
    rs = [100.0 * x / y if x is not None and y else None for x, y in zip(c, ref)]

    def comp(xs, s_, n_):
        sm = p_ema(xs, s_)
        b = p_ema(sm, n_)
        return [100.0 * u / v if u is not None and v else None for u, v in zip(sm, b)]

    def blend(xs, f, g):
        return [0.6 * a + 0.4 * b if a is not None and b is not None else None for a, b in zip(comp(xs, *f), comp(xs, *g))]
    r = blend(rs, (15, 21), (26, 34))
    m = blend(r, (8, 15), (15, 26))
    n = len(r)
    ch1 = [None] + [r[t] - r[t - 1] if r[t] is not None and r[t - 1] is not None else None for t in range(1, n)]
    out = []
    for t in range(n):
        adj = 0.0
        w = ch1[t - 19:t + 1] if t >= 19 else []
        if w and None not in w and t >= 5 and r[t - 5] is not None:
            mu = sum(w) / 20
            sd = (sum((x - mu) ** 2 for x in w) / 20) ** 0.5
            if sd > 1e-12:
                z = (ch1[t] - (r[t] - r[t - 5]) / 5) / (sd + 1e-12)
                adj = 0.10 * (2.0 / (1.0 + math.exp(-2.0 * max(-20.0, min(20.0, z)))) - 1.0)
        out.append(None if m[t] is None else m[t] + adj)
    return r, out


def quadrant(ratio, mom):
    return ("Leading" if mom >= 100 else "Weakening") if ratio >= 100 else ("Improving" if mom >= 100 else "Lagging")


def rotation_block(funds_bars, spy, funds=HEAT_FUNDS, diag=None):
    spy = _closes(spy)
    cal_ = [_iso(b["t"]) for b in spy]
    keys = [cal._as_date(d).isocalendar()[:2] for d in cal_]
    ends = [i for i in range(len(cal_)) if i == len(cal_) - 1 or keys[i + 1] != keys[i]]   # each week's last session
    ref = [float(spy[i]["c"]) for i in ends]
    rows, left = [], {}
    for sym, name, group, _ in funds:
        bars = {_iso(b["t"]): float(b["c"]) for b in _closes(funds_bars.get(sym))}
        if not bars:
            left[sym] = "no bars yet"
            continue
        daily, last = [], None
        for d in cal_:
            last = bars.get(d, last)
            daily.append(last)
        c = [daily[i] for i in ends]
        r, m = rrr(c, ref)
        if len(r) < TAIL or None in r[-TAIL:] or None in m[-TAIL:]:
            left[sym] = f"{sum(1 for x in c if x is not None)} weeks of history; his averages need about 100"
            continue
        rows.append({"sym": sym, "name": name, "group": group, "ratio": round(r[-1], 2), "mom": round(m[-1], 2),
                     "quad": quadrant(r[-1], m[-1]),
                     "tail": [{"d": cal_[ends[k]], "ratio": round(r[k], 2), "mom": round(m[k], 2)}
                              for k in range(len(ends) - TAIL, len(ends))]})
    if diag is not None:
        diag["rotation_left_out"] = left
    if not rows:
        return None
    out = {"freq": "weekly", "credit": CREDIT_ROTATION, "funds": rows}
    if left:                                       # on the page: a fund missing from the map says why
        out["left_out"] = [{"sym": s_, "why": w} for s_, w in left.items()]
    return out


# ---------------------------------------------------------------------------------------------------- market.json: mood
# His VIX Mood Ring on Cboe's official daily closes (cache/cboe_daily: VIX, VIX3M, VVIX and SKEW, kept current by the
# lz_cl_vmr_qqq lane's feed, desk/sleeves/families/lazarus.refresh_cboe; GrokBot's tab reads the same files), shown only
# while its last date is within 5 days of the market's session; and the edition's volatility chip over the year
# (market.volatility on market.vix_doc, the chip's own input: Cboe's VIX file, or the IDX_VIX record when that file is
# more than 5 days behind; so the last day is the chip's).
CREDIT_MOOD = "ChartsLector's VIX Mood Ring"
CBOE_FILES = (("vix", "VIX_History.csv", "CLOSE"), ("vix3m", "VIX3M_History.csv", "CLOSE"),
              ("vvix", "VVIX_History.csv", "VVIX"), ("skew", "SKEW_History.csv", "SKEW"))
STALE_DAYS = 5                  # market.volatility's rule: an input more than 5 days behind the session is not shown
VOL_BANDS = [{"lo": 0.0, "hi": 0.2, "word": "Calm"}, {"lo": 0.2, "hi": 0.6, "word": "Normal"},
             {"lo": 0.6, "hi": 0.9, "word": "Elevated"}, {"lo": 0.9, "hi": 1.0, "word": "High"}]   # market.volatility's


def cboe_series(root):
    """{name: {date: close}} from the cached Cboe CSVs, or None when one is missing or unreadable"""
    out = {}
    for name, fn, col in CBOE_FILES:
        try:
            with open(os.path.join(root, "cache", "cboe_daily", fn)) as f:
                lines = f.read().splitlines()
            j = [h.strip().upper() for h in lines[0].split(",")].index(col)
        except (OSError, IndexError, ValueError):
            return None
        d = {}
        for line in lines[1:]:
            parts = line.split(",")
            try:
                m, dd, y = parts[0].strip().split("/")
                d[f"{int(y):04d}-{int(m):02d}-{int(dd):02d}"] = float(parts[j])
            except (ValueError, IndexError):
                continue
        out[name] = d
    return out


def _days_apart(a, b):
    return (cal._as_date(a) - cal._as_date(b)).days


def vol_block(root, as_of, days, n=MOOD_DAYS):
    doc = market.vix_doc(root, cal._as_date(as_of)) or {}
    dates, closes = (doc.get("dates") or [])[-600:], (doc.get("close") or [])[-600:]   # the year before each day
    doc = {"dates": dates, "close": closes}
    now = market.volatility(doc, cal._as_date(as_of))
    if not now:
        return None
    hist = []
    for d in days[-n:]:
        v = market.volatility(doc, cal._as_date(d))
        if v:
            hist.append({"d": d, "pct": round(v["pct"], 3)})
    return {"def": "the VIX's percentile within its trailing 252 sessions",
            "as_of": max(x for x, c in zip(dates, closes) if c is not None and x <= as_of), "word": now["word"],
            "pct": round(now["pct"], 3), "bands": [dict(b) for b in VOL_BANDS], "days": hist}


def mood_block(root, as_of, days, ser=None, diag=None):
    """the Mood Ring block, or None (no Cboe cache, or its last date more than STALE_DAYS behind as_of)"""
    diag = {} if diag is None else diag
    ser = cboe_series(root) if ser is None else ser
    if not ser:
        diag["mood"] = "no Cboe cache"
        return None
    dates = sorted(d for d in set().union(*ser.values()) if d <= as_of)
    cols = {k: _aligned(v, dates) for k, v in ser.items()}
    rows = [(d,) + tuple(cols[k][i] for k in ("vix", "vix3m", "vvix", "skew")) for i, d in enumerate(dates)]
    rows = [r for r in rows if None not in r and r[2] > 0]
    if not rows or _days_apart(as_of, rows[-1][0]) > STALE_DAYS:
        diag["mood"] = f"Cboe last {rows[-1][0] if rows else None}, the session {as_of}"
        return None
    d, vx, v3, vv, sk = rows[-1]
    score, term = vmr(vx, v3, vv, sk), vx / v3
    size = ("bigger" if term >= 1 or score < MOOD_CUTS["bigger_below"] else
            "smaller" if score >= MOOD_CUTS["smaller_from"] else "usual")
    out = {"credit": CREDIT_MOOD, "source": "Cboe", "as_of": d, "basis": MOOD_BASIS, "score": round(score, 1),
           "band": mood_band(score), "word": MOOD_WORDS[size], "backwardation": term >= 1, "cuts": dict(MOOD_CUTS),
           "inputs": {"vix": round(vx, 2), "vix3m": round(v3, 2), "term": round(term, 3), "vvix": round(vv, 2),
                      "skew": round(sk, 2)},
           "parts": {"vix": round(score_vix(vx), 1), "term": round(score_term(term), 1), "skew": round(score_skew(sk), 1),
                     "vvix": round(score_vvix(vv), 1)},
           "weights": {"vix": 35, "term": 25, "skew": 25, "vvix": 15},
           "bands": [{"lo": lo, "band": b} for lo, b in ((75, "GREEN"), (65, "BLUE"), (55, "YELLOW"), (45, "AMBER"),
                                                         (30, "PURPLE"), (0, "RED"))],
           "days": [{"d": r[0], "v": round(vmr(*r[1:]), 1)} for r in rows[-MOOD_DAYS:]]}
    vb = vol_block(root, as_of, days)
    if vb:
        out["vol"] = vb
    return out


# ---------------------------------------------------------------------------------------------------- market.json: assembly

def roster_rows(root, hub, as_of, spy, diag, market_read=None, now=None, live=False):
    """the roster's rows for the session as_of, or None while it is not whole (fewer than market.REPRESENTATIVE of the
    roster report it: the chip's rule). Read once per session and kept (cache/terminal/dash_roster.json, internal);
    the chip's own participation for its session (market.read's diag "part") replaces this pass's when it has it"""
    from ..util import read_json, write_json_atomic
    path = os.path.join(root, "cache", "terminal", "dash_roster.json")
    st = None if live else read_json(path, None)     # a live session is read again every edition
    if st and st.get("as_of") == as_of and st.get("whole"):
        diag["roster"] = "kept"
        return st["rows"]
    names = _roster()

    def stream():                                   # 200 names at a time: one batch of bars in memory, not 1,838
        for i in range(0, len(names), 200):
            got = hub.bars("equity_split", "1d", names[i:i + 200], ROSTER_DEPTH, cache_only=True) or {}
            yield from (market.with_today(hub, now, got)[0] if live else got).values()
    days = [_iso(b["t"]) for b in _closes(spy)][-(ROSTER_DEPTH - MIN_BARS + 1):]
    rows = roster_pass(stream(), days)
    last = rows[-1] if rows else None
    whole = bool(last) and last["d"] == as_of and last["a50"] is not None and \
        last["n"] >= market.REPRESENTATIVE * len(names)
    diag["roster"] = f"{last['n'] if last else 0} of {len(names)} report {as_of}"
    if not whole:
        return None
    mr = market_read or {}
    part = mr.get("part") if mr.get("as_of") == as_of else None
    if part:
        last.update(n=part["n"], a20=part["above20"], a50=part["above50"], a200=part["above200"], adv=part["adv"],
                    dec=part["dec"])
        diag["roster"] += ", the chip's own count"
    if not live:
        write_json_atomic(path, {"as_of": as_of, "whole": True, "rows": rows})
    return rows


def market_doc(root, hub, now, diag=None, mood=None, market_read=None):
    """market.json for the latest session SPY's cached bars hold, or None (no SPY bars, or the roster not yet whole
    for that session: the page keeps the previous session's). diag (a dict) receives what the page never shows: the
    funds left out and why, how much of the roster reported"""
    diag = {} if diag is None else diag
    mood = MOOD if mood is None else mood
    if hub is None:
        return None
    spy = (hub.bars("equity_split", "1d", ["SPY"], BARS, cache_only=True) or {}).get("SPY") or []
    if not spy:
        return None
    got, live = market.with_today(hub, now, {"SPY": spy})      # mid-session: today's forming bars
    spy = got["SPY"]
    as_of = _iso(spy[-1]["t"])
    rows = roster_rows(root, hub, as_of, spy, diag, market_read, now=now, live=bool(live))
    if rows is None:
        return None
    funds = hub.bars("equity_split", "1d", list(FUNDS), BARS, cache_only=True) or {}
    if live:
        funds, _ = market.with_today(hub, now, funds)
    calendar = [_iso(b["t"]) for b in _closes(spy)]
    heat_rows, left = heat(funds, as_of)
    diag["heat_left_out"] = left
    net = {r["d"]: 1000.0 * (r["adv"] - r["dec"]) / (r["adv"] + r["dec"]) for r in rows if r["adv"] + r["dec"]}
    doc = {"v": 1, "as_of": as_of, "generated_at": int(now), "n_roster": len(_roster()), "heat": heat_rows,
           "participation": participation_block(rows), "movers": movers_block(rows), "breadth": breadth_block(rows)}
    ser = cboe_series(root) if mood else None
    mb = mood_block(root, as_of, calendar, ser, diag) if mood else None
    pulse = pulse_block(funds, calendar, net, ser if mb else None)
    risk = risk_block(funds, calendar[-200:], diag=diag)
    rot = rotation_block(funds, spy, diag=diag)
    for k, v in (("pulse", pulse), ("risk", risk), ("rotation", rot), ("mood", mb)):
        if v:
            doc[k] = v
    return validate(doc, MARKET_ALLOWED)


# ---------------------------------------------------------------------------------------------------- writing

def _dump(doc):
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _write(path, text):
    """atomically: a reader (the publisher) sees the old file or the new one, never half"""
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write(root, hub, edition, now, market_read=None, mood=None):
    """build and write this edition's dashboards to cache/terminal/dash/ -> {name: {syms|..., gz, s}} (the job's
    record: sizes and seconds; never published). A dashboard that fails is left out of this edition and reported"""
    from .publish import dash_dir
    out = {}
    t0 = time.time()
    try:
        doc = charts(hub, edition, now)
        text = _dump(doc)
        _write(os.path.join(dash_dir(root), "charts.json"), text)
        out["charts"] = {"syms": len(doc["syms"]), "gz": len(gzip.compress(text.encode())),
                         "s": round(time.time() - t0, 3)}
    except Exception as e:                          # noqa: BLE001  (a dashboard never stops the edition)
        out["charts"] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
    t0, diag = time.time(), {}
    try:
        doc = market_doc(root, hub, now, diag=diag, mood=mood, market_read=market_read)
        if doc is not None:
            text = _dump(doc)
            _write(os.path.join(dash_dir(root), "market.json"), text)
            out["market"] = {"as_of": doc["as_of"], "heat": len(doc["heat"]), "left_out": diag.get("heat_left_out"),
                             "blocks": sorted(k for k in doc if isinstance(doc[k], (dict, list))),
                             "gz": len(gzip.compress(text.encode())), "s": round(time.time() - t0, 3)}
        else:                                       # the page keeps the previous session's
            out["market"] = {"kept": "the previous session's", "s": round(time.time() - t0, 3)}
        for k in ("roster", "mood", "rotation_left_out", "risk_left_out"):
            if k in diag:
                out["market"][k] = diag[k]
    except Exception as e:                          # noqa: BLE001
        out["market"] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
    return out
