"""coffin_rebuilt sleeve: CAND-ROT-04 "The Coffin Rebuilt" — monthly
worst-sector rotation with a trailing month-end exit.

Provenance: Biotech2k sector-rotation family, formulated and frozen
2026-11-09 (~/workspace/midna-book/strategy-candidates/
2026-11-09-biotech2k-rotation.md, CAND-ROT-04). The frozen variant
(ROT-01 / W126 / lowage-only gate / trail15_18) was backtested on
Alpaca SIP daily bars 2017-01-31 to 2026-11-06 and reproduced by the
independent quantjourney-bt oracle with an identical trade path
(research_notes/biotech2k-rotation-tests-20261109/: SWEEP-REPORT.md,
CROSSCHECK-REPORT.md, qj/CROSSCHECK-FREEZE.md — the freeze governs
where any summary disagrees). Desk landing ordered by the owner
2026-11-09: the desk exists to test individual sleeves; this sleeve
executes the frozen rules on the desk's $10,000 slice, basket (a)
(the sector ETF) only. The top-5 basket form is NOT this sleeve.

Frozen rules, exactly as cross-checked:

  * Universe: the 11 SPDR sector ETFs. SPY bars are the session
    calendar. Daily bars, adjustment as served by the desk.
  * Ranked set at a month-end (last SPY session of the month): a
    sector is ranked when, over the SPY calendar, its trailing
    126-session return rW = close/close[-126] - 1 and its distance
    distW = close / max(close over trailing 126 sessions) - 1 are
    both present (the frozen rs6 presence condition is the same
    trailing-126 return, so it adds no further restriction).
  * Entry (month-end, flat): candidates are ranked sectors with
    rW rank-from-worst <= 2 AND distW rank-from-worst <= 2 AND the
    lowage-only stopped-falling gate: low_age >= 20, where low_age
    is the sessions since the minimum intraday low of the trailing
    126 sessions on the sector's own session series. Enter the
    candidate with the lowest rW (tie: lowest distW). One position
    at a time; the full slice goes into the single sector ETF.
  * Entry-month low: the sector's minimum intraday low over the
    signal calendar month (known at signal time).
  * Exits, decided on closes and filled at the next session through
    the dispatcher (the desk's next_bar convention):
      (1) Invalidation, DAILY: held sector close < entry-month low.
      (2) Trail15, MONTH-END closes only: month-end close
          <= 0.85 x peak, where peak is the running maximum of the
          held sector's daily closes starting with the entry FILL
          session's close. An intra-month breach that recovers by
          month-end never exits (frozen gap G1, by design).
      (3) Cap, month-end: months since the entry-signal month >= 18
          (checked only when trail15 did not fire).
    Per-session order, frozen: fill at the open, then peak update,
    then invalidation, then the month-end block; the month-end block
    is skipped on a session where invalidation fired.

Desk mapping (the frozen machine runs on completed sessions; the
sleeve consumes only bars whose session date precedes the current
session, so every decision rests on closed bars and its intent is
emitted during the next session, the desk's next_bar fill):

  * The machine state persists in ctx.extra["coffin_state"],
    round-tripped by adapters/coffin_rebuilt.py beside the sleeve
    journal (the soxl_pm_breakout idiom). Cold start: the state
    initializes at the latest completed session, flat; the first
    month-end evaluated is the first one that completes after
    landing (2026-11-30), matching the registered forward test.
  * A completed session counts as a month-end only when the next
    session (for the latest completed session: the current one)
    falls in a different calendar month — the frozen "last SPY
    session of the month" definition, made streaming-safe.
  * Fill adoption follows SLEEVE-AUTHORING-STANDARD.md: a decision's
    intent is emitted once; the fill is adopted from the slice's
    actual position on the fill session's close processing. An exit
    whose position is still present after its fill session is
    re-emitted once per session until flat (a working/partial exit
    keeps the remainder under the same decision). An entry that
    fills partially adopts the filled portion as the position and
    does not chase the remainder the next day (named: chasing would
    break the frozen fill-at-next-open semantics further than
    adopting the partial does). An entry that does not fill at all
    is dropped and named in last_evaluation; the next month-end
    re-evaluates from flat, exactly as a missed signal would.
  * Reconciliation: holding state with no broker position and no
    exit outstanding reconciles to flat and is named; a broker
    position the machine does not own is named and never traded on.
"""
from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

SECTORS = ("XLK", "XLC", "XLY", "XLP", "XLE", "XLF", "XLV", "XLI",
           "XLB", "XLRE", "XLU")
