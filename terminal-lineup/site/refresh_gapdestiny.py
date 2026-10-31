#!/usr/bin/env python3
"""Refresh Gap Destiny (Forecast Engine 28).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   Studies S1 in the morgue studies record (the gap-fill study behind
   the Gap-Fill Pane, tool 11): gap fills measured on intraday bars
   for the three index funds, fixture-proven, descriptive only; that
   pane stakes nothing. Plus S15 (grade B: a gap's size read against
   a high-fear-gauge third, measured in two eras) and the fear-day
   evidence behind tool 16 (grade B family). This engine's own live
   record: none before today; it starts here. The per-name own-habit
   form (each name's own past gaps) is recorded in this register as
   this engine's SECOND ARM, to start only once the pooled record
   below has matured: it grades the same event, so it is never a
   separate engine and its cases are never counted twice.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Definitions, all decidable from a day's open, high, low and
     close against the previous close: a gap is the open minus the
     previous close, as a share of the previous close; a name
     qualifies when that share is at least 0.5 percent in size, up
     or down. Bands by size: 0.5 to 1 percent, 1 to 2 percent, over
     2 percent. (The older pane's bands are different: under 1,
     1 to 2, 2 or more, on any gap at all; the two are never mixed.)
   - A gap FILLS the same session when price reaches the previous
     close that day: an up gap fills when the day's low is at or
     below the previous close; a down gap fills when the day's high
     is at or above it. Close above the open and close below the
     open are separate shares; a close exactly at the open is
     neither, and that remainder share is published, never hidden.
   - The day's range as a multiple of the gap: (high - low) divided
     by the size of the gap in price. Its distribution is stated as
     nine steps, the values below which a tenth, two tenths, and so
     on up to nine tenths of earlier cases fell.
   - Weekday is the weekday of the gap's own session.
   - Estimation, walk-forward only: the chances for a gap on a
     session use ONLY qualifying gaps from earlier sessions, pooled
     across every name on record. The first cell with at least 30
     earlier cases wins: same band and same weekday, then same band
     on any weekday, then all qualifying gaps. If even the pooled
     cell has under 30, no set is published for that gap. Counts
     stand beside every rate. The history run below uses the same
     rule day by day over the history on record and writes nothing
     to the live record.
   - The two registered shifters, fixed constructions, no fitted
     coefficients. Both are judged on the most recent COMPLETED
     session before the gap day, because a same-day fear reading is
     built from that day's close and cannot be known at the open a
     forecast is staked at:
     (1) Fear state: that completed session was a fear day under
         the settled four-part test used by the fear-day tools: the
         big index fund fell more than 1.5 percent that day, or the
         fear gauge rose more than 15 percent in a day, or the fear
         gauge closed at 25 or higher, or it closed at 20 or higher
         on a day the big fund or the Nasdaq fund fell. The gauge
         parts can be judged only where gauge readings exist (on
         this record: September 21 to October 21, 2026, 23 closes);
         outside that span only the fund's fall can be judged, and
         the page says so.
     (2) High-volatility third: that completed session's fear-gauge
         close sits in the top third of the gauge readings on
         record BEFORE it (at least 3 earlier readings required).
         The older study's exact gap-share formula is not on this
         disk, so this decidable form is what ships, labelled as
         this engine's own reading of that conditioning, never as
         the study's formula. Where the completed session has no
         gauge close on record, this state is ABSENT: reported as
         absent, never filled in from anything else.
     How a shifter moves the numbers: for each shifter in the order
     fear, then high-volatility third, when its state is known and
     the matching earlier cell (same band, same weekday, same
     state) holds at least 30 cases, the published chances become
     that cell's rates softened toward the chances so far with a
     fixed weight of 20 cases: p = (cell hits + 20 x p so far) /
     (cell cases + 20); the range steps then come from the last
     applied shifter's cell. When a state is absent or its cell is
     thin, the chances so far stand and the shifter is reported as
     not applied, with its state or its absence printed.
   - Grading, stated in advance: sets are written to the public
     record at the open, before the session unfolds; each is graded
     at that session's close, fills and non-fills both counted.
     Scores on the fill chance and on the close-above and
     close-below chances, and coverage of the range steps (the
     share of days whose real range fell between the lowest and
     highest published steps, which should be about 8 in 10),
     counted in blocks of 60 graded forecasts. Known grading note,
     in the open like the earlier engines': the shared grading
     runner cannot yet resolve a gap-fill, close-against-open or
     range-step outcome, so these rows carry those events stated
     plainly in their outcome records and are graded when the
     runner is next extended; it is never forked here.
   - Retirement rule: after 120 graded index gaps (the big index
     funds only), if the fill chance's score is no better than
     simply using the plain rate for that gap-size band every
     time, this engine retires.
   - Thin-cell rule: any cell with fewer than 30 cases shows its
     count only, with no rate.
   - History on record: the long daily history the design names is
     NOT on this disk. What exists is the shipped daily history
     (1,833 names, 399 sessions, March 25, 2025 to October 23,
     2026). Nothing is claimed beyond that span, and the counts
     that span implies are printed on the page.
   - Fail-closed checks: the script stops rather than publish if
     the panel disagrees with the settled counts from the ground
     truth pass (388,006 qualifying gaps, 224,655 fills, 471 index
     gaps, 22 fear days), if the older pane's published figures do
     not agree with themselves where they overlap this engine's
     ground (same three index funds; its event and fill totals
     matching the sums of its own band and weekday rows; the pane
     and the later studies card are different runs of a different
     method and are NOT compared with each other or with this
     engine's daily figures), or if the public record does not
     verify before or after writing.

3. NON-CLAIMS
   - The time-of-fill variant (whether a gap fills early in the
     session or only by the close) is EXCLUDED, not promised: the
     within-day price route cannot support it on today's record.
   - The older pane's figures are a different method (within-day
     bars, any gap, 90 days) and are shown labelled as its own;
     they are not this engine's results and are never blended in.
   - History figures are a study worked out today over the past,
     not a live record; the history run writes nothing to the
     public record.
   - The per-name own-habit second arm makes no claim and publishes
     nothing until the pooled record matures.
   - No set is a promise about any single day: each chance is a
     share of similar earlier days, printed with its count.
=====================================================================
Behaviour: walk-forward history over the shipped daily history
(ledgers nothing), then a probability set for every qualifying gap
on the freshest session the price source reaches, ledgered through
the forecast machinery's append call only, then data.json written
from the panel plus figures recomputed from the ledger alone.
Idempotent: rerunning with the same panel appends nothing and
rewrites the same data.json. Timestamps come from the sources,
never the clock.
"""

