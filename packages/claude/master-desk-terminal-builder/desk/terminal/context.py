"""Card context (edition `setups[].context`): what sits around a card's plan, every part with its own status.

  why       the read's evidence kinds (read/call.family_votes, the record's "kinds") against the roster's median for the
            same kind today: value, base, signed difference, and the value's percentile among the roster. These are
            evidence weights, never probabilities (WHY_BASIS rides on the block).
  ladder    the plan's prices top to bottom (target 2, target 1, buy zone, stop) with today's price inserted at its
            rank, each with its distance in % from today's price.
  chop      a 0-1 trend-quality score (AlgoPoint's published weights): ADX 30%, short/long ATR ratio 30%, price
            efficiency 25%, direction consistency 15%; Trending >= 0.6, Mixed >= 0.35, else Choppy.
  reclaim   the named reclaim trigger: a close back above the prior 20-session swing low after trading under it in the
            last 5 sessions ("sweep"), or a close back over a fresh demand bar's top after tapping it ("demand");
            the stop is a close back through the swept low / zone bottom. "none" when neither happened.
  levels    up to four supports under price (3-bar swing lows of the last 120 sessions within 3 ATR), each aged:
            fresh (never retested), tested (held 1-2 retests), delivered (a retest bounced 1 ATR or more within 10
            sessions), decaying (3+ retests, or a close under it since).
  heikin    Heikin-Ashi colour, run of candles and flat bottom (vendor_ext.heikin_read, C222)
  stoch     Stochastic RSI %K and %D with its zone (C125)
  pivots    the next session's classic, Fibonacci, Woodie and Camarilla levels, in % from the close (C126)
  range     the last session's range as a share of the prior ATR(14), and the EMA-cloud trend (Saty ATR Levels, C2)
  falsifier the one price that voids the plan and how long the read stands (FolioTend / Tensor, V-tensor-3)
  catalyst  next earnings (sessions away; blackout when it falls inside the plan's horizon), the latest SEC filing,
            a share-offering filing (S-1, S-3, F-3, 424B*) in the last 30 days, which voids a pullback, and an event
            study: the median 5- and 21-session move after the name's past reports, net of SPY, with n (4 or more).
Every block carries status "ok" or "no_data" with a reason; nothing is guessed or zero-filled. Closed daily bars only."""
import datetime as dt
import os
import statistics
import time

from .. import calendar as cal
from ..util import ET
from .read import ta
from . import vendor_ext as vx
from .ranking import LABEL

WHY_BASIS = "Evidence weights against today's roster median, not probabilities"
AGES = ("fresh", "tested", "delivered", "decaying")
OFFERING = ("S-1", "S-1/A", "S-3", "S-3/A", "S-3ASR", "F-3", "F-3ASR", "424B1", "424B2", "424B3", "424B4", "424B5",
            "424B7")
OFFER_DAYS = 30
EVENT_MIN_N = 4
# the public contract of the block (desk/terminal/__init__.py merges it under setups[].context)
ALLOWED = {
    "": {"as_of", "why", "ladder", "chop", "reclaim", "levels", "catalyst", "heikin", "stoch", "pivots", "range",
         "falsifier"},
    "why": {"status", "reason", "basis", "rows"},
    "why.rows[]": {"key", "label", "value", "base", "diff", "pct"},
    "ladder": {"status", "reason", "rows"},
    "ladder.rows[]": {"role", "label", "at"},
    "chop": {"status", "reason", "score", "word", "parts"},
    "chop.parts": {"adx", "atr", "eff", "cons"},
    "reclaim": {"status", "reason", "kind", "at", "stop_at", "date", "text"},
    "levels": {"status", "reason", "rows"},
    "levels.rows[]": {"at", "age", "tests", "since"},
    "catalyst": {"status", "reason", "earnings", "filing", "offering", "event", "text"},
    "catalyst.earnings": {"date", "sessions", "blackout"},
    "catalyst.filing": {"status", "reason", "form", "date"},
    "catalyst.offering": {"form", "date", "voids"},
    "catalyst.event": {"status", "reason", "n", "med5", "med21"},
    "heikin": {"status", "reason", "color", "run", "flat_bottom"},
    "stoch": {"status", "reason", "k", "d", "zone", "cross", "rsi"},
    "pivots": {"status", "reason", "from", "for", "classic", "fibonacci", "woodie", "camarilla"},
    "pivots.classic": {"P", "R1", "R2", "R3", "S1", "S2", "S3"},
    "pivots.fibonacci": {"P", "R1", "R2", "R3", "S1", "S2", "S3"},
    "pivots.woodie": {"P", "R1", "R2", "S1", "S2"},
    "pivots.camarilla": {"R1", "R2", "R3", "R4", "S1", "S2", "S3", "S4"},
    "range": {"status", "reason", "pct", "band", "trend", "as_of"},
    "falsifier": {"status", "reason", "form", "text", "at", "trigger_at", "valid_through"},
}


