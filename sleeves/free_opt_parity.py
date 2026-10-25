"""FREE_OPT_PARITY — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from aurelia_free_options.py contracts(): shape parity_model,
execution model_test — "No economic order." Indicative conversion is
recorded and is not an economic order (MODEL_TEST_ONLY on the old desk).
parity_status() returns the old desk's row (retained as a status helper).

UNFENCE-119 (owner ruling 2026-10-24 10:38 ET): the Decision #119
monitor-only fence is REVERSED for this sleeve in muse-desk-v2 —
CONFIG.monitor_only=False and the adapter routes signal() intents
to the dispatcher instead of journaling monitor_status.

DESIGNED-ORDER-LOGIC (DESIGNED-ORDER-LOGIC.md §4, owner ruling
2026-10-24 11:41 ET "Fix that defect"): no parity order logic existed
in any source to port, so the logic below was AUTHORED to the locked
design. These constants were authored under the owner's 2026-10-24
'Fix that defect' ruling: ENTRY_EDGE = 0.30 (per share), EXIT_EDGE =
0.05, QTY = 1 box. The designed economic expression of the parity_model
is a BOX-SPREAD parity trade on SPY options — chosen and recorded in
the design doc because a conversion/reversal's 100-share stock leg
(~$68k) cannot fit this sleeve's $10,000 slice, while a box spread is
a pure parity instrument (locked payout = strike width at expiry)
whose max loss is the debit, capped by width.

Design: inputs arrive via extra["parity_quotes"] (SPY chain quotes
[{symbol (OCC), expiration, strike, right, bid, ask}] produced at warm
time by runtime/options_warm.py and injected by the adapter) and
extra["parity_spot"] (newest SPY close from the bar cache). Group
quotes by (expiry, strike), keeping only strikes with BOTH a call and
a put with valid non-crossed bid/ask; expiries >= 7 DTE only. For
strike pairs K1 < K2 (width = K2-K1 <= 5): long-box executable debit
per share = C(K1).ask - P(K1).bid - C(K2).bid + P(K2).ask, long edge =
width - debit; short-box executable credit per share = C(K1).bid -
P(K1).ask - C(K2).ask + P(K2).bid, short edge = credit - width.
FLAT: take the pair with the largest edge; long edge >= 0.30 -> ONE
entry Intent carrying 4 legs (buy C(K1), sell P(K1), sell C(K2), buy
P(K2), each qty 1, package_id set, limit at the executable debit);
short edge >= 0.30 -> the mirror package at the executable credit.
OPEN (package reconstructed from sleeve_state positions): exit Intent
unwinding all 4 legs when the same box's executable unwind value >=
width - 0.05 per share OR on the expiry date; otherwise hold. One open
position at a time; fail closed on missing, stale, crossed, or
malformed inputs (any missing leg quote included); never raise.
parity_status() is retained as a status helper.

VIRTUAL BOOK MAPPING: sizing goes through the existing slice
machinery (config slice capital_usd = 10000 for this sleeve); the
dispatcher checks buying power locally as for every sleeve.
"""
import hashlib
import json
import math
import re
from datetime import date, datetime, timezone

from desk3.contract import BaseSleeve, Intent, SleeveConfig

UNDERLYING = "SPY"
ENTRY_EDGE = 0.30
EXIT_EDGE = 0.05
QTY = 1
MAX_WIDTH = 5.0
MIN_DTE = 7

CONFIG = SleeveConfig(
    sleeve_id="free_opt_parity", cadence_s=300, universe=(), monitor_only=False,
    state_schema={}, risk_pct=None)

_OCC = re.compile(r"^([A-Z]{1,6})(\d{6})([CP])(\d{8})$")


def _parse_occ(symbol):
    m = _OCC.match(str(symbol or ""))
    if not m:
        return None
    yy, mm, dd = int(m.group(2)[:2]), int(m.group(2)[2:4]), int(m.group(2)[4:6])
    try:
        exp = date(2000 + yy, mm, dd).isoformat()
    except ValueError:
        return None
    return {"root": m.group(1), "expiration": exp,
            "right": "call" if m.group(3) == "C" else "put",
            "strike": int(m.group(4)) / 1000.0}


