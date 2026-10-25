"""LEAPS Momentum — lean-desk port (Wave B).

EXTRACTED from the old desk's leaps_momentum.py. The signal is the
momentum sleeve's live book (a core Data/Ledger product here): mirror
its positions with 70-80 delta LEAPS, exit when a name rotates out.
Contract selection, sizing, LEAPS exits and the PMCC short-call
selection are the old file's pure logic over chain snapshots the core
provides. See ports/leaps_momentum.md.

LEAPS: nearest expiry >= 365 DTE; strike nearest 80% of spot (the
documented 75-delta proxy — the chain carries no Greeks); two-sided
quote with (ask-bid)/mid <= 5%; premium paid <= 5% of equity per name;
contracts mirror momentum shares (1 per 100 shares), capped by that
5% premium cap; max 8 positions. Momentum book staleness: a book
older than 7 days is a fossil — fail closed (2026-10-11 semfix);
extra["momentum_book_age_days"] carries the age, absent = fail closed.
LEAPS exits: rotated out of the book, 60-DTE floor, -30% stop on the
premium (core-supplied mid via extra["quotes"]).
PMCC: monthly ~25-delta short calls (~30 DTE, 25-38 window): target =
spot x (1 + 0.67 x sigma_30d), never below LEAPS breakeven x 1.02;
first strike >= target; same 5% quote gate; rolled at 21 DTE or when
the stock is within 3% of the short strike (roll rules are emitted as
exit+enter intent pairs by the core-facing signal — the short's own
state rides in sleeve_state["pmcc_short"]).

Inputs via context.extra:
  "momentum_book": {SYM: {"qty": shares}} | None
  "momentum_book_age_days": float
  "chains":  {SYM: [{"symbol","strike","expiration"}]} (calls)
  "quotes":  {OCC: {"bid","ask"}}
  "sleeve_state": {SYM: {"position": {...}|None, "pmcc_short": {...}|None}}
Bars (arg): daily dicts (spot + the 30d realized-vol series for PMCC).
"""
import math

from core.sleeve import BaseSleeve, Intent, SleeveConfig

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
LEAPS_STRIKE_FRAC = 0.80   # deep-ITM ~75-0.85 delta proxy

CONFIG = SleeveConfig(
    sleeve_id="leaps_momentum", cadence_s=300, universe=(),
    state_schema={"position": "dict|None", "pmcc_short": "dict|None"},
    risk_pct=LEAPS_NOTIONAL_CAP)


def _parse_date(s):
    try:
        from datetime import date as _date
        return _date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def _quote_ok(q):
    """Two-sided quote inside the 5% gate. Returns (bid, ask) or None.
    (Bid AND ask required — the 2026-10-10 ask=0 wedge fix.)"""
    if not q:
        return None
    try:
        bid, ask = float(q.get("bid") or 0), float(q.get("ask") or 0)
    except (TypeError, ValueError):
        return None
    if bid <= 0 or ask <= 0 or ask < bid:
        return None
    if not (math.isfinite(bid) and math.isfinite(ask)):
        return None
    if (ask - bid) / ((ask + bid) / 2) > SPREAD_GATE_FRAC:
        return None
    return bid, ask


def enhance_enabled(extra):
    """ENH leaps_momentum (IMPROVE-leaps_momentum): nearest-first
    strike-walk switch, ctx.extra['leaps_momentum_enhance']
    ['enabled'], default ON; OFF restores the pre-change rule
    exactly (target strike or nothing)."""
    ov = (extra or {}).get("leaps_momentum_enhance")
    if isinstance(ov, dict) and "enabled" in ov:
        return bool(ov["enabled"])
    if isinstance(ov, bool):
        return ov
    return True


def find_leaps_contract(chain, quotes, stock_price, session_iso,
                        min_dte=MIN_DTE, walk=False):
    """Pure form of the old find_leaps_contract: nearest expiry >=
    min_dte; strike nearest 0.80 x spot; quote must pass _quote_ok.
    Returns {"occ","ask","bid","strike","expiry"} or None.
    ENH (walk=True): try the expiry's strikes nearest-first from
    0.80 x spot and take the first passing the same _quote_ok gate;
    None only when no strike in the expiry passes."""
    ref = _parse_date(session_iso)
    if ref is None:
        return None
    by_exp = {}
    for c in chain or []:
        exp = str(c.get("expiration") or c.get("expiration_date") or "")[:10]
        d = _parse_date(exp)
        try:
            strike = float(c["strike"])
        except (TypeError, ValueError, KeyError):
            continue
        if not c.get("symbol"):
            continue  # malformed row: no OCC to trade — skip, never crash
        if d is None or (d - ref).days < min_dte:
            continue
        by_exp.setdefault(exp, []).append({"occ": c["symbol"], "strike": strike})
    if not by_exp:
        return None
    expiry = sorted(by_exp.keys())[0]
    target = stock_price * LEAPS_STRIKE_FRAC
    ordered = sorted(by_exp[expiry],
                     key=lambda c: abs(c["strike"] - target))
    if not walk:
        ordered = ordered[:1]
    for cand in ordered:
        ok = _quote_ok((quotes or {}).get(cand["occ"]))
        if not ok:
            continue
        bid, ask = ok
        return {"occ": cand["occ"], "ask": ask, "bid": bid,
                "strike": cand["strike"], "expiry": expiry}
    return None