def _nd(reason):
    return {"status": "no_data", "reason": reason}


def _day(b):
    return dt.datetime.fromtimestamp(float(b["t"]), ET).date()


# ---- why ------------------------------------------------------------------------------------------------------------
def baseline(kinds_list):
    """{kind: sorted roster values} from every record's kinds today (missing kinds count as 0: a read that filed no
    vote in a kind voted nothing there)"""
    keys = set()
    for k in kinds_list:
        keys |= set(k or {})
    return {key: sorted(float((k or {}).get(key) or 0.0) for k in kinds_list) for key in keys}


def why(kinds, base):
    if not kinds:
        return _nd("The read has no evidence kinds yet")
    rows = []
    for key, v in kinds.items():
        xs = base.get(key) or []
        if not xs:
            continue
        v = float(v or 0.0)
        med = statistics.median(xs)
        pct = round(100.0 * sum(1 for x in xs if x < v) / len(xs))   # strictly under: ties (many 0s) do not lift it
        rows.append({"key": key, "label": LABEL.get(key, key.capitalize()), "value": round(v, 2),
                     "base": round(med, 2), "diff": round(v - med, 2), "pct": pct})
    if not rows:
        return _nd("No roster baseline for these kinds")
    rows.sort(key=lambda r: (-abs(r["diff"]), r["key"]))
    return {"status": "ok", "basis": WHY_BASIS, "rows": rows[:6]}


# ---- ladder ---------------------------------------------------------------------------------------------------------
_ROLES = (("t2", "Target 2"), ("t1", "Target 1"), ("zone_hi", "Buy zone top"), ("zone_lo", "Buy zone bottom"),
          ("out", "Stop"))


def ladder(plan, close, now_pct=None):
    """rows top to bottom in % from the read's close ("at"); the page prices them with its own rounding (prices.py):
    the edition never carries a dollar price"""
    if not isinstance(close, (int, float)) or close <= 0 or not plan:
        return _nd("No close to price the plan from")
    rows = []
    for key, label in _ROLES:
        v = plan.get(key)
        if key == "t2" and not plan.get("trim"):
            continue
        if isinstance(v, (int, float)):
            rows.append({"role": "stop" if key == "out" else key, "label": label, "at": round(float(v), 2)})
    if not rows:
        return _nd("The plan has no prices")
    rows.append({"role": "now", "label": "Now", "at": round(float(now_pct or 0.0), 2) + 0.0})
    rows.sort(key=lambda r: (-r["at"], r["role"] != "now"))
    return {"status": "ok", "rows": rows}


# ---- not-chop -------------------------------------------------------------------------------------------------------
def _clip(x):
    return max(0.0, min(1.0, x))


