"""BB-touch RSI-divergence sleeve for the Femto-lean trading desk.

This module is deliberately parked. It consumes completed 1-hour RTH
bars and only emits a long entry after the exact pivot-confirmation
bar is new, fresh, quoteable, and risk-sized. A bearish divergence
closes an existing long; this version does not open short positions.

Integration requirements are recorded in integration/Femto-lean_Wiring.md.
"""
from datetime import datetime, time as dtime, timezone
from zoneinfo import ZoneInfo
import math

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

# Broad, liquid default universe. Add/remove supported US-listed equities
# or ETFs here; no ticker-specific price scale or indicator constants exist.
UNIVERSE = (
    "SPY", "QQQ", "IWM", "DIA",
    "GLD", "SLV",
    "TLT", "IEF",
    "USO", "UUP",
    "XLF", "XLK",
)

BB_LENGTH = 20
BB_MULTIPLIER = 2.0
RSI_LENGTH = 14
ATR_LENGTH = 14

PIVOT_LEFT = 3
PIVOT_RIGHT = 3
RSI_ALIGN_RADIUS = 1
MIN_PIVOT_GAP = 5
MAX_PIVOT_GAP = 60
MIN_RSI_DIVERGENCE = 2.0
MIN_PRICE_EXTENSION_PCT = 0.0
REQUIRE_CLOSE_BACK_INSIDE = False

STOP_ATR_BUFFER = 0.5
MIN_REWARD_RISK = 1.2
MAX_HOLD_BARS = 24
RISK_PCT = 0.0025
MAX_NOTIONAL_PCT = 0.05
MAX_SPREAD_BPS = 15.0
QUOTE_MAX_AGE_S = 60.0
BAR_MAX_AGE_S = 10.0 * 60.0
ENTRY_CLOSE_START = dtime(10, 0)
ENTRY_CLOSE_END = dtime(15, 0)
BAR_SECONDS = 3600.0

CONFIG = SleeveConfig(
    sleeve_id="bb_rsi_divergence",
    cadence_s=300,
    universe=UNIVERSE,
    state_schema={"meta.last_evaluated_bar_by_symbol": "dict"},
    risk_pct=RISK_PCT,
    parked=False,
)


def _number(value):
    if isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _epoch(value):
    """Parse epoch seconds/milliseconds or an ISO timestamp."""
    n = _number(value)
    if n is not None:
        return n / 1000.0 if n > 1.0e12 else n
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def _rth_bars(raw):
    """Keep valid, complete one-hour intervals inside the ET cash session."""
    parsed = []
    for row in raw or []:
        if not isinstance(row, dict):
            continue
        t = _epoch(row.get("t"))
        o = _number(row.get("o"))
        h = _number(row.get("h"))
        l = _number(row.get("l"))
        c = _number(row.get("c"))
        if None in (t, o, h, l, c) or min(o, h, l, c) <= 0 or h < l:
            continue
        start = datetime.fromtimestamp(t, tz=ET)
        end = datetime.fromtimestamp(t + BAR_SECONDS, tz=ET)
        if start.date() != end.date():
            continue
        if start.time() < dtime(9, 30) or end.time() > dtime(16, 0):
            continue
        parsed.append({"t": t, "o": o, "h": h, "l": l, "c": c})

    parsed.sort(key=lambda b: b["t"])
    deduped = []
    for bar in parsed:
        if deduped and bar["t"] == deduped[-1]["t"]:
            deduped[-1] = bar
        else:
            deduped.append(bar)
    return deduped


def _has_intraday_gap(bars):
    """Reject a same-session missing hourly interval in the recent frame."""
    for previous, current in zip(bars[-25:-1], bars[-24:]):
        pdt = datetime.fromtimestamp(previous["t"], tz=ET)
        cdt = datetime.fromtimestamp(current["t"], tz=ET)
        if pdt.date() == cdt.date() and current["t"] - previous["t"] > BAR_SECONDS + 1:
            return True
    return False


