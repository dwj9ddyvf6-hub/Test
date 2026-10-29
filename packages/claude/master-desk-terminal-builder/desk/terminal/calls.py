"""The scorecard: every setup the terminal publishes becomes a call, resolved mechanically and never edited.

Since Best Setups v2 (2026-10-18) a call is the desk's read (kind "read", open_read_call / resolve_reads below): its
buy zone and cap, its trigger, its out line, its targets, its buy window and its horizon, written before the outcome
with the read's evidence. It fills on the desk's daily bars after the read's session: a buy or a pullback when a
session trades down to the cap (at the open when it opens under it; a session that opens under the out line voids the
call), a breakout or a turn on the first daily close over the trigger and a reaction on its daily close up inside the
zone, each at the next session's open, what a reader who saw that close can trade (a close past the cap is a missed
buy, and so is a next open past it; a next open under the out line voids it). It closes at the next session's open
after the first daily close under the out line, on the first session that trades up to the first target (at the
target, or the open when it opens over it), or at the close of the time stop, twice the horizon (at most 40
sessions); the out line first when both happen in one session. Calls listed before this rule (no "fill" key) keep the
one they were listed with: filled and sold at the signal's close itself. A wave call (its plan's trim, since
2026-10-19) scales out the way Echo manages a trade: a fifth comes off on the first session that trades up to the
first target (at the target, or the open over it), and the rest closes on the out line, the second target or its time
stop (twice the horizon to the second target); its result counts both parts. A buy that never comes within its window
expires and is not a result. Calls before v2 (kind "plan") keep the rules below.

A call opens the first time a setup is listed. Internally (state/terminal/calls.json) it keeps its reference price,
the latest close the desk's caches held at publication; that price is never published. It resolves on the desk's own
daily bars after its opening day:
  - the plan's stop or target, whichever a bar reaches first (both in one bar: the stop; a gap through a level fills at
    the open);
  - otherwise the close of the plan's last session (5 sessions when the plan names none).
Published per call: side, grade, opening edition, status, how it closed, the outcome in % (and in R when the plan has a
stop), and for a long its status under the owner's fear-day rule (desk/terminal/fear.py), recomputed while the call is
open and kept as it was when it closed. Calls are only ever added and closed. Each edition's published calls are hashed into a chain with the previous
edition's hash, so a quiet rewrite of history would show."""
import hashlib
import json
import os
from datetime import datetime

from .. import calendar as cal
from ..util import read_json, write_json_atomic

DEFAULT_SESSIONS = 5
NEXT_OPEN = "next_open"         # a call's fill rule: a daily close that buys or sells trades at the next session's open
PUBLIC_KEYS = ("id", "kind", "symbol", "side", "form", "conviction", "take", "opened", "status", "exit",
               "outcome_pct", "outcome_r", "sessions", "fear", "ref_close",      # no grade: v2 shows none (old calls keep theirs)
               "filled", "closed", "stop_by")     # the sessions it filled and closed on, and its time stop's (stop_by)
TIME_STOP_MAX = 40


def path(root):
    return os.path.join(root, "state", "terminal", "calls.json")


def load(root):
    return read_json(path(root), []) or []


def save(root, calls):
    write_json_atomic(path(root), calls)


def open_call(calls, setup, ref, opened_iso, signal_at=None):
    """append one open call for a newly listed setup; -> its id"""
    cid = f"c-{len(calls) + 1:04d}"
    plan = setup.get("plan") or {}
    calls.append({"id": cid, "symbol": setup["symbol"], "side": setup["side"], "grade": setup["grade"],
                  "opened": opened_iso, "signal_at": signal_at, "ref": ref, "stop_pct": plan.get("stop_pct"),
                  "target_pct": plan.get("target_pct"), "sessions": plan.get("sessions"), "status": "open",
                  "exit": None, "outcome_pct": None, "outcome_r": None, "closed": None})
    return cid


def find(calls, cid):
    return next((c for c in calls if c["id"] == cid), None)


def until(c):
    """the call's last session: its horizon (the plan's sessions, else DEFAULT_SESSIONS) counted after its opening day,
    as resolve() counts it"""
    d = cal._as_date(c["opened"])
    for _ in range(int(c.get("sessions") or DEFAULT_SESSIONS)):
        d = cal.next_trading_day(d)
    return d


