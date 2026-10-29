"""midna_qqq_csp_ladder — Midna's QQQ put ladder (src/lib/equity/qqq-ladder.ts @ entire 43f08f96, blob 4f73c7fb:
applyQqqLadder and its helpers; options-surface.ts calendarDays / impliedVol / normCdf / yearFraction / occSymbol,
blob f4713824), ported line for line, on the listed QQQ chain of the option-marks producer
(desk/feedlib/midna_options.py, the scripts/option-marks.ts port: Cboe delayed quotes).

  book      its own $1,000,000; three contracts a layer; sales at the bid, buy-backs at the ask (per contract x 100)
  session   regular hours from 10:00 ET
  severe    spot (QQQ last, else the chain's) <= strike, ask >= 3 x the sale credit, or live put delta >= 0.35 ->
            bought back (needs today's fresh chain and the cash for it)
  7 DTE     anything with 7 days or fewer left is bought back
  roll up   8..21 DTE, not rolled before, not challenged: QQQ above the sale's spot (quote and chain within 2%), the
            put's ask <= half its credit -> buy it back and sell the band put (delta 0.05..0.08, nearest 0.065, lower
            strike on a tie) above it in the same expiration whose bid >= that ask, when the cash still secures it
  roll down 8..21 DTE, challenged (ask >= 2 x credit, delta >= 0.20, or QQQ <= strike) but not severe: buy back and
            sell the band put below the strike in the later expiration nearest 45 days (38..52) whose bid >= half
            the old credit, when the cash still secures it
  new layer once per ISO week: QQQ not down on the day and VIX not up on the day (both quoted with a previous close),
            no open put challenged, today's fresh chain (<= 20 min) whose spot is within 2% of QQQ's quote; the
            expiration nearest 45 days (38..52, a tie takes the later) not already held; the band put; the cash
            after the credit, less the strikes already secured, must secure 3 x strike x 100
  expiry    a put still open on its expiration day settles at intrinsic x 100

The QQQ-down / VIX-up layer conditions are this sleeve's own written rule (the file's header: "A new layer waits
when QQQ is down on the day, VIX is up on the day, ..."; the manifest row: "variant of the QQQ put ladder with
Midna's QQQ-not-down/VIX-not-up gates"), not the desk's shared gate (green.ts), and stay.

Removed (cutover doctrine): entriesHeld(state) — "New layers are halted" when the desk is halted or its ledger chain
broke (the desk kill switch).

Named divergences: orders are engine children (sales: DAY limit at the bid, buy-backs: DAY limit at the ask, as the
source priced its paper fills) and a working order counts as done; the 4% annual yield the source accrued on the
ladder's cash each calendar day (accrue, LADDER_YIELD) is not paid — the engine has no cash-yield capability (core
patch proposed: a per-book daily cash accrual) — so the cash the roll / layer checks read lacks the accrued yield;
an option the engine still holds at its expiry close settles by the engine's rule (delivery at the strike, booked
at the settlement close) where the source booked intrinsic x 100 in cash; the chain hand-off (option-marks.json) is
the producer feed; marks are the engine's (mid) where the source marked shorts at the ask."""
import math
from datetime import date

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as M

SOURCE = {"repo": "midna", "ref": "entire", "commit": "43f08f96fce33ee67521002e09f8bc7534cfe264",
          "path": "src/lib/equity/qqq-ladder.ts", "blob": "4f73c7fb1f6f441f7433c9976b728ac9e48ac5bd",
          "surface": {"path": "src/lib/equity/options-surface.ts", "blob": "f4713824fd1b"},
          "producer": {"path": "scripts/option-marks.ts"}}
