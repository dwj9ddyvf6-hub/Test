"""core/em_1587 — the pure math of Azrael's 15.87 Rule
(AZRAEL-1587-20261022), reverse engineered in
~/workspace/opt/rea-teardowns/azrael-1587/ (TEARDOWN.md,
MATH-RECONSTRUCTION.md, SPEC.md). This module is the rule and
nothing else: given a prior close and a prior ^VIX close it
draws the five-line map, names the regime, evaluates the
morning boxes, the Three-Ticker Break and the edge fade, and
cross-checks the map against the open-interest shortlist.
No desk doors, no orders — sleeves/em_1587.py consumes it.

The reconstruction decisions RD-1..RD-12 (SPEC.md) are bound
here as named constants/formulas, not re-decided:

  RD-1  the divisor is the LITERAL 15.87 (the document's own
        print of sqrt(252) = 15.874508...; the golden days
        reproduce only with the literal).
  RD-3  EM is rounded to 0.1 pt BEFORE any line is drawn and
        before any scaling (the weekly figure proves it: the
        post day's weekly is 182.2 = round1(81.5 x sqrt(5)),
        not the 182.3 the unrounded EM would give).
  RD-4  funded range to time t: EM x sqrt(elapsed / session),
        session = 390 min on a full day (the actual session
        length on early-close days).
  RD-6  each ticker's box gate uses THAT ticker's own EM
        (per-ticker reading — the reading under which the
        2026-10-19 worked example does not trade).
  RD-7  room gate: strictly more than 8 SPX points to the
        next map line AND at least 1R, 1R = entry close minus
        the box edge.
  RD-8  OI agreement tolerance: 5 SPX points.
  RD-9  the OI shortlist is the top-3 strikes by TOTAL open
        interest above and below spot; the second-wall pair is
        ceiling = argmax CALL OI above spot, floor = argmax
        PUT OI below spot.
  RD-10 the fade's entry line is the +/-1.0 wall (desk
        default); its stop is the pre-written session 1R in
        points — the source specifies NO fade stop, so the
        sleeve binds the slot to the worksheet convention
        (DESK-CHOICE DC-3 in ports/em_1587.md: session 1R =
        EM/2, the map's station spacing). A reconstruction,
        never the author's rule.
  RD-11 regimes off the same prior VIX print: < 15 FADE,
        15 <= v <= 18.5 CONFIRM, > 18.5 FAST (the brief's
        names for the spec's CALM / MIXED / FAST).
  RD-12 the session's one_R slot: for the Break it is set at
        signal time from the structural stop; the worksheet
        slot otherwise carries the desk-filled session 1R
        (DC-3). Contract sizing is a desk parameter and lives
        in the sleeve, not here.

Desk expression: SPX has no price feed on this desk's doors,
so the map is computed in SPY terms and the three tickers are
SPY (the map), SPY, QQQ. SPX-denominated constants (RD-7's 8
points, RD-8's 5 points) are converted to anchor points by
SPX_SCALE = 10.0 (DC-1: SPX trades at ~10x SPY; on the
2026-10-19 worked example the SPY room of 4.23 pts reads 42.3
SPX pts, consistent with the document's own SPX reading of
that morning). The golden tests in
tests/test_em_1587_20261022.py run this module on the
author's own SPX inputs, where scale = 1.
"""
import math
from datetime import time as dtime

# -- the rule's own constants ----------------------------------
DIVISOR = 15.87                    # RD-1 (literal)
WALL_FRAC = 1.0                    # the +/-1.0 EM walls
SHELF_FRAC = 0.5                   # the +/-0.5 EM shelves
BOX_MAX_FRAC = 0.2                 # box width cap, x EM_X
BREAK_MIN_FRAC = 0.05              # break distance, x EM_X
ROOM_MIN_SPX = 8.0                 # RD-7, SPX points
AGREE_TOL_SPX = 5.0                # RD-8, SPX points
FADE_ENTRY_FRAC = 1.0              # RD-10 default: the wall
REGIME_FADE_MAX = 15.0             # RD-11: vix < 15 -> FADE
REGIME_CONFIRM_MAX = 18.5          # RD-11: vix <= 18.5 -> CONFIRM
SPX_SCALE = 10.0                   # DC-1 (SPX ~ 10 x SPY)

