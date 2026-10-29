"""midna_hyperliquid_momentum_floor — Midna's Hyperliquid paper floor (src/lib/desk.ts @ entire 43f08f96, blob 4fa32cb6,
lines 194-387: runScan / propose, with decide / applyExits / closeAt / maybeWatch; src/lib/decide.ts, blob 0a178f61:
pickScan, classifySetup, stopDistancePct, sizeTrade, levels, withinCaps, fillPrice, exitSignal), ported line for line,
on Hyperliquid's public book (desk/feedlib/midna_hyperliquid.py, the market.ts port).

  scan     every 10 minutes while armed and no ticket is pending: the perps with a day notional >= $25M ranked by
           |day move|; a setup is up >= 1% with funding <= 0.004% (not a crowded long) -> long, or down >= 1% with
           funding >= -0.001% (not a crowded short) -> short; BTC / ETH / SOL first when one qualifies, else the
           strongest qualifying move; a (coin, side) in its 6-hour reject cooldown is passed over
  ticket   stop distance = max(0.6%, 1.2 x the mean hourly range of the last 8 hours), at most 8% (1.2% without
           candles); stop / target = mark -/+ the stop distance / 2R; notional = floor(min(0.5% of equity / stop
           distance, 20% of equity single-name cap, 60% gross cap room)), >= $50, at most 3 open; no second ticket in
           an open coin
  fill     at approval, re-checked at the door (a mark through the stop kills it; the book, the caps and the coin
           checked again): the mark +/- 1 bp against; qty = notional / entry
  exits    each pass with a live book: the mark through the stop or the target closes at the mark -/+ 1 bp

Removed (cutover doctrine): the daily loss halt (dailyLossHaltPct 3%: "No new risk until the next UTC day" — a
drawdown brake / kill switch) and with it rollDay / refreshHalt.

Named divergences: the floor queued every ticket for the operator's approval with the watch off until armed; the
forward test runs the watch armed and approves each ticket at once (the floor's own door checks still run) — so no
ticket is ever rejected and the reject cooldown never starts; Hyperliquid is not a desk venue: a coin trades as its
Kraken Futures perpetual on the sim venue sim:kraken_futures (the notional sized on the Hyperliquid mark, filled at
the Kraken quote; a coin Kraken does not list like for like — the 'k' thousand-unit coins and unlisted names — is
not traded and its ticket is recorded as unfilled), while the scan, the stop / target and the exits read the
Hyperliquid marks as the source did; the engine accrues Kraken perpetual funding on the open book (the paper floor
booked no funding) and charges its venue costs instead of the 1 bp slippage; equity is the engine book's; the floor
closed a position at the mark at once, the engine's exit child can end unfilled, so an exit sent is kept (state
"closing") and sent again until its perp is flat."""
import math

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig

SOURCE = {"repo": "midna", "ref": "entire", "commit": "43f08f96fce33ee67521002e09f8bc7534cfe264",
          "path": "src/lib/desk.ts", "blob": "4fa32cb66f732bd0a3f79ee3cd4ed3024bb1c696", "lines": [194, 387],
          "decide": {"path": "src/lib/decide.ts", "blob": "0a178f61506ada2afc615889317ce24c9c271de4"},
          "market": {"path": "src/lib/market.ts", "blob": "9e07dd93"}}
RULES = {"trendPct": 0.01, "crowdedLongFunding": 0.00004, "crowdedShortFunding": -0.00001, "minStopPct": 0.006,
         "rangeMultiple": 1.2, "fallbackStopPct": 0.012, "maxStopPct": 0.08, "rewardMultiple": 2, "slippageBps": 1,
         "minDayNotional": 25_000_000, "minNotional": 50, "watchMinutes": 10, "rejectCooldownHours": 6,
         "startingCash": 100_000}
LIMITS = {"riskPerTradePct": 0.5, "maxOpenPositions": 3, "dailyLossHaltPct": 3, "maxGrossNotionalPct": 60,
          "singleNameNotionalPct": 20}
MAJORS = ("BTC", "ETH", "SOL")
REMOVED = ["daily loss halt: day P&L <= -3% -> no new risk until the next UTC day (drawdown brake / kill switch)"]


def classify_setup(q):
    ch, f = q["changePct"], q["funding"]
    if not math.isfinite(f) or not math.isfinite(ch):
        return None
    if ch >= RULES["trendPct"] and f <= RULES["crowdedLongFunding"]:
        return "long"
    if ch <= -RULES["trendPct"] and f >= RULES["crowdedShortFunding"]:
        return "short"
    return None


def candidates(quotes):
    """the coins a scan can pick (the liquid qualifying movers) — the feed fetches their hourly ranges."""
    return {q["coin"] for q in quotes if q["dayNotional"] >= RULES["minDayNotional"] and classify_setup(q)}


