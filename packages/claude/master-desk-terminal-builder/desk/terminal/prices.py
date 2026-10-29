"""The dollars a card shows, and the check every card passes before it is published (batch bs1, item 4).

The edition carries each plan line in % from the close it was measured on; the page draws the dollars
(web/terminal/app.js px), tick-valid and rounded to each line's safe side (item 7). px() here is the same
arithmetic, so the publisher checks the prices a reader sees:
  check(card, high)  -> (the card, its reward to risk computed from the shown prices; [problems])
A card with a problem is held back from publication. Its reasons stay in the desk's own state (board.json,
reads.json and the job's info), never on the page:
  - every plan line a finite number, and for a long: exit < buy low <= buy high < take-profit (< the second target
    a scaled plan sells the rest at), a trigger above the exit and no higher than the buy high, in shown dollars;
  - no take-profit that already traded on the session the plan was made from (high: that session's high, on the
    card's close's scale)."""
import math
from decimal import ROUND_HALF_UP, Decimal

LINES = ("zone_lo", "zone_hi", "trigger", "out", "t1", "t2")


DOWN, UP = -1, 1                # a line's safe side: the buy range and the take-profit down, the exit and a trigger up
ROLE = {"zone_lo": DOWN, "zone_hi": DOWN, "t1": DOWN, "t2": DOWN, "out": UP, "trigger": UP}


def px(close, pct, role=0):
    """the dollar price the page shows for a plan line pct % from close (app.js px, the same arithmetic step by
    step): on the tick an order uses, $0.0001 under $1 and a cent from $1 (whole dollars from $1,000, the owner's
    display), rounded to the safe side of its role (DOWN, UP; 0 the nearest, halves up as Math.round)"""
    x = close * (1 + pct / 100)
    k = 1 if x >= 1000 else 10000 if x < 1 else 100
    y = x * k
    n = math.floor(y + 1e-7) if role < 0 else math.ceil(y - 1e-7) if role > 0 else \
        int(Decimal(y).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return n / k


def usd(close, pct, role=0):
    """the price as the page writes it: $0.5501, $13.86, $1,234"""
    v = px(close, pct, role)
    return "$" + (f"{int(v):,}" if v >= 1000 else f"{v:.4f}" if v < 1 else f"{v:.2f}")


def session_high(bars, as_of, close):
    """the high of the read's own session (as_of) on the scale of `close`, the close its plan is measured from: the
    bar's high over its own close, so a split since the read compares like with like; None without that bar"""
    if not close:
        return None
    from .. import calendar as cal
    b = next((b for b in reversed(bars or ()) if b.get("c") and cal._as_date(float(b["t"])).isoformat() == as_of),
             None)
    return close * float(b["h"]) / float(b["c"]) if b and b.get("h") is not None else None


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def check(card, high=None):
    """(the card with plan.r, and plan.r2 for a scaled plan, computed from the prices it shows; [why it must be held
    back]). A read that stands aside has no prices to check"""
    pl = card.get("plan") or {}
    if card.get("form") == "wait" or pl.get("out") is None:
        return card, []
    if not all(_num(pl.get(k)) for k in ("zone_lo", "zone_hi", "out", "t1")) or \
            not all(pl.get(k) is None or _num(pl[k]) for k in ("trigger", "t2")):
        return card, ["a plan line is not a number"]
    close = card.get("close")
    shown = (lambda k: px(close, pl[k], ROLE[k])) if _num(close) and close > 0 else (lambda k: pl[k])
    d = {k: shown(k) for k in LINES if pl.get(k) is not None}
    lo, hi, out, t1 = d["zone_lo"], d["zone_hi"], d["out"], d["t1"]
    why = []
    if not out < lo <= hi < t1:
        why.append(f"prices out of order: exit {out}, buy {lo} to {hi}, take-profit {t1}")
    if "trigger" in d and not out < d["trigger"] <= hi:
        why.append(f"trigger {d['trigger']} outside exit {out} to buy high {hi}")
    scaled = pl.get("trim") and "t2" in d
    if scaled and not d["t2"] > t1:
        why.append(f"second target {d['t2']} not above the take-profit {t1}")
    if high is not None and _num(close) and close > 0 and t1 <= round(high, 4):
        why.append(f"take-profit {t1} already traded on the plan's own session (high {round(high, 4)})")
    if why:
        return card, why
    plan = dict(pl, r=round((t1 - hi) / (hi - out), 1))
    if scaled and pl.get("r2") is not None:
        plan["r2"] = round((d["t2"] - hi) / (hi - out), 1)
    return dict(card, plan=plan), []
