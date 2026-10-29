"""em_1587 — Azrael's 15.87 Rule, automated for the lean
paper desk (AZRAEL-1587-20261022), from the reverse
engineering in ~/workspace/opt/rea-teardowns/azrael-1587/
(TEARDOWN.md, MATH-RECONSTRUCTION.md, SPEC.md). Build report:
ports/em_1587.md.

THE SYSTEM (his document, implemented as written; the spec's
reconstruction decisions RD-1..RD-12 are parameters, bound in
core/em_1587.py). Before the open: EM% = prior ^VIX close /
15.87; EM points = EM% x prior close, rounded to 0.1 pt
BEFORE lines are drawn. Five lines: close +/- EM (walls),
close +/- EM/2 (shelves), close (magnet). Regime off the same
VIX print: < 15 FADE (fade the edges toward the magnet);
15-18.5 CONFIRM (trades only on three-ticker confirmation);
> 18.5 FAST (never fade, size down). The lines are
cross-checked against the three biggest open-interest
strikes above and below price (filed context; RD-8/RD-9).
Entries 09:50-11:05 ET only; flat at 11:30 ET, hard; at most
one setup position per session. The one full setup, in
CONFIRM and FAST: the Three-Ticker Break — SPY (the map
ticker), SPY and QQQ each close outside their own first-20-
minute box (box width <= 0.2 x that ticker's EM) on the same
completed 5-minute bar, break distance >= 0.05 x EM, with
more than 8 points of room to the next map line and at least
1R (1R = entry close to the box edge); target = that next
line; stop = a completed 5-minute close back inside the SPY
box. In FADE: price reaching a wall emits the fade toward the
magnet; target the magnet; stop bound by RD-10 to the
pre-written session 1R (see DC-3 — a reconstruction, never
the author's rule; the source names no fade stop).

THE TRANSLATION, STATED PLAINLY. SPX has no price feed on
this desk's Alpaca doors (verified 2026-10-21: SPX bars and
quotes return nothing), so the map is computed in SPY terms —
prior SPY close, SPY-scaled EM — and the three tickers are
SPY (map), SPY, QQQ per RD-6 mechanics on desk instruments.
Execution is SPY 0DTE options, at-the-money or nearest, long
calls for upside breaks / long puts for downside breaks and
the fade's direction, through the desk's existing options
path — the same expression saty_day uses. SPX-denominated
constants convert at SPX_SCALE = 10 (DC-1). Every result this
sleeve produces is a SPY result, never an SPX result.

SIZING (RD-12 — the source has no contract-count formula):
DESK-CHOICE DC-8 = premium 4% of the sleeve's virtual slice
equity per position (the desk's standing day-sleeve
convention from saty_day), 1-contract minimum, ONE position
at a time across both setups, no adds; in FAST the budget
halves (the source's "size down," quantified as half).

DESK-CHOICEs (all logged in ports/em_1587.md):
  DC-1 SPX_SCALE = 10.0: RD-7's 8 SPX points of room = 0.8
       SPY points; RD-8's 5 SPX points of OI tolerance = 0.5.
  DC-2 regime names FADE / CONFIRM / FAST (the spec's CALM /
       MIXED / FAST).
  DC-3 session 1R = EM/2 (the map's station spacing) fills
       the worksheet's pre-written 1R slot; the fade's stop
       is a completed 5m close beyond the entry wall by that
       1R against the fade. Source-unspecified; a
       reconstruction.
  DC-4 SPEC 3.5 touch counts and 3.6 flow check are NOT
       built: filed context analytics in the source's own
       form; no trading decision consumes them.
  DC-5 same-bar ties: Break — target touch before stop close;
       fade — stop close before target touch.
  DC-6 fade touches count only on bars closing inside the
       entry window; a bar touching both walls stands the
       fade down (ambiguous).
  DC-7 the OI door reads the same contracts snapshot window
       the desk's GEX publisher reads (expiries within 35
       days), via run_live's one raw OI pull.
  DC-8 sizing above.

DESK SHAPE. CONFIG + signal() in the bilbo_options /
saty_day idiom: a pure function of the bars and broker state
it is handed, deterministically reconstructed on every tick
— the map from the prior closes + VIX print, the boxes from
the morning's first four bars, management facts replayed
from the day's bars up to the fill. Every decision — map,
regime, boxes, OI cross-check, signals, skips with reasons,
exits, the 11:30 flat, a NO_TRADE_DAY naming its missing
input — is stamped onto self.last_evaluation (Ink filing at
dispatch). Intent.stop / Intent.target are NEVER set: exits
are the sleeve's own completed-close rules, and those fields
would feed a different exit system.
"""
from datetime import date, datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

