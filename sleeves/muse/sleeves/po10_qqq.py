"""po10_qqq — Milkman's PO10 extreme algo, automated for the
lean paper desk (2026-10-21), as a TRANSLATION in QQQ shares.

THE ORIGINAL (his thread, Aug 26 2026, status 2092599219521507760;
research record MILKMAN-PO10-FOUND.md). Saty Phase Oscillator on
the NQ 10-minute chart, extended hours: a 10m PO close above +100
goes long, below -100 goes short; entries 09:30-11:00 ET only;
exit on the opposite cross, or flat at the close; NO stop, NO
target — the exit rule is the whole risk model. His published
line for that configuration (since 2019, 1 NQ contract, friction
included): 392 trades, 59% win rate, PF 1.86, +$259,883, max
drawdown -$29,707. Those are NQ futures numbers from his
backtest; nothing in this sleeve reproduces or claims them.

THE TRANSLATION, STATED PLAINLY. NQ futures are not tradeable on
this desk's Alpaca paper API (verified 2026-10-21: the futures
asset class returns empty and the NQ contracts return 404), so
the position is taken in QQQ SHARES — the linear Nasdaq-100
expression — through the desk's existing equity path. No options:
their convexity and decay would distort a linear futures system.
Every result this sleeve produces is a QQQ result, never an NQ
result. Known translation gaps, named once: QQQ extended-hours
prices are not NQ extended-hours prices (session liquidity,
futures basis, and a QQQ/NQ ratio that drifts); his fills were
simulated at the next 1-minute open while the desk's are paper
fills at the prevailing quote when the signal is evaluated; and
the desk's SIP bars lag the futures tape (the producer's recency
clamp), so signals are read later than his backtest read them.

SIZING (his own portfolio construction). His dashboard's $50K
portfolio runs 2 MNQ. One MNQ pays $2 per NQ point, so the
exposure is $4 of P&L per NQ point: shares = round(4 x NQ_level
/ QQQ_price), a pure function of the two prices. This desk has
no NQ feed, so the NQ reference level is QQQ x 41.0 — a
documented constant (QQQ tracks the Nasdaq-100 at roughly 1/41
of the index; DESK-CHOICE PO10-5). The sleeve sizes exactly
that many shares, one position at a time, no adds.

ENTRY SEMANTICS (dashboard tiebreaks, logged in the build
report). His dashboard's morning sleeves define the signal as
the FIRST close beyond +/-100 inside the window — implemented
state-based (DESK-CHOICE PO10-1): the first completed 10m close
of the session whose close time falls in [09:30, 11:00) ET and
whose PO is beyond the threshold is the signal, whether the
cross itself printed in-window or earlier. "Flat at the close"
is the dashboard's own convention — its sleeves flat at 15:59
ET (PO10-2). One entry per session, no flip on the exit close,
no re-entry after an opposite-cross exit (PO10-3, enforced
from broker-truth session fills). The signal fires only while
fresh — 1800s after its close, the saty_day one-shot convention
that covers the SIP clamp (PO10-4); a signal first seen stale
is spent and stamped, never backfilled.

DESK SHAPE. CONFIG + signal() in the bilbo_options / saty_day
idiom: a pure function of the bars and broker state it is
handed, deterministically reconstructed on every tick (the desk
is process-per-pass; position facts come from the broker's
record, which is truth). Indicator math comes only from the
landed port (core/saty_bars, core/saty_indicators) run on QQQ
10-minute bars over the extended session 04:00-20:00 ET,
aggregated from the desk's 5-minute SIP door on the clock grid.
Only COMPLETED 10m bars are ever read: a bar counts when its
full 10-minute span has closed (an unfinished bucket built from
a partial set of 5-minute constituents never signals — the
trap the tests prove). Every decision — signal close, entry,
opposite-cross exit, end-of-day flat, window skip, spent
signal — is stamped onto self.last_evaluation, which the
dispatcher merges into the evaluation ledger row; intents are
filed through the Ink intent door at dispatch. No bars = no
signal: missing data stands the sleeve down, it never guesses.
Intent.stop / Intent.target are NEVER set: this system has no
stop and no target by design, and the fields would feed the
broker protection-stop path — a different, wrong exit system.
"""
from datetime import date, datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