def pick_scan(quotes, cooling):
    liquid = [q for q in quotes if q["dayNotional"] >= RULES["minDayNotional"]]
    ranked = sorted(((q, classify_setup(q)) for q in liquid), key=lambda x: -abs(x[0]["changePct"]))
    tradable = [x for x in ranked if x[1] and not cooling(x[0]["coin"], x[1])]
    majors = [x for x in tradable if x[0]["coin"] in MAJORS]
    pool = majors if majors else tradable
    return (pool[0][0], pool[0][1]) if pool else None


def stop_distance_pct(avg_range):
    if avg_range is None:
        return RULES["fallbackStopPct"]
    return min(max(RULES["minStopPct"], avg_range * RULES["rangeMultiple"]), RULES["maxStopPct"])


def size_trade(equity, stop_pct, gross_used, open_positions, limits=LIMITS):
    if open_positions >= limits["maxOpenPositions"]:
        return None
    if not (stop_pct > 0) or not math.isfinite(stop_pct):
        return None
    if not (equity > 0):
        return None
    budget = equity * (limits["riskPerTradePct"] / 100)
    notional = budget / stop_pct
    single = equity * (limits["singleNameNotionalPct"] / 100)
    gross = equity * (limits["maxGrossNotionalPct"] / 100)
    room = max(0.0, gross - gross_used)
    if room < RULES["minNotional"]:
        return None
    notional = math.floor(min(notional, single, room))
    if notional < RULES["minNotional"]:
        return None
    return notional


def levels(mark, side, stop_pct):
    if side == "long":
        return mark * (1 - stop_pct), mark * (1 + stop_pct * RULES["rewardMultiple"])
    return mark * (1 + stop_pct), mark * (1 - stop_pct * RULES["rewardMultiple"])


def within_caps(equity, notional, gross_used, limits=LIMITS):
    if not (equity > 0) or not math.isfinite(notional) or notional <= 0:
        return False
    single = equity * (limits["singleNameNotionalPct"] / 100)
    room = equity * (limits["maxGrossNotionalPct"] / 100) - gross_used
    return not (notional > single + 0.5) and not (notional > room + 0.5)


def fill_price(side, mark, kind):
    slip = RULES["slippageBps"] / 10_000
    against = (kind == "entry") if side == "long" else (kind == "exit")
    return mark * (1 + slip) if against else mark * (1 - slip)


def exit_signal(side, mark, stop, target):
    if side == "long":
        return "stop" if mark <= stop else ("target" if mark >= target else None)
    return "stop" if mark >= stop else ("target" if mark <= target else None)


def step(book, now, market, equity):
    """applyExits, then maybeWatch -> runScan("watch") -> propose -> an immediate approve (decide).
    book = {"positions": {coin: {side, entry, stop, target, notional, qty}}, "lastScanAt", "cooldowns"} (mutated).
    -> [orders]"""
    orders = []
    if market.get("stale") or not market.get("quotes"):
        return orders
    marks = {q["coin"]: q["mark"] for q in market["quotes"]}
    for coin, p in list(book["positions"].items()):
        m = marks.get(coin)
        if not (m and m > 0):
            continue
        sig = exit_signal(p["side"], m, p["stop"], p["target"])
        if sig:
            book["positions"].pop(coin)
            orders.append({"action": "exit", "coin": coin, "side": p["side"], "price": fill_price(p["side"], m, "exit"),
                           "reason": sig})
    if book.get("lastScanAt") is not None and now - book["lastScanAt"] < RULES["watchMinutes"] * 60:
        return orders
    book["lastScanAt"] = now
    book["cooldowns"] = [c for c in book.get("cooldowns") or [] if c["until"] > now]
    cooling = lambda coin, side: any(c["coin"] == coin and c["side"] == side for c in book["cooldowns"])
    picked = pick_scan(market["quotes"], cooling)
    if not picked:
        return orders
    q, side = picked
    stop_pct = stop_distance_pct((market.get("ranges") or {}).get(q["coin"]))
    stop, target = levels(q["mark"], side, stop_pct)
    gross = sum(p["notional"] for p in book["positions"].values())
    if q["coin"] in book["positions"]:
        return orders                                       # risk veto: the coin is already open
    notional = size_trade(equity, stop_pct, gross, len(book["positions"]))
    if notional is None:
        return orders
    # approve at once: the door checks of decide()
    through = q["mark"] <= stop if side == "long" else q["mark"] >= stop
    if through or len(book["positions"]) >= LIMITS["maxOpenPositions"] or not within_caps(equity, notional, gross):
        return orders
    entry = fill_price(side, q["mark"], "entry")
    book["positions"][q["coin"]] = {"side": side, "entry": entry, "stop": stop, "target": target,
                                    "notional": notional, "qty": notional / entry, "openedAt": now}
    orders.append({"action": "enter", "coin": q["coin"], "side": side, "price": entry, "notional": notional,
                   "stop": stop, "target": target, "stopPct": stop_pct})
    return orders


