"""Phoenix Breakout — lean-desk port (proof port, spec section 6 step 3).

EXTRACTED from the old desk's phoenix_sleeve.py (frozen SPEC; Judgments /
Decisions #39-#49 are its law) + the detection convention of
phoenix_watch.py. The pure decision logic below is verbatim in behavior:
same constants, same strictness, same fail-closed branches, same gate
order on the sleeve-local entry path. What changed is only what the
sleeve contract (spec section 3) forces — plumbing the old file owned
(broker submits, client-order-ids, file state, ledger writes, the chart
gate, the desk risk stack) is the core's job now; this file emits
intents and expresses its exits as ExitRule data. See ports/phoenix.md
for the full extracted-vs-changed ledger and the named misfits.

Strategy (old module docstring, condensed):
  Signal (closed bars only): close[t] > max(close[t-20..t-1]) strict
  (ties do NOT count) AND trailing-60d SPY return at the breakout bar
  r60 = SPY_c[t] / SPY_c[t-60] - 1 <= 0 (regime anchored at t);
  t >= 60 bars warmup; signal-bar volume > 0.
  Entry (Arm B, Decision #39): first day d in (t+1..t+5) with
  close_d < open_d (red vs the day's OWN open — Decision #93: this is
  phoenix's ONLY red-day test). No red day in the window => SKIPPED.
  Exit: close of the 20th trading day after the entry bar; a dead exit
  session defers to the next available close (fail SAFE toward exiting).
  Disaster stop (Decision #41, labeled non-research safety rail): GTC
  sell stop 25% below the entry fill — here expressed as data.
  Risk: 0.25% equity/trade on the -25% stop distance => 1.0% notional
  target; 1-share minimum (overshoot flagged, Decision #20); max 8
  concurrent Phoenix positions; 25% sleeve notional cap (Decision #44).
  De-overlap: an entry day on/before the last exit day is skipped.
  Auto-pause (Decision #49): 3 disaster-stop hits in the trailing 20
  closed trades halt new entries; resume is User's explicit call only.

master-desk — gone under the cutover doctrine: the Decision #8 earnings
blackout (3 days before through the earnings date; a stale or missing
calendar or an unknown date blocked entries). The SPEC's section 5 adopts
"the desk's existing earnings-blackout semantics": a desk-wide rail, not
a Phoenix rule.

Inputs the core injects (context.extra) — the sleeve reads nothing else:
  "sleeve_state": {SYM: {"pending_signals": [...], "pending_entry": ...,
                    "position": {...} | None, "last_exit_date": ...}}
  "meta":         {"closed_trades": [...],
                    "entries_paused_by_disaster_rule": bool}
  "forming":      {SYM: {"o": .., "c": .., "v": ..}}  (today's session)
  "broker_qty":   {SYM: qty}   (absent key == unreadable == fail closed)
  "foreign_holders": {SYM: [sleeve, ...]}  (Decision #46 co-hold view)
Pending-signal bookkeeping is a pure function of the bars plus that
state: detections are recomputed from the closed bars every call and
merged with any persisted rows, exactly as the old record_signals did.
"""
import math
from datetime import datetime
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

# ------------------------------------------------------------- constants
# Verbatim from the old sleeve (SPEC section 1: frozen 19-name universe;
# SPY doubles as regime proxy AND tradeable name). Never substitute.
UNIVERSE = ("MU", "WDC", "ANF", "CLS", "FFIV", "AAOI", "AXTI", "SOXL",
            "AEHR", "FCEL", "TTMI", "SIMO", "VICR", "AG", "SILJ",
            "SPY", "QQQ", "NVDA", "AAPL")
REGIME_PROXY = "SPY"

