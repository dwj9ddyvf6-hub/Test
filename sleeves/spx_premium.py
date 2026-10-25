"""SPX Premium — ATR index premium selling (XSP weeklies) — lean port.

EXTRACTED from the old desk's spx_premium.py (Milkman Trades author's
spec, followed exactly there and here). The pure level/settlement
math (Wilder weekly ATR, ATR-level strikes, natural credit, settle
P&L, full-width-loss + cooldown, entry-day rule) is verbatim. See
ports/spx_premium.md.

** NO-CUTOVER-UNTIL-FLAT **: the old desk holds an open XSP 761/756
spread expiring Fri 2026-10-16. Code-complete port; cutover waits
until flat or explicit reconciled state import.

Author's spec: entry on the week's first trading day ~10:00 ET;
short strike = round1(prior weekly close - 1.0 x prior-week ATR14)
(XSP scale; round5 is the SPX-scale original, kept for parity);
long wing 5 points below; expiry = that week's last trading session;
NO exit — hold to settlement (paper adaptation: the core closes both
legs on the last session; here that is an exit intent with reason
"settlement_close" — the sleeve itself has no stop/defense). The close
is ARMED at 15:15 ET (SETTLEMENT_CLOSE_HM, SETTLEFIX 2026-10-16): the
broker rejects PM-settled index option orders placed after the 16:00
close on expiry day, and the desk's sequential pass submits a branch
armed at 15:55 only after the close (proven live 2026-10-16: fired in
the 15:55:19 pass, submitted 16:11:30, Alpaca 422). Armed at 15:15 and
evaluated first in the tick (CONFIG.settlement_exit), the close
submits by 15:45 under the desk's pass cadence;
skip unless natural credit (short bid - wing ask) > 0. 1 lot always.
Equity honesty gate: no entry under $37,000 equity. The gate is an
ACCOUNT-size rule (author's spec): it reads context.account_equity
(the broker account total, door read-back cached at warm), NOT
context.equity, which in v2 is the sleeve's $10k slice — feeding the
slice made the gate unpassable and the sleeve fail-closed forever
(cure 2026-10-24; the sleeve never sizes off equity — 1 lot always —
so no sizing consumer is affected).
Monty Carlo policy: a settlement losing >= 90% of the 5-wide arms a
4-week entry cooldown (state cooldown_until ISO week; settle_pnl +
is_full_width_loss + cooldown_until_week are the core Ledger's
recording helpers, ported here verbatim).

ENH (ENHANCE-DESIGN-spx_premium.md, Edge v3 IMPROVE pass 2026-10-24,
plan R-1): the author's entry gate accepted ANY positive natural
credit for a $500 max loss held to settlement — the reservation-price
leak (a $0.05 credit needs a 99% binary break-even win probability;
the CARA reservation interval for supplied scenarios is $89-$194).
ENH refuses entry when the executable credit is below one third of
the spread's own width (max loss at most twice the credit taken;
binary break-even win probability at most 2/3). Switched by
context.extra["spx_premium_enhance"]["credit_floor"] (default ON;
OFF restores the pre-change credit > 0 rule exactly). Every entry
decision that reaches the credit comparison records a paired
control/treatment record in the spx_premium_enh_journal (adopted
from context.extra, filed on self.last_evaluation); the pre-change
rule is the shadow control and never emits intents. Settlement and
all other rails are untouched.
DECISION #85 as extended by #96 (confirmed #118): net-credit premium
sale — entries EXEMPT from Decision #75 gates (no red-day, no chart
gate staging); carried on the intent reason, as with the condor.

Inputs via context.extra:
  "weekly_bars":  SPY weekly bars (the level series; SPX_EQUIV=1.0)
  "traded_dates": ["YYYY-MM-DD", ...] sessions with SPY 1H bars
  "chains":       {"XSP": [{"symbol","strike","expiration"}]} (puts)
  "quotes":       {OCC: {"bid","ask"}}
  "sleeve_state": {"XSP": {"position": {...}|None,
                    "cooldown_until": [iso_year, iso_week] | None,
                    "last_entry_week": [iso_year, iso_week] | None}}
Bars (arg): unused (levels are weekly; kept for contract uniformity).
The entry clock read is context.now in ET, as the contract requires.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

WING_WIDTH = 5
ATR_PERIOD = 14
SPX_EQUIV = 1.0
LOT_QTY = 1
EQUITY_GATE = 37000.0
ENTRY_HOUR_ET = 10
FULL_WIDTH_LOSS_USD = -(WING_WIDTH * 100.0 * 0.9)
COOLDOWN_WEEKS = 4
UNDERLYING = "XSP"
LEVEL_PROXY = "SPY"
GATE_EXEMPT_DECISION75 = True  # Decision #85 extended by #96

# SETTLEFIX (2026-10-16): the settlement close must SUBMIT by 15:45 ET
# on the expiry session — 15 minutes before the 16:00 close after which
# the broker rejects PM-settled index option orders outright. The arm
# is the deadline minus the worst-case gap to the first tick that can
# see it: passes run back-to-back at <= ~26 min, so arm = 15:45 - 30
# min = 15:15. settlement_exit (below) makes the dispatcher evaluate
# this sleeve first in the tick, so submission ~= first tick start
# >= arm; even the stacked worst case (a 26-min pass starting 15:14:59,
# next tick 15:41) submits ~15:41.
SETTLEMENT_CLOSE_HM = (15, 15)


def settlement_arm_hm(session_iso):
    """The settlement-close arm for a session (D-B2 cure,
    2026-10-22): 15:15 ET on a normal session (SETTLEFIX), or
    45 minutes before an early close (12:15 ET for a 13:00
    close) — the pre-cure fixed 15:15 arm fell two hours AFTER
    an early close, when the broker already rejects PM-settled
    index orders, so no settlement exit could ever fire."""
    from core.early_close import session_close_dt
    close_dt = session_close_dt(session_iso)
    arm = close_dt - timedelta(minutes=45)
    return (arm.hour, arm.minute)

CONFIG = SleeveConfig(
    sleeve_id="spx_premium", cadence_s=300, universe=(UNDERLYING,),
    state_schema={"position": "dict|None", "cooldown_until": "list|None",
                  "last_entry_week": "list|None"},
    risk_pct=None, settlement_exit=True)


# ------------------------------------------------------- verbatim math
def round5(x):
    """Round to the nearest 5 (author's strike rule, SPX scale)."""
    return int(5 * round(float(x) / 5.0))


def round1(x):
    """Round to the nearest 1 (XSP scale: $1 strikes)."""
    return int(round(float(x)))


def wilder_atr(weekly, period=ATR_PERIOD):
    """Wilder ATR over weekly bars; SMA-seeded at index period-1,
    None before. Verbatim (numpy -> lists)."""
    n = len(weekly)
    trs = []
    for i, b in enumerate(weekly):
        pc = float(weekly[i - 1]["c"]) if i > 0 else float(b["c"])
        trs.append(max(float(b["h"]) - float(b["l"]),
                       abs(float(b["h"]) - pc), abs(float(b["l"]) - pc)))
    atr = [None] * n
    if n >= period:
        atr[period - 1] = sum(trs[:period]) / period
        for i in range(period, n):
            atr[i] = atr[i - 1] + (trs[i] - atr[i - 1]) / period
    return atr


def atr_level_strikes(prior_close, atr14):
    """Author's strike rule: (short, long) on the XSP scale."""
    short = round1(prior_close - 1.0 * atr14)
    return short, short - WING_WIDTH


def natural_credit(bid_short, ask_long):
    return float(bid_short) - float(ask_long)


def settle_pnl(credit_pts, k_short, k_long, settle):
    """Settlement P&L in USD for the put credit spread. Verbatim."""
    width = k_short - k_long
    intrinsic_owed = max(0.0, min(k_short - settle, width))
    return credit_pts * 100.0 - intrinsic_owed * 100.0


def is_full_width_loss(pnl_usd):
    return pnl_usd <= FULL_WIDTH_LOSS_USD


def iso_week_tuple(dt):
    iso = dt.isocalendar()
    return [iso[0], iso[1]]


def week_leq(a, b):
    return (a[0], a[1]) <= (b[0], b[1])


def cooldown_until_week(today, weeks=COOLDOWN_WEEKS):
    return iso_week_tuple(today + timedelta(weeks=weeks))


# ------------------------------------------------------------ ENH
ENH_EXP_ID = "ENH-SPX-PREMIUM-20261024"
CREDIT_FLOOR_FRAC = 1.0 / 3.0  # refuse when credit < width / 3


def credit_floor_enabled(extra):
    """ctx.extra['spx_premium_enhance']['credit_floor'], default ON;
    OFF restores the pre-change credit > 0 rule exactly."""
    ov = (extra or {}).get("spx_premium_enhance")
    if isinstance(ov, dict) and "credit_floor" in ov:
        return bool(ov["credit_floor"])
    return True


def _enh_journal(extra):
    raw = (extra or {}).get("spx_premium_enh_journal")
    if isinstance(raw, dict) and raw.get("exp_id") == ENH_EXP_ID \
            and isinstance(raw.get("records"), list):
        return raw
    return {"exp_id": ENH_EXP_ID, "records": []}


def credit_floor_refuses(credit, width=WING_WIDTH):
    """The enhancement's one comparison: executable credit below one
    third of the spread's own width prices the warehoused tail at a
    max loss more than twice the compensation taken. Equality is
    TAKEN (max loss exactly twice the credit)."""
    return width > 0 and credit < CREDIT_FLOOR_FRAC * width - 1e-9


def entry_day_ok(now_et, traded_dates):
    """(ok, reason): now_et (a datetime) is the week's first trading
    day and >= 10:00 ET. Verbatim logic; traded_dates = set of dates."""
    today = now_et.date()
    if today not in traded_dates:
        return False, "market_closed"
    wd = now_et.weekday()
    if wd == 0:
        ok_day, reason = True, "monday"
    elif wd == 1:
        monday = today - timedelta(days=1)
        if monday in traded_dates:
            return False, "not_first_trading_day"
        ok_day, reason = True, "tuesday_after_monday_holiday"
    else:
        return False, "not_first_trading_day"
    if (now_et.hour, now_et.minute) < (ENTRY_HOUR_ET, 0):
        return False, "too_early"
    return ok_day, reason


def prior_week_level(weekly):
    """(prior_close, atr14) from the last COMPLETED weekly bar: the
    old prior_week_level read the weekly frame built from SPY 1H; the
    core supplies completed weekly bars, so the level is the last
    bar's close and its Wilder ATR14. (None, None) when unseeded."""
    if not weekly or len(weekly) < ATR_PERIOD:
        return None, None
    atr = wilder_atr(weekly)
    if atr[-1] is None:
        return None, None
    return float(weekly[-1]["c"]), float(atr[-1])


class SpxPremium(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        st = state.get(UNDERLYING) or {}
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        # Gate-semantic equity ONLY (see header): the account total,
        # never the slice. Fallbacks: extra["account_equity"] for
        # direct-call fixtures; absent account read-back -> 0.0 ->
        # the $37k gate below fails closed.
        _acct = getattr(context, "account_equity", None)
        if callable(_acct):
            _acct = _acct()
        if _acct is None:
            _acct = extra.get("account_equity")
        try:
            equity = float(_acct) if _acct is not None else 0.0
        except (TypeError, ValueError):
            equity = 0.0
        now_et = datetime.fromtimestamp(float(context.now),
                                         tz=timezone.utc).astimezone(ET)
        intents = []
        pos = st.get("position")
        if pos:
            # Settlement: the position's expiry IS the week's last
            # session; on that session the core closes both legs
            # (paper has no PM cash settlement), armed at
            # SETTLEMENT_CLOSE_HM so the order SUBMITS by 15:45 ET —
            # a 15:55 arm inside a sequential pass submitted after
            # the close and was rejected (SETTLEFIX, 2026-10-16).
            # The sleeve has no other exit — no stop, no defense
            # (author's spec).
            if str(pos.get("expiry"))[:10] == context.session \
                    and (now_et.hour, now_et.minute) \
                    >= settlement_arm_hm(context.session):
                qty = int(float(pos.get("qty") or LOT_QTY))
                intents.append(Intent(
                    "exit", UNDERLYING, qty_hint=qty,
                    reason="spx_premium settlement_close: short=%s long=%s "
                           "expiry=%s credit=%.2f (no intraday exit by spec)"
                           % (pos.get("short_occ"), pos.get("long_occ"),
                              pos.get("expiry"), float(pos.get("credit") or 0))))
            return intents
        # ---- entry rails (author's + desk), old run_entry order
        traded = set()
        for d in extra.get("traded_dates") or []:
            try:
                from datetime import date as _date
                traded.add(_date.fromisoformat(str(d)[:10]))
            except ValueError:
                continue
        ok, _reason = entry_day_ok(now_et, traded)
        if not ok:
            return intents
        this_week = iso_week_tuple(now_et)
        if st.get("last_entry_week") == this_week:
            return intents  # already entered this week
        cooldown = st.get("cooldown_until")
        if cooldown and week_leq(this_week, cooldown):
            return intents  # Monty Carlo cooldown still running
            # (old desk, verbatim: skip while week_leq(this_week,
            # cooldown_until) — the cooldown_until week itself is the
            # 4th skipped week; the port's inverted comparison let an
            # entry through in that week, blocking only 3 of 4.)
        if equity < EQUITY_GATE:
            return intents
        weekly = extra.get("weekly_bars") or []
        prior_close, atr14 = prior_week_level(weekly)
        if prior_close is None:
            return intents
        k_short, k_long = atr_level_strikes(prior_close, atr14)
        chain = chains.get(UNDERLYING) or []
        # Expiry: that week's last trading session (author's spec +
        # old run_entry, verbatim): the old code fetched the chain for
        # Mon-Fri of the current week only and took expiries[-1]. The
        # port took the NEAREST expiry on/after today with no week
        # bound — on a Monday entry that is the same-day expiry, not
        # the week's last session. Restrict to this week's Mon-Fri
        # window and take the LAST expiry carrying both strikes.
        from datetime import date as _date
        try:
            _sess = _date.fromisoformat(str(context.session)[:10])
        except ValueError:
            return intents
        _monday = _sess - timedelta(days=_sess.weekday())
        _friday = _monday + timedelta(days=4)
        cands = []
        for c in chain:
            try:
                strike = float(c["strike"])
            except (TypeError, ValueError, KeyError):
                continue
            exp = str(c.get("expiration") or "")[:10]
            if strike in (float(k_short), float(k_long)) \
                    and _monday.isoformat() <= exp <= _friday.isoformat():
                cands.append((exp, strike, c["symbol"]))
        exps = sorted({e for e, _, _ in cands})
        if not exps:
            return intents
        expiry = exps[-1]
        occ = {s: o for e, s, o in cands if e == expiry}
        if float(k_short) not in occ or float(k_long) not in occ:
            return intents
        qs, ql = quotes.get(occ[float(k_short)]) or {}, \
            quotes.get(occ[float(k_long)]) or {}
        try:
            bid_short, ask_long = float(qs.get("bid") or 0), float(ql.get("ask") or 0)
        except (TypeError, ValueError):
            return intents
        credit = natural_credit(bid_short, ask_long)
        if credit <= 0:
            return intents  # author's skip rule: positive credit only
        # ENH paired record: control (pre-change rule) vs treatment
        # (credit floor), evaluated on this same opportunity; the
        # control is shadow-only and never emits intents.
        enh_on = credit_floor_enabled(extra)
        treatment = "refuse_credit_floor" \
            if credit_floor_refuses(credit) else "enter"
        journal = _enh_journal(extra)
        journal["records"].append({
            "session": context.session, "symbol": UNDERLYING,
            "credit": round(credit, 2), "width": WING_WIDTH,
            "floor": round(CREDIT_FLOOR_FRAC * WING_WIDTH, 4),
            "max_loss": round((WING_WIDTH - credit) * 100.0, 2),
            "k_short": k_short, "k_long": k_long, "expiry": expiry,
            "control": "enter", "treatment": treatment,
            "switch_on": enh_on})
        self.last_evaluation = {"spx_premium_enh_journal": journal}
        if enh_on and treatment == "refuse_credit_floor":
            return intents  # ENH refusal: credit below reservation floor
        intents.append(Intent(
            "enter", UNDERLYING, qty_hint=LOT_QTY,
            price_hint=round(prior_close, 2),
            reason="spx_premium put_credit_spread: short=%s@%d long=%s@%d "
                   "expiry=%s credit=%.2f prior_close=%.2f atr14=%.2f "
                   "structure=put_credit_spread wing_width=%d "
                   "gate_exempt_decision75=#85/#96 (net-credit sale)"
                   % (occ[float(k_short)], k_short, occ[float(k_long)],
                      k_long, expiry, round(credit, 2), prior_close, atr14,
                      WING_WIDTH)))
        return intents


def signal(bars, slice_state, context):
    return SpxPremium().signal(bars, slice_state, context)