# -- the clock (hard constants, SPEC section 1) ----------------
WINDOW_START = dtime(9, 50)        # no entries before 09:50
LAST_ENTRY_CLOSE = dtime(11, 5)    # last signal close 11:05
FLAT_T = dtime(11, 30)             # hard flat 11:30
BOX_BAR_STARTS = (dtime(9, 30), dtime(9, 35),
                  dtime(9, 40), dtime(9, 45))

REGIME_FADE = "FADE"
REGIME_CONFIRM = "CONFIRM"
REGIME_FAST = "FAST"

LINE_ORDER = ("WALL_DN", "SHELF_DN", "MAGNET",
              "SHELF_UP", "WALL_UP")


def round1(x):
    return round(float(x), 1)


def pct_move(vix_close):
    """The day's priced move in PERCENT: prior VIX close /
    15.87 (RD-1). PDF day: 14.84 / 15.87 = 0.9351 -> the
    document prints 0.94%."""
    return float(vix_close) / DIVISOR


def expected_move(anchor_close, vix_close):
    """EM in points, rounded to 0.1 BEFORE anything is drawn
    or scaled from it (RD-3)."""
    return round1(float(anchor_close) * pct_move(vix_close)
                  / 100.0)


def regime_for(vix_close):
    """RD-11 boundaries: exactly 15 is CONFIRM, exactly 18.5
    is CONFIRM; FAST begins strictly above 18.5."""
    v = float(vix_close)
    if v < REGIME_FADE_MAX:
        return REGIME_FADE
    if v <= REGIME_CONFIRM_MAX:
        return REGIME_CONFIRM
    return REGIME_FAST


def map_lines(anchor_close, em):
    """The five lines from the ROUNDED EM (RD-3). Values are
    rounded to 2dp for filing (the author's prints are 2dp;
    the arithmetic itself is exact at 2dp: a 2dp close plus a
    1dp EM or its exact half)."""
    c = float(anchor_close)
    e = float(em)
    return {
        "WALL_UP": round(c + WALL_FRAC * e, 2),
        "SHELF_UP": round(c + SHELF_FRAC * e, 2),
        "MAGNET": round(c, 2),
        "SHELF_DN": round(c - SHELF_FRAC * e, 2),
        "WALL_DN": round(c - WALL_FRAC * e, 2),
    }


def funded_range(em, minutes_since_open, session_minutes=390):
    """RD-4: the elapsed-time funded range, EM x
    sqrt(elapsed / session). At the 11:30 flat on a full day
    (120 of 390 minutes) the PDF day's 73.0 EM funds +/-40.5.
    """
    if session_minutes <= 0:
        return 0.0
    frac = max(0.0, float(minutes_since_open)
               / float(session_minutes))
    return float(em) * math.sqrt(frac)


def weekly_em(em):
    """The weekly bound: the ROUNDED daily EM x sqrt(5),
    itself rounded to 0.1 (RD-3's pipeline; post day 182.2).
    """
    return round1(float(em) * math.sqrt(5.0))


def build_map(anchor_close, vix_close, session_minutes=390):
    """The frozen pre-open map (SPEC section 3.1). Pure: the
    same two prints always draw the same map. session_1r is
    the worksheet's pre-written 1R slot, desk-filled with the
    station spacing EM/2 (DC-3); for a Break position the
    position's own 1R is set at signal time instead (RD-12).
    """
    em = expected_move(anchor_close, vix_close)
    lines = map_lines(anchor_close, em)
    return {
        "anchor_close": float(anchor_close),
        "vix_close": float(vix_close),
        "pct": pct_move(vix_close),
        "em": em,
        "lines": lines,
        "regime": regime_for(vix_close),
        "session_1r": round(em / 2.0, 4),
        "funded_at_flat": funded_range(
            em, 120, session_minutes),
        "weekly_em": weekly_em(em),
        "session_minutes": int(session_minutes),
    }


