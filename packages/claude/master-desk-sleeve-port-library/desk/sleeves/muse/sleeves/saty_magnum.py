"""saty_magnum — Saty Mahajan's COMPLETE system as one sleeve:
the level map, the ribbon regime, the Phase Oscillator state
machine, Volume Stack confirmation, and the close-confirmed
Golden Gate with a pullback entry, built 2026-10-22 from
MAGNUM-SPEC.md (workflow saty-magnum-opus-20261022) against the
3,822-post corpus and the five verbatim Pine originals in the
study home (opt/rea-teardowns/saty-stack/).

THE SYSTEM IN ONE PARAGRAPH. Before the open the sleeve writes
its plan: the day ladder frozen from the previous completed
regular-session daily close (anchor) and that period's ATR(14)
(unit) — levels at anchor +/- unit x {0.236 trigger, 0.382
Golden Gate, 0.500, 0.618 midrange, 0.786, 1.000, extensions to
2.000} — plus the weekly (Multiday) ladder as context, the range
gauge, the daily regime, and a $VIX key level (the prior
session's ^VIX close). It trades only when the Pro ribbon
(8/13/21/48/200, pullback overlap on — there is NO 34 EMA in the
Pro) agrees on the daily AND 10-minute frames at once: above
the ribbon riding it is bullish, repeated crossings are chop,
and his mantra is a gate, not a hint — "I don't trade in a
sideways market. I wait for trend confirmation." Three arms, in
a fixed arbitration order: Arm C, the one quantified snap-back
(3m PO below -100 AND 10m PO below -100 AND 1h PO below -80,
with momentum already waning — extremes are never faded on the
extreme alone: "High can go higher. Low can go lower"); Arm B,
a compression release (the Phase Oscillator's stateless
compression predicate true on at least two consecutive
completed 10m bars, then a release close beyond the coil range
— "compression followed by green or red is a very clear
indication of directional price expansion"); and Arm A, the
Golden Gate continuation: a completed 10-minute bar CLOSES
through the +/-38.2% gate, then the sleeve waits for the
pullback it is taught to wait for ("I never chase the trend. I
wait for a pullback to execute my trade") — a completed 3-minute
retest of the gate zone that closes back on the trend side,
confirmed on that bar by the Volume Stack. Exits are underlying
close rules and level touches, never premium: a completed 10m
close back through the origin trigger kills an Arm A position
("cut it if it goes below the call trigger"), the coil midpoint
kills Arm B; a third comes off at +50%, a third at +61.8% (the
runner's risk then moves to break-even — "move stops as you
go"), and the runner exits at +1 ATR (Arm B's squeeze runner
targets +2 ATR, his named profit zone's safe end). Everything
is flat by close - 5 minutes, always: a close-rule system has
no stop overnight, so it holds no overnight position.

INSTRUMENT. SPY SHARES only, long and short — the linear
expression of a level-to-level system (partial exits at exact
ladder rungs and break-even migration are share-native). SPX
cash has no desk feed and does not trade; there are no futures
and no options in this sleeve (both sibling sleeves already
express the system in options). The snap-back arm's SPX leg is
read on SPY — a labeled translation in the po10_qqq precedent,
never presented as an SPX read.

COMPLETED BARS ONLY (hazard H-1, binding). The oscillator
original's Time Warp leaks the forming higher-timeframe bar.
This sleeve never warps: every indicator is computed on its own
timeframe's bars through the landed port (core/saty_bars,
core/saty_indicators, core/saty_primitives — the sleeve
re-derives no indicator math), and a bar counts only when its
close time is <= now. No forming bar can arm, trigger, confirm
or exit anything. Session basis is REGULAR (RTH) for every
component and both ladders — one basis, auditable, matching the
traded session; which basis Saty himself trades from is
UNPROVEN in the corpus and this choice is the desk's, stated
here so no reader mistakes it for his proven practice.

BUILDER REGISTER (MAGNUM-SPEC section 16 — every number the
evidence does not state, the desk's choices, never Saty's, and
never presented as his on any reader surface):
  MAG-B1 v1 scope: the day system with multiday context, flat
    by close; arm arbitration order C -> B -> A; the EOD flat
    as the mechanization of his no-stop-overnight doctrine.
  MAG-B2 the range gauge at red (>=90%) blocks new Arm A/B
    entries; the VIX key level is the prior ^VIX close; the
    Arm A runner extends its final target from +1.000 to the
    +1.236 extension only when the nearest weekly rung beyond
    the day target lies beyond +1.236.
  MAG-B3 risk_pct 0.005 of slice equity risked to the
    invalidation level per trade; notional cap 25% of slice
    equity; Arm C at half size; the sleeve's own session stop
    at -1% of slice equity (no new entries; exits continue —
    NOT Milkman's $10K and NOT Sol's 1% latch); one position
    at a time; entry caps Arm A <= 2, Arm B <= 1 per coil,
    Arm C <= 1 per episode, 3 entries per session; station
    fractions in thirds.
  MAG-B4 event freshness 1800 s; the Arm A retest window is
    60 minutes from the gate-open bar's close; chop = at least
    3 crossings of the 10m EMA21 in the last 12 completed 10m
    bars; the opening wait is 10 minutes (the short end of his
    stated 10-20); midday stand-down 11:30-13:30 for Arms A/B;
    no new entries after close - 30 minutes; Arm C time stop
    60 minutes.
  MAG-B5 the Golden Gate OPEN is a completed-10m-CLOSE
    definition (his own event semantics are UNPROVEN; the
    practitioner touch definition is saty_day's rule, not this
    sleeve's); equality on a kill level does not breach it;
    the coil minimum is 2 bars; a release needs no retest.
  MAG-B6 Volume Stack confirmation is a builder-chosen vote:
    the retest bar's winning side must agree with the trade
    direction AND hold at least 55% of the bar's split volume.
    No Volume Stack trade rule exists in the corpus; the 55%
    figure and the winner rule are the desk's and must never
    be attributed to Saty.

UNPROVEN AND EXCLUDED (MAGNUM-SPEC section 15): Vomy/iVomy in
any form; Phase Oscillator divergence as a mechanical rule
(hand-drawn only in his charts); any mechanical VIX gate; any
economic-calendar stand-down (no desk calendar door in v1 —
the gap is named, not papered over); swing/position-horizon
Golden Gate trading (those ladders are computed and stamped as
context only); adds. Saty states no fixed risk number anywhere
in 3,822 posts — every number in the sizing section is the
desk's, tagged MAG-B3 above.

FORWARD TESTING ONLY. This sleeve claims no edge and no
backtest result anywhere. Its edge, if any, is established by
forward testing on paper from its first landed session — the
desk's law for every sleeve. (Saty's one backtest sentence in
the corpus is recorded in the study as his claim; it is not
used here.)

DESK SHAPE. CONFIG + signal() in the saty_day / po10_qqq
idiom: a pure function of the bars and broker state it is
handed, deterministically reconstructed on every 60-second
pass; position facts come from the broker record, which is
truth, and the position's arm is attributed by replaying the
session's entry events up to the fill (the saty_day _identify
precedent) — an unattributable position is managed on the Arm
A baseline for its direction and stamped ownership_mismatch,
never silently adopted and never left unmanaged. Every
decision is stamped onto self.last_evaluation, which the
dispatcher merges into the evaluation ledger row; intents are
filed through the Ink intent door at dispatch. Intent.stop /
Intent.target are NEVER set: on this desk those fields feed
the broker protection-stop path, and this system's
invalidation is an underlying CLOSE rule, not a resting stop.
No bars = no signal: missing data stands the sleeve down for
entries, and a held position still receives its time-based
exits (the D-B1 pattern). saty_sol.py is never touched by this
build; its sha256 is asserted unchanged by the trap tests.
"""
import math
from datetime import date, datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