CALENDAR_SYMBOL = "SPY"
WINDOW = 126
LOW_AGE_MIN = 20
RANK_FROM_WORST_MAX = 2
TRAIL_FRAC = 0.85
CAP_MONTHS = 18

CONFIG = SleeveConfig(
    sleeve_id="coffin_rebuilt",
    cadence_s=300,
    universe=SECTORS + (CALENDAR_SYMBOL,),
    state_schema={"coffin_state": "dict", "position": "dict|None"},
    parked=False,
)


def _number(v):
    if isinstance(v, bool):
        return None
    try:
        out = float(v)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _epoch(v):
    n = _number(v)
    if n is not None:
        return n / 1000.0 if n > 1.0e12 else n
    if not isinstance(v, str):
        return None
    try:
        p = datetime.fromisoformat(v.replace("Z", "+00:00"))
        from datetime import timezone
        if p.tzinfo is None:
            p = p.replace(tzinfo=timezone.utc)
        return p.timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def _session_date(t_epoch):
    """Session date of a daily bar: the UTC date of its timestamp.
    The desk's daily-bar stamps are the session date at 04:00/05:00Z
    (midnight ET) or the 09:30 ET open; every one of those has the
    session's own UTC date, and the desk's other daily sleeves
    derive bar dates the same way (the momentum_rotation +4h form).
    Converting via ET instead would shift a UTC-midnight stamp to
    the previous day and move month boundaries by one session."""
    from datetime import timezone
    return datetime.fromtimestamp(t_epoch, tz=timezone.utc).date().isoformat()


def clean_daily_bars(raw, before_session):
    """Completed daily bars only: valid OHLC dicts whose session
    date is strictly before `before_session` (the current session's
    bar is still forming and never reaches a decision), sorted,
    deduped by session date (last wins)."""
    out = []
    for row in raw or []:
        if not isinstance(row, dict):
            continue
        t = _epoch(row.get("t"))
        o, h, l, c = (_number(row.get(k)) for k in ("o", "h", "l", "c"))
        v = _number(row.get("v")) or 0.0
        if None in (t, o, h, l, c) or min(o, h, l, c) <= 0 or h < l:
            continue
        d = _session_date(t)
        if d >= before_session:
            continue
        out.append({"t": t, "date": d, "o": o, "h": h, "l": l,
                    "c": c, "v": v})
    out.sort(key=lambda b: b["t"])
    deduped = []
    for b in out:
        if deduped and deduped[-1]["date"] == b["date"]:
            deduped[-1] = b
        else:
            deduped.append(b)
    return deduped


def month_end_set(calendar, today):
    """Month-end sessions within the completed calendar. A session
    is a month-end when the NEXT session falls in a different
    calendar month; for the latest completed session the next
    session is `today` (the current session). Judging the latest
    completed session by the truncated calendar alone would label
    every latest session a month-end — the successor rule is the
    frozen definition (last SPY session of the month) made
    streaming-safe."""
    out = set()
    for i, d in enumerate(calendar):
        nxt = calendar[i + 1] if i + 1 < len(calendar) else today
        if nxt[:7] != d[:7]:
            out.add(d)
    return out


def sector_stats(closes_by_date, own_bars, calendar, idx):
    """Frozen W126 stats for one sector at calendar position idx.

    closes_by_date: {date: close} on the SPY calendar (absent =
    no bar that session, the frozen NaN). own_bars: the sector's
    own cleaned bar list (for the low-age gate). Returns None when
    rW or distW is not present (the sector is then unranked)."""
    d = calendar[idx]
    c = closes_by_date.get(d)
    if c is None or idx < WINDOW:
        return None
    c_prev = closes_by_date.get(calendar[idx - WINDOW])
    if c_prev is None or c_prev <= 0:
        return None
    window_closes = [closes_by_date.get(calendar[j])
                     for j in range(idx - WINDOW + 1, idx + 1)]
    present = [x for x in window_closes if x is not None]
    if len(present) < WINDOW:
        return None
    r_w = c / c_prev - 1.0
    dist_w = c / max(present) - 1.0
    # low_age on the sector's own session series: sessions since
    # the minimum intraday low of the trailing WINDOW own sessions
    # ending at (and including) the sector's session on date d.
    own_dates = [b["date"] for b in own_bars]
    try:
        oi = own_dates.index(d)
    except ValueError:
        return None
    if oi < WINDOW - 1:
        return None
    lows = [b["l"] for b in own_bars[oi - WINDOW + 1: oi + 1]]
    argmin = min(range(len(lows)), key=lambda k: lows[k])
    low_age = (len(lows) - 1) - argmin
    return {"rW": r_w, "distW": dist_w, "low_age": low_age, "close": c}


