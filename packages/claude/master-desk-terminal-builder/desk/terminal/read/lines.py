"""Lines a chart reader draws beyond the read's horizontal levels, ported from the study's tested, point-in-time
detectors (scratch lab/src/structure_build.py; its columns in lab/structure.md; PATTERNS.md 2l), each read at the last
completed session from bars through it only:

  trendlines   a straight line through two confirmed minor swing lows (support) or highs (resistance) of the last
               250 sessions that no low (high) between them pokes through (Edwards & Magee); broken by a close more than
               0.25 ATR beyond it, dropped if broken before its second swing was confirmed; its touches are separate
               episodes, five sessions or more apart, of a low (high) within 0.25 ATR of it
  value area   the volume profile of the last 60 and 250 sessions, built as the read's levels.poc builds its own (each
               session's volume spread evenly over the half-ATR bins its range covers): the point of control and the
               70% of volume around it (Steidlmayer), said beside the six-month point of control the levels hold
  structure    the minor swings' state from the long's side: an uptrend's higher highs and higher lows intact, a lower
               high as a warning, broken once a close goes under the last higher low

The swings are the read's own (pivots.zigzag at core.MINOR_K and MAJOR_K), each with the session that confirmed it.

How each reading votes, and why no stretch of bars is voted twice:
  - a trendline votes (Levels) only on its own events: a break, a held test of a rising support line, a falling
    resistance line turning price back. It is context when its value at the last session sits within the read's merge
    radius (levels.MERGE_ATR) of a swing it runs through, where the horizontal levels already hold that price, and when
    a flag or triangle the patterns read is drawn on the same swings;
  - the structure state votes (Trend) only where trend.swings reads the same swings as sideways and votes nothing:
    wherever trend.swings votes, the state is context beside it, so the swings vote once;
  - the value area is context: the levels' areas already vote where the close sits against support and resistance.
    Joined to the level set instead (kind "volume"), its six lines changed 29 of 196 plan forms and 22 takes on the
    2026-10-16 roster sample, with no study support (PATTERNS.md 2l: more kinds stacked at support, IC -0.011)

A sloped line is no floor or ceiling for a plan: a plan's zone, out and target are fixed prices the record scores until
its time stop, while a line moves every session. The study's nearest live line moves a median 0.05 ATR a session: half
an ATR by a plan's median 9 sessions to target and about an ATR by its median 18-session time stop (the 2026-10-16
sample), against an out set 0.25 ATR under its line and a zone 0.3 to 1 ATR deep, so a zone, out or target set at the
line's value at the last session would soon name a line it no longer sits at. The readings use that value for their
distance only, and the close that proves a reading against the long wrong is the line at the next session, said so.
Prices stay internal: sentences speak in % from the close and ATR."""
import numpy as np

from . import levels, patterns, pivots, words
from .core import MINOR_K, Fact, atr_words, pct
from .geometry import point, seg

LOOKBACK = levels.LOOKBACK   # 250 sessions: the read's level lookback, the study's line window (structure_build)
TOUCH = 0.25    # ATR: a low (high) this close to a line touches it. Ported unchanged from the study's detector
                # (structure_build.TOUCH), equal to the read's own touch band for an average (structure._averages).
                # The study tested the detector with this band and no other: the data has not chosen the value
BREAK = 0.25    # ATR: a close this far through a line breaks it (structure_build.BREAK), equal to the read's failure
                # band for a breakout level (levels.retested). Not chosen by data, as TOUCH
FRESH = 5       # sessions: touch episodes this far apart are separate, and a break or a touch this recent is the
                # line's news (structure_build.FRESH), equal to the spacing at which the read's levels.Area counts
                # separate tests. Not chosen by data, as TOUCH
MIN_TOUCH = 3   # touches that make a drawn line a trendline: two swings draw it, a third touch tests it (Edwards &
                # Magee; the read's levels count a level as tested once price came back to it). The data cannot set it:
                # on 197 roster names x 10 dates the study's nearest support line had 3+ touches on 47.6% of real
                # charts, 47.8% of the same sessions shuffled and 30.8% of Gaussian walks; 4+: 14.3%, 14.6%, 8.0%;
                # 5+: 2.9%, 4.0%, 2.3%; 6+: 0.8%, 0.8%, 0.5%. No count separates real charts from shuffled sessions,
                # so the textbook's count stands, and the rate it fires at on noise is stated in the tests
