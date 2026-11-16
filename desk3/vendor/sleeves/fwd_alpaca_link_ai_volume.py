"""FWD Alpaca LINK AI-volume — lean-desk port (Wave D, Decision #119).

EXTRACTED from aurelia_alpaca_forward.py decide() + BOOKS spec
FWD_ALPACA_LINK_AI_VOLUME_V1 (preserves PUBLIC_AI_VOLUME_SPOT100): the
USD forward of the AI-volume spot recipe on completed native 4Hour
bars — volume above twice the volume EMA, close above the price EMA
and above the open; exit flat on the fifth completed bar of the
position, counting the entry bar. No stop in the source recipe. Long only,
no pyramid. Decision window: an ENTRY order is allowed only within 300s
after the last completed bar's close; a late bar is NOT replayed. The
5th-bar timed exit is not an entry decision: a due exit fires on any
pass (still quote-gated), because it is the position's only exit
(AUDIT-20261018-CURE16; the same exit-first cure was
applied to the ADA book as LG-3, audit #3 2026-10-19, and the two
decide() bodies were unified verbatim by MAC-6, desk review
2026-10-19 — the blocker diffs them).
Quote gates verbatim: fresh within 10s at the exchange stamp, not
future, not crossed, spread <= 100 bps. Size: up to 10% of the
$100,000 budget.

FENCE PRESERVED (named misfit): the recipe engine that computes
long_signal / long_close_signal lived only in the excluded Ausar
archive; on the old desk _features() raised and EVERY decision was
BLOCKED with that reason. The lean port keeps the fence honestly:
features arrive as context.extra["features"] from a core Data
product; absent features, decide() reports BLOCKED and no intent is
emitted — identical observable behavior to the old desk.

VIRTUAL BOOK MAPPING: Ledger account "fwd_alpaca" family — this
sleeve's account is "fwd_alpaca_link_ai_volume_v1", BUDGET_USD = 100,000,
per-book max exposure 10%. Fractional LINK qty rides in the reason
(whole-unit qty_hint contract; donchian_crypto precedent). Held qty
via context.extra["held_qty"]; entry bar close via
context.extra["entry_close_at"].

ENH (IMPROVE-fwd_alpaca_link_ai_volume, Edge program 2026-10-24):
one added exit — when a completed bar after entry closes below the
same price EMA the entry required (the served features' price_ema,
the recipe engine's EMA of closes), exit on the next pass under the
same quote gates as the existing timed exit. The fifth-bar timed
exit remains the outer bound. Switched by
context.extra["fwd_alpaca_link_ai_volume_enhance"]["enabled"],
default ON; OFF restores the pre-change rule exactly (exit at the
fifth bar only). The pre-change rule is the shadow control,
recorded paired on every decide() row as "enh_pair"; it never emits
intents. Absent served features the exit cannot be evaluated and
behaviour degrades to the pre-change (clock-exit) rule.
"""
from datetime import datetime, timedelta, timezone
from decimal import ROUND_DOWN, Decimal

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ACCOUNT = "fwd_alpaca_link_ai_volume_v1"
BUDGET_USD = 100_000
MAX_EXPOSURE = Decimal("0.10")
MAX_SPREAD_BPS = Decimal("100")
DECISION_SECONDS = 300

SPEC = {
    "id": "FWD_ALPACA_LINK_AI_VOLUME_V1",
    "preserves": "PUBLIC_AI_VOLUME_SPOT100",
    "strategy": "ai_volume",
    "symbol": "LINK/USD",
    "timeframe": "4Hour",
    "step_seconds": 14400,
    "warmup": 60,
    "listed": True,
}

CONFIG = SleeveConfig(
    sleeve_id="fwd_alpaca_link_ai_volume", cadence_s=14400, universe=("LINK/USD",),
    state_schema={"position": "dict|None"}, risk_pct=None)

FENCE_REASON = ("public recipe source is in the excluded Ausar archive; "
                "alpaca_forward features are fenced in Femto (Decision #119)")


def enhance_enabled(extra):
    """ENH fwd_alpaca_link_ai_volume switch:
    ctx.extra['fwd_alpaca_link_ai_volume_enhance']['enabled'], default
    ON; OFF restores the pre-change rule exactly."""
    ov = (extra or {}).get("fwd_alpaca_link_ai_volume_enhance")
    if isinstance(ov, dict) and "enabled" in ov:
        return bool(ov["enabled"])
    if isinstance(ov, bool):
        return ov
    return True


def parse_utc(value):
    text = str(value).replace("Z", "+00:00")
    if "." in text:
        head, rest = text.split(".", 1)
        digits = []
        index = 0
        while index < len(rest) and rest[index].isdigit():
            digits.append(rest[index]); index += 1
        frac = "".join(digits)[:6]
        text = f"{head}.{frac}{rest[index:]}" if frac else f"{head}{rest[index:]}"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("UTC timestamp required")
    return parsed.astimezone(timezone.utc)