from core.data import is_trading_day
from core.sleeve import BaseSleeve, Intent, SleeveConfig
from core import em_1587 as em
from core import saty_bars as sb

ET = ZoneInfo("America/New_York")
SYM = "SPY"
CONFIRM_SYM = "QQQ"

CONFIG = SleeveConfig(
    sleeve_id="em_1587",
    cadence_s=60,
    universe=("SPY", "QQQ"),
    state_schema={"position": "dict|None"},
    risk_pct=0.04,
)

# -- desk conventions (saty_day's, unchanged) ------------------
BUDGET_PCT = 0.04              # DC-8: premium budget per entry
EXPIRY_DTE = 0                 # SPY 0DTE expression
QUOTE_STALE_S = 60.0           # fresh-quote door discipline
SPREAD_MAX_FRAC = 0.05         # entry quote spread gate
ENTRY_FRESH_S = 1800.0         # one-shot signal freshness
ROOM_MIN_ANCHOR = em.ROOM_MIN_SPX / em.SPX_SCALE   # DC-1: 0.8
AGREE_TOL_ANCHOR = em.AGREE_TOL_SPX / em.SPX_SCALE  # DC-1: 0.5

# NYSE early closes (13:00 ET) — the funded-range denominator
# is the ACTUAL session length (RD-4); the 11:30 flat and the
# 09:50-11:05 window are clock constants on every session.
# READINESS-20261022 F-A4 (D-B3 class): the ONE shared table —
# this sleeve's private copy had drifted (missing 2027-07-02 /
# 2027-12-23 and every 2029-2030 entry; session_minutes read
# 390 where the correct value is 210).
from core.early_close import EARLY_CLOSES as EARLY_CLOSES  # noqa: F401


def session_close_dt(session_iso):
    d = date.fromisoformat(session_iso)
    return datetime.combine(
        d, EARLY_CLOSES.get(session_iso, dtime(16, 0)),
        tzinfo=ET)