LADDER_NAV = 1_000_000.0
LADDER_QTY = 3
LADDER_RATE = 0.04
LADDER_YIELD = 0.04
CONTRACT = 100
TARGET_DELTA = 0.065
DELTA_LO, DELTA_HI = 0.05, 0.08
DTE_LO, DTE_HI, TARGET_DTE = 38, 52, 45
MANAGE_DTE, CLOSE_DTE = 21, 7
CHALLENGED_DELTA, SEVERE_DELTA = 0.2, 0.35
DECAYED = 0.5
CHALLENGED_MULT, SEVERE_MULT = 2, 3
REPAIR_COVER = 0.5
MAX_REL_SPREAD = 1
MIN_BID = 0.05
MAX_SPOT_GAP = 0.02
MARKS_FRESH_MS = 20 * 60_000
KEEP = ("expiration", "strike", "entrySpot", "credit", "rolledUp", "entryDay", "openedAt", "id")
REMOVED = ["entriesHeld: desk halted or ledger break -> 'New layers are halted' (desk kill switch)"]


# -- options-surface.ts ----------------------------------------------------------------------------------------
def calendar_days(frm, to):
    return M.js_round((date.fromisoformat(to) - date.fromisoformat(frm)).days)


def occ_symbol(root, expiration, right, strike):
    return f"{root}{expiration[2:4]}{expiration[5:7]}{expiration[8:10]}{right}{M.js_round(strike * 1000):08d}"


def _erf(x):
    sign = -1 if x < 0 else 1
    a1, a2, a3, a4, a5, p = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429, 0.3275911
    t = 1 / (1 + p * abs(x))
    y = 1 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return sign * y


def norm_cdf(x):
    return 0.5 * (1 + _erf(x / math.sqrt(2)))


def bs_price(right, spot, strike, t, rate, vol):
    if not (spot > 0) or not (strike > 0) or not (t > 0) or not (vol > 0):
        return math.nan
    sq = math.sqrt(t)
    d1 = (math.log(spot / strike) + (rate + (vol * vol) / 2) * t) / (vol * sq)
    d2 = d1 - vol * sq
    disc = math.exp(-rate * t)
    if right == "C":
        return spot * norm_cdf(d1) - strike * disc * norm_cdf(d2)
    return strike * disc * norm_cdf(-d2) - spot * norm_cdf(-d1)


def implied_vol(right, spot, strike, t, rate, price):
    if not (price > 0) or not (t > 0) or not (spot > 0) or not (strike > 0):
        return None
    disc = math.exp(-rate * t)
    intrinsic = max(0, spot - strike * disc) if right == "C" else max(0, strike * disc - spot)
    if price <= intrinsic + 0.01:
        return None
    lo, hi = 1e-4, 5.0
    at_lo, at_hi = bs_price(right, spot, strike, t, rate, lo), bs_price(right, spot, strike, t, rate, hi)
    if not math.isfinite(at_lo) or not math.isfinite(at_hi) or price < at_lo or price > at_hi:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if bs_price(right, spot, strike, t, rate, mid) > price:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def year_fraction(session, expiration):
    days = calendar_days(session, expiration)
    return None if days <= 0 else days / 365


# -- qqq-ladder.ts -----------------------------------------------------------------------------------------------
def contract_key(right, strike):
    return f"{right}:{M.js_num(strike)}"


def ladder_expiration_window(session, expirations):
    return [e for e in expirations if DTE_LO <= calendar_days(session, e) <= DTE_HI]


def pick_ladder_expiration(session, expirations):
    best = None
    for e in ladder_expiration_window(session, expirations):
        dist = abs(calendar_days(session, e) - TARGET_DTE)
        if best is None or dist < best[1] or (dist == best[1] and e > best[0]):
            best = (e, dist)
    return best[0] if best else None


def put_delta(spot, strike, t, rate, vol):
    if not (spot > 0) or not (strike > 0) or not (t > 0) or not (vol > 0):
        return math.nan
    sq = math.sqrt(t)
    d1 = (math.log(spot / strike) + (rate + (vol * vol) / 2) * t) / (vol * sq)
    return norm_cdf(d1) - 1


def tradable(row):
    if not (row["bid"] >= MIN_BID) or not (row["ask"] > 0) or row["ask"] < row["bid"]:
        return False
    mid = (row["bid"] + row["ask"]) / 2
    return mid > 0 and (row["ask"] - row["bid"]) / mid <= MAX_REL_SPREAD


