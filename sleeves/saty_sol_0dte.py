"""saty_sol_0dte — the 0DTE variant of ChatGPT's (Sol's)
Saty/Milkman autonomous engine design v1.0, implemented as a
desk sleeve (2026-10-22).

the owner's ruling (2026-10-22 02:32 ET, chosen from presented
options): "Build a 0DTE variant sleeve, keep Sol's original
intact." This sleeve is that variant. Sol's original
(sleeves/saty_sol.py, profile SPY_RESEARCH_BOOK_V1, 2-4
calendar DTE, ZERO_DTE disabled in his config) is NOT modified
by this build and remains the untouched head-to-head reference;
this sibling inherits his system with exactly ONE deviation,
and the deviation is the point of the sleeve:

THE ONE DEVIATION — ZERO_DTE ENABLED. The active product
profile is SPY_ZERO_DTE_BOOK_V1, named in this header, on every
evaluation stamp, in every intent reason, and on the reader
card: SPY signal, SPY options expiring the SAME session day
(0 calendar DTE). The selection law is Sol's, unchanged in
shape: nearest eligible expiry — here today's expiry only —
then nearest strike to the signal coordinate (spot), tie-break
relative spread then contract id. A session with NO same-day
SPY expiry listed is no trade (his unavailable = skip): a later
expiry is NEVER substituted, even when it is the only chain
available. That refusal is the variant's core law.

EVERYTHING ELSE IS SOL'S, inherited without alteration (the
governing texts and the full mapping register are
ports/saty_sol.md; the variant's register is
ports/saty_sol_0dte.md). Two policies trade: GG_TOUCH_RAW_V1
(both directions) and TRIGGER_3M_CALL_V1 (bullish only). From
the frozen prior-day close C0 and ATR A0 the coordinate is
x = d*(S-C0)/A0; a GG direction arms only when the session
opens with x < .382, and the FIRST crossing of .382 consumes
the episode for the session — even outside the entry window,
rejected, unaffordable or unfilled — and a start already
beyond .382 is not a crossing (no gap entries). Entry requires
the mark inside the kernel band [.382, .382+.03 ATR], the .618
target not already achieved, a resolved contract and a valid
quote. The completed-1h Phase Oscillator tag is RECORDED on
every GG event (aligned d*PO >= 61.8, opposing <= -61.8) and
never gates. Management exits ALL filled quantity at the first
mark x >= .618 after fill, or on a 10-minute close with
x < .236 (strict: equality does not breach) whose bar end is
strictly after the first fill. No partials, no runners. The
trigger policy's open-inside-the-band arm, 3-minute confirming
close, entry band and exits are his, as built in saty_sol.

Windows and arbitration are his config's: new entries
09:35-14:30 ET and at least 90 minutes before the actual
session close; mandatory liquidation begins 10 minutes before
the cash close — on a same-day-expiry book that window is also
the expiry backstop: the position is managed out, never left
to expiry settlement while a managed exit is still possible.
At most ONE filled or risk-reserved position across both
policies and both directions; exits evaluate before entries,
then GG, then the trigger policy (his champion is null; the
policy-ID tie-break orders GG_TOUCH_RAW_V1 first). Re-arming is
disabled. A submitted-but-unfilled entry counts as
risk-reserved exposure (his UNKNOWN rule) until a fill appears
or the session ends; timeout manufactures no blind retry. The
state machine is PREPARE / ARMED / ENTRY_PENDING / OPEN /
EXIT_PENDING / DONE with a separate persistent HALTED flag;
losing entry permission never disables exits.

Risk is his section 10 with his paper numbers:
q = max(0, min(q_premium, q_stop, q_liquidity, q_desk,
q_broker)); premium sizing floors and CAN BE ZERO
(force_minimum_contract is false: a $500 budget against a $680
contract is q 0, no trade). Full premium budget 0.5% of the
sleeve's virtual equity per session (the remaining-budget
pool); daily loss limit 1% of virtual equity — on breach, new
entries cancel, HALTED persists for the session (a restart
must not clear it), exits continue. No stop model is
configured, so q_stop does not bind; the desk's quotes door
carries no displayed size, so q_liquidity does not bind on
this door.

STATE ISOLATION. The variant is its own sleeve: its own ledger
identity (sleeve_id saty_sol_0dte), its own session fills door,
and its own durable journal under the stamp/extra key
sol0_journal (saty_sol's is sol_journal). Neither sleeve's
fills, episodes or HALT latch can reach the other's — proven
both directions by the variant's blockers. As in saty_sol,
every evaluation stamps the full session journal onto
self.last_evaluation, the dispatcher ledgers it on the tick
row, and the producer serves it back next pass
(extra["sol0_journal"], tools/run_live.py). Crossings are
recomputed from today's bars each pass; the journal carries
only what bars cannot prove — decisions and latches.
Indicator math comes only from the landed port (core/saty_bars,
core/saty_indicators); the Volume Stack is never consulted
(his section 3).

The D-B1 cure pattern of the 2026-10-22 desk audit holds here
as it does in saty_sol at this build's base: position
management is evaluated even on data/warmup-blocked passes —
the time-based exits (session liquidation, overnight flat) go
out unpriced on the desk's market/EOD door when the ladder is
unavailable.

Disabled experiments of Sol's config stay disabled here too:
BILBO_FILTER, RIBBON_FILTER, NQ_CONFIRM, RANGE_REJECT,
TREND_RUNNER, TRIGGER_3M_PUT. The ONLY flag that differs from
saty_sol is ZERO_DTE: enabled here, at the owner's order, and named
here, in ports/saty_sol_0dte.md, in the buglog entry
(SATY-SOL-0DTE-20261022) and on the reader card.
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

ET = ZoneInfo("America/New_York")
SYM = "SPY"

CONFIG = SleeveConfig(
    sleeve_id="saty_sol_0dte",
    cadence_s=60,
    universe=("SPY",),
    state_schema={"position": "dict|None"},
    risk_pct=0.005,
)

# -- his numbers (report sections 6, 7, 9, 10; engine_config) ----
F_TRIGGER = 0.236
F_GATE = 0.382
F_TARGET = 0.618
MAX_ADVERSE_ATR = 0.03         # no-chase band above the crossing
PO_EXTREME = 61.8              # tag thresholds (recorded, never gates)
SPREAD_GATE = 0.05             # spread <= 5% of mid (his section 9)
DTE_MIN, DTE_MAX = 0, 0        # calendar days: SAME-DAY ONLY
                               # (the owner's ordered deviation;
                               # saty_sol keeps his 2-4)
PREMIUM_FRACTION = 0.005       # full-premium budget (paper value)
DAILY_LOSS_FRACTION = 0.01     # daily loss limit (paper value)
FEES_PER_CONTRACT = 0.0        # the paper account's commission input
MULTIPLIER = 100
ENTRY_START = dtime(9, 35)     # his entry window opens 09:35
ENTRY_END = dtime(14, 30)      # ... and closes 14:30
MIN_MINUTES_TO_CLOSE = 90      # ... and >= 90 min before the close
LIQ_MINUTES_BEFORE_CLOSE = 10  # mandatory liquidation lead
QUOTE_STALE_S = 60.0           # desk mapping of his freshness budgets
                               # onto the scan-cadence quotes door
ENTRY_FRESH_S = 120.0          # an event is actionable only at the
                               # first evaluation that observes it
                               # (two cadence cycles of slack); older
                               # first sightings are missed-while-
                               # offline consumption (his example B)

PROFILE_ACTIVE = "SPY_ZERO_DTE_BOOK_V1"
PROFILE_PREFERRED = "SPXW_CASH_V1"   # inactive: no SPX cash feed,
                                     # no OPRA entitlement (header)

POLICY_GG = "GG_TOUCH_RAW_V1"
POLICY_TRIGGER = "TRIGGER_3M_CALL_V1"
# his config's disabled experiments — none of them trade or gate:
DISABLED_EXPERIMENTS = ("BILBO_FILTER", "RIBBON_FILTER", "NQ_CONFIRM",
                        "RANGE_REJECT", "TREND_RUNNER",
                        "TRIGGER_3M_PUT")
# ZERO_DTE is NOT in the register above: it is ENABLED in this
# variant, at the owner's order (2026-10-22 02:32 ET) — the sleeve's
# one deviation from Sol's config. In saty_sol it stays disabled.

# NYSE early closes (13:00 ET) — the desk's calendar mapping (his
# section 4: deadlines derive from actual closes; the desk has no
# early-close calendar door, so the named table is carried here,
# the saty_day D-16 precedent). Fully closed days are the
# calendar's business (core.data.is_trading_day).
EARLY_CLOSES = _SHARED_EARLY_CLOSES  # core/early_close.py (D-B3 cure: one shared table)

_OCC_RE = re.compile(r"^([A-Z.\\-]{1,6})(\d{6})([CP])(\d{8})$")


def parse_occ(occ):
    m = _OCC_RE.match(str(occ or ""))
    if not m:
        return None
    return {"underlying": m.group(1), "kind": m.group(3),
            "strike": int(m.group(4)) / 1000.0}


def session_close_dt(session_iso):
    """The session's actual close: 16:00 ET or the named early
    close. Every clock mark of the day derives from it."""
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


def _lvl(anchor, unit, frac, sign):
    return anchor + sign * frac * unit


def _x(mark, anchor, unit, direction):
    """His ladder coordinate: x = d*(S - C0)/A0."""
    return direction * (mark - anchor) / unit


def _ladder(daily_completed, today):
    """The frozen ladder from the port's ATR Levels (the desk's
    RTH-aggregated daily profile — his config names the daily
    profile UNVALIDATED; the profile identity is stamped, never
    hidden): anchor = previous completed daily close, unit = its
    ATR(14). The placeholder bar appended to the daily series IS
    today; its own OHLC never enters the read."""
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
                            session_basis="regular")
    except Exception:
        return None
    row = res["rows"][0]
    if row.get("anchor") is None or row.get("unit") is None \
            or not row.get("unit") > 0:
        return None
    return row


def _fresh_quote(fresh, now_epoch):
    """(mid, bid, ask) from a fresh-quotes-door row ({bp, ap, t,
    received_at}) when two-sided, inside his spread gate, and no
    older than the door's staleness bound; else None."""
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


