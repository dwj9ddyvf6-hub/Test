"""VIX Hedge — portfolio tail insurance — lean-desk port (Wave B).

master-desk: the old desk's vix_hedge_sleeve.py restored on the engine. When the market is complacent (VIX < 16
OR its 30-day percentile < 25), buy cheap ~90-DTE VXX calls (~25 delta) as tail insurance. INSURANCE: loses money
most quarters by design; 1% of equity per hedge, one hedge at a time, never added to.

  read ..... the ^VIX daily closes ending at the live VIX (the old read Yahoo's daily series, whose last value is
             the session's running VIX); percentile = the share of the last 30 values strictly below the newest.
  entry .... complacent, flat (no hedge held or working): VXX calls 60-110 DTE; per expiry the strike nearest
             1.20 x spot; expiries closest to 90 DTE first; the first with a two-sided quote whose spread is
             <= 20% of mid wins (none: no hedge vehicle); floor(1% of equity / (ask x 100)) contracts (0: skip);
             buy to open, limit at the ask.
  exits .... (never gated; checked every pass, complacent or not) the call's mid worth >= 2x the debit paid
             (+100%), the live VIX > 30 (the hedge worked), <= 21 days to expiry (the roll); sell to close,
             limit at the mid.

Gone under the cutover doctrine: the risk gate (kill switch, daily loss), the Decision #75 chart gate (pre_buy
staging, its 24h pending TTL and release replay), the 150% desk cap (the drawdown brake never applied: exempt).
Named divergences: passes hourly at :49 in the session (the old cron ran hourly at :49 around the clock); the
spot is VXX's live quote (the old read the latest SIP daily bar's close); candidate quotes come from the chain
snapshot (the old made a separate latest-quote call for them); the debit is the fill (book average).

Inputs via context.extra:
  "vix_closes"  [float, ...] the ^VIX daily closes, oldest first, ending at the live VIX
  "chain"       {"VXX": chain rows {"symbol","strike","expiration","type","bid","ask",...}} (calls)
  "option_quotes" {OCC: {"bid","ask"}} — the held call
  "quotes"      {"VXX": {"bid","ask","last"}} — the spot
  "sleeve_state" {"VXX": {"position": {"qty","entry_px","occ",...} | None, "pending_entry": ...}}
Bars (arg): {"VXX": daily bars} (the spot when no quote)."""
import math
from datetime import datetime, timezone

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

VIX_LEVEL_COMPLACENT = 16.0
VIX_PCTL_LOOKBACK = 30
VIX_PCTL_COMPLACENT = 25.0
VIX_EXIT_SPIKE = 30.0
HEDGE_UNDERLYING = "VXX"
DTE_MIN, DTE_MAX = 60, 110
DTE_TARGET = 90
DTE_FLOOR = 21
DELTA_STRIKE_OTM = 1.20
SPREAD_GATE_FRAC = 0.20
HEDGE_RISK_FRACTION = 0.01
MAX_HEDGES = 1
PROFIT_TARGET_MULT = 2.0
BRAKE_EXEMPT = True  # 2026-10-10 ruling: tail hedge is brake-exempt

CONFIG = SleeveConfig(
    sleeve_id="vix_hedge", cadence_s=300, universe=(HEDGE_UNDERLYING,),
    state_schema={"position": "dict|None"}, risk_pct=HEDGE_RISK_FRACTION)


def vix_percentile(closes, lookback=VIX_PCTL_LOOKBACK):
    """Percentile of the last close within the last `lookback` closes:
    share of window closes strictly below it, x 100. Verbatim."""
    if not closes:
        return None
    window = closes[-lookback:]
    vix = closes[-1]
    return sum(1 for c in window if c < vix) / len(window) * 100.0


def vix_complacent(closes):
    """(complacent, vix, percentile). Fail-closed on no read (the old fetch refused fewer than 35 closes)."""
    if not closes or len(closes) < VIX_PCTL_LOOKBACK + 5:
        return False, None, None
    vix = closes[-1]
    pctl = vix_percentile(closes)
    return (vix < VIX_LEVEL_COMPLACENT or pctl < VIX_PCTL_COMPLACENT), vix, pctl


def pick_hedge_call(chain, quotes, ref_px, session_iso):
    """Pure form of the old pick_hedge_call: per expiry in 60-110 DTE
    the strike nearest 1.20 x spot; expiries ordered by closeness to
    90 DTE; first candidate with a two-sided quote inside the 20%
    gate wins. None => no hedge vehicle (fail closed)."""
    from datetime import date as _date
    try:
        ref = _date.fromisoformat(session_iso)
    except ValueError:
        return None
    calls = []
    for c in chain or []:
        try:
            calls.append({"strike": float(c["strike"]), "occ": c["symbol"],
                          "exp": str(c.get("expiration")
                                     or c.get("expiration_date") or "")[:10]})
        except (KeyError, TypeError, ValueError):
            continue
    if not calls:
        return None
    by_exp = {}
    for c in calls:
        by_exp.setdefault(c["exp"], []).append(c)
    target = ref_px * DELTA_STRIKE_OTM
    cands = []
    for exp, grp in by_exp.items():
        try:
            dte = (_date.fromisoformat(exp) - ref).days
        except ValueError:
            continue
        if dte < DTE_MIN or dte > DTE_MAX:
            continue
        cand = min(grp, key=lambda c: abs(c["strike"] - target))
        cands.append((exp, dte, cand["strike"], cand["occ"]))
    if not cands:
        return None
    cands.sort(key=lambda t: abs(t[1] - DTE_TARGET))
    q = quotes or {}
    for exp, dte, strike, occ in cands:
        qq = q.get(occ, {})
        try:
            bid, ask = float(qq.get("bid") or 0), float(qq.get("ask") or 0)
        except (TypeError, ValueError):
            continue
        if not (bid > 0 and ask >= bid):
            continue
        mid = (bid + ask) / 2
        if (ask - bid) / mid > SPREAD_GATE_FRAC:
            continue
        return {"occ": occ, "strike": strike, "expiry": exp, "dte": dte,
                "bid": bid, "ask": ask, "mid": round(mid, 2),
                "ref_px": round(ref_px, 2)}
    return None