def choose_listed_put(name, session, expiration, spot, accept=lambda r: True):
    book = (name.get("expirations") or {}).get(expiration)
    t = year_fraction(session, expiration)
    if not book or t is None or not (spot > 0):
        return None
    best = None
    for strike in book["strikes"]:
        if not (strike < spot):
            continue
        row = book["contracts"].get(contract_key("P", strike))
        if not row or not tradable(row):
            continue
        mid = (row["bid"] + row["ask"]) / 2
        vol = implied_vol("P", spot, strike, t, LADDER_RATE, mid)
        if vol is None:
            continue
        delta = -put_delta(spot, strike, t, LADDER_RATE, vol)
        if not (delta >= DELTA_LO) or not (delta <= DELTA_HI):
            continue
        pick = {"strike": strike, "bid": row["bid"], "ask": row["ask"], "delta": delta}
        if not accept(pick):
            continue
        score = abs(delta - TARGET_DELTA)
        if best is None or score < best["score"] - 1e-9 or (abs(score - best["score"]) <= 1e-9 and strike < best["strike"]):
            best = dict(pick, score=score)
    return best


def row_at(name, expiration, strike):
    row = (((name or {}).get("expirations") or {}).get(expiration) or {}).get("contracts", {}).get(contract_key("P", strike))
    if not row or not M.finite(row.get("bid")) or not M.finite(row.get("ask")) or row["ask"] < row["bid"] or \
            row["bid"] < 0 or row["ask"] < 0:
        return None
    return row


def fresh_chain(name, marks, now):
    if not name or not marks or not ((name.get("spot") or 0) > 0) or name.get("day") != M.et_ymd(now):
        return False
    built = marks.get("builtAt")
    if built is None:
        return False
    return now * 1000 - built * 1000 <= MARKS_FRESH_MS and now * 1000 >= built * 1000 - 60_000


def live_delta(p, name, session):
    if not name or not ((name.get("spot") or 0) > 0):
        return None
    row = row_at(name, p["expiration"], p["strike"])
    t = year_fraction(session, p["expiration"])
    if not row or t is None:
        return None
    mid = (row["bid"] + row["ask"]) / 2
    if not (mid > 0):
        return None
    vol = implied_vol("P", name["spot"], p["strike"], t, LADDER_RATE, mid)
    if vol is None:
        return None
    d = -put_delta(name["spot"], p["strike"], t, LADDER_RATE, vol)
    return d if math.isfinite(d) else None


def close_ask(p, name):
    row = row_at(name, p["expiration"], p["strike"])
    return row["ask"] if row else None


def challenged(p, name, quote, session):
    ask = close_ask(p, name)
    if ask is not None and ask >= p["credit"] * CHALLENGED_MULT:
        return True
    d = live_delta(p, name, session)
    if d is not None and d >= CHALLENGED_DELTA:
        return True
    return bool(quote and quote["last"] > 0 and quote["last"] <= p["strike"])


def severe(p, name, quote, session):
    spot = quote["last"] if quote and quote["last"] > 0 else (name or {}).get("spot")
    if spot is not None and spot <= p["strike"]:
        return True
    ask = close_ask(p, name)
    if ask is not None and ask >= p["credit"] * SEVERE_MULT:
        return True
    d = live_delta(p, name, session)
    return d is not None and d >= SEVERE_DELTA