VA_SHARE = 0.70  # the value area's share of volume: Steidlmayer's definition (the study's VA_SHARE), not chosen by data
PROFILES = (60, 250)    # the brief's windows (SCOPE row 12): the study's st_vp60_* and st_vp250_*
MAX_BINS = 4000  # half-ATR bins: a profile wider than 2,000 ATR is a degenerate series (structure_build.MAX_BINS)
AT_CLOSE = 0.1      # ATR: a line this near the close is "at the close", the read's words for it (structure._atr)
PATTERN_SPAN = 60   # sessions: patterns._triangle reads the swings of the last 60 sessions
FLAG_SPAN = 22      # sessions: patterns._flag's pole top lies within the last 22 sessions, its drift after it
BIG = 1 << 40

# strengths and rarities. The study cannot set them: none of these readings holds alone against the next 1 to 60
# sessions (PATTERNS.md 2l), and the read is never tuned on outcomes (MODEL.md 8: the forward ledger calibrates). Each
# takes the strength and rarity the read already gives its nearest relative, so a line counts as much as that relative.
# A rarity only ranks standouts until the session's roster shares are known; the roster's shares replace it
# (call._salience)
S_BREAK, R_BREAK = 0.35, 0.35    # a close through a line: levels.reclaim50, the read's close through the 50-day
S_HELD, R_HELD = 0.4, 0.4        # a held test of a rising line: levels.bounce50, the held test of the rising 50-day
S_TURNED, R_TURNED = 0.35, 0.35  # turned back under a falling line: levels.ceiling's strength within an ATR; the read
                                 # has no rarity for a turn, so it takes the break's, the same line's other event
S_WARN, R_WARN = 0.25, 0.2       # a lower high: one of the two swings trend.swings reads turned, half its 0.5; the
                                 # rarity of its swings_down reading
S_BROKEN, R_BROKEN = 0.5, 0.45   # a close under the last higher low: trend.swings' own strength and rarity for it
# Votes wait for evidence (the owner's rule, 2026-10-19: nothing arbitrary). The strengths above are borrowed from the
# nearest relatives, not measured; the events fire about as often on shuffled sessions as on real charts (a 3-touch
# line exists on 89% of random walks; support and resistance breaks fire 4.1% and 9.7% on both; the structure state
# breaks on 10.7% real against 11.7% shuffled). Until a study shows an event predicts, it is read and shown as context
# and votes nothing; setting a flag restores its vote exactly as built (tests/test_read_structure.py proves both).
TRENDLINE_VOTES = False
STRUCTURE_VOTES = False
LISTED = 0.3    # a context reading against the long at this strength is listed with what argues against it
                # (call.against lists from 0.3) and votes nothing: a broken structure price has climbed back over

words.GLOSSARY.update({
    "trendline": ("Trendline", "A straight line through two swing lows (or two swing highs) that price has come back "
                               "to and respected since; a daily close a quarter of a day's range through it breaks "
                               "it."),
    "value_area": ("Value area", "The price range where 70% of a period's volume traded, around its most-traded "
                                 "price (the point of control)."),
    "structure": ("Swing structure", "An uptrend steps up in higher highs and higher lows; a lower high is the first "
                                     "warning, and losing the last higher low breaks it."),
})
_MAJOR_SHORT = {"intact": "intact", "warning": "a lower high", "broken": "broken", "sideways": "sideways",
                "none": "no higher low"}            # the sheet's words for the larger swings (the text has _MAJOR's)
_MAJOR = {"intact": "are intact", "warning": "show a lower high", "broken": "are broken", "sideways": "are sideways",
          "none": "have no higher low"}


