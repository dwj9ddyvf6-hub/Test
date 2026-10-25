"""saty_day — Milkman's SATY day-trading system (Golden Gate /
Bilbo GG / Trigger Box) on SPY options, automated for the lean
paper desk from AUTOMATION-DESIGN.md (2026-10-21).

THE SYSTEM IN ONE PARAGRAPH. Before the open, the day ladder is
frozen from the previous completed REGULAR-session daily bar:
anchor = that close, unit = its ATR(14); levels at anchor +/-
unit x {0.236 trigger, 0.382 Golden Gate open, 0.500 midpoint,
0.618 primary target, 0.786 and 1.000 runner stations}. A Golden
Gate trade enters when price touches the +/-38.2% level, gated by
the last COMPLETED 1-hour Phase Oscillator (an aligned extreme
zone tags the trade Bilbo and earns runner rights; the opposite
extreme blocks it; mid-zone is a plain Golden Gate), by the 10m
Pivot Ribbon Pro (a full opposing stack or a chop read stands the
trade down), and by SPX/NQ confluence (QQQ is the desk's Nasdaq
proxy: no Golden Gate entry without QQQ moving the same way).
A Trigger Box trade enters when the day opens inside the trigger
box and a 3-minute bar CLOSES beyond a trigger. Exits are keyed
to the underlying's bar closes and level touches, never to the
option premium: a 10-minute close back through the 23.6% trigger
kills a Golden Gate position; half comes off at the midpoint;
the rest exits at 61.8% unless Bilbo or trend runner rights keep
a runner to 78.6% and the full ATR. Everything is flat by the
close. While the day is range-bound, the same levels also offer
range scalps in the opposite posture (fade the 38.2% touch
toward the opposite 38.2% level, out on a range break) — his
stated home turf in his posts, at ladder-native defaults.

SIZING, STATED PLAINLY (design section 7, as corrected by
Milkman himself, 2026-10-21). He publishes no per-trade risk %
and no dollar risk per trade. He DOES run one daily stop, in
his own words: "Once I'm down $10K, good sign to stop trading."
That stop is sleeve-internal strategy logic here, not a desk
veto: when this sleeve's session P&L (broker truth — the desk
ledger's fill rows for this sleeve, realized plus the open
position marked at the current mid) reaches -$10,000, no new
entries are taken for the rest of the session; exits, kills and
the end-of-day flat continue normally. The $10,000 figure is
his, used as stated, unscaled. Beyond that stop, the only
brakes are his own rules — the entry windows, the kills, one
position per signal, no adds. The desk operationalization
(DESK-CHOICE D-14) sizes each trade at a premium budget of 4% of
this sleeve's slice equity (his Bilbo worked figure inside his
published 3-5% range), 1 contract minimum, exact quantity on the
intent, midday bull Golden Gates at half size (his decay table).

INSTRUMENT (his answer, 2026-10-21): "SPX 0dte — usually at the
money or close to it." SPX is not tradeable on Alpaca, so the
expression is SPY options expiring the SAME DAY (0 DTE), strike
at-the-money or the nearest listed strike to the spot. No
same-day expiry listed = no trade; no other expiry is ever
substituted. This supersedes the design's 2-4 DTE window and
its 0DTE exclusion. He also confirmed he watches both SPX (RTH)
and ES (ETH) at the same time: the regular-session ladder is
the trading basis, and the extended-session ladder is computed
and filed daily as his ETH watch — it never trades. And the
confluence filter is his, confirmed in his words: it is not
about levels — NQ also breaking out is what decides whether an
SPX breakout is real or likely fake; a breakout without it is
treated as likely fake and not entered.

DESK SHAPE. CONFIG + signal() in the bilbo_options idiom: the
sleeve is a pure function of the bars and broker state it is
handed (the desk is process-per-pass; there is no memory between
evaluations, so the whole day — plan, touches, gate reads,
stations — is deterministically reconstructed from completed
bars on every tick, and position facts come from the broker's
position record, which is truth). Indicator math comes only from
the port (core/saty_bars, core/saty_indicators); the sleeve never
re-derives an indicator and never consults the Volume Stack for
a decision (excluded by construction, design section 8). Every
decision — arm, touch, gate result, stand-down, order, partial,
kill, exit — is stamped onto self.last_evaluation, which the
dispatcher merges into the evaluation ledger row (the filing
door); intents themselves are filed through the Ink intent door
at dispatch. No bars = no signal: missing data stands the sleeve
down for the day, it never guesses.

ORDER MECHANICS NOTE. Entry/exit intents carry the OCC in the
reason (the desk's proven options door, bilbo_options C-1b):
qty exact, limit at the quoted mid, position_intent buy_to_open /
sell_to_close. Intent.stop/target are deliberately NOT set: on
this desk those fields feed the broker protection-stop path,
and this system's invalidation is an underlying CLOSE rule, not
a resting premium stop (his rule: exits keyed to the stock,
never the premium). The kill/target levels ride the reason text
and the evaluation stamp instead.
"""
import math
import re
from datetime import date, datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

from core.data import is_trading_day
from core.early_close import EARLY_CLOSES as _SHARED_EARLY_CLOSES
from core.sleeve import BaseSleeve, Intent, SleeveConfig
from core import saty_bars as sb
from core import saty_indicators as si
from core import saty_primitives as sp

ET = ZoneInfo("America/New_York")
SYM = "SPY"
BENCH = "QQQ"          # the desk's Nasdaq proxy for SPX/NQ confluence

CONFIG = SleeveConfig(
    sleeve_id="saty_day",
    cadence_s=60,
    universe=("SPY",),
    state_schema={"position": "dict|None"},
    risk_pct=0.04,
)