def morning_box(bars, session_d):
    """The first-20-minute box (09:30-09:50) from shaped 5m
    bars: the four bars STARTING 09:30/09:35/09:40/09:45.
    Returns {"hi", "lo", "width"} or None when any of the
    four bars is missing — a partial box is no box."""
    picked = {}
    for b in bars or []:
        t = b["t"]
        if t.date() == session_d and t.time() in BOX_BAR_STARTS:
            picked[t.time()] = b
    if len(picked) != len(BOX_BAR_STARTS):
        return None
    hi = max(float(b["high"]) for b in picked.values())
    lo = min(float(b["low"]) for b in picked.values())
    return {"hi": round(hi, 4), "lo": round(lo, 4),
            "width": round(hi - lo, 4)}


def box_cap(em_x):
    """SPEC section 7's setup arithmetic: EM 60 -> cap 12."""
    return BOX_MAX_FRAC * float(em_x)


def break_min(em_x):
    """SPEC section 7: EM 60 -> break distance 3."""
    return BREAK_MIN_FRAC * float(em_x)


def box_ok(box, em_x):
    """The width gate (RD-6): width <= 0.2 x that ticker's
    own EM. A wider box is no trade — the 2026-10-20 lesson,
    where the gate rejected an all-morning uptrend."""
    if not box or float(em_x) <= 0:
        return False
    return float(box["width"]) <= box_cap(em_x)


def next_line(lines, price, direction):
    """The next map line strictly beyond `price` in
    `direction` — the Break's target (and the room gate's
    measuring point). Returns (name, level) or None when
    price is already beyond the wall on that side."""
    p = float(price)
    if direction > 0:
        cands = [(lines[k], k) for k in LINE_ORDER
                 if lines[k] > p]
        if not cands:
            return None
        level, name = min(cands)
        return name, level
    cands = [(lines[k], k) for k in LINE_ORDER if lines[k] < p]
    if not cands:
        return None
    level, name = max(cands)
    return name, level


def _in_entry_window(close_dt, session_d):
    return close_dt.date() == session_d \
        and WINDOW_START <= close_dt.time() <= LAST_ENTRY_CLOSE