class Ladder:
    """the LadderAccount during one pass: cash and open positions, mutated as the source does; records orders."""

    def __init__(self, cash, positions, added_week=None, told=None):
        self.cash = cash
        self.positions = positions        # open, in book order: {occ, qty (-3), entryAvg, expiration, strike,
        self.added_week = added_week      #  entrySpot, credit, rolledUp, entryDay, id}
        self.told = dict(told or {})
        self.orders = []

    def reserved(self, except_=None):
        return M.js_sum(p["strike"] * CONTRACT * abs(p["qty"]) for p in self.positions if p is not except_)

    def room_for(self, strike, bid, except_=None, close_ask_px=None):
        closing = abs(except_["qty"]) * (close_ask_px or 0) * CONTRACT if except_ is not None else 0
        cash_after = self.cash - closing
        if cash_after < 0:
            return False
        credit = bid * CONTRACT * LADDER_QTY
        need = strike * CONTRACT * LADDER_QTY
        return cash_after + credit - self.reserved(except_) >= need - 0.01

    def finish(self, p, price, now, reason):
        qty = p["qty"]
        self.cash = M.round2(self.cash - abs(qty) * price)
        self.positions.remove(p)
        self.orders.append({"action": "buy_close", "occ": p["occ"], "qty": abs(qty), "price": price / CONTRACT,
                            "reason": reason, "id": p.get("id")})

    def open_short(self, pick, expiration, spot, today, now, rolled_up):
        credit = M.round2(pick["bid"] * CONTRACT)
        self.cash = M.round2(self.cash + credit * LADDER_QTY)
        occ = occ_symbol("QQQ", expiration, "P", pick["strike"])
        p = {"occ": occ, "qty": -LADDER_QTY, "entryAvg": credit, "expiration": expiration, "strike": pick["strike"],
             "entrySpot": spot, "credit": pick["bid"], "rolledUp": rolled_up, "entryDay": today, "openedAt": now,
             "id": f"qqq-ladder:{expiration}:{M.js_num(pick['strike'])}:{now}"}
        self.positions.append(p)
        self.orders.append({"action": "sell_open", "occ": occ, "qty": LADDER_QTY, "price": pick["bid"], "pos": p})

    def buy_back(self, p, name, marks, now, reason):
        if not fresh_chain(name, marks, now):
            return False
        row = row_at(name, p["expiration"], p["strike"])
        if not row:
            return False
        cost = M.round2(row["ask"] * CONTRACT)
        if M.round2(self.cash - abs(p["qty"]) * cost) < 0:
            return False
        self.finish(p, cost, now, reason)
        return True


def roll_up(acc, p, name, quote, today, now):
    spot = (quote or {}).get("last")
    if not (spot is not None and spot > 0) or abs(name["spot"] - spot) / spot > MAX_SPOT_GAP:
        return False
    if not (spot > p["entrySpot"]):
        return False
    row = row_at(name, p["expiration"], p["strike"])
    if not row or row["ask"] > p["credit"] * DECAYED:
        return False
    nxt = choose_listed_put(name, today, p["expiration"], name["spot"],
                            lambda pk: pk["strike"] > p["strike"] and pk["bid"] >= row["ask"])
    if not nxt or not acc.room_for(nxt["strike"], nxt["bid"], p, row["ask"]):
        return False
    acc.finish(p, M.round2(row["ask"] * CONTRACT), now, "Roll the strike up")
    acc.open_short(nxt, p["expiration"], spot, today, now, True)
    return True


def roll_down(acc, p, name, today, now):
    row = row_at(name, p["expiration"], p["strike"])
    if not row:
        return False
    exp = pick_ladder_expiration(today, [e for e in name["expirations"] if e > p["expiration"]])
    if not exp:
        return False
    nxt = choose_listed_put(name, today, exp, name["spot"],
                            lambda pk: pk["strike"] < p["strike"] and pk["bid"] >= p["credit"] * REPAIR_COVER)
    if not nxt or not acc.room_for(nxt["strike"], nxt["bid"], p, row["ask"]):
        return False
    acc.finish(p, M.round2(row["ask"] * CONTRACT), now, "Roll out and down")
    acc.open_short(nxt, exp, name["spot"], today, now, False)
    return True