# -- his numbers (design sections 1, 3-6; MILKMAN-X-EXECUTION) ----
F_TRIGGER = 0.236
F_GATE = 0.382
F_MID = 0.500
F_TARGET = 0.618
F_RUNNER = 0.786
F_FULL = 1.000
PO_EXTREME = 61.8              # Bilbo gate zones (design 4.4)
SPREAD_GATE = 0.05             # desk options convention (bilbo)
QUOTE_STALE_S = 60.0           # D-3
BUDGET_PCT = 0.04              # D-14 (his 3-5% range, worked 4%)
# Milkman's own answer (2026-10-21 20:52 ET, relayed mid-build):
# "SPX 0dte - usually at the money or close to it." The expiry
# rule is now same-day expiry ONLY (0 DTE); the 2-4 DTE window
# and the design's 0DTE exclusion are both superseded. SPX is
# not tradeable on Alpaca, so the expression stays SPY options.
EXPIRY_DTE = 0
DAILY_STOP_USD = 10000.0       # his daily stop, as stated (below)
ENTRY_FRESH_S = 1800.0         # one scan cycle: a touch is fired by
                               # at most one entry-submitting tick
STATION_FRESH_S = 600.0        # two exit sweeps for halving stations
RANGE_LOW_PCT = 70.0           # port range gauge LOW band (SPEC 5.1)
RANGE_HIGH_PCT = 90.0          # port range gauge HIGH band

# NYSE early closes (13:00 ET) the sleeve's clock keys off
# (DESK-CHOICE D-16). Named, dated maintenance: extend yearly.
# Days the exchange is fully closed are the calendar's business
# (core.data.is_trading_day); this table holds only early closes.
EARLY_CLOSES = _SHARED_EARLY_CLOSES  # core/early_close.py (D-B3 cure: one shared table)

_OCC_RE = re.compile(r"^([A-Z.\\-]{1,6})(\d{6})([CP])(\d{8})$")


def parse_occ(occ):
    m = _OCC_RE.match(str(occ or ""))
    if not m:
        return None
    return {"underlying": m.group(1), "kind": m.group(3),
            "strike": int(m.group(4)) / 1000.0}


def session_close_dt(session_iso):
    """The session's actual close (D-16): 16:00 ET, or the named
    early close. All of the day's clock marks derive from it."""
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


def _touch_bar(bars, level, direction):
    """First bar whose range touches `level` in `direction`
    (+1: high reaches up to it; -1: low reaches down to it)."""
    for b in bars:
        if direction > 0 and b["high"] >= level:
            return b
        if direction < 0 and b["low"] <= level:
            return b
    return None


def _run_len(states, idx):
    """Length of the run of equal states ending at idx (None
    breaks a run)."""
    if idx < 0 or states[idx] is None:
        return 0
    v, n, i = states[idx], 0, idx
    while i >= 0 and states[i] == v:
        n += 1
        i -= 1
    return n


def _ladder(daily_completed, today, basis):
    """The frozen Day-mode ladder (design 3.3) from the port's
    ATR Levels: anchor = previous completed daily close, unit =
    that period's ATR(14). Returns the port row (anchor, unit,
    levels, warmed_up) or None when the ladder cannot form.
    The placeholder bar appended to the daily series IS today
    (its own OHLC never enters the read — atr_levels takes the
    anchor/unit from the PREVIOUS period); it exists so today's
    period key resolves in the port's period index."""
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
                            [placeholder], mode="Day",
                            session_basis=basis)
    except Exception:
        return None
    row = res["rows"][0]
    if row.get("anchor") is None or row.get("unit") is None:
        return None
    return row


