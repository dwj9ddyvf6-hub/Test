"""QQQ put ladder from the public campaign, paper only.

The campaign, as stated: sell three puts about 45 days out, delta about 0.05
to 0.08, then wait a week and do it again. Manage the oldest layer around 21
days. Roll the strike up in the same expiration only after QQQ has risen and
the put has lost a meaningful amount of value. Do not roll up just because a
week passed. If QQQ falls, volatility or the macro posture deteriorates, or a
put becomes challenged, stop adding. A challenged layer near 21 days is rolled
out and down, or closed. Leave a healthy strike alone when the roll has not
been earned.

Desk limits that the campaign left open, fixed here so the paper account can
run them: at most 12 open contracts, a put is challenged at 0.20 delta or when
spot is within 3% of the strike, "meaningful" decay is half the entry credit,
and a short put is bought back at 5 days so the paper book does not take
assignment by drifting into expiration week. Alpaca level 3 secures a short
put with cash. The QQQ shares are not acceptable collateral on this account.
The ladder never changes the Aurelia ticket.
"""

from __future__ import annotations

import re
from datetime import date

UNDERLYING = "QQQ"
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


def parse_occ(symbol: str) -> dict | None:
    match = _OCC.match(symbol or "")
    if not match:
        return None
    year = 2000 + int(match.group(2)[:2])
    month = int(match.group(2)[2:4])
    day = int(match.group(2)[4:6])
    return {
        "root": match.group(1),
        "expiration": date(year, month, day).isoformat(),
        "cp": match.group(3),
        "strike": int(match.group(4)) / 1000.0,
    }


def cash_required(strike: float, bid: float, qty: int = LAYER_QTY) -> float:
    """Cash a cash-secured put reserves: strike proceeds minus the bid premium."""
    return round(max(0.0, float(strike) - float(bid)) * 100.0 * int(qty), 2)