def _bollinger(closes):
    n = len(closes)
    basis = [None] * n
    lower = [None] * n
    upper = [None] * n
    for i in range(BB_LENGTH - 1, n):
        window = closes[i - BB_LENGTH + 1:i + 1]
        mean = sum(window) / BB_LENGTH
        variance = sum((x - mean) ** 2 for x in window) / BB_LENGTH
        deviation = math.sqrt(variance)
        basis[i] = mean
        lower[i] = mean - BB_MULTIPLIER * deviation
        upper[i] = mean + BB_MULTIPLIER * deviation
    return basis, lower, upper


def _wilder_rsi(closes):
    n = len(closes)
    out = [None] * n
    if n <= RSI_LENGTH:
        return out

    avg_gain = 0.0
    avg_loss = 0.0
    for i in range(1, n):
        change = closes[i] - closes[i - 1]
        gain = max(change, 0.0)
        loss = max(-change, 0.0)

        if i == RSI_LENGTH:
            gains = []
            losses = []
            for j in range(1, RSI_LENGTH + 1):
                delta = closes[j] - closes[j - 1]
                gains.append(max(delta, 0.0))
                losses.append(max(-delta, 0.0))
            avg_gain = sum(gains) / RSI_LENGTH
            avg_loss = sum(losses) / RSI_LENGTH
        elif i > RSI_LENGTH:
            avg_gain = ((avg_gain * (RSI_LENGTH - 1)) + gain) / RSI_LENGTH
            avg_loss = ((avg_loss * (RSI_LENGTH - 1)) + loss) / RSI_LENGTH
        else:
            continue

        if avg_loss == 0.0:
            out[i] = 100.0 if avg_gain > 0.0 else 50.0
        else:
            rs = avg_gain / avg_loss
            out[i] = 100.0 - (100.0 / (1.0 + rs))
    return out


def _wilder_atr(bars):
    n = len(bars)
    out = [None] * n
    if n <= ATR_LENGTH:
        return out

    tr_values = [None] * n
    for i in range(1, n):
        tr_values[i] = max(
            bars[i]["h"] - bars[i]["l"],
            abs(bars[i]["h"] - bars[i - 1]["c"]),
            abs(bars[i]["l"] - bars[i - 1]["c"]),
        )

    average = None
    for i in range(1, n):
        if i == ATR_LENGTH:
            average = sum(tr_values[1:ATR_LENGTH + 1]) / ATR_LENGTH
        elif i > ATR_LENGTH:
            average = (
                average * (ATR_LENGTH - 1) + tr_values[i]
            ) / ATR_LENGTH
        if i >= ATR_LENGTH:
            out[i] = average
    return out


def _pivot_value(values, pivot_index, left, right, is_low):
    start = pivot_index - left
    end = pivot_index + right + 1
    if start < 0 or end > len(values):
        return None
    window = values[start:end]
    center = values[pivot_index]
    if is_low and center == min(window):
        return center
    if not is_low and center == max(window):
        return center
    return None


def _aligned_rsi(rsi, pivot_index, is_low):
    start = max(0, pivot_index - RSI_ALIGN_RADIUS)
    end = min(len(rsi), pivot_index + RSI_ALIGN_RADIUS + 1)
    values = [v for v in rsi[start:end] if v is not None]
    if not values:
        return None
    return min(values) if is_low else max(values)