def fear_days(calls, daily_by_sym):
    """the fear-day status of every open long call, from the setup's first signal (or, for a call opened before the
    signal was kept, its opening); a closed call keeps the status it had"""
    from . import fear
    for c in calls:
        if c["status"] not in ("open", "waiting") or c["side"] != "long":     # a read call waits for its buy
            continue
        at = c.get("signal_at") or datetime.fromisoformat(c["opened"]).timestamp()
        f = fear.status(c["symbol"], c["side"], at, daily_by_sym)
        if f:
            c["fear"] = {k: f[k] for k in ("state", "label", "short", "date")}
    return calls


def _outcome(c, px):
    sign = 1 if c["side"] == "long" else -1
    pct = sign * (px / c["ref"] - 1) * 100
    r = pct / abs(c["stop_pct"]) if c.get("stop_pct") else None
    return round(pct, 2), (None if r is None else round(r, 2))


def resolve(calls, daily_by_sym):
    """close every open call whose plan or horizon has resolved on the bars after its opening day (the calls before
    v2; read calls resolve in resolve_reads)"""
    for c in calls:
        if c.get("kind") == "read":
            continue
        if c["status"] != "open" or not c.get("ref"):
            if c["status"] == "open" and not c.get("ref"):
                c.update(status="void", exit="no reference price")
            continue
        opened = cal._as_date(c["opened"])
        bars = [b for b in daily_by_sym.get(c["symbol"]) or [] if cal._as_date(float(b["t"])) > opened]
        horizon = int(c.get("sessions") or DEFAULT_SESSIONS)
        ref, long_ = float(c["ref"]), c["side"] == "long"
        stop = ref * (1 + c["stop_pct"] / 100) if c.get("stop_pct") is not None else None
        target = ref * (1 + c["target_pct"] / 100) if c.get("target_pct") is not None else None
        for b in bars[:horizon]:
            o, h, lo = float(b["o"]), float(b["h"]), float(b["l"])
            hit_stop = stop is not None and (lo <= stop if long_ else h >= stop)
            hit_target = target is not None and (h >= target if long_ else lo <= target)
            if hit_stop:                                   # the stop first, also when both are in one bar
                px = (min(o, stop) if long_ else max(o, stop))
                c.update(status="closed", exit="stop", closed=cal._as_date(float(b["t"])).isoformat())
                c["outcome_pct"], c["outcome_r"] = _outcome(c, px)
                break
            if hit_target:
                px = (max(o, target) if long_ else min(o, target))
                c.update(status="closed", exit="target", closed=cal._as_date(float(b["t"])).isoformat())
                c["outcome_pct"], c["outcome_r"] = _outcome(c, px)
                break
        else:
            if len(bars) >= horizon:
                b = bars[horizon - 1]
                c.update(status="closed", exit="horizon", closed=cal._as_date(float(b["t"])).isoformat())
                c["outcome_pct"], c["outcome_r"] = _outcome(c, float(b["c"]))
    return calls


def stop_by(c):
    """the session a filled read call's time stop closes it on, by resolve_reads' own count: a buy at a session's
    open holds from that session (the next-open rule's breakouts, turns and reactions), any other buy from the
    session after its fill; None before a fill"""
    if c.get("kind") != "read" or not c.get("filled") or not c.get("time_stop"):
        return None
    on_open = c.get("fill") == NEXT_OPEN and (c.get("form") in ("breakout", "turn") or c.get("mode") == "reaction")
    d = cal._as_date(c["filled"])
    for _ in range(int(c["time_stop"]) - (1 if on_open else 0)):
        d = cal.next_trading_day(d)
    return d.isoformat()


def public(calls, limit=50):
    """the newest calls first, published fields only (no reference price, no line), each call's own fields: a call
    before v2 has no form, conviction or take; its kind reads "plan" """
    out = []
    for c in reversed(calls[-limit:]):
        c = dict(c, stop_by=stop_by(c))
        d = {k: c.get(k) for k in PUBLIC_KEYS if c.get(k) is not None or k in ("exit", "outcome_pct", "outcome_r")}
        d["kind"] = c.get("kind") or "plan"
        out.append(d)
    return out


