"""Qullamaggie paper test — lean-desk port (Wave D, Decision #119).

EXTRACTED from aurelia_qulla_live.py (the carrier): the reconstruction
engine (aurelia_qulla_engine.py, a pandas point-in-time scan) decides;
this sleeve carries an ACCEPTED long breakout onto the paper close
inside its own budget. Rules ported verbatim: long only (side == 1);
parabolic_short stays closed (no locate); episodic pivots stay closed
without a first-public timestamp (the engine enforces that upstream);
QQQ/TQQQ/GLD are never traded here (Aurelia owns them); dedupe by
client id qulla-{session}-{symbol}-buy; cumulative budget check
(sent orders' notional + new <= $100,000) else blocked_budget.

VIRTUAL BOOK MAPPING: Ledger account "qullamaggie_paper", budget
config BUDGET_USD = 100,000 (aurelia_common.BUDGETS). Book state
arrives as context.extra["sleeve_state"] = {"orders": [prior order
rows]} — the old state file's orders, used for dedupe + spent math.

BUDGET AUTHORITY (QULLA-BUDGET-AUTHORITY-20261116, provenance hunt
2026-11-16, four routes run in order):
(1) Git history: the constant entered this estate at femto-lean
    d5829b9 "Wave D: port the Aurelia family" (2026-10-15, Decision
    #119), extracted from the old desk's aurelia_qulla_live.py, and
    was carried byte-identical into muse-desk-v3 at f2e35ca
    (PORT batch 5, 2026-10-24). No commit note fixes any other value.
(2) Source/author material: femto-lean ports/qullamaggie_paper.md
    records the figure verbatim as the carrier's own config,
    aurelia_common.BUDGETS["qullamaggie_paper"] = $100,000 — the old
    Aurelia virtual book's budget. The Qullamaggie author material
    fixes NO absolute book budget: the superthesis
    (dwj9ddyvf6-hub/quant-research-critical
    quallamaggie_superthesis_v3.md) and qualla_desk/config.json size
    in fractions of equity (risk_per_trade_pct 0.0035, cap 0.005;
    max_position_notional_pct 0.20; max_gross_exposure_pct 1.0), and
    the adopted master-trader playbook (2026-10-28; report section
    1.10 step 5 / section 7.5) likewise: risk 0.25-1% of account,
    position 10-20% of account, max ~30% overnight.
(3) Internet research (2026-11-16): canonical Qullamaggie sizing
    summaries agree with (2) — percentage-of-account sizing only;
    no source publishes a $100,000 (or any absolute) book budget.
(4) Derivation: none needed and none claimed — route (2) fixes the
    figure. AUTHORITY, stated: $100,000 is the ported carrier book's
    budget config, authoritative as that book's cumulative-notional
    gate. It is NOT a Qullamaggie sizing rule, and it is NOT this
    sleeve's v3 slice (config/sleeves.json row: $10,000) — the gate
    caps cumulative sent notional against the virtual book, a
    different quantity from the desk slice allocation. Re-basing
    the gate onto the slice would be a sizing change; no source or
    ruling in the record fixes that, so the figure stands as
    ported, with its authority now on the record.

MISFIT (named): the engine's scan() consumes pandas DataFrames
(daily/intraday/events/universe) — it does not fit the contract's
bars-dict pure signal. The engine stays a core Data/research product
upstream; its accepted proposals arrive as context.extra["proposals"]
(list of dicts {symbol, side, setup, quantity, entry, stop}), exactly
as the old run(proposals=...) path accepted them.

V-07 (parent ruling, 2026-10-18): acceptance REFUSES a proposal
whose stop is missing or unreadable (named "missing_stop" in
accept()). The stop is the position's initial protection (the GTC
protection stop core places on fill from the proposal's stop) and
the R basis for management, so a stop-less position must never
enter.

EXIT CANON (QULLA-EXIT-CANON-20261116, Mon 2026-11-16 total audit):
before this cure the sleeve evaluated NO exits in-signal — a filled
position's only exit route was the core GTC stop, which the morning
audit proved suboptimal against the method as adopted. The exit
structure now evaluated in-signal is the Qullamaggie two-stage exit
AS ADOPTED in the estate's 2026-10-28 master-trader playbook
(research_notes/master-traders-deep-dive-20261029-0229/report.md):
section 1.10, Setup 1, step 6 — "Sell 1/3 to 1/2 after 3-5 days
into strength / at roughly +2-3R, move stop on the rest to
breakeven, then trail with the 10-day (faster names) or 20-day
MA — exit on first close below the trailing MA"; carried onto the
playbook cards in section 7.2 (Setup 2 Breakout Continuation:
"same two-stage exit"; Setup 3 Episodic Pivot: "partial into
strength, trail"). Constants are the reconstruction's own frozen
config (qualla_desk/config.json in dwj9ddyvf6-hub/
quant-research-critical): scale_days 3, scale_fraction 1/3,
trail_default_ma 10, trail_extended_ma 20,
extension_threshold_atr 1.5 — the same form the sibling sleeve
sleeves/qullamaggie.py already runs (its Manage block). Per
position, in order: (a) stop breach — close below the position's
stop exits in full in-signal (the core GTC stop remains as the
broker-side backstop, unchanged); (b) scale — held >= 3 sessions,
profitable, not yet scaled, qty >= 3: exit 1/3, the intent reason
declares the residual stop -> breakeven and scaled_third=1;
(c) trail — held >= 3 sessions and close below the trailing MA
(10MA, or 20MA when extended > 1.5 ATR above the 10MA) exits the
residual in full. Positions arrive as context.extra["positions"]
(adapter-served from the cycle's position view; the params
fixture channel overrides), daily bars via the signal's bars
argument for the symbols held. Entry signal, sizing and the
acceptance chain are unchanged.
"""
from core.sleeve import BaseSleeve, Intent, SleeveConfig