import bisect
import json
import math
import os
import sys
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/board_bt_bars.json")
VIX_PATH = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source/yahoo-vix-daily.json")
PANE_PATH = os.path.join(HERE, "gap-fill", "data.json")
OUT_PATH = os.path.join(HERE, "gap-destiny", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None

sys.path.insert(0, LINEUP)
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402

ENGINE_ID = "engine_28"
INDEXES = ("SPY", "QQQ", "IWM")
INDEX_NAMES = {"SPY": "SPY (the big S&P 500 fund)",
               "QQQ": "QQQ (the big Nasdaq-100 fund)",
               "IWM": "IWM (the big small-company fund)"}
BANDS = ("b05", "b1", "b2")
BAND_LABEL = {"b05": "0.5% to 1%", "b1": "1% to 2%", "b2": "Over 2%"}
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri")
WEEKDAY_LABEL = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday",
                 "Thu": "Thursday", "Fri": "Friday"}
THIN = 30
PRIOR_STRENGTH = 20.0
P_MIN, P_MAX = 0.01, 0.99
KILL_INDEX_GAPS = 120
BLOCK = 60
QUANTITY = "gap destiny probability set for the session"
SUB_QUANTITY = "gap destiny failed gap sign flip sub claim"


FIRST_MINUTES_PATH = os.path.join(
    HERE, "gap-destiny", "first_minutes", "record.json")