def session_minutes(session_iso):
    """Minutes from the 09:30 open to the session's cash
    close: 390 on a full day, 210 on a 13:00 early close."""
    d = date.fromisoformat(session_iso)
    open_dt = datetime.combine(d, dtime(9, 30), tzinfo=ET)
    return int((session_close_dt(session_iso)
                - open_dt).total_seconds() // 60)


def flat_dt(session_iso):
    """The hard flat: 11:30 ET, regardless of state."""
    return datetime.combine(date.fromisoformat(session_iso),
                            em.FLAT_T, tzinfo=ET)


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


def _kind(occ):
    """The C/P letter of an OCC symbol (root + YYMMDD + C/P +
    8-digit strike): position -9 from the end."""
    return occ[-9] if occ and len(occ) >= 9 else ""


class Em1587(BaseSleeve):
    CONFIG = CONFIG

    # ------------------------------------------------------------
    # frame: map inputs from the doors (fail closed, named)
    # ------------------------------------------------------------
    def _frame(self, extra, session_d, session_iso, now_dt):
        """Assemble everything the rule reads. Returns a frame
        dict, or {"missing": [...]} — the caller files a
        NO_TRADE_DAY naming the missing inputs (SPEC 1: if you
        cannot write all five numbers, you do not trade)."""
        raw = extra.get("bars_5m_long") or {}
        missing = []
        shaped = {}
        for sym in (SYM, CONFIRM_SYM):
            if not raw.get(sym):
                missing.append(f"bars_5m_long:{sym}")
            else:
                shaped[sym] = sb.with_end(_shape(raw[sym]), 5)
        vix_close = None
        series = extra.get("vix_series")
        if series:
            best = None
            for row in series:
                try:
                    if isinstance(row, dict):
                        d_iso, c = row["date"], float(row["close"])
                    else:
                        d_iso, c = row[0], float(row[1])
                except (KeyError, TypeError, ValueError,
                        IndexError):
                    continue
                if d_iso < session_iso \
                        and (best is None or d_iso > best[0]):
                    best = (d_iso, c)
            if best is not None:
                vix_close = best[1]
        if vix_close is None:
            missing.append("vix_close")
        if missing:
            return {"missing": missing}
        frame = {"vix_close": vix_close}
        for sym in (SYM, CONFIRM_SYM):
            reg = sb.filter_session(shaped[sym], "regular")
            daily = {}
            for b in sb.aggregate_daily(reg):
                daily[b["t"].date().isoformat()] = float(b["close"])
            prior = [d for d in daily if d < session_iso]
            if not prior:
                return {"missing": [f"prior_close:{sym}"]}
            frame[f"prior_close:{sym}"] = daily[max(prior)]
            today = []
            for b in reg:
                if b["t"].date() != session_d:
                    continue
                ct = sb.close_time(b)
                if ct <= now_dt:      # completed bars only
                    nb = dict(b)
                    nb["close_dt"] = ct
                    today.append(nb)
            frame[f"today:{sym}"] = today
        plan = em.build_map(
            frame[f"prior_close:{SYM}"], vix_close,
            session_minutes=session_minutes(session_iso))
        frame["plan"] = plan
        frame[f"em:{CONFIRM_SYM}"] = em.expected_move(
            frame[f"prior_close:{CONFIRM_SYM}"], vix_close)
        frame["box:SPY"] = em.morning_box(frame["today:SPY"],
                                          session_d)
        frame["box:QQQ"] = em.morning_box(frame["today:QQQ"],
                                          session_d)
        oi = extra.get("oi_by_strike")
        if oi:
            shortlist = em.oi_shortlist(
                oi, frame[f"prior_close:{SYM}"])
            frame["oi"] = {
                "shortlist": shortlist,
                "agreement": em.line_agreement(
                    plan["lines"], shortlist, AGREE_TOL_ANCHOR)}
        else:
            frame["oi"] = None
        return frame

    def _file_map(self, stamp, frame):
        plan = frame["plan"]
        stamp["map"] = {
            "anchor_close": plan["anchor_close"],
            "vix_close": plan["vix_close"],
            "pct": round(plan["pct"], 4),
            "em": plan["em"],
            "lines": plan["lines"],
            "regime": plan["regime"],
            "session_1r": plan["session_1r"],
            "funded_at_flat": round(plan["funded_at_flat"], 2),
            "weekly_em": plan["weekly_em"],
            "em_qqq": frame[f"em:{CONFIRM_SYM}"],
            "oi": frame["oi"] if frame["oi"] is not None
            else "unavailable",
        }
        boxes = {}
        for sym, em_x in ((SYM, plan["em"]),
                          (CONFIRM_SYM, frame[f"em:{CONFIRM_SYM}"])):
            box = frame[f"box:{sym}"]
            boxes[sym] = ({"hi": box["hi"], "lo": box["lo"],
                           "width": box["width"],
                           "cap": round(em.box_cap(em_x), 4),
                           "ok": em.box_ok(box, em_x)}
                          if box else None)
        stamp["boxes"] = boxes

    # ------------------------------------------------------------
    # quote / contract doors (saty_day's discipline, unchanged)
    # ------------------------------------------------------------
    def _spot(self, extra, today_spy, now_epoch):
        q = (extra.get("latest_quote") or {}).get(SYM)
        if q and q.get("t"):
            try:
                t_epoch = datetime.fromisoformat(
                    str(q["t"]).replace("Z", "+00:00")).timestamp()
                if now_epoch - t_epoch <= 90:
                    return (float(q["bp"]) + float(q["ap"])) / 2.0
            except (KeyError, TypeError, ValueError):
                pass
        return float(today_spy[-1]["close"]) if today_spy else None

    def _fresh_mid(self, extra, occ, now_epoch):
        """(mid, bid, ask) from the fresh-quotes door when the
        quote is two-sided, tight and fresh; else None."""
        q = (extra.get("fresh_quotes") or {}).get(occ)
        if not isinstance(q, dict):
            return None
        try:
            bp, ap = float(q["bp"]), float(q["ap"])
        except (KeyError, TypeError, ValueError):
            return None
        if bp <= 0 or ap < bp:
            return None
        mid = (bp + ap) / 2.0
        if mid <= 0 or (ap - bp) > SPREAD_MAX_FRAC * mid:
            return None
        for key in ("received_at", "t"):
            ts = q.get(key)
            if ts is None:
                continue
            try:
                t_epoch = float(ts) if not isinstance(ts, str) \
                    else datetime.fromisoformat(
                        ts.replace("Z", "+00:00")).timestamp()
            except (TypeError, ValueError):
                return None
            if now_epoch - t_epoch > QUOTE_STALE_S:
                return None
        return mid, bp, ap

    def _pick_contract(self, extra, session_d, kind, spot):
        """The 0DTE expression: nearest expiry at dte == 0,
        strike nearest spot, of the entry direction's kind."""
        rows = (extra.get("chains") or {}).get(SYM) or []
        best = None
        for r in rows:
            occ = r.get("symbol")
            if not occ or _kind(occ) != kind:
                continue
            try:
                dte = (date.fromisoformat(r["expiration"])
                       - session_d).days
                strike = float(r["strike"])
            except (KeyError, TypeError, ValueError):
                continue
            if dte != EXPIRY_DTE:
                continue
            key = (abs(strike - spot), strike)
            if best is None or key < best[0]:
                best = (key, occ, strike, r["expiration"])
        if best is None:
            return None
        return {"occ": best[1], "strike": best[2],
                "expiration": best[3]}

    def _size(self, equity, mid, half):
        budget = BUDGET_PCT * float(equity) * (0.5 if half
                                                else 1.0)
        per = float(mid) * 100.0
        qty = int(budget // per) if per > 0 else 0
        overshoot = qty < 1
        return max(1, qty), budget, overshoot

    # ------------------------------------------------------------
    # exits (the sleeve's own rules; priced off the snapshot
    # door on saty_day's ladder, keyed to the 11:30 flat)
    # ------------------------------------------------------------
    def _exit_intent(self, pos, qty, rule, extra, ctx, now_dt,
                     facts, stamp):
        occ = pos.get("occ")
        snap = ((extra.get("quotes") or {}).get(occ)
                if occ else None)
        f_dt = flat_dt(ctx.session)
        limit = None
        market = False
        if snap is not None:
            try:
                bp, ap = float(snap["bid"]), float(snap["ask"])
                mid = (bp + ap) / 2.0
            except (KeyError, TypeError, ValueError):
                bp = ap = mid = None
            if mid is not None and mid > 0:
                if now_dt >= f_dt - timedelta(minutes=2):
                    market = True
                elif now_dt >= f_dt - timedelta(minutes=5):
                    limit = round(bp, 2)     # aggressive side
                else:
                    limit = round(mid, 2)
        if limit is None and not market:
            if now_dt >= f_dt - timedelta(minutes=2):
                market = True               # flat is hard
            else:
                stamp["state"] = "exit_pending_no_quote"
                stamp["exit_rule"] = rule
                return []
        stamp["state"] = "exit"
        stamp["decision"] = f"exit_{rule}"
        stamp["exit"] = dict(facts, rule=rule, qty=qty,
                             occ=occ, limit=limit,
                             market=market)
        reason = (
            f"em_1587 exit {rule}: occ={occ} qty={qty:g} "
            f"{'market (11:30 flat is hard)' if market else f'limit={limit:.2f}'} "
            f"facts={facts} "
            "translation=SPY map + SPY 0DTE options for SPX "
            "(15.87 Rule)")
        return [Intent(
            "exit", SYM, qty=qty, limit_price=limit,
            price_hint=limit, side="sell",
            position_intent="sell_to_close", reason=reason,
            signal_date=ctx.session)]

    def _manage(self, pos, frame, extra, ctx, now_dt, stamp):
        plan = frame["plan"]
        lines = plan["lines"]
        occ = pos.get("occ") or ""
        qty = float(pos.get("qty") or 0)
        direction = 1 if _kind(occ) == "C" else -1
        setup = "fade" if plan["regime"] == em.REGIME_FADE \
            else "break"
        stamp["position"] = {"occ": occ, "qty": qty,
                             "direction": direction,
                             "setup": setup,
                             "entry_px": pos.get("entry_px")}
        fill_epoch = pos.get("fill_t") or pos.get("entry_t")
        if fill_epoch:
            fill_dt = datetime.fromtimestamp(float(fill_epoch),
                                             tz=ET)
        else:
            fill_dt = datetime.combine(
                date.fromisoformat(ctx.session), dtime(0, 0),
                tzinfo=ET)
        facts = {"setup": setup, "direction": direction}
        # a prior session's survivor flats at first evaluation
        pos_day = pos.get("signal_date") or pos.get("entry_date")
        if pos_day and pos_day < ctx.session:
            return self._exit_intent(
                pos, qty, "overnight_flat", extra, ctx, now_dt,
                dict(facts, pos_day=pos_day), stamp)
        spy_today = frame["today:SPY"]
        bars_after = [b for b in spy_today
                      if b["close_dt"] > fill_dt]
        rule = None
        if now_dt >= flat_dt(ctx.session):
            rule = "flat_1130"
        elif setup == "break":
            replay = em.find_break(
                [b for b in spy_today if b["close_dt"] <= fill_dt],
                [b for b in frame["today:QQQ"]
                 if b["close_dt"] <= fill_dt],
                frame["box:SPY"], frame["box:QQQ"],
                plan["em"], frame[f"em:{CONFIRM_SYM}"], lines,
                date.fromisoformat(ctx.session), ROOM_MIN_ANCHOR)
            if replay.get("state") == "signal" \
                    and replay["direction"] == direction:
                hit = em.break_exit(bars_after, direction,
                                    frame["box:SPY"],
                                    replay["target"])
                if hit:
                    rule, bar = hit
                    facts.update(
                        target=replay["target"],
                        deciding_close=bar["close_dt"].isoformat())
            else:
                stamp["manage_replay_missing"] = replay.get(
                    "state")
        else:
            replay = em.find_fade(
                [b for b in spy_today if b["close_dt"] <= fill_dt],
                lines, plan["session_1r"],
                date.fromisoformat(ctx.session))
            if replay.get("state") == "signal" \
                    and replay["direction"] == direction:
                entry_line = replay["entry_line"]
            else:
                # the fade's facts are fully determined by the
                # direction and the frozen map (DC-3).
                entry_line = (lines["WALL_DN"] if direction > 0
                              else lines["WALL_UP"])
                stamp["manage_replay_fallback"] = True
            hit = em.fade_exit(bars_after, direction, entry_line,
                               lines["MAGNET"],
                               plan["session_1r"])
            if hit:
                rule, bar = hit
                facts.update(
                    entry_line=entry_line,
                    deciding_close=bar["close_dt"].isoformat())
        if rule is None:
            stamp["state"] = "holding"
            return []
        return self._exit_intent(pos, qty, rule, extra, ctx,
                                 now_dt, facts, stamp)

    # ------------------------------------------------------------
    # the evaluation
    # ------------------------------------------------------------
    def signal(self, bars, slice_state, ctx):
        stamp = {"sleeve": "em_1587", "session": ctx.session,
                 "system": "Azrael 15.87 Rule (RD-1..RD-12)",
                 "translation": "SPY map + SPY 0DTE options "
                 "(no SPX cash feed on desk doors)"}
        self.last_evaluation = stamp
        session_d = date.fromisoformat(ctx.session)
        if not is_trading_day(session_d):
            stamp["state"] = "not_a_trading_day"
            return []
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        extra = ctx.extra or {}
        frame = self._frame(extra, session_d, ctx.session,
                            now_dt)
        if "missing" in frame:
            # READINESS-20261022 F-A4 (D-B1 class): the time-based
            # exits — a prior session's overnight flat and the hard
            # 11:30 flat — need no frame and run BEFORE the
            # NO_TRADE_DAY stand-down. _exit_intent's own ladder
            # goes market inside the flat window, so a quoteless
            # blocked pass still flats at/after 11:28.
            _state = extra.get("sleeve_state") or {}
            _pos = (_state.get(SYM) or {}).get("position")
            if isinstance(_pos, dict) \
                    and float(_pos.get("qty") or 0) != 0:
                _qty = float(_pos.get("qty") or 0)
                _pos_day = (_pos.get("signal_date")
                            or _pos.get("entry_date"))
                _rule = None
                if _pos_day and _pos_day < ctx.session:
                    _rule = "overnight_flat"
                elif now_dt >= flat_dt(ctx.session):
                    _rule = "flat_1130"
                if _rule is not None:
                    stamp["missing"] = frame["missing"]
                    return self._exit_intent(
                        _pos, _qty, _rule, extra, ctx, now_dt,
                        {"setup": "blocked_data",
                         "pos_day": _pos_day}, stamp)
            stamp["state"] = "no_trade_day"
            stamp["decision"] = "NO_TRADE_DAY"
            stamp["missing"] = frame["missing"]
            return []
        self._file_map(stamp, frame)
        plan = frame["plan"]

        # position first (broker truth): manage, never add.
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYM) or {}).get("position")
        if isinstance(pos, dict) \
                and float(pos.get("qty") or 0) != 0:
            return self._manage(pos, frame, extra, ctx, now_dt,
                                stamp)

        # one setup a day, proven from the session's own fill
        # rows — broker truth, not memory.
        fills = extra.get("session_fills")
        if fills is None:
            stamp["fills_unavailable"] = True
        elif any(f.get("position_intent") == "buy_to_open"
                 for f in fills):
            stamp["state"] = "one_setup_done"
            stamp["entered_today"] = True
            return []

        if now_dt >= flat_dt(ctx.session):
            stamp["state"] = "past_flat_no_entry"
            return []

        spy_today = frame["today:SPY"]
        if plan["regime"] == em.REGIME_FADE:
            verdict = em.find_fade(spy_today, plan["lines"],
                                   plan["session_1r"], session_d)
            setup = "fade"
        else:
            verdict = em.find_break(
                spy_today, frame["today:QQQ"], frame["box:SPY"],
                frame["box:QQQ"], plan["em"],
                frame[f"em:{CONFIRM_SYM}"], plan["lines"],
                session_d, ROOM_MIN_ANCHOR)
            setup = "break"
        stamp["verdict"] = verdict["state"]
        if verdict["state"] != "signal":
            if verdict["state"] == "no_signal":
                if now_dt.time() < em.WINDOW_START:
                    stamp["state"] = "armed_pre_window"
                elif now_dt.time() <= em.LAST_ENTRY_CLOSE:
                    stamp["state"] = "armed_no_signal"
                else:
                    stamp["state"] = "window_closed_no_signal"
            else:
                vstate = verdict["state"]
                stamp["state"] = vstate if vstate.startswith(
                    "stood_down") else f"stood_down_{vstate}"
                stamp["verdict_facts"] = {
                    k: (v.isoformat() if hasattr(v, "isoformat")
                        else v)
                    for k, v in verdict.items() if k != "state"}
            return []
        sig_close = verdict["close_dt"]
        stamp["signal"] = {
            "setup": setup, "regime": plan["regime"],
            "direction": verdict["direction"],
            "close": sig_close.isoformat(),
            "entry_close": verdict.get("entry_close"),
            "target": verdict.get("target"),
            "target_name": verdict.get("target_name"),
            "one_r": verdict.get("one_r"),
            "room": verdict.get("room"),
            "entry_line": verdict.get("entry_line")}
        age = (now_dt - sig_close).total_seconds()
        if age > ENTRY_FRESH_S or age < -60:
            stamp["state"] = "signal_spent"
            return []

        direction = verdict["direction"]
        spot = self._spot(extra, spy_today, ctx.now)
        if spot is None:
            stamp["state"] = "stood_down_no_spot"
            return []
        pick = self._pick_contract(extra, session_d,
                                   "C" if direction > 0 else "P",
                                   spot)
        if pick is None:
            stamp["state"] = "stood_down_no_same_day_contract"
            return []
        fq = self._fresh_mid(extra, pick["occ"], ctx.now)
        if fq is None:
            stamp["state"] = "stood_down_no_quote"
            stamp["occ"] = pick["occ"]
            return []
        mid, bp, ap = fq
        half = plan["regime"] == em.REGIME_FAST
        qty, budget, overshoot = self._size(ctx.equity, mid,
                                            half)
        limit = round(mid, 2)
        stamp["state"] = "enter"
        stamp["decision"] = (
            f"enter_{setup}_{'long' if direction > 0 else 'short'}")
        stamp["entry"] = {"occ": pick["occ"],
                          "strike": pick["strike"],
                          "qty": qty, "mid": round(mid, 4),
                          "limit": limit,
                          "budget": round(budget, 2),
                          "overshoot_minimum": overshoot,
                          "size_down_fast": half,
                          "spot": round(float(spot), 4)}
        target_txt = (
            f"target={verdict.get('target_name')} "
            f"{verdict.get('target')} (1R={verdict.get('one_r')}, "
            f"room={verdict.get('room')})"
            if setup == "break" else
            f"target=MAGNET {verdict.get('target')} "
            f"(wall={verdict.get('entry_line')}, "
            f"stop=close beyond wall by session 1R "
            f"{plan['session_1r']}, DC-3)")
        reason = (
            f"em_1587 enter {setup} "
            f"{'long' if direction > 0 else 'short'}: "
            f"regime={plan['regime']} VIX={plan['vix_close']} "
            f"EM={plan['em']} anchor={plan['anchor_close']} "
            f"signal_close={sig_close.isoformat()} {target_txt}; "
            f"occ={pick['occ']} strike={pick['strike']:g} "
            f"exp={pick['expiration']} mid={mid:.2f} "
            f"limit={limit:.2f} qty={qty} "
            f"budget={budget:.2f}"
            f"{' (1-contract minimum overshoot)' if overshoot else ''}"
            f"{' SIZE_DOWN FAST x0.5' if half else ''} "
            "translation=SPY map + SPY 0DTE options for SPX "
            "(15.87 Rule)")
        return [Intent(
            "enter", SYM, qty=qty, limit_price=limit,
            price_hint=round(float(spot), 4), side="buy",
            position_intent="buy_to_open", reason=reason,
            signal_date=ctx.session)]


def signal(bars, slice_state, context):
    return Em1587().signal(bars, slice_state, context)
