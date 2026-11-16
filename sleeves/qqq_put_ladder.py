"""QQQ put ladder — lean-desk port (Wave D, Decision #119 family).

EXTRACTED VERBATIM from the old desk's aurelia_put_ladder.py (pure
ladder rules, no dependencies in the source): sell 3 puts ~45 DTE,
delta 0.05-0.08, one new layer per ISO week; manage the oldest layer at
~21 DTE; roll up in the same expiration only after QQQ rose AND the put
lost half its entry credit; a challenged layer (delta >= 0.20 or spot
within 3% of strike) near manage age rolls out-and-down or closes;
buy back at 5 DTE. Desk limits fixed by the source: max 12 open
contracts, cash-secured (cash_required = (strike - bid) * 100 * qty).

VIRTUAL BOOK MAPPING: Ledger account "qqq_put_ladder". Its budget is
cash-secured by construction — aurelia_common.BUDGETS lists it as None
(no fixed budget; each layer's cash_required is the Risk budget check,
supplied as context.extra["buying_power"]). The ladder's layers ARE
the book state: context.extra["layers"] (the old state file's layer
dicts). The old module's broker I/O (aurelia_ladder_broker.py) does
not come over; decide() actions map to intents: sell_open -> enter,
buy_close -> exit, roll_up/roll_out -> exit(close leg) + enter(open leg).

Inputs via context.extra: "layers", "quotes" (option quote dicts with
symbol/expiration/strike/delta/bid/ask), "spot", "posture",
"qqq_closes" (for price_fell), "buying_power", "equity_pending",
"week_opened". Today = context.session.
"""
import re
from datetime import date

from core.sleeve import BaseSleeve, Intent, SleeveConfig

UNDERLYING = "QQQ"
ACCOUNT = "qqq_put_ladder"
LAYER_QTY = 3
DELTA_LO = 0.05
DELTA_HI = 0.08
TARGET_DELTA = 0.05
DTE_LO = 38
DTE_HI = 52
TARGET_DTE = 45
MANAGE_DTE = 21
CLOSE_DTE = 5
MAX_CONTRACTS = 12
CHALLENGED_DELTA = 0.20
CHALLENGED_SPOT = 1.03
DECAY_RATIO = 0.50
WEEK_LOOKBACK = 5
MIN_BID = 0.05
_OCC = re.compile(r"^([A-Z]{1,6})(\d{6})([CP])(\d{8})$")

CONFIG = SleeveConfig(
    sleeve_id="qqq_put_ladder", cadence_s=900, universe=(UNDERLYING,),
    state_schema={"layers": "list"}, risk_pct=None)


# --- aurelia_put_ladder.py, verbatim ------------------------------------
def parse_occ(symbol):
    match = _OCC.match(symbol or "")
    if not match:
        return None
    year = 2000 + int(match.group(2)[:2])
    month = int(match.group(2)[2:4])
    day = int(match.group(2)[4:6])
    return {"root": match.group(1), "expiration": date(year, month, day).isoformat(),
            "cp": match.group(3), "strike": int(match.group(4)) / 1000.0}


def cash_required(strike, bid, qty=LAYER_QTY):
    return round(max(0.0, float(strike) - float(bid)) * 100.0 * int(qty), 2)


def iso_week(day):
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def price_fell(closes, lookback=WEEK_LOOKBACK):
    if len(closes) <= lookback:
        return None
    return float(closes[-1]) < float(closes[-1 - lookback])


def dte(expiration, today):
    return (date.fromisoformat(expiration) - today).days


def challenged(strike, delta, spot):
    if abs(float(delta)) >= CHALLENGED_DELTA:
        return True
    return float(spot) <= float(strike) * CHALLENGED_SPOT


def _tradable(quote, spot):
    bid = float(quote.get("bid") or 0)
    ask = float(quote.get("ask") or 0)
    strike = float(quote["strike"])
    if bid < MIN_BID or ask <= bid or strike >= spot:
        return False
    mid = (bid + ask) / 2.0
    return (ask - bid) <= max(0.10, 0.25 * mid)