from core.data import is_trading_day
from core.early_close import EARLY_CLOSES as _SHARED_EARLY_CLOSES
from core.sleeve import BaseSleeve, Intent, SleeveConfig
from core import saty_bars as sb
from core import saty_indicators as si

ET = ZoneInfo("America/New_York")
SYM = "SPY"

CONFIG = SleeveConfig(
    sleeve_id="saty_magnum",
    cadence_s=60,
    universe=("SPY",),
    state_schema={"position": "dict|None"},
    risk_pct=0.005,
)

# -- his numbers (MAGNUM-SPEC sections 3, 5, 8-11) -------------
F_TRIGGER = 0.236
F_GATE = 0.382
F_MID = 0.500
F_TARGET = 0.618
F_RUNNER = 0.786
F_FULL = 1.000
F_EXT = 1.236
F_SQUEEZE = 2.000
SNAP_M3 = -100.0               # Arm C legs (R26): strict below
SNAP_M10 = -100.0
SNAP_H1 = -80.0
QUOTE_STALE_S = 60.0           # desk IEX quote convention

# -- builder numbers (MAG-B3 / MAG-B4 / MAG-B6) ----------------
RISK_PCT = 0.005               # MAG-B3
NOTIONAL_CAP = 0.25            # MAG-B3
SESSION_STOP_PCT = 0.01        # MAG-B3 (no-entry, not a latch)
FRESH_S = 1800.0               # MAG-B4
RETEST_WINDOW_S = 3600.0       # MAG-B4
CHOP_CROSSINGS = 3             # MAG-B4
CHOP_BARS = 12                 # MAG-B4
OPEN_WAIT_MIN = 10             # MAG-B4
MIDDAY = (dtime(11, 30), dtime(13, 30))   # MAG-B4
ENTRY_CUTOFF_MIN = 30          # MAG-B4 (before the close)
ARM_C_TIME_STOP_MIN = 60       # MAG-B4
COIL_MIN_BARS = 2              # MAG-B5
VS_MIN_PCT = 55.0              # MAG-B6
CAP_A, CAP_B, CAP_C, CAP_ALL = 2, 1, 1, 3   # MAG-B3

EARLY_CLOSES = _SHARED_EARLY_CLOSES  # core/early_close.py (one shared table)


def session_close_dt(session_iso):
    """The session's actual close: 16:00 ET, or the named early
    close (core/early_close.py). Every clock mark derives from it."""
    d = date.fromisoformat(session_iso)
    t = EARLY_CLOSES.get(session_iso, dtime(16, 0))
    return datetime.combine(d, t, tzinfo=ET)


def _shape(raw):
    """Desk bars ({t epoch, o/h/l/c/v}) -> port bars (aware ET
    datetimes). Unparseable rows are dropped, never guessed."""
    out = []
    for b in raw or []:
        try:
            t = float(b["t"])
            out.append({
                "t": datetime.fromtimestamp(t, tz=ET),
                "open": float(b["o"]), "high": float(b["h"]),
                "low": float(b["l"]), "close": float(b["c"]),
                "volume": float(b.get("v") or 0.0)})
        except (KeyError, TypeError, ValueError):
            continue
    out.sort(key=lambda x: x["t"])
    return out


def _completed(bars, now_dt):
    return [b for b in bars if sb.close_time(b) <= now_dt]


def _today(bars, d):
    return [b for b in bars if b["t"].date() == d]


def _lvl(anchor, unit, frac, sign):
    return anchor + sign * frac * unit


def _zone_of(v):
    """The spec section 5.1 zone of a Phase Oscillator value;
    boundary inclusivity follows the port's _zone_of grid."""
    if v is None:
        return None
    if v >= 100.0:
        return "EXTREME_UP"
    if v >= 61.8:
        return "DISTRIBUTION"
    if v >= 23.6:
        return "LAUNCH_UP"
    if v > -23.6:
        return "NEUTRAL"
    if v > -61.8:
        return "LAUNCH_DOWN"
    if v > -100.0:
        return "ACCUMULATION"
    return "EXTREME_DOWN"


def _ladder(daily_completed, today, mode):
    """A frozen ladder from the port's ATR Levels: anchor =
    previous completed period's close, unit = that period's
    ATR(14). The placeholder bar appended to the daily series
    IS today (its own OHLC never enters the read — atr_levels
    takes anchor/unit from the PREVIOUS period); it exists so
    today's period key resolves in the port's period index.
    Signal bars are the placeholder alone here; the range gauge
    is read by _gauge() from today's own bars."""
    if len(daily_completed) < 15:
        return None
    prev_close = daily_completed[-1]["close"]
    placeholder = {
        "t": datetime.combine(today, dtime(0, 0), tzinfo=ET),
        "end": datetime.combine(today, dtime(16, 0), tzinfo=ET),
        "open": prev_close, "high": prev_close, "low": prev_close,
        "close": prev_close, "volume": 0.0}
    try:
        res = si.atr_levels(daily_completed + [placeholder],
                            [placeholder], mode=mode,
                            session_basis="regular")
    except Exception:
        return None
    row = res["rows"][0]
    if row.get("anchor") is None or row.get("unit") is None:
        return None
    return row