WARMUP_BARS = 60        # t >= 60 (regime needs 60d of SPY)
LOOKBACK = 20           # strict 20-day closing high
ENTRY_WINDOW = 5        # first red day in (t+1 .. t+5)
HOLD_DAYS = 20          # exit at close of the 20th trading day after entry
DISASTER_STOP = 0.25    # GTC sell stop 25% below entry fill (desk-norm)
RISK_FRACTION = 0.0025  # per-trade risk budget (Phase convention)
MAX_POSITIONS = 8       # Phoenix-local cap (desk-wide 10 is core Risk's)
SLEEVE_NOTIONAL_CAP = 0.25  # sleeve notional <= 25% of equity
COST_BPS = 0.0005           # 5bp/side cost assumption (paper calibration ref)

CONFIG = SleeveConfig(
    sleeve_id="phoenix",
    cadence_s=300,
    universe=UNIVERSE,
    state_schema={"pending_signals": "list", "pending_entry": "dict|None",
                  "position": "dict|None", "last_exit_date": "str|None",
                  "meta.closed_trades": "list",
                  "meta.entries_paused_by_disaster_rule": "bool"},
    risk_pct=RISK_FRACTION,
)


# ------------------------------------------------- bar helpers (list form)
# Bars arrive as the core's bar dicts {"t","o","h","l","c","v"} ascending.
# A daily bar's "t" is anchored 04:00Z == midnight ET, so its UTC date IS
# its ET session date (the old desk's +4h shift convention).

def _dates(bars):
    # Verbatim old convention (phoenix_watch + the desk's forming-bar
    # strip): shift +4h, then take the UTC date. NOT a tz-aware ET
    # conversion — under EST a 04:00Z stamp is 23:00 the prior ET day,
    # and the old desk still dated it by the +4h shift.
    from datetime import timezone as _tz
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=_tz.utc).date().isoformat()
            for b in bars]


def _bar_loc(dates, date_iso):
    """Integer position of a calendar date in the bars, or None."""
    try:
        return dates.index(date_iso)
    except ValueError:
        return None


# -------------------------------------------- pure signal/entry math
# Verbatim ports of the old sleeve's unit-testable functions; DataFrame
# indexing becomes list indexing, outcomes identical (incl. NaN: the old
# numpy max propagated NaN into a False comparison — the finite checks
# below reproduce exactly those skips).

def find_breakout_signals(sym, bars, spy):
    """All breakout signals in closed bars: strict 20-day closing high
    with trailing-60d SPY return at the breakout bar <= 0. SPY is
    date-anchored, so the two series need not share an index. Any
    missing data fails closed (no signal)."""
    out = []
    if not bars or not spy:
        return out
    if len(bars) < WARMUP_BARS + 1 or len(spy) < WARMUP_BARS + 1:
        return out
    closes = [float(b["c"]) for b in bars]
    vols = [float(b["v"]) for b in bars]
    dates = _dates(bars)
    spy_c = [float(b["c"]) for b in spy]
    spy_pos = {}
    for i, d in enumerate(_dates(spy)):
        spy_pos[d] = i
    for t in range(WARMUP_BARS, len(bars)):
        if not vols[t] > 0:
            continue  # SPEC: signal-bar volume hygiene
        c = closes[t]
        window = closes[t - LOOKBACK:t]
        if not all(math.isfinite(x) for x in window) or not math.isfinite(c):
            continue  # old numpy semantics: NaN in window => no breakout
        prior_max = max(window)
        if not c > prior_max:
            continue  # strict breakout; ties do NOT count
        sp = spy_pos.get(dates[t])
        if sp is None or sp < WARMUP_BARS:
            continue  # regime unknowable -> fail closed
        r60 = spy_c[sp] / spy_c[sp - WARMUP_BARS] - 1
        if not r60 <= 0:
            continue  # NaN-safe: NaN comparisons are False
        out.append({"symbol": sym, "signal_date": dates[t],
                    "close": round(float(c), 2),
                    "prior_max": round(float(prior_max), 2),
                    "r60": round(float(r60), 4),
                    "volume": int(vols[t])})
    return out