def find_break(spy_bars, qqq_bars, box_spy, box_qqq,
               em_spy, em_qqq, lines, session_d,
               room_min_anchor):
    """The Three-Ticker Break scan (SPEC section 3.3) over
    COMPLETED 5m bars (the caller filters completion; bars
    carry their close time under "close_dt"). The SPX leg is
    the SPY leg on this desk (the map ticker stands in for
    SPX, RD-6 mechanics on desk instruments), so the joint
    condition is SPY and QQQ closing beyond their own boxes,
    by >= 0.05 x their own EM, on the same bar, in the same
    direction, on a bar closing inside 09:50-11:05.

    The FIRST bar satisfying the joint break is the signal.
    Its room gates then decide: room (entry close to the next
    map line) must be strictly more than `room_min_anchor`
    (RD-7's 8 SPX points in anchor terms) AND at least 1R
    (entry close to the SPY box edge). A signal that fails
    its room gates is stood down, not deferred — later bars
    are the same break, older.

    Returns a verdict dict: {"state": "signal", ...} /
    {"state": "box_gate"|"stood_down_room"|"no_signal", ...}.
    """
    caps = {"SPY": box_cap(em_spy), "QQQ": box_cap(em_qqq)}
    if not box_ok(box_spy, em_spy) or not box_ok(box_qqq, em_qqq):
        return {"state": "box_gate",
                "widths": {"SPY": box_spy["width"] if box_spy
                           else None,
                           "QQQ": box_qqq["width"] if box_qqq
                           else None},
                "caps": caps}
    qqq_by_start = {b["t"]: b for b in qqq_bars or []}
    for bar in spy_bars or []:
        close_dt = bar["close_dt"]
        if not _in_entry_window(close_dt, session_d):
            continue
        qb = qqq_by_start.get(bar["t"])
        if qb is None:
            continue          # no same-bar confirmation leg
        for d in (1, -1):
            if d > 0:
                s_beyond = float(bar["close"]) - box_spy["hi"]
                q_beyond = float(qb["close"]) - box_qqq["hi"]
                edge = box_spy["hi"]
            else:
                s_beyond = box_spy["lo"] - float(bar["close"])
                q_beyond = box_qqq["lo"] - float(qb["close"])
                edge = box_spy["lo"]
            if s_beyond < break_min(em_spy) \
                    or q_beyond < break_min(em_qqq):
                continue
            entry_close = float(bar["close"])
            one_r = abs(entry_close - edge)
            nl = next_line(lines, entry_close, d)
            room = (abs(nl[1] - entry_close) if nl else 0.0)
            facts = {"bar_start": bar["t"], "close_dt": close_dt,
                     "direction": d, "entry_close": entry_close,
                     "box_edge": edge, "one_r": round(one_r, 4),
                     "target_name": nl[0] if nl else None,
                     "target": nl[1] if nl else None,
                     "room": round(room, 4)}
            if nl is None or room <= room_min_anchor \
                    or room < one_r:
                return dict(facts, state="stood_down_room")
            return dict(facts, state="signal")
    return {"state": "no_signal"}


def find_fade(spy_bars, lines, one_r_points, session_d):
    """The FADE-mode edge fade (SPEC section 3.4, RD-10): the
    first bar closing inside the entry window whose RANGE
    reaches a wall emits the fade candidate — direction
    toward the magnet, target the magnet, stop a completed
    5m close beyond the entry wall by the pre-written session
    1R against the fade (DC-3; the source names no fade stop).

    Touches are counted only on bars closing inside the entry
    window (DC-6): a pre-09:50 touch that has retraced by
    09:50 is not an entry, and a bar touching BOTH walls is
    ambiguous and stands the fade down for the day.
    """
    wall_up = float(lines["WALL_UP"])
    wall_dn = float(lines["WALL_DN"])
    magnet = float(lines["MAGNET"])
    for bar in spy_bars or []:
        close_dt = bar["close_dt"]
        if not _in_entry_window(close_dt, session_d):
            continue
        up = float(bar["high"]) >= wall_up
        dn = float(bar["low"]) <= wall_dn
        if up and dn:
            return {"state": "stood_down_ambiguous",
                    "bar_start": bar["t"], "close_dt": close_dt}
        if not (up or dn):
            continue
        if up:
            d, line = -1, wall_up
            breached = float(bar["close"]) > line + one_r_points
        else:
            d, line = 1, wall_dn
            breached = float(bar["close"]) < line - one_r_points
        facts = {"bar_start": bar["t"], "close_dt": close_dt,
                 "direction": d, "entry_line": line,
                 "target": magnet, "one_r": float(one_r_points)}
        if breached:
            return dict(facts, state="stood_down_stop_breached")
        return dict(facts, state="signal")
    return {"state": "no_signal"}


def break_exit(bars_after, direction, box, target_level):
    """The Break's exits over completed bars strictly after
    the fill, in bar order — first decider wins (SPEC section
    3.3): target touch (the bar's range reaches the target
    line) or stop (a completed 5m close back inside the SPY
    box). Within one bar the target is checked first (DC-5:
    the level was reached before the close printed). Returns
    (rule, bar) or None."""
    for bar in bars_after or []:
        if direction > 0:
            if float(bar["high"]) >= float(target_level):
                return "target", bar
            if float(bar["close"]) <= float(box["hi"]):
                return "stop_box", bar
        else:
            if float(bar["low"]) <= float(target_level):
                return "target", bar
            if float(bar["close"]) >= float(box["lo"]):
                return "stop_box", bar
    return None


