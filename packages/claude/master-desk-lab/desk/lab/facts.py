"""What the lab records beside the counterfactuals (docs/research/2026-10-18-lab/DESIGN.md sections 5 and 6): how fresh
the price a sleeve decided on was, and how the desk actually executed the decision.

freshness  the price's basis is the freshest bar completed at the decision whose close it matches (within MATCH_REL or
           a cent); no match is a live quote, and so is a price equal to an execution within EXEC_NEAR_S of the
           decision when the bar it matches is not the freshest (a coincidence: ALHC's live 8.31 and its close three
           sessions before, 2026-10-16). Flags: stale (a newer bar of the strategy's own interval had completed),
           cross_session (decided on an earlier session's bar than the one it executed in), off_market (a live price
           more than OFF_MARKET_PCT from the market then: a completed bar at most MARKET_AGE_S old, else an execution
           within EXEC_NEAR_S of the decision; a wide IEX book's ask), mismatch (more than MISMATCH_PCT or MISMATCH_ATR
           from the execution price)
capture    Perold's implementation shortfall of the executed part, in bps signed so that positive is a cost: fill vs the
           decision price (is), the arrival price vs the decision price (delay; arrival = the NBBO mid a fill
           correction recorded, else the quote at submit), fill vs arrival (trade), fill vs the counterfactual next-bar
           open (vs_nbo), and the round trip: the first exit fill of the same sleeve and instrument after the entry"""
import re

from .. import calendar as cal
from ..data.cache import INTERVAL_S
from ..util import et_date
from .tape import session_for

EVENT = re.compile(r"\b(1h|1d|1wk) event (\d{9,11})\b")          # a tensor event row's reason names its event bar
TOKEN = re.compile(r"(?<![0-9A-Za-z])(1m|5m|15m|30m|1h|4h|1d|1wk|1w)(?![0-9A-Za-z])")
ORDER = ("1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1wk")
DAILY = ("1d", "1w", "1wk")
MATCH_REL, MATCH_ABS = 0.0015, 0.01
OFF_MARKET_PCT, MISMATCH_PCT, MISMATCH_ATR = 2.0, 2.0, 0.5
MARKET_AGE_S, EXEC_NEAR_S = 3900, 300


def finest(intervals):
    """the finest of some bar intervals, or None"""
    known = [iv for iv in intervals or () if iv in ORDER]
    return min(known, key=ORDER.index) if known else None


def own_interval(declared, key, reason):
    """the strategy's own bar: its declared bars' finest interval, else its event bar's, else one its key names"""
    if declared:
        return declared
    m = EVENT.search(reason or "")
    if m:
        return m.group(1)
    m = TOKEN.search(key or "")
    return m.group(1) if m else None


def _near(price, ref):
    return abs(price - ref) <= max(MATCH_REL * ref, MATCH_ABS)


def _event_end(iv, t):
    d = cal._as_date(float(t))
    if iv == "1h":
        return min(float(t) + 3600.0, cal.session_close(d)) if cal.is_trading_day(d) else float(t) + 3600.0
    if iv == "1d":
        return cal.session_close(d)
    return cal.session_close(cal.week_last_session(d))


def freshness(tape, t0, price, atr, own=None, exec_px=None, exec_at=None, reason=None):
    """the price basis of one decision (None without a price)"""
    if not price or float(price) <= 0:
        return None
    price = float(price)
    comp = tape.completed(t0)
    basis = next((c for c in comp if _near(price, c[3])), None)
    if basis and basis is not comp[0] and exec_px and exec_at and abs(float(exec_at) - t0) <= EXEC_NEAR_S \
            and _near(price, float(exec_px)):
        basis = None                 # the market at the decision: an older close it also equals is a coincidence
    out = {"basis": basis[0] if basis else ("quote" if comp else None), "own": own}
    if basis:
        out.update(basis_session=basis[2], basis_age_s=round(t0 - basis[1]))
    if comp:
        fresh = comp[0][3]
        out.update(fresh_iv=comp[0][0], fresh_px=round(fresh, 6), fresh_age_s=round(t0 - comp[0][1]),
                   dev_pct=round(100 * (price / fresh - 1), 3),
                   dev_atr=round((price - fresh) / atr, 3) if atr else None)
    m = EVENT.search(reason or "")
    if m:
        out["event_age_s"] = round(t0 - _event_end(m.group(1), int(m.group(2))))
    ex_session = et_date(exec_at) if exec_at else session_for(t0)
    if exec_px:
        gap = price / float(exec_px) - 1
        out.update(exec_px=round(float(exec_px), 6), exec_gap_pct=round(100 * gap, 3),
                   exec_gap_atr=round((price - float(exec_px)) / atr, 3) if atr else None)
    stale = None
    if own in DAILY[:1]:
        last_day = next((c[2] for c in comp if c[0] == "1d"), None)
        stale = bool(basis and basis[0] == "1d" and last_day and basis[2] < last_day)
    elif own in INTERVAL_S and own not in DAILY:
        s = INTERVAL_S[own] + 60
        stale = bool((basis and t0 - basis[1] > s) or out.get("event_age_s", 0) > s)
    out["stale"] = stale
    out["cross_session"] = bool(basis and basis[2] < ex_session) if comp else None
    market = comp[0][3] if comp and t0 - comp[0][1] <= MARKET_AGE_S else \
        (float(exec_px) if exec_px and exec_at and abs(float(exec_at) - t0) <= EXEC_NEAR_S else None)
    out["off_market"] = None if market is None else \
        bool(out["basis"] == "quote" and abs(100 * (price / market - 1)) > OFF_MARKET_PCT)
    out["mismatch"] = None if not exec_px else \
        bool(abs(out["exec_gap_pct"]) > MISMATCH_PCT or abs(out.get("exec_gap_atr") or 0) > MISMATCH_ATR)
    return out


