"""LEAPS Momentum — lean-desk port (Wave B).

master-desk: the old desk's leaps_momentum.py restored on the engine. The momentum sleeve's book carried in
deep in-the-money LEAPS calls instead of stock, with a monthly call sold against each (the poor man's covered
call).

  signal ... the momentum sleeve's book on this desk (femto_momentum's holdings, in the order they filled) and
             the time of its last pass (the old read momentum_state.json "book" / "last_rank_date"): an empty
             or missing book = no entries and no rotation exits; a book whose last pass is more than 7 days old
             (or never ran) = stale: no entries, and every held LEAPS counts as rotated out.
  entry .... each book name in book order while fewer than 8 LEAPS are held, closing or in flight: the nearest
             call expiry >= 365 DTE, the strike nearest 0.80 x spot (the 75-delta proxy); its bid > 0, ask > 0
             and (ask - bid) / mid <= 5%; contracts = the momentum shares // 100, at least 1 (100 shares when
             the book carries no count), cut so the premium is <= 5% of equity; bought at the ask.
  exits .... (never gated) in the old order: rotated out of the book; <= 60 DTE (the floor); the mid at or below
             70% of the fill premium (the -30% stop). The LEAPS sells at its mid (at the bid on the stop) and
             its covered call is bought back at its mid, as one package; no order at all while the call has no
             mid. A name still in the book is bought again in the same pass (the old re-entered at once: a
             60-DTE exit rolls the LEAPS out a year).
  pmcc ..... a held LEAPS with no covered call sells one: the nearest 25-38 DTE call expiry, the first strike at
             or above max(spot x (1 + 0.67 x the 30-day realized vol x sqrt(30/365)), (LEAPS strike + its fill
             premium) x 1.02); bid > 0, ask >= bid, (ask - bid) / mid <= 5%; sold at the bid, one per LEAPS
             contract. The call is bought back at its mid at <= 21 DTE or when the stock trades within 3% of its
             strike (the roll); the next call is sold once the buy-back has filled. A call left without its
             LEAPS is bought back at the ask.

Gone under the cutover doctrine: the risk gate (kill switch), Decision #75 chart-gate staging, the 150% desk
cap, the cross-sleeve overlap check, the desk earnings blackout (earnings within 3 days, or a name missing from
the calendar, blocked entries; the SPEC has no earnings rule). Named divergences: the book and its clock are
femto_momentum's on this desk; sized on the sleeve's own book equity (the old read the account's); the spot is
the live quote (the old read the latest SIP bar); the 8 slots count LEAPS held, closing or in flight (the old's
count also took in-flight covered-call sales and buy-backs, which are not LEAPS); the LEAPS and its covered call
close as one package at the old's leg prices (the old sent the call's buy-back, then the LEAPS sale); a LEAPS
whose exit is due but has no bid buys its calls back and sells on a later pass, and meanwhile neither rolls nor
sells a call (the old could sell a fresh call against it, or buy a call back twice); a LEAPS whose call is
already being bought back sells after that buy-back (the old re-sent the buy-back and sold at once); hourly passes at :37 in the session (the old
cron ran mirror -> pmcc -> reconcile hourly around the clock), so a covered call is sold on the pass after its
LEAPS fills; fills, partial fills and dead orders are the OMS's (the old's promote_fills / reconcile).

Inputs via context.extra:
  "momentum"      {"book": {SYM: {"qty": shares}} in fill order, "ran_at": epoch of its last pass | None} | None
  "legs"          the sleeve's option positions {OCC: {"qty", "avg", "opened_at", "meta"}} (meta = position_meta)
  "pending"       the sleeve's working orders, one row per contract [{"action", "occ", "key"}]
  "leaps_chains"  {SYM: call rows >= 365 DTE {"symbol","strike","expiration","bid","ask"}} (fetched on demand)
  "pmcc_chains"   {SYM: call rows 25-38 DTE}
  "option_quotes" {OCC: {"bid","ask"}} — the held contracts
  "quotes"        {SYM: {"bid","ask","last"}} — spots
Bars (arg): daily bars (the spot when no quote; the 30-day realized vol)."""
import math
from datetime import date, datetime, timezone