def apply_ladder(acc, now, quotes, marks):
    """applyQqqLadder without the yield accrual (named divergence) and the halt (removed). Mutates acc."""
    name = ((marks or {}).get("names") or {}).get("QQQ")
    today = M.et_ymd(now)
    if not (M.phase_at(now) == "rth" and M.et_parts(now)["minutes"] >= 10 * 60):
        return
    qqq = quotes.get("QQQ")
    spot = (qqq or {}).get("last")
    if spot is not None and spot > 0:                      # settle
        for p in list(acc.positions):
            if calendar_days(today, p["expiration"]) > 0:
                continue
            acc.finish(p, M.round2(max(0, p["strike"] - spot) * CONTRACT), now, "Expiration")
            acc.orders[-1]["action"] = "settle"
    for p in list(acc.positions):
        if p in acc.positions and severe(p, name, qqq, today):
            if not acc.buy_back(p, name, marks, now, "Closed the challenged put"):
                _note(acc, f"out:{p['expiration']}:{M.js_num(p['strike'])}", today)
    for p in list(acc.positions):
        if p not in acc.positions:
            continue
        if calendar_days(today, p["expiration"]) > CLOSE_DTE:
            continue
        if not acc.buy_back(p, name, marks, now, "Bought back with 7 days left"):
            _note(acc, f"out:{p['expiration']}:{M.js_num(p['strike'])}", today)
    if fresh_chain(name, marks, now):
        for p in list(acc.positions):
            if p not in acc.positions or p["rolledUp"]:
                continue
            dte = calendar_days(today, p["expiration"])
            if dte > MANAGE_DTE or dte <= CLOSE_DTE:
                continue
            if challenged(p, name, qqq, today):
                continue
            roll_up(acc, p, name, qqq, today, now)
        for p in list(acc.positions):
            if p not in acc.positions:
                continue
            dte = calendar_days(today, p["expiration"])
            if dte > MANAGE_DTE or dte <= CLOSE_DTE:
                continue
            if not challenged(p, name, qqq, today) or severe(p, name, qqq, today):
                continue
            roll_down(acc, p, name, today, now)
    add_week(acc, name, marks, quotes, now)


def _note(acc, key, day):
    acc.told[key] = day


def add_week(acc, name, marks, quotes, now):
    today = M.et_ymd(now)
    week = M.iso_week(today)
    if acc.added_week == week:
        return "already"
    qqq, vix = quotes.get("QQQ"), quotes.get("^VIX")
    if not qqq or not (qqq["last"] > 0) or not ((qqq.get("previousClose") or 0) > 0) or not vix or \
            not (vix["last"] > 0) or not ((vix.get("previousClose") or 0) > 0):
        return "waiting"
    if qqq["last"] < qqq["previousClose"]:
        _note(acc, "down", today)
        return "down"
    if vix["last"] > vix["previousClose"]:
        _note(acc, "vix", today)
        return "vix"
    if any(challenged(p, name, qqq, today) for p in acc.positions):
        _note(acc, "challenged", today)
        return "challenged"
    if not fresh_chain(name, marks, now):
        return "chain"
    if abs(name["spot"] - qqq["last"]) / qqq["last"] > MAX_SPOT_GAP:
        return "gap"
    held = {p["expiration"] for p in acc.positions}
    exp = pick_ladder_expiration(today, [e for e in name["expirations"] if e not in held])
    if not exp:
        _note(acc, "expiry", today)
        return "expiry"
    pick = choose_listed_put(name, today, exp, name["spot"])
    if not pick:
        _note(acc, "strike", today)
        return "strike"
    if not acc.room_for(pick["strike"], pick["bid"]):
        _note(acc, "cash", today)
        return "cash"
    acc.open_short(pick, exp, qqq["last"], today, now, False)
    acc.added_week = week
    return "sold"