def _snap_quote(quotes, occ):
    """(mid, bid, ask) from the snapshot door's quotes map
    ({occ: {bid, ask}}) — the exit pricing door."""
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


def premium_quantity(budget, limit_price, fees=FEES_PER_CONTRACT):
    """His section 10 premium sizing, kernel-exact: floor of
    budget / (multiplier * price + fees). CAN BE ZERO — there is
    no forced one-contract floor."""
    if budget <= 0 or limit_price <= 0:
        return 0
    return int(math.floor(budget / (MULTIPLIER * limit_price + fees)))


class SatySol0Dte(BaseSleeve):
    CONFIG = CONFIG

    # ------------------------------------------------------------
    # frames (port plumbing only; no indicator math here)
    # ------------------------------------------------------------
    def _frames(self, extra, session_d, now_dt):
        m5_long = extra.get("bars_5m_long") or {}
        m1 = extra.get("bars_1m") or {}
        if not m5_long.get(SYM):
            return None
        spy5 = sb.with_end(_shape(m5_long.get(SYM)), 5)
        spy1 = sb.with_end(_shape(m1.get(SYM)), 1)
        spy5_rth = sb.filter_session(spy5, "regular")
        daily_rth = [b for b in sb.aggregate_daily(spy5_rth)
                     if b["t"].date() < session_d]
        m1_today = [b for b in spy1 if b["t"].date() == session_d]
        m1_rth = sb.filter_session(m1_today, "regular")
        return {
            "daily_rth": daily_rth,
            "h1": _completed(sb.aggregate(spy5_rth, 60,
                                          anchor="09:30"), now_dt),
            "m10": _completed(sb.aggregate(spy5_rth, 10,
                                           anchor="09:30"), now_dt),
            "m1_rth": m1_rth,
            "m3_today": _completed(sb.aggregate(m1_rth, 3,
                                                anchor="09:30"),
                                   now_dt),
        }

    def _marks(self, frames, extra, now_dt):
        """The eligible underlying mark stream (his section 6
        detector input): the session open mark, every completed
        1-minute close, and the fresh IEX latest-quote mid as the
        live leg. Marks are (datetime, price), time-ordered."""
        marks = []
        m1 = frames["m1_rth"]
        if m1:
            marks.append((m1[0]["t"], m1[0]["open"]))
            for b in m1:
                ct = sb.close_time(b)
                if ct <= now_dt:
                    marks.append((ct, b["close"]))
        q = (extra.get("latest_quote") or {}).get(SYM)
        if isinstance(q, dict) and q.get("t") and q.get("bp") \
                and q.get("ap"):
            try:
                t_epoch = datetime.fromisoformat(
                    str(q["t"]).replace("Z", "+00:00")).timestamp()
                bp, ap = float(q["bp"]), float(q["ap"])
            except (TypeError, ValueError):
                bp = ap = None
            if bp and ap and bp > 0 and ap >= bp:
                now_epoch = now_dt.timestamp()
                if now_epoch - t_epoch <= QUOTE_STALE_S and marks \
                        and marks[-1][0] < now_dt:
                    # the live leg only EXTENDS an existing session
                    # stream; it can never create the open mark
                    marks.append((now_dt, (bp + ap) / 2.0))
        return marks

    # ------------------------------------------------------------
    # journal (durable session state via the filing door)
    # ------------------------------------------------------------
    @staticmethod
    def _journal(extra):
        j = extra.get("sol0_journal")
        if not isinstance(j, dict):
            j = {}
        j.setdefault("equity_basis", None)
        j.setdefault("halted", False)
        j.setdefault("halt_pnl", None)
        j.setdefault("episodes", {})
        j.setdefault("last_now", None)
        return j

    @staticmethod
    def _episode(journal, key):
        ep = journal["episodes"].get(key)
        if not isinstance(ep, dict):
            ep = {"state": "open"}
            journal["episodes"][key] = ep
        return ep

    # ------------------------------------------------------------
    # session P&L (his section 10 daily-loss accounting)
    # ------------------------------------------------------------
    def _session_pnl(self, extra, pos):
        """Realized cash over today's fill rows for this sleeve
        (sells add, buys subtract, options at x100 — broker truth
        from the desk ledger) plus the open position marked at
        the current BID. None when the fills door is absent or an
        open position has no bid: unverifiable is stamped, never
        guessed."""
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
                cash += q * p * MULTIPLIER
            elif f.get("position_intent") == "buy_to_open":
                cash -= q * p * MULTIPLIER
        if isinstance(pos, dict) and float(pos.get("qty") or 0) != 0:
            snap = _snap_quote(extra.get("quotes") or {},
                               pos.get("occ"))
            if snap is None:
                return None
            cash += abs(float(pos["qty"])) * snap[1] * MULTIPLIER
        return cash

    def _filled_premium(self, extra):
        """Premium actually spent on today's entry fills (the
        spent part of his remaining-budget pool)."""
        fills = extra.get("session_fills")
        if fills is None:
            return None
        spent = 0.0
        for f in fills:
            if f.get("position_intent") != "buy_to_open":
                continue
            try:
                spent += abs(float(f.get("qty") or 0)) \
                    * float(f.get("price") or 0) * MULTIPLIER
            except (TypeError, ValueError):
                continue
        return spent

    # ------------------------------------------------------------
    # contract resolution (his section 9 selection law)
    # ------------------------------------------------------------
    def _pick_contract(self, extra, direction, session_d, spot,
                       now_epoch):
        """(occ, ask, expiry_iso) or (None, reason). Selection is
        deterministic and happens BEFORE quote validation: nearest
        eligible expiry inside the SAME-DAY window (0 calendar DTE —
        this variant's one deviation), then
        nearest strike to spot, tie-break relative spread then
        contract id. The single selected contract is then
        validated (two-sided, spread gate, fresh); an invalid
        quote is no trade, never a walk down the chain."""
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
            if DTE_MIN <= dte <= DTE_MAX:
                cands.append((exp, float(c["strike"]), c["symbol"]))
        if not cands:
            return None, "no_valid_contract"
        expiry = min(e for e, _, _ in cands)

        def sort_key(row):
            _e, strike, occ = row
            q = _fresh_quote(fresh.get(occ), now_epoch)
            rel = ((q[2] - q[1]) / q[0]) if q else math.inf
            return (abs(strike - spot), rel, occ)

        same_day = sorted((r for r in cands if r[0] == expiry),
                          key=sort_key)
        _e, _s, occ = same_day[0]
        q = _fresh_quote(fresh.get(occ), now_epoch)
        if q is None:
            return None, "no_valid_contract"
        return (occ, q[2], expiry.isoformat()), None

    # ------------------------------------------------------------
    # entry decisions
    # ------------------------------------------------------------
    def _po_tag(self, frames, direction, moment_dt):
        """The completed-1h Phase Oscillator tag for a GG event
        (recorded attribution; never gates). Uses only hour bars
        completed at or before the event moment."""
        h1 = frames["h1"]
        if not h1:
            return "UNKNOWN"
        rows = si.phase_oscillator(h1)["rows"]
        idx = None
        for i, b in enumerate(h1):
            if sb.close_time(b) <= moment_dt:
                idx = i
            else:
                break
        if idx is None:
            return "UNKNOWN"
        row = rows[idx]
        if not row.get("warmed_up") \
                or row.get("phase_oscillator") is None:
            return "UNKNOWN"
        v = direction * row["phase_oscillator"]
        if v >= PO_EXTREME:
            return "ALIGNED_EXTREME"
        if v <= -PO_EXTREME:
            return "OPPOSING_EXTREME"
        return "MID"

    def _enter_intent(self, policy, key, direction, occ, ask, spot,
                      plan, ctx, qty, ep):
        anchor, unit = plan["anchor"], plan["unit"]
        parsed = parse_occ(occ)
        tgt = _lvl(anchor, unit,
                   F_TARGET if policy == POLICY_GG else F_GATE,
                   direction)
        kill = _lvl(anchor, unit, F_TRIGGER, direction)
        reason = (
            f"saty_sol_0dte {policy} {'long' if direction > 0 else 'short'}: "
            f"occ={occ} strike={parsed['strike']:.2f} "
            f"expiry={ep['expiry']} ask={ask:.2f} spot={spot:.2f} "
            f"profile={PROFILE_ACTIVE} episode={key} "
            f"po_tag={ep.get('po_tag') or 'NA'} "
            f"kill_level={kill:.2f} target_level={tgt:.2f} "
            f"debit_cap={ask:.2f}")
        return Intent(
            "enter", SYM, qty=qty, price_hint=spot,
            limit_price=round(ask, 2), side="buy",
            position_intent="buy_to_open", reason=reason,
            signal_date=ctx.session)

    def _entry_decision(self, policy, key, direction, event_t,
                        frames, plan, journal, extra,
                        ctx, now_dt, marks, stamp):
        """The shared tail of both entry policies once their event
        has fired: window, arbitration reservation, contract,
        sizing. Every outcome consumes the episode (his section 6:
        outside-window, rejected, unaffordable, unfilled — the
        episode is spent). Returns an Intent or None."""
        ep = self._episode(journal, key)
        ep["state"] = "consumed"
        ep["event_t"] = event_t.isoformat()
        ep["policy"] = policy
        ep["profile"] = PROFILE_ACTIVE
        session_d = date.fromisoformat(ctx.session)
        close_dt = session_close_dt(ctx.session)
        win_end = min(datetime.combine(session_d, ENTRY_END,
                                       tzinfo=ET),
                      close_dt - timedelta(
                          minutes=MIN_MINUTES_TO_CLOSE))
        win_start = datetime.combine(session_d, ENTRY_START,
                                     tzinfo=ET)
        if not (win_start <= now_dt < win_end):
            ep["outcome"] = "outside_window"
            stamp["stood_down"] = "outside_window"
            return None
        # arbitration: a risk-reserved entry (emitted, unresolved)
        # or a filled sibling episode owns the family slot.
        for other_key, other in journal["episodes"].items():
            if other_key != key and other.get("state") in (
                    "intent", "filled"):
                ep["outcome"] = "family_busy"
                stamp["stood_down"] = "family_busy"
                return None
        spot = marks[-1][1] if marks else None
        if spot is None:
            ep["outcome"] = "no_valid_contract"
            return None
        picked, why = self._pick_contract(extra, direction,
                                          date.fromisoformat(
                                              ctx.session),
                                          spot, ctx.now)
        if picked is None:
            ep["outcome"] = why
            stamp["stood_down"] = why
            return None
        occ, ask, expiry = picked
        ep["expiry"] = expiry
        # his sizing: the REMAINING full-premium budget (session
        # pool minus filled premium minus the reserved premium of
        # an outstanding entry — none can exist here by the
        # arbitration check above, but the term is kept explicit).
        basis = journal.get("equity_basis") or float(ctx.equity or 0.0)
        spent = self._filled_premium(extra)
        if spent is None:
            ep["outcome"] = "unaffordable"
            stamp["stood_down"] = "pnl_unverifiable"
            return None
        budget = PREMIUM_FRACTION * basis - spent
        qty = premium_quantity(budget, ask)
        if qty <= 0:
            ep["outcome"] = "unaffordable"
            stamp["stood_down"] = "unaffordable"
            return None
        ep["state"] = "intent"
        ep["occ"] = occ
        ep["qty"] = qty
        ep["limit"] = round(ask, 2)
        stamp["decision"] = f"enter_{key}"
        return self._enter_intent(policy, key, direction, occ, ask,
                                  spot, plan, ctx, qty, ep)

    def _gg_entries(self, frames, plan, journal, extra, ctx,
                    now_dt, marks, stamp):
        anchor, unit = plan["anchor"], plan["unit"]
        if not marks:
            return None
        open_mark = marks[0][1]
        for direction in (1, -1):
            key = f"gg:{direction:+d}"
            ep = self._episode(journal, key)
            if ep.get("state") != "open":
                continue
            if _x(open_mark, anchor, unit, direction) >= F_GATE:
                ep["state"] = "consumed"
                ep["outcome"] = "not_armed_open_beyond"
                continue
            # first directed crossing over the mark stream
            cross = None
            prev_x = None
            for t, p in marks:
                x = _x(p, anchor, unit, direction)
                if prev_x is not None and prev_x < F_GATE <= x:
                    cross = (t, p)
                    break
                prev_x = x
            if cross is None:
                continue
            cross_t, _cross_p = cross
            ep["po_tag"] = self._po_tag(frames, direction, cross_t)
            age = (now_dt - cross_t).total_seconds()
            if age > ENTRY_FRESH_S:
                ep["state"] = "consumed"
                ep["outcome"] = "missed_while_offline"
                stamp.setdefault("stood_down", "missed_while_offline")
                continue
            # target already occurred between crossing and decision
            if any(_x(p, anchor, unit, direction) >= F_TARGET
                   for t, p in marks if t >= cross_t):
                ep["state"] = "consumed"
                ep["outcome"] = "target_already_occurred"
                stamp["stood_down"] = "target_already_occurred"
                continue
            # no-chase: the current mark must sit in the kernel band
            cur_x = _x(marks[-1][1], anchor, unit, direction)
            if not (F_GATE - 1e-12 <= cur_x
                    <= F_GATE + MAX_ADVERSE_ATR + 1e-12):
                ep["state"] = "consumed"
                ep["outcome"] = "no_chase"
                stamp["stood_down"] = "no_chase"
                continue
            return self._entry_decision(
                POLICY_GG, key, direction, cross_t, frames,
                plan, journal, extra, ctx, now_dt, marks, stamp)
        return None

    def _trigger_entries(self, frames, plan, journal, extra, ctx,
                         now_dt, marks, stamp):
        anchor, unit = plan["anchor"], plan["unit"]
        key = "trigger:+1"
        ep = self._episode(journal, key)
        if ep.get("state") != "open" or not marks:
            return None
        open_mark = marks[0][1]
        if abs(_x(open_mark, anchor, unit, 1)) >= F_TRIGGER:
            ep["state"] = "consumed"
            ep["outcome"] = "not_armed_open_outside_band"
            return None
        trig = _lvl(anchor, unit, F_TRIGGER, 1)
        bars = frames["m3_today"]
        signal_bar = None
        for i, b in enumerate(bars):
            prev = open_mark if i == 0 else bars[i - 1]["close"]
            if prev <= trig and b["close"] > trig:
                signal_bar = b
                break
        if signal_bar is None:
            return None
        sig_t = sb.close_time(signal_bar)
        age = (now_dt - sig_t).total_seconds()
        if age > ENTRY_FRESH_S:
            ep["state"] = "consumed"
            ep["outcome"] = "missed_while_offline"
            stamp.setdefault("stood_down", "missed_while_offline")
            return None
        cur = marks[-1][1]
        confirm = signal_bar["close"]
        gate_lvl = _lvl(anchor, unit, F_GATE, 1)
        if not (cur > trig and cur < gate_lvl
                and cur <= confirm + MAX_ADVERSE_ATR * unit):
            ep["state"] = "consumed"
            ep["outcome"] = "no_chase"
            stamp["stood_down"] = "no_chase"
            return None
        return self._entry_decision(
            POLICY_TRIGGER, key, 1, sig_t, frames, plan,
            journal, extra, ctx, now_dt, marks, stamp)

    # ------------------------------------------------------------
    # position management (his sections 6/7 exits; all quantity)
    # ------------------------------------------------------------
    def _exit_intent(self, pos, qty, occ, bid, spot, ctx, rule,
                     market=False):
        kw = {}
        if not market and bid is not None:
            kw["limit_price"] = round(bid, 2)
        return Intent(
            "exit", SYM, qty=int(qty), price_hint=spot, side="sell",
            position_intent="sell_to_close",
            reason=(f"saty_sol_0dte exit: {rule} occ={occ} "
                    f"qty={int(qty)} profile={PROFILE_ACTIVE}"),
            signal_date=ctx.session, **kw)

    def _manage(self, frames, plan, pos, journal, extra, ctx,
                now_dt, marks, stamp):
        anchor, unit = plan["anchor"], plan["unit"]
        close_dt = session_close_dt(ctx.session)
        occ = pos.get("occ")
        parsed = parse_occ(occ)
        qty = int(float(pos.get("qty") or 0))
        if parsed is None or qty <= 0:
            return []
        direction = 1 if parsed["kind"] == "C" else -1
        fill_t = float(pos.get("fill_t") or pos.get("entry_t") or 0)
        fill_dt = datetime.fromtimestamp(fill_t, tz=ET) \
            if fill_t else now_dt
        spot = marks[-1][1] if marks else None
        stamp["position"] = {"occ": occ, "qty": qty,
                             "direction": direction}
        snap = _snap_quote(extra.get("quotes") or {}, occ)
        liq_start = close_dt - timedelta(
            minutes=LIQ_MINUTES_BEFORE_CLOSE)

        # attribute the position to its episode (journal); an
        # unmatched contract is an ownership exception — managed
        # on the GG baseline for its direction, never adopted
        # silently (his section 12).
        owner = None
        for k, ep in journal["episodes"].items():
            if ep.get("occ") == occ and ep.get("state") in (
                    "intent", "filled"):
                owner = (k, ep)
                break
        if owner is not None:
            owner[1]["state"] = "filled"
            policy = owner[1].get("policy") or POLICY_GG
        else:
            policy = POLICY_GG
            stamp["ownership_mismatch"] = True
        stamp["setup"] = policy

        def priced(q, rule):
            """Exit at the fresh bid (persistent intent). With no
            quote the decision stays pending outside the
            liquidation window — filed, never dropped — and goes
            out unpriced inside it on the desk's EOD door."""
            if snap is not None:
                return self._exit_intent(pos, q, occ, snap[1], spot,
                                         ctx, rule)
            if now_dt >= liq_start:
                return self._exit_intent(pos, q, occ, None, spot,
                                         ctx, rule, market=True)
            stamp["exit_pending_no_quote"] = rule
            return None

        # overnight survivor: outside every rule the design
        # trades — liquidate at the first evaluation; entries are
        # blocked by the caller's arbitration while it exists.
        if str(pos.get("signal_date") or "") != ctx.session:
            stamp["decision"] = "overnight_flat"
            it = priced(qty, "overnight_flat")
            return [it] if it else []

        # mandatory liquidation (his window rule)
        if now_dt >= liq_start:
            stamp["decision"] = "session_liquidation"
            it = priced(qty, "session_liquidation")
            return [it] if it else []

        # first exit event wins; a tie goes to invalidation (his
        # section 6: never award the favorable path).
        target_t = None
        stop_t = None
        if policy == POLICY_TRIGGER:
            tgt_lvl = _lvl(anchor, unit, F_GATE, 1)
            for t, p in marks:
                if t >= fill_dt and p >= tgt_lvl:
                    target_t = t
                    break
            trig = _lvl(anchor, unit, F_TRIGGER, 1)
            for b in frames["m3_today"]:
                if sb.close_time(b) > fill_dt and b["close"] < trig:
                    stop_t = sb.close_time(b)
                    break
        else:
            for t, p in marks:
                if t >= fill_dt and _x(p, anchor, unit,
                                       direction) >= F_TARGET:
                    target_t = t
                    break
            for b in frames["m10"]:
                if sb.close_time(b) > fill_dt and \
                        _x(b["close"], anchor, unit,
                           direction) < F_TRIGGER:
                    stop_t = sb.close_time(b)
                    break
        rule = None
        if target_t is not None and (stop_t is None
                                     or target_t < stop_t):
            rule = "target"
        elif stop_t is not None:
            rule = "invalidation"
        if rule is None:
            return []
        stamp["decision"] = rule
        it = priced(qty, f"{policy}_{rule}")
        return [it] if it else []

    # ------------------------------------------------------------
    # the evaluation
    # ------------------------------------------------------------
    def _blocked_exit(self, extra, ctx, now_dt, stamp):
        """D-B1 cure (2026-10-22): a held position gets its
        time-based exits even when the data/warmup gates block
        the ladder — the mandatory session liquidation
        (close - LIQ_MINUTES_BEFORE_CLOSE, the _manage window)
        and the overnight flat need no bars, no ladder and no
        quote: they go out unpriced on the desk's market/EOD
        door. Outside those windows the blocked pass still
        returns [] (level exits genuinely need the ladder)."""
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
        liq_start = close_dt - timedelta(
            minutes=LIQ_MINUTES_BEFORE_CLOSE)
        if overnight:
            rule = "overnight_flat_blocked_data"
        elif now_dt >= liq_start:
            rule = "session_liquidation_blocked_data"
        else:
            return []
        stamp["state"] = "blocked_data"
        stamp["decision"] = rule
        stamp["position"] = {"occ": occ, "qty": qty}
        return [self._exit_intent(pos, qty, occ, None, None, ctx,
                                  rule, market=True)]

    def signal(self, bars, slice_state, ctx):
        stamp = {"sleeve": "saty_sol_0dte", "session": ctx.session,
                 "profile": PROFILE_ACTIVE,
                 "profile_preferred": PROFILE_PREFERRED}
        self.last_evaluation = stamp
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        session_d = date.fromisoformat(ctx.session)
        journal = self._journal(ctx.extra or {})
        stamp["sol0_journal"] = journal
        journal["last_now"] = float(ctx.now)
        if not is_trading_day(session_d):
            stamp["state"] = "not_a_trading_day"
            return []
        extra = ctx.extra or {}
        if journal.get("equity_basis") is None \
                and float(ctx.equity or 0) > 0:
            journal["equity_basis"] = float(ctx.equity)
        frames = self._frames(extra, session_d, now_dt)
        if frames is None:
            stamp["state"] = "blocked_data"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        plan = _ladder(frames["daily_rth"], session_d)
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYM) or {}).get("position")
        has_pos = isinstance(pos, dict) \
            and float(pos.get("qty") or 0) != 0

        # daily-loss accounting runs every pass (entries or not):
        # the breach latches HALTED in the durable journal and a
        # restart cannot clear it. Exits are never disabled.
        pnl = self._session_pnl(extra, pos if has_pos else None)
        stamp["session_pnl"] = (round(pnl, 2) if pnl is not None
                                else "unavailable")
        basis = journal.get("equity_basis") or float(ctx.equity or 0.0)
        if pnl is not None and basis > 0 \
                and pnl <= -DAILY_LOSS_FRACTION * basis:
            if not journal.get("halted"):
                journal["halted"] = True
                journal["halt_pnl"] = round(pnl, 2)
            stamp["daily_loss_halt"] = True
        if journal.get("halted"):
            stamp["halted"] = True

        if plan is None:
            if has_pos:
                # D-B1 cure: the session liquidation / overnight
                # flat speak without a ladder (unpriced EOD door);
                # outside those windows the position is stamped
                # unmanaged, never silently held through them.
                out = self._blocked_exit(extra, ctx, now_dt, stamp)
                if out:
                    return out
                stamp["position_unmanaged_no_ladder"] = True
            stamp["state"] = "blocked_data"
            return []
        stamp["plan"] = {"anchor": round(plan["anchor"], 2),
                         "unit": round(plan["unit"], 2),
                         "basis": "regular",
                         "daily_profile": "desk_rth_aggregate_unvalidated"}
        if not plan.get("warmed_up"):
            stamp["state"] = "blocked_warmup"
            return self._blocked_exit(extra, ctx, now_dt, stamp)
        stamp["state"] = "armed"
        marks = self._marks(frames, extra, now_dt)
        if marks:
            stamp["spot"] = round(marks[-1][1], 2)

        # journal reconciliation: an episode whose position has
        # fully exited retires to DONE, freeing the family slot
        # for a later episode (the reservation it held is over).
        if not has_pos:
            for ep in journal["episodes"].values():
                if ep.get("state") == "filled":
                    ep["state"] = "done"

        # position first (broker truth): exits before entries,
        # always — including while HALTED.
        if has_pos:
            stamp["family_busy"] = True
            return self._manage(frames, plan, pos, journal, extra,
                                ctx, now_dt, marks, stamp)

        # a risk-reserved entry (emitted, no fill yet) owns the
        # family slot: no second submission can ever be manufactured
        # (his UNKNOWN rule). The episode's own crossing logic is
        # not re-run.
        for ep in journal["episodes"].values():
            if ep.get("state") == "intent":
                stamp["family_busy"] = True
                stamp["stood_down"] = "entry_pending"
                return []

        if journal.get("halted"):
            stamp["stood_down"] = "daily_loss_halt"
            return []
        close_dt = session_close_dt(ctx.session)
        if now_dt >= close_dt - timedelta(
                minutes=MIN_MINUTES_TO_CLOSE):
            stamp["stood_down"] = "entry_window_closed"
            return []
        if now_dt < datetime.combine(session_d, dtime(9, 30),
                                     tzinfo=ET):
            stamp["state"] = "armed_preopen"
            return []

        # Episodes evaluate from the open: a crossing before the
        # 09:35 window is observed and consumed as outside-window
        # by the decision tail, exactly his section 6/7 semantics —
        # it is not left for a later pass to misread as fresh.
        # Arbitration order: GG (champion-null tie-break by policy
        # id) before the trigger policy.
        intent = self._gg_entries(frames, plan, journal, extra, ctx,
                                  now_dt, marks, stamp)
        if intent is None:
            intent = self._trigger_entries(frames, plan, journal,
                                           extra, ctx, now_dt,
                                           marks, stamp)
        return [intent] if intent is not None else []


def signal(bars, slice_state, context):
    return SatySol0Dte().signal(bars, slice_state, context)