def _median(values):
    ordered = sorted(v for v in values if v is not None and math.isfinite(v))
    if not ordered:
        return None
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _adaptive_context(bars, closes, lower, upper, atr, index, direction):
    """Causal local regime and volatility sizing features at confirmation."""
    current_atr = atr[index]
    close = closes[index]
    if current_atr in (None, 0.0) or close <= 0:
        return {
            "regime": "unknown",
            "efficiency_ratio": 0.0,
            "band_walk_count": 0,
            "atr_pct": 0.0,
            "atr_ratio": 1.0,
            "vol_scale": 0.5,
            "trend_scale": 1.0,
            "risk_scale": 0.5,
        }

    atr_pcts = [
        atr[j] / closes[j]
        for j in range(max(0, index - 59), index + 1)
        if atr[j] is not None and closes[j] > 0
    ]
    atr_pct = current_atr / close
    reference = _median(atr_pcts)
    atr_ratio = atr_pct / reference if reference not in (None, 0.0) else 1.0

    # Volatility can only reduce the fixed base risk. This caps the effect
    # of regime estimation and prevents quiet periods from increasing size.
    vol_scale = max(0.5, min(1.0, 1.0 / math.sqrt(max(1.0, atr_ratio))))

    trend_window = 12
    start = max(0, index - trend_window)
    path = sum(
        abs(closes[j] - closes[j - 1])
        for j in range(start + 1, index + 1)
    )
    net = closes[index] - closes[start]
    efficiency = net / path if path > 0 else 0.0

    band_window = range(max(0, index - 3), index + 1)
    if direction > 0:
        band_walk = sum(
            1 for j in band_window
            if lower[j] is not None and closes[j] <= lower[j]
        )
        against_trend = efficiency <= -0.55 and band_walk >= 2
        regime = (
            "downtrend_band_walk" if against_trend
            else "mixed_or_range"
        )
    else:
        band_walk = sum(
            1 for j in band_window
            if upper[j] is not None and closes[j] >= upper[j]
        )
        against_trend = efficiency >= 0.55 and band_walk >= 2
        regime = (
            "uptrend_band_walk" if against_trend
            else "mixed_or_range"
        )

    trend_scale = 0.5 if against_trend else 1.0
    risk_scale = max(0.25, vol_scale * trend_scale)
    return {
        "regime": regime,
        "efficiency_ratio": efficiency,
        "band_walk_count": band_walk,
        "atr_pct": atr_pct,
        "atr_ratio": atr_ratio,
        "vol_scale": vol_scale,
        "trend_scale": trend_scale,
        "risk_scale": risk_scale,
    }