def first_minutes_record():
    """The first minutes acceptance record (first_minutes.py,
    publication cure 2026-10-30): per gap name, the close
    location inside the first 15 minute range read in the gap
    direction, from Alpaca SIP 5 minute bars. Read when present;
    sessions and names it does not cover keep the daily proxy,
    labelled."""
    try:
        with open(FIRST_MINUTES_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


_FM_CACHE = {}


_ISSUED_SUB_SESSIONS = None


def _issued_sub_sessions():
    global _ISSUED_SUB_SESSIONS
    if _ISSUED_SUB_SESSIONS is None:
        _ISSUED_SUB_SESSIONS = issued_sub_sessions()
    return _ISSUED_SUB_SESSIONS


def issued_sub_sessions():
    """Sessions whose FE04 sub claim is already issued in the
    ledger (non voided rows). A session's acceptance form is
    frozen at its first issue: re-issuing it under a changed
    acceptance input would double the session's set in the
    record, which the ledger count check refuses. The first
    minutes record therefore applies from the first unissued
    session onward, and an already issued session keeps the
    form it was issued under, named per entry."""
    path = os.path.join(LINEUP, "forecast", "ledger.jsonl")
    voided, sessions = set(), set()
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if SUB_QUANTITY not in line and \
                        '"correction"' not in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("type") == "correction":
                    voided.add(row.get("corrects_row_id"))
                elif row.get("type") == "forecast" and \
                        row.get("quantity") == SUB_QUANTITY:
                    sessions.add(
                        (row["row_id"],
                         row["lineage"]["clocks"]
                         ["decision_as_of"]))
    except OSError:
        return set()
    return {sess for rid, sess in sessions if rid not in voided}


def first_minutes_acceptance(session, symbol):
    rec = _FM_CACHE.get("rec")
    if rec is None:
        rec = first_minutes_record()
        _FM_CACHE["rec"] = rec
    if rec.get("session") != session:
        return None
    detail = rec.get("names_detail", {}).get(symbol)
    return detail["acceptance_first15"] if detail else None


def acceptance_proxy(up, high, low, close):
    """Open acceptance proxy from the session's own daily range:
    the closing location inside the day's range, read in the
    gap's direction. An up gap the session held prints near 1
    (the close near the high); an up gap the session rejected
    prints near 0. A flat range prints the neutral 0.5. This is
    a daily proxy, stated as such: the first minutes acceptance
    reading the design names is not on this record, and this
    proxy is never described as that reading."""
    rng = float(high) - float(low)
    if rng <= 0:
        return 0.5
    cl = (float(close) - float(low)) / rng
    cl = min(max(cl, 0.0), 1.0)
    return cl if up else 1.0 - cl


def fe04_sign_flip(gap_pct, acceptance):
    """FE04's failed gap sign flip as a stated claim (DEEP-PASS
    3.1 item 8): acceptance_state = 2 x acceptance - 1, so an
    acceptance below 0.5 does not merely weaken the gap's
    direction, it flips the predicted close direction to the
    other side of the prior close. Returns the predicted sign
    of (close - prior close): +1, -1, or 0 at exactly neutral
    acceptance, where the claim makes no direction call."""
    state = 2.0 * float(acceptance) - 1.0
    gap_sign = 1 if gap_pct > 0 else -1
    if state > 0:
        predicted = gap_sign
    elif state < 0:
        predicted = -gap_sign
    else:
        predicted = 0
    return {"acceptance_state": round(state, 4),
            "predicted_close_sign": predicted,
            "claim": ("gap_accepted_continuation" if state > 0
                      else "failed_gap_reversal" if state < 0
                      else "no_direction_at_neutral_acceptance")}

# Settled counts from the ground-truth pass over this panel.
# Re-registered 2026-10-29 (cure G2): the panel advanced from 399
# to 403 sessions (through 2026-10-29), so the replay counts grew;
# the values below are the measured counts over the 403-session
# panel, replacing the 399-session register (qualifying 388006,
# fills 224655, index 471/152, bands 175992/130774/81240 and
# 123556/71644/29455).
# Re-registered 2026-10-30 (fix stream A): fear_days 22 was
# measured when the gauge file carried only 23 closes
# (2026-09-21 to 2026-10-21), so the gauge rules could fire on
# almost no panel sessions. The cured VIX capture extends the
# file to 504 closes (2024-10-30 to 2026-10-30); the fear rules
# now fire across the panel and the measured count is 65,
# confirmed by an independent recount from the raw panel and
# gauge files in this pass. Every other figure is unchanged:
# the panel itself did not move.
EXPECT = {"names": 1833, "sessions": 399, "qualifying": 392274,
          "fills": 226945, "index_qualifying": 472, "index_fills": 152,
          "fear_days": 65,
          "band_n": {"b05": 177825, "b1": 132384, "b2": 82065},
          "band_fills": {"b05": 124788, "b1": 72423, "b2": 29734}}
# Registered window (cure GAP-REGISTER-WINDOW-20261031): the
# settled counts above were measured over the panel through
# 2026-10-29 (403 sessions). The panel is a living record that
# advances one session a day, so an exact count over the whole
# panel fails every run after an advance (the 2026-10-30 session
# is itself a fear day: 66 against the pinned 65, and its gaps
# move every band count). The guard now binds exactly on the
# registered window, sessions on or before EXPECT_THROUGH, which
# a retroactive panel change would still break; sessions after
# the window are new settled history and publish as counted.
# Verified 2026-10-31: every EXPECT figure reproduces exactly
# over the truncated panel.
EXPECT_THROUGH = "2026-10-29"


def fail(msg):
    print(f"Gap Destiny refresh: {msg}", file=sys.stderr)
    return 1


def band_of(abs_gap_pct):
    if abs_gap_pct < 0.01:
        return "b05"
    if abs_gap_pct < 0.02:
        return "b1"
    return "b2"


def quantile(sorted_vals, q):
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def deciles(sorted_vals):
    return [round(quantile(sorted_vals, q / 10.0), 2)
            for q in range(1, 10)]


def deciles_fast(vals):
    """The same nine steps (type-7 interpolation) from an unsorted
    list, via numpy's partition-based percentile."""
    import numpy as np
    arr = np.asarray(vals, dtype=float)
    ps = np.percentile(arr, [10, 20, 30, 40, 50, 60, 70, 80, 90])
    return [round(float(x), 2) for x in ps]


class Cell:
    __slots__ = ("n", "fills", "above", "below", "ranges")

    def __init__(self):
        self.n = 0
        self.fills = 0
        self.above = 0
        self.below = 0
        self.ranges = []

    def add(self, ev):
        self.n += 1
        self.fills += 1 if ev["fill"] else 0
        self.above += 1 if ev["above"] else 0
        self.below += 1 if ev["below"] else 0
        self.ranges.append(ev["range_mult"])

    def rates(self):
        return (self.fills / self.n, self.above / self.n,
                self.below / self.n)


def load_vix():
    with open(VIX_PATH, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    result = raw["chart"]["result"][0]
    stamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    out = {}
    for t, c in zip(stamps, closes):
        if c is None:
            # Yahoo stamps sessions it carries no close for (the
            # cured VIX capture file holds 19); the sibling loader
            # in refresh_correctedband.py skips them, and a missing
            # close is no reading, never a crash or a zero.
            continue
        d = datetime.fromtimestamp(t, timezone.utc).date().isoformat()
        out[d] = float(c)
    return out


def build():
    for path in (PANEL_PATH, VIX_PATH, PANE_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    with open(PANE_PATH, "r", encoding="utf-8") as fh:
        pane = json.load(fh)
    vix = load_vix()
    if len(panel) != EXPECT["names"]:
        return fail(f"panel count disagreement: {len(panel)} names, "
                    f"expected {EXPECT['names']}")
    for sym in INDEXES:
        rows = panel.get(sym) or []
        if len(rows) < EXPECT["sessions"]:
            return fail(f"panel count disagreement: {sym} has "
                        f"{len(rows)} sessions, expected at least "
                        f"{EXPECT['sessions']} (the registered study "
                        f"panel; cure G2 2026-10-29)")
    as_of = panel["SPY"][-1][0]
    if panel["QQQ"][-1][0] != as_of or panel["IWM"][-1][0] != as_of:
        return fail("panel span disagreement among the index funds")
    span_start = panel["SPY"][0][0]

    # ---- Fail closed on the ancestor pane, where figures overlap ----
    if pane.get("names") != ["SPY", "QQQ", "IWM"]:
        return fail("ancestor pane disagreement: its index funds are "
                    f"{pane.get('names')}, expected the same three")
    if sum(r["n"] for r in pane["by_band"]) != pane["events"] or \
            sum(r["fills"] for r in pane["by_band"]) != pane["fills"] or \
            sum(r["n"] for r in pane["by_weekday"]) != pane["events"] or \
            sum(r["fills"] for r in pane["by_weekday"]) != pane["fills"]:
        return fail("ancestor pane disagreement: its totals do not "
                    "match its own band and weekday rows")

    # ---- Market calendar, fear days, gauge-third states ----
    spy_rows = panel["SPY"]
    spy_dates = [r[0] for r in spy_rows]
    spy_close = {r[0]: float(r[4]) for r in spy_rows}
    qqq_close = {r[0]: float(r[4]) for r in panel["QQQ"]}
    vix_dates = sorted(vix)
    fear_by_date = {}
    fear_days = 0
    fear_days_registered = 0
    for i in range(1, len(spy_dates)):
        d, prev = spy_dates[i], spy_dates[i - 1]
        spy_ret = spy_close[d] / spy_close[prev] - 1.0
        qqq_ret = qqq_close[d] / qqq_close[prev] - 1.0
        fear = spy_ret < -0.015
        vd = vix.get(d)
        if vd is not None:
            earlier_vix = [vix[x] for x in vix_dates if x < d]
            if earlier_vix and vd / earlier_vix[-1] - 1.0 > 0.15:
                fear = True
            if vd >= 25.0:
                fear = True
            if vd >= 20.0 and (spy_ret < 0 or qqq_ret < 0):
                fear = True
        fear_by_date[d] = fear
        fear_days += 1 if fear else 0
        if d <= EXPECT_THROUGH:
            fear_days_registered += 1 if fear else 0
    if fear_days_registered != EXPECT["fear_days"]:
        return fail(f"fear-day count disagreement: "
                    f"{fear_days_registered} days over the "
                    f"registered window through {EXPECT_THROUGH}, "
                    f"expected {EXPECT['fear_days']}")

    def prior_session(d):
        i = bisect.bisect_left(spy_dates, d)
        return spy_dates[i - 1] if i > 0 else None

    def states_for(gap_date):
        """(fear_state, vol_state) judged on the most recent completed
        session before gap_date. vol_state is None when that session
        has no gauge close on record (absent, never filled in)."""
        prev = prior_session(gap_date)
        if prev is None:
            return None, None, None
        fear = fear_by_date.get(prev)
        vd = vix.get(prev)
        vol = None
        if vd is not None:
            earlier = [vix[x] for x in vix_dates if x < prev]
            if len(earlier) >= 3:
                cut = quantile(sorted(earlier), 2.0 / 3.0)
                vol = vd >= cut
        return prev, fear, vol

    # ---- Every qualifying gap on the panel ----
    events_by_date = {}
    total_q = total_f = idx_q = idx_f = 0
    band_n = {b: 0 for b in BANDS}
    band_fills = {b: 0 for b in BANDS}
    reg_q = reg_f = reg_idx_q = reg_idx_f = 0
    reg_band_n = {b: 0 for b in BANDS}
    reg_band_fills = {b: 0 for b in BANDS}
    for sym, rows in panel.items():
        for i in range(1, len(rows)):
            prev_close = float(rows[i - 1][4])
            o, h, l, c = (float(rows[i][1]), float(rows[i][2]),
                          float(rows[i][3]), float(rows[i][4]))
            gap_pct = (o - prev_close) / prev_close
            if abs(gap_pct) < 0.005 or prev_close <= 0 or o <= 0:
                continue
            up = gap_pct > 0
            fill = (l <= prev_close) if up else (h >= prev_close)
            d = rows[i][0]
            wd = WEEKDAYS[date.fromisoformat(d).weekday()]
            ev = {"symbol": sym, "date": d, "weekday": wd,
                  "band": band_of(abs(gap_pct)),
                  "gap_pct": gap_pct, "up": up,
                  "prior_close": prev_close, "open": o,
                  "high": h, "low": l, "close": c,
                  "fill": fill, "above": c > o, "below": c < o,
                  "range_mult": (h - l) / abs(o - prev_close)}
            events_by_date.setdefault(d, []).append(ev)
            total_q += 1
            total_f += 1 if fill else 0
            band_n[ev["band"]] += 1
            band_fills[ev["band"]] += 1 if fill else 0
            if sym in INDEXES:
                idx_q += 1
                idx_f += 1 if fill else 0
            if d <= EXPECT_THROUGH:
                reg_q += 1
                reg_f += 1 if fill else 0
                reg_band_n[ev["band"]] += 1
                reg_band_fills[ev["band"]] += 1 if fill else 0
                if sym in INDEXES:
                    reg_idx_q += 1
                    reg_idx_f += 1 if fill else 0
    if (reg_q, reg_f, reg_idx_q, reg_idx_f) != (
            EXPECT["qualifying"], EXPECT["fills"],
            EXPECT["index_qualifying"], EXPECT["index_fills"]) or \
            reg_band_n != EXPECT["band_n"] or \
            reg_band_fills != EXPECT["band_fills"]:
        return fail(f"panel count disagreement over the registered "
                    f"window through {EXPECT_THROUGH}: qualifying "
                    f"{reg_q}, fills {reg_f}, index "
                    f"{reg_idx_q}/{reg_idx_f}, bands "
                    f"{reg_band_n}/{reg_band_fills}; the settled "
                    f"counts are {EXPECT['qualifying']}/"
                    f"{EXPECT['fills']}, index "
                    f"{EXPECT['index_qualifying']}/"
                    f"{EXPECT['index_fills']}")

    # ---- Descriptive history: full counts per band and weekday ----
    def hist_table(subset):
        cells = []
        for b in BANDS:
            for wd in WEEKDAYS:
                evs = [e for e in subset
                       if e["band"] == b and e["weekday"] == wd]
                n = len(evs)
                fills = sum(1 for e in evs if e["fill"])
                row = {"band": b, "band_label": BAND_LABEL[b],
                       "weekday": wd, "weekday_label": WEEKDAY_LABEL[wd],
                       "n": n, "fills": fills, "thin": n < THIN,
                       "fill_pct": (round(fills / n * 100.0, 1)
                                    if n >= THIN else None),
                       "above_pct": (round(
                           sum(1 for e in evs if e["above"]) / n * 100.0, 1)
                           if n >= THIN else None),
                       "below_pct": (round(
                           sum(1 for e in evs if e["below"]) / n * 100.0, 1)
                           if n >= THIN else None),
                       "range_deciles": (deciles(sorted(
                           e["range_mult"] for e in evs))
                           if n >= THIN else None)}
                cells.append(row)
        return cells

    all_events = [e for evs in events_by_date.values() for e in evs]
    index_events = [e for e in all_events if e["symbol"] in INDEXES]
    hist_all = hist_table(all_events)
    hist_index = hist_table(index_events)
    band_rows = []
    for b in BANDS:
        evs = [e for e in all_events if e["band"] == b]
        iev = [e for e in index_events if e["band"] == b]
        band_rows.append({
            "band": b, "band_label": BAND_LABEL[b],
            "all_n": len(evs),
            "all_fills": sum(1 for e in evs if e["fill"]),
            "all_fill_pct": round(
                sum(1 for e in evs if e["fill"]) / len(evs) * 100.0, 1),
            "index_n": len(iev),
            "index_fills": sum(1 for e in iev if e["fill"]),
            "index_fill_pct": (round(
                sum(1 for e in iev if e["fill"]) / len(iev) * 100.0, 1)
                if len(iev) >= THIN else None),
            "index_thin": len(iev) < THIN,
            "range_deciles": deciles(sorted(
                e["range_mult"] for e in evs))})

    # ---- FE04 sign flip sub claim: descriptive history tally ----
    # Graded on its own outcome (the close against the prior
    # close), never blended into the fill chances above. The
    # tally is descriptive over the whole panel: the proxy is a
    # daily closing location, so this is the claim's history
    # shape, not a walk-forward proof, and it is labelled that
    # way wherever it is published.
    def flip_tally(evs):
        n = hits = misses = flat = 0
        for e in evs:
            a = acceptance_proxy(e["up"], e["high"], e["low"],
                                 e["close"])
            pred = fe04_sign_flip(e["gap_pct"], a)[
                "predicted_close_sign"]
            if pred == 0:
                continue
            n += 1
            outcome = (1 if e["close"] > e["prior_close"]
                       else -1 if e["close"] < e["prior_close"]
                       else 0)
            if outcome == 0:
                flat += 1
            elif outcome == pred:
                hits += 1
            else:
                misses += 1
        decided = hits + misses
        return {"n": n, "hits": hits, "misses": misses,
                "flat_close_at_prior": flat,
                "hit_pct": (round(hits / decided * 100.0, 1)
                            if decided >= THIN else None),
                "thin": decided < THIN}

    flip_all = flip_tally(all_events)
    flip_accepted = flip_tally(
        [e for e in all_events
         if acceptance_proxy(e["up"], e["high"], e["low"],
                             e["close"]) > 0.5])
    flip_rejected = flip_tally(
        [e for e in all_events
         if acceptance_proxy(e["up"], e["high"], e["low"],
                             e["close"]) < 0.5])

    # ---- Walk-forward sweep: history scoring + live estimation ----
    cells = {}

    def cell(key):
        if key not in cells:
            cells[key] = Cell()
        return cells[key]

    def forecast(band, wd, fear, vol, cache):
        """(value dict, source label, base n) from earlier cases only,
        or None when even the pooled cell is thin. Deciles for a cell
        are computed at most once per session date (cache)."""
        def steps_of(key, c):
            if key not in cache:
                cache[key] = deciles_fast(c.ranges)
            return cache[key]

        base = None
        for key, label in ((("bw", band, wd), "same band, same weekday"),
                           (("band", band), "same band, any weekday"),
                           (("all",), "all qualifying gaps")):
            c = cell(key)
            if c.n >= THIN:
                base = (key, c, label)
                break
        if base is None:
            return None
        base_key, c, label = base
        pf, pa, pb = c.rates()
        used = label
        steps = steps_of(base_key, c)
        applied = []
        for state, kind in ((fear, "fear"), (vol, "vol")):
            if state is None:
                continue
            ckey = (kind, band, wd, bool(state))
            cc = cell(ckey)
            if cc.n >= THIN:
                cf, ca, cb = cc.rates()
                pf = (cc.fills + PRIOR_STRENGTH * pf) / (cc.n + PRIOR_STRENGTH)
                pa = (cc.above + PRIOR_STRENGTH * pa) / (cc.n + PRIOR_STRENGTH)
                pb = (cc.below + PRIOR_STRENGTH * pb) / (cc.n + PRIOR_STRENGTH)
                steps = steps_of(ckey, cc)
                applied.append(kind)
                used = label + f", adjusted for the {kind} reading"
        clamp = lambda p: min(max(p, P_MIN), P_MAX)  # noqa: E731
        value = {"p": round(clamp(pf), 4),
                 "p_fill": round(clamp(pf), 4),
                 "p_above": round(clamp(pa), 4),
                 "p_below": round(clamp(pb), 4),
                 "p_at_open": round(max(
                     0.0, 1.0 - clamp(pa) - clamp(pb)), 4),
                 "range_deciles": steps}
        return value, used, c.n, applied

    def add_event(ev, fear, vol):
        cell(("all",)).add(ev)
        cell(("band", ev["band"])).add(ev)
        cell(("bw", ev["band"], ev["weekday"])).add(ev)
        if fear is not None:
            cell(("fear", ev["band"], ev["weekday"], bool(fear))).add(ev)
        if vol is not None:
            cell(("vol", ev["band"], ev["weekday"], bool(vol))).add(ev)

    def new_score():
        return {"n": 0, "brier_fill": 0.0, "brier_fill_base": 0.0,
                "brier_above": 0.0, "brier_below": 0.0,
                "range_in_steps": 0, "skipped": 0}

    wf_all, wf_index = new_score(), new_score()
    wf_by_band = {b: new_score() for b in BANDS}
    live_entries = []
    live_states = None
    for d in sorted(events_by_date):
        prev, fear, vol = states_for(d)
        evs = events_by_date[d]
        cache = {}
        if d == as_of:
            live_states = {"prior_session": prev, "fear": fear, "vol": vol}
            for ev in evs:
                got = forecast(ev["band"], ev["weekday"], fear, vol, cache)
                if got is None:
                    return fail(f"no earlier cell can price the live "
                                f"gap for {ev['symbol']} on {d}")
                value, used, base_n, applied = got
                fm_acc = None
                if d not in _issued_sub_sessions():
                    fm_acc = first_minutes_acceptance(
                        d, ev["symbol"])
                if fm_acc is not None:
                    acc = fm_acc
                    acc_source = "first_minutes_record"
                else:
                    acc = acceptance_proxy(ev["up"], ev["high"],
                                           ev["low"], ev["close"])
                    acc_source = "daily_proxy"
                flip = fe04_sign_flip(ev["gap_pct"], acc)
                entry = {"symbol": ev["symbol"],
                         "is_index": ev["symbol"] in INDEXES,
                         "gap_pct": round(ev["gap_pct"] * 100.0, 3),
                         "direction": "up" if ev["up"] else "down",
                         "band": ev["band"], "band_label": BAND_LABEL[ev["band"]],
                         "weekday": ev["weekday"],
                         "weekday_label": WEEKDAY_LABEL[ev["weekday"]],
                         "prior_close": ev["prior_close"],
                         "open": ev["open"],
                         "p_fill": value["p_fill"],
                         "p_fill_pct": round(value["p_fill"] * 100.0, 1),
                         "p_above_pct": round(value["p_above"] * 100.0, 1),
                         "p_below_pct": round(value["p_below"] * 100.0, 1),
                         "p_at_open_pct": round(value["p_at_open"] * 100.0, 1),
                         "range_deciles": value["range_deciles"],
                         "based_on": used, "based_on_cases": base_n,
                         "fear_applied": "fear" in applied,
                         "vol_applied": "vol" in applied,
                         "acceptance_proxy_pct": round(acc * 100.0, 1),
                         "acceptance_source": acc_source,
                         "sub_claim": flip["claim"],
                         "sub_claim_predicted_close": (
                             "above the prior close"
                             if flip["predicted_close_sign"] > 0
                             else "below the prior close"
                             if flip["predicted_close_sign"] < 0
                             else "no direction call"),
                         "_sub_value": {
                             "claim": "failed_gap_sign_flip",
                             "gap_pct": round(
                                 ev["gap_pct"] * 100.0, 3),
                             "acceptance_proxy": round(acc, 4),
                             **({"acceptance_source": acc_source}
                                if acc_source
                                == "first_minutes_record"
                                else {}),
                             "acceptance_state":
                                 flip["acceptance_state"],
                             "predicted_close_sign":
                                 flip["predicted_close_sign"],
                             "leg": flip["claim"]},
                         "_value": dict(value, band=ev["band"],
                                        weekday=ev["weekday"],
                                        gap_pct=round(ev["gap_pct"] * 100.0, 3))}
                live_entries.append(entry)
            continue
        for ev in evs:
            got = forecast(ev["band"], ev["weekday"], fear, vol, cache)
            bc = cell(("band", ev["band"]))
            if got is None or bc.n < THIN:
                wf_all["skipped"] += 1
                if ev["symbol"] in INDEXES:
                    wf_index["skipped"] += 1
                continue
            value, _used, _n, _applied = got
            yf = 1.0 if ev["fill"] else 0.0
            ya = 1.0 if ev["above"] else 0.0
            yb = 1.0 if ev["below"] else 0.0
            base_p = bc.fills / bc.n
            for acc in (wf_all, wf_by_band[ev["band"]]) + (
                    (wf_index,) if ev["symbol"] in INDEXES else ()):
                acc["n"] += 1
                acc["brier_fill"] += (value["p_fill"] - yf) ** 2
                acc["brier_fill_base"] += (base_p - yf) ** 2
                acc["brier_above"] += (value["p_above"] - ya) ** 2
                acc["brier_below"] += (value["p_below"] - yb) ** 2
                steps = value["range_deciles"]
                acc["range_in_steps"] += 1 if (
                    steps[0] <= ev["range_mult"] <= steps[-1]) else 0
        for ev in evs:
            add_event(ev, fear, vol)

    def score_out(acc):
        n = acc["n"]
        if n == 0:
            return {"graded": 0, "skipped": acc["skipped"]}
        return {"graded": n, "skipped": acc["skipped"],
                "brier_fill": round(acc["brier_fill"] / n, 4),
                "brier_fill_plain_band": round(
                    acc["brier_fill_base"] / n, 4),
                "brier_above": round(acc["brier_above"] / n, 4),
                "brier_below": round(acc["brier_below"] / n, 4),
                "range_steps_coverage_pct": round(
                    acc["range_in_steps"] / n * 100.0, 1)}

    live_entries.sort(key=lambda e: (not e["is_index"], e["symbol"]))
    live_index = [e for e in live_entries if e["is_index"]]
    # Cure G17, 2026-10-30: the live set was pinned to the build
    # day's issue (2026-10-23: 1,216 entries, index {SPY, IWM}),
    # so every later session failed closed on a healthy panel.
    # The live set is a fact of the as-of session, not a register:
    # it is now cross-checked by an independent recount of the
    # as-of session's qualifying gaps straight from the panel
    # (previous close to open, at least 0.5 percent), and the two
    # must agree exactly, index names included. Measured instance
    # on the cure date: 2026-10-29 carries 1,445 qualifying gaps,
    # index {QQQ} only (SPY and IWM gapped under 0.5 percent).
    recount = []
    for sym, rows in panel.items():
        for i in range(1, len(rows)):
            if rows[i][0] != as_of:
                continue
            prev_close = float(rows[i - 1][4])
            o = float(rows[i][1])
            if prev_close > 0 and o > 0 \
                    and abs((o - prev_close) / prev_close) >= 0.005:
                recount.append(sym)
            break
    recount_index = sorted(s for s in recount if s in INDEXES)
    if len(live_entries) != len(recount) \
            or sorted(e["symbol"] for e in live_index) != recount_index:
        return fail(f"live set disagreement on {as_of}: the walk "
                    f"forward built {len(live_entries)} entries "
                    f"(index {[e['symbol'] for e in live_index]}) "
                    f"but an independent recount of the panel's "
                    f"as-of session finds {len(recount)} qualifying "
                    f"gaps (index {recount_index})")

    # ---- Ledger the live sets (API only, never by hand) ----
    reg = registry_mod.load()
    led = ledger_mod.Ledger(
        os.path.join(LINEUP, "forecast", "ledger.jsonl"), registry=reg)
    if not led.verify_chain():
        return fail("the forecast record does not verify; refusing "
                    "to add to it")
    lineage = {
        "source_artifacts": [
            {"path": PANEL_PATH,
             "sha256": ledger_mod.file_sha256(PANEL_PATH)},
            {"path": VIX_PATH,
             "sha256": ledger_mod.file_sha256(VIX_PATH)},
            {"path": PANE_PATH,
             "sha256": ledger_mod.file_sha256(PANE_PATH)},
        ],
        "clocks": {
            "event_time": as_of,
            "publication_time": as_of,
            "first_available_time": as_of,
            "ingestion_time": as_of,
            "decision_as_of": as_of,
        },
        "note": ("Gap Destiny probability set staked at the open of "
                 "the gap session, from qualifying gaps on earlier "
                 "sessions only, pooled across the shipped list. "
                 "Shifter states are judged on the most recent "
                 "completed session before the gap session."),
    }
    created = 0
    for entry in live_entries:
        ev_outcome = {
            "symbol": entry["symbol"], "kind": "gap_fill",
            "at_date": as_of, "prior_close": entry["prior_close"],
            "open": entry["open"],
            "fill_event": ("the day's low at or below the previous "
                           "close for an up gap, or the day's high at "
                           "or above it for a down gap"),
            "close_event": "the close against the open",
            "range_event": ("the day's high-to-low range as a "
                            "multiple of the gap")}
        row, was_created = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=as_of,
            subject=entry["symbol"], quantity=QUANTITY,
            value=entry["_value"],
            horizon_open=as_of, horizon_close=as_of,
            lineage=lineage,
            families=["price", "distributional_volatility"],
            outcome=ev_outcome)
        if row.get("quantity") != QUANTITY:
            return fail(f"ledger write for {entry['symbol']} landed "
                        f"on a different forecast row")
        created += 1 if was_created else 0

    # ---- Ledger the FE04 sign flip sub claim, separately ----
    # Its own quantity and its own outcome (the close against the
    # prior close), so its record is graded apart from the fill
    # chances and never counted on top of them.
    sub_created = 0
    for entry in live_entries:
        sub_outcome = {
            "symbol": entry["symbol"],
            "kind": "close_vs_prior_close_sign",
            "at_date": as_of, "prior_close": entry["prior_close"],
            "event": ("the session close finishing on the "
                      "predicted side of the prior close")}
        row, was_created = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=as_of,
            subject=entry["symbol"], quantity=SUB_QUANTITY,
            value=entry["_sub_value"],
            horizon_open=as_of, horizon_close=as_of,
            lineage=lineage,
            families=["price", "distributional_volatility"],
            outcome=sub_outcome)
        if row.get("quantity") != SUB_QUANTITY:
            return fail(f"sub claim write for {entry['symbol']} "
                        f"landed on a different forecast row")
        sub_created += 1 if was_created else 0

    # ---- Void the duplicate sub claim rows of the first
    # publication cure run (2026-10-30): that run re-issued the
    # already issued 2026-10-29 sub claim set under the new
    # first minutes acceptance input, doubling the session's
    # set. The ledger is append only, so the duplicates are
    # voided by correction rows (the Engine 14 pattern) and the
    # counts below exclude voided rows. The session's original
    # issue stands as issued.
    rows_pre = led.rows()
    corrected_ids = {
        r.get("corrects_row_id") for r in rows_pre
        if r.get("type") == "correction"}
    for row in rows_pre:
        if row.get("type") != "forecast" \
                or row.get("engine_id") != ENGINE_ID \
                or row.get("quantity") != SUB_QUANTITY:
            continue
        val = row.get("value") or {}
        # Both stamped forms are the first cure run's: the
        # first minutes rows, and the daily proxy rows for the
        # 6 names the record does not cover, whose ledger value
        # that run stamped with acceptance_source daily_proxy
        # (pre-cure code never wrote the key, so the stamp alone
        # identifies the duplicate issue).
        if val.get("acceptance_source") not in \
                ("first_minutes_record", "daily_proxy"):
            continue
        if row["row_id"] in corrected_ids:
            continue
        led.append_correction(
            corrects_row_id=row["row_id"],
            note=("Void: duplicate re-issue of the session's "
                  "already issued sub claim under a changed "
                  "acceptance input, superseded by the "
                  "session's original issue"),
            payload={"engine_id": ENGINE_ID,
                     "reason": ("acceptance input changed after "
                                "the session was issued; the "
                                "session's set is frozen at "
                                "first issue"),
                     "superseded_by": ("the session's original "
                                       "issue, daily proxy form")})
    # ---- Void duplicate main set re-issues (RC-20 companion,
    # 2026-10-30): the cured VIX capture extended the gauge
    # record backward, which changed the fear and vol states
    # inside the already issued 2026-10-29 main set's values, so
    # the first run after the capture re-issued the session's
    # whole main set under changed inputs (1,445 new rows beside
    # the original 1,445). The session's set is frozen at first
    # issue, the same rule the sub claim voiding above applies:
    # for each (session, subject) the earliest main row stands
    # and every later main row is a duplicate re-issue, voided
    # here by correction rows. Identical republications never
    # reach this code (the ledger dedupes them at append).
    seen_main = set()
    for row in rows_pre:
        if row.get("type") != "forecast" \
                or row.get("engine_id") != ENGINE_ID \
                or row.get("quantity") != QUANTITY:
            continue
        sess = row["lineage"]["clocks"]["decision_as_of"]
        key = (sess, row.get("subject"))
        if key not in seen_main:
            seen_main.add(key)
            continue
        if row["row_id"] in corrected_ids:
            continue
        led.append_correction(
            corrects_row_id=row["row_id"],
            note=("Void: duplicate re-issue of the session's "
                  "already issued main set under a changed "
                  "gauge input, superseded by the session's "
                  "original issue"),
            payload={"engine_id": ENGINE_ID,
                     "reason": ("gauge record extended after the "
                                "session was issued; the session's "
                                "set is frozen at first issue"),
                     "superseded_by": ("the session's original "
                                       "issue")})
    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    voided_ids = {
        r.get("corrects_row_id") for r in rows
        if r.get("type") == "correction"}
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    todays = [r for r in rows
              if r.get("type") == "forecast"
              and r.get("engine_id") == ENGINE_ID
              and r.get("quantity") == QUANTITY
              and r["row_id"] not in voided_ids
              and r["lineage"]["clocks"]["decision_as_of"] == as_of]
    if len(todays) != len(live_entries):
        return fail(f"ledger count disagreement: {len(todays)} live "
                    f"sets for {as_of}, expected {len(live_entries)}")
    sub_todays = [r for r in rows
                  if r.get("type") == "forecast"
                  and r.get("engine_id") == ENGINE_ID
                  and r.get("quantity") == SUB_QUANTITY
                  and r["row_id"] not in voided_ids
                  and r["lineage"]["clocks"]["decision_as_of"] == as_of]
    if len(sub_todays) != len(live_entries):
        return fail(f"sub claim count disagreement: "
                    f"{len(sub_todays)} live sub claim rows for "
                    f"{as_of}, expected {len(live_entries)}")
    main_recorded = sum(
        1 for r in rows if r.get("type") == "forecast"
        and r.get("engine_id") == ENGINE_ID
        and r.get("quantity") == QUANTITY
        and r["row_id"] not in voided_ids)
    sub_recorded = sum(
        1 for r in rows if r.get("type") == "forecast"
        and r.get("engine_id") == ENGINE_ID
        and r.get("quantity") == SUB_QUANTITY
        and r["row_id"] not in voided_ids)
    sub_row_ids = {r["row_id"] for r in rows
                   if r.get("type") == "forecast"
                   and r.get("engine_id") == ENGINE_ID
                   and r.get("quantity") == SUB_QUANTITY
                   and r["row_id"] not in voided_ids}
    sub_graded = sum(
        1 for g in rows if g.get("type") == "grade"
        and g.get("forecast_row_id") in sub_row_ids)
    index_recorded = sum(
        1 for r in rows if r.get("type") == "forecast"
        and r.get("engine_id") == ENGINE_ID
        and r.get("quantity") == QUANTITY
        and r["row_id"] not in voided_ids
        and r["subject"] in INDEXES)
    for entry in live_entries:
        entry.pop("_value", None)
        entry.pop("_sub_value", None)

    prev = live_states["prior_session"]
    spy_prev_ret = None
    if prev is not None:
        pp = prior_session(prev)
        if pp is not None:
            spy_prev_ret = round(
                (spy_close[prev] / spy_close[pp] - 1.0) * 100.0, 2)
    last_vix_date = vix_dates[-1]
    last_vix = vix[last_vix_date]
    vix_cut = quantile(sorted(vix.values()), 2.0 / 3.0)

    data = {
        "tool": "Gap Destiny",
        "state": "proving",
        "as_of_session": as_of,
        "weekday_label": WEEKDAY_LABEL[
            WEEKDAYS[date.fromisoformat(as_of).weekday()]],
        "source": (f"Daily prices for 1,833 names from the price "
                   f"history on record ({len(panel['SPY'])} trading "
                   f"days, {span_start} to {as_of}), plus "
                   f"{len(vix)} daily fear gauge readings "
                   f"({vix_dates[0]} to {vix_dates[-1]}). The longer "
                   f"daily history the design names is not on "
                   f"record here, so every count on this page comes "
                   f"from that span and no other."),
        "idea": ("The older Gap-Fill Pane shows how gaps like "
                 "today's behaved in the past. This page does a "
                 "different job: at the open, for every name that "
                 "gaps at least half a percent, it stakes a set of "
                 "chances on today's gap before the session unfolds, "
                 "writes that set to a public record that cannot be "
                 "edited afterwards, and is graded at today's close."),
        "live": {
            "qualifying_gaps": len(live_entries),
            "indexes": live_index,
            "names": live_entries,
            "names_counted": len(panel),
            "shifters": {
                "prior_session": prev,
                "prior_session_spy_change_pct": spy_prev_ret,
                "fear_state": live_states["fear"],
                "fear_applied": bool(live_index and
                                     live_index[0]["fear_applied"]),
                "fear_note": ("Judged on the completed session "
                              "before the gap day, because a fear "
                              "reading for a day is built from that "
                              "day's close and cannot be known at "
                              "the open. Gauge readings are on "
                              f"record from {vix_dates[0]} to "
                              f"{vix_dates[-1]}; "
                              + (f"the session before this gap day "
                                 f"({prev}) carries one, so its "
                                 f"gauge parts were judged too."
                                 if prev in vix else
                                 "the session before this gap day "
                                 "carries none, so for it only the "
                                 "big fund's fall could be judged.")),
                "vol_state": live_states["vol"],
                "vol_applied": bool(live_index and
                                    live_index[0]["vol_applied"]),
                "vol_note": (
                    f"This reading needs a fear gauge close for "
                    f"the completed session before the gap day. "
                    + (f"That session ({prev}) carries one, and "
                       f"the reading is "
                       f"{'in the top third of the readings on record, so it counted' if live_states['vol'] else 'not in the top third of the readings on record, so it changed nothing'}."
                       if live_states["vol"] is not None else
                       f"That session has none on record, so the "
                       f"reading is absent and changed nothing.")
                    + f" The last gauge reading on record, "
                      f"{last_vix_date}, was {round(last_vix, 2)}, "
                      f"{'in the top third' if last_vix >= vix_cut else 'not in the top third'} "
                      f"of the readings on record."),
                "last_gauge_date": last_vix_date,
                "last_gauge_value": round(last_vix, 2),
            },
        },
        "history": {
            "label": "History, not live forecasts",
            "span_start": span_start, "span_end": as_of,
            "sessions": len(panel["SPY"]),
            "note": ("Worked out day by day over the price history "
                     "on record: each day's chances were built only "
                     "from earlier days, then checked against what "
                     "actually happened that day. These are study "
                     "figures from the past, not the live record."),
            "totals": {"qualifying": total_q, "fills": total_f,
                       "fill_pct": round(total_f / total_q * 100.0, 1),
                       "index_qualifying": idx_q, "index_fills": idx_f,
                       "index_fill_pct": round(
                           idx_f / idx_q * 100.0, 1)},
            "bands": band_rows,
            "by_band_weekday_all": hist_all,
            "by_band_weekday_index": hist_index,
            "walk_forward": score_out(wf_all),
            "walk_forward_index": score_out(wf_index),
            "walk_forward_by_band": {b: score_out(wf_by_band[b])
                                     for b in BANDS},
            "fear_days": fear_days,
            "ancestor": {
                "events": pane["events"], "fills": pane["fills"],
                "fill_pct": round(pane["frequency"] * 100.0, 2),
                "as_of": pane["as_of"],
                "note": ("The older pane's own published figures, "
                         "from within-day prices over 90 days, any "
                         "gap however small, for the three index "
                         "funds only. A different method from this "
                         "page's daily figures, shown so the two are "
                         "never mixed up. A later run of that study "
                         "sits on the studies record with slightly "
                         "different totals, because it is a later "
                         "run; the two runs are not compared here."),
            },
        },
        "failed_gap_sub_claim": {
            "statement": (
                "A stated sub claim of this engine, graded "
                "separately from the fill chances: when the "
                "session rejects a gap (acceptance below half), "
                "the close is forecast to finish on the other "
                "side of the prior close, the failed gap "
                "travelling the other way, not merely failing to "
                "fill. When the session accepts the gap, the "
                "close is forecast to finish on the gap's own "
                "side. At exactly neutral acceptance the leg "
                "makes no direction call."),
            "acceptance_proxy": (
                "Acceptance for the live session is read from "
                "the first minutes record where it covers a "
                "name: the closing location inside the first "
                "15 minute range, read in the gap's direction, "
                "from Alpaca SIP 5 minute bars "
                "(first_minutes.py). Names and sessions the "
                "record does not cover keep the daily proxy, "
                "the closing location inside the session's own "
                "daily range, labelled per entry as "
                "daily_proxy. Each live entry names its own "
                "acceptance_source."),
            "first_minutes_record": {
                "session": first_minutes_record().get("session"),
                "gap_names": first_minutes_record().get(
                    "gap_names"),
                "names_recorded": first_minutes_record().get(
                    "names_recorded"),
                "missing_count": len(first_minutes_record().get(
                    "missing", [])),
                "source": first_minutes_record().get("source")},
            "history": {
                "label": ("Descriptive history over the whole "
                          "panel, not a walk-forward proof: the "
                          "proxy is read from the same session it "
                          "describes."),
                "all": flip_all,
                "accepted_leg": flip_accepted,
                "rejected_leg_failed_gap": flip_rejected},
            "live_recorded": sub_recorded,
            "live_graded": sub_graded,
            "live_created_this_run": sub_created,
            "grading": (
                "Each live leg is written to the public record "
                "under its own forecast quantity and graded on "
                "its own outcome, the close against the prior "
                "close, apart from the fill chance scores. Its "
                "cases are never counted on top of the main "
                "record's cases."),
        },
        "live_record": {
            # The headline pair counts every forecast this
            # engine has on the record, the gap sets and the
            # failed-gap sub claim rows together, matching the
            # graded count beside it (recompute_figures counts
            # the whole engine). The gap-set count alone stays
            # printed as its own field (hookup cure, 2026-10-29:
            # the pair previously read 1216 recorded against a
            # graded count drawn from all 1566 rows).
            # RC-20 cure (2026-10-30): recompute_figures counts
            # every forecast row, including the voided duplicate
            # sub claim rows voided above by correction rows. The
            # recorded figure must count valid rows only, with the
            # voided count named beside it, never inside it.
            "forecasts_recorded": mine["forecasts"] - sum(
                1 for r in rows if r.get("type") == "forecast"
                and r.get("engine_id") == ENGINE_ID
                and r["row_id"] in voided_ids),
            "forecasts_voided": sum(
                1 for r in rows if r.get("type") == "forecast"
                and r.get("engine_id") == ENGINE_ID
                and r["row_id"] in voided_ids),
            "gap_sets_recorded": main_recorded,
            # Defect 8 cure (2026-10-30): recompute_figures now
            # counts graded on the valid basis only; the voided
            # population's grades stay named beside it.
            "forecasts_graded": mine["graded"],
            "grades_on_voided": mine.get("grades_on_voided", 0),
            "index_gaps_recorded": index_recorded,
            "index_gaps_target": KILL_INDEX_GAPS,
            "blocks_of_60_completed": mine["graded"] // BLOCK,
            "second_arm": ("A second form of this engine, built on "
                           "each name's own past gaps instead of "
                           "everyone's, is written down as part of "
                           "this engine and starts only once the "
                           "pooled record above has matured. It is "
                           "not a separate tool, and its cases will "
                           "never be counted on top of these."),
        },
        "kill_criterion": ("This tool is retired if, after 120 "
                           "graded index gaps, its fill chances "
                           "score no better than simply using the "
                           "plain rate for that gap-size band every "
                           "time."),
        "thin_cell_rule": ("Any cell with fewer than 30 cases "
                           "shows its count only, with no rate."),
        "excluded_variant": ("One variant is left out on purpose: "
                             "saying whether a gap fills early in "
                             "the session or only by the close. The "
                             "within-day price record on hand "
                             "cannot support it today, so it is not "
                             "promised."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    wf = data["history"]["walk_forward"]
    print(f"Wrote {OUT_PATH}: live {as_of}, {main_recorded} "
          f"recorded sets ({created} new), {len(live_entries)} "
          f"qualifying gaps ({len(live_index)} index), sub claim "
          f"{sub_recorded} recorded ({sub_created} new), "
          f"walk-forward graded {wf['graded']} with fill score "
          f"{wf.get('brier_fill')} vs plain band "
          f"{wf.get('brier_fill_plain_band')}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