def completed_bars(raw, step_seconds, now):
    """Verbatim: drop a bar that has not closed. Bar t is the open."""
    rows = []
    for bar in raw or []:
        opened = datetime.fromtimestamp(float(bar["t"]), tz=timezone.utc)
        closed = opened + timedelta(seconds=step_seconds)
        if closed > now:
            continue
        rows.append({"open_at": opened.isoformat(), "close_at": closed.isoformat(),
                     "open": float(bar["o"]), "high": float(bar["h"]),
                     "low": float(bar["l"]), "close": float(bar["c"]),
                     "volume": float(bar["v"])})
    return rows


def quantity_for(price):
    notional = Decimal(BUDGET_USD) * MAX_EXPOSURE
    return (notional / price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)


def decide(now, raw_bars, quote, held, entry_close, features, enhance=True):
    """Verbatim port of aurelia_alpaca_forward.decide() for this spec.
    features=None reproduces the old desk's fenced BLOCKED outcome.
    enhance=False restores the pre-ENH rule exactly (fifth-bar exit
    only)."""
    row = {"id": SPEC["id"], "preserves": SPEC["preserves"],
           "symbol": SPEC["symbol"], "orders_disabled": False}
    if raw_bars is None:
        return {**row, "status": "BLOCKED", "reason": "Bars were not fetched.",
                "order": None, "orders_disabled": True}
    bars = completed_bars(raw_bars, SPEC["step_seconds"], now)

    def _ema_due(feats, last_bar):
        """ENH: a completed bar closed below the served price EMA
        (features['price_ema']) while held."""
        if not enhance or held <= 0 or not feats or last_bar is None:
            return False
        ema = feats.get("price_ema")
        if ema is None:
            return False
        try:
            return float(last_bar["close"]) < float(ema)
        except (TypeError, ValueError):
            return False
    # READINESS-20261022 F-A7/F-A8: a due exit is evaluated BEFORE
    # the entry warmup gate — the warmup guards entries only. The
    # exit-due computation below is the same one the post-warmup
    # path uses (CURE16/MAC-6 shared body, kept in one place here).
    _exit_due_pre = False
    if SPEC["strategy"] == "ai_volume" and held > 0 and entry_close:
        try:
            _entry_at = parse_utc(entry_close)
            _after = [b for b in bars
                      if parse_utc(b["close_at"]) >= _entry_at]
            _exit_due_pre = len(_after) >= 5
        except (ValueError, TypeError):
            _exit_due_pre = False
    _close_due_pre = (bool(features.get("long_close_signal"))
                      and held > 0 if features is not None else False)
    _ema_due_pre = _ema_due(features, bars[-1] if bars else None)
    if len(bars) < SPEC["warmup"] and not (_exit_due_pre or _close_due_pre
                                           or _ema_due_pre):
        return {**row, "status": "BLOCKED",
                "reason": f"{len(bars)} completed bars; {SPEC['warmup']} required.",
                "order": None, "orders_disabled": True}
    if not bars:
        return {**row, "status": "BLOCKED",
                "reason": "0 completed bars; no exit can be evaluated.",
                "order": None, "orders_disabled": True}
    last = bars[-1]
    closed = parse_utc(last["close_at"])
    age = (now - closed).total_seconds()
    # Exit FIRST (AUDIT-20261018-CURE16, applied to both books by
    # LG-3, audit #3 2026-10-19; unified verbatim by MAC-6, desk
    # review 2026-10-19): a due exit is this position's ONLY exit
    # (no stop in either source recipe) and is a pure function of
    # bars/features/held — it is not an entry decision. Evaluating
    # it after the 300s entry window held the exit hostage to pass
    # timing; a due exit must fire on any pass, still subject to
    # the quote gates below. The two exits are SPEC-gated below:
    # the ai_volume book's timed 5th-bar exit and the rsi2 book's
    # long_close_signal exit — one shared body, never two copies
    # that can drift apart again (the MAC-6 blocker diffs them).
    exit_due = False
    if SPEC["strategy"] == "ai_volume" and held > 0 and entry_close:
        # Count bars by instant, not string order (P3 audit 2026-10-15:
        # a 'Z'-formatted entry_close_at sorted after every '+00:00'
        # bar stamp, silently delaying the 5-bar exit to the 6th bar).
        # An unparseable anchor fails closed: no timed exit.
        try:
            entry_at = parse_utc(entry_close)
            after = [b for b in bars if parse_utc(b["close_at"]) >= entry_at]
            exit_due = len(after) >= 5
        except (ValueError, TypeError):
            exit_due = False
    close_due = (bool(features.get("long_close_signal")) and held > 0
                 if features is not None else False)
    ema_due = _ema_due(features, last)
    # ENH paired record: control = pre-change rule (exit at the
    # fifth bar only); treatment = control + the EMA-failure exit.
    enh_pair = {"control": "hold_to_fifth_bar",
                "treatment": "exit_ema_break" if ema_due else "hold",
                "switch_on": bool(enhance),
                "price_ema": (features or {}).get("price_ema"),
                "last_close": last["close"]}
    outside_window = age < 0 or age > DECISION_SECONDS
    if outside_window and not exit_due and not close_due and not ema_due:
        return {**row, "status": "ACTIVE/OUTSIDE WINDOW",
                "reason": f"The last completed {SPEC['timeframe']} bar closed at "
                          f"{last['close_at']}. Orders are allowed for "
                          f"{DECISION_SECONDS} seconds after that close.",
                "order": None}
    if features is None:
        if not exit_due and not close_due and not ema_due:
            return {**row, "status": "BLOCKED", "reason": FENCE_REASON,
                    "order": None, "orders_disabled": True}
        features = {}  # a due exit needs no more recipe features
    enter = bool(features.get("long_signal")) and held <= 0
    if not enter and not exit_due and not close_due and not ema_due:
        return {**row, "status": "ACTIVE/AWAITING SIGNAL", "order": None,
                "enh_pair": enh_pair,
                "reason": "The book is open and the latest completed bar is "
                          "not an entry or an exit."}
    if quote is None:
        return {**row, "status": "QUOTE", "needs_quote": True, "order": None,
                "reason": "Exit is due." if (exit_due or close_due or ema_due) and outside_window
                          else "Decision window is open."}
    if quote.get("bid") is None or quote.get("ask") is None or not quote.get("exchange_at"):
        return {**row, "status": "BLOCKED", "order": None, "orders_disabled": True,
                "reason": "Quote is missing inside the decision window."}
    try:
        quoted = parse_utc(quote["exchange_at"])
    except ValueError as exc:
        return {**row, "status": "BLOCKED", "reason": str(exc),
                "order": None, "orders_disabled": True}
    bid, ask = Decimal(str(quote["bid"])), Decimal(str(quote["ask"]))
    if bid <= 0 or ask < bid or (now - quoted).total_seconds() > 10 or quoted > now:
        return {**row, "status": "BLOCKED", "order": None, "orders_disabled": True,
                "reason": "Quote is stale, future, or crossed."}
    if ask and (ask - bid) / ask * Decimal(10000) > MAX_SPREAD_BPS:
        return {**row, "status": "BLOCKED", "order": None, "orders_disabled": True,
                "reason": "Quote is wider than 100 bps."}
    side = "sell" if held > 0 else "buy"
    price = bid if side == "sell" else ask
    qty = Decimal(str(held)) if side == "sell" else quantity_for(price)
    # The cap is an ENTRY notional cap: it gates buys only. On the sell
    # side qty is the held quantity, sized to the cap at entry — applying
    # the cap there trapped the exit after any price appreciation
    # (LG-2, audit #3 2026-10-19).
    if qty <= 0 or (side == "buy" and qty * price > Decimal(BUDGET_USD) * MAX_EXPOSURE + Decimal("0.01")):
        return {**row, "status": "BLOCKED", "order": None, "orders_disabled": True,
                "reason": "Order size is outside the sleeve cap."}
    return {**row, "status": "PAPER-ACTIVE", "enh_pair": enh_pair,
            "reason": "Exit is due with a fresh quote; exits are not "
                      "bound by the entry decision window."
                      if (exit_due or close_due or ema_due) and outside_window else
                      "Signal is inside the decision window with a fresh quote.",
            "order": {"side": side, "quantity": float(qty),
                      "limit_price": float(price), "bar_close_at": last["close_at"]}}