def swings(x, k=MINOR_K):
    """the read's confirmed swings at k ATR with the session that confirmed each: [(i, price, kind, conf)], oldest
    first. The walk is pivots.zigzag's, step for step (a test holds the two equal); it also keeps the session of the
    price event that confirmed each swing, the first session at which the swing is known"""
    bars, atrs = x.bars, x.atrs
    start = next((i for i, a in enumerate(atrs) if a), None)
    if not bars or start is None:
        return []
    out = []
    d = 0
    hi = lo = hi_i = lo_i = None
    opp = opp_i = None
    for i, px, kind in pivots._events(bars, start):
        thr = k * atrs[i]
        if d == 0:
            if hi is None or (kind == "h" and px > hi):
                hi, hi_i = (px, i) if kind == "h" else (float(bars[i]["h"]), i)
            if lo is None or (kind == "l" and px < lo):
                lo, lo_i = (px, i) if kind == "l" else (float(bars[i]["l"]), i)
            if kind == "l" and hi - px >= thr:
                out.append((hi_i, hi, "H", i))
                d, lo, lo_i, opp, opp_i = -1, px, i, None, None
            elif kind == "h" and px - lo >= thr:
                out.append((lo_i, lo, "L", i))
                d, hi, hi_i, opp, opp_i = 1, px, i, None, None
            continue
        if d == 1:
            if kind == "h":
                if px > hi:
                    hi, hi_i, opp, opp_i = px, i, None, None
                continue
            if opp is None or px < opp:
                opp, opp_i = px, i
            last_lo = out[-1][1] if out else None
            if hi - opp >= thr or (last_lo is not None and opp < last_lo):
                out.append((hi_i, hi, "H", i))
                d, lo, lo_i, opp, opp_i = -1, opp, opp_i, None, None
        else:
            if kind == "l":
                if px < lo:
                    lo, lo_i, opp, opp_i = px, i, None, None
                continue
            if opp is None or px > opp:
                opp, opp_i = px, i
            last_hi = out[-1][1] if out else None
            if opp - lo >= thr or (last_hi is not None and opp > last_hi):
                out.append((lo_i, lo, "L", i))
                d, hi, hi_i, opp, opp_i = 1, opp, opp_i, None, None
    return out


def _arrays(x):
    nan = float("nan")
    return (np.array([float(b["l"]) for b in x.bars]), np.array([float(b["h"]) for b in x.bars]),
            np.array(x.c, dtype=float), np.array([nan if a is None else float(a) for a in x.atrs]))


def trendlines(x, piv=None, support=True, arrays=None):
    """every live line at the last session through two confirmed swing lows (support) or highs (resistance) whose
    first swing lies in the last LOOKBACK sessions, as dicts: the anchors, the slope (price a session), the line's value
    at the last session and the next, its distance from the close (ATR), its touches, the session that broke it (None
    while unbroken), its last touching session and the swings it runs through. Live: unbroken, or broken in the last
    FRESH sessions. The study's structure_build.trendlines at one session (a test holds the two equal)"""
    n = x.n
    piv = swings(x) if piv is None else piv
    lo_i = max(0, n - LOOKBACK)
    want = "L" if support else "H"
    pts = [(i, p, cf) for i, p, kd, cf in piv if kd == want and i >= lo_i]
    if len(pts) < 2 or not x.atr:
        return []
    L, H, C, A = arrays or _arrays(x)
    I = np.array([q[0] for q in pts])
    P = np.array([q[1] for q in pts])
    CF = np.array([q[2] for q in pts])
    a, b = np.triu_indices(len(pts), 1)
    keep = I[b] > I[a]
    a, b = a[keep], b[keep]
    if not len(a):
        return []
    ia, ib, pa, pb, cb = I[a], I[b], P[a], P[b], CF[b]
    slope = (pb - pa) / (ib - ia)
    T = np.arange(lo_i, n)
    E, Ct, At = (L if support else H)[lo_i:], C[lo_i:], A[lo_i:]
    line = pa[:, None] + slope[:, None] * (T[None, :] - ia[:, None])
    tol = 1e-9 * np.abs(line)
    between = (T[None, :] > ia[:, None]) & (T[None, :] < ib[:, None])
    after = T[None, :] > ib[:, None]
    with np.errstate(invalid="ignore"):
        if support:
            viol = between & (E[None, :] < line - tol)
            bm = after & (Ct[None, :] < line - BREAK * At[None, :])
            near = E[None, :] <= line + TOUCH * At[None, :]
        else:
            viol = between & (E[None, :] > line + tol)
            bm = after & (Ct[None, :] > line + BREAK * At[None, :])
            near = E[None, :] >= line - TOUCH * At[None, :]
    hb = bm.any(1)
    bk = np.where(hb, T[np.argmax(bm, 1)], BIG)
    ok = ~viol.any(1) & (bk > cb) & (bk >= n - FRESH)    # known before any break, and live
    if not ok.any():
        return []
    touch = near & (T[None, :] >= ia[:, None]) & (T[None, :] < bk[:, None])
    prev = np.zeros_like(touch)
    for s in range(1, FRESH):
        prev[:, s:] |= touch[:, :-s]
    eps = (touch & ~prev).sum(1)
    width = touch.shape[1]
    last = np.where(touch.any(1), T[width - 1 - np.argmax(touch[:, ::-1], 1)], -1)
    d = n - 1
    out = []
    for j in np.flatnonzero(ok):
        at = pa[j] + slope[j] * (d - ia[j])
        on = [(int(i), float(p)) for i, p in zip(I, P) if touch[j, i - lo_i]]   # the swings it runs through
        out.append({"ia": int(ia[j]), "ib": int(ib[j]), "pa": float(pa[j]), "pb": float(pb[j]),
                    "slope": float(slope[j]), "at": float(at), "next": float(at + slope[j]),
                    "dist": (at - x.close) / x.atr, "touches": int(eps[j]),
                    "broke": None if bk[j] >= BIG else int(bk[j]), "last_touch": int(last[j]),
                    "swings": on, "support": support})
    return out