from core.data import is_trading_day
from core.early_close import EARLY_CLOSES as _SHARED_EARLY_CLOSES
from core.sleeve import BaseSleeve, Intent, SleeveConfig
from core import saty_bars as sb
from core import saty_indicators as si

ET = ZoneInfo("America/New_York")
SYM = "QQQ"

CONFIG = SleeveConfig(
    sleeve_id="po10_qqq",
    cadence_s=60,
    universe=("QQQ",),
    state_schema={"position": "dict|None"},
    # Sizing is his fixed exposure rule (2 MNQ equivalents), not
    # a risk_pct budget; the register value is None by design.
    risk_pct=None,
)

# -- his numbers (thread + dashboard, MILKMAN-PO10-FOUND) -------
PO_THRESHOLD = 100.0           # strict: beyond, never at
WINDOW_START = dtime(9, 30)    # entries 09:30-11:00 ET
WINDOW_END = dtime(11, 0)      # a close AT 11:00 does not enter
FLAT_T = dtime(15, 59)         # the dashboard's flat convention
MNQ_COUNT = 2                  # his $50K portfolio construction
MNQ_USD_PER_POINT = 2.0        # 1 MNQ = $2 per NQ point
USD_PER_NQ_POINT = MNQ_COUNT * MNQ_USD_PER_POINT   # $4.00
# PO10-5: no NQ feed exists on this desk; QQQ tracks the
# Nasdaq-100 at roughly 1/41 of the index. Documented constant;
# its drift is a named translation gap, not a hidden one.
NQ_QQQ_MULTIPLIER = 41.0
ENTRY_FRESH_S = 1800.0         # PO10-4 one-shot freshness
QUOTE_STALE_S = 60.0           # desk IEX quote convention

# NYSE early closes (13:00 ET); the flat mark derives from the
# session close the same way saty_day's clock does (its D-16
# table, same desk convention). Fully closed days are the
# calendar's business (core.data.is_trading_day).
EARLY_CLOSES = _SHARED_EARLY_CLOSES  # core/early_close.py (D-B3 cure: one shared table)


def flat_dt(session_iso):
    """The session's flat moment: one minute before the cash
    close (16:00 ET, or the named early close) — the dashboard's
    'flat 15:59 ET' convention (PO10-2)."""
    d = date.fromisoformat(session_iso)
    close_t = EARLY_CLOSES.get(session_iso, dtime(16, 0))
    return datetime.combine(d, close_t, tzinfo=ET) \
        - timedelta(minutes=1)


def beyond(po, direction):
    """Strict threshold test (his rule: closes ABOVE +100 /
    BELOW -100). A close at exactly +/-100 is not a signal."""
    if po is None:
        return False
    return po > PO_THRESHOLD if direction > 0 else po < -PO_THRESHOLD


def in_entry_window(close_dt, session_d):
    """A signal close qualifies when it lands on the session
    date with a close time in [09:30, 11:00) ET: a 10:59 close
    enters; a close at 11:00 or later does not."""
    return close_dt.date() == session_d \
        and WINDOW_START <= close_dt.time() < WINDOW_END


def nq_level_from_qqq(qqq_price):
    """The NQ reference level implied by a QQQ price (PO10-5)."""
    return float(qqq_price) * NQ_QQQ_MULTIPLIER