class QqqCspLadder(Sleeve):
    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="midna_qqq_csp_ladder", family="midna", cadence_s=300, capital=LADDER_NAV,
            universe=("QQQ", "^VIX"), schedule="rth",
            needs={"quotes": {"source": "equity", "symbols": ["QQQ", "^VIX"]}, "feeds": ["midna_option_marks"]},
            params={"qty": LADDER_QTY, "rate": LADDER_RATE, "delta_band": [DELTA_LO, DELTA_HI], "dte": [DTE_LO, DTE_HI],
                    "manage_dte": MANAGE_DTE, "close_dte": CLOSE_DTE, "removed_gates": REMOVED,
                    "unpaid_cash_yield": LADDER_YIELD},
            source=SOURCE, state_schema={"addedWeek": "str|None", "told": "dict", "pos": "dict"})
        self._st = None

    def signal(self, view):
        st = dict(view.state or {})
        marks = view.extra.get("midna_option_marks")
        rec = dict(st.get("pos") or {})
        positions, cash = option_book(view, rec)
        acc = Ladder(cash, positions, st.get("addedWeek"), st.get("told"))
        quotes = {s: M.mq(view.quotes.get(s)) for s in ("QQQ", "^VIX")}
        apply_ladder(acc, view.now, {k: v for k, v in quotes.items() if v}, marks)
        close = M.et_to_epoch(view.session, 0, 0) + M.session_close_minutes(view.session) * 60
        window = max(60.0, close - view.now)
        out = []
        for o in acc.orders:
            if o["action"] == "sell_open":
                p = o["pos"]
                out.append(Intent("enter", o["occ"], side="short", asset="option", qty=float(o["qty"]),
                                  price_hint=o["price"], signal_key=f"ladder:{p['id']}",
                                  reason=f"sell {LADDER_QTY} QQQ {M.js_num(p['strike'])} puts {p['expiration']}",
                                  order=OrderSpec(type="limit", limit_price=round(o["price"], 2), tif="day",
                                                  window_s=window),
                                  meta={"position_meta": {k: p[k] for k in KEEP}}))
            elif o["action"] == "buy_close":
                out.append(Intent("exit", o["occ"], side="short", asset="option", price_hint=o["price"],
                                  signal_key=f"ladder:{o.get('id') or o['occ']}:close:{view.session}", reason=o["reason"],
                                  order=OrderSpec(type="limit", limit_price=round(o["price"], 2), tif="day",
                                                  window_s=window)))
        keep = {}
        for p in acc.positions:
            keep[p["occ"]] = {k: p.get(k) for k in KEEP}
        for inst in view.positions:
            occ = inst[4:] if inst.startswith("OPT:") else None
            if occ and occ not in keep and occ in rec:
                keep[occ] = rec[occ]
        st.update(addedWeek=acc.added_week, told=acc.told, pos=keep)
        self._st = st
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})


def option_book(view, rec):
    """the ladder's open shorts as the source's instant-fill book would hold them: the engine's OPT positions plus
    working sales (at their limit), less working buy-backs; cash moved the same way."""
    cash = float(view.cash)
    held = {}
    for inst, p in view.positions.items():
        if inst.startswith("OPT:") and float(p["qty"]) < 0:
            held[inst[4:]] = {"qty": float(p["qty"]), "meta": (p.get("meta") or {}).get("position_meta") or {}}
    for ch in view.extra.get("pending_orders", []) or []:
        inst = str(ch.get("inst", ""))
        if not inst.startswith("OPT:"):
            continue
        occ = inst[4:]
        rem = float(ch.get("vqty") or 0.0) - float(ch.get("filled_v") or 0.0)
        if rem <= 1e-9:
            continue
        ref = float(ch.get("ref") or 0.0)
        if ch.get("side") == "sell":
            cur = held.setdefault(occ, {"qty": 0.0, "meta": {}})
            cur["qty"] -= rem
            cash += rem * ref * CONTRACT
        else:
            cur = held.get(occ)
            if cur is None:
                continue
            cur["qty"] += rem
            cash -= rem * ref * CONTRACT
            if cur["qty"] >= -1e-9:
                held.pop(occ)
    out = []
    for occ, h in held.items():
        r = rec.get(occ) or h["meta"] or {}
        if not r.get("expiration"):
            continue
        out.append({"occ": occ, "qty": h["qty"], "entryAvg": M.round2((r.get("credit") or 0) * CONTRACT),
                    "expiration": r["expiration"], "strike": float(r["strike"]), "entrySpot": float(r["entrySpot"]),
                    "credit": float(r["credit"]), "rolledUp": bool(r.get("rolledUp")), "entryDay": r.get("entryDay"),
                    "openedAt": float(r.get("openedAt") or 0), "id": r.get("id") or occ})
    out.sort(key=lambda p: (p["openedAt"], p["id"]))           # the source's insertion (opening) order
    return out, cash