ACCOUNT = "qullamaggie_paper"
BUDGET_USD = 100_000.0  # CONSTANTS-PROVENANCE-20261116: header VIRTUAL BOOK MAPPING (aurelia_common.BUDGETS book budget; cumulative accept check vs $100,000) — authority resolved by QULLA-BUDGET-AUTHORITY-20261116 (the ported carrier book's budget, not a Qullamaggie sizing rule and not the v3 $10,000 slice)
# EXIT CANON constants — qualla_desk/config.json (scale_days,
# scale_fraction, trail_default_ma, trail_extended_ma,
# extension_threshold_atr), as adopted in the 2026-10-28 playbook
# section 1.10 step 6; same values as sleeves/qullamaggie.py.
SCALE_DAYS = 3
SCALE_FRACTION = 1 / 3
TRAIL_HELD_MIN = 3
TRAIL_MA_FAST = 10
TRAIL_MA_SLOW = 20
EXTENSION_ATR = 1.5
AURELIA_SYMBOLS = {"QQQ", "TQQQ", "GLD"}
UNIVERSE = ("NVDA", "AVGO", "META", "AMZN", "AAPL", "MSFT", "GOOGL", "TSLA",
            "AMD", "NFLX", "COST", "LLY", "JPM", "CAT", "GE", "PLTR",
            "CRWD", "AMAT", "MU", "PANW")

CONFIG = SleeveConfig(
    sleeve_id="qullamaggie_paper", cadence_s=300, universe=UNIVERSE,
    state_schema={"orders": "list"}, risk_pct=None)


def client_id(session, symbol):
    return f"qulla-{session}-{symbol}-buy"


def spent_of(orders):
    """Verbatim _dispatch spent math: sent orders' qty * entry."""
    total = 0.0
    for order in orders or []:
        if order.get("status") == "sent" and order.get("quantity"):
            total += float(order["quantity"]) * float(order.get("entry") or 0)
    return total


def stop_below_entry_gate_enabled(ov):
    """ENH-qullamaggie_paper (Edge IMPROVE, Group A): the switch rides
    the proposal stream as proposal["_improve"]["stop_below_entry_gate"]
    (this sleeve's acceptance predicate receives no context); default
    ON; OFF restores the pre-change acceptance exactly (control)."""
    if isinstance(ov, dict) and "stop_below_entry_gate" in ov:
        return bool(ov["stop_below_entry_gate"])
    return True