def shares_for(qqq_price, nq_level, usd_per_point=USD_PER_NQ_POINT):
    """QQQ shares whose dollar P&L per NQ point equals
    `usd_per_point` (his 2 MNQ = $4/pt): a position of N shares
    moves N x (QQQ/NQ) dollars per NQ point, so
    N = usd_per_point x NQ_level / QQQ_price. Pure; zero on
    unusable prices (no trade, never a guessed size)."""
    try:
        q = float(qqq_price)
        n = float(nq_level)
        u = float(usd_per_point)
    except (TypeError, ValueError):
        return 0
    if q <= 0 or n <= 0 or u <= 0:
        return 0
    return int(round(u * n / q))


def first_signal(closes, session_d):
    """The day's entry signal over completed (close_dt, po)
    pairs: the FIRST close inside the entry window beyond
    either threshold (PO10-1). Returns (close_dt, direction,
    po) or None."""
    for close_dt, po in closes:
        if not in_entry_window(close_dt, session_d):
            continue
        if beyond(po, 1):
            return close_dt, 1, po
        if beyond(po, -1):
            return close_dt, -1, po
    return None


def opposite_cross(closes, direction, after_dt):
    """The first completed close strictly after `after_dt` that
    is beyond the OPPOSITE extreme — his exit. Returns
    (close_dt, po) or None."""
    for close_dt, po in closes:
        if close_dt <= after_dt:
            continue
        if beyond(po, -direction):
            return close_dt, po
    return None


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


def _completed_10m(bars5, now_dt):
    """Completed QQQ 10-minute bars on the clock grid from
    shaped 5-minute bars: extended session only, aggregated
    with the midnight anchor (NQ 10m bars are clock-aligned),
    and a bar counts ONLY when its full 10-minute span has
    closed — end <= now AND span >= 10 minutes — so an
    unfinished bucket assembled from a partial constituent set
    can never signal (the unfinished-bar trap)."""
    ext = sb.filter_session(bars5, "extended")
    m10 = sb.aggregate(ext, 10, anchor="00:00")
    out = []
    for b in m10:
        end = sb.close_time(b)
        if end <= now_dt and end - b["t"] >= timedelta(minutes=10):
            out.append(b)
    return out