def scorecard(calls):
    def summary(cs):
        closed = [c for c in cs if c["status"] == "closed"]
        hits = sum(1 for c in closed if (c["outcome_pct"] or 0) > 0)
        rs = [c["outcome_r"] for c in closed if c.get("outcome_r") is not None]
        return {"calls": len(cs), "closed": len(closed), "hits": hits,
                "hit_rate": round(hits / len(closed), 3) if closed else None,
                "mean_pct": round(sum(c["outcome_pct"] for c in closed) / len(closed), 2) if closed else None,
                "mean_r": round(sum(rs) / len(rs), 2) if rs else None}
    live = [c for c in calls if c["status"] in ("open", "closed")]
    s = summary(live)
    s.update(since=live[0]["opened"][:10] if live else None, open=sum(1 for c in live if c["status"] == "open"),
             by_grade={g: summary([c for c in live if c["grade"] == g]) for g in ("A", "B", "C")
                       if any(c["grade"] == g for c in live)},
             note=("Every published setup becomes a call and stays listed, losers included; a call closes on its "
                   "plan's stop or target, or at the end of its holding period (5 sessions when the plan names none). "
                   "Paper results."))
    return s


def chain(prev, public_calls):
    """sha256 of the previous edition's chain and this edition's published calls"""
    body = json.dumps(public_calls, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(((prev or "") + body).encode()).hexdigest()


def open_read_call(calls, pub, rec, opened_iso, listed_ts=None, published=True, engine=None):
    """append one call for a newly listed read; -> its id. The prices stay here, never published. published=False:
    its edition has not reached the public yet; it waits (mark_published) and counts from the edition that does.
    engine: the card's engine line at listing with the screen's tier and veto (engine.at_listing), kept so the forward
    record can split calls by them; it scores nothing and is never published"""
    cid = f"c-{len(calls) + 1:04d}"
    pl = pub["plan"]
    calls.append({"id": cid, "kind": "read", "symbol": pub["symbol"], "side": "long", "form": pub["form"],
                  "conviction": pub["conviction"]["word"], "take": pub["gut"]["word"], "opened": opened_iso,
                  "signal_at": listed_ts, "as_of": rec["as_of"], "zone": list(rec["zone"]), "trigger": rec["trigger"],
                  "out": rec["out"], "t1": rec["t1"], "t2": rec["t2"], "window_until": pl["window"],
                  "sessions": pl["sessions"], "time_stop": min(2 * int(pl["sessions"]), TIME_STOP_MAX),
                  "read": {k: rec.get(k) for k in ("v", "code", "evidence", "points", "gut_points", "source",
                                                   "facts")},
                  "status": "waiting", "filled": None, "entry": None, "exit": None, "closed": None,
                  "outcome_pct": None, "outcome_r": None, "ref_close": rec.get("close"),
                  "mode": rec.get("mode") or "level", "fill": NEXT_OPEN})
    if rec.get("trim") and rec.get("t2"):                  # a wave call scales out: a fifth at t1, the rest at t2
        calls[-1].update(trim=rec["trim"], time_stop=int(rec.get("time_stop") or calls[-1]["time_stop"]))
    if not published:
        calls[-1]["published"] = False
    if engine:
        calls[-1]["engine"] = dict(engine)
    return cid


def mark_published(calls, at_iso):
    """the calls whose edition just reached the public count from that edition's time (the audit's F5: a call from an
    edition whose push failed counted sessions the public never saw it in)"""
    for c in calls:
        if c.get("published") is False:
            c.update(published=True, opened=at_iso)


def risk_unit(c):
    """the plan's own risk, set before the outcome: its cap over its out line (in the read's prices). R is measured in
    it, never in the fill's distance to the out, which a gap down to just above the out makes as small as it likes
    (the audit's F1: +219R on a plan that risked 5)"""
    return c["zone"][1] - c["out"]


def _close_read(c, b, px, why, day=None):
    """close the call (the rest of it, after a trim) at px; the result counts the trimmed part at its own price"""
    c.update(status="closed", exit=why, closed=day or cal._as_date(float(b["t"])).isoformat())
    e, t, u = c["entry"], c.get("trimmed"), risk_unit(c)
    w = float(c["trim"]) if t else 0.0
    gain = (1 - w) * (px - e) + (w * (t["px"] - e) if t else 0.0)
    c["outcome_pct"] = round(gain / e * 100, 2) if t else round((px / e - 1) * 100, 2)
    c["outcome_r"] = round(gain / u, 2) if u > 0 else None


def first_session(c):
    """the first session that opens after the call was listed (a call listed before a session's open counts that
    session, as in the fear-day rule's window): the record never fills a call on prices that began before it"""
    try:
        at = datetime.fromisoformat(c["opened"]).timestamp()
    except (KeyError, TypeError, ValueError):
        return None
    d = cal._as_date(at)
    if not (cal.is_trading_day(d) and at < cal.session_open(d)):
        d = cal.next_trading_day(d)
    return d


def split_factor(c, bars):
    """the cache's scale against the call's: its read's session close in today's split-adjusted bars over the close
    the read saw (1.0 within 0.5%), or None when the bars hold no close for that session (the call waits for it: a
    guess of 1.0 would read a split's halved prices as a crash). A call opened before ref_close was kept takes
    today's close of that session as its reference, once"""
    as_of = c.get("as_of")
    base = next((float(b["c"]) for b in bars if cal._as_date(float(b["t"])).isoformat() == as_of), None)
    if base is None:
        return None
    if not c.get("ref_close"):
        c["ref_close"] = base
        return 1.0
    f = base / float(c["ref_close"])
    return f if abs(f - 1.0) > 0.005 else 1.0


RAN_AWAY = "it reached its target without coming back to the buy"


GRACE = 5                      # trading sessions without a bar before a name's prices count as stopped


def resolve_reads(calls, daily_by_sym, today=None):
    """fill, then close, every live read call on the daily bars from the first session that opens after it was listed
    (first_session; never before its read's). Each edition walks the call again: an open call skips the sessions up
    to its fill. A waiting buy whose price reaches its target before any fill is missed (RAN_AWAY). The call keeps its
    read's prices; a split since then scales them to the cache (split_factor) and every price it stores goes back to
    the read's scale. With today (the session the caller is in), no call waits forever (the audit's F7): a buy whose
    window has passed by the calendar expires even when no bar came to show it, and a held call whose prices stopped
    (no bar in the last GRACE sessions) closes at its last close once its time stop has passed by the calendar. A call
    whose edition has not reached the public yet waits (mark_published)"""
    today = cal._as_date(today) if today is not None else None
    for c in calls:
        if c.get("kind") != "read" or c["status"] not in ("waiting", "open") or c.get("published") is False:
            continue
        as_of = cal._as_date(c["as_of"])
        every = daily_by_sym.get(c["symbol"]) or []
        f = split_factor(c, every)
        if f is None:
            if any(cal._as_date(float(b["t"])) > as_of for b in every):
                c["baseline"] = "missing"                  # its read's session is gone from the prices: it waits
            if today and c["status"] == "waiting" and today.isoformat() > c["window_until"]:
                c.update(status="expired", closed=c["window_until"],
                         exit="its read's session is missing from the prices")
            continue
        c.pop("baseline", None)
        first = first_session(c) or as_of
        bars = [b for b in every if cal._as_date(float(b["t"])) > as_of and cal._as_date(float(b["t"])) >= first]
        lo_z, cap = c["zone"]
        cap, out, t1 = cap * f, c["out"] * f, c["t1"] * f
        trigger = c["trigger"] * f if c.get("trigger") is not None else None
        held = 0
        nxt = c.get("fill") == NEXT_OPEN                   # a close that buys or sells trades at the next open
        on_open = nxt and (c["form"] in ("breakout", "turn") or c.get("mode") == "reaction")   # bought at an open
        pending = None                                     # "buy" or "out": last session's close, done at this open
        for b in bars:
            day = cal._as_date(float(b["t"])).isoformat()
            o, h, lw, cl = float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"])
            if c["status"] == "open" and c.get("filled") and day <= c["filled"] and not (on_open and day == c["filled"]):
                if nxt and day == c["filled"] and cl <= out:
                    pending = "out"                        # walked again: the buy's own session closed under the out
                continue                                   # walked again: the sessions up to the fill are behind it
            if c["status"] == "waiting" and pending == "buy":
                pending = None                             # the close that buys came last session: this open fills
                if o > cap:
                    c.update(status="missed", exit="opened past the cap", closed=day)
                    break
                if o <= out:
                    c.update(status="void", exit="opened under the out line before the buy", closed=day)
                    break
                c.update(status="open", filled=day, entry=o / f)      # held from this open: the session counts
            elif c["status"] == "waiting":
                if day > c["window_until"]:
                    c.update(status="expired", closed=day,
                             exit="never triggered" if c["form"] in ("breakout", "turn") else "never reached the buy")
                    break
                if c["form"] in ("now", "pullback") and c.get("mode") == "reaction":
                    prev = float(every[every.index(b) - 1]["c"]) if every.index(b) > 0 else o
                    if cl <= out:
                        c.update(status="void", exit="closed under the out line before a reaction", closed=day)
                        break
                    if lw > cap or not (cl > o and cl > prev) or cl < lo_z * f:
                        if h >= t1:
                            c.update(status="missed", exit=RAN_AWAY, closed=day)
                            break
                        continue                               # no reaction yet: a close up inside the zone
                    if cl > cap:
                        c.update(status="missed", exit="the reaction closed past the cap", closed=day)
                        break
                    if nxt:
                        pending = "buy"
                        continue
                    c.update(status="open", filled=day, entry=cl / f)
                    continue
                if c["form"] in ("now", "pullback"):
                    if lw > cap:
                        if h >= t1:                            # the move happened without it: the plan is spent
                            c.update(status="missed", exit=RAN_AWAY, closed=day)
                            break
                        continue
                    px = min(o, cap)
                    if px <= out:
                        c.update(status="void", exit="opened under the out line before the buy", closed=day)
                        break
                    c.update(status="open", filled=day, entry=px / f)
                    if cl <= out:
                        if nxt:
                            pending = "out"
                            continue
                        _close_read(c, b, cl / f, "out")
                        break
                    continue
                if cl < trigger:
                    continue
                if cl > cap:
                    c.update(status="missed", exit="closed past the cap", closed=day)
                    break
                if nxt:
                    pending = "buy"
                    continue
                c.update(status="open", filled=day, entry=cl / f)
                continue
            if pending == "out":
                _close_read(c, b, o / f, "out")           # the close under the out line sells at this open
                break
            held += 1
            if cl <= out:
                if nxt:
                    pending = "out"                        # the out line first: it sells at the next open
                    continue
                _close_read(c, b, cl / f, "out")
                break
            if c.get("trim") and c.get("t2"):              # Echo's management: a fifth at t1, the rest rides to t2
                t2 = c["t2"] * f
                if h >= t1 and not c.get("trimmed"):
                    c["trimmed"] = {"day": day, "px": max(o, t1) / f}
                if h >= t2:
                    _close_read(c, b, max(o, t2) / f, "target")
                    break
            elif h >= t1:
                _close_read(c, b, max(o, t1) / f, "target")
                break
            if held >= c["time_stop"]:
                _close_read(c, b, cl / f, "time stop")
                break
        if today and c["status"] in ("waiting", "open"):
            _by_the_calendar(c, bars, f, today, pending)
    return calls


def _by_the_calendar(c, bars, f, today, pending=None):
    """end a call the bars cannot: a buy past its window, a held call whose prices stopped past its time stop. A buy
    whose close came (pending, its fill at the next open) waits for that open, unless the prices stopped"""
    if c["status"] == "waiting" and pending == "buy":
        last = cal._as_date(float(bars[-1]["t"]))
        if last <= cal.prev_trading_day(today, GRACE):
            c.update(status="expired", closed=today.isoformat(), exit=f"no prices after {last.isoformat()}")
        return
    if c["status"] == "waiting" and today.isoformat() > c["window_until"]:
        c.update(status="expired", closed=c["window_until"],
                 exit="never triggered" if c["form"] in ("breakout", "turn") else "never reached the buy")
        return
    if c["status"] != "open" or not c.get("filled"):
        return
    last = cal._as_date(float(bars[-1]["t"])) if bars else cal._as_date(c["filled"])
    if last > cal.prev_trading_day(today, GRACE):
        return                                             # the prices are current: the bars decide
    if cal.trading_days_between(cal._as_date(c["filled"]), today) <= c["time_stop"]:
        return
    px = float(bars[-1]["c"]) / f if bars else c["entry"]          # its last close; the fill's own price at worst
    _close_read(c, None, px, f"no prices after {last.isoformat()}", day=today.isoformat())


RETIRED_BOARD = "v2"


def retire(calls, day, board=RETIRED_BOARD):
    """freeze the old board: every read call made before `day` is marked retired once (the board, the date); nothing
    is deleted, its status and grading go on, and the record keeps showing it -> how many were marked"""
    n = 0
    for c in calls:
        if c.get("kind") == "read" and not c.get("retired") and (c.get("opened") or "")[:10] <= day:
            c["retired"] = {"board": board, "on": day}
            n += 1
    return n


def live(calls):
    """{call id: symbol} of the read calls still waiting or open"""
    return {c["id"]: c["symbol"] for c in calls if c.get("kind") == "read" and c["status"] in ("waiting", "open")}


def called(calls):
    """the (symbol, read session) pairs that already had a read call"""
    return {(c["symbol"], c.get("as_of")) for c in calls if c.get("kind") == "read"}


def result_words(c):
    """a closed read call's result in words: "Hit its target: +6.1% (+1.5R)" """
    if c["status"] == "expired":
        return "Expired: " + c["exit"]
    if c["status"] in ("missed", "void"):
        return c["exit"][0].upper() + c["exit"][1:]
    if c["status"] != "closed":
        return None
    r = c.get("outcome_r")
    pct = c["outcome_pct"]
    num = f"{pct:+.1f}%".replace("-", "−") + (f" ({r:+.1f}R)".replace("-", "−") if r is not None else "")
    head = {"target": "Hit its target", "out": "Out", "time stop": "Time stop"}.get(c["exit"], c["exit"])
    if c.get("trim") and c["exit"] == "target":
        head = "Hit its second target"
    elif c.get("trimmed"):
        head += ", a fifth off at the first target"
    return head + ": " + num


def scorecard_reads(calls):
    """the record of the read calls: every listed call, how many filled, closed and hit, the mean R, by conviction
    and by the desk's take"""
    def summary(cs):
        closed = [c for c in cs if c["status"] == "closed"]
        hits = sum(1 for c in closed if (c.get("outcome_r") or 0) > 0)
        rs = [c["outcome_r"] for c in closed if c.get("outcome_r") is not None]
        return {"calls": len(cs), "filled": sum(1 for c in cs if c.get("filled")), "closed": len(closed),
                "hits": hits, "hit_rate": round(hits / len(closed), 3) if closed else None,
                "mean_r": round(sum(rs) / len(rs), 2) if rs else None}
    rc = [c for c in calls if c.get("kind") == "read"]
    s = summary(rc)
    s.update(since=rc[0]["opened"][:10] if rc else None,
             open=sum(1 for c in rc if c["status"] == "open"), waiting=sum(1 for c in rc if c["status"] == "waiting"),
             by_conviction={w: summary([c for c in rc if c["conviction"] == w])
                            for w in ("High conviction", "Solid", "Speculative") if any(c["conviction"] == w for c in rc)},
             by_take={w: summary([c for c in rc if c["take"] == w])
                      for w in ("Strong", "For", "Leaning", "Against") if any(c["take"] == w for c in rc)},
             note="Every listed setup is a call, written down before the outcome and scored as a reader could "
                  "trade it: a buy that waits for a daily close fills at the next session's open, a daily close below "
                  "the out line sells at the next open, the target when it trades, the time stop at the close of "
                  "twice the horizon, at most 40 sessions (a wave call's measured to its second target). A wave "
                  "call takes a fifth off at its first target and holds the rest for its second. Earlier calls keep "
                  "the rule they were listed with: filled and sold at that close.")
    return s