def ranks_at(stats_by_sector):
    """Add rank-from-worst (1 = worst) for rW and distW."""
    vals = {s: v for s, v in stats_by_sector.items() if v is not None}
    if not vals:
        return {}
    r_w_order = sorted(vals, key=lambda s: vals[s]["rW"])
    dist_order = sorted(vals, key=lambda s: vals[s]["distW"])
    out = {}
    for s, v in vals.items():
        row = dict(v)
        row["rW_rank_from_worst"] = r_w_order.index(s) + 1
        row["distW_rank_from_worst"] = dist_order.index(s) + 1
        out[s] = row
    return out


def month_low(own_bars, ym):
    """Minimum intraday low over the calendar month ym=(year, month)
    on the sector's own sessions in that month; None when absent."""
    lows = [b["l"] for b in own_bars
            if int(b["date"][:4]) == ym[0] and int(b["date"][5:7]) == ym[1]]
    return min(lows) if lows else None


def _fresh_state(last_processed):
    return {"mode": "flat", "held": None, "entry_signal_ym": None,
            "entry_month_low": None, "peak_close": None,
            "entry_fill_session": None, "pending": None,
            "emitted": None, "last_processed": last_processed,
            "defects": []}


class CoffinRebuiltSleeve(BaseSleeve):
    CONFIG = CONFIG
    SLEEVE_ID = "coffin_rebuilt"

    # -- state machine ------------------------------------------------
    def _apply_fill(self, st, series, qty, ev):
        """Frozen step 1 for the emitted decision's fill session:
        adopt the fill from the slice's actual position. Returns
        True when the emitted block is resolved either way."""
        em = st["emitted"]
        fill_session = em["fill_session"]
        sector = em["sector"]
        held_qty = float(qty.get(sector) or 0.0)
        if em["action"] == "enter":
            if held_qty > 0:
                st["mode"] = "holding"
                st["held"] = sector
                st["entry_signal_ym"] = em["signal_ym"]
                st["entry_month_low"] = em["month_low"]
                st["entry_fill_session"] = fill_session
                closes = series[sector]["closes"]
                st["peak_close"] = closes.get(fill_session)
                if em.get("intended_qty") and held_qty < em["intended_qty"]:
                    ev["defects"].append(
                        "entry_partial_fill_adopted:%s:%s" % (sector, fill_session))
                st["emitted"] = None
                ev["fill_adopted"] = "enter:%s@%s" % (sector, fill_session)
                return True
            ev["defects"].append(
                "entry_fill_unconfirmed:%s:%s" % (sector, fill_session))
            st["emitted"] = None
            return True
        # exit
        if held_qty == 0:
            st["mode"] = "flat"
            st["held"] = None
            st["entry_signal_ym"] = None
            st["entry_month_low"] = None
            st["peak_close"] = None
            st["entry_fill_session"] = None
            st["emitted"] = None
            ev["fill_adopted"] = "exit:%s@%s" % (sector, fill_session)
            return True
        ev["defects"].append(
            "exit_unconfirmed_reemit:%s:%s" % (sector, fill_session))
        return False  # stays emitted; signal() re-emits once per session

    def _process_session(self, st, d, series, calendar, idx, mes, qty, ev):
        """One completed session, frozen order: fill, peak,
        invalidation, month-end block."""
        # (1) fill at the open
        if st["emitted"] is not None and \
                st["emitted"]["fill_session"] <= d:
            self._apply_fill(st, series, qty, ev)
        if st["emitted"] is not None:
            # A decision is still outstanding (its fill did not
            # adopt on its fill session): it owns the book. The
            # frozen machine never stacks a second decision on an
            # unexecuted one; freeze this session's remaining
            # checks until the fill adopts or is resolved.
            st["last_processed"] = d
            return
        # (2) peak update
        if st["mode"] == "holding" and st["held"] is not None:
            c = series[st["held"]]["closes"].get(d)
            if c is not None and st["peak_close"] is not None:
                st["peak_close"] = max(st["peak_close"], c)
            elif c is not None and st["peak_close"] is None:
                st["peak_close"] = c
        # (3) invalidation, daily
        decided = False
        if st["mode"] == "holding" and st["pending"] is None:
            c = series[st["held"]]["closes"].get(d)
            if c is not None and st["entry_month_low"] is not None \
                    and c < st["entry_month_low"]:
                st["pending"] = {"action": "exit", "sector": st["held"],
                                 "reason": "invalidation", "signal_date": d}
                decided = True
                ev["decision"] = "exit:invalidation@%s" % d
        # (4) month-end block
        if d in mes and not decided and st["pending"] is None:
            if st["mode"] == "holding":
                held = st["held"]
                c = series[held]["closes"].get(d)
                ey, em_ = st["entry_signal_ym"]
                months_held = (int(d[:4]) - ey) * 12 + (int(d[5:7]) - em_)
                if c is not None and st["peak_close"] is not None \
                        and c <= TRAIL_FRAC * st["peak_close"]:
                    st["pending"] = {"action": "exit", "sector": held,
                                     "reason": "trail15", "signal_date": d}
                    ev["decision"] = "exit:trail15@%s" % d
                elif months_held >= CAP_MONTHS:
                    st["pending"] = {"action": "exit", "sector": held,
                                     "reason": "18_months", "signal_date": d}
                    ev["decision"] = "exit:18_months@%s" % d
            elif st["mode"] == "flat":
                stats = {}
                for s in SECTORS:
                    stats[s] = sector_stats(series[s]["closes"],
                                            series[s]["bars"],
                                            calendar, idx)
                rk = ranks_at(stats)
                cands = [s for s in rk
                         if rk[s]["rW_rank_from_worst"] <= RANK_FROM_WORST_MAX
                         and rk[s]["distW_rank_from_worst"] <= RANK_FROM_WORST_MAX
                         and rk[s]["low_age"] >= LOW_AGE_MIN]
                if cands:
                    cands.sort(key=lambda s: (rk[s]["rW"], rk[s]["distW"]))
                    s = cands[0]
                    ml = month_low(series[s]["bars"],
                                   (int(d[:4]), int(d[5:7])))
                    if ml is not None:
                        st["pending"] = {
                            "action": "enter", "sector": s,
                            "reason": "entry", "signal_date": d,
                            "signal_ym": [int(d[:4]), int(d[5:7])],
                            "month_low": ml}
                        ev["decision"] = "enter:%s@%s" % (s, d)
        st["last_processed"] = d

    # -- contract -----------------------------------------------------
    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        raw_state = extra.get("coffin_state") or {}
        ev = {"sleeve": self.SLEEVE_ID, "session": context.session,
              "defects": []}
        self.last_evaluation = ev
        qty = {}
        for sym, q in (slice_state or {}).items():
            qn = _number(q)
            if qn:
                qty[sym] = qn

        series = {}
        for sym in SECTORS + (CALENDAR_SYMBOL,):
            cleaned = clean_daily_bars((bars or {}).get(sym),
                                       context.session)
            series[sym] = {
                "bars": cleaned,
                "closes": {b["date"]: b["c"] for b in cleaned},
            }
        calendar = [b["date"] for b in series[CALENDAR_SYMBOL]["bars"]]
        if not calendar:
            st = dict(raw_state) if raw_state else _fresh_state(None)
            self.coffin_state = st
            ev["state"] = "no_calendar_bars"
            return []

        if not raw_state or "last_processed" not in raw_state:
            # Cold start: begin at the latest completed session,
            # flat. The first month-end evaluated is the first one
            # that completes after landing.
            st = _fresh_state(calendar[-1])
            ev["state"] = "cold_start"
        else:
            st = _fresh_state(None)
            st.update(raw_state)
            ev["state"] = st.get("mode") or "flat"
        self.coffin_state = st
        mes = month_end_set(calendar, context.session)

        # Reconciliation before processing: machine holding with no
        # position and nothing emitted is a vanished position.
        if st["mode"] == "holding" and st["emitted"] is None \
                and not qty.get(st["held"] or ""):
            ev["defects"].append("position_missing_reconciled_flat:%s"
                                 % st["held"])
            st["mode"] = "flat"
            st["held"] = None
            st["entry_signal_ym"] = None
            st["entry_month_low"] = None
            st["peak_close"] = None
            st["entry_fill_session"] = None
            st["pending"] = None
        # Flat machine with a position it does not own: name it,
        # never trade on it.
        foreign = [s for s in SECTORS if qty.get(s)]
        if st["mode"] == "flat" and st["emitted"] is None and foreign:
            ev["defects"].append("unattributed_position:%s"
                                 % ",".join(sorted(foreign)))
            ev["defects_out"] = list(ev["defects"])
            st["defects"] = list(ev["defects"])
            return []

        # Process every completed session not yet processed.
        last = st["last_processed"]
        todo = [d for d in calendar if last is None or d > last]
        idx_of = {d: i for i, d in enumerate(calendar)}
        for d in todo:
            self._process_session(st, d, series, calendar, idx_of[d],
                                  mes, qty, ev)
        ev["last_processed"] = st["last_processed"]

        # Emission: a pending decision is emitted once, during the
        # first session after its signal date (this evaluation),
        # and only when no earlier decision is still outstanding.
        intents = []
        if st["pending"] is not None and st["emitted"] is not None:
            if st["pending"]["action"] == "enter":
                ev["defects"].append("stale_enter_dropped:%s"
                                     % st["pending"]["sector"])
                st["pending"] = None
        if st["pending"] is not None and st["emitted"] is None:
            p = st["pending"]
            if context.session > p["signal_date"]:
                if p["action"] == "enter":
                    equity = _number(context.equity) or 0.0
                    px = series[p["sector"]]["closes"].get(p["signal_date"])
                    if equity <= 0 or not px:
                        ev["defects"].append("entry_size_unavailable:%s"
                                             % p["sector"])
                        st["pending"] = None
                    else:
                        q = int(math.floor(equity / px))
                        if q <= 0:
                            ev["defects"].append("entry_size_zero:%s"
                                                 % p["sector"])
                            st["pending"] = None
                        else:
                            st["emitted"] = dict(
                                p, fill_session=context.session,
                                intended_qty=q)
                            st["pending"] = None
                            intents.append(Intent(
                                "enter", p["sector"], qty=q,
                                price_hint=round(px, 4),
                                reason=("%s entry %s: worst-sector "
                                        "rotation signal %s, lowage gate "
                                        "passed, entry-month low %.4f; "
                                        "full slice, one position"
                                        % (self.SLEEVE_ID, p["sector"],
                                           p["signal_date"], p["month_low"])),
                                side="buy", position_intent="buy_to_open",
                                signal_date=p["signal_date"]))
                            ev["emitted"] = "enter:%s" % p["sector"]
                else:  # exit decision
                    held = p["sector"]
                    q = abs(qty.get(held) or 0.0)
                    if q == 0:
                        # Position already gone: adopt the flat
                        # reality, drop the decision.
                        st["mode"] = "flat"
                        st["held"] = None
                        st["entry_signal_ym"] = None
                        st["entry_month_low"] = None
                        st["peak_close"] = None
                        st["entry_fill_session"] = None
                        st["pending"] = None
                        ev["defects"].append(
                            "exit_decision_position_absent:%s" % held)
                    else:
                        st["emitted"] = dict(
                            p, fill_session=context.session,
                            intended_qty=None)
                        st["pending"] = None
                        px = series[held]["closes"].get(p["signal_date"])
                        intents.append(Intent(
                            "exit", held, qty=float(q),
                            price_hint=round(px, 4) if px else None,
                            reason=("%s exit %s: %s (signal %s)"
                                    % (self.SLEEVE_ID, held, p["reason"],
                                       p["signal_date"])),
                            side="sell", position_intent="sell_to_close",
                            signal_date=p["signal_date"]))
                        ev["emitted"] = "exit:%s:%s" % (held, p["reason"])
        elif st["emitted"] is not None \
                and st["emitted"]["action"] == "exit" \
                and st["emitted"].get("fill_session", "") < context.session \
                and qty.get(st["emitted"]["sector"]):
            # An exit whose fill session has completed but whose
            # position is still present (unconfirmed / partial):
            # re-emit once per session under the same decision.
            em = st["emitted"]
            if em.get("reemit_session") != context.session:
                em["reemit_session"] = context.session
                em["fill_session"] = context.session
                held = em["sector"]
                q = abs(qty.get(held) or 0.0)
                px = series[held]["closes"].get(em["signal_date"])
                intents.append(Intent(
                    "exit", held, qty=float(q),
                    price_hint=round(px, 4) if px else None,
                    reason=("%s exit %s: %s (signal %s; re-emitted, "
                            "prior fill unconfirmed)"
                            % (self.SLEEVE_ID, held, em["reason"],
                               em["signal_date"])),
                    side="sell", position_intent="sell_to_close",
                    signal_date=em["signal_date"]))
                ev["emitted"] = "exit_reemit:%s:%s" % (held, em["reason"])
        ev["mode"] = st["mode"]
        ev["held"] = st["held"]
        st["defects"] = list(ev["defects"])
        return intents


_INSTANCE = CoffinRebuiltSleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.coffin_state = _INSTANCE.coffin_state
    return out