def nearest(x, piv=None, support=True, arrays=None, min_touch=0):
    """the live line nearest the close among those with at least `min_touch` touches, or None; min_touch 0 gives the
    study's own st_tls / st_tlr line"""
    ls = [q for q in trendlines(x, piv, support, arrays) if q["touches"] >= min_touch and np.isfinite(q["dist"])]
    return min(ls, key=lambda q: abs(q["dist"])) if ls else None


def _own_line(x, q):
    """the pattern a flag or triangle drawn on the same swings makes of this line, or None (the rule call.reconcile
    keeps for the swings inside a flag: one stretch of bars is read once, as the pattern)"""
    if q["ia"] < x.n - PATTERN_SPAN:
        return None
    for f in patterns._triangle(x):
        if (f.side > 0) == q["support"]:      # its sloped side: an ascending triangle's lows, a descending one's highs
            return "the triangle's"
    if q["ia"] >= x.n - FLAG_SPAN and patterns._flag(x):
        return "the flag's"
    return None


def _trend_facts(x, piv, arrays):
    out = []
    for support in (True, False):
        q = nearest(x, piv, support, arrays, MIN_TOUCH)
        if q is None:
            continue
        key = "levels.support_line" if support else "levels.resistance_line"
        what = "support" if support else "resistance"
        rising = q["slope"] > 0
        tilt = "rising" if rising else "falling"
        name = f"{tilt} {what} line"
        c, at, nxt = x.close, q["at"], q["next"]
        d_pct = x.pct_of(at)
        per = abs(q["slope"]) / c * 100.0
        move = (f"{'rises' if rising else 'falls'} about {pct(per, 2).lstrip('+−')} a session" if round(per, 2)
                else "is all but flat")
        drawn = (f"the {name} through the {x.when(q['ia'])} and {x.when(q['ib'])} "
                 f"{'lows' if support else 'highs'} ({q['touches']} touches)")
        where = f"the line sits {pct(d_pct)} from the close ({atr_words(q['dist'])}) and {move}"
        side, strength, rarity, head, clause, wrong = 0, 0.0, 0.0, "", "", None
        reading = f"{what.capitalize()} line: {tilt}, {pct(d_pct)}, {q['touches']} touches since {x.when(q['ia'])}"
        if q["broke"] is not None:
            back = (c > at) if support else (c < at)                # closed back through it since: no break held
            head = f"Broke {'its' if support else 'above its'} {name}" + (", then closed back" if back else "")
            text = (f"{x.on(q['broke'], cap=True)} it closed {'under' if support else 'over'} {drawn}"
                    + ("; it has closed back since, so the break has not held" if back else "") + f": {where}.")
            reading = f"{what.capitalize()} line: broken {x.on(q['broke'])} ({tilt}, {q['touches']} touches)" + \
                (", closed back since" if back else "")
            if not back:
                side, strength, rarity = (-1 if support else 1), S_BREAK, R_BREAK
                clause = f"it broke {'its' if support else 'above its'} {name}"
                if support and nxt > c:
                    wrong = (nxt, f"the broken {name} (its next session's level)")
        elif support and rising and q["last_touch"] >= x.n - FRESH and c >= at:
            head = f"Holding its {name}"
            text = f"{x.on(q['last_touch'], cap=True)} it touched {drawn} and held: {where}."
            reading = f"Support line: tested and held ({q['touches']} touches since {x.when(q['ia'])})"
            side, strength, rarity, clause = 1, S_HELD, R_HELD, f"it is holding its {name}"
        elif not support and not rising and q["last_touch"] >= x.n - FRESH and c <= min(at, nxt):
            head = f"Turned back at its {name}"
            text = f"{x.on(q['last_touch'], cap=True)} it touched {drawn} and closed under it: {where}."
            reading = f"Resistance line: turned price back ({q['touches']} touches since {x.when(q['ia'])})"
            side, strength, rarity, clause = -1, S_TURNED, R_TURNED, f"its {name} turned it back"
            wrong = (nxt, f"the {name} (its next session's level)")
        else:                                                       # within 0.1 ATR: "right at the close", the
            at_close = abs(q["dist"]) < AT_CLOSE                     # read's own words for it (structure._atr)
            head = f"A {name} " + ("at the close" if at_close else f"{pct(d_pct)} {'below' if at <= c else 'above'}")
            text = f"{drawn[0].upper() + drawn[1:]}: {where}."
        # one price read once: within the merge radius of a swing it runs through, the horizontal levels hold it
        i_f, p_f = min(q["swings"], key=lambda s: abs(at - s[1])) if q["swings"] else (None, None)
        flat = p_f is not None and abs(at - p_f) <= levels.MERGE_ATR * x.atr
        owner = _own_line(x, q) if side else None
        if side and (flat or owner):
            text = text.rstrip(".") + (f": {owner} line, read with the pattern." if owner else
                                       f". At this price the line runs through the {x.when(i_f)} "
                                       f"{'low' if support else 'high'}, which the levels read.")
            side, strength, rarity, clause, wrong = 0, 0.0, 0.0, "", None
        if side and not TRENDLINE_VOTES:                            # context until a study shows it predicts
            strength, rarity, clause, wrong = 0.0, 0.0, "", None
        end = q["broke"] if q["broke"] is not None else x.n - 1     # drawn from its first anchor to its break or today
        draw = [seg(x, q["ia"], q["pa"], end, q["pa"] + q["slope"] * (end - q["ia"]),
                    "Support line" if support else "Resistance line", "trendline")]
        pts = [point(x, q["ia"], "Low" if support else "High", "trendline"),
               point(x, q["ib"], "Low" if support else "High", "trendline")]
        if q["broke"] is not None:
            pts.append(point(x, q["broke"], "Line break", "trendline"))
        elif q["last_touch"] >= 0:
            pts.append(point(x, q["last_touch"], "Line touch", "trendline"))
        out.append(Fact(key, "Levels", "structure" if side and TRENDLINE_VOTES else "context", side, strength, head,
                        text, reading,
                        "trendline", rarity,
                        {"at": at, "next": nxt, "dist": q["dist"], "slope_atr": q["slope"] / x.atr,
                         "touches": q["touches"], "broke": q["broke"], "first": q["ia"], "second": q["ib"],
                         "last_touch": q["last_touch"], "flat": flat, "owner": owner, "draw": draw, "marks": pts},
                        clause, wrong))
    return out