def regime(bars, n=20):
    if not bars or len(bars) < 60:
        return _nd(f"Needs 60 daily bars, has {len(bars or [])}")
    adx = ta.adx(bars)[0][-1]
    a5, a20 = ta.atr(bars, 5)[-1], ta.atr(bars, 20)[-1]
    cs = ta.closes(bars)[-(n + 1):]
    moves = [b - a for a, b in zip(cs, cs[1:])]
    path = sum(abs(m) for m in moves)
    net = cs[-1] - cs[0]
    if adx is None or not a20 or not path:
        return _nd("Flat or missing prices")
    parts = {"adx": round(_clip(adx / 40.0), 3),
             "atr": round(_clip((a5 / a20 - 0.6) / 0.8), 3),
             "eff": round(_clip(abs(net) / path), 3),
             "cons": round(_clip((sum(1 for m in moves if m * net > 0) / len(moves) - 0.5) * 2.0), 3)}
    score = round(0.30 * parts["adx"] + 0.30 * parts["atr"] + 0.25 * parts["eff"] + 0.15 * parts["cons"], 2)
    word = "Trending" if score >= 0.6 else "Mixed" if score >= 0.35 else "Choppy"
    return {"status": "ok", "score": score, "word": word, "parts": parts}


# ---- reclaim --------------------------------------------------------------------------------------------------------
def _at(price, close):
    return round(100.0 * (price / close - 1.0), 2) + 0.0


def reclaim(bars, look=5, base=20, close=None):
    """levels in % from the read's close (the last bar's when none is given): the edition carries no dollar price"""
    if bars and not close:
        close = float(bars[-1]["c"])
    if not bars or len(bars) < base + look + 2:
        return _nd("Too few bars for a swing low")
    prior = bars[-(base + look):-look]
    low = min(float(b["l"]) for b in prior)
    recent = bars[-look:]
    swept = [i for i, b in enumerate(recent) if float(b["l"]) < low]
    if swept:
        i0 = swept[0]
        after = [b for b in recent[i0:] if float(b["c"]) > low]
        if after and float(recent[-1]["c"]) > low:
            stop = min(float(b["l"]) for b in recent[i0:])
            d = _day(after[0]).isoformat()
            return {"status": "ok", "kind": "sweep", "at": _at(low, close), "stop_at": _at(stop, close), "date": d,
                    "text": f"Swept the {_day(min(prior, key=lambda b: float(b['l']))).strftime('%b %-d')} low and "
                            f"closed back above it on {_day(after[0]).strftime('%b %-d')}"}
    atr = ta.atr(bars, 14)
    hist = bars[-60:-look]
    for j in range(len(hist) - 2, 0, -1):            # newest strong up bar first: its base bar is the demand zone
        k = len(bars) - 60 + j
        a = atr[k] if k < len(atr) else None
        b, z = hist[j], hist[j - 1]
        if a and float(b["c"]) - float(b["o"]) > 1.5 * a:
            top, bot = max(float(z["o"]), float(z["c"])), float(z["l"])
            between = hist[j + 1:]
            if any(float(x["l"]) <= top for x in between):
                break                                  # tapped before: not fresh
            taps = [x for x in recent if float(x["l"]) <= top]
            if taps and float(recent[-1]["c"]) > top and all(float(x["c"]) >= bot for x in recent):
                return {"status": "ok", "kind": "demand", "at": _at(top, close), "stop_at": _at(bot, close),
                        "date": _day(taps[0]).isoformat(),
                        "text": f"Tapped fresh demand from {_day(z).strftime('%b %-d')} and closed back above it"}
            break
    return {"status": "ok", "kind": "none"}


# ---- level age ------------------------------------------------------------------------------------------------------
def age_of(tests, bounced, broken):
    if broken or tests >= 3:
        return "decaying"
    if tests == 0:
        return "fresh"
    return "delivered" if bounced else "tested"