def iso_week(day: date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def price_fell(closes: list[float], lookback: int = WEEK_LOOKBACK) -> bool | None:
    """True when the last close is below the close `lookback` sessions earlier."""
    if len(closes) <= lookback:
        return None
    return float(closes[-1]) < float(closes[-1 - lookback])


def dte(expiration: str, today: date) -> int:
    return (date.fromisoformat(expiration) - today).days


def challenged(strike: float, delta: float, spot: float) -> bool:
    if abs(float(delta)) >= CHALLENGED_DELTA:
        return True
    return float(spot) <= float(strike) * CHALLENGED_SPOT


def _tradable(quote: dict, spot: float) -> bool:
    bid = float(quote.get("bid") or 0)
    ask = float(quote.get("ask") or 0)
    strike = float(quote["strike"])
    if bid < MIN_BID or ask <= bid or strike >= spot:
        return False
    mid = (bid + ask) / 2.0
    return (ask - bid) <= max(0.10, 0.25 * mid)


def pick_short_put(quotes: list[dict], today: date, spot: float, *, expiration: str | None = None,
                    strike_above: float | None = None, strike_at_most: float | None = None,
                    exclude_expirations: set[str] | None = None) -> dict | None:
    """The put inside the campaign band, or None. Near-misses stay out."""
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
    found.sort(key=lambda quote: (
        abs(dte(quote["expiration"], today) - TARGET_DTE),
        abs(abs(float(quote["delta"])) - TARGET_DELTA),
        float(quote["ask"]) - float(quote["bid"]),
        float(quote["strike"]),
    ))
    chosen = dict(found[0])
    chosen["delta"] = abs(float(chosen["delta"]))
    chosen["dte"] = dte(chosen["expiration"], today)
    chosen["qty"] = LAYER_QTY
    chosen["cash_required"] = cash_required(chosen["strike"], chosen["bid"], LAYER_QTY)
    return chosen


def _quote_map(quotes: list[dict]) -> dict[str, dict]:
    return {quote["symbol"]: quote for quote in quotes if quote.get("symbol")}


def _open_layers(layers: list[dict]) -> list[dict]:
    return [layer for layer in layers if layer.get("status") in {"working", "open"}]


def _add_block(today: date, spot: float, quotes: list[dict], layers: list[dict], *, posture: str,
               fell: bool | None, buying_power: float | None, equity_pending: bool,
               week_opened: str | None) -> tuple[str | None, dict | None]:
    candidate = pick_short_put(quotes, today, spot, exclude_expirations={
        layer["expiration"] for layer in _open_layers(layers)
    })
    # Aurelia remains the main equity book. A pending equity ticket does not
    # stop this separate paper test; the broker still has to accept the cash.
    _ = equity_pending
    if posture != "normal":
        return f"posture_{posture}", candidate
    if fell is None:
        return "data_unavailable", candidate
    if fell:
        return "qqq_down_on_the_week", candidate
    if any(challenged(layer["strike"], _delta_of(layer, quotes), spot) for layer in _open_layers(layers)):
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


def _delta_of(layer: dict, quotes: list[dict]) -> float:
    live = _quote_map(quotes).get(layer.get("symbol") or "")
    if live and live.get("delta") is not None:
        return abs(float(live["delta"]))
    return abs(float(layer.get("entry_delta") or 0))


def _limit(side: str, quote: dict) -> float:
    raw = float(quote["bid"] if side == "sell" else quote["ask"])
    return round(raw + 1e-9, 2)


def decide(layers: list[dict], quotes: list[dict], today: date, spot: float, *, posture: str,
           fell: bool | None, buying_power: float | None, equity_pending: bool,
           week_opened: str | None) -> dict:
    """Actions for one session. A blocked new layer is still returned as `candidate`."""
    by_symbol = _quote_map(quotes)
    actions = []
    missing_quote = False
    for layer in sorted(_open_layers(layers), key=lambda row: row.get("expiration") or ""):
        life = dte(layer["expiration"], today)
        quote = by_symbol.get(layer["symbol"])
        if quote is None:
            missing_quote = True
            continue
        delta = abs(float(quote["delta"]))
        is_hot = challenged(layer["strike"], delta, spot)
        if life <= CLOSE_DTE:
            actions.append(_close(layer, quote, "inside five days of expiration"))
            continue
        if life > MANAGE_DTE or layer.get("rolled_on") == today.isoformat():
            continue
        entry_spot = float(layer.get("entry_spot") or 0)
        entry_credit = float(layer.get("entry_credit") or 0)
        earned = (
            posture == "normal"
            and not is_hot
            and spot > entry_spot
            and entry_credit > 0
            and float(quote["ask"]) <= DECAY_RATIO * entry_credit
        )
        if earned:
            higher = pick_short_put(
                quotes, today, spot, expiration=layer["expiration"], strike_above=float(layer["strike"]),
            )
            if higher and float(higher["bid"]) > float(quote["ask"]):
                actions.append({
                    "kind": "roll_up",
                    "qty": int(layer["qty"]),
                    "reason": "QQQ is higher and the put has lost half its credit",
                    "layer_id": layer["id"],
                    "close": _leg(layer["symbol"], "buy", quote, int(layer["qty"])),
                    "open": _leg(higher["symbol"], "sell", higher, int(layer["qty"]), contract=higher),
                })
                continue
        if is_hot:
            later = pick_short_put(quotes, today, spot, strike_at_most=float(layer["strike"]))
            if later and later["symbol"] != layer["symbol"] and posture != "stand_down":
                actions.append({
                    "kind": "roll_out",
                    "qty": int(layer["qty"]),
                    "reason": "the put is challenged, so the strike moves out and not up",
                    "layer_id": layer["id"],
                    "close": _leg(layer["symbol"], "buy", quote, int(layer["qty"])),
                    "open": _leg(later["symbol"], "sell", later, int(layer["qty"]), contract=later),
                })
            else:
                actions.append(_close(layer, quote, "the put is challenged"))
    add_block, candidate = _add_block(
        today, spot, quotes, layers, posture=posture, fell=fell, buying_power=buying_power,
        equity_pending=equity_pending, week_opened=week_opened,
    )
    if missing_quote and add_block is None:
        add_block = "quote_missing"
    if add_block is None and candidate is not None:
        actions.append({
            "kind": "sell_open",
            "qty": LAYER_QTY,
            "reason": "new weekly layer",
            "close": None,
            "open": _leg(candidate["symbol"], "sell", candidate, LAYER_QTY, contract=candidate),
        })
    return {"actions": actions, "add_block": add_block, "candidate": candidate}


def _leg(symbol: str, side: str, quote: dict, qty: int, contract: dict | None = None) -> dict:
    body = {
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "limit": _limit(side, quote),
        "position_intent": "sell_to_open" if side == "sell" else "buy_to_close",
    }
    if contract:
        body.update({
            "expiration": contract["expiration"],
            "strike": contract["strike"],
            "delta": contract["delta"],
            "bid": contract["bid"],
            "ask": contract["ask"],
            "dte": contract.get("dte"),
            "cash_required": contract.get("cash_required"),
        })
    return body


def _close(layer: dict, quote: dict, reason: str) -> dict:
    return {
        "kind": "buy_close",
        "qty": int(layer["qty"]),
        "reason": reason,
        "layer_id": layer["id"],
        "close": _leg(layer["symbol"], "buy", quote, int(layer["qty"])),
        "open": None,
    }


def explain(add_block: str | None, candidate: dict | None, *, market_closed: bool, buying_power: float | None) -> str:
    """One sentence the desk can show. The campaign block stays visible when the session is shut."""
    bits = []
    if market_closed:
        bits.append("Nothing is sent while the session is shut.")
    text = {
        "aurelia_ticket_open": "Aurelia's equity ticket is still unfilled, so this cash stays with that book.",
        "qqq_down_on_the_week": "QQQ is down over the last five sessions, so no new layer is added.",
        "a_put_is_challenged": "A put is challenged, so the ladder stops adding.",
        "ladder_full": "Twelve contracts are already open. That is the size of this account's ladder.",
        "already_added_this_week": "A layer was already opened this week.",
        "no_contract": "No 38-to-52-day put sits inside the 0.05 to 0.08 delta band.",
        "insufficient_options_buying_power": _cash_sentence(candidate, buying_power),
        "data_unavailable": "A quote or the weekly QQQ change is missing, so nothing new is added.",
        "quote_missing": "An open put has no quote, so nothing new is added.",
    }.get(add_block or "")
    if add_block and add_block.startswith("posture_"):
        text = f"The desk posture is {add_block.removeprefix('posture_')}, so no new layer is added."
    if text:
        bits.append(text)
    if candidate:
        bits.append(
            f"The next layer would be {candidate['qty']} {candidate['expiration']} {candidate['strike']:g} puts, "
            f"delta {candidate['delta']:.2f}, about ${candidate['cash_required']:,.0f} secured."
        )
    return " ".join(bits) if bits else "No ladder action this cycle."


def _cash_sentence(candidate: dict | None, buying_power: float | None) -> str:
    need = f"${candidate['cash_required']:,.0f}" if candidate else "the strike cash"
    have = f"${float(buying_power):,.0f}" if buying_power is not None else "an unknown amount"
    return (
        f"Three contracts need {need} of options buying power and the account has {have}. "
        "Alpaca secures these puts with cash, not with the QQQ shares."
    )


def client_order_id(session: str, expiration: str, strike: float, intent: str, attempt: int = 1) -> str:
    """Broker id, at most 48 characters. Intent is `sto` or `btc`."""
    stamp = session.replace("-", "")
    exp = expiration[2:4] + expiration[5:7] + expiration[8:10]
    strike_code = int(round(float(strike) * 10))
    base = f"ld-{stamp}-{exp}-{strike_code}-{intent}"
    if attempt > 1:
        base = f"{base}-r{attempt}"
    return base[:48]