def _latest_confirmed_signals(bars):
    """Rebuild pivot state and return signals known on the latest bar."""
    closes = [b["c"] for b in bars]
    lows = [b["l"] for b in bars]
    highs = [b["h"] for b in bars]
    basis, lower, upper = _bollinger(closes)
    rsi = _wilder_rsi(closes)
    atr = _wilder_atr(bars)

    previous_low = None
    previous_high = None
    latest = []

    for confirmed_index in range(PIVOT_LEFT + PIVOT_RIGHT, len(bars)):
        pivot_index = confirmed_index - PIVOT_RIGHT

        low_value = _pivot_value(
            lows, pivot_index, PIVOT_LEFT, PIVOT_RIGHT, True
        )
        if (
            low_value is not None
            and lower[pivot_index] is not None
        ):
            pivot_rsi = _aligned_rsi(rsi, pivot_index, True)
            if pivot_rsi is not None:
                gap = (
                    pivot_index - previous_low["index"]
                    if previous_low is not None else 0
                )
                comparable = (
                    previous_low is not None
                    and MIN_PIVOT_GAP <= gap <= MAX_PIVOT_GAP
                )
                touched = low_value <= lower[pivot_index]
                close_inside = (
                    not REQUIRE_CLOSE_BACK_INSIDE
                    or bars[pivot_index]["c"] > lower[pivot_index]
                )
                price_extension = (
                    previous_low is not None
                    and low_value
                    < previous_low["price"]
                    * (1.0 - MIN_PRICE_EXTENSION_PCT / 100.0)
                )
                rsi_extension = (
                    previous_low is not None
                    and pivot_rsi
                    > previous_low["rsi"] + MIN_RSI_DIVERGENCE
                )
                valid = comparable and touched and close_inside
                if (
                    confirmed_index == len(bars) - 1
                    and valid and price_extension and rsi_extension
                ):
                    context = _adaptive_context(
                        bars, closes, lower, upper, atr,
                        confirmed_index, direction=1
                    )
                    latest.append({
                        "direction": 1,
                        "pivot_index": pivot_index,
                        "pivot_price": low_value,
                        "pivot_rsi": pivot_rsi,
                        "previous_rsi": previous_low["rsi"],
                        "rsi_delta": pivot_rsi - previous_low["rsi"],
                        "basis": basis[confirmed_index],
                        "atr": atr[confirmed_index],
                        "touch_depth_atr": (
                            max(0.0, lower[pivot_index] - low_value)
                            / atr[confirmed_index]
                            if atr[confirmed_index] not in (None, 0.0)
                            else 0.0
                        ),
                        **context,
                    })

                if previous_low is None or gap >= MIN_PIVOT_GAP:
                    previous_low = {
                        "index": pivot_index,
                        "price": low_value,
                        "rsi": pivot_rsi,
                    }

        high_value = _pivot_value(
            highs, pivot_index, PIVOT_LEFT, PIVOT_RIGHT, False
        )
        if high_value is not None and upper[pivot_index] is not None:
            pivot_rsi = _aligned_rsi(rsi, pivot_index, False)
            if pivot_rsi is not None:
                gap = (
                    pivot_index - previous_high["index"]
                    if previous_high is not None else 0
                )
                comparable = (
                    previous_high is not None
                    and MIN_PIVOT_GAP <= gap <= MAX_PIVOT_GAP
                )
                touched = high_value >= upper[pivot_index]
                close_inside = (
                    not REQUIRE_CLOSE_BACK_INSIDE
                    or bars[pivot_index]["c"] < upper[pivot_index]
                )
                price_extension = (
                    previous_high is not None
                    and high_value
                    > previous_high["price"]
                    * (1.0 + MIN_PRICE_EXTENSION_PCT / 100.0)
                )
                rsi_extension = (
                    previous_high is not None
                    and pivot_rsi
                    < previous_high["rsi"] - MIN_RSI_DIVERGENCE
                )
                valid = comparable and touched and close_inside
                if (
                    confirmed_index == len(bars) - 1
                    and valid and price_extension and rsi_extension
                ):
                    context = _adaptive_context(
                        bars, closes, lower, upper, atr,
                        confirmed_index, direction=-1
                    )
                    latest.append({
                        "direction": -1,
                        "pivot_index": pivot_index,
                        "pivot_price": high_value,
                        "pivot_rsi": pivot_rsi,
                        "previous_rsi": previous_high["rsi"],
                        "rsi_delta": previous_high["rsi"] - pivot_rsi,
                        "basis": basis[confirmed_index],
                        "atr": atr[confirmed_index],
                        "touch_depth_atr": (
                            max(0.0, high_value - upper[pivot_index])
                            / atr[confirmed_index]
                            if atr[confirmed_index] not in (None, 0.0)
                            else 0.0
                        ),
                        **context,
                    })

                if previous_high is None or gap >= MIN_PIVOT_GAP:
                    previous_high = {
                        "index": pivot_index,
                        "price": high_value,
                        "rsi": pivot_rsi,
                    }

    return latest

def _fresh_quote(quotes, symbol, now):
    quote = (quotes or {}).get(symbol)
    if not isinstance(quote, dict):
        return None
    bid = _number(quote.get("bp", quote.get("bid")))
    ask = _number(quote.get("ap", quote.get("ask")))
    quote_t = _epoch(quote.get("t", quote.get("timestamp")))
    if bid is None or ask is None or quote_t is None:
        return None
    if bid <= 0 or ask < bid:
        return None
    age = float(now) - quote_t
    if age < -1.0 or age > QUOTE_MAX_AGE_S:
        return None
    mid = (bid + ask) / 2.0
    spread_bps = ((ask - bid) / mid) * 10000.0 if mid > 0 else math.inf
    return {
        "bid": bid,
        "ask": ask,
        "t": quote_t,
        "age_s": age,
        "spread_bps": spread_bps,
    }