def size_leaps_contracts(mom_qty, ask, equity):
    """Mirror momentum's share count; 1 contract per 100 shares,
    capped so premium <= 5% of equity. 0 = skip. Verbatim.
    OBS-1 (ruling 2026-10-22): the 1-contract floor is removed —
    a mirror quantity under 100 shares is 0 contracts (skip),
    as this function's own cap path already allowed."""
    contracts = int(mom_qty) // 100
    if equity and equity > 0 and ask and ask > 0:
        cap_n = int((equity * LEAPS_NOTIONAL_CAP) / (ask * 100))
        contracts = min(contracts, max(0, cap_n))
    return max(0, contracts)


def leaps_exit_due(sym, pos, mom_book, dte, mid):
    """Verbatim old order: rotation out, 60-DTE floor, -30% stop."""
    if mom_book is not None and sym not in mom_book:
        return "momentum_rotation_out"
    if dte is not None and dte <= LEAPS_DTE_FLOOR:
        return "dte_floor_60"
    entry = pos.get("entry_premium") or 0
    if mid and mid > 0 and entry > 0 and mid <= entry * (1 - LEAPS_STOP_FRAC):
        return "stop_minus30pct"
    return None


def realized_vol_30d(closes):
    """30d annualized realized vol from daily closes. Pure form of
    the old _realized_vol_30d (which fetched bars itself)."""
    try:
        closes = [float(c) for c in closes[-31:]]
    except (TypeError, ValueError):
        return None
    if len(closes) < 21 or any(c <= 0 for c in closes):
        return None  # log returns are undefined on a non-positive close
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))
            if closes[i - 1] > 0]
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


def select_pmcc_short(chain, quotes, stock_px, leaps_strike,
                      leaps_entry_premium, vol_ann, session_iso):
    """Pure form of the old select_pmcc_short: nearest 25-38 DTE
    expiry, first strike >= target, 5% two-sided quote gate."""
    if vol_ann is None or vol_ann <= 0 or stock_px <= 0:
        return None
    ref = _parse_date(session_iso)
    if ref is None:
        return None
    target = pmcc_target(stock_px, leaps_strike, leaps_entry_premium, vol_ann)
    by_exp = {}
    for c in chain or []:
        exp = str(c.get("expiration") or c.get("expiration_date") or "")[:10]
        d = _parse_date(exp)
        try:
            strike = float(c["strike"])
        except (TypeError, ValueError, KeyError):
            continue
        if not c.get("symbol"):
            continue  # malformed row: no OCC to trade — skip, never crash
        if d is None or not (PMCC_DTE_MIN <= (d - ref).days <= PMCC_DTE_MAX):
            continue
        by_exp.setdefault(exp, []).append({"occ": c["symbol"], "strike": strike})
    if not by_exp:
        return None
    expiry = sorted(by_exp.keys())[0]
    cands = sorted([c for c in by_exp[expiry] if c["strike"] >= target],
                   key=lambda c: c["strike"])
    if not cands:
        return None
    best = cands[0]
    ok = _quote_ok((quotes or {}).get(best["occ"]))
    if not ok:
        return None
    bid, ask = ok
    return {"occ": best["occ"], "strike": best["strike"], "expiry": expiry,
            "dte": (_parse_date(expiry) - ref).days, "bid": bid, "ask": ask,
            "target": round(target, 2), "vol_ann": round(vol_ann, 3)}


def pmcc_roll_due(short, spot, session_iso):
    """Roll at 21 DTE or when spot is within 3% of the short strike."""
    exp_d = _parse_date((short or {}).get("expiry"))
    ref = _parse_date(session_iso)
    if exp_d is not None and ref is not None \
            and (exp_d - ref).days <= PMCC_ROLL_DTE:
        return "pmcc_roll_dte_21"
    strike = (short or {}).get("strike") or 0
    if spot and strike > 0 and spot >= strike * (1 - PMCC_TEST_FRAC):
        return "pmcc_tested_within_3pct"
    return None