def profile(x, w):
    """(point of control, value-area high, value-area low) of the last w sessions, or None: the read's levels.poc
    profile (each session's volume spread evenly over the half-ATR bins its range covers, bins from the window's low,
    the last session's ATR) and its value area, VA_SHARE of the volume grown from the point of control one bin at a
    time toward the heavier neighbour (ties up). Shares are counted in parts per billion so equal bins tie exactly, the
    lowest winning, as levels.poc's do (structure_build.vprofile)"""
    if x.n < w or not x.atr:
        return None
    bs = x.bars[-w:]
    wd = 0.5 * x.atr
    lo_ = np.array([float(b["l"]) for b in bs])
    hi_ = np.array([float(b["h"]) for b in bs])
    v = np.array([float(b.get("v") or 0) for b in bs])
    base = lo_.min()
    if (hi_.max() - base) / wd >= MAX_BINS - 1 or v.sum() <= 0:
        return None
    a = np.floor((lo_ - base) / wd).astype(np.int64)
    z = np.maximum(np.floor((hi_ - base) / wd).astype(np.int64), a)
    nb = int(z.max()) + 1
    share = v / (z - a + 1)
    prof = np.cumsum(np.bincount(a, share, nb + 1) - np.bincount(z + 1, share, nb + 1))[:nb]
    q = np.round(np.maximum(prof, 0.0) / v.sum() * 1e9)
    poc = int(np.argmax(q))
    lo, hi, acc, target = poc, poc, q[poc], VA_SHARE * q.sum()
    while acc < target:
        vu = q[hi + 1] if hi + 1 < nb else -1.0
        vd = q[lo - 1] if lo - 1 >= 0 else -1.0
        if vu < 0 and vd < 0:
            break
        if vu >= vd:
            hi, acc = hi + 1, acc + vu
        else:
            lo, acc = lo - 1, acc + vd
    return base + (poc + 0.5) * wd, base + (hi + 1) * wd, base + lo * wd