class Index:
    """the record's execution facts by identity: children by (sleeve, instrument), fills by child, corrections by fill
    seq, the engine's rule exits, and the reasons of the exit / target intents by (pass, sleeve, symbol)"""

    def __init__(self, rec):
        self.kids, self.fills, self.rules, self.reasons = {}, {}, {}, {}
        for c in rec.children.values():
            self.kids.setdefault((c.get("sleeve"), c.get("inst")), []).append(c)
        for v in self.kids.values():
            v.sort(key=lambda c: c["at"])
        for f in rec.fills:
            for cid in f.get("children") or ():
                self.fills.setdefault(cid, []).append(f)
        for x in rec.exits.values():
            self.rules.setdefault((x.get("sleeve"), x.get("inst")), []).append(x)
        for at, sid, it in rec.intents:
            if it.get("kind") != "enter":
                self.reasons[(at, sid, it.get("symbol"))] = it.get("reason")
        self.corrected, self.ended = rec.corrected, rec.ended

    def price(self, f):
        """a fill's price after its NBBO correction"""
        c = self.corrected.get(f.get("seq"))
        return float(c["to_px"]) if c and c.get("to_px") else float(f["price"])

    def fills_of(self, children):
        seen, out = set(), []
        for c in children:
            for f in self.fills.get(c["child"], ()):
                if f.get("seq") not in seen:
                    seen.add(f.get("seq"))
                    out.append(f)
        return sorted(out, key=lambda f: (f["at"], f.get("seq") or 0))

    def made_by(self, at, sid, sym, action):
        """the children one intent made in its pass"""
        return [c for c in self.kids.get((sid, "EQ:" + sym), ()) if c["at"] == at and c.get("action") == action]

    def arrival(self, f):
        """the arrival price of a fill: the NBBO mid its correction recorded, else its quote at submit's"""
        for q in ((self.corrected.get(f.get("seq")) or {}).get("nbbo"), f.get("quote_at_submit")):
            try:
                b, a = float(q[0]), float(q[1])
            except (TypeError, ValueError, IndexError):
                continue
            if b > 0 and a >= b:
                return (a + b) / 2.0
        return None


def _bps(sgn, a, b):
    return round(sgn * (float(a) / float(b) - 1.0) * 1e4, 2) if a and b else None


def capture(idx, sid, sym, side, t0, session, px, nbo_px=None):
    """the desk's own execution of one entry signal: {"children": 0} when it made no child"""
    inst, want = "EQ:" + sym, "buy" if side == "long" else "sell"
    kids = [c for c in idx.kids.get((sid, inst), ()) if c.get("action") == "enter" and c.get("side") == want
            and c["at"] >= t0 - 1 and session_for(c["at"]) == session]
    if not kids:
        return {"children": 0}
    fills = idx.fills_of(kids)
    if not fills:
        return {"children": len(kids), "filled": False, "ended": all(c["child"] in idx.ended for c in kids)}
    w = [float(f.get("qty") or 0) or 1.0 for f in fills]
    fill_px = sum(wi * idx.price(f) for wi, f in zip(w, fills)) / sum(w)
    orig_px = sum(wi * float(f["price"]) for wi, f in zip(w, fills)) / sum(w)
    f0, sgn = fills[0], 1.0 if side == "long" else -1.0
    arr = idx.arrival(f0)
    out = {"children": len(kids), "filled": True, "fills": len(fills), "fill_px": round(fill_px, 6),
           "fill_seqs": [f.get("seq") for f in fills], "fill_at": round(f0["at"]), "lag_s": round(f0["at"] - t0),
           "corrected": any(f.get("seq") in idx.corrected for f in fills),
           "arrival_px": None if arr is None else round(arr, 6), "is_bps": _bps(sgn, fill_px, px),
           "delay_bps": _bps(sgn, arr, px), "trade_bps": _bps(sgn, fill_px, arr),
           "vs_nbo_bps": _bps(sgn, fill_px, nbo_px), "corr_bps": _bps(sgn, orig_px, fill_px)}
    out.update(_round_trip(idx, sid, sym, want, f0))
    return out


def _round_trip(idx, sid, sym, want, f0):
    """the first exit fill of the position after the entry fill f0: its reason and its session distance"""
    inst, best = "EQ:" + sym, None
    for c in idx.kids.get((sid, inst), ()):
        if c["at"] >= f0["at"] and c.get("action") in ("exit", "target") and c.get("side") != want:
            for f in idx.fills_of([c]):
                if best is None or f["at"] < best[0]["at"]:
                    best = (f, idx.reasons.get((c["at"], sid, sym)) or c.get("action"))
    for x in idx.rules.get((sid, inst), ()):
        if x["at"] >= f0["at"]:
            for f in idx.fills_of([{"child": x.get("child")}]):
                if best is None or f["at"] < best[0]["at"]:
                    best = (f, "engine rule: " + str(x.get("why") or ""))
    if best is None:
        return {"exit_at": None}
    held = cal.trading_days_between(et_date(f0["at"]), et_date(best[0]["at"]))
    return {"exit_at": round(best[0]["at"]), "exit_reason": (best[1] or "")[:120], "held_sessions": held,
            "same_session_exit": held == 0}