def window_end_date(dates, signal_date, window=ENTRY_WINDOW):
    """ISO date of the last session of the (t+1..t+window) entry window,
    or None when the bars do not cover it yet."""
    loc = _bar_loc(dates, signal_date)
    if loc is None:
        return None
    tgt = loc + window
    if tgt >= len(dates):
        return None
    return dates[tgt]


def exit_due_date(dates, entry_date, hold=HOLD_DAYS):
    """ISO date of the 20th trading bar after the entry bar (None if the
    bars do not cover it yet)."""
    loc = _bar_loc(dates, entry_date)
    if loc is None:
        return None
    tgt = loc + hold
    if tgt >= len(dates):
        return None
    return dates[tgt]


def deoverlap_ok(entry_date_iso, last_exit_date_iso):
    """True when an entry on entry_date does not overlap the last exit.
    SPEC: skip iff entry day <= last exit day; the day after is fine."""
    if not last_exit_date_iso:
        return True
    return entry_date_iso > last_exit_date_iso


def size_qty(equity, ref_px):
    """(qty, overshoot). Notional target = risk_budget / stop_distance
    = 0.25% / 25% = 1.0% of equity. 1-share minimum per Decision #20;
    overshoot of the risk budget is flagged, never blocks."""
    target = equity * RISK_FRACTION / DISASTER_STOP
    if ref_px and ref_px > 0:
        qty = max(1, int(target // ref_px))
    else:
        qty = 1
    return qty, bool(qty * ref_px > target)


def detect_provisional_red(forming, prior_close=None):
    """True when the 15:55 session read says red: last < the day's OPEN.
    SPEC #39 (frozen): close_d < open_d — the day's OWN open, NOT the
    prior close (prior_close is advisory and ignored, as in the old
    code). Decision #93: this Arm B test is phoenix's ONLY red-day test."""
    if not forming or not forming.get("v"):
        return False
    try:
        return bool(float(forming["c"]) < float(forming["o"]))
    except (TypeError, ValueError, KeyError):
        return False


def count_positions(state):
    """Open Phoenix slots: a booked position OR a pending entry each
    holds a capacity slot (old 2026-10-08 fix: counting only booked
    positions let same-pass entries blow the 8-position cap)."""
    n = 0
    for st in state.values():
        if not isinstance(st, dict):
            continue
        if st.get("position"):
            n += 1
        elif st.get("pending_entry"):
            n += 1
    return n


def sleeve_notional(state):
    """Booked + pending-entry notional (old 2026-10-08/2026-10-14
    guards: unreadable rows are skipped, never raise)."""
    tot = 0.0
    for st in state.values():
        if not isinstance(st, dict):
            continue
        p = st.get("position")
        if isinstance(p, dict) and p.get("entry_px") and p.get("qty"):
            try:
                tot += float(p["entry_px"]) * float(p["qty"])
            except (TypeError, ValueError):
                pass
        pe = st.get("pending_entry") or {}
        if isinstance(pe, dict) and pe and pe.get("ref_px") and pe.get("qty"):
            try:
                tot += float(pe["ref_px"]) * float(pe["qty"])
            except (TypeError, ValueError):
                pass
    return tot


def active_signal(st):
    """Earliest unexpired, un-entered pending signal (chronological)."""
    cands = [ps for ps in st.get("pending_signals", [])
             if isinstance(ps, dict)
             and not ps.get("entered") and not ps.get("skipped")]
    cands.sort(key=lambda ps: ps.get("signal_date", ""))
    return cands[0] if cands else None


def disaster_pause_check(closed_trades):
    """Decision #49 condition: >= 3 disaster-stop hits in the trailing
    20 closed trades. (The old code also latched a persisted flag and
    logged; the latch lives in core-persisted meta — see entries_paused.)"""
    trailing = (closed_trades or [])[-20:]
    hits = sum(1 for t in trailing
               if isinstance(t, dict) and t.get("reason") == "disaster_stop")
    return hits >= 3


def entries_paused(meta):
    """Decision #49, verbatim old semantics: the entry path reads ONLY
    the latched flag. The old sleeve evaluates disaster_pause_check at
    close-recording time (its _close_position -> _maybe_disaster_pause)
    and latches the flag there; it never re-derives 3-in-20 at entry
    time. In the lean desk the CORE evaluates disaster_pause_check when
    it records a close and latches this flag in meta. Resume only via
    User's explicit decision (the latch is cleared by ruling)."""
    meta = meta or {}
    return bool(meta.get("entries_paused_by_disaster_rule"))


def record_signals(st, sym, bars, spy, today_iso):
    """The old record_signals, pure: merge fresh detections into the
    symbol's pending_signals (returned as a NEW list); a signal whose
    whole window already elapsed before first evaluation is recorded
    skipped; pending rows whose window has fully closed expire to
    skipped. Window end resolves lazily (None = not covered yet)."""
    dates = _dates(bars)
    rows = [dict(ps) for ps in st.get("pending_signals", [])
            if isinstance(ps, dict)]
    for s in find_breakout_signals(sym, bars, spy):
        if any(ps.get("signal_date") == s["signal_date"] for ps in rows):
            continue
        wend = window_end_date(dates, s["signal_date"])
        entry = dict(s, window_end=wend, entered=False, skipped=False)
        if wend is not None and wend < today_iso:
            entry["skipped"] = True  # window elapsed before evaluation
        rows.append(entry)
    for ps in rows:
        if not ps.get("entered") and not ps.get("skipped"):
            wend = ps.get("window_end") or window_end_date(
                dates, ps.get("signal_date"))
            if wend is None:
                continue  # a still-uncoverable window cannot expire
            ps["window_end"] = wend
            if wend < today_iso:
                ps["skipped"] = True
    return rows


# ------------------------------------------------------------- the sleeve

class Phoenix(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        meta = latched_meta(extra, context.session)   # master-desk: a stop filled since the last pass latches #49 now
        forming_map = extra.get("forming") or {}
        broker_qty = extra.get("broker_qty")  # None == unreadable
        foreign = extra.get("foreign_holders") or {}
        spy = bars.get(REGIME_PROXY)
        today_iso = context.session
        now_et = datetime.fromtimestamp(float(context.now), tz=ET)
        in_window = (15, 55) <= (now_et.hour, now_et.minute) < (16, 0)
        intents = []
        book = {s: v for s, v in state.items() if isinstance(v, dict)}   # master-desk: this pass's entries count
        for sym in CONFIG.universe:
            bl = bars.get(sym)
            if not bl or len(bl) < WARMUP_BARS + 1:
                continue  # insufficient history: fail closed, no substitute
            st = state.get(sym) or {}
            rows = record_signals(st, sym, bl, spy, today_iso)
            merged = dict(st, pending_signals=rows)
            if in_window:
                ex = self._exit_intent(sym, merged, bl, forming_map,
                                       today_iso)
                if ex is not None:
                    intents.append(ex)
                    continue
                en = self._entry_intent(sym, merged, book, bl, context, meta,
                                        forming_map, broker_qty,
                                        foreign, today_iso)
                if en is not None:
                    intents.append(en)
                    # old maybe_enter: the pending_entry is written before the submit, so the 8-slot and 25%
                    # notional caps of every later symbol in this pass already count it
                    book[sym] = dict(merged, pending_entry={"qty": en.qty_hint, "ref_px": en.price_hint})
        return intents

    # -- exits (never gated; the core clamps qty to this sleeve's slice)
    def _exit_intent(self, sym, st, bars, forming_map, today_iso):
        p = st.get("position")
        if not p or p.get("exit_submitted"):
            return None
        dates = _dates(bars)
        due = p.get("exit_due_date")
        if not due and p.get("entry_date"):
            due = exit_due_date(dates, p["entry_date"])
            if not due:
                eloc = _bar_loc(dates, p["entry_date"])
                if eloc is not None and (len(bars) - 1) - eloc == HOLD_DAYS - 1:
                    due = today_iso  # d+20 session is forming today
                elif dates and dates[-1] > _plus25(p["entry_date"]):
                    due = today_iso  # entry bar absent: fail SAFE, exit ASAP
        if not due or today_iso < due:
            return None
        forming = forming_map.get(sym)
        if forming is None or not forming.get("v"):
            return None  # dead exit session: next available close (retry)
        try:
            qty = int(float(p.get("qty") or 0))
        except (TypeError, ValueError):
            qty = 0
        if qty <= 0:
            return None
        rules = ()
        if p.get("stop_px"):
            rules = (ExitRule("stop", float(p["stop_px"])),)
        return Intent("exit", sym, qty_hint=qty,
                      price_hint=round(float(forming["c"]), 2),
                      exit_rules=rules,
                      reason="time_stop d+20 (exit_due_date=%s)" % due)

    # -- entries (sleeve-local gate chain, old maybe_enter order; the
    #    desk-wide gates — chart gate, brake, cap, breaker, kill switch —
    #    are the core's, downstream of this intent)
    def _entry_intent(self, sym, st, state, bars, context, meta, forming_map,
                      broker_qty, foreign, today_iso):
        if st.get("position") or st.get("pending_entry"):
            return None
        # Broker cross-check (old 2026-10-06/10-10): unreadable book
        # fails closed; a holding claimed by another sleeve is a
        # Decision #46 co-hold and does NOT burn the signal; an
        # unclaimed holding is treated as our post-wipe orphan — no
        # double entry (the signal consumption itself is core state).
        if broker_qty is None or sym not in broker_qty:
            return None
        if broker_qty[sym] != 0 and not foreign.get(sym):
            return None
        ps = active_signal(st)
        if not ps or not ps.get("signal_date"):
            return None
        dates = _dates(bars)
        loc = _bar_loc(dates, ps["signal_date"])
        if loc is None:
            return None
        # Window day in trading sessions (bars exclude today's forming
        # session, which this pass evaluates): day = bars_since + 1.
        wday = (len(bars) - 1 - loc) + 1
        if not 1 <= wday <= ENTRY_WINDOW:
            return None
        if entries_paused(meta):
            return None  # Decision #49: signal NOT consumed; window stays open
        forming = forming_map.get(sym)
        if forming is None:
            return None  # no forming bar at 15:55: deferred, fail-closed
        if not detect_provisional_red(forming):
            return None  # not a red day (yet); the window stays open
        ref_px = float(forming["c"])
        # ---- gates below consume the signal in the old code (first red
        # ---- day only); in the contract that consumption is persisted
        # ---- core state — the intent simply is not emitted.
        if not deoverlap_ok(today_iso, st.get("last_exit_date")):
            return None
        equity = float(context.equity or 0.0)
        if equity <= 0:
            return None  # old: equity unknown consumed the signal
        book = {s: v for s, v in state.items() if isinstance(v, dict)}
        book[sym] = st
        if count_positions(book) >= MAX_POSITIONS:
            return None
        qty, overshoot = size_qty(equity, ref_px)
        if sleeve_notional(book) + qty * ref_px > SLEEVE_NOTIONAL_CAP * equity:
            return None
        stop_px = round(ref_px * (1 - DISASTER_STOP), 2)
        return Intent("enter", sym, qty_hint=qty, price_hint=round(ref_px, 2),
                      stop=stop_px,
                      exit_rules=(ExitRule("stop", stop_px),
                                  ExitRule("time_bars", float(HOLD_DAYS))),
                      reason="phoenix Arm B red-day entry: signal_date=%s "
                             "window_day=%d overshoot=%s"
                             % (ps["signal_date"], wday, overshoot))


def next_symbol_state(bars, slice_state, context, intents):
    """master-desk: the per-symbol state the old sleeve wrote (M1/M2), recomputed purely:
    pending_signals merged by record_signals, and the active signal CONSUMED (entered=True) exactly where the
    old maybe_enter consumed it — on submit, and on a red day vetoed by de-overlap / unknown
    equity / max positions / notional cap. Pause, broker-unreadable, no forming bar and not-red leave the
    window open (not consumed)."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    meta = latched_meta(extra, context.session)
    forming_map = extra.get("forming") or {}
    broker_qty = extra.get("broker_qty")
    foreign = extra.get("foreign_holders") or {}
    spy = bars.get(REGIME_PROXY)
    today_iso = context.session
    now_et = datetime.fromtimestamp(float(context.now), tz=ET)
    in_window = (15, 55) <= (now_et.hour, now_et.minute) < (16, 0)
    entered = {i.symbol: i for i in intents if i.kind == "enter"}
    pass_book = {s: v for s, v in state.items() if isinstance(v, dict)}
    out = {}
    for sym in CONFIG.universe:
        bl = bars.get(sym)
        if not bl or len(bl) < WARMUP_BARS + 1:
            continue
        st = state.get(sym) or {}
        rows = record_signals(st, sym, bl, spy, today_iso)
        merged = dict(st, pending_signals=rows)
        ps = active_signal(merged)
        if ps is not None and sym in entered:
            ps["entered"] = True
            en = entered[sym]
            pass_book[sym] = dict(merged, pending_entry={"qty": en.qty_hint, "ref_px": en.price_hint})
        elif ps is not None and in_window and not st.get("position") and not st.get("pending_entry") \
                and broker_qty is not None and sym in broker_qty \
                and (broker_qty[sym] == 0 or foreign.get(sym)):
            dates = _dates(bl)
            loc = _bar_loc(dates, ps.get("signal_date"))
            wday = None if loc is None else (len(bl) - 1 - loc) + 1
            forming = forming_map.get(sym)
            if wday is not None and 1 <= wday <= ENTRY_WINDOW and not entries_paused(meta) \
                    and forming is not None and detect_provisional_red(forming):
                ref_px = float(forming["c"])
                equity = float(context.equity or 0.0)
                book = dict(pass_book)                 # this pass's earlier entries hold slots and notional
                book[sym] = merged
                consumed = (not deoverlap_ok(today_iso, st.get("last_exit_date"))
                            or equity <= 0 or count_positions(book) >= MAX_POSITIONS)
                if not consumed:
                    qty, _ = size_qty(equity, ref_px)
                    consumed = sleeve_notional(book) + qty * ref_px > SLEEVE_NOTIONAL_CAP * equity
                if consumed:
                    ps["entered"] = True
        out[sym] = {"pending_signals": rows}
    return out


def latched_meta(extra, session=None):
    """master-desk: the Decision #49 latch exactly as the old _close_position -> _maybe_disaster_pause set it —
    checked after EVERY recorded close (each prefix of the closed trades since the last check), so a pass sees
    a pause latched by a stop that filled since the previous pass; once latched it stays latched (resume =
    an explicit ruling)."""
    meta = dict(extra.get("meta") or {})
    trades = list(extra.get("closed_trades") or [])
    seen = float(meta.get("closes_checked_to") or 0.0)
    if not meta.get("entries_paused_by_disaster_rule"):
        for k, t in enumerate(trades):
            if float(t.get("closed_at") or 0.0) <= seen:
                continue
            if disaster_pause_check(trades[:k + 1]):
                meta["entries_paused_by_disaster_rule"] = True
                meta["paused_at"] = session
                break
    if trades:
        meta["closes_checked_to"] = max(seen, max(float(t.get("closed_at") or 0.0) for t in trades))
    return meta


def next_meta(bars, slice_state, context):
    return latched_meta(context.extra or {}, context.session)


def _plus25(entry_date_iso):
    """entry_date + 25 calendar days, ISO (old exit failsafe horizon)."""
    from datetime import date as _date, timedelta as _td
    try:
        return (_date.fromisoformat(str(entry_date_iso)[:10])
                + _td(days=25)).isoformat()
    except ValueError:
        return "9999-12-31"


def signal(bars, slice_state, context):
    """Module-level contract shape: delegates to the Phoenix class."""
    return Phoenix().signal(bars, slice_state, context)