def accept(proposal, session, existing_ids, spent, budget=BUDGET_USD,
           enhanced=True):
    """The old run()/_queue()/_dispatch() acceptance chain, as a pure
    predicate: returns (ok, reason, new_spent)."""
    symbol = str(proposal.get("symbol") or "")
    try:
        side = int(proposal.get("side") or 0)
    except (TypeError, ValueError):
        return False, "malformed", spent
    setup = str(proposal.get("setup") or "")
    if not symbol:
        return False, "malformed", spent
    if side != 1 or setup == "parabolic_short":
        return False, "not_a_long_breakout", spent
    if symbol in AURELIA_SYMBOLS:
        return False, "aurelia_owns_symbol", spent
    if client_id(session, symbol) in existing_ids:
        return False, "duplicate", spent
    try:
        price = float(proposal.get("entry") or 0)
        qty = int(proposal.get("quantity") or 0)
    except (TypeError, ValueError):
        # A malformed proposal fails closed on its own; it must not
        # raise and kill the tick's remaining valid proposals.
        return False, "malformed", spent
    # V-07 (parent ruling, 2026-10-18): a proposal whose stop is
    # missing or unreadable is REFUSED here, at acceptance. The
    # stop is the position's initial protection (the protection
    # stop core places on fill from the proposal's stop,
    # core/protection.py QUALIFYING) and the R basis for the
    # EXIT CANON management below — a stop-less position would
    # enter with neither, and must never enter. Before this
    # ruling the stop was carried as absent and the position
    # entered anyway. Well-formed proposals are untouched.
    try:
        stop = float(proposal.get("stop"))
    except (TypeError, ValueError):
        return False, "missing_stop", spent
    if stop <= 0:
        return False, "missing_stop", spent
    # ENH (IMPROVE-qullamaggie_paper section 2): a long breakout whose
    # stop is not strictly below its entry is already breached at
    # acceptance - refuse it beside V-07, in the same style.
    # Well-formed proposals (stop < entry) are accepted as before.
    if enhanced and price > 0 and stop >= price:
        return False, "stop_not_below_entry", spent
    if price <= 0 or qty < 1 or qty * price > budget - spent:
        return False, "blocked_budget", spent
    return True, "accepted", spent + qty * price


def _bar_dates(bars):
    """Session dates for bar dicts — the sibling sleeve's convention
    (sleeves/qullamaggie.py _dates: epoch t, +4h, UTC date). A bar
    whose t is already an ISO string keeps its own date prefix."""
    from datetime import datetime, timezone
    out = []
    for b in bars or []:
        t = b.get("t")
        if isinstance(t, str):
            out.append(t[:10])
            continue
        try:
            out.append(datetime.fromtimestamp(
                float(t) + 4 * 3600, tz=timezone.utc).date().isoformat())
        except (TypeError, ValueError, OverflowError, OSError):
            continue
    return out


def _sessions_held(bars, entry_date):
    """Sessions strictly after the entry date — the sibling sleeve's
    cured date-count form (its ENH sessions_held_datecount): an entry
    date aged out of the delivered window still counts, so the
    scale/trail exits never silently disarm."""
    if not entry_date:
        return 0
    entry = str(entry_date)[:10]
    return sum(1 for d in _bar_dates(bars) if d > entry)


def _atr20(bars):
    """20-session mean true range — verbatim from the sibling sleeve
    (0.0 when < 21 bars)."""
    if len(bars) < 21:
        return 0.0
    trs = []
    for i in range(1, len(bars)):
        h, l = float(bars[i]["h"]), float(bars[i]["l"])
        pc = float(bars[i - 1]["c"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-20:]) / 20


def _trail_target(bars):
    """(trail_ma, label): 20MA when extended > 1.5 ATR above 10MA,
    else 10MA — verbatim from the sibling sleeve; periods are the
    EXIT CANON constants (qualla_desk trail_default_ma /
    trail_extended_ma)."""
    if len(bars) < TRAIL_MA_SLOW:
        return None, "none"
    close = [float(b["c"]) for b in bars]
    ma_fast = sum(close[-TRAIL_MA_FAST:]) / TRAIL_MA_FAST
    ma_slow = sum(close[-TRAIL_MA_SLOW:]) / TRAIL_MA_SLOW
    atr = _atr20(bars)
    if atr > 0 and close[-1] - ma_fast > EXTENSION_ATR * atr:
        return ma_slow, "20MA-ext"
    return ma_fast, "10MA"