def levels(bars, span=120, near_atr=3.0, close=None):
    if not bars or len(bars) < 40:
        return _nd("Too few bars for supports")
    atr = ta.atr(bars, 14)[-1]
    if not atr:
        return _nd("No range to measure supports by")
    last = float(bars[-1]["c"])
    off = max(0, len(bars) - span)
    w = bars[off:]
    rows = []
    for i in range(3, len(w) - 3):
        l = float(w[i]["l"])
        if not all(l < float(w[i + d]["l"]) for d in (-3, -2, -1, 1, 2, 3)):
            continue
        if not (last - near_atr * atr <= l < last):
            continue
        tests, bounced, broken, k = 0, False, False, i + 4
        while k < len(w):
            b = w[k]
            if float(b["c"]) < l:
                broken = True
                break
            if float(b["l"]) <= l + 0.25 * atr:
                tests += 1
                hi = max(float(x["h"]) for x in w[k:k + 10])
                bounced = bounced or hi - l >= atr
                k += 3
                continue
            k += 1
        rows.append({"at": _at(l, close or last),
                     "age": age_of(tests, bounced, broken), "tests": tests, "since": _day(w[i]).isoformat()})
    if not rows:
        return _nd("No swing-low support within 3 ATR under price")
    rows.sort(key=lambda r: -r["at"])
    return {"status": "ok", "rows": rows[:4]}


# ---- catalyst -------------------------------------------------------------------------------------------------------
def earnings_line(row, today, until):
    d = (row or {}).get("date")
    if not d or d < today.isoformat():
        return None
    return {"date": d, "sessions": cal.trading_days_between(today, d), "blackout": bool(until and d <= until)}


def filings_block(filings, today):
    if filings is None:
        return {"latest": None, "offering": None}
    fl = sorted((f for f in filings if f.get("date")), key=lambda f: f["date"], reverse=True)
    latest = {"form": fl[0]["form"], "date": fl[0]["date"]} if fl else None
    cut = (today - dt.timedelta(days=OFFER_DAYS)).isoformat()
    off = next((f for f in fl if f.get("form") in OFFERING and f["date"] >= cut), None)
    return {"latest": latest, "offering": {"form": off["form"], "date": off["date"], "voids": True} if off else None}


def event_study(bars, spy, reports, min_n=EVENT_MIN_N):
    if not bars or not spy or not reports:
        return _nd("No past reports on file")
    sday = {_day(b): float(b["c"]) for b in spy}
    days = [_day(b) for b in bars]
    cs = [float(b["c"]) for b in bars]
    e5, e21 = [], []
    for r in reports:
        try:
            d = dt.date.fromisoformat(r[0])
        except (TypeError, ValueError):
            continue
        i = next((j for j, x in enumerate(days) if x >= d), None)
        if i is None or i < 1 or i + 21 >= len(cs):
            continue
        a, s0 = days[i - 1], sday.get(days[i - 1])
        s5, s21 = sday.get(days[i + 4]), sday.get(days[i + 20])
        if not (s0 and s5 and s21):
            continue
        e5.append(100.0 * ((cs[i + 4] / cs[i - 1]) - (s5 / s0)))
        e21.append(100.0 * ((cs[i + 20] / cs[i - 1]) - (s21 / s0)))
    if len(e5) < min_n:
        return _nd(f"{len(e5)} past reports with 21 sessions after them; needs {min_n}")
    return {"status": "ok", "n": len(e5), "med5": round(statistics.median(e5), 2),
            "med21": round(statistics.median(e21), 2)}


def catalyst(bars, spy, earnings_row, filings, today, until, filing_reason=None):
    e = earnings_line(earnings_row, today, until)
    fb = filings_block(filings, today)
    out = {"status": "ok", "event": event_study(bars, spy, (earnings_row or {}).get("reports"))}
    if e:
        out["earnings"] = e
    if filings is None:
        out["filing"] = _nd(filing_reason or "Filings not fetched")
    elif fb["latest"]:
        out["filing"] = dict(fb["latest"], status="ok")
    else:
        out["filing"] = _nd("No recent filings")
    if fb["offering"]:
        out["offering"] = fb["offering"]
    words = []
    if fb["offering"]:
        words.append(f"Share offering filed {fb['offering']['date']} ({fb['offering']['form']}): the pullback is void")
    if e:
        words.append(("Earnings inside the plan: " if e["blackout"] else "Earnings in ") +
                     f"{e['sessions']} session{'s' if e['sessions'] != 1 else ''} ({e['date']})")
    ev = out["event"]
    if ev["status"] == "ok":
        words.append(f"After its last {ev['n']} reports: median {ev['med5']:+.1f}% in 5 sessions, "
                     f"{ev['med21']:+.1f}% in 21, net of SPY")
    if words:
        out["text"] = "; ".join(words)
    return out