class LeapsMomentum(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        mom_book = extra.get("momentum_book")
        try:
            book_age = float(extra.get("momentum_book_age_days"))
        except (TypeError, ValueError):
            book_age = None  # an unreadable age is a stale book: fail closed
        book_fresh = mom_book is not None and book_age is not None \
            and book_age <= MOMENTUM_BOOK_MAX_AGE_DAYS
        equity = float(context.equity or 0.0)
        intents = []
        self._paired = []
        self.last_evaluation = {"sleeve": "leaps_momentum",
                                "enhance_switch": enhance_enabled(extra),
                                "paired": self._paired}
        syms = sorted(set(state.keys()) | set((mom_book or {}).keys()))
        open_n = sum(1 for s in syms if (state.get(s) or {}).get("position"))
        for sym in syms:
            st = state.get(sym) or {}
            pos = st.get("position")
            bl = bars.get(sym) or []
            spot = float(bl[-1]["c"]) if bl else 0.0
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                q = quotes.get(pos.get("occ")) or {}
                try:
                    mid = (float(q["bid"]) + float(q["ask"])) / 2 \
                        if q.get("bid") and q.get("ask") else None
                except (TypeError, ValueError):
                    mid = None
                exp_d, ref = _parse_date(pos.get("expiry")), \
                    _parse_date(context.session)
                dte = (exp_d - ref).days if exp_d and ref else None
                # A stale book disables rotation exits too (the fossil
                # must not fire exits): pass None book when stale.
                reason = leaps_exit_due(sym, pos,
                                        mom_book if book_fresh else None,
                                        dte, mid)
                if reason:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(spot, 2) if spot else None,
                        reason="leaps_momentum exit: %s occ=%s" % (reason, pos.get("occ"))))
                    continue
                # PMCC management: roll a tested/aging short; open one
                # when none is on (the short sale is an intent the core
                # routes as a premium-sale, Decision #85 family).
                short = st.get("pmcc_short")
                if short:
                    roll = pmcc_roll_due(short, spot, context.session)
                    if roll:
                        intents.append(Intent(
                            "exit", sym, qty_hint=int(float(short.get("qty") or 0)) or qty,
                            price_hint=round(spot, 2) if spot else None,
                            reason="leaps_momentum pmcc_roll: %s occ=%s"
                                   % (roll, short.get("occ"))))
                    continue
                if spot > 0:
                    vol = realized_vol_30d([float(b["c"]) for b in bl])
                    sel = select_pmcc_short(chains.get(sym), quotes, spot,
                                            pos.get("strike"),
                                            pos.get("entry_premium"), vol,
                                            context.session)
                    if sel:
                        intents.append(Intent(
                            "enter", sym, qty_hint=qty,
                            price_hint=round(spot, 2),
                            reason="leaps_momentum pmcc_short: occ=%s "
                                   "strike=%.2f expiry=%s dte=%d bid=%.2f "
                                   "structure=pmcc_short_call delta~%.2f"
                                   % (sel["occ"], sel["strike"], sel["expiry"],
                                      sel["dte"], sel["bid"], PMCC_SHORT_DELTA)))
                continue
            # AUDIT3-C-03 (2026-10-16): an orphaned PMCC short —
            # the LEAPS long exited (its record cleared; the
            # entry's pmcc_short overlay persists) — was never
            # managed again: PMCC management lived inside
            # `if pos:`, so the covered call became a naked short
            # no code path could close. An uncovered short is
            # closed on first evaluation (the strategy's cover
            # is gone); dispatch's pmcc_roll route resolves the
            # OCC + qty from the record.
            short = st.get("pmcc_short")
            if short:
                intents.append(Intent(
                    "exit", sym,
                    qty_hint=int(float(short.get("qty") or 0)),
                    price_hint=round(spot, 2) if spot else None,
                    reason="leaps_momentum pmcc_roll: "
                           "orphaned_short_close occ=%s"
                           % (short.get("occ"),)))
                continue
            # entries: mirror a fresh momentum book only
            if not book_fresh or equity <= 0 or open_n >= MAX_POSITIONS:
                continue
            rec = mom_book.get(sym) or {}
            mom_qty = rec.get("qty") if isinstance(rec, dict) else rec
            if not mom_qty or spot <= 0:
                continue
            enh_on = enhance_enabled(extra)
            control = find_leaps_contract(chains.get(sym), quotes, spot,
                                          context.session, walk=False)
            found = find_leaps_contract(chains.get(sym), quotes, spot,
                                        context.session, walk=enh_on)
            paired = getattr(self, "_paired", None)
            if paired is not None:
                paired.append({
                    "symbol": sym,
                    "control_occ": (control or {}).get("occ"),
                    "treatment_occ": (found or {}).get("occ"),
                    "treatment_strike": (found or {}).get("strike"),
                    "switch_on": enh_on})
            if not found:
                continue
            qty = size_leaps_contracts(mom_qty, found["ask"], equity)
            if qty <= 0:
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(spot, 2),
                reason="leaps_momentum long_call: occ=%s strike=%.2f "
                       "expiry=%s ask=%.2f mom_qty=%s structure=leaps_call "
                       "strike_rule=nearest(0.80*spot) min_dte=%d"
                       % (found["occ"], found["strike"], found["expiry"],
                          found["ask"], mom_qty, MIN_DTE)))
            open_n += 1
        return intents


def signal(bars, slice_state, context):
    return LeapsMomentum().signal(bars, slice_state, context)