def pick_short_put(quotes, today, spot, *, expiration=None, strike_above=None,
                   strike_at_most=None, exclude_expirations=None):
    excluded = exclude_expirations or set()
    found = []
    for quote in quotes:
        if quote.get("expiration") in excluded:
            continue
        if expiration and quote.get("expiration") != expiration:
            continue
        life = dte(quote["expiration"], today)
        if expiration is None and not (DTE_LO <= life <= DTE_HI):
            continue
        if life < 0:
            continue
        delta = abs(float(quote.get("delta") or 0))
        if not (DELTA_LO <= delta <= DELTA_HI):
            continue
        if strike_above is not None and float(quote["strike"]) <= float(strike_above):
            continue
        if strike_at_most is not None and float(quote["strike"]) > float(strike_at_most):
            continue
        if not _tradable(quote, spot):
            continue
        found.append(quote)
    if not found:
        return None
    found.sort(key=lambda q: (abs(dte(q["expiration"], today) - TARGET_DTE),
                              abs(abs(float(q["delta"])) - TARGET_DELTA),
                              float(q["ask"]) - float(q["bid"]),
                              float(q["strike"])))
    chosen = dict(found[0])
    chosen["delta"] = abs(float(chosen["delta"]))
    chosen["dte"] = dte(chosen["expiration"], today)
    chosen["qty"] = LAYER_QTY
    chosen["cash_required"] = cash_required(chosen["strike"], chosen["bid"], LAYER_QTY)
    return chosen


def _quote_map(quotes):
    return {q["symbol"]: q for q in quotes if q.get("symbol")}


def _open_layers(layers):
    return [layer for layer in layers if layer.get("status") in {"working", "open"}]


def _delta_of(layer, quotes):
    live = _quote_map(quotes).get(layer.get("symbol") or "")
    if live and live.get("delta") is not None:
        return abs(float(live["delta"]))
    return abs(float(layer.get("entry_delta") or 0))


def _limit(side, quote):
    raw = float(quote["bid"] if side == "sell" else quote["ask"])
    return round(raw + 1e-9, 2)


def _leg(symbol, side, quote, qty, contract=None):
    body = {"symbol": symbol, "side": side, "qty": qty, "limit": _limit(side, quote),
            "position_intent": "sell_to_open" if side == "sell" else "buy_to_close"}
    if contract:
        body.update({"expiration": contract["expiration"], "strike": contract["strike"],
                     "delta": contract["delta"], "bid": contract["bid"],
                     "ask": contract["ask"], "dte": contract.get("dte"),
                     "cash_required": contract.get("cash_required")})
    return body


def _close(layer, quote, reason):
    return {"kind": "buy_close", "qty": int(layer["qty"]), "reason": reason,
            "layer_id": layer["id"],
            "close": _leg(layer["symbol"], "buy", quote, int(layer["qty"])), "open": None}


def _add_block(today, spot, quotes, layers, *, posture, fell, buying_power,
               equity_pending, week_opened):
    candidate = pick_short_put(quotes, today, spot, exclude_expirations={
        layer["expiration"] for layer in _open_layers(layers)})
    _ = equity_pending  # a pending equity ticket does not stop this test
    if posture != "normal":
        return f"posture_{posture}", candidate
    if fell is None:
        return "data_unavailable", candidate
    if fell:
        return "qqq_down_on_the_week", candidate
    if any(challenged(layer["strike"], _delta_of(layer, quotes), spot)
           for layer in _open_layers(layers)):
        return "a_put_is_challenged", candidate
    open_qty = sum(int(layer.get("qty") or 0) for layer in _open_layers(layers))
    if open_qty + LAYER_QTY > MAX_CONTRACTS:
        return "ladder_full", candidate
    if week_opened == iso_week(today):
        return "already_added_this_week", candidate
    if candidate is None:
        return "no_contract", None
    if buying_power is None:
        return "data_unavailable", candidate
    if float(buying_power) < float(candidate["cash_required"]):
        return "insufficient_options_buying_power", candidate
    return None, candidate