def _value_facts(x):
    got = {w: profile(x, w) for w in PROFILES}
    if not got[PROFILES[0]]:
        return []
    c = x.close
    span = {60: "60-day", 250: "one-year"}

    def where(p):
        return "inside" if p[2] <= c <= p[1] else "above" if c > p[1] else "below"
    bits, data, short = [], {}, []
    for w, p in got.items():
        if not p:
            continue
        poc, vah, val = p
        bits.append(f"the {span[w]} value area runs from {pct(x.pct_of(val))} to {pct(x.pct_of(vah))}, its most-traded "
                    f"price at {pct(x.pct_of(poc))}, and the close sits {where(p)} it")
        short.append(f"{span[w]} {pct(x.pct_of(val))} to {pct(x.pct_of(vah))} (most traded {pct(x.pct_of(poc))}, "
                     f"close {where(p)})")
        data[w] = {"poc": poc, "vah": vah, "val": val, "where": where(p)}
    head = f"{where(got[PROFILES[0]]).capitalize()} its 60-day value area"
    return [Fact("levels.value_area", "Levels", "context", 0, 0.0, head,
                 "Where 70% of the volume traded: " + "; ".join(bits) + ".", "Value area: " + "; ".join(short),
                 "value_area", 0.0, data)]


def state(piv, closes):
    """the swing structure from the long's side on confirmed swings [(i, price, kind)] and the closes: (state,
    details), state 'intact' (higher highs and higher lows, no close under the last higher low since it formed),
    'warning' (that low holds, but the last swing high came in under the one before it, which had topped its own
    predecessor: the study's lhwarn), 'broken' (a close under the last higher low since it formed: the study's intact
    flag off), 'sideways' (the higher low holds, the highs have not stepped up), 'none' (no confirmed low above the one
    before it), or None with fewer than two swing highs and lows. The study's st_mn_* and st_mj_* at the last session"""
    hs = [(i, p) for i, p, k in piv if k == "H"]
    ls = [(i, p) for i, p, k in piv if k == "L"]
    if len(hs) < 2 or len(ls) < 2:
        return None, {}
    hl = next((ls[j] for j in range(len(ls) - 1, 0, -1) if ls[j][1] > ls[j - 1][1]), None)
    broke = next((t for t in range(hl[0] + 1, len(closes)) if closes[t] < hl[1]), None) if hl else None
    lh = (hs[-1], hs[-2]) if len(hs) >= 3 and hs[-1][1] < hs[-2][1] > hs[-3][1] else None
    up = hs[-1][1] > hs[-2][1] and ls[-1][1] > ls[-2][1]
    det = {"hl": hl, "broke": broke, "lh": lh, "up": up}
    if hl is None:
        return "none", det
    if broke is not None:
        return "broken", det
    if lh:
        return "warning", det
    return ("intact" if up else "sideways"), det


def swings_side(x):
    """the side trend.swings reads on this chart, as trend.facts computes it (None when it reads nothing): the
    structure state votes only where this is 0 (a test holds the two equal)"""
    st = pivots.structure(x.minor)
    conf = [p for p in x.minor if p.confirmed]
    last_l = next((p for p in reversed(conf) if p.kind == "L"), None)
    last_h = next((p for p in reversed(conf) if p.kind == "H"), None)
    if st == "up" and last_l and x.close < last_l.price:
        return -1
    if st == "down" and last_h and x.close > last_h.price:
        return 1
    return {"up": 1, "down": -1, "range": 0}.get(st)