class Po10Qqq(BaseSleeve):
    CONFIG = CONFIG

    # ------------------------------------------------------------
    # frame: completed 10m bars + their PO values (port math only)
    # ------------------------------------------------------------
    def _series(self, extra, now_dt):
        """[(close_dt, po, bar_close)] over completed, warmed
        10m bars; None when the feed is absent (fail closed),
        [] when bars exist but the oscillator is not warmed."""
        raw = (extra.get("bars_5m_long") or {}).get(SYM)
        if not raw:
            return None
        m10 = _completed_10m(sb.with_end(_shape(raw), 5), now_dt)
        if not m10:
            return []
        rows = si.phase_oscillator(m10, session_basis="extended")["rows"]
        out = []
        for bar, row in zip(m10, rows):
            if not row.get("warmed_up"):
                continue
            out.append((sb.close_time(bar), row.get("phase_oscillator"),
                        bar["close"]))
        return out

    def _quote(self, extra, now_epoch):
        """(bid, ask, mid) from the IEX latest-quote door when
        two-sided and <= QUOTE_STALE_S old; else None."""
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
    # position management (broker truth; his two exits only)
    # ------------------------------------------------------------
    def _manage(self, series, pos, extra, ctx, now_dt, stamp):
        qty = float(pos.get("qty") or 0)
        direction = 1 if qty > 0 else -1
        stamp["position"] = {"qty": qty,
                             "direction": direction,
                             "entry_px": pos.get("entry_px")}
        fill_epoch = pos.get("fill_t") or pos.get("entry_t")
        if fill_epoch:
            fill_dt = datetime.fromtimestamp(float(fill_epoch), tz=ET)
        else:
            fill_dt = datetime.combine(
                date.fromisoformat(ctx.session), dtime(0, 0), tzinfo=ET)
        if pos.get("entry_date") and pos["entry_date"] < ctx.session:
            stamp["overnight_residual"] = True
        pairs = [(c_dt, po) for c_dt, po, _c in series]
        rule, x_dt, x_po = None, None, None
        hit = opposite_cross(pairs, direction, fill_dt)
        if hit is not None:
            rule, (x_dt, x_po) = "opposite_cross", hit
        elif now_dt >= flat_dt(ctx.session):
            rule = "eod_flat"
        if rule is None:
            stamp["state"] = "holding"
            return []
        quote = self._quote(extra, ctx.now)
        last_close = series[-1][2] if series else None
        if direction > 0:      # sell a long out
            limit = quote[0] if quote else last_close
            side, pi = "sell", "sell_to_close"
        else:                  # buy a short back
            limit = quote[1] if quote else last_close
            side, pi = "buy", "buy_to_close"
        if limit is None or float(limit) <= 0:
            stamp["state"] = "exit_unpriced"
            return []
        limit = round(float(limit), 2)
        stamp["state"] = "exit"
        stamp["decision"] = f"exit_{rule}"
        stamp["exit"] = {
            "rule": rule,
            "cross_close": x_dt.isoformat() if x_dt else None,
            "cross_po": round(x_po, 2) if x_po is not None else None,
            "qty": abs(qty), "limit": limit}
        reason = (
            f"po10_qqq exit {rule}: "
            f"{'long' if direction > 0 else 'short'} "
            f"qty={abs(qty):g} limit={limit:.2f} "
            + (f"cross_close={x_dt.isoformat()} cross_po={x_po:.2f} "
               if rule == "opposite_cross" else
               f"flat_at={flat_dt(ctx.session).isoformat()} ")
            + "translation=QQQ shares for NQ futures (PO10)")
        return [Intent(
            "exit", SYM, qty=abs(qty), limit_price=limit,
            price_hint=limit, side=side, position_intent=pi,
            reason=reason, signal_date=ctx.session)]

    def _blocked_exit(self, extra, ctx, now_dt, stamp):
        """READINESS-20261022 F-B1 (D-B1 class): the hard EOD flat
        needs no series — when a position is held and the flat
        moment has arrived (or the position is a prior session's
        survivor), emit the flat exit priced off the quote door
        when a fresh quote exists, unpriced (the desk's market
        exit door) when it does not."""
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYM) or {}).get("position")
        if not isinstance(pos, dict) \
                or float(pos.get("qty") or 0) == 0:
            return []
        qty = float(pos.get("qty") or 0)
        overnight = bool(pos.get("entry_date")
                         and pos["entry_date"] < ctx.session)
        if not overnight and now_dt < flat_dt(ctx.session):
            return []
        direction = 1 if qty > 0 else -1
        quote = self._quote(extra, ctx.now)
        if direction > 0:
            limit = quote[0] if quote else None
            side, pi = "sell", "sell_to_close"
        else:
            limit = quote[1] if quote else None
            side, pi = "buy", "buy_to_close"
        limit = round(float(limit), 2) if limit else None
        rule = "overnight_flat_blocked_data" if overnight \
            else "eod_flat_blocked_data"
        stamp["state"] = "blocked_data"
        stamp["decision"] = f"exit_{rule}"
        stamp["exit"] = {"rule": rule, "qty": abs(qty),
                         "limit": limit}
        return [Intent(
            "exit", SYM, qty=abs(qty), limit_price=limit,
            price_hint=limit, side=side, position_intent=pi,
            reason=(f"po10_qqq exit {rule}: "
                    f"{'long' if direction > 0 else 'short'} "
                    f"qty={abs(qty):g} "
                    f"flat_at={flat_dt(ctx.session).isoformat()} "
                    "translation=QQQ shares for NQ futures (PO10)"),
            signal_date=ctx.session)]

    # ------------------------------------------------------------
    # the evaluation
    # ------------------------------------------------------------
    def signal(self, bars, slice_state, ctx):
        stamp = {"sleeve": "po10_qqq", "session": ctx.session,
                 "instrument": "QQQ shares (translation of NQ "
                 "futures PO10; not an NQ result)"}
        self.last_evaluation = stamp
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        session_d = date.fromisoformat(ctx.session)
        if not is_trading_day(session_d):
            stamp["state"] = "not_a_trading_day"
            return []
        extra = ctx.extra or {}
        series = self._series(extra, now_dt)
        if series is None:
            stamp["state"] = "blocked_data"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        if not series:
            stamp["state"] = "blocked_warmup"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        closes = [(c_dt, po) for c_dt, po, _c in series]
        last_dt, last_po, _ = series[-1]
        stamp["po_last"] = {"close": last_dt.isoformat(),
                            "value": (round(last_po, 2)
                                      if last_po is not None else None)}
        stamp["state"] = "armed"

        # position first (broker truth): manage, never add.
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYM) or {}).get("position")
        if isinstance(pos, dict) and float(pos.get("qty") or 0) != 0:
            return self._manage(series, pos, extra, ctx, now_dt,
                                stamp)

        # one entry per session (PO10-3), proven from the
        # session's own fill rows — broker truth, not memory.
        fills = extra.get("session_fills")
        if fills is None:
            # D-B4 cure (2026-10-22): the one-entry-per-session
            # law is proven from these fills; with the door absent
            # it cannot be proven, so entries fail closed (the
            # position branch above already ran — exits are
            # unaffected).
            stamp["fills_unavailable"] = True
            stamp["state"] = "blocked_no_fills_proof"
            return []
        elif any(f.get("position_intent") in
                 ("buy_to_open", "sell_to_open") for f in fills):
            stamp["state"] = "flat_after_entry"
            stamp["entered_today"] = True
            return []

        sig = first_signal(closes, session_d)
        if sig is None:
            if now_dt.time() < WINDOW_START:
                stamp["state"] = "armed_pre_window"
            elif now_dt.time() < WINDOW_END:
                stamp["state"] = "armed_in_window"
            else:
                stamp["state"] = "window_closed_no_signal"
            return []
        sig_dt, direction, sig_po = sig
        stamp["signal"] = {"close": sig_dt.isoformat(),
                           "po": round(sig_po, 2),
                           "direction": direction}
        age = (now_dt - sig_dt).total_seconds()
        if age > ENTRY_FRESH_S or age < -60:
            stamp["state"] = "signal_spent"
            return []

        quote = self._quote(extra, ctx.now)
        ref = quote[2] if quote else series[-1][2]
        shares = shares_for(ref, nq_level_from_qqq(ref))
        if shares <= 0:
            stamp["state"] = "size_zero"
            return []
        if direction > 0:
            limit = quote[1] if quote else ref
            side, pi, word = "buy", "buy_to_open", "long"
        else:
            limit = quote[0] if quote else ref
            side, pi, word = "sell", "sell_to_open", "short"
        limit = round(float(limit), 2)
        stamp["state"] = "enter"
        stamp["decision"] = f"enter_{word}"
        stamp["entry"] = {"qty": shares, "limit": limit,
                          "ref": round(float(ref), 2),
                          "nq_level_approx": round(
                              nq_level_from_qqq(ref), 1),
                          "usd_per_nq_point": USD_PER_NQ_POINT}
        reason = (
            f"po10_qqq enter {word}: PO 10m close "
            f"{sig_po:.2f} beyond {'+100' if direction > 0 else '-100'} "
            f"at {sig_dt.isoformat()} in window 09:30-11:00 ET; "
            f"shares={shares} (2 MNQ equiv: $4.00/NQ pt x NQ "
            f"~{nq_level_from_qqq(ref):.0f} / QQQ {ref:.2f}); "
            f"limit={limit:.2f} "
            "translation=QQQ shares for NQ futures (PO10)")
        return [Intent(
            "enter", SYM, qty=shares, limit_price=limit,
            price_hint=round(float(ref), 2), side=side,
            position_intent=pi, reason=reason,
            signal_date=ctx.session)]


def signal(bars, slice_state, context):
    return Po10Qqq().signal(bars, slice_state, context)