def challenged_any_dte_enabled(extra):
    """ENH-qqq_put_ladder (Edge IMPROVE, Group A): context.extra
    ["qqq_put_ladder_improve"]["challenged_any_dte"], default ON;
    OFF restores the pre-change 21-DTE-gated rule exactly (control)."""
    ov = (extra or {}).get("qqq_put_ladder_improve")
    if isinstance(ov, dict) and "challenged_any_dte" in ov:
        return bool(ov["challenged_any_dte"])
    return True


def decide(layers, quotes, today, spot, *, posture, fell, buying_power,
           equity_pending, week_opened, enhanced=True):
    """Verbatim port of the source decide(): actions for one session.
    ENH: with enhanced=True (the default), the existing challenged
    branch (roll out-and-down, else close) is evaluated for a layer at
    any DTE; the 21-DTE gate survives only on the roll-UP branch
    (IMPROVE-qqq_put_ladder section 2)."""
    by_symbol = _quote_map(quotes)
    actions = []
    missing_quote = False
    for layer in sorted(_open_layers(layers), key=lambda row: row.get("expiration") or ""):
        life = dte(layer["expiration"], today)
        quote = by_symbol.get(layer["symbol"])
        if quote is None:
            missing_quote = True
            if life <= CLOSE_DTE:
                # D-B5 cure (2026-10-22): the 5-DTE buy-back must
                # not silently skip on a missing quote — emit an
                # unpriced close (the desk EOD/market door), the
                # saty_sol liquidation precedent.
                actions.append({
                    "kind": "buy_close", "qty": int(layer["qty"]),
                    "reason": "inside five days of expiration "
                              "(quote missing: unpriced close)",
                    "layer_id": layer["id"],
                    "close": {"symbol": layer["symbol"],
                              "side": "buy", "qty": int(layer["qty"]),
                              "limit": None,
                              "position_intent": "buy_to_close"},
                    "open": None, "unpriced_close": True})
            continue
        delta = abs(float(quote["delta"]))
        is_hot = challenged(layer["strike"], delta, spot)
        if life <= CLOSE_DTE:
            actions.append(_close(layer, quote, "inside five days of expiration"))
            continue
        if enhanced and is_hot and layer.get("rolled_on") != today.isoformat():
            later = pick_short_put(quotes, today, spot, strike_at_most=float(layer["strike"]))
            if later and later["symbol"] != layer["symbol"] and posture != "stand_down":
                actions.append({
                    "kind": "roll_out", "qty": int(layer["qty"]),
                    "reason": "the put is challenged, so the strike moves out and not up",
                    "layer_id": layer["id"],
                    "close": _leg(layer["symbol"], "buy", quote, int(layer["qty"])),
                    "open": _leg(later["symbol"], "sell", later, int(layer["qty"]),
                                 contract=later)})
            else:
                actions.append(_close(layer, quote, "the put is challenged"))
            continue
        if life > MANAGE_DTE or layer.get("rolled_on") == today.isoformat():
            continue
        entry_spot = float(layer.get("entry_spot") or 0)
        entry_credit = float(layer.get("entry_credit") or 0)
        earned = (posture == "normal" and not is_hot and spot > entry_spot
                  and entry_credit > 0 and float(quote["ask"]) <= DECAY_RATIO * entry_credit)
        if earned:
            higher = pick_short_put(quotes, today, spot, expiration=layer["expiration"],
                                    strike_above=float(layer["strike"]))
            if higher and float(higher["bid"]) > float(quote["ask"]):
                actions.append({
                    "kind": "roll_up", "qty": int(layer["qty"]),
                    "reason": "QQQ is higher and the put has lost half its credit",
                    "layer_id": layer["id"],
                    "close": _leg(layer["symbol"], "buy", quote, int(layer["qty"])),
                    "open": _leg(higher["symbol"], "sell", higher, int(layer["qty"]),
                                 contract=higher)})
                continue
        if is_hot:
            later = pick_short_put(quotes, today, spot, strike_at_most=float(layer["strike"]))
            if later and later["symbol"] != layer["symbol"] and posture != "stand_down":
                actions.append({
                    "kind": "roll_out", "qty": int(layer["qty"]),
                    "reason": "the put is challenged, so the strike moves out and not up",
                    "layer_id": layer["id"],
                    "close": _leg(layer["symbol"], "buy", quote, int(layer["qty"])),
                    "open": _leg(later["symbol"], "sell", later, int(layer["qty"]),
                                 contract=later)})
            else:
                actions.append(_close(layer, quote, "the put is challenged"))
    add_block, candidate = _add_block(
        today, spot, quotes, layers, posture=posture, fell=fell,
        buying_power=buying_power, equity_pending=equity_pending,
        week_opened=week_opened)
    if missing_quote and add_block is None:
        add_block = "quote_missing"
    if add_block is None and candidate is not None:
        actions.append({"kind": "sell_open", "qty": LAYER_QTY,
                        "reason": "new weekly layer", "close": None,
                        "open": _leg(candidate["symbol"], "sell", candidate,
                                     LAYER_QTY, contract=candidate)})
    return {"actions": actions, "add_block": add_block, "candidate": candidate}