from zoneinfo import ZoneInfo

from .compat import BaseSleeve, Intent, SleeveConfig

_ET = ZoneInfo("America/New_York")

MIN_DTE = 365
LEAPS_DTE_FLOOR = 60
LEAPS_STOP_FRAC = 0.30
PMCC_SHORT_DELTA = 0.25
PMCC_DTE_MIN, PMCC_DTE_MAX = 25, 38
PMCC_ROLL_DTE = 21
PMCC_TEST_FRAC = 0.03
SPREAD_GATE_FRAC = 0.05
MAX_POSITIONS = 8
LEAPS_NOTIONAL_CAP = 0.05
MOMENTUM_BOOK_MAX_AGE_DAYS = 7
LEAPS_STRIKE_FRAC = 0.80   # deep-ITM ~0.75-0.85 delta proxy

CONFIG = SleeveConfig(
    sleeve_id="leaps_momentum", cadence_s=1800, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=LEAPS_NOTIONAL_CAP)


def _parse_date(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def momentum_book(feed, now):
    """the old read_momentum_book: None when the book is missing or empty (no entries, no rotation exits);
    {} when its last pass is more than 7 days old or unknown (no entries; every LEAPS counts as rotated out);
    else {SYM: {"qty": shares}} in the book's order."""
    book = (feed or {}).get("book") or {}
    if not isinstance(book, dict) or not book:
        return None
    ran = (feed or {}).get("ran_at")
    if ran is None:
        return {}
    ran_d = datetime.fromtimestamp(float(ran), tz=timezone.utc).astimezone(_ET).date()
    if (datetime.fromtimestamp(float(now), tz=timezone.utc).date() - ran_d).days > MOMENTUM_BOOK_MAX_AGE_DAYS:
        return {}
    return {str(k).upper(): v for k, v in book.items() if isinstance(v, dict)}


def find_leaps_contract(chain, quotes, stock_price, session_iso, min_dte=MIN_DTE):
    """the old find_leaps_contract: the nearest expiry >= min_dte; the strike nearest 0.80 x spot (the first of
    equals); its quote needs bid > 0, ask > 0 and (ask - bid) / mid <= 5%. {"occ","ask","bid","strike",
    "expiry"} or None."""
    ref = _parse_date(session_iso)
    if ref is None or not stock_price:
        return None
    by_exp = {}
    for c in chain or []:
        exp = str(c.get("expiration") or "")[:10]
        d = _parse_date(exp)
        if d is None or (d - ref).days < min_dte:
            continue
        by_exp.setdefault(exp, []).append(c)
    if not by_exp:
        return None
    expiry = sorted(by_exp)[0]
    target = stock_price * LEAPS_STRIKE_FRAC
    best, best_d = None, 1e9
    for c in by_exp[expiry]:
        try:
            s = float(c.get("strike", 0))
        except (TypeError, ValueError):
            continue
        if abs(s - target) < best_d:
            best_d, best = abs(s - target), c
    if not best:
        return None
    q = (quotes or {}).get(best["symbol"])
    try:
        bid, ask = float((q or {}).get("bid") or 0), float((q or {}).get("ask") or 0)
    except (TypeError, ValueError):
        return None
    if bid <= 0 or ask <= 0 or (ask - bid) / ((ask + bid) / 2) > SPREAD_GATE_FRAC:
        return None
    return {"occ": best["symbol"], "ask": ask, "bid": bid, "strike": float(best.get("strike", 0)),
            "expiry": expiry}


def size_leaps_contracts(mom_qty, ask, equity):
    """Mirror momentum's share count; 1 contract per 100 shares, capped so premium <= 5% of equity. 0 = skip.
    Verbatim."""
    contracts = max(1, int(mom_qty) // 100)
    if equity and equity > 0 and ask and ask > 0:
        cap_n = int((equity * LEAPS_NOTIONAL_CAP) / (ask * 100))
        contracts = min(contracts, max(0, cap_n))
    return max(0, contracts)


def leaps_exit_due(sym, pos, mom_book, dte, mid):
    """Verbatim old order: rotation out, 60-DTE floor, -30% stop on the mid."""
    if mom_book is not None and sym not in mom_book:
        return "momentum_rotation_out"
    if dte is not None and dte <= LEAPS_DTE_FLOOR:
        return "dte_floor_60"
    entry = pos.get("entry_premium") or 0
    if mid and mid > 0 and entry > 0 and mid <= entry * (1 - LEAPS_STOP_FRAC):
        return "stop_minus30pct"
    return None


def realized_vol_30d(closes):
    """the old _realized_vol_30d on the last 31 daily closes (annualized, population variance)."""
    closes = [float(c) for c in closes[-31:]]
    if len(closes) < 21:
        return None
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
    if len(rets) < 20:
        return None
    m = sum(rets) / len(rets)
    var = sum((r - m) ** 2 for r in rets) / len(rets)
    return math.sqrt(var) * math.sqrt(252)


def pmcc_target(stock_px, leaps_strike, leaps_entry_premium, vol_ann):
    """25-delta ~30d proxy target, floored at breakeven x 1.02."""
    sigma_30 = vol_ann * math.sqrt(30 / 365.0)
    target = stock_px * (1 + 0.67 * sigma_30)
    breakeven = (leaps_strike or 0) + (leaps_entry_premium or 0)
    return max(target, breakeven * 1.02)


def select_pmcc_short(chain, quotes, stock_px, leaps_strike, leaps_entry_premium, vol_ann, session_iso):
    """the old select_pmcc_short: the nearest 25-38 DTE expiry, the first strike >= the target; bid > 0,
    ask >= bid, (ask - bid) / mid <= 5%."""
    if vol_ann is None or vol_ann <= 0 or not stock_px:
        return None
    ref = _parse_date(session_iso)
    if ref is None:
        return None
    target = pmcc_target(stock_px, leaps_strike, leaps_entry_premium, vol_ann)
    by_exp = {}
    for c in chain or []:
        exp = str(c.get("expiration") or "")[:10]
        d = _parse_date(exp)
        if d is None or not (PMCC_DTE_MIN <= (d - ref).days <= PMCC_DTE_MAX):
            continue
        by_exp.setdefault(exp, []).append(c)
    if not by_exp:
        return None
    expiry = sorted(by_exp)[0]
    cands = []
    for c in by_exp[expiry]:
        try:
            s = float(c.get("strike", 0))
        except (TypeError, ValueError):
            continue
        if s >= target:
            cands.append((s, c))
    if not cands:
        return None
    strike, best = min(cands, key=lambda t: t[0])
    q = (quotes or {}).get(best["symbol"])
    if not q:
        return None
    try:
        bid, ask = float(q.get("bid") or 0), float(q.get("ask") or 0)
    except (TypeError, ValueError):
        return None
    if not (bid > 0 and ask >= bid) or (ask - bid) / ((ask + bid) / 2) > SPREAD_GATE_FRAC:
        return None
    return {"occ": best["symbol"], "strike": strike, "expiry": expiry, "dte": (_parse_date(expiry) - ref).days,
            "bid": bid, "ask": ask, "target": round(target, 2), "vol_ann": round(vol_ann, 3)}


def pmcc_roll_due(short, spot, session_iso):
    """the old manage_pmcc_shorts trigger: "roll_21dte" at <= 21 DTE, else "tested" when the stock trades within
    3% of the strike."""
    exp_d, ref = _parse_date((short or {}).get("expiry")), _parse_date(session_iso)
    dte = (exp_d - ref).days if exp_d is not None and ref is not None else None
    if dte is not None and dte <= PMCC_ROLL_DTE:
        return "roll_21dte"
    strike = (short or {}).get("strike")
    if spot and strike and spot >= strike * (1 - PMCC_TEST_FRAC):
        return "tested"
    return None


def _mid(q):
    """the old quote mid: (bid + ask) / 2 of whatever is quoted, 0 when unquoted."""
    try:
        return (float(q.get("bid") or 0) + float(q.get("ask") or 0)) / 2 if q else 0.0
    except (TypeError, ValueError):
        return 0.0


def spot_of(sym, quotes, bars):
    q = (quotes or {}).get(sym) or {}
    try:
        bid, ask, last = q.get("bid"), q.get("ask"), q.get("last")
        if bid and ask and float(ask) >= float(bid) > 0:
            return (float(bid) + float(ask)) / 2
        if last and float(last) > 0:
            return float(last)
    except (TypeError, ValueError):
        pass
    bl = (bars or {}).get(sym) or []
    return float(bl[-1]["c"]) if bl else None


def _underlying(occ):
    return occ[:-15]


def book_state(legs, pending):
    """the old state from the sleeve's contracts: positions {SYM: LEAPS {occ, contracts, entry_premium,
    leaps_strike, expiry, pmcc_shorts: [...]}}, closing {SYM: the same, exit working}, in-flight entries by
    kind, and calls without a LEAPS."""
    exiting = {p["occ"] for p in pending if p.get("action") in ("exit", "target")}
    entering = [p for p in pending if p.get("action") == "enter"]
    positions, closing, shorts = {}, {}, {}
    for occ, lg in legs.items():
        qty = float(lg.get("qty") or 0)
        meta = lg.get("meta") or {}
        sym = meta.get("sym") or _underlying(occ)
        if qty > 0:
            rec = {"symbol": sym, "occ": occ, "contracts": int(round(qty)),
                   "entry_premium": round(float(lg.get("avg") or 0), 2), "leaps_strike": meta.get("strike"),
                   "expiry": meta.get("expiry"), "opened_at": lg.get("opened_at"), "pmcc_shorts": []}
            (closing if occ in exiting else positions)[sym] = rec
        elif qty < 0:
            shorts.setdefault(sym, []).append({"occ": occ, "contracts": int(round(-qty)), "strike": meta.get("strike"),
                                               "expiry": meta.get("expiry"), "closing": occ in exiting})
    orphans = []
    for sym, shs in shorts.items():
        home = positions.get(sym) or closing.get(sym)
        if home is None:
            orphans += [dict(s, symbol=sym) for s in shs]
        else:
            home["pmcc_shorts"] = shs
    leaps_in = {str(p.get("key") or "").split(":")[1] for p in entering if str(p.get("key")).startswith("leaps:")}
    pmcc_in = {str(p.get("key") or "").split(":")[1] for p in entering if str(p.get("key")).startswith("pmcc:")}
    return positions, closing, leaps_in, pmcc_in, orphans


def slots_used(positions, closing, leaps_in, pending):
    """the 8 slots: LEAPS held, closing, or in flight."""
    return len(positions) + len(closing) + len(leaps_in)


def _btc(occ):
    return {"symbol": occ, "side": "buy", "ratio": 1, "position_intent": "buy_to_close"}


def _stc(occ):
    return {"symbol": occ, "side": "sell", "ratio": 1, "position_intent": "sell_to_close"}


def _close(sym, pos, reason, oq, session):
    """the old close_leaps: (intents, closed). The calls first at their mids (no order at all while one has
    none, or while one is already being bought back), then the LEAPS at its mid (its bid on the stop) — one
    package when both legs size alike."""
    if any(s.get("closing") for s in pos.get("pmcc_shorts") or []):
        return [], False
    shorts = list(pos.get("pmcc_shorts") or [])
    px = {}
    for sh in shorts:
        m = _mid(oq.get(sh["occ"]))
        if m <= 0:
            return [], False
        px[sh["occ"]] = m
    q = oq.get(pos["occ"]) or {}
    try:
        bid, ask = float(q.get("bid") or 0), float(q.get("ask") or 0)
    except (TypeError, ValueError):
        bid, ask = 0.0, 0.0
    key = "%s:%s:leaps-exit" % (sym, session)
    why = "leaps_momentum exit: %s occ=%s contracts=%d" % (reason, pos["occ"], pos["contracts"])
    out = []
    if bid <= 0:                        # the old bought the calls back and left the LEAPS for a later pass
        for sh in shorts:
            out.append(Intent("exit", sym, qty_hint=sh["contracts"], legs=(_btc(sh["occ"]),),
                              order={"type": "limit", "limit_price": px[sh["occ"]], "window_s": 3300},
                              signal_key="%s:%s:pmcc-close" % (sym, session), reason=why + " (calls only: no bid)"))
        return out, False
    lp = bid if reason == "stop_minus30pct" else (bid + ask) / 2
    if shorts and all(sh["contracts"] == pos["contracts"] for sh in shorts):
        net = sum(px.values()) - lp                                    # pay for the calls, receive the LEAPS
        legs = tuple([_stc(pos["occ"])] + [_btc(sh["occ"]) for sh in shorts])
        out.append(Intent("exit", sym, qty_hint=pos["contracts"], legs=legs, net_price=net,
                          order={"window_s": 3300}, signal_key=key, reason=why))
        return out, True
    for sh in shorts:
        out.append(Intent("exit", sym, qty_hint=sh["contracts"], legs=(_btc(sh["occ"]),),
                          order={"type": "limit", "limit_price": px[sh["occ"]], "window_s": 3300},
                          signal_key="%s:%s:pmcc-close" % (sym, session), reason=why))
    out.append(Intent("exit", sym, qty_hint=pos["contracts"], legs=(_stc(pos["occ"]),),
                      order={"type": "limit", "limit_price": lp, "window_s": 3300}, signal_key=key, reason=why))
    return out, True


def decide(bars, context):
    """one pass of the old cron: mirror (LEAPS exits, then entries), then pmcc (rolls, then new calls)."""
    extra = context.extra or {}
    now, today = float(context.now), context.session
    equity = float(context.equity or 0.0)
    oq = extra.get("option_quotes") or {}
    quotes = extra.get("quotes") or {}
    legs = extra.get("legs") or {}
    pending = extra.get("pending") or []
    positions, closing, leaps_in, pmcc_in, orphans = book_state(legs, pending)
    mom = momentum_book(extra.get("momentum"), now)
    intents, due = [], set()
    # mirror: exits first, never gated
    for sym in list(positions):
        pos = positions[sym]
        d = _parse_date(pos.get("expiry"))
        dte = (d - date.fromisoformat(today)).days if d else None
        reason = leaps_exit_due(sym, pos, mom, dte, _mid(oq.get(pos["occ"])))
        if not reason:
            continue
        due.add(sym)
        out, closed = _close(sym, pos, reason, oq, today)
        intents += out
        if closed:
            closing[sym] = positions.pop(sym)
        elif out:
            pos["pmcc_shorts"] = [dict(s, closing=True) for s in pos["pmcc_shorts"]]
    # mirror: entries in the book's order
    slots = slots_used(positions, closing, leaps_in, pending)
    if mom and equity > 0:
        for sym, rec in mom.items():
            if sym in positions or sym in leaps_in:
                continue
            if slots >= MAX_POSITIONS:
                break
            spot = spot_of(sym, quotes, bars)
            if not spot:
                continue
            rows = (extra.get("leaps_chains") or {}).get(sym) or []
            found = find_leaps_contract(rows, {r["symbol"]: r for r in rows}, spot, today)
            if not found:
                continue
            try:
                mom_qty = int((rec or {}).get("qty") or 0)
            except (TypeError, ValueError):
                mom_qty = 0
            n = size_leaps_contracts(mom_qty or 100, found["ask"], equity)
            if n <= 0:
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=n, asset="option",
                legs=({"symbol": found["occ"], "side": "buy", "ratio": 1, "position_intent": "buy_to_open"},),
                order={"type": "limit", "limit_price": found["ask"], "window_s": 3300},
                signal_key="leaps:%s:%s:%s" % (sym, found["occ"], today),
                position_meta={"role": "leaps", "sym": sym, "strike": found["strike"], "expiry": found["expiry"],
                               "ask": found["ask"], "mom_qty": mom_qty},
                reason="leaps_momentum long_call: occ=%s strike=%.2f expiry=%s ask=%.2f x%d mom_qty=%d spot=%.2f"
                       % (found["occ"], found["strike"], found["expiry"], found["ask"], n, mom_qty, spot)))
            leaps_in.add(sym)
            slots += 1
    # pmcc: roll the tested / aging calls, then sell a call on each LEAPS without one
    for sym, pos in positions.items():
        if sym in due:                      # a LEAPS whose exit is due neither rolls nor sells a call
            continue
        spot = spot_of(sym, quotes, bars)
        for sh in pos["pmcc_shorts"]:
            if sh.get("closing"):
                continue
            why = pmcc_roll_due(sh, spot, today)
            if not why:
                continue
            m = _mid(oq.get(sh["occ"]))
            if m <= 0:
                continue
            intents.append(Intent(
                "exit", sym, qty_hint=sh["contracts"], legs=(_btc(sh["occ"]),),
                order={"type": "limit", "limit_price": m, "window_s": 3300},
                signal_key="%s:%s:pmcc-roll" % (sym, today),
                reason="leaps_momentum pmcc_roll: %s occ=%s contracts=%d" % (why, sh["occ"], sh["contracts"])))
            sh["closing"] = True
        if pos["pmcc_shorts"] or sym in pmcc_in or not spot:
            continue
        vol = realized_vol_30d([float(b["c"]) for b in (bars or {}).get(sym) or []])
        rows = (extra.get("pmcc_chains") or {}).get(sym) or []
        sel = select_pmcc_short(rows, {r["symbol"]: r for r in rows}, spot, pos.get("leaps_strike"),
                                pos.get("entry_premium"), vol, today)
        if not sel:
            continue
        intents.append(Intent(
            "enter", sym, qty_hint=pos["contracts"], asset="option",
            legs=({"symbol": sel["occ"], "side": "sell", "ratio": 1, "position_intent": "sell_to_open"},),
            order={"type": "limit", "limit_price": sel["bid"], "window_s": 3300},
            signal_key="pmcc:%s:%s:%s" % (sym, sel["occ"], today),
            position_meta={"role": "pmcc", "sym": sym, "strike": sel["strike"], "expiry": sel["expiry"],
                           "target": sel["target"], "vol_ann": sel["vol_ann"], "leaps_occ": pos["occ"]},
            reason="leaps_momentum pmcc_short: occ=%s strike=%.2f expiry=%s dte=%d bid=%.2f x%d target=%.2f "
                   "vol=%.3f delta~%.2f" % (sel["occ"], sel["strike"], sel["expiry"], sel["dte"], sel["bid"],
                                            pos["contracts"], sel["target"], sel["vol_ann"], PMCC_SHORT_DELTA)))
    # a call whose LEAPS is gone is bought back at the ask (the old _flatten_pmcc_short)
    for sh in orphans:
        if sh.get("closing"):
            continue
        try:
            ask = float((oq.get(sh["occ"]) or {}).get("ask") or 0)
        except (TypeError, ValueError):
            ask = 0.0
        if ask > 0:
            intents.append(Intent(
                "exit", sh["symbol"], qty_hint=sh["contracts"], legs=(_btc(sh["occ"]),),
                order={"type": "limit", "limit_price": ask, "window_s": 3300},
                signal_key="%s:%s:pmcc-orphan" % (sh["symbol"], today),
                reason="leaps_momentum pmcc_orphan: occ=%s contracts=%d (LEAPS gone)" % (sh["occ"], sh["contracts"])))
    return intents


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_leaps_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:           # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_leaps_pass"] = memo
    return memo[1]


class LeapsMomentum(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context))


def signal(bars, slice_state, context):
    return LeapsMomentum().signal(bars, slice_state, context)