def manage_positions(bars, positions, orders):
    """EXIT CANON management (playbook section 1.10 step 6, section
    7.2 cards 2-3): stop breach, then the 1/3 scale into strength
    with the residual stop declared to breakeven, then the MA trail
    on the residual. Positions are the served position dicts
    {symbol, qty, avg_price|entry_px, stop_px|stop,
    opened_at|entry_date, scaled_third?}; a position whose current
    qty is below its sent entry order's quantity (sleeve_state
    orders) has already scaled. Exits are never gated by entries."""
    intents = []
    sent_qty = {}
    for o in orders or []:
        if o.get("status") == "sent" and o.get("symbol"):
            try:
                sent_qty[o["symbol"]] = float(o.get("quantity") or 0)
            except (TypeError, ValueError):
                continue
    for p in positions or []:
        if not isinstance(p, dict):
            continue
        sym = p.get("symbol")
        bl = (bars or {}).get(sym) or []
        if not sym or len(bl) < TRAIL_MA_SLOW:
            continue
        try:
            qty = int(float(p.get("qty") or 0))
            entry = float(p.get("entry_px") or p.get("avg_price") or 0)
        except (TypeError, ValueError):
            continue
        if qty <= 0 or entry <= 0:
            continue
        try:
            curr = float(bl[-1]["c"])
        except (TypeError, ValueError, KeyError):
            continue
        held = _sessions_held(bl, p.get("entry_date")
                              or p.get("opened_at"))
        try:
            stop_level = float(p.get("stop") or p.get("stop_px") or entry)
        except (TypeError, ValueError):
            stop_level = entry
        if curr < stop_level:
            intents.append(Intent(
                "exit", sym, qty_hint=qty, price_hint=round(curr, 2),
                reason="qullamaggie_paper stop breach: close %.2f < "
                       "stop %.2f" % (curr, stop_level)))
            continue
        scaled = bool(p.get("scaled_third")) or (
            sent_qty.get(sym, 0) > qty > 0)
        if not scaled and held >= SCALE_DAYS and curr > entry \
                and qty >= 3:
            sell = max(1, int(qty * SCALE_FRACTION))
            intents.append(Intent(
                "exit", sym, qty_hint=sell, price_hint=round(curr, 2),
                reason="qullamaggie_paper scale 1/3: held %dd "
                       "profitable; residual stop -> breakeven %.2f "
                       "scaled_third=1" % (held, entry)))
            continue
        ma, lbl = _trail_target(bl)
        if ma is not None and held >= TRAIL_HELD_MIN and curr < ma:
            intents.append(Intent(
                "exit", sym, qty_hint=qty, price_hint=round(curr, 2),
                reason="qullamaggie_paper trail breach (%s): close "
                       "%.2f < %.2f" % (lbl, curr, ma)))
    return intents


class QullamaggiePaper(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        orders = state.get("orders") or []
        # EXIT CANON: exits are evaluated first and never gated by
        # the proposal stream.
        intents = manage_positions(
            bars, extra.get("positions") or [], orders)
        proposals = extra.get("proposals")
        if not proposals:
            return intents
        existing = {o.get("client_id") for o in orders}
        spent = spent_of(orders)
        for proposal in proposals:
            ok, _why, spent = accept(
                proposal, context.session, existing, spent,
                enhanced=stop_below_entry_gate_enabled(
                    (proposal or {}).get("_improve")
                    if isinstance(proposal, dict) else None))
            if not ok:
                continue
            existing.add(client_id(context.session, str(proposal["symbol"])))
            try:
                stop = round(float(proposal["stop"]), 2) \
                    if proposal.get("stop") else None
            except (TypeError, ValueError):
                # Unreachable for accepted proposals since V-07
                # (accept refuses a missing/unreadable stop); kept
                # as a belt so a surprise here never raises.
                stop = None
            intents.append(Intent(
                "enter", str(proposal["symbol"]),
                qty_hint=int(proposal["quantity"]),
                price_hint=round(float(proposal["entry"]), 2),
                stop=stop,
                reason="qullamaggie_paper breakout setup=%s paper close "
                       "(account=%s budget=%d)" % (
                           proposal.get("setup"), ACCOUNT, BUDGET_USD)))
        return intents


def signal(bars, slice_state, context):
    return QullamaggiePaper().signal(bars, slice_state, context)