# ---- EDGAR (only with the owner's SEC contact set: AGENTS.md) ----------------------------------------------------
class FilingsBudget:
    """one edition build's allowance for fresh SEC lookups: at most `max_fresh` of them and `deadline_s` seconds in all;
    cached names cost nothing. Past either, a card reads 'Filings not fetched' and the build moves on."""

    def __init__(self, max_fresh=20, deadline_s=90.0, clock=time.monotonic):
        self.max_fresh, self.deadline_s, self.clock = max_fresh, float(deadline_s), clock
        self.t0, self.fresh = clock(), 0

    def remaining(self):
        return self.deadline_s - (self.clock() - self.t0)

    def expired(self):
        return self.remaining() <= 0 or self.fresh >= self.max_fresh

    def spend(self):
        self.fresh += 1
        return max(1, min(10, int(self.remaining())))        # the per-request timeout, never past the deadline


def fetch_filings(root, sym, today, fetch=None, budget=None):
    """-> (filings or None, reason). Cached a day per name under state/terminal/filings.json. The SEC contact is
    $SEC_USER_AGENT or the desk default naming the owner's contact, Jack Tailor (owner, 2026-10-27)."""
    from ..util import read_json, write_json_atomic
    from ..feedlib import edgar_buyback as eb
    path = os.path.join(root, "state", "terminal", "filings.json")
    cache = read_json(path, {}) or {}
    hit = cache.get(sym)
    if hit and hit.get("day") == today.isoformat():
        return hit.get("rows"), hit.get("reason")
    timeout = 30
    if budget is not None:
        if budget.expired():                         # not cached: the next build asks again
            return None, "Filings not fetched"
        timeout = budget.spend()
    sc = eb.Scanner(os.path.join(root, "cache", "edgar_buyback"), fetch=fetch)
    rows, reason = None, None
    try:
        cik = sc.ticker_to_cik(sym)
        if not cik:
            reason = "No SEC registrant for this ticker"
        else:
            import json
            doc = sc.fetch_url(f"https://data.sec.gov/submissions/CIK{cik}.json", timeout=timeout)
            rec = (json.loads(doc).get("filings") or {}).get("recent") or {} if doc else None
            if rec is None:
                reason = "SEC request failed"
            else:
                rows = [{"form": f, "date": d} for f, d in zip(rec.get("form") or [], rec.get("filingDate") or [])][:40]
    except Exception:                               # noqa: BLE001  (a filing lookup never stops the edition)
        rows, reason = None, "SEC request failed"
    cache[sym] = {"day": today.isoformat(), "rows": rows, "reason": reason}
    try:
        write_json_atomic(path, cache)
    except OSError:
        pass
    return rows, reason


# ---- the block -----------------------------------------------------------------------------------------------------
def block(bars, spy, plan, close, now_pct, kinds, base, earnings_row, filings, today, until, filing_reason=None,
          form=None):
    as_of = _day(bars[-1]).isoformat() if bars else today.isoformat()
    return {"as_of": as_of, "why": why(kinds, base), "ladder": ladder(plan, close, now_pct), "chop": regime(bars),
            "reclaim": reclaim(bars, close=close), "levels": levels(bars, close=close),
            "catalyst": catalyst(bars, spy, earnings_row, filings, today, until, filing_reason),
            "heikin": vx.heikin_read(bars), "stoch": vx.stoch_rsi(bars), "pivots": vx.pivots(bars),
            "range": vx.atr_range(bars), "falsifier": vx.falsifier(plan, form, as_of)}