def _f(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _now_dt(now):
    if isinstance(now, datetime):
        return now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromtimestamp(float(now), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _valid(bid, ask):
    return bid is not None and ask is not None and bid > 0 and ask >= bid


def _normalize_quotes(quotes):
    """Quote rows (list shape from the producer, or {OCC: row} dict
    shape) -> {(expiry, strike): {"call": row, "put": row}} keeping
    only strikes with BOTH legs valid and non-crossed. Rows carry
    {symbol, expiration, strike, right, bid, ask}; OCC parsing fills
    any missing field. Malformed rows are dropped, never raised."""
    rows = []
    if isinstance(quotes, dict):
        for occ, row in quotes.items():
            if isinstance(row, dict):
                rows.append({**row, "symbol": row.get("symbol") or occ})
    elif isinstance(quotes, (list, tuple)):
        rows = [r for r in quotes if isinstance(r, dict)]
    grouped = {}
    for r in rows:
        parsed = _parse_occ(r.get("symbol"))
        right = str(r.get("right") or r.get("type") or "").lower()
        if right in ("c", "call"):
            right = "call"
        elif right in ("p", "put"):
            right = "put"
        elif parsed:
            right = parsed["right"]
        else:
            continue
        exp = str(r.get("expiration") or r.get("expiry") or "")[:10]
        if not exp and parsed:
            exp = parsed["expiration"]
        try:
            date.fromisoformat(exp)
        except (TypeError, ValueError):
            continue
        strike = _f(r.get("strike"))
        if strike is None and parsed:
            strike = parsed["strike"]
        bid, ask = _f(r.get("bid")), _f(r.get("ask"))
        if not exp or strike is None or not _valid(bid, ask):
            continue
        slot = grouped.setdefault((exp, float(strike)), {})
        slot[right] = {"symbol": r.get("symbol"), "expiration": exp,
                       "strike": float(strike), "right": right,
                       "bid": bid, "ask": ask}
    return {k: v for k, v in grouped.items() if "call" in v and "put" in v}


def _box_values(slot1, slot2):
    """(long_debit, short_credit) per share for strikes K1 < K2."""
    c1, p1, c2, p2 = slot1["call"], slot1["put"], slot2["call"], slot2["put"]
    long_debit = c1["ask"] - p1["bid"] - c2["bid"] + p2["ask"]
    short_credit = c1["bid"] - p1["ask"] - c2["ask"] + p2["bid"]
    return long_debit, short_credit


def _event_id(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _package_id(expiry, k1, k2, direction):
    return "spy-box-%s-%g-%g-%s" % (expiry, k1, k2, direction)


def parity_status():
    return {"id": "FREE_OPT_PARITY_V1", "preserves": "OPT_PARITY_MONITOR",
            "status": "ARMED_BOX_SPREAD", "broker_order": True,
            "economic_forward": True,
            "reason": "Designed box-spread parity trade on SPY options (DESIGNED-ORDER-LOGIC.md \u00a74): long/short box (K1<K2, width <= 5, expiries >= 7 DTE) when the executable edge >= 0.30/share; exit when the unwind value >= width - 0.05/share or on expiry. Authored under the owner's 2026-10-24 'Fix that defect' ruling; the pre-design MODEL_TEST_ONLY contract placed no economic order."}


def parity_decision(quotes, spot, now, position=None):
    """Designed parity decision (family style of
    sleeves/free_kraken_ada_breakdown.py): decision dict with
    status/reason. `position` (an open box reconstructed by signal())
    switches to the exit evaluation for that same box."""
    n = _now_dt(now)
    if n is None:
        return {"status": "BLOCKED_INPUT", "reason": "Unusable clock."}
    today = n.date()
    grouped = _normalize_quotes(quotes)
    grouped = {k: v for k, v in grouped.items()
               if (date.fromisoformat(k[0]) - today).days >= MIN_DTE
               or (position and k[0] == position.get("expiry"))}
    spot_f = _f(spot)
    if position:
        expiry, k1, k2 = position["expiry"], float(position["k1"]), float(position["k2"])
        width = k2 - k1
        base = {"expiry": expiry, "k1": k1, "k2": k2, "width": width,
                "direction": position["direction"],
                "event_id": _event_id({"expiry": expiry, "k1": k1, "k2": k2,
                                       "direction": position["direction"]}),
                "decision_at": n.isoformat()}
        try:
            expired = today >= date.fromisoformat(expiry)
        except ValueError:
            expired = False
        s1, s2 = grouped.get((expiry, k1)), grouped.get((expiry, k2))
        if s1 is None or s2 is None:
            if expired:
                return {**base, "status": "exit_ready", "priceable": False,
                        "reason": "Expiry date reached; unwind the box (leg quotes missing, market unwind)."}
            return {**base, "status": "BLOCKED_INPUT", "priceable": False,
                    "reason": "Open box leg quote missing; fail closed, hold."}
        long_debit, short_credit = _box_values(s1, s2)
        unwind = short_credit if position["direction"] == "long" else width - long_debit
        base = {**base, "priceable": True, "unwind_value": unwind,
                "long_debit": long_debit, "short_credit": short_credit,
                "slots": (s1, s2)}
        if expired:
            return {**base, "status": "exit_ready",
                    "reason": "Expiry date reached; unwind the box."}
        if unwind >= width - EXIT_EDGE:
            return {**base, "status": "exit_ready",
                    "reason": "Unwind value %.2f >= width %.2f - %.2f; locked value nearly fully capturable." % (unwind, width, EXIT_EDGE)}
        return {**base, "status": "QUALIFIED/AWAITING SIGNAL",
                "reason": "Box open; unwind value %.2f < width %.2f - %.2f and expiry %s not reached." % (unwind, width, EXIT_EDGE, expiry)}
    # FLAT: scan every admissible pair, take the largest edge.
    if not grouped:
        return {"status": "BLOCKED_INPUT",
                "reason": "No SPY strike carries both a valid call and a put quote at an expiry >= %d DTE." % MIN_DTE,
                "decision_at": n.isoformat()}
    if spot_f is None or spot_f <= 0:
        return {"status": "BLOCKED_INPUT",
                "reason": "SPY spot missing or invalid; fail closed.",
                "decision_at": n.isoformat()}
    best = None
    expiries = sorted({e for e, _ in grouped})
    for expiry in expiries:
        strikes = sorted(k for e, k in grouped if e == expiry)
        for i, k1 in enumerate(strikes):
            for k2 in strikes[i + 1:]:
                width = k2 - k1
                if width <= 0 or width > MAX_WIDTH + 1e-9:
                    continue
                long_debit, short_credit = _box_values(grouped[(expiry, k1)], grouped[(expiry, k2)])
                for direction, edge, price in (
                        ("long", width - long_debit, long_debit),
                        ("short", short_credit - width, short_credit)):
                    cand = {"expiry": expiry, "k1": k1, "k2": k2, "width": width,
                            "direction": direction, "edge": edge, "price": price,
                            "long_debit": long_debit, "short_credit": short_credit,
                            "slots": (grouped[(expiry, k1)], grouped[(expiry, k2)])}
                    if best is None or edge > best["edge"]:
                        best = cand
    if best is None:
        return {"status": "BLOCKED_INPUT",
                "reason": "No strike pair within width <= %g." % MAX_WIDTH,
                "decision_at": n.isoformat()}
    best = {**best, "spot": spot_f,
            "event_id": _event_id({"expiry": best["expiry"], "k1": best["k1"],
                                   "k2": best["k2"], "direction": best["direction"],
                                   "edge": round(best["edge"], 6)}),
            "decision_at": n.isoformat()}
    if best["edge"] >= ENTRY_EDGE:
        return {**best, "status": "entry_ready",
                "reason": "%s box edge %.2f/share >= %.2f (width %.2f, executable price %.2f)." % (
                    best["direction"], best["edge"], ENTRY_EDGE, best["width"], best["price"])}
    return {**best, "status": "QUALIFIED/AWAITING SIGNAL",
            "reason": "Best box edge %.2f/share inside +/-%.2f; no trade." % (best["edge"], ENTRY_EDGE)}


def _qty_map(extra, slice_state):
    """{OCC: qty} + {OCC: opened_at} from every served state shape
    (build_extra nested/flat sleeve_state, raw position lists, and the
    slice_state argument in dict or list form)."""
    qty, opened = {}, {}

    def take(sym, q, when=None):
        qf = _f(q)
        if qf is None or qf == 0 or not _parse_occ(sym):
            return
        qty[sym] = qf
        if when:
            opened[sym] = when

    def walk_map(m):
        if not isinstance(m, dict):
            return
        for sym, val in m.items():
            if isinstance(val, dict) and isinstance(val.get("position"), dict):
                val = val["position"]
            if isinstance(val, dict):
                take(sym, val.get("qty"), val.get("opened_at") or val.get("entry_due_at"))
            elif isinstance(val, (int, float)):
                take(sym, val)

    if isinstance(extra, dict):
        walk_map(extra.get("sleeve_state"))
        walk_map(extra.get("sleeve_state_flat"))
        for p in extra.get("positions") or []:
            if isinstance(p, dict):
                take(p.get("symbol"), p.get("qty"), p.get("opened_at"))
    if isinstance(slice_state, dict):
        walk_map(slice_state)
    elif isinstance(slice_state, (list, tuple)):
        for p in slice_state:
            if isinstance(p, dict):
                take(p.get("symbol"), p.get("qty"), p.get("opened_at"))
    return qty, opened


def _open_box(extra, slice_state):
    """Reconstruct the one open box from held OCC positions, or None.
    Long box at K1<K2: +C(K1), -P(K1), -C(K2), +P(K2); short = mirror."""
    qty, opened = _qty_map(extra, slice_state)
    by_expiry = {}
    for sym, q in qty.items():
        p = _parse_occ(sym)
        by_expiry.setdefault(p["expiration"], {})[(p["right"], p["strike"])] = (sym, q)
    for expiry in sorted(by_expiry):
        legs = by_expiry[expiry]
        strikes = sorted({k for _, k in legs})
        for i, k1 in enumerate(strikes):
            for k2 in strikes[i + 1:]:
                keys = [("call", k1), ("put", k1), ("call", k2), ("put", k2)]
                if any(k not in legs for k in keys):
                    continue
                qs = [legs[k][1] for k in keys]
                mag = abs(qs[0])
                if mag == 0 or any(abs(q) != mag for q in qs):
                    continue
                signs = [1 if q > 0 else -1 for q in qs]
                if signs == [1, -1, -1, 1]:
                    direction = "long"
                elif signs == [-1, 1, 1, -1]:
                    direction = "short"
                else:
                    continue
                return {"direction": direction, "expiry": expiry, "k1": k1, "k2": k2,
                        "qty": mag,
                        "symbols": {"C1": legs[keys[0]][0], "P1": legs[keys[1]][0],
                                    "C2": legs[keys[2]][0], "P2": legs[keys[3]][0]},
                        "opened_at": min([opened[s] for s in
                                          [legs[k][0] for k in keys] if s in opened] or [None])}
    return None


def _legs(symbols, prices, direction, kind):
    """The 4 package legs. prices: {key: executable price or None}
    keyed C1/P1/C2/P2 for the side each leg trades at."""
    if kind == "enter":
        table = {"long": [("C1", "buy", "buy_to_open"), ("P1", "sell", "sell_to_open"),
                          ("C2", "sell", "sell_to_open"), ("P2", "buy", "buy_to_open")],
                 "short": [("C1", "sell", "sell_to_open"), ("P1", "buy", "buy_to_open"),
                           ("C2", "buy", "buy_to_open"), ("P2", "sell", "sell_to_open")]}[direction]
    else:
        table = {"long": [("C1", "sell", "sell_to_close"), ("P1", "buy", "buy_to_close"),
                          ("C2", "buy", "buy_to_close"), ("P2", "sell", "sell_to_close")],
                 "short": [("C1", "buy", "buy_to_close"), ("P1", "sell", "sell_to_close"),
                           ("C2", "sell", "sell_to_close"), ("P2", "buy", "buy_to_close")]}[direction]
    legs = []
    for key, side, pi in table:
        leg = {"symbol": symbols[key], "side": side, "position_intent": pi, "qty": QTY}
        px = prices.get(key)
        if px is not None and px > 0:
            leg["limit_price"] = round(float(px), 2)
        legs.append(leg)
    return tuple(legs)


def _slot_symbols_prices(slots, direction, kind):
    s1, s2 = slots
    rows = {"C1": s1["call"], "P1": s1["put"], "C2": s2["call"], "P2": s2["put"]}
    symbols = {k: r["symbol"] for k, r in rows.items()}
    if kind == "enter":
        px = {"long": {"C1": rows["C1"]["ask"], "P1": rows["P1"]["bid"],
                       "C2": rows["C2"]["bid"], "P2": rows["P2"]["ask"]},
              "short": {"C1": rows["C1"]["bid"], "P1": rows["P1"]["ask"],
                        "C2": rows["C2"]["ask"], "P2": rows["P2"]["bid"]}}[direction]
    else:
        px = {"long": {"C1": rows["C1"]["bid"], "P1": rows["P1"]["ask"],
                       "C2": rows["C2"]["ask"], "P2": rows["P2"]["bid"]},
              "short": {"C1": rows["C1"]["ask"], "P1": rows["P1"]["bid"],
                        "C2": rows["C2"]["bid"], "P2": rows["P2"]["ask"]}}[direction]
    return symbols, px


class FreeOptParity(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        try:
            return self._signal(bars, slice_state, context)
        except Exception:
            return []  # fail closed, never raise

    def _signal(self, bars, slice_state, context):
        extra = context.extra or {}
        now = _now_dt(context.now)
        if now is None:
            return []
        quotes = extra.get("parity_quotes")
        if quotes is None and isinstance(extra.get("quotes"), list):
            quotes = extra.get("quotes")
        spot = extra.get("parity_spot", extra.get("spot"))
        position = _open_box(extra, slice_state)
        if position is not None:
            d = parity_decision(quotes, spot, now, position=position)
            if d.get("status") != "exit_ready":
                return []
            if d.get("priceable"):
                symbols, prices = _slot_symbols_prices(d["slots"], position["direction"], "exit")
                pkg_price = d["unwind_value"] if position["direction"] == "long" \
                    else d["long_debit"]
            else:
                symbols, prices = position["symbols"], {}
                pkg_price = None
            qty = position["qty"]
            qty_hint = int(qty) if float(qty) == int(float(qty)) else None
            if qty_hint is None:
                return []
            return [Intent(
                "exit", UNDERLYING, qty_hint=qty_hint,
                limit_price=round(float(pkg_price), 2) if pkg_price and pkg_price > 0 else None,
                price_hint=round(float(spot), 2) if _f(spot) else None,
                legs=_legs(symbols, prices, position["direction"], "exit"),
                package_id=_package_id(position["expiry"], position["k1"],
                                       position["k2"], position["direction"]),
                reason="free_opt_parity EXIT %s box SPY exp=%s K1=%g K2=%g width=%.2f %s event=%s" % (
                    position["direction"], position["expiry"], position["k1"],
                    position["k2"], position["k2"] - position["k1"],
                    d["reason"], d["event_id"]))]
        d = parity_decision(quotes, spot, now)
        if d.get("status") != "entry_ready":
            return []
        symbols, prices = _slot_symbols_prices(d["slots"], d["direction"], "enter")
        return [Intent(
            "enter", UNDERLYING, qty_hint=QTY,
            side="buy" if d["direction"] == "long" else "sell",
            limit_price=round(float(d["price"]), 2) if d["price"] and d["price"] > 0 else None,
            price_hint=round(float(spot), 2) if _f(spot) else None,
            legs=_legs(symbols, prices, d["direction"], "enter"),
            package_id=_package_id(d["expiry"], d["k1"], d["k2"], d["direction"]),
            reason="free_opt_parity %s box SPY exp=%s K1=%g K2=%g width=%.2f %s=%.2f edge=%.2f event=%s" % (
                d["direction"].upper(), d["expiry"], d["k1"], d["k2"], d["width"],
                "debit" if d["direction"] == "long" else "credit",
                d["price"], d["edge"], d["event_id"]))]


def signal(bars, slice_state, context):
    return FreeOptParity().signal(bars, slice_state, context)