class HyperliquidFloor(Sleeve):
    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="midna_hyperliquid_momentum_floor", family="midna", cadence_s=60, capital=float(RULES["startingCash"]),
            universe=(), schedule="always", needs={"feeds": ["midna_hyperliquid"]}, venue_pref="sim:kraken_futures",
            params={"rules": RULES, "limits": {k: v for k, v in LIMITS.items() if k != "dailyLossHaltPct"},
                    "removed_gates": REMOVED, "watch": "armed", "approval": "immediate"},
            source=SOURCE, state_schema={"pos": "dict", "lastScanAt": "float|None", "cooldowns": "list",
                                         "closing": "dict"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def signal(self, view):
        st = dict(view.state or {})
        market = view.extra.get("midna_hyperliquid") or {}
        kraken = market.get("kraken") or {}
        held = {i.split(":", 2)[2]: p for i, p in view.positions.items() if i.startswith("PERP:")}
        pos = {}
        for coin, p in (st.get("pos") or {}).items():       # a recorded position whose perp is gone is closed
            sym = kraken.get(coin) or p.get("perp")
            working = any(o.get("signal_key", "").startswith(f"hl:{coin}:") and o.get("action") == "enter"
                          for o in view.extra.get("pending_orders", []))
            if (sym and sym in held) or working:
                pos[coin] = p
        # the floor's paper book drops a coin when its exit fires; the engine's exit child can end unfilled, so each
        # exit sent is remembered until its perp is flat and goes again (its key's next attempt) while none works
        entering = {coin for coin in (st.get("closing") or {})
                    if any(o.get("signal_key", "").startswith(f"hl:{coin}:") and o.get("action") == "enter"
                           for o in view.extra.get("pending_orders", []))}
        closing = {coin: c for coin, c in (st.get("closing") or {}).items()
                   if abs(float((held.get(c["perp"]) or {}).get("qty") or 0.0)) > 1e-12 or coin in entering}
        book = {"positions": pos, "lastScanAt": st.get("lastScanAt"), "cooldowns": st.get("cooldowns") or []}
        orders = step(book, view.now, market, float(view.equity))
        out = []
        for o in orders:
            sym = kraken.get(o["coin"]) or (pos.get(o["coin"]) or {}).get("perp")
            if o["action"] == "enter":
                if not sym:
                    book["positions"].pop(o["coin"], None)
                    out.append(Intent("signal", o["coin"], reason=f"{o['side']} {o['coin']} ticket: no like-for-like "
                                      f"perpetual on the sim venue (not filled)", signal_key=f"hl:{o['coin']}:unfilled"))
                    continue
                book["positions"][o["coin"]]["perp"] = sym
                out.append(Intent("enter", sym, side=o["side"], asset="perp", venue="sim:kraken_futures",
                                  qty=float(o["notional"]) / o["price"], price_hint=o["price"],
                                  signal_key=f"hl:{o['coin']}:{int(view.now)}:open",
                                  reason=f"{o['side']} {o['coin']} {o['notional']} notional; stop {o['stop']:.6g} "
                                         f"target {o['target']:.6g} ({o['stopPct'] * 100:.2f}% stop, 2R)",
                                  order=OrderSpec(window_s=600)))
            elif sym:
                p = held.get(sym)
                key = f"hl:{o['coin']}:{int(view.now)}:{o['reason']}"
                out.append(Intent("exit", sym, side=("long" if (p and float(p["qty"]) > 0) else o["side"]),
                                  asset="perp", venue="sim:kraken_futures", signal_key=key,
                                  reason=f"{o['coin']} {o['reason']} on the Hyperliquid mark", order=OrderSpec(window_s=600)))
                closing[o["coin"]] = {"perp": sym, "key": key, "reason": o["reason"]}
        sent = {i.symbol for i in out if i.kind == "exit"}
        exiting = {str(o.get("inst", "")).split(":", 2)[-1] for o in view.extra.get("pending_orders", []) or []
                   if o.get("action") == "exit"}
        for coin, c in closing.items():
            # skipped: nothing held yet, sent this pass, still working, or re-opened (its own exit closes the perp)
            q = float((held.get(c["perp"]) or {}).get("qty") or 0.0)
            if abs(q) <= 1e-12 or c["perp"] in sent or c["perp"] in exiting or coin in book["positions"]:
                continue
            out.append(Intent("exit", c["perp"], side="long" if q > 0 else "short", asset="perp",
                              venue="sim:kraken_futures", signal_key=c["key"],
                              reason=f"{coin} {c['reason']} on the Hyperliquid mark (sent again: the last exit ended "
                                     f"unfilled)", order=OrderSpec(window_s=600)))
        st.update(pos=book["positions"], lastScanAt=book["lastScanAt"], cooldowns=book["cooldowns"], closing=closing)
        self._st = st
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})