def _limit_cents(price):
    """Round a buy limit upward to a cent so it remains marketable."""
    return math.ceil((price * 100.0) - 1e-9) / 100.0


def _open_positions(slice_state, extra):
    out = {}
    for symbol, raw_qty in (slice_state or {}).items():
        qty = _number(raw_qty)
        if qty is not None and abs(qty) > 0:
            out[symbol] = qty
    if out:
        return out

    state = (extra or {}).get("sleeve_state") or {}
    for symbol, entry in state.items():
        pos = entry.get("position") if isinstance(entry, dict) else None
        if isinstance(pos, dict):
            qty = _number(pos.get("qty"))
            if qty is not None and abs(qty) > 0:
                out[symbol] = qty
    return out


def _entry_activity_today(fills, orders):
    """Return filled, working, False, or None when lifecycle feeds are absent."""
    if fills is None or orders is None:
        return None
    for fill in fills:
        if not isinstance(fill, dict):
            continue
        if fill.get("position_intent") in ("buy_to_open", "sell_to_open"):
            return "filled"

    active_statuses = {
        "accepted", "pending_new", "new", "partially_filled",
        "pending_cancel", "pending_replace", "held",
    }
    completed_fill_statuses = {"filled"}
    for order in orders:
        if not isinstance(order, dict):
            continue
        if order.get("position_intent") not in ("buy_to_open", "sell_to_open"):
            continue
        status = str(order.get("status", "")).lower().replace("-", "_").replace(" ", "_")
        filled_qty = _number(order.get("filled_qty", order.get("filled_qty_total")))
        if (filled_qty is not None and filled_qty > 0) or status in completed_fill_statuses:
            return "filled"
        if status in active_statuses:
            return "working_order"
    return False

_WORKING_EXIT_STATUSES = {
    "accepted", "pending_new", "new", "partially_filled",
    "pending_cancel", "pending_replace", "held",
}
_PROTECTIVE_ORDER_TYPES = {"stop", "stop_limit", "trailing_stop"}


def _working_exit_order(order, symbol=None):
    """Identify an active strategy close, excluding broker disaster stops."""
    if not isinstance(order, dict):
        return False
    if order.get("position_intent") != "sell_to_close":
        return False
    if str(order.get("type", "")).lower() in _PROTECTIVE_ORDER_TYPES:
        return False
    if symbol is not None and str(
            order.get("symbol") or order.get("submit_symbol") or ""
    ).upper() != symbol:
        return False
    status = str(order.get("status", "")).lower().replace("-", "_").replace(" ", "_")
    return status in _WORKING_EXIT_STATUSES


