"""The Fear-Day Buy List's decision card: what sits around each picker card's plan (picker card `context`).

SCOPE (InfinityBlade, 2026-10-27):
  Surface   this module; the edition's `picker.<lane>[].context` (desk/terminal/__init__.py merges ALLOWED here); the
            page's drawing of it (web/terminal/brief.js, context.js).
  Constraints  the block is context.py's (why, ladder, chop, reclaim, levels, catalyst) built from the same closed daily
            bars the picker used, cut at its as_of (truncating later bars never changes an answer); levels in % from
            the close, never a dollar price (the page prices them through its own px); targets are real levels only:
            confirmed swing highs and the 1-year high (picker/replay.resistances) and the trend-based Fibonacci
            projections and measured move of the last advance (read/plan.projections); no reward-to-risk multiple, no
            fallback; a failed card keeps its plan without a context. Sleeves are untouched.
  Outcome   buy zone, stop, T1/T2 on a ladder, a why panel (each factor against today's median, signed in its favourable
            direction, with its percentile among today's names), the not-chop number, the reclaim trigger, level age
            and the catalyst line (earnings countdown, latest SEC filing, offering flag).
  Proof     tests/test_picker_cards.py (fixture bars with known answers, the ordering gate, point in time, strings).
  Edges     analog odds: the picker replay (docs/research/picker-replay-*.md) grades its own plans (stop under a swing
            low, T1 the nearest resistance); the card's plan (a disaster stop, a 60-session hold) is not one of them,
            and the picker has no forward record yet, so the line reads "not yet graded, 0 logged" until it does.

The buy zone is the last close's cap (read/plan.CAP_ATR over it) down by the plan's widest zone (ZONE_MAX_ATR), the
stop is the card's own disaster stop. The ordering gate: stop < zone bottom < zone top < T1 < T2, one direction; a
target the buy zone already reached is dropped, and a plan whose stop sits inside the zone gets no ladder."""
import copy

from . import context as contextmod
from .read import plan as readplan
from .read import ta
from ..picker import fearday as F
from ..picker import replay as R

# a target nearer than this to the close is not a target: the replay's constant (R.MIN_T1_ATR), read when used, because
# desk.picker.replay imports the terminal package and this module imports it back: a module-level read breaks `import
# desk.picker.replay` as the first import
GAP_ATR = 0.5                         # T2 stands at least this far over T1
ODDS_WHY = ("The picker has no forward record yet: its cards are logged from today and graded at 1, 5 and 21 "
            "sessions. The replay grades other plans (a stop under a swing low), so its rates do not carry over")
WHY_BASIS = "Each factor against today's median for names in this state, in spreads of those names"

# the public contract of the block: context.py's, plus the odds line
ALLOWED = copy.deepcopy(contextmod.ALLOWED)
ALLOWED[""] = ALLOWED[""] | {"odds"}
ALLOWED["odds"] = {"status", "n", "text", "reason"}
PLAN_KEYS = ("zone_hi", "zone_lo", "t1", "t2", "out")


def _pct(price, close):
    return round(100.0 * (price / close - 1.0), 2) + 0.0


def _source(words):
    """a target's source in two or three words, from the read's own phrase for it"""
    import re
    m = re.search(r"the ([\d.]+) extension", words or "")
    if m and "pullback" in words:
        return f"{m.group(1)} pullback extension"
    return f"{m.group(1)} extension" if m else "measured move" if "repeated" in (words or "") else "prior high"


def levels_for(bars, params=None, stop_pct=None, atr=None):
    """{"stop", "zone_lo", "zone_hi", "t1", "t2", "t1_src", "t2_src"} in % from the last close (t1 and t2 None when no
    real level stands above). stop_pct and atr default to the card's own rule (picker plan: stop_atr x ATR(14))"""
    p = params or F.CONFIG
    close = float(bars[-1]["c"])
    atr = float(atr) if atr else float(ta.atr(bars, 14)[-1] or 0.0)
    if not atr or close <= 0:
        return None
    stop_atr = p["plan"].get("stop_atr")
    stop = stop_pct if stop_pct is not None else (_pct(close - stop_atr * atr, close) if stop_atr is not None else None)
    hi = readplan.CAP_ATR * atr
    lo = hi - readplan.ZONE_MAX_ATR * atr
    pool = []                                                         # (price, source): real levels only
    a = R.prepare(bars)
    i = len(bars) - 1
    pool += [(x, "prior high") for x in R.resistances(a, i, close)]
    try:
        from .read.core import Ctx
        pool += [(x, _source(w)) for x, w in readplan.projections(Ctx("X", bars), base=close + hi)]
    except Exception:                                                  # noqa: BLE001  (a projection never stops a card)
        pass
    pool = sorted((x, s) for x, s in pool if x - close >= R.MIN_T1_ATR * atr)
    t1 = pool[0] if pool else None
    t2 = next((q for q in pool if t1 and q[0] - t1[0] >= GAP_ATR * atr), None)
    return {"stop": stop, "zone_lo": _pct(close + lo, close), "zone_hi": _pct(close + hi, close),
            "t1": _pct(t1[0], close) if t1 else None, "t1_src": t1[1] if t1 else None,
            "t2": _pct(t2[0], close) if t2 else None, "t2_src": t2[1] if t2 else None}