class SatyMagnum(BaseSleeve):
    CONFIG = CONFIG

    # ------------------------------------------------------------
    # frames (all port plumbing; no indicator math here)
    # ------------------------------------------------------------
    def _frames(self, extra, session_d, now_dt):
        """Every bar frame the machine reads, from the producer
        bundle. None when a load-bearing door is absent (fail
        closed: no bars, no signal)."""
        m5_long = extra.get("bars_5m_long") or {}
        m1 = extra.get("bars_1m") or {}
        if not m5_long.get(SYM):
            return None
        spy5 = sb.with_end(_shape(m5_long.get(SYM)), 5)
        spy1 = sb.with_end(_shape(m1.get(SYM)), 1)
        spy5_rth = sb.filter_session(spy5, "regular")
        spy5_ext = sb.filter_session(spy5, "extended")
        daily_rth = [b for b in sb.aggregate_daily(spy5_rth)
                     if b["t"].date() < session_d]
        h1 = sb.aggregate(spy5_rth, 60, anchor="09:30")
        m10 = sb.aggregate(spy5_rth, 10, anchor="09:30")
        m1_today = _today(spy1, session_d)
        m1_rth = sb.filter_session(m1_today, "regular")
        m3 = sb.aggregate(m1_rth, 3, anchor="09:30")
        today5 = [b for b in _today(spy5_rth, session_d)
                  if sb.close_time(b) <= now_dt]
        return {
            "daily": daily_rth,
            "h1": _completed(h1, now_dt),
            "m10": _completed(m10, now_dt),
            "m10_all": m10,
            "m1_today": m1_today, "m1_rth": m1_rth,
            "m3_today": _completed(m3, now_dt),
            "today5": today5,
            "premarket": [b for b in _today(spy5_ext, session_d)
                          if (b["t"].hour, b["t"].minute) < (9, 30)],
        }

    # ------------------------------------------------------------
    # indicator reads (port outputs only)
    # ------------------------------------------------------------
    def _pro(self, bars):
        if not bars:
            return [], []
        res = si.pivot_ribbon_pro(bars, session_basis="regular")
        return res["rows"], res["events"]

    def _po(self, bars):
        if not bars:
            return []
        return si.phase_oscillator(
            bars, session_basis="regular")["rows"]

    def _po_at(self, rows, bars, moment_dt):
        """The last completed PO row at or before a moment."""
        idx = None
        for i, b in enumerate(bars):
            if sb.close_time(b) <= moment_dt:
                idx = i
            else:
                break
        return rows[idx] if idx is not None and idx < len(rows) else None

    def _quote(self, extra, now_epoch):
        """(bid, ask, mid) from the IEX latest-quote door when
        two-sided and <= QUOTE_STALE_S old; else None (the
        po10_qqq desk convention)."""
        q = (extra.get("latest_quote") or {}).get(SYM)
        if not isinstance(q, dict) or not q.get("t"):
            return None
        try:
            t_epoch = datetime.fromisoformat(
                str(q["t"]).replace("Z", "+00:00")).timestamp()
            bp, ap = float(q["bp"]), float(q["ap"])
        except (KeyError, TypeError, ValueError):
            return None
        if now_epoch - t_epoch > QUOTE_STALE_S or bp <= 0 or ap < bp:
            return None
        return bp, ap, (bp + ap) / 2.0

    # ------------------------------------------------------------
    # the plan (spec section 4 — a pure function of completed bars)
    # ------------------------------------------------------------
    def _plan(self, frames, extra, session_d):
        day = _ladder(frames["daily"], session_d, "Day")
        if day is None:
            return None
        anchor, unit = day["anchor"], day["unit"]
        week = _ladder(frames["daily"], session_d, "Multiday")
        # range gauge: the port's own gauge over today's
        # completed 5m bars (accumulated range / day unit).
        gauge_pct, gauge_band = None, None
        if frames["today5"]:
            try:
                grows = si.atr_levels(
                    frames["daily"] + [frames["today5"][0]],
                    frames["today5"], mode="Day",
                    session_basis="regular")["rows"]
                if grows and grows[-1].get("range_pct") is not None:
                    gauge_pct = grows[-1]["range_pct"]
                    gauge_band = grows[-1]["range_band"]
            except Exception:
                gauge_pct = gauge_band = None
        if gauge_pct is None and frames["today5"]:
            hi = max(b["high"] for b in frames["today5"])
            lo = min(b["low"] for b in frames["today5"])
            gauge_pct = (hi - lo) / unit * 100.0
            gauge_band = ("LOW" if gauge_pct <= 70 else
                          "HIGH" if gauge_pct >= 90 else "MID")
        # VIX key level (MAG-B2): the prior session's ^VIX close
        # from the dated series door. Context only — never a gate.
        vix_key = None
        for row in extra.get("vix_series") or []:
            try:
                d_iso, c = str(row[0]), float(row[1])
            except (TypeError, ValueError, IndexError):
                continue
            if d_iso < session_d.isoformat():
                vix_key = c
        # intraday pivot (R42): the day level most interacted
        # with by pre-market price action, else the nearest
        # round-10 level to the pre-market/last close.
        levels = day.get("levels") or {}
        pivot = None
        pm = frames["premarket"]
        if pm and levels:
            best, best_n = None, -1
            for name, lv in levels.items():
                n = sum(1 for b in pm if b["low"] <= lv <= b["high"])
                if n > best_n:
                    best, best_n = lv, n
            pivot = best
        if pivot is None:
            ref = pm[-1]["close"] if pm else anchor
            pivot = round(ref / 10.0) * 10.0
        # weekly room (MAG-B2): the nearest weekly rung beyond
        # the day +1.000 target, per direction.
        room = {1: None, -1: None}
        if week and week.get("levels"):
            wl = sorted(week["levels"].values())
            for d in (1, -1):
                tgt = _lvl(anchor, unit, F_FULL, d)
                beyond = [x for x in wl
                          if (x > tgt if d > 0 else x < tgt)]
                if beyond:
                    room[d] = (min(beyond) if d > 0 else max(beyond))
        return {
            "anchor": anchor, "unit": unit, "levels": levels,
            "warmed": bool(day.get("warmed_up")),
            "weekly_anchor": week["anchor"] if week else None,
            "weekly_unit": week["unit"] if week else None,
            "weekly_levels": week.get("levels") if week else None,
            "range_pct": gauge_pct, "range_band": gauge_band,
            "vix_key": vix_key, "pivot": pivot, "room": room,
        }

    def _plan_stamp(self, plan):
        lv = {k: round(v, 2) for k, v in (plan["levels"] or {}).items()}
        return {
            "day_anchor": round(plan["anchor"], 2),
            "day_unit": round(plan["unit"], 2),
            "ladder": lv,
            "weekly_anchor": (round(plan["weekly_anchor"], 2)
                              if plan["weekly_anchor"] else None),
            "weekly_unit": (round(plan["weekly_unit"], 2)
                            if plan["weekly_unit"] else None),
            "range_pct": (round(plan["range_pct"], 1)
                          if plan["range_pct"] is not None else None),
            "range_band": plan["range_band"],
            "vix_key_level": (round(plan["vix_key"], 2)
                              if plan["vix_key"] else None),
            "intraday_pivot": (round(plan["pivot"], 2)
                               if plan["pivot"] else None),
        }

    # ------------------------------------------------------------
    # regime (spec section 6) + PO states (section 5)
    # ------------------------------------------------------------
    def _regime(self, frames, daily_pro, m10_pro, daily_rows_n):
        """(state, detail). TREND_UP/DOWN need BOTH frames' fast
        AND slow clouds aligned; CHOP is MIXED plus >= 3 EMA21
        crossings in the last 12 completed 10m bars (MAG-B4);
        UNKNOWN when either frame is unwarmed or unaligned-able."""
        det = {"daily": None, "m10": None,
               "conviction_last_transition": None}
        d_rows, _ = daily_pro
        m_rows, m_events = m10_pro
        if d_rows:
            r = d_rows[-1]
            det["daily"] = {
                "fast_cloud": r.get("fast_cloud"),
                "slow_cloud": r.get("slow_cloud"),
                "conviction_state": r.get("conviction_state")}
        if m_rows:
            r = m_rows[-1]
            det["m10"] = {
                "fast_cloud": r.get("fast_cloud"),
                "slow_cloud": r.get("slow_cloud"),
                "conviction_state": r.get("conviction_state")}
        for ev in reversed(m_events):
            if ev["type"] in ("CONVICTION_BULL", "CONVICTION_BEAR"):
                det["conviction_last_transition"] = {
                    "type": ev["type"],
                    "bar_close_time_et": ev["bar_close_time_et"]}
                break
        if not d_rows or not m_rows \
                or not d_rows[-1].get("warmed_up") \
                or not m_rows[-1].get("warmed_up"):
            return "UNKNOWN", det
        dfc, dsc = det["daily"]["fast_cloud"], det["daily"]["slow_cloud"]
        mfc, msc = det["m10"]["fast_cloud"], det["m10"]["slow_cloud"]
        if None in (dfc, dsc, mfc, msc):
            return "UNKNOWN", det
        if dfc and dsc and mfc and msc:
            return "TREND_UP", det
        if not dfc and not dsc and not mfc and not msc:
            return "TREND_DOWN", det
        # CHOP: price crossing the 10m EMA21 >= 3 times in the
        # last CHOP_BARS completed 10m bars.
        m10 = frames["m10"][-CHOP_BARS:]
        rows = m_rows[-CHOP_BARS:]
        signs = []
        for b, r in zip(m10, rows):
            e = r.get("ema21")
            if e is None:
                signs = []
                continue
            signs.append(1 if b["close"] >= e else -1)
        crossings = sum(1 for a, b in zip(signs, signs[1:]) if a != b)
        if crossings >= CHOP_CROSSINGS:
            return "CHOP", det
        return "MIXED", det

    def _po_stamp(self, row):
        if row is None:
            return {"value": None, "zone": None, "compression": None}
        v = row.get("phase_oscillator")
        return {"value": round(v, 2) if v is not None else None,
                "zone": _zone_of(v),
                "compression": row.get("compression_a")}

    # ------------------------------------------------------------
    # session facts from the fills door (broker truth)
    # ------------------------------------------------------------
    def _fills(self, extra):
        fills = extra.get("session_fills")
        if fills is None:
            return None
        out = []
        for f in fills:
            try:
                out.append({"position_intent": f.get("position_intent"),
                            "qty": abs(float(f.get("qty") or 0)),
                            "price": float(f.get("price") or 0)})
            except (TypeError, ValueError):
                continue
        return out

    def _session_pnl(self, extra, pos, quote):
        """Session P&L (spec 12.4): realized cash flow over this
        sleeve's fill rows (shares at x1) plus the open position
        marked at the fresh mid (at entry price when no quote —
        a neutral mark). None when the fills door is absent:
        stamped pnl_unverifiable, never guessed."""
        fills = self._fills(extra)
        if fills is None:
            return None
        cash = 0.0
        for f in fills:
            if f["position_intent"] in ("sell_to_open", "sell_to_close"):
                cash += f["qty"] * f["price"]
            elif f["position_intent"] in ("buy_to_open", "buy_to_close"):
                cash -= f["qty"] * f["price"]
        if isinstance(pos, dict) and float(pos.get("qty") or 0) != 0:
            q = float(pos["qty"])
            mark = quote[2] if quote else float(pos.get("entry_px") or 0)
            cash += q * mark
        return cash

    def _entry_counts(self, fills):
        """Open fills today, in ledger order: (total, [rows])."""
        if fills is None:
            return None, []
        opens = [f for f in fills if f["position_intent"]
                 in ("buy_to_open", "sell_to_open")]
        return len(opens), opens

    def _attribute_opens(self, events, opens):
        """Per-arm entry counts: each open fill is matched to the
        nearest-price unmatched entry event of the session
        (events carry the arm and the decision reference price);
        an unmatched open counts to the Arm A baseline (the
        section 11.1 convention). Caps are also structural —
        one Arm A entry per gate open, one Arm B entry per coil,
        one Arm C entry per episode — because the events
        themselves are one-shot."""
        counts = {"A": 0, "B": 0, "C": 0}
        used = set()
        for f in opens or []:
            best, best_d = None, None
            for i, ev in enumerate(events):
                if i in used:
                    continue
                d = abs(f["price"] - ev["ref"])
                if best_d is None or d < best_d:
                    best, best_d = i, d
            if best is not None and best_d <= max(2.0, 0.02 * f["price"]):
                used.add(best)
                counts[events[best]["arm"]] += 1
            else:
                counts["A"] += 1
        return counts

    # ------------------------------------------------------------
    # entry events: Arm A gate/retest, Arm B coil/release, Arm C
    # ------------------------------------------------------------
    def _gg_scan(self, frames, plan, m10_pro_rows, session_d):
        """The session's Golden Gate OPEN events and their
        retests (spec 8.2/8.3). Returns a list of dicts:
        {dir, open_t, gate, cancelled, retest: None|{bar, close_t}}.
        A later completed 10m close back through the origin
        trigger cancels the open before any entry."""
        anchor, unit = plan["anchor"], plan["unit"]
        m10 = frames["m10"]
        events = []
        prev_close = None
        for i, b in enumerate(m10):
            if b["t"].date() != session_d:
                prev_close = b["close"]
                continue
            for d in (1, -1):
                gate = _lvl(anchor, unit, F_GATE, d)
                beyond = b["close"] > gate if d > 0 else b["close"] < gate
                was = (prev_close > gate if d > 0
                       else prev_close < gate) if prev_close is not None \
                    else False
                if beyond and not was:
                    events.append({
                        "dir": d, "open_t": sb.close_time(b),
                        "gate": gate, "cancelled": None,
                        "retest": None, "open_idx": i})
            prev_close = b["close"]
        # cancellation + retest, per event, in time order
        m3 = frames["m3_today"]
        for ev in events:
            d = ev["dir"]
            trig = _lvl(anchor, unit, F_TRIGGER, d)
            deadline = ev["open_t"] + timedelta(seconds=RETEST_WINDOW_S)
            for b in frames["m10"]:
                ct = sb.close_time(b)
                if ct <= ev["open_t"]:
                    continue
                if (d > 0 and b["close"] < trig) or \
                        (d < 0 and b["close"] > trig):
                    ev["cancelled"] = "close_back_through_trigger"
                    break
            if ev["cancelled"]:
                continue
            # retest zone: gate level to the last completed 10m
            # EMA21 at the retest bar, whichever nearer price.
            for b in m3:
                ct = sb.close_time(b)
                if ct <= ev["open_t"] or ct > deadline:
                    continue
                row = self._pro_row_at(m10_pro_rows, frames["m10"], ct)
                e21 = row.get("ema21") if row else None
                gate = ev["gate"]
                if e21 is None or (d > 0 and e21 > gate) or \
                        (d < 0 and e21 < gate):
                    lo = hi = gate
                else:
                    lo, hi = min(gate, e21), max(gate, e21)
                reaches = b["low"] <= hi and b["high"] >= lo
                back = b["close"] > gate if d > 0 else b["close"] < gate
                if reaches and back:
                    ev["retest"] = {"bar": b, "close_t": ct}
                    break
        return events

    def _pro_row_at(self, rows, bars, moment_dt):
        idx = None
        for i, b in enumerate(bars):
            if sb.close_time(b) <= moment_dt:
                idx = i
            else:
                break
        return rows[idx] if idx is not None and idx < len(rows) else None

    def _coil_scan(self, frames, po10_rows, session_d):
        """Coils and releases on the 10m frame (spec 9.2): a run
        of >= COIL_MIN_BARS consecutive completed bars with the
        port's compression predicate true; the release is the
        FIRST bar after the run with compression false — it
        releases only if its close is beyond the coil range and
        its PO color direction agrees. Returns (coil_stamp,
        releases) with releases [{dir, bar, close_t, range_high,
        range_low, midpoint}]."""
        m10 = frames["m10"]
        stamp = {"active": False, "bars": 0, "range_high": None,
                 "range_low": None, "midpoint": None}
        releases = []
        run = 0
        run_bars = []
        for i, b in enumerate(m10):
            row = po10_rows[i] if i < len(po10_rows) else {}
            comp = row.get("compression_a")
            if comp:
                run += 1
                run_bars.append(b)
                if b["t"].date() == session_d:
                    stamp = {
                        "active": True, "bars": run,
                        "range_high": max(x["high"] for x in run_bars),
                        "range_low": min(x["low"] for x in run_bars),
                        "midpoint": (max(x["high"] for x in run_bars)
                                     + min(x["low"] for x in run_bars))
                        / 2.0}
                continue
            if run >= COIL_MIN_BARS and run_bars \
                    and run_bars[-1]["t"].date() == session_d:
                hi = max(x["high"] for x in run_bars)
                lo = min(x["low"] for x in run_bars)
                color = row.get("color_state")
                d = 0
                if b["close"] > hi and color == "POSITIVE":
                    d = 1
                elif b["close"] < lo and color == "NEGATIVE":
                    d = -1
                if d:
                    releases.append({
                        "dir": d, "bar": b,
                        "close_t": sb.close_time(b),
                        "range_high": hi, "range_low": lo,
                        "midpoint": (hi + lo) / 2.0})
            run = 0
            run_bars = []
        return stamp, releases

    def _snap_state(self, frames, po3_rows, po10_rows, po1_rows):
        """Arm C's simultaneous read (spec 10.3): the three PO
        legs on completed bars, aligned by close time onto the
        3m frame, plus the waning test and the episode count.
        Returns {legs_ok(dir), waning(dir), episodes, current} —
        evaluated for both directions; legs are SPY on all three
        frames (the SPX leg's labeled translation, section 10.2)."""
        m3 = frames["m3_today"]
        out = {"current": {1: False, -1: False},
               "waning": {1: False, -1: False}, "episodes": 0}
        if not m3 or not po3_rows:
            return out
        v10 = sb.align_values(frames["m10"],
                              [r.get("phase_oscillator")
                               for r in po10_rows], m3)
        v1 = sb.align_values(frames["h1"],
                             [r.get("phase_oscillator")
                              for r in po1_rows], m3)
        in_ep = False
        for i, b in enumerate(m3):
            v3 = po3_rows[i].get("phase_oscillator") \
                if i < len(po3_rows) else None
            a, c = v10[i], v1[i]
            if v3 is None or a is None or c is None:
                continue
            for d in (1, -1):
                ok = (v3 < SNAP_M3 and a < SNAP_M10 and c < SNAP_H1) \
                    if d > 0 else \
                    (v3 > -SNAP_M3 and a > -SNAP_M10 and c > -SNAP_H1)
                if ok and not in_ep:
                    out["episodes"] += 1
                    in_ep = True
                if i == len(m3) - 1:
                    out["current"][d] = ok
            if in_ep and (abs(v3) <= 61.8 or abs(a) <= 61.8
                          or abs(c) <= 61.8):
                in_ep = False
        if len(m3) >= 2 and len(po3_rows) >= 2:
            p, q = po3_rows[-2].get("phase_oscillator"), \
                po3_rows[-1].get("phase_oscillator")
            if p is not None and q is not None:
                out["waning"][1] = q > p     # long: momentum rising
                out["waning"][-1] = q < p    # short: momentum falling
        out["last3_close_t"] = sb.close_time(m3[-1]) if m3 else None
        return out

    # ------------------------------------------------------------
    # sizing + intent construction (spec 12, 13.2)
    # ------------------------------------------------------------
    def _size(self, equity, entry_ref, invalidation, half=False):
        """Risk-to-invalidation sizing (MAG-B3). Quantity can be
        zero — there is NO forced one-share floor (the OBS-1
        ruling): qty < 1 means no trade, stamped unaffordable."""
        if entry_ref is None or entry_ref <= 0 or invalidation is None:
            return 0
        per_share = abs(entry_ref - invalidation)
        if per_share <= 0:
            return 0
        budget = RISK_PCT * float(equity or 0.0) * (0.5 if half else 1.0)
        qty = math.floor(budget / per_share)
        cap = math.floor(NOTIONAL_CAP * float(equity or 0.0) / entry_ref)
        return max(0, min(qty, cap))

    def _enter_intent(self, arm, d, qty, quote, plan, ctx,
                      invalidation, note):
        bp, ap, mid = quote
        limit = ap if d > 0 else bp
        side = "buy" if d > 0 else "sell"
        pi = "buy_to_open" if d > 0 else "sell_to_open"
        reason = (
            f"saty_magnum enter arm={arm} "
            f"{'long' if d > 0 else 'short'}: qty={qty} "
            f"limit={limit:.2f} mid={mid:.2f} "
            f"invalidation={invalidation:.2f} "
            f"anchor={plan['anchor']:.2f} unit={plan['unit']:.2f} "
            f"{note}")
        return Intent(
            "enter", SYM, qty=int(qty), limit_price=round(limit, 2),
            price_hint=round(mid, 2), side=side, position_intent=pi,
            reason=reason, signal_date=ctx.session)

    def _exit_intent(self, qty_signed, rule, quote, ctx, market=False):
        d = 1 if qty_signed > 0 else -1
        q = abs(int(qty_signed))
        kw = {}
        if not market and quote is not None:
            limit = quote[0] if d > 0 else quote[1]
            kw["limit_price"] = round(limit, 2)
            kw["price_hint"] = round(limit, 2)
        side = "sell" if d > 0 else "buy"
        pi = "sell_to_close" if d > 0 else "buy_to_close"
        return Intent(
            "exit", SYM, qty=q, side=side, position_intent=pi,
            reason=(f"saty_magnum exit: {rule} "
                    f"{'long' if d > 0 else 'short'} qty={q}"),
            signal_date=ctx.session, **kw)

    # ------------------------------------------------------------
    # schedule (spec 13)
    # ------------------------------------------------------------
    def _schedule(self, now_dt, session_d, close_dt):
        """(entries_open_any, ab_open, reason)."""
        open_dt = datetime.combine(session_d, dtime(9, 30), tzinfo=ET) \
            + timedelta(minutes=OPEN_WAIT_MIN)
        if now_dt < open_dt:
            return False, False, "opening_wait"
        if now_dt >= close_dt - timedelta(minutes=ENTRY_CUTOFF_MIN):
            return False, False, "entry_cutoff"
        ab = not (MIDDAY[0] <= now_dt.time() < MIDDAY[1])
        return True, ab, None

    # ------------------------------------------------------------
    # position attribution + management (spec 11)
    # ------------------------------------------------------------
    def _identify(self, frames, plan, ctxs, pos, entry_dt, d):
        """Attribute the held position to its arm by replaying
        the session's entry events up to the fill (the saty_day
        precedent): the event closest before the fill owns it.
        Returns (arm, event) or (None, None)."""
        cands = []
        for ev in ctxs["gg_events"]:
            if ev["dir"] == d and ev.get("retest") \
                    and ev["retest"]["close_t"] <= entry_dt \
                    + timedelta(seconds=300):
                cands.append((ev["retest"]["close_t"], "A", ev))
        for rel in ctxs["releases"]:
            if rel["dir"] == d and rel["close_t"] <= entry_dt \
                    + timedelta(seconds=300):
                cands.append((rel["close_t"], "B", rel))
        # Arm C is attributed by the snap state AT the fill:
        # replay the three legs over the bars completed by
        # entry_dt (the current pass's read may already have
        # recovered — that recovery is the exit, not evidence
        # the position was never a snap).
        m3e = [b for b in (frames.get("m3_today") or [])
               if sb.close_time(b) <= entry_dt]
        m10e = [b for b in (frames.get("m10") or [])
                if sb.close_time(b) <= entry_dt]
        h1e = [b for b in (frames.get("h1") or [])
               if sb.close_time(b) <= entry_dt]
        if not m3e and ctxs.get("snap", {}).get("current", {}).get(d):
            cands.append((entry_dt, "C", None))
        if m3e:
            snap_e = self._snap_state(
                {"m3_today": m3e, "m10": m10e, "h1": h1e},
                self._po(m3e), self._po(m10e), self._po(h1e))
            if snap_e["current"][d]:
                cands.append((sb.close_time(m3e[-1]), "C", None))
        if not cands:
            return None, None
        cands.sort(key=lambda x: abs((entry_dt - x[0]).total_seconds()))
        return cands[0][1], cands[0][2]

    def _stations(self, arm, plan, d, weekly_room_ok):
        """The station ladder for an arm (spec 11.3): list of
        (fraction, kind) in path order. kind: 'third' exits a
        third of the ORIGINAL quantity; 'be' also migrates the
        runner's invalidation to break-even; 'half_runner' exits
        half the runner; 'all' exits everything left."""
        if arm == "B":
            return [(F_MID, "third"), (F_TARGET, "third_be"),
                    (F_FULL, "half_runner"), (F_SQUEEZE, "all")]
        s3 = F_EXT if weekly_room_ok else F_FULL
        return [(F_MID, "third"), (F_TARGET, "third_be"), (s3, "all")]

    def _manage(self, frames, plan, ctxs, pos, extra, ctx, now_dt,
                stamp):
        anchor, unit = plan["anchor"], plan["unit"]
        close_dt = session_close_dt(ctx.session)
        qty_signed = float(pos.get("qty") or 0)
        d = 1 if qty_signed > 0 else -1
        qty = abs(qty_signed)
        entry_px = float(pos.get("entry_px") or 0)
        fill_t = float(pos.get("fill_t") or pos.get("entry_t") or 0)
        entry_dt = datetime.fromtimestamp(fill_t, tz=ET) \
            if fill_t else now_dt
        quote = self._quote(extra, ctx.now)
        stamp["position"] = {"qty": qty_signed, "direction": d,
                             "entry_px": entry_px or None,
                             "arm": None}
        # overnight survivor: flattened at the first evaluation
        held_from = str(pos.get("signal_date")
                        or pos.get("entry_date") or "")
        if held_from and held_from != ctx.session:
            stamp["decision"] = "overnight_flat"
            return [self._exit_intent(qty_signed, "overnight_flat",
                                      None, ctx, market=True)]
        # EOD flat (close - 5m): unpriced, on the market door
        if now_dt >= close_dt - timedelta(minutes=5):
            stamp["decision"] = "eod_flat"
            return [self._exit_intent(qty_signed, "eod_flat",
                                      None, ctx, market=True)]
        arm, ev = self._identify(frames, plan, ctxs, pos, entry_dt, d)
        if arm is None:
            arm = "A"
            stamp["ownership_mismatch"] = True
        stamp["position"]["arm"] = arm
        # original quantity + stations done, from the trade's own
        # fill partition (one position at a time: walk the fills,
        # a partition closes when its net returns to zero).
        fills = self._fills(extra) or []
        orig_qty, exited = qty, 0.0
        net = 0.0
        part_open = part_close = 0.0
        for f in fills:
            if f["position_intent"] in ("buy_to_open", "sell_to_open"):
                if net == 0:
                    part_open, part_close = 0.0, 0.0
                part_open += f["qty"]
                net += f["qty"] if f["position_intent"] == "buy_to_open" \
                    else -f["qty"]
            elif f["position_intent"] in ("buy_to_close", "sell_to_close"):
                part_close += f["qty"]
                net += f["qty"] if f["position_intent"] == "buy_to_close" \
                    else -f["qty"]
        if part_open > 0:
            orig_qty, exited = part_open, part_close
        stamp["position"]["orig_qty"] = orig_qty
        stamp["position"]["exited_qty"] = exited

        def priced(q_signed, rule):
            """A priced exit needs the fresh quote; without it the
            decision stays pending (filed), never dropped (13.2)."""
            if quote is None:
                stamp["exit_pending_no_quote"] = rule
                return []
            return [self._exit_intent(q_signed, rule, quote, ctx)]

        m10 = frames["m10"]
        m10_today = [b for b in m10 if b["t"].date()
                     == date.fromisoformat(ctx.session)]
        since = [b for b in frames["m1_rth"]
                 if sb.close_time(b) > entry_dt]

        # warnings: filed, never acted on (spec 11.7)
        self._warnings(frames, ctxs, d, entry_dt, stamp)

        if arm == "C":
            # (a) 10m PO re-enters the launch/neutral band
            row10 = ctxs["po10_rows"][-1] if ctxs["po10_rows"] else None
            v10 = row10.get("phase_oscillator") if row10 else None
            if v10 is not None and ((d > 0 and v10 >= -23.6)
                                    or (d < 0 and v10 <= 23.6)):
                stamp["decision"] = "snap_exit_zone_reentry"
                return priced(qty_signed, "snap_exit_zone_reentry")
            # (b) a completed 10m close beyond the opposite trigger
            opp = _lvl(anchor, unit, F_TRIGGER, -d)
            for b in m10_today:
                if sb.close_time(b) <= entry_dt:
                    continue
                if (d > 0 and b["close"] < opp) or \
                        (d < 0 and b["close"] > opp):
                    stamp["decision"] = "snap_exit_opposite_trigger"
                    return priced(qty_signed,
                                  "snap_exit_opposite_trigger")
            # (c) the 60-minute time stop (MAG-B4)
            if (now_dt - entry_dt).total_seconds() >= \
                    ARM_C_TIME_STOP_MIN * 60:
                stamp["decision"] = "snap_exit_time_stop"
                return priced(qty_signed, "snap_exit_time_stop")
            return []

        # invalidation level for this arm (spec 11.2)
        if arm == "B":
            inv = ev["midpoint"] if ev else None
            if inv is None:
                inv = _lvl(anchor, unit, F_TRIGGER, d)
        else:
            inv = _lvl(anchor, unit, F_TRIGGER, d)
        stamp["position"]["invalidation_level"] = round(inv, 2)
        # kill: a completed 10m close back through the level
        # (equality does NOT breach — MAG-B5)
        for b in m10_today:
            if sb.close_time(b) <= entry_dt:
                continue
            if (d > 0 and b["close"] < inv) or \
                    (d < 0 and b["close"] > inv):
                stamp["decision"] = "kill"
                return priced(qty_signed,
                              "kill_10m_close_through_invalidation")
        # stations, in path order (far stations checked only
        # after nearer ones have fired — one per pass)
        room_ok = False
        if arm == "A":
            rung = plan["room"].get(d)
            ext_lvl = _lvl(anchor, unit, F_EXT, d)
            room_ok = rung is not None and \
                ((d > 0 and rung > ext_lvl) or (d < 0 and rung < ext_lvl))
        stations = self._stations(arm, plan, d, room_ok)
        # planned exit quantity per station (whole shares; the
        # "all" station takes whatever remains)
        planned = []
        runner = orig_qty
        for frac, kind in stations:
            if kind in ("third", "third_be"):
                q = int(orig_qty // 3)
            elif kind == "half_runner":
                q = int(runner // 2)
            else:
                q = None
            planned.append(q)
            if q:
                runner -= q
        # stations done, from the exited quantity against the
        # cumulative planned exits (the trade's own fill record)
        done = 0
        acc = 0
        for q in planned:
            if q is None:
                break
            acc += q
            if exited >= acc - 0.5:
                done += 1
            else:
                break
        stamp["position"]["stations_done"] = done
        # break-even migration: after S2, a completed 10m close
        # back through the ENTRY price exits the rest
        be_done = done >= 2
        if be_done and entry_px:
            for b in m10_today:
                if sb.close_time(b) <= entry_dt:
                    continue
                if (d > 0 and b["close"] < entry_px) or \
                        (d < 0 and b["close"] > entry_px):
                    stamp["decision"] = "runner_breakeven_exit"
                    return priced(qty_signed, "runner_breakeven_exit")
        if done < len(stations):
            frac, kind = stations[done]
            lvl = _lvl(anchor, unit, frac, d)
            touched = any(
                (b["high"] >= lvl if d > 0 else b["low"] <= lvl)
                for b in since)
            if touched:
                q = planned[done]
                if q is None:
                    q = int(qty)
                q = max(1, min(int(q), int(qty)))
                if q > 0:
                    stamp["decision"] = f"station_s{done + 1}"
                    return priced(d * q, f"station_s{done + 1}_"
                                  f"at_{frac:.3f}")
        return []

    def _warnings(self, frames, ctxs, d, entry_dt, stamp):
        """1h EMA21 / 10m Pro EMA48 breaks against the position —
        filed, never acted on (spec 11.7; the desk's R-5 pattern)."""
        h1 = frames["h1"]
        if h1:
            from core import saty_primitives as sp
            e21 = sp.ema_series([b["close"] for b in h1], 21)
            for i, b in enumerate(h1):
                if sb.close_time(b) <= entry_dt or e21[i] is None:
                    continue
                if (d > 0 and b["close"] < e21[i]) or \
                        (d < 0 and b["close"] > e21[i]):
                    stamp["warning_1h_ema21_break"] = True
                    break
        rows = ctxs["m10_pro_rows"]
        for i, b in enumerate(frames["m10"]):
            if sb.close_time(b) <= entry_dt or i >= len(rows):
                continue
            e48 = rows[i].get("ema48")
            if e48 is None:
                continue
            if (d > 0 and b["close"] < e48) or \
                    (d < 0 and b["close"] > e48):
                stamp["warning_10m_ema48_break"] = True
                break

    def _blocked_exit(self, extra, ctx, now_dt, stamp):
        """Spec 11.6 (the D-B1 pattern): a held position gets its
        time-based exits even when data/warmup gates block
        everything else — the EOD flat and the overnight flat
        need no bars, no ladder and no quote, and go out unpriced
        on the market/EOD door."""
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYM) or {}).get("position")
        if not isinstance(pos, dict) \
                or float(pos.get("qty") or 0) == 0:
            return []
        qty_signed = float(pos["qty"])
        held_from = str(pos.get("signal_date")
                        or pos.get("entry_date") or "")
        overnight = bool(held_from) and held_from != ctx.session
        close_dt = session_close_dt(ctx.session)
        if overnight:
            rule = "overnight_flat_blocked_data"
        elif now_dt >= close_dt - timedelta(minutes=5):
            rule = "eod_flat_blocked_data"
        else:
            return []
        stamp["state"] = "blocked_data"
        stamp["decision"] = rule
        stamp["position"] = {"qty": qty_signed}
        return [self._exit_intent(qty_signed, rule, None, ctx,
                                  market=True)]

    # ------------------------------------------------------------
    # the evaluation (spec section 7 — fixed order)
    # ------------------------------------------------------------
    def signal(self, bars, slice_state, ctx):
        stamp = {"sleeve": "saty_magnum", "session": ctx.session,
                 "state": "armed", "plan": None, "regime": None,
                 "po": None, "volume_stack": None, "gg": None,
                 "coil": None, "spot": None, "decision": None,
                 "stood_down": None, "position": None,
                 "session_pnl": "unavailable",
                 "entries_today": {"A": 0, "B": 0, "C": 0}}
        self.last_evaluation = stamp
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        session_d = date.fromisoformat(ctx.session)
        # 1. calendar
        if not is_trading_day(session_d):
            stamp["state"] = "not_a_trading_day"
            return []
        extra = ctx.extra or {}
        # 2. data
        frames = self._frames(extra, session_d, now_dt)
        if frames is None:
            stamp["state"] = "blocked_data"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        frames["session_d"] = session_d
        # 3. plan
        plan = self._plan(frames, extra, session_d)
        if plan is None:
            stamp["state"] = "blocked_data"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        stamp["plan"] = self._plan_stamp(plan)
        if not plan["warmed"]:
            stamp["state"] = "blocked_warmup"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        # indicator frames
        daily_pro = self._pro(frames["daily"])
        m10_pro = self._pro(frames["m10"])
        po10_rows = self._po(frames["m10"])
        po1_rows = self._po(frames["h1"])
        po3_rows = self._po(frames["m3_today"])
        po_daily_rows = self._po(frames["daily"])
        regime, reg_det = self._regime(frames, daily_pro, m10_pro,
                                       len(frames["daily"]))
        stamp["regime"] = {"state": regime, **reg_det}
        stamp["po"] = {
            "m3": self._po_stamp(po3_rows[-1] if po3_rows else None),
            "m10": self._po_stamp(po10_rows[-1] if po10_rows else None),
            "h1": self._po_stamp(po1_rows[-1] if po1_rows else None),
            "daily": self._po_stamp(
                po_daily_rows[-1] if po_daily_rows else None)}
        ctxs = {"daily_pro": daily_pro, "m10_pro": m10_pro,
                "m10_pro_rows": m10_pro[0], "po10_rows": po10_rows,
                "po1_rows": po1_rows, "po3_rows": po3_rows}
        # entry events (replayed deterministically every pass)
        gg_events = self._gg_scan(frames, plan, m10_pro[0], session_d)
        ctxs["gg_events"] = gg_events
        coil_stamp, releases = self._coil_scan(frames, po10_rows,
                                               session_d)
        ctxs["releases"] = releases
        stamp["coil"] = {
            "active": coil_stamp["active"], "bars": coil_stamp["bars"],
            "range_high": (round(coil_stamp["range_high"], 2)
                           if coil_stamp["range_high"] else None),
            "range_low": (round(coil_stamp["range_low"], 2)
                          if coil_stamp["range_low"] else None),
            "midpoint": (round(coil_stamp["midpoint"], 2)
                         if coil_stamp["midpoint"] else None)}
        snap = self._snap_state(frames, po3_rows, po10_rows, po1_rows)
        ctxs["snap"] = snap
        gg_live = next((e for e in gg_events if not e["cancelled"]),
                       None)
        stamp["gg"] = {
            "open": ({"dir": gg_live["dir"],
                      "bar_close_t": gg_live["open_t"].isoformat(),
                      "gate_level": round(gg_live["gate"], 2)}
                     if gg_live else None),
            "retest_deadline": (
                (gg_live["open_t"]
                 + timedelta(seconds=RETEST_WINDOW_S)).isoformat()
                if gg_live else None),
            "cancelled": (gg_events[0]["cancelled"]
                          if gg_events and gg_events[0]["cancelled"]
                          else None)}
        quote = self._quote(extra, ctx.now)
        if quote:
            stamp["spot"] = round(quote[2], 2)
        # session P&L + position (steps 4-5)
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYM) or {}).get("position")
        pnl = self._session_pnl(extra, pos, quote)
        stamp["session_pnl"] = (round(pnl, 2) if pnl is not None
                                else "unavailable")
        if isinstance(pos, dict) and float(pos.get("qty") or 0) != 0:
            return self._manage(frames, plan, ctxs, pos, extra, ctx,
                                now_dt, stamp)
        if regime == "UNKNOWN":
            stamp["state"] = "blocked_warmup"
            stamp["stood_down"] = "regime_unknown"
            return []
        # entry counts (fills are broker truth)
        fills = self._fills(extra)
        total_opens, opens = self._entry_counts(fills)
        if total_opens is None:
            stamp["stood_down"] = "pnl_unverifiable"
            stamp["fills_unavailable"] = True
            return []
        events = []
        for e in gg_events:
            if e.get("retest"):
                events.append({"arm": "A", "t": e["retest"]["close_t"],
                               "ref": e["retest"]["bar"]["close"]})
        for r in releases:
            events.append({"arm": "B", "t": r["close_t"],
                           "ref": r["bar"]["close"]})
        events.sort(key=lambda x: x["t"])
        counts = self._attribute_opens(events, opens)
        # Arm C opens attribute by episode (no price signature):
        # any opens beyond the A/B-attributed count in a session
        # with snap episodes are C's, bounded by episodes.
        attributed = counts["A"] + counts["B"]
        if snap["episodes"] and total_opens > attributed:
            counts["C"] = min(total_opens - attributed,
                               snap["episodes"])
            counts["A"] = max(0, counts["A"]
                              - (total_opens - attributed
                                 - counts["C"]))
        stamp["entries_today"] = counts
        # 5. session stop (the sleeve's own, MAG-B3)
        if pnl is not None and pnl <= -SESSION_STOP_PCT * float(
                ctx.equity or 0.0):
            stamp["stood_down"] = "session_stop"
            return []
        if total_opens >= CAP_ALL:
            stamp["stood_down"] = "entry_cap_session"
            return []
        # schedule
        close_dt = session_close_dt(ctx.session)
        any_open, ab_open, why = self._schedule(now_dt, session_d,
                                                close_dt)
        if not any_open:
            stamp["stood_down"] = why
            if now_dt < datetime.combine(session_d, dtime(9, 30),
                                         tzinfo=ET):
                stamp["state"] = "armed_preopen"
            return []
        red = plan["range_pct"] is not None and plan["range_pct"] >= 90.0

        # -- Arm C first (its extremes are perishable) -----------
        intent = self._arm_c(frames, plan, ctxs, snap, counts, quote,
                             extra, ctx, now_dt, stamp)
        if intent is not None:
            return [intent]
        # -- Arm B (a coiled release outranks a waiting gate) ----
        if ab_open and not red:
            intent = self._arm_b(frames, plan, ctxs, counts, quote,
                                 ctx, now_dt, stamp)
            if intent is not None:
                return [intent]
        elif not ab_open:
            if not stamp["stood_down"]:
                stamp["stood_down"] = "midday_stand_down"
        elif red:
            if not stamp["stood_down"]:
                stamp["stood_down"] = "range_gauge_red"
        # -- Arm A (Golden Gate continuation) ---------------------
        if ab_open and not red:
            intent = self._arm_a(frames, plan, ctxs, gg_events,
                                 counts, quote, extra, ctx, now_dt,
                                 stamp, regime)
            if intent is not None:
                return [intent]
        return []

    # ------------------------------------------------------------
    # Arm C — snap-back (spec 10)
    # ------------------------------------------------------------
    def _arm_c(self, frames, plan, ctxs, snap, counts, quote, extra,
               ctx, now_dt, stamp):
        if counts["C"] >= CAP_C and snap["episodes"] <= counts["C"]:
            return None
        for d in (1, -1):
            if not snap["current"][d] or not snap["waning"][d]:
                continue
            # one entry per episode: entries used vs episodes seen
            if counts["C"] >= snap["episodes"]:
                stamp["stood_down"] = "snap_episode_used"
                return None
            last3 = snap.get("last3_close_t")
            if last3 is not None and \
                    (now_dt - last3).total_seconds() > FRESH_S:
                stamp["stood_down"] = "snap_stale"
                return None
            if quote is None:
                stamp["stood_down"] = "no_quote"
                return None
            inv = _lvl(plan["anchor"], plan["unit"], F_TRIGGER, -d)
            qty = self._size(ctx.equity, quote[2], inv, half=True)
            if qty < 1:
                stamp["stood_down"] = "unaffordable"
                return None
            stamp["decision"] = f"snap_enter_{d:+d}"
            return self._enter_intent(
                "C", d, qty, quote, plan, ctx, inv,
                "snap-back: 3m/10m PO beyond -100, 1h beyond -80 "
                "(SPY legs), momentum waning, half size")
        return None

    # ------------------------------------------------------------
    # Arm B — compression release (spec 9)
    # ------------------------------------------------------------
    def _arm_b(self, frames, plan, ctxs, counts, quote, ctx, now_dt,
               stamp):
        if counts["B"] >= CAP_B:
            return None
        m10_rows, _ = ctxs["m10_pro"]
        regime = stamp["regime"]["state"]
        for rel in ctxs["releases"]:
            age = (now_dt - rel["close_t"]).total_seconds()
            if age > FRESH_S or age < -60:
                continue
            d = rel["dir"]
            # ribbon not opposed: 10m clouds not BOTH against d,
            # daily regime not the full opposite trend
            row = m10_rows[-1] if m10_rows else {}
            fc, sc = row.get("fast_cloud"), row.get("slow_cloud")
            if fc is not None and sc is not None:
                both_against = (not fc and not sc) if d > 0 \
                    else (fc and sc)
                if both_against:
                    stamp["stood_down"] = "release_ribbon_opposed"
                    return None
            if (d > 0 and regime == "TREND_DOWN") or \
                    (d < 0 and regime == "TREND_UP"):
                stamp["stood_down"] = "release_regime_opposed"
                return None
            if quote is None:
                stamp["stood_down"] = "no_quote"
                return None
            qty = self._size(ctx.equity, quote[2], rel["midpoint"])
            if qty < 1:
                stamp["stood_down"] = "unaffordable"
                return None
            stamp["decision"] = f"coil_enter_{d:+d}"
            return self._enter_intent(
                "B", d, qty, quote, plan, ctx, rel["midpoint"],
                f"compression release: coil range "
                f"{rel['range_low']:.2f}-{rel['range_high']:.2f} "
                f"midpoint stop")
        return None

    # ------------------------------------------------------------
    # Arm A — Golden Gate continuation (spec 8)
    # ------------------------------------------------------------
    def _arm_a(self, frames, plan, ctxs, gg_events, counts, quote,
               extra, ctx, now_dt, stamp, regime):
        if counts["A"] >= CAP_A:
            return None
        anchor, unit = plan["anchor"], plan["unit"]
        po10_rows, po1_rows = ctxs["po10_rows"], ctxs["po1_rows"]
        for ev_i, ev in enumerate(gg_events):
            if ev["cancelled"] or not ev.get("retest"):
                continue
            d = ev["dir"]
            # one entry per gate open: attributed Arm A opens
            # consume the session's gate opens in order, so an
            # open whose index is below the attributed count has
            # already fired; a second entry needs a FRESH gate
            # open (a later event) after the first trade
            # completed — and this code only runs while flat.
            if ev_i < counts["A"]:
                continue
            rt = ev["retest"]
            age = (now_dt - rt["close_t"]).total_seconds()
            if age > FRESH_S or age < -60:
                stamp["stood_down"] = "retest_stale"
                continue
            # regime must be the tradeable trend for d
            want = "TREND_UP" if d > 0 else "TREND_DOWN"
            if regime != want:
                stamp["stood_down"] = "regime_not_trend"
                return None
            # PO gate (8.4): 10m not counter-extreme; 1h zone
            # must not oppose
            r10 = po10_rows[-1] if po10_rows else None
            v10 = r10.get("phase_oscillator") if r10 else None
            if v10 is not None:
                if (d > 0 and _zone_of(v10) == "EXTREME_DOWN") or \
                        (d < 0 and _zone_of(v10) == "EXTREME_UP"):
                    stamp["stood_down"] = "po_counter_extreme"
                    return None
            r1 = po1_rows[-1] if po1_rows else None
            v1 = r1.get("phase_oscillator") if r1 else None
            if v1 is not None:
                z1 = _zone_of(v1)
                if (d > 0 and z1 in ("ACCUMULATION", "EXTREME_DOWN")) \
                        or (d < 0 and z1 in ("DISTRIBUTION",
                                             "EXTREME_UP")):
                    stamp["stood_down"] = "po_1h_opposes"
                    return None
            # Volume Stack confirmation on the retest bar (MAG-B6)
            vs = si.volume_stack(frames["m3_today"])["rows"]
            m3 = frames["m3_today"]
            idx = None
            for i, b in enumerate(m3):
                if sb.close_time(b) == rt["close_t"]:
                    idx = i
                    break
            if idx is None or idx >= len(vs):
                stamp["volume_stack"] = {"m3_winner": None,
                                         "m3_buy_pct": None,
                                         "m3_sell_pct": None}
                stamp["stood_down"] = "vs_unavailable"
                return None
            row = vs[idx]
            bpct, spct = row.get("buy_pct"), row.get("sell_pct")
            stamp["volume_stack"] = {
                "m3_winner": row.get("winner"),
                "m3_buy_pct": (round(bpct, 1) if bpct is not None
                               and not math.isnan(bpct) else None),
                "m3_sell_pct": (round(spct, 1) if spct is not None
                                and not math.isnan(spct) else None)}
            win_pct = bpct if d > 0 else spct
            want_winner = "BUY" if d > 0 else "SELL"
            if bpct is None or spct is None \
                    or math.isnan(bpct) or math.isnan(spct) \
                    or win_pct is None or math.isnan(win_pct):
                # a zero-range bar (the original's unguarded
                # division yields NaN) = confirmation absent
                stamp["stood_down"] = "vs_unavailable"
                return None
            if row.get("winner") != want_winner \
                    or win_pct < VS_MIN_PCT:
                stamp["stood_down"] = "vs_no_confirm"
                return None
            if quote is None:
                stamp["stood_down"] = "no_quote"
                return None
            inv = _lvl(anchor, unit, F_TRIGGER, d)
            qty = self._size(ctx.equity, quote[2], inv)
            if qty < 1:
                stamp["stood_down"] = "unaffordable"
                return None
            stamp["decision"] = f"gg_enter_{d:+d}"
            return self._enter_intent(
                "A", d, qty, quote, plan, ctx, inv,
                "golden gate: 10m close through the 38.2% gate, "
                "3m retest held, volume stack confirmed")
        return None


def signal(bars, slice_state, context):
    return SatyMagnum().signal(bars, slice_state, context)