class BbRsiDivergenceSleeve(BaseSleeve):
    CONFIG = CONFIG

    def _frame(self, symbol, raw_bars, ctx, previous_bar_t):
        bars = _rth_bars(raw_bars)
        minimum = (
            BB_LENGTH + RSI_LENGTH + MAX_PIVOT_GAP
            + PIVOT_LEFT + PIVOT_RIGHT
        )
        if len(bars) < minimum:
            return None, "blocked_warmup"
        if _has_intraday_gap(bars):
            return None, "blocked_intraday_gap"

        latest = bars[-1]
        latest_close_t = latest["t"] + BAR_SECONDS
        age = float(ctx.now) - latest_close_t
        if age < -1.0 or age > BAR_MAX_AGE_S:
            return None, "blocked_stale_bar"
        same_bar_consumed = (
            previous_bar_t is not None and latest["t"] <= previous_bar_t
        )
        close_dt = datetime.fromtimestamp(latest_close_t, tz=ET)
        setups = _latest_confirmed_signals(bars)
        return {
            "bars": bars,
            "latest": latest,
            "latest_close_t": latest_close_t,
            "close_dt": close_dt,
            "setups": setups,
            "same_bar_consumed": same_bar_consumed,
        }, ("same_bar_consumed" if same_bar_consumed else "armed")

    def signal(self, bars, slice_state, ctx):
        extra = ctx.extra or {}
        self.last_evaluation = {
            "sleeve": CONFIG.sleeve_id,
            "policy_version": "2.2.0",
            "session": ctx.session,
            "state": "scanning",
            "universe_size": 0,
            "symbol_states": {},
            "signals": [],
            "candidate_rejections": {},
        }

        configured = extra.get("active_universe")
        if isinstance(configured, (list, tuple, set)):
            requested_universe = tuple(dict.fromkeys(
                str(symbol).strip().upper()
                for symbol in configured
                if isinstance(symbol, str) and symbol.strip()
            ))
        else:
            requested_universe = CONFIG.universe
        open_positions = _open_positions(slice_state, extra)
        universe = tuple(dict.fromkeys(
            tuple(requested_universe) + tuple(open_positions.keys())
        ))
        self.last_evaluation["universe_size"] = len(universe)

        meta = extra.get("meta") or {}
        last_seen = meta.get("last_evaluated_bar_by_symbol") or {}
        if not isinstance(last_seen, dict):
            last_seen = {}

        frames = {}
        for symbol in universe:
            raw = (bars or {}).get(symbol) or []
            if not raw:
                self.last_evaluation["symbol_states"][symbol] = "no_bars"
                continue
            previous = _number(last_seen.get(symbol))
            frame, state = self._frame(symbol, raw, ctx, previous)
            if frame is not None:
                frames[symbol] = frame
                setups = frame["setups"]
                consumed = frame["same_bar_consumed"]
                self.last_evaluation["symbol_states"][symbol] = (
                    "same_bar_consumed" if consumed else
                    "new_bar_signal" if setups else "new_bar_no_signal"
                )
                if not consumed:
                    for setup in setups:
                        self.last_evaluation["signals"].append({
                            "symbol": symbol,
                            "direction": setup["direction"],
                            "rsi_delta": round(setup["rsi_delta"], 2),
                            "regime": setup["regime"],
                            "risk_scale": round(setup["risk_scale"], 3),
                            "bar_close": frame["close_dt"].isoformat(),
                        })
            else:
                self.last_evaluation["symbol_states"][symbol] = state

        self.last_evaluation["new_bars"] = sum(
            1 for frame in frames.values()
            if not frame["same_bar_consumed"]
        )
        for reason in self.last_evaluation["symbol_states"].values():
            if reason.startswith("blocked_") or reason == "outside_entry_window":
                counts = self.last_evaluation["candidate_rejections"]
                counts[reason] = counts.get(reason, 0) + 1

        if open_positions:
            orders = extra.get("session_orders")
            if orders is None:
                self.last_evaluation["state"] = "blocked_exit_order_state_unavailable"
                return []
            state = extra.get("sleeve_state") or {}
            had_working_exit = False
            for symbol, qty in sorted(open_positions.items()):
                if qty <= 0:
                    continue
                working_exit = any(
                    _working_exit_order(order, symbol) for order in orders
                )
                if working_exit:
                    had_working_exit = True
                    continue

                frame = frames.get(symbol)
                if frame is None:
                    continue
                entry = state.get(symbol) or {}
                position = entry.get("position") if isinstance(entry, dict) else {}
                position = position if isinstance(position, dict) else {}
                stop = _number(position.get("stop_px"))
                target = _number(position.get("target_px"))
                for rule in position.get("exit_rules") or []:
                    if not isinstance(rule, dict):
                        continue
                    value = _number(rule.get("value"))
                    if value is None:
                        continue
                    if rule.get("kind") == "stop" and stop is None:
                        stop = value
                    elif rule.get("kind") == "target" and target is None:
                        target = value
                entry_t = _number(
                    position.get("entry_bar_t",
                                 position.get("entry_t", position.get("fill_t")))
                )
                bars_held = sum(
                    1 for bar in frame["bars"]
                    if entry_t is not None
                    and bar["t"] + BAR_SECONDS > entry_t
                )
                latest = frame["latest"]
                setup = next(
                    (item for item in frame["setups"] if item["direction"] < 0),
                    None,
                )
                exit_reason = None
                # Conservative same-bar ordering: if both levels traded,
                # record the stop outcome before the target outcome.
                if stop is not None and latest["l"] <= stop:
                    exit_reason = f"primary_stop_touched stop={stop:.4f}"
                elif target is not None and latest["h"] >= target:
                    exit_reason = f"basis_target_touched target={target:.4f}"
                elif bars_held >= MAX_HOLD_BARS:
                    exit_reason = f"time_exit bars_held={bars_held}"
                elif setup is not None:
                    pivot_t = frame["bars"][setup["pivot_index"]]["t"]
                    exit_reason = (
                        "bearish upper-band divergence; "
                        f"rsi_now={setup['pivot_rsi']:.2f}; "
                        f"rsi_prev={setup['previous_rsi']:.2f}; "
                        f"pivot_t={pivot_t:.0f}"
                    )
                if exit_reason is None:
                    continue

                signal_date = datetime.fromtimestamp(
                    frame["latest_close_t"], tz=ET
                ).date().isoformat()
                reason = (
                    f"bb_rsi_divergence exit long: {exit_reason}; "
                    f"confirmed_at={frame['latest_close_t']:.0f}"
                )
                self.last_evaluation["state"] = "exit_triggered"
                return [Intent(
                    "exit", symbol, qty=abs(qty),
                    price_hint=latest["c"],
                    reason=reason, side="sell",
                    position_intent="sell_to_close",
                    signal_date=signal_date,
                )]
            self.last_evaluation["state"] = (
                "working_exit_order" if had_working_exit else "position_open"
            )
            return []

        fills = extra.get("session_fills")
        orders = extra.get("session_orders")
        entry_activity = _entry_activity_today(fills, orders)
        if entry_activity is None:
            self.last_evaluation["state"] = "blocked_order_or_fill_state_unavailable"
            return []
        if entry_activity == "filled":
            self.last_evaluation["state"] = "one_filled_entry_per_session"
            return []
        if entry_activity == "working_order":
            self.last_evaluation["state"] = "blocked_working_entry_order"
            return []
        if any(_working_exit_order(order) for order in orders):
            self.last_evaluation["state"] = "blocked_working_exit_order"
            return []

        if extra.get("bar_cursor_ready") is not True:
            self.last_evaluation["state"] = "blocked_bar_cursor_unavailable"
            return []

        candidates = []
        for symbol, frame in frames.items():
            if frame["same_bar_consumed"]:
                continue
            setups = [s for s in frame["setups"] if s["direction"] == 1]
            if not setups:
                continue
            if not (
                ENTRY_CLOSE_START <= frame["close_dt"].time()
                <= ENTRY_CLOSE_END
            ):
                self.last_evaluation["symbol_states"][symbol] = "outside_entry_window"
                continue
            for setup in setups:
                quote = _fresh_quote(
                    extra.get("latest_quote"), symbol, ctx.now
                )
                if quote is None:
                    self.last_evaluation["symbol_states"][symbol] = "blocked_quote_missing_or_stale"
                    continue
                if quote["spread_bps"] > MAX_SPREAD_BPS:
                    self.last_evaluation["symbol_states"][symbol] = "blocked_spread"
                    continue

                entry = _limit_cents(quote["ask"])
                stop = setup["pivot_price"] - STOP_ATR_BUFFER * setup["atr"]
                target = setup["basis"]
                risk_per_share = entry - stop
                reward_per_share = target - entry
                if risk_per_share <= 0 or reward_per_share <= 0:
                    self.last_evaluation["symbol_states"][symbol] = "blocked_nonpositive_payoff"
                    continue
                reward_risk = reward_per_share / risk_per_share
                if reward_risk < MIN_REWARD_RISK:
                    self.last_evaluation["symbol_states"][symbol] = "blocked_reward_risk"
                    continue
                self.last_evaluation["symbol_states"][symbol] = "qualified_candidate"
                candidates.append({
                    "symbol": symbol,
                    "frame": frame,
                    "setup": setup,
                    "quote": quote,
                    "entry": entry,
                    "stop": stop,
                    "target": target,
                    "risk_per_share": risk_per_share,
                    "reward_risk": reward_risk,
                })

        if not candidates:
            if self.last_evaluation["state"] == "scanning":
                self.last_evaluation["state"] = "no_qualified_setup"
            return []

        candidates.sort(key=lambda x: (
            -x["setup"]["risk_scale"],
            -x["reward_risk"],
            -x["setup"]["rsi_delta"],
            -x["setup"]["touch_depth_atr"],
            x["quote"]["spread_bps"],
            x["symbol"],
        ))
        chosen = candidates[0]

        equity = _number(ctx.equity)
        if equity is None or equity <= 0:
            self.last_evaluation["state"] = "blocked_equity_unavailable"
            return []
        risk_budget = equity * RISK_PCT * chosen["setup"]["risk_scale"]
        notional_cap = equity * MAX_NOTIONAL_PCT
        qty = int(math.floor(min(
            risk_budget / chosen["risk_per_share"],
            notional_cap / chosen["entry"],
        )))
        if qty <= 0:
            self.last_evaluation["state"] = "blocked_size_zero"
            return []

        frame = chosen["frame"]
        setup = chosen["setup"]
        quote = chosen["quote"]
        pivot_t = frame["bars"][setup["pivot_index"]]["t"]
        signal_date = datetime.fromtimestamp(
            frame["latest_close_t"], tz=ET
        ).date().isoformat()
        reason = (
            "bb_rsi_divergence v2 long: confirmed lower-band bullish "
            f"divergence; regime={setup['regime']}; "
            f"er={setup['efficiency_ratio']:.3f}; "
            f"bandwalk={setup['band_walk_count']}; "
            f"atr_pct={setup['atr_pct']:.5f}; "
            f"atr_ratio={setup['atr_ratio']:.3f}; "
            f"vol_scale={setup['vol_scale']:.3f}; "
            f"trend_scale={setup['trend_scale']:.3f}; "
            f"risk_scale={setup['risk_scale']:.3f}; "
            f"rsi_now={setup['pivot_rsi']:.2f}; "
            f"rsi_prev={setup['previous_rsi']:.2f}; "
            f"rsi_delta={setup['rsi_delta']:.2f}; "
            f"pivot_t={pivot_t:.0f}; "
            f"confirmed_at={frame['latest_close_t']:.0f}; "
            f"quote_t={quote['t']:.3f}; bid={quote['bid']:.4f}; "
            f"ask={quote['ask']:.4f}; spread_bps={quote['spread_bps']:.2f}; "
            f"entry_limit={chosen['entry']:.2f}; stop={chosen['stop']:.4f}; "
            f"target_basis={chosen['target']:.4f}; "
            f"rr={chosen['reward_risk']:.2f}; qty={qty}"
        )
        self.last_evaluation["state"] = "entry_intent"
        self.last_evaluation["selected_symbol"] = chosen["symbol"]
        self.last_evaluation["size"] = qty
        self.last_evaluation["risk_budget"] = round(risk_budget, 2)
        self.last_evaluation["base_risk_budget"] = round(equity * RISK_PCT, 2)
        self.last_evaluation["risk_scale"] = round(setup["risk_scale"], 3)
        self.last_evaluation["reward_risk"] = round(chosen["reward_risk"], 3)

        return [Intent(
            "enter",
            chosen["symbol"],
            qty=qty,
            limit_price=chosen["entry"],
            price_hint=chosen["entry"],
            stop=chosen["stop"],
            target=chosen["target"],
            exit_rules=(
                ExitRule("stop", chosen["stop"]),
                ExitRule("target", chosen["target"]),
                ExitRule("time_bars", float(MAX_HOLD_BARS)),
            ),
            reason=reason,
            side="buy",
            position_intent="buy_to_open",
            signal_date=signal_date,
        )]