def _structure_facts(x):
    s, det = state([(p.i, p.price, p.kind) for p in x.minor if p.confirmed], x.c)
    if s is None:
        return []
    ts = swings_side(x)
    major, _ = state([(p.i, p.price, p.kind) for p in x.major if p.confirmed], x.c)
    c = x.close
    hl, broke, lh = det["hl"], det["broke"], det["lh"]
    data = {"state": s, "major": major, "swings_side": ts, "hl": hl[1] if hl else None, "broke": broke,
            "lower_high": lh[0][1] if lh else None}
    side, strength, rarity, clause, wrong, listed = 0, 0.0, 0.0, "", None, 0.0
    if s == "intact":
        head = "Uptrend structure intact"
        text = (f"Its swings step up in higher highs and higher lows, and no close has gone under the {x.when(hl[0])} "
                "higher low since it formed.")
        reading = f"Structure: intact (the {x.when(hl[0])} higher low holds)"
        side = 1
    elif s == "warning":
        (i3, p3), (i2, _) = lh
        cleared = c >= p3
        head = "A lower high in the swings" + (", since cleared" if cleared else "")
        text = (f"The {x.when(i3)} swing high came in under the {x.when(i2)} high, which had topped the one before it: "
                f"a lower high, the first warning in an uptrend's steps, while the {x.when(hl[0])} higher low holds"
                + (f"; price has since closed over the {x.when(i3)} high." if cleared else "."))
        reading = f"Structure: a lower high (the {x.when(i3)} high), the {x.when(hl[0])} higher low holding"
        side = -1
        if not cleared:
            strength, rarity = S_WARN, R_WARN
            clause = "its last swing high came in lower, the first warning in its steps"
            wrong = (p3, f"the {x.when(i3)} lower high")
    elif s == "broken":
        back = c >= hl[1]
        head = "Uptrend structure broken" + (", then reclaimed" if back else "")
        text = (f"{x.on(broke, cap=True)} it closed under the {x.when(hl[0])} higher low, ending the run of higher "
                "lows" + (", and it has closed back over that low since." if back else "."))
        reading = (f"Structure: broken {x.on(broke)} (under the {x.when(hl[0])} higher low)"
                   + (", back over it since" if back else ""))
        side = -1
        if back:
            listed = LISTED if ts is not None and ts >= 0 else 0.0
        else:
            strength, rarity = S_BROKEN, R_BROKEN
            clause = f"it closed under its {x.when(hl[0])} higher low, breaking the run of higher lows"
            wrong = (hl[1], f"the {x.when(hl[0])} higher low")
    elif s == "sideways":
        head = "Swing structure sideways"
        text = (f"The {x.when(hl[0])} higher low holds, but the swing highs have not stepped up with it: no uptrend's "
                "steps to keep or break.")
        reading = f"Structure: sideways (the {x.when(hl[0])} higher low holds)"
    else:
        head = "No higher low in the swings"
        text = "Each confirmed swing low has come in under the one before it: no uptrend step to hold."
        reading = "Structure: no higher low"
        side = -1
    if major and major != s:
        text = text.rstrip(".") + f"; the larger swings (4 ATR) {_MAJOR[major]}."
        reading += f", larger swings: {_MAJOR_SHORT[major]}"
    votes = STRUCTURE_VOTES and strength > 0 and ts == 0   # trend.swings reads these swings as sideways and votes
                                                          # nothing on them
    if votes and any(f.side == -side for f in patterns._flag(x)):
        votes = False                      # a flag's drift is the flag (call.reconcile's rule for the swings)
        text = text.rstrip(".") + ": the flag's drift."
    if not votes:
        strength, rarity, clause, wrong = listed, 0.0, "", None
    return [Fact("trend.structure", "Trend", "structure" if votes else "context", side, strength, head, text, reading,
                 "structure", rarity, data, clause, wrong)]


def facts(x):
    if x.n < 60 or not x.atr:
        return []
    arrays = _arrays(x)
    return _trend_facts(x, swings(x), arrays) + _value_facts(x) + _structure_facts(x)