def size_contracts(equity, ask):
    """Contracts fitting 1% of equity at the ask. 0 = skip. Verbatim."""
    if equity is None or equity <= 0 or ask <= 0:
        return 0
    return max(0, int(math.floor((equity * HEDGE_RISK_FRACTION) / (ask * 100))))


def exit_due(pos, dte, mid, vix):
    """Verbatim old exit_due: +100% of debit (entry_debit is the TOTAL
    debit for the position), VIX spike > 30, 21-DTE floor."""
    if mid is not None and pos.get("entry_debit", 0) > 0:
        cur_val = mid * pos["contracts"] * 100
        if cur_val >= PROFIT_TARGET_MULT * pos["entry_debit"]:
            return "profit_target_100pct"
    if vix is not None and vix > VIX_EXIT_SPIKE:
        return "vol_spike_take_profit"
    if dte is not None and dte <= DTE_FLOOR:
        return "dte_floor_21"
    return None


class VixHedge(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        oq = extra.get("option_quotes") or {}
        equity = float(context.equity or 0.0)
        complacent, vix, pctl = vix_complacent(extra.get("vix_closes") or [])
        st = state.get(HEDGE_UNDERLYING) or {}
        pos = st.get("position")
        intents = []
        if pos:
            qty = int(float(pos.get("contracts") or pos.get("qty") or 0))
            occ = pos.get("occ")
            if qty > 0 and occ and not pos.get("exit_submitted"):
                q = oq.get(occ) or {}
                try:
                    mid = (float(q["bid"]) + float(q["ask"])) / 2 if q.get("bid") and q.get("ask") else None
                except (TypeError, ValueError):
                    mid = None
                dte = None
                try:
                    from datetime import date as _date
                    dte = (_date.fromisoformat(str(pos.get("expiry") or occ_expiry(occ))[:10])
                           - _date.fromisoformat(context.session)).days
                except (ValueError, TypeError):
                    pass
                p = dict(pos, contracts=qty, entry_debit=float(pos.get("entry_px") or 0) * qty * 100)
                reason = exit_due(p, dte, mid, vix)
                if reason and mid:                        # close_hedge sells at the mid; no mid, no order
                    order = {"type": "limit", "limit_price": round(mid, 2), "window_s": 3600}
                    intents.append(Intent(
                        "exit", HEDGE_UNDERLYING, qty_hint=qty, order=order,
                        signal_key="%s:%s:exit" % (occ, context.session),
                        reason="vix_hedge exit: %s occ=%s mid=%s vix=%s" % (reason, occ, mid, vix)))
            return intents
        if st.get("pending_entry") or not complacent or equity <= 0:
            return intents
        spot = spot_of(extra.get("quotes"), bars)
        if not spot:
            return intents
        hedge = pick_hedge_call((extra.get("chain") or {}).get(HEDGE_UNDERLYING),
                                {r["symbol"]: r for r in (extra.get("chain") or {}).get(HEDGE_UNDERLYING) or []
                                 if r.get("symbol")}, spot, context.session)
        if not hedge:
            return intents  # no_hedge_vehicle: fail closed, do nothing
        qty = size_contracts(equity, hedge["ask"])
        if qty <= 0:
            return intents
        intents.append(Intent(
            "enter", HEDGE_UNDERLYING, qty_hint=qty, asset="option",
            legs=({"symbol": hedge["occ"], "side": "buy", "ratio": 1, "position_intent": "buy_to_open"},),
            order={"type": "limit", "limit_price": hedge["ask"], "window_s": 3600},
            signal_key="%s:%s:hedge" % (hedge["occ"], context.session),
            position_meta={"occ": hedge["occ"], "expiry": hedge["expiry"], "strike": hedge["strike"],
                           "dte_at_entry": hedge["dte"], "ask": hedge["ask"], "vix": round(vix, 2),
                           "pctl30": round(pctl, 1) if pctl is not None else None, "ref_px": hedge["ref_px"]},
            reason="vix_hedge long call: %s strike %.2f expiry %s dte %d ask %.2f x%d; vix %.2f pctl30 %.1f "
                   "(complacent); strike nearest 1.20 x spot %.2f"
                   % (hedge["occ"], hedge["strike"], hedge["expiry"], hedge["dte"], hedge["ask"], qty, vix,
                      pctl, spot)))
        return intents


def occ_expiry(occ):
    s = str(occ)[-15:]
    return "20%s-%s-%s" % (s[0:2], s[2:4], s[4:6])


def spot_of(quotes, bars):
    """VXX's live price: the quote's mid when two-sided, else its last, else the last daily close."""
    q = (quotes or {}).get(HEDGE_UNDERLYING) or {}
    try:
        bid, ask, last = q.get("bid"), q.get("ask"), q.get("last")
        if bid and ask and float(ask) >= float(bid) > 0:
            return (float(bid) + float(ask)) / 2
        if last and float(last) > 0:
            return float(last)
    except (TypeError, ValueError):
        pass
    bl = (bars or {}).get(HEDGE_UNDERLYING) or []
    return float(bl[-1]["c"]) if bl else 0.0


def signal(bars, slice_state, context):
    return VixHedge().signal(bars, slice_state, context)