class QqqPutLadder(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        spot = extra.get("spot")
        if spot is None:
            bl = bars.get(UNDERLYING) or []
            spot = float(bl[-1]["c"]) if bl else None
        if spot is None:
            return []
        today = date.fromisoformat(context.session)
        quotes = list(extra.get("quotes") or [])
        layers = list(extra.get("layers") or [])
        decision = decide(
            layers, quotes, today, float(spot), posture=extra.get("posture") or "unknown",
            fell=price_fell(list(extra.get("qqq_closes") or [])),
            buying_power=extra.get("buying_power"),
            equity_pending=bool(extra.get("equity_pending")),
            week_opened=extra.get("week_opened"),
            enhanced=challenged_any_dte_enabled(extra))
        intents = []
        for action in decision["actions"]:
            close_leg, open_leg = action.get("close"), action.get("open")
            if close_leg:
                if close_leg.get("limit") is None:
                    intents.append(Intent(
                        "exit", close_leg["symbol"],
                        qty_hint=int(close_leg["qty"]),
                        reason="qqq_put_ladder %s buy_to_close layer=%s: %s (account=%s)"
                               % (action["kind"], action.get("layer_id"),
                                  action["reason"], ACCOUNT)))
                    continue
                intents.append(Intent(
                    "exit", close_leg["symbol"], qty_hint=int(close_leg["qty"]),
                    limit_price=float(close_leg["limit"]),
                    price_hint=float(close_leg["limit"]),
                    reason="qqq_put_ladder %s buy_to_close layer=%s: %s (account=%s)"
                           % (action["kind"], action.get("layer_id"),
                              action["reason"], ACCOUNT)))
            if open_leg:
                intents.append(Intent(
                    "enter", open_leg["symbol"], qty_hint=int(open_leg["qty"]),
                    limit_price=float(open_leg["limit"]),
                    price_hint=float(open_leg["limit"]),
                    reason="qqq_put_ladder %s sell_to_open cash_required=%s "
                           "delta=%s dte=%s (account=%s)"
                           % (action["kind"], open_leg.get("cash_required"),
                              open_leg.get("delta"), open_leg.get("dte"), ACCOUNT)))
        return intents


def signal(bars, slice_state, context):
    return QqqPutLadder().signal(bars, slice_state, context)