def gate(lv):
    """the ordering gate -> the levels, or None when the stop and zone do not make a plan. A target the buy zone has
    already reached (or a T2 under T1) is dropped, never moved"""
    if not lv or not (lv["zone_lo"] < lv["zone_hi"]) or (lv["stop"] is not None and not lv["stop"] < lv["zone_lo"]):
        return None                                                    # a plan with no stop (the fit's) has none to order
    out = dict(lv)
    if out.get("t1") is None or out["t1"] <= out["zone_hi"]:
        out["t1"] = out["t2"] = None
    elif out.get("t2") is not None and out["t2"] <= out["t1"]:
        out["t2"] = None
    return out


def why_rows(card):
    """the why panel from the card's own factors: signed in each factor's favourable direction (z), with its percentile"""
    rows = []
    for f in card.get("features") or ():
        if f.get("z") is None or f.get("pct") is None:
            continue
        rows.append({"key": f["key"], "label": f["label"], "value": f["value"], "base": f["median"], "diff": f["z"],
                     "pct": f["pct"]})
    if not rows:
        return contextmod._nd("No factor to set against today's names")
    rows.sort(key=lambda r: (-abs(r["diff"]), r["key"]))
    return {"status": "ok", "basis": WHY_BASIS, "rows": rows}


def odds_line(n=0):
    return {"status": "pending", "n": n, "reason": ODDS_WHY,
            "text": f"Not yet graded: {n} logged. No win rate until the picker has a record of its own."}


def card_context(card, bars, spy, today, earnings_row=None, filings=None, params=None):
    p = card["plan"]
    lv = gate(levels_for(bars, params, p.get("stop_pct"), p.get("atr")))
    close = card["close"]
    if lv:
        plan = {"zone_hi": lv["zone_hi"], "zone_lo": lv["zone_lo"], "out": lv["stop"], "t1": lv["t1"], "t2": lv["t2"],
                "trim": lv["t2"] is not None and 1}
        plan = {k: v for k, v in plan.items() if v is not None}
    else:
        plan = {}
    fl, fwhy = filings if filings else (None, "Filings not fetched")
    ctx = contextmod.block(bars, spy, plan, close, 0.0, None, {}, earnings_row, fl, today, p.get("exit_by"), fwhy)
    ctx["why"] = why_rows(card)
    if lv:
        for r in ctx["ladder"].get("rows", ()):
            src = lv.get("t1_src") if r["role"] == "t1" else lv.get("t2_src") if r["role"] == "t2" else None
            if src:
                r["label"] += " · " + src
        if lv["t1"] is None and ctx["ladder"]["status"] == "ok":
            ctx["ladder"]["reason"] = "No real level stands above the buy zone"
    ctx["odds"] = odds_line(0)
    return ctx


def enrich(block, bars_by_sym, spy_bars, today, earnings=None, filings=None, params=None):
    """block (fearday.pick) with each card's `context` added, from the bars cut at the block's as_of. filings(sym) ->
    (rows or None, reason); a card whose context cannot be built keeps its plan and carries none"""
    as_of = block.get("as_of")
    if not as_of:
        return block
    spy = F._cut(spy_bars, as_of)
    for lane in ("buy", "watch", "small"):
        for card in block.get(lane) or ():
            try:
                bars = F._cut(bars_by_sym[card["symbol"]], as_of)
                fl = filings(card["symbol"]) if filings else None
                card["context"] = card_context(card, bars, spy, today, (earnings or {}).get(card["symbol"]), fl, params)
            except Exception:                                          # noqa: BLE001  (a card without its context)
                card.pop("context", None)
    return block
