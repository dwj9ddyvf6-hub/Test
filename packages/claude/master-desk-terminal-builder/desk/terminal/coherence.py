"""The board's logic gate (owner, 2026-10-26: "there shouldn't be any logical gaps"): every card and watching row is
checked against the rules a careful reader applies, every edition. A watching row that fails is dropped (it is
context); a card that fails keeps its place (its call is on the record) and the failure is reported in the edition's
status, so the desk's own check names it before a reader does.

Rules, on a long plan in % from its own close:
  order     the stop sits below the buy and the buy below the target (out < zone_lo <= zone_hi < t1, or out < trigger < t1);
            a short or a put mirrors it (stop above the entry, entry above the target, the target below today's price)
  target    the target is above today's price (now_pct)
  room      High conviction needs reward to risk of 1.3 or more (call.R_HIGH); a watching row 1.5 from the top of its buy
  spike     no breakout trigger beside "up N% in 10 sessions" (a spike waits for a pullback, never a breakout)
  dates     the buy window and the plan's horizon are not in the past
  room      a card's reward to risk is at least R_MIN (1.0), the floor the page states
  one way   a Buy card is a long: a short or put side on a Buy is two directions on one card"""
from .read.call import R_HIGH
from .board import WATCH_MIN_R

R_MIN = 1.0                     # a card's reward to risk floor (the page's own rule)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def problems(entry, today, kind):
    """[str]: what does not add up on one card (kind 'setup') or watching row (kind 'watching')"""
    p = entry.get("plan") if kind == "setup" else entry
    p = p or {}
    out, t1, trig, lo, hi = p.get("out"), p.get("t1"), p.get("trigger"), p.get("zone_lo"), p.get("zone_hi")
    now = entry.get("now_pct")
    if str(entry.get("side") or p.get("side") or "long").lower() in ("short", "put"):
        # a short or a put mirrors the long: stop above the entry, entry above the target. Flip every level about the
        # close and the long's rules read the same (the zone's ends swap)
        neg = lambda v: -v if _num(v) else v
        out, t1, trig, lo, hi, now = neg(out), neg(t1), neg(trig), neg(hi), neg(lo), neg(now)
    bad = []
    if kind == "setup" and entry.get("action") == "Buy" and \
            str(entry.get("side") or p.get("side") or "long").lower() in ("short", "put"):
        bad.append("one direction: a Buy card with a short side")
    buy_lo = trig if _num(trig) else lo
    buy_hi = trig if _num(trig) else hi
    if not all(_num(v) for v in (out, t1, buy_hi)) or not (_num(trig) or _num(lo)):
        return ["plan incomplete"]                       # a range needs both ends ("Buy between $NaN and ..." live)
    if not (out < (buy_lo if _num(buy_lo) else buy_hi) <= buy_hi < t1):
        bad.append("stop, buy and target out of order")
    if _num(now) and t1 <= now:
        bad.append("target at or below today's price")
    risk = buy_hi - out
    if risk > 0:
        room = (t1 - buy_hi) / risk
        if kind == "watching" and room < WATCH_MIN_R:
            bad.append(f"reward to risk {room:.1f} from the top of the buy")
        word = (entry.get("conviction") or {}).get("word") if kind == "setup" else None
        r = p.get("r")
        if kind == "setup" and _num(r) and r < R_MIN:
            bad.append(f"reward to risk {r} under {R_MIN}")
        if word == "High conviction" and _num(r) and r < R_HIGH:
            bad.append(f"High conviction on reward to risk {r}")
    if kind == "watching" and entry.get("spike") is not None and _num(trig):
        bad.append("a breakout trigger after a spike")
    for k in ("window", "by"):
        d = p.get(k)
        if isinstance(d, str) and today and d < today and entry.get("status", "waiting") == "waiting":
            bad.append(f"{k} {d} is past")
    return bad


def gate(edition, today):
    """(edition, report): watching rows that fail are dropped; failing cards stay and are named in the report"""
    report = {}
    for s in edition.get("setups") or []:
        b = problems(s, today, "setup")
        if b:
            report[s["symbol"]] = b
    kept = []
    for w in edition.get("watching") or []:
        b = problems(w, today, "watching")
        if b:
            report["watching:" + w["symbol"]] = b
        else:
            kept.append(w)
    edition["watching"] = kept
    return edition, report