class FwdLinkAiVolume(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        now = datetime.fromtimestamp(float(context.now), tz=timezone.utc)
        held = float(extra.get("held_qty") or 0)
        row = decide(now, bars.get(SPEC["symbol"]), extra.get("quote"), held,
                     extra.get("entry_close_at"), extra.get("features"),
                     enhance=enhance_enabled(extra))
        self.last_evaluation = {"sleeve": "fwd_alpaca_link_ai_volume",
                                "enh_pair": row.get("enh_pair")}
        order = row.get("order")
        if row.get("status") != "PAPER-ACTIVE" or not order:
            return []
        kind = "exit" if order["side"] == "sell" else "enter"
        enh_note = (" enh_exit=ema_break"
                    if kind == "exit" and (row.get("enh_pair") or {}).get(
                        "treatment") == "exit_ema_break" else "")
        return [Intent(
            kind, SPEC["symbol"], qty=float(order["quantity"]),
            limit_price=float(order["limit_price"]),
            price_hint=round(float(order["limit_price"]), 6),
            reason="fwd_alpaca_link_ai_volume %s qty=%s bar_close=%s strategy=%s%s "
                   "(account=%s max_exposure=%s)"
                   % (order["side"], order["quantity"], order["bar_close_at"],
                      SPEC["strategy"], enh_note, ACCOUNT, MAX_EXPOSURE))]


def signal(bars, slice_state, context):
    return FwdLinkAiVolume().signal(bars, slice_state, context)