def _quote_ok(fresh, now_epoch):
    """(mid, bid, ask) when a fresh-quotes-door row is two-sided,
    inside the spread gate, and <= QUOTE_STALE_S old (D-3);
    else None. `fresh` rows are the quotes/latest door's shape
    ({bp, ap, t ISO, received_at})."""
    if not isinstance(fresh, dict):
        return None
    bp, ap = fresh.get("bp"), fresh.get("ap")
    if bp is None or ap is None:
        return None
    bp, ap = float(bp), float(ap)
    if bp <= 0 or ap < bp:
        return None
    mid = (bp + ap) / 2.0
    if mid <= 0 or (ap - bp) / mid > SPREAD_GATE:
        return None
    t = fresh.get("t")
    if not t:
        return None
    try:
        t_epoch = datetime.fromisoformat(
            str(t).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None
    if now_epoch - t_epoch > QUOTE_STALE_S:
        return None
    return mid, bp, ap


def _snap_mid(quotes, occ):
    """(mid, bid, ask) from the snapshot door's quotes map
    ({occ: {bid, ask}}); exits price from this door (design 5)."""
    q = (quotes or {}).get(occ)
    if not isinstance(q, dict):
        return None
    bid, ask = q.get("bid"), q.get("ask")
    if bid is None or ask is None:
        return None
    bid, ask = float(bid), float(ask)
    if bid <= 0 or ask < bid:
        return None
    return (bid + ask) / 2.0, bid, ask


class SatyDay(BaseSleeve):
    CONFIG = CONFIG

    # ------------------------------------------------------------
    # frame building (all port plumbing; no indicator math here)
    # ------------------------------------------------------------
    def _frames(self, extra, session_d, now_dt):
        """Build every bar frame the day machine reads, from the
        producer feeds. Returns None when a load-bearing feed is
        absent (fail closed: no bars, no signal)."""
        m5_long = extra.get("bars_5m_long") or {}
        m1 = extra.get("bars_1m") or {}
        if not m5_long.get(SYM):
            return None
        spy5 = sb.with_end(_shape(m5_long.get(SYM)), 5)
        qqq5 = sb.with_end(_shape(m5_long.get(BENCH)), 5)
        spy1 = sb.with_end(_shape(m1.get(SYM)), 1)
        qqq1 = sb.with_end(_shape(m1.get(BENCH)), 1)

        spy5_rth = sb.filter_session(spy5, "regular")
        spy5_ext = sb.filter_session(spy5, "extended")
        daily_rth = [b for b in sb.aggregate_daily(spy5_rth)
                     if b["t"].date() < session_d]
        daily_ext = [b for b in sb.aggregate_daily(spy5_ext)
                     if b["t"].date() < session_d]
        qqq5_rth = sb.filter_session(qqq5, "regular")
        qqq_daily = [b for b in sb.aggregate_daily(qqq5_rth)
                     if b["t"].date() < session_d]

        h1_rth = sb.aggregate(spy5_rth, 60, anchor="09:30")
        m10_rth = sb.aggregate(spy5_rth, 10, anchor="09:30")
        m1_today = _today(spy1, session_d)
        m1_today_rth = sb.filter_session(m1_today, "regular")
        m3_today = sb.aggregate(m1_today_rth, 3, anchor="09:30")
        qqq1_today = sb.filter_session(_today(qqq1, session_d),
                                       "regular")
        qqq10 = sb.aggregate(
            sb.filter_session(qqq5_rth, "regular"), 10,
            anchor="09:30")
        return {
            "daily_rth": daily_rth, "daily_ext": daily_ext,
            "qqq_daily": qqq_daily,
            "h1": _completed(h1_rth, now_dt),
            "m10": _completed(m10_rth, now_dt),
            "m1_today": m1_today, "m1_rth": m1_today_rth,
            "m3_today": _completed(m3_today, now_dt),
            "qqq1_today": qqq1_today,
            "qqq10": _completed(qqq10, now_dt),
            "premarket": [b for b in _today(spy5_ext, session_d)
                          if (b["t"].hour, b["t"].minute) < (9, 30)],
        }

    # ------------------------------------------------------------
    # indicator reads (port outputs only)
    # ------------------------------------------------------------
    def _po_rows(self, h1_completed):
        if not h1_completed:
            return []
        return si.phase_oscillator(h1_completed)["rows"]

    def _po_at(self, po_rows, h1_completed, moment_dt):
        """The last COMPLETED 1h PO value at or before a moment —
        the only PO read the Bilbo gate ever makes (design 4.4;
        the unfinished-1h join is excluded by construction)."""
        idx = None
        for i, b in enumerate(h1_completed):
            if sb.close_time(b) <= moment_dt:
                idx = i
            else:
                break
        if idx is None:
            return None
        return po_rows[idx]

    def _ribbon_rows(self, m10_completed):
        if not m10_completed:
            return []
        return si.pivot_ribbon_pro(m10_completed)["rows"]

    def _qqq_confirmed(self, frames, qqq_ladder, direction, now_dt):
        """SPX/NQ confluence (X-learning addition; DESK-CHOICE
        read, filed either way): QQQ confirms a direction when
        its last completed 10m close sits beyond its own 23.6%
        trigger that way, or it has already touched its own
        38.2% level today that way."""
        if qqq_ladder is None:
            return False
        anchor, unit = qqq_ladder["anchor"], qqq_ladder["unit"]
        trig = _lvl(anchor, unit, F_TRIGGER, direction)
        gate = _lvl(anchor, unit, F_GATE, direction)
        m10 = frames["qqq10"]
        if m10:
            c = m10[-1]["close"]
            if (direction > 0 and c > trig) or \
                    (direction < 0 and c < trig):
                return True
        return _touch_bar(frames["qqq1_today"], gate,
                          direction) is not None

    # ------------------------------------------------------------
    # day classification helpers
    # ------------------------------------------------------------
    def _classify_open(self, frames, plan):
        """(class, direction) from the first RTH 1m bar (design
        4.2): gap beyond +/-38.2, inside the trigger box, or
        between trigger and gate."""
        m1 = frames["m1_rth"]
        if not m1:
            return None, 0
        anchor, unit = plan["anchor"], plan["unit"]
        o = m1[0]["open"]
        for direction in (1, -1):
            if (direction > 0 and o >= _lvl(anchor, unit, F_GATE, 1)) \
                    or (direction < 0
                        and o <= _lvl(anchor, unit, F_GATE, -1)):
                return "gap_gate", direction
        if abs(o - anchor) < F_TRIGGER * unit:
            return "inside_box", 0
        return "between", 0

    def _range_state(self, frames, plan, now_dt):
        """Range-scalp classification (X-learning addition,
        ladder-native defaults): range-bound once a completed 1h
        bar shows the day's range at <= 70% of the unit with its
        close inside the trigger box; broken by a completed 10m
        close beyond +/-61.8 or an hourly range above 90%."""
        anchor, unit = plan["anchor"], plan["unit"]
        m1 = frames["m1_rth"]
        if not m1:
            return False, None
        state, range_pct = False, None
        h1_today = [b for b in frames["h1"]
                    if b["t"].date() == frames["session_d"]]
        seen = []
        for hb in h1_today:
            seen += [b for b in m1 if sb.close_time(b) <= sb.close_time(hb)]
            if not seen:
                continue
            hi = max(b["high"] for b in seen)
            lo = min(b["low"] for b in seen)
            range_pct = (hi - lo) / unit * 100.0
            if range_pct > RANGE_HIGH_PCT:
                state = False
            elif range_pct <= RANGE_LOW_PCT and \
                    abs(hb["close"] - anchor) < F_TRIGGER * unit:
                state = True
        if state:
            for b in frames["m10"]:
                if b["t"].date() != frames["session_d"]:
                    continue
                if b["close"] > _lvl(anchor, unit, F_TARGET, 1) or \
                        b["close"] < _lvl(anchor, unit, F_TARGET, -1):
                    state = False
                    break
        return state, range_pct

    # ------------------------------------------------------------
    # contract selection (design 3.4)
    # ------------------------------------------------------------
    def _pick_contract(self, extra, direction, session_d, spot,
                       now_epoch):
        """(occ, mid, expiry_iso) or (None, reason). Expiry: the
        nearest listed expiry inside his 2-4 DTE window — no
        substitution outside it. Strike: nearest the spot (D-2).
        Quote: fresh-quotes door, two-sided, spread gate, fresh
        (D-3)."""
        chains = (extra.get("chains") or {}).get(SYM) or []
        fresh = extra.get("fresh_quotes") or {}
        kind = "C" if direction > 0 else "P"
        cands = []
        for c in chains:
            parsed = parse_occ(c.get("symbol"))
            if not parsed or parsed["kind"] != kind:
                continue
            try:
                exp = date.fromisoformat(str(c["expiration"])[:10])
            except (KeyError, ValueError):
                continue
            dte = (exp - session_d).days
            if dte == EXPIRY_DTE:
                cands.append((exp, float(c["strike"]), c["symbol"]))
        if not cands:
            return None, "no_same_day_expiry"
        expiry = min(e for e, _, _ in cands)
        same_day = [(s, o) for e, s, o in cands if e == expiry]
        same_day.sort(key=lambda x: (abs(x[0] - spot), x[0]))
        for strike, occ in same_day:
            q = _quote_ok(fresh.get(occ), now_epoch)
            if q is not None:
                return (occ, q[0], expiry.isoformat()), None
        return None, "no_contract"

    def _size(self, equity, mid, half):
        budget = BUDGET_PCT * float(equity or 0.0) * (0.5 if half else 1.0)
        per = mid * 100.0
        qty = int(budget // per) if per > 0 else 0
        return max(1, qty), budget

    def _enter_intent(self, direction, setup, occ, mid, spot, plan,
                      ctx, half, tag, expiry_iso):
        anchor, unit = plan["anchor"], plan["unit"]
        qty, budget = self._size(ctx.equity, mid, half)
        if setup == "box":
            tgt = _lvl(anchor, unit, F_FULL, direction)
            kill = _lvl(anchor, unit, F_TRIGGER, direction)
            name = "trigger box confirmation"
        elif setup == "scalp":
            # fade posture: entered at the -direction gate level,
            # target is the opposite (+direction) gate level, the
            # kill is a range break through the far 61.8 that way.
            tgt = _lvl(anchor, unit, F_GATE, direction)
            kill = _lvl(anchor, unit, F_TARGET, -direction)
            name = "range scalp"
        else:
            tgt = _lvl(anchor, unit, F_TARGET, direction)
            kill = _lvl(anchor, unit, F_TRIGGER, direction)
            name = "golden gate" + (" bilbo" if tag == "BILBO" else "")
        parsed = parse_occ(occ)
        reason = (
            f"saty_day {name} {'long' if direction > 0 else 'short'}: "
            f"occ={occ} strike={parsed['strike']:.2f} "
            f"expiry={expiry_iso} mid={mid:.2f} ask={mid:.2f} "
            f"spot={spot:.2f} setup={setup} tag={tag or 'plain'} "
            f"kill_level={kill:.2f} target_level={tgt:.2f} "
            f"budget={budget:.2f} overshoot="
            f"{'yes' if qty * mid * 100.0 > budget else 'no'}")
        return Intent(
            "enter", SYM, qty=qty, price_hint=spot,
            limit_price=round(mid, 2), side="buy",
            position_intent="buy_to_open", reason=reason,
            signal_date=ctx.session)

    # ------------------------------------------------------------
    # entry engine
    # ------------------------------------------------------------
    def _gates_gg(self, direction, frames, plan, po_rows, rb_rows,
                  now_dt, gap_open):
        """Golden Gate gate stack (design 4.4/4.5 + confluence).
        Returns (ok, stood_down_reason, bilbo_tag)."""
        anchor, unit = plan["anchor"], plan["unit"]
        po = self._po_at(po_rows, frames["h1"], now_dt)
        if po is None or not po.get("warmed_up") \
                or po.get("phase_oscillator") is None:
            return False, "po_unavailable", None
        v = po["phase_oscillator"]
        tag = None
        if direction > 0:
            if v <= -PO_EXTREME:
                return False, "po_counter_directional", None
            if v >= PO_EXTREME:
                tag = "BILBO"
        else:
            if v >= PO_EXTREME:
                return False, "po_counter_directional", None
            if v <= -PO_EXTREME:
                tag = "BILBO"
        if not gap_open:
            if not rb_rows:
                return False, "ribbon_unavailable", tag
            row = rb_rows[-1]
            if not row.get("warmed_up"):
                return False, "ribbon_unavailable", tag
            fc, sc = row.get("fast_cloud"), row.get("slow_cloud")
            if fc is not None and sc is not None:
                opposed = (fc is False and sc is False) \
                    if direction > 0 else (fc is True and sc is True)
                if opposed:
                    return False, "ribbon_opposed", tag
                if self._chop(rb_rows, frames["m10"], plan):
                    return False, "chop", tag
        return True, None, tag

    @staticmethod
    def _chop(rb_rows, m10, plan):
        """Ribbon chop (design D-10): both cloud runs shorter
        than 3 consecutive completed 10m bars AND the last
        completed 10m close inside the trigger box."""
        if not rb_rows or not m10:
            return False
        fast = [r.get("fast_cloud") for r in rb_rows]
        slow = [r.get("slow_cloud") for r in rb_rows]
        last = len(rb_rows) - 1
        return _run_len(fast, last) < 3 and _run_len(slow, last) < 3 \
            and abs(m10[-1]["close"] - plan["anchor"]) \
            < F_TRIGGER * plan["unit"]

    def _entry_engine(self, frames, plan, qqq_ladder, extra, ctx,
                      now_dt, stamp):
        """Returns (intent or None). Evaluated only when the GG
        family slot and the box slot are both free of positions
        the caller has not already handled; positions are checked
        by signal() before this runs."""
        anchor, unit = plan["anchor"], plan["unit"]
        session_d = frames["session_d"]
        close_dt = session_close_dt(ctx.session)
        window_close = close_dt - timedelta(minutes=60)
        box_down = close_dt - timedelta(minutes=90)
        po_rows = self._po_rows(frames["h1"])
        rb_rows = self._ribbon_rows(frames["m10"])
        stamp["po_last"] = (po_rows[-1]["phase_oscillator"]
                            if po_rows else None)
        cls, cls_dir = self._classify_open(frames, plan)
        stamp["open_class"] = cls
        spot = self._spot(frames, extra, now_dt)
        if spot is None:
            stamp["stood_down"] = "no_spot"
            return None
        stamp["spot"] = round(spot, 2)
        # caller guarantees flat: entries never run beside a position
        range_bound, range_pct = self._range_state(frames, plan, now_dt)
        stamp["range_pct"] = (round(range_pct, 1)
                              if range_pct is not None else None)
        stamp["range_bound"] = range_bound

        # -- Golden Gate, both directions (his primary setup) ----
        for direction in (1, -1):
            gate_lvl = _lvl(anchor, unit, F_GATE, direction)
            touch = _touch_bar(frames["m1_rth"], gate_lvl, direction)
            touch_t = None
            if touch is not None:
                touch_t = sb.close_time(touch)
            elif self._quote_beyond(extra, direction, gate_lvl, ctx.now):
                touch_t = now_dt
            if touch_t is None:
                continue
            age = (now_dt - touch_t).total_seconds()
            if age > ENTRY_FRESH_S or age < -60:
                continue  # the one shot is spent (or not yet real)
            gap_open = (cls == "gap_gate" and cls_dir == direction
                        and touch is not None
                        and frames["m1_rth"]
                        and touch is frames["m1_rth"][0])
            ok, why, tag = self._gates_gg(
                direction, frames, plan, po_rows, rb_rows, now_dt,
                gap_open)
            if not ok:
                stamp["stood_down"] = why
                continue
            conf = self._qqq_confirmed(frames, qqq_ladder, direction,
                                        now_dt)
            stamp[f"confluence_{direction:+d}"] = conf
            if not conf:
                stamp["stood_down"] = "no_confluence"
                continue
            half = (direction > 0
                    and dtime(12, 0) <= now_dt.time() < window_close.time())
            picked, why = self._pick_contract(
                extra, direction, session_d, spot, ctx.now)
            if picked is None:
                stamp["stood_down"] = why
                continue
            occ, mid, expiry = picked
            stamp["decision"] = f"gg_enter_{direction:+d}"
            return self._enter_intent(direction, "gg", occ, mid, spot,
                                      plan, ctx, half, tag, expiry)

        # -- Trigger Box (opened inside the box; 3m CLOSE) ------
        if cls == "inside_box" and now_dt < box_down:
            for direction in (1, -1):
                trig = _lvl(anchor, unit, F_TRIGGER, direction)
                conf_bar = None
                for b in frames["m3_today"]:
                    if (direction > 0 and b["close"] > trig) or \
                            (direction < 0 and b["close"] < trig):
                        conf_bar = b
                        break
                if conf_bar is None:
                    continue
                age = (now_dt - sb.close_time(conf_bar)).total_seconds()
                if age > ENTRY_FRESH_S or age < 0:
                    continue
                if rb_rows:
                    row = rb_rows[-1]
                    fc, sc = row.get("fast_cloud"), row.get("slow_cloud")
                    if fc is not None and sc is not None:
                        opposed = (fc is False and sc is False) \
                            if direction > 0 else (fc is True
                                                   and sc is True)
                        if opposed:
                            stamp["stood_down"] = "ribbon_opposed"
                            continue
                if self._chop(rb_rows, frames["m10"], plan):
                    stamp["stood_down"] = "ribbon_chop"
                    continue
                stamp[f"confluence_{direction:+d}"] = \
                    self._qqq_confirmed(frames, qqq_ladder, direction,
                                        now_dt)
                picked, why = self._pick_contract(
                    extra, direction, session_d, spot, ctx.now)
                if picked is None:
                    stamp["stood_down"] = why
                    continue
                occ, mid, expiry = picked
                stamp["decision"] = f"box_enter_{direction:+d}"
                return self._enter_intent(direction, "box", occ, mid,
                                          spot, plan, ctx, False, None,
                                          expiry)
        elif cls == "inside_box" and now_dt >= box_down:
            stamp.setdefault("stood_down", "box_expired")

        # -- Range scalp (fade the level while range-bound) -----
        if range_bound:
            for direction in (1, -1):
                # a long scalp buys the -38.2 touch; a short scalp
                # sells the +38.2 touch (fade posture, `direction`
                # is the TRADE direction; the touch is opposite)
                touch_lvl = _lvl(anchor, unit, F_GATE, -direction)
                touch = _touch_bar(frames["m1_rth"], touch_lvl,
                                   -direction)
                if touch is None:
                    continue
                age = (now_dt - sb.close_time(touch)).total_seconds()
                if age > ENTRY_FRESH_S or age < -60:
                    continue
                picked, why = self._pick_contract(
                    extra, direction, session_d, spot, ctx.now)
                if picked is None:
                    stamp["stood_down"] = why
                    continue
                occ, mid, expiry = picked
                stamp["decision"] = f"scalp_enter_{direction:+d}"
                return self._enter_intent(direction, "scalp", occ, mid,
                                          spot, plan, ctx, False, None,
                                          expiry)
        return None

    def _quote_beyond(self, extra, direction, level, now_epoch):
        """The real-time leg of the touch test (D-5): a fresh IEX
        quote whose mid is beyond the level right now."""
        q = (extra.get("latest_quote") or {}).get(SYM)
        if not isinstance(q, dict) or not q.get("t"):
            return False
        try:
            t_epoch = datetime.fromisoformat(
                str(q["t"]).replace("Z", "+00:00")).timestamp()
            bp, ap = float(q["bp"]), float(q["ap"])
        except (KeyError, TypeError, ValueError):
            return False
        if now_epoch - t_epoch > QUOTE_STALE_S or bp <= 0 or ap < bp:
            return False
        mid = (bp + ap) / 2.0
        return mid >= level if direction > 0 else mid <= level

    def _spot(self, frames, extra, now_dt):
        q = (extra.get("latest_quote") or {}).get(SYM)
        if isinstance(q, dict) and q.get("bp") and q.get("ap"):
            try:
                return (float(q["bp"]) + float(q["ap"])) / 2.0
            except (TypeError, ValueError):
                pass
        m1 = frames["m1_rth"] or frames["m1_today"]
        return m1[-1]["close"] if m1 else None

    # ------------------------------------------------------------
    # position identification (broker record + deterministic
    # replay of today's events — the record is truth for WHAT is
    # held; the replay only names WHICH setup brought it in)
    # ------------------------------------------------------------
    def _identify(self, frames, plan, direction, entry_dt):
        anchor, unit = plan["anchor"], plan["unit"]
        cands = []
        t = _touch_bar(frames["m1_rth"],
                       _lvl(anchor, unit, F_GATE, direction), direction)
        if t is not None:
            cands.append((sb.close_time(t), "gg"))
        cls, _ = self._classify_open(frames, plan)
        if cls == "inside_box":
            trig = _lvl(anchor, unit, F_TRIGGER, direction)
            for b in frames["m3_today"]:
                if (direction > 0 and b["close"] > trig) or \
                        (direction < 0 and b["close"] < trig):
                    cands.append((sb.close_time(b), "box"))
                    break
        t = _touch_bar(frames["m1_rth"],
                       _lvl(anchor, unit, F_GATE, -direction), -direction)
        if t is not None:
            cands.append((sb.close_time(t), "scalp"))
        cands = [c for c in cands
                 if c[0] <= entry_dt + timedelta(seconds=300)]
        if not cands:
            return "gg", None
        # The firing event is the one closest to the fill (a
        # stood-down touch earlier in the day must not mislabel a
        # later setup's position); ties break GG > box > scalp.
        order = {"gg": 0, "box": 1, "scalp": 2}
        cands.sort(key=lambda x: (abs((entry_dt - x[0]).total_seconds()),
                                  order[x[1]]))
        return cands[0][1], cands[0][0]

    def _bilbo_tag_at(self, frames, po_rows, direction, moment_dt):
        po = self._po_at(po_rows, frames["h1"], moment_dt)
        if po is None or po.get("phase_oscillator") is None:
            return None
        v = po["phase_oscillator"]
        if direction > 0 and v >= PO_EXTREME:
            return "BILBO"
        if direction < 0 and v <= -PO_EXTREME:
            return "BILBO"
        return None

    def _trend_at(self, rb_rows, m10, direction, moment_dt):
        """Full aligned 10m Pro stack at a moment (D-10 TREND)."""
        idx = None
        for i, b in enumerate(m10):
            if sb.close_time(b) <= moment_dt:
                idx = i
            else:
                break
        if idx is None or not rb_rows:
            return False
        row = rb_rows[idx]
        fc, sc = row.get("fast_cloud"), row.get("slow_cloud")
        if fc is None or sc is None:
            return False
        return (fc and sc) if direction > 0 else (not fc and not sc)

    # ------------------------------------------------------------
    # position management (design 5; exits keyed to the stock)
    # ------------------------------------------------------------
    def _exit_intent(self, pos, qty, occ, mid, spot, ctx, rule,
                     market=False):
        kw = {}
        if not market and mid is not None:
            kw["limit_price"] = round(mid, 2)
        return Intent(
            "exit", SYM, qty=int(qty), price_hint=spot, side="sell",
            position_intent="sell_to_close",
            reason=(f"saty_day exit: {rule} occ={occ} "
                    f"qty={int(qty)}"), signal_date=ctx.session, **kw)

    def _manage(self, frames, plan, pos, extra, ctx, now_dt, stamp):
        anchor, unit = plan["anchor"], plan["unit"]
        close_dt = session_close_dt(ctx.session)
        occ = pos.get("occ")
        parsed = parse_occ(occ)
        qty = int(float(pos.get("qty") or 0))
        if parsed is None or qty <= 0:
            return []
        direction = 1 if parsed["kind"] == "C" else -1
        entry_t = float(pos.get("fill_t") or pos.get("entry_t") or 0)
        entry_dt = datetime.fromtimestamp(entry_t, tz=ET) \
            if entry_t else now_dt
        spot = self._spot(frames, extra, now_dt)
        stamp["position"] = {"occ": occ, "qty": qty,
                             "direction": direction}
        quotes = extra.get("quotes") or {}
        snap = _snap_mid(quotes, occ)

        # An overnight survivor is outside every statistic the
        # system publishes: flat it at the first evaluation.
        if str(pos.get("signal_date") or "") != ctx.session:
            stamp["decision"] = "overnight_flat"
            mid = snap[0] if snap else None
            return [self._exit_intent(pos, qty, occ, mid, spot, ctx,
                                      "overnight_flat",
                                      market=snap is None)]

        setup, ev_t = self._identify(frames, plan, direction, entry_dt)
        stamp["setup"] = setup
        po_rows = self._po_rows(frames["h1"])
        rb_rows = self._ribbon_rows(frames["m10"])
        tag = self._bilbo_tag_at(frames, po_rows, direction,
                                  ev_t or entry_dt)
        if tag:
            stamp["bilbo_tag"] = tag
        since = [b for b in frames["m1_rth"]
                 if sb.close_time(b) > entry_dt]
        flat_t = close_dt - timedelta(minutes=5)
        bid_t = close_dt - timedelta(minutes=3)
        market_t = close_dt - timedelta(minutes=2)

        def priced(q, rule):
            """The 5.5 ladder inside the EOD window; mid-limit
            before it; a decision with no price door outside the
            window stays pending (filed), never dropped (9.5)."""
            if now_dt >= flat_t:
                if snap is None:
                    return self._exit_intent(pos, q, occ, None, spot,
                                             ctx, rule, market=True)
                if now_dt >= market_t:
                    return self._exit_intent(pos, q, occ, None, spot,
                                             ctx, rule, market=True)
                if now_dt >= bid_t:
                    return self._exit_intent(pos, q, occ, snap[1],
                                             spot, ctx, rule)
                return self._exit_intent(pos, q, occ, snap[0], spot,
                                         ctx, rule)
            if snap is None:
                stamp["exit_pending_no_quote"] = rule
                return None
            return self._exit_intent(pos, q, occ, snap[0], spot, ctx,
                                     rule)

        # warnings: filed, never acted on (design 5.4 / R-5)
        self._warnings(frames, rb_rows, direction, entry_dt, stamp)

        # -- EOD flat (D-7) --------------------------------------
        if now_dt >= flat_t:
            stamp["decision"] = "eod_flat"
            it = priced(qty, "eod_flat")
            return [it] if it else []

        # -- kills (close-based; first deciding close rules) -----
        if setup == "box":
            trig = _lvl(anchor, unit, F_TRIGGER, direction)
            for b in frames["m3_today"]:
                if sb.close_time(b) <= entry_dt:
                    continue
                if (direction > 0 and b["close"] < trig) or \
                        (direction < 0 and b["close"] > trig):
                    stamp["decision"] = "box_kill"
                    it = priced(qty, "box_kill_3m_close_through_trigger")
                    return [it] if it else []
        elif setup == "scalp":
            far = _lvl(anchor, unit, F_TARGET, -direction)
            for b in frames["m10"]:
                if sb.close_time(b) <= entry_dt:
                    continue
                if (direction > 0 and b["close"] < far) or \
                        (direction < 0 and b["close"] > far):
                    stamp["decision"] = "scalp_range_break"
                    it = priced(qty, "scalp_kill_range_break")
                    return [it] if it else []
            tgt = _touch_bar(since, _lvl(anchor, unit, F_GATE,
                                         direction), direction)
            if tgt is not None:
                stamp["decision"] = "scalp_target"
                it = priced(qty, "scalp_target_opposite_level")
                return [it] if it else []
            return []
        else:  # gg
            trig = _lvl(anchor, unit, F_TRIGGER, direction)
            for b in frames["m10"]:
                if sb.close_time(b) <= entry_dt:
                    continue
                if (direction > 0 and b["close"] < trig) or \
                        (direction < 0 and b["close"] > trig):
                    stamp["decision"] = "gg_kill"
                    it = priced(qty, "gg_kill_10m_close_through_trigger")
                    return [it] if it else []

        # -- stations --------------------------------------------
        if setup == "box":
            full = _touch_bar(since, _lvl(anchor, unit, F_FULL,
                                          direction), direction)
            if full is not None:
                rights = self._trend_at(rb_rows, frames["m10"],
                                        direction,
                                        sb.close_time(full))
                if not rights:
                    stamp["decision"] = "box_full_atr"
                    it = priced(qty, "box_exit_full_atr")
                    return [it] if it else []
                keep = math.ceil(qty / 2)
                if qty > keep and (now_dt - sb.close_time(full)) \
                        .total_seconds() <= STATION_FRESH_S:
                    stamp["decision"] = "box_runner_transition"
                    it = priced(qty - keep, "box_runner_keep_half")
                    return [it] if it else []
                stamp["runner"] = "trend"
                return []
            mid_t = _touch_bar(since, _lvl(anchor, unit, F_MID,
                                           direction), direction)
            if mid_t is not None and qty >= 2 and \
                    (now_dt - sb.close_time(mid_t)).total_seconds() \
                    <= STATION_FRESH_S:
                stamp["decision"] = "box_partial"
                it = priced(qty // 2, "box_scale_half_at_midrange")
                return [it] if it else []
            return []

        # gg stations, far end first (path order supersedes)
        prim = _touch_bar(since, _lvl(anchor, unit, F_TARGET,
                                      direction), direction)
        if prim is not None:
            rights = bool(tag) or self._trend_at(
                rb_rows, frames["m10"], direction,
                sb.close_time(prim))
            if not rights:
                stamp["decision"] = "gg_target"
                it = priced(qty, "gg_exit_at_618")
                return [it] if it else []
            stamp["runner"] = "bilbo" if tag else "trend"
            full = _touch_bar(since, _lvl(anchor, unit, F_FULL,
                                          direction), direction)
            if full is not None:
                stamp["decision"] = "gg_full_atr"
                it = priced(qty, "gg_runner_exit_full_atr")
                return [it] if it else []
            r78 = _touch_bar(since, _lvl(anchor, unit, F_RUNNER,
                                         direction), direction)
            keep = math.ceil(qty / 2)
            if r78 is not None and qty > keep and \
                    (now_dt - sb.close_time(r78)).total_seconds() \
                    <= STATION_FRESH_S:
                stamp["decision"] = "gg_runner_halve_786"
                it = priced(qty - keep, "gg_runner_halve_at_786")
                return [it] if it else []
            if qty > keep and (now_dt - sb.close_time(prim)) \
                    .total_seconds() <= STATION_FRESH_S:
                stamp["decision"] = "gg_runner_transition"
                it = priced(qty - keep, "gg_runner_keep_half_at_618")
                return [it] if it else []
            return []
        mid_t = _touch_bar(since, _lvl(anchor, unit, F_MID,
                                       direction), direction)
        if mid_t is not None and qty >= 2 and \
                (now_dt - sb.close_time(mid_t)).total_seconds() \
                <= STATION_FRESH_S:
            stamp["decision"] = "gg_partial"
            it = priced(qty // 2, "gg_partial_half_at_midpoint")
            return [it] if it else []
        return []

    def _warnings(self, frames, rb_rows, direction, entry_dt, stamp):
        """1h EMA21 / 10m EMA48 breaks — filed, never acted on
        (design 5.4; R-5 leaves any mechanical response to the owner)."""
        h1 = frames["h1"]
        if h1:
            closes = [b["close"] for b in h1]
            e21 = sp.ema_series(closes, 21)
            for i, b in enumerate(h1):
                if sb.close_time(b) <= entry_dt or e21[i] is None:
                    continue
                if (direction > 0 and b["close"] < e21[i]) or \
                        (direction < 0 and b["close"] > e21[i]):
                    stamp["warning_1h_ema21_break"] = True
                    break
        m10 = frames["m10"]
        for i, b in enumerate(m10):
            if sb.close_time(b) <= entry_dt:
                continue
            row = rb_rows[i] if i < len(rb_rows) else None
            if not row or row.get("ema48") is None:
                continue
            if (direction > 0 and b["close"] < row["ema48"]) or \
                    (direction < 0 and b["close"] > row["ema48"]):
                stamp["warning_10m_ema48_break"] = True
                break

    def _session_pnl(self, extra, pos):
        """The sleeve's session P&L, broker truth (his $10K
        daily stop): cash flow over today's fill rows for this
        sleeve (served from the desk ledger by the producer —
        sells add, buys subtract, options at x100) plus the open
        position marked at the current mid (at entry price when
        no quote — a neutral mark). None when the fills door is
        absent: the stop then cannot be verified and the fact is
        stamped, never guessed."""
        fills = extra.get("session_fills")
        if fills is None:
            return None
        cash = 0.0
        for f in fills:
            try:
                q = abs(float(f.get("qty") or 0))
                p = float(f.get("price") or 0)
            except (TypeError, ValueError):
                continue
            if f.get("position_intent") == "sell_to_close":
                cash += q * p * 100.0
            elif f.get("position_intent") == "buy_to_open":
                cash -= q * p * 100.0
        if isinstance(pos, dict) and float(pos.get("qty") or 0) != 0:
            snap = _snap_mid(extra.get("quotes") or {}, pos.get("occ"))
            mark = snap[0] if snap else float(pos.get("entry_px") or 0)
            cash += abs(float(pos["qty"])) * mark * 100.0
        return cash

    # ------------------------------------------------------------
    # the evaluation
    # ------------------------------------------------------------
    def _blocked_exit(self, extra, ctx, now_dt, stamp):
        """D-B1 cure (2026-10-22): a held position gets its
        time-based exits even when the data/warmup gates block
        the ladder — the mandatory EOD flat (close - 5 min, the
        _manage ladder's own flat_t) and the overnight flat need
        no bars, no ladder and no quote: they go out unpriced on
        the desk's market/EOD door. Outside those windows the
        blocked pass still returns [] (level exits genuinely
        need the ladder)."""
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYM) or {}).get("position")
        if not isinstance(pos, dict) \
                or float(pos.get("qty") or 0) == 0:
            return []
        occ = pos.get("occ")
        parsed = parse_occ(occ)
        qty = int(float(pos.get("qty") or 0))
        if parsed is None or qty <= 0:
            return []
        overnight = str(pos.get("signal_date") or "") != ctx.session
        close_dt = session_close_dt(ctx.session)
        if overnight:
            rule = "overnight_flat_blocked_data"
        elif now_dt >= close_dt - timedelta(minutes=5):
            rule = "eod_flat_blocked_data"
        else:
            return []
        stamp["state"] = "blocked_data"
        stamp["decision"] = rule
        stamp["position"] = {"occ": occ, "qty": qty}
        return [self._exit_intent(pos, qty, occ, None, None, ctx,
                                  rule, market=True)]

    def signal(self, bars, slice_state, ctx):
        self.last_evaluation = {}
        stamp = {"sleeve": "saty_day", "session": ctx.session}
        self.last_evaluation = stamp
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        session_d = date.fromisoformat(ctx.session)
        if not is_trading_day(session_d):
            stamp["state"] = "not_a_trading_day"
            return []
        extra = ctx.extra or {}
        frames = self._frames(extra, session_d, now_dt)
        if frames is None:
            stamp["state"] = "blocked_data"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        frames["session_d"] = session_d

        plan = _ladder(frames["daily_rth"], session_d, "regular")
        shadow = _ladder(frames["daily_ext"], session_d, "extended")
        if plan is None:
            stamp["state"] = "blocked_data"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        stamp["plan"] = {
            "anchor": round(plan["anchor"], 2),
            "unit": round(plan["unit"], 2),
            "basis": "regular",
            "shadow_anchor": round(shadow["anchor"], 2)
            if shadow else None,
            "shadow_unit": round(shadow["unit"], 2)
            if shadow else None,
        }
        if not plan.get("warmed_up"):
            stamp["state"] = "blocked_warmup"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        # ribbon / oscillator warmup is part of the plan's inputs
        # (design 3.2): read at the last completed bars.
        po_rows = self._po_rows(frames["h1"])
        rb_rows = self._ribbon_rows(frames["m10"])
        if (po_rows and not po_rows[-1].get("warmed_up")) or \
                (rb_rows and not rb_rows[-1].get("warmed_up")) or \
                not po_rows or not rb_rows:
            stamp["state"] = "blocked_warmup"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        stamp["state"] = "armed"
        # filed context (design 3.3): daily EMA21 stance, daily PO
        # zone, premarket high/low. Context only; gates nothing.
        closes = [b["close"] for b in frames["daily_rth"]]
        e21 = sp.ema_series(closes, 21)
        if e21 and e21[-1] is not None:
            stamp["daily_vs_ema21"] = "above" if closes[-1] >= e21[-1] \
                else "below"
        pm = frames["premarket"]
        if pm:
            stamp["premarket_high"] = round(max(b["high"] for b in pm), 2)
            stamp["premarket_low"] = round(min(b["low"] for b in pm), 2)
        stamp["event_day"] = "absent"  # G-7: filed as absent context

        # position first (broker truth): manage, never add.
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYM) or {}).get("position")
        pnl = self._session_pnl(extra, pos)
        stamp["session_pnl"] = (round(pnl, 2) if pnl is not None
                                else "unavailable")
        if isinstance(pos, dict) and float(pos.get("qty") or 0) != 0:
            stamp["family_busy"] = True
            return self._manage(frames, plan, pos, extra, ctx, now_dt,
                                stamp)

        # his daily stop (sleeve-internal strategy logic, NOT a
        # desk veto): down $10,000 on the day ends NEW entries;
        # exits and the EOD flat above are unaffected.
        if pnl is not None and pnl <= -DAILY_STOP_USD:
            stamp["daily_stop_halt"] = True
            stamp["stood_down"] = "daily_stop"
            return []

        close_dt = session_close_dt(ctx.session)
        window_close = close_dt - timedelta(minutes=60)
        if now_dt >= window_close:
            stamp["stood_down"] = "entry_window_closed"
            return []
        if now_dt < datetime.combine(session_d, dtime(9, 30), tzinfo=ET):
            stamp["state"] = "armed_preopen"
            return []
        qqq_ladder = _ladder(frames["qqq_daily"], session_d, "regular")
        intent = self._entry_engine(frames, plan, qqq_ladder, extra,
                                    ctx, now_dt, stamp)
        return [intent] if intent is not None else []


def signal(bars, slice_state, context):
    return SatyDay().signal(bars, slice_state, context)