def fade_exit(bars_after, direction, entry_line, magnet,
              one_r_points):
    """The fade's exits over completed bars strictly after
    the fill, in bar order — first decider wins: target touch
    (the bar's range reaches the magnet) or stop (a completed
    5m close beyond the entry wall by the session 1R against
    the fade, DC-3). Within one bar the stop close is checked
    first (DC-5: the close is the bar's final truth).
    Returns (rule, bar) or None."""
    for bar in bars_after or []:
        if direction > 0:      # long fade from WALL_DN
            if float(bar["close"]) < float(entry_line) \
                    - float(one_r_points):
                return "stop_1r", bar
            if float(bar["high"]) >= float(magnet):
                return "target", bar
        else:                  # short fade from WALL_UP
            if float(bar["close"]) > float(entry_line) \
                    + float(one_r_points):
                return "stop_1r", bar
            if float(bar["low"]) <= float(magnet):
                return "target", bar
    return None


def oi_shortlist(oi_by_strike, spot):
    """RD-9: the second-wall layer from per-strike open
    interest {strike: {"call", "put", "total"}} (anchor
    terms). Top-3 strikes by TOTAL OI above and below spot,
    plus ceiling (argmax call OI above spot) and floor
    (argmax put OI below spot); ties break to the strike
    nearest spot. Pure; empty input files as empty lists."""
    rows = []
    for strike, v in (oi_by_strike or {}).items():
        try:
            s = float(strike)
            rows.append((s, float(v.get("call") or 0),
                         float(v.get("put") or 0),
                         float(v.get("total") or 0)))
        except (TypeError, ValueError, AttributeError):
            continue
    above = sorted((r for r in rows if r[0] > spot),
                   key=lambda r: (-r[3], abs(r[0] - spot)))
    below = sorted((r for r in rows if r[0] < spot),
                   key=lambda r: (-r[3], abs(r[0] - spot)))
    ceil_rows = [r for r in rows if r[0] > spot]
    floor_rows = [r for r in rows if r[0] < spot]
    ceiling = max(ceil_rows, key=lambda r: (r[1], -abs(r[0] - spot)),
                  default=None)
    floor = max(floor_rows, key=lambda r: (r[2], -abs(r[0] - spot)),
                default=None)
    return {
        "above": [{"strike": r[0], "total_oi": r[3]}
                  for r in above[:3]],
        "below": [{"strike": r[0], "total_oi": r[3]}
                  for r in below[:3]],
        "ceiling": ({"strike": ceiling[0], "call_oi": ceiling[1]}
                    if ceiling else None),
        "floor": ({"strike": floor[0], "put_oi": floor[1]}
                  if floor else None),
    }


def line_agreement(lines, shortlist, tol_anchor):
    """RD-8: the map is cross-checked against the OI
    shortlist — a shortlist strike within `tol_anchor` of a
    map line (5 SPX points in anchor terms, DC-1) is an
    agreement. State exposure only (SPEC section 3.5's spirit
    on the OI layer): filed, never a trade gate. Returns the
    list of {line, level, strike, gap} agreements."""
    strikes = set()
    for side in ("above", "below"):
        for row in (shortlist or {}).get(side) or []:
            strikes.add(float(row["strike"]))
    for key in ("ceiling", "floor"):
        row = (shortlist or {}).get(key)
        if row:
            strikes.add(float(row["strike"]))
    out = []
    for name in LINE_ORDER:
        level = float(lines[name])
        for s in sorted(strikes):
            gap = abs(s - level)
            if gap <= tol_anchor:
                out.append({"line": name, "level": level,
                            "strike": s, "gap": round(gap, 4)})
    return out
