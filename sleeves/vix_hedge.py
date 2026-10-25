"""VIX Hedge — v3 port (batch 8): strategy copied faithfully from
muse-desk-v2 sleeves/vix_hedge.py (sha256 7e04e844…801ec7); only the
v2 core.sleeve import is re-expressed as the local contract below.
Adapter/registry declaration lives in adapters/vix_hedge.py.

Original docstring follows.
---
VIX Hedge — portfolio tail insurance — lean-desk port (Wave B).

EXTRACTED from the old desk's vix_hedge_sleeve.py. When the market is
complacent (VIX < 16 OR 30-day VIX percentile < 25), buy cheap
~90-DTE VXX calls (~25 delta) as tail insurance. INSURANCE: loses
money most quarters by design; size small (1% of equity per hedge,
max 1 hedge), never add to losers. See ports/vix_hedge.md.

** NO-CUTOVER-UNTIL-FLAT **: the old desk holds an open VXX hedge
(8x Dec $20 calls per the design spec section 4). This port is
code-complete but must NOT cut over until that position is flat on
the old desk or its state is imported explicitly and reconciled.

Complacency is a pure function of the VIX close series the core Data
door supplies (extra["vix_closes"], oldest->newest). Fail-closed:
no VIX read = NOT complacent. (The old last-good-cache path with its
2.5-day staleness TTL is core Data state, not sleeve logic; a cached
read arrives already staleness-labeled by the core.)
Vehicle: VXX calls 60-110 DTE; per expiry the strike nearest 1.20x
spot (the documented ~25-delta proxy — no Greeks on the chain);
expiries tried closest-to-90-DTE first; first with a two-sided quote
inside the 20% spread gate wins; none => no_hedge_vehicle (fail
closed). Drawdown brake: DELIBERATELY EXEMPT (2026-10-10) — a tail
hedge must be buyable during drawdowns; recorded here so core Risk
skips the brake for this sleeve's entries.
Exits (never gated): +100% of debit, VIX > 30 spike, 21-DTE floor.

Inputs via context.extra:
  "vix_closes": [float, ...] (the ^VIX daily closes; price-only use
                of Yahoo is the standing desk exception)
  "chains":     {"VXX": [{"symbol","strike","expiration"}]} (calls)
  "quotes":     {OCC: {"bid","ask"}}
  "sleeve_state": {"VXX": {"position": {...} | None}}
Bars (arg): {"VXX": daily bars} for the spot reference.
"""
import math
from dataclasses import dataclass, field


# --- v3 local contract (replaces v2 core.sleeve; semantics identical) ---
@dataclass(frozen=True)
class SleeveConfig:
    sleeve_id: str
    cadence_s: int
    universe: tuple = ()
    state_schema: dict = field(default_factory=dict)
    risk_pct: float = 0.0


@dataclass(frozen=True)
class Intent:
    kind: str
    symbol: str
    qty_hint: int | None = None
    qty: float | None = None
    limit_price: float | None = None
    price_hint: float | None = None
    stop: float | None = None
    target: float | None = None
    exit_rules: tuple = ()
    reason: str = ""
    side: str | None = None
    position_intent: str | None = None
    legs: tuple | None = None
    package_id: str | None = None
    signal_date: str | None = None

    def __post_init__(self):
        if self.kind not in ("enter", "exit"):
            raise ValueError(f"intent kind must be enter|exit, got {self.kind!r}")
        if self.qty_hint is not None and (int(self.qty_hint) != self.qty_hint or self.qty_hint <= 0):
            raise ValueError("qty_hint must be a positive whole number")


class BaseSleeve:
    CONFIG = None
    last_evaluation = None

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

# ENH (IMPROVE-vix_hedge): the broker-imported hedge adopted as the
# sleeve's position of record (import fields verbatim: 8 contracts,
# avg entry premium $1.10 — total debit $880 by the sleeve's own
# exit_due fallback arithmetic).
ADOPTED_IMPORT = {"occ": "VXX261218C00020000", "contracts": 8,
                  "expiry": "2026-12-18", "entry_premium": 1.10}


def improve_enabled(extra):
    """Adoption switch — context.extra["vix_hedge_improve"]
    ["adopt_imported_position"], default ON; OFF restores the
    pre-change rule exactly (import ignored, state as supplied)."""
    ov = (extra or {}).get("vix_hedge_improve")
    if isinstance(ov, dict) and "adopt_imported_position" in ov:
        return bool(ov["adopt_imported_position"])
    return True


def adopt_position(pos, extra):
    """Return the position of record: a state-carried position for
    the adopted OCC is completed with the import's expiry/contracts/
    entry_premium where missing; with no state position, an import
    record supplied via extra["vix_hedge_import"] is adopted whole.
    Otherwise None (pre-change behavior)."""
    imp = (extra or {}).get("vix_hedge_import")
    if pos:
        if pos.get("occ") == ADOPTED_IMPORT["occ"]:
            pos = dict(pos)
            pos.setdefault("expiry", ADOPTED_IMPORT["expiry"])
            if not pos.get("contracts"):
                pos["contracts"] = ADOPTED_IMPORT["contracts"]
            if not pos.get("entry_premium"):
                pos["entry_premium"] = ADOPTED_IMPORT["entry_premium"]
        return pos
    if isinstance(imp, dict) and imp.get("occ") == ADOPTED_IMPORT["occ"]:
        out = dict(ADOPTED_IMPORT)
        for k in ("contracts", "expiry", "entry_premium"):
            if imp.get(k):
                out[k] = imp[k]
        return out
    return None


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
    """(complacent, vix, percentile). Fail-closed on no read."""
    if not closes:
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
    debit for the position), VIX spike > 30, 21-DTE floor.

    Lean-state repair (2026-10-15): a core-recorded position carries
    entry_debit=None / contracts=None (core.state_store defaults; the
    dispatcher writes entry_premium = per-share ask and qty instead).
    The old expression `pos.get("entry_debit", 0) > 0` raised TypeError
    on None and the profit target could never fire on a desk fill.
    Fall back to the identical total: entry_premium x contracts x 100
    (qty standing in for contracts when only qty was recorded)."""
    contracts = pos.get("contracts") or pos.get("qty") or 0
    total_debit = pos.get("entry_debit") or pos.get("debit") or 0
    if not total_debit:
        prem = pos.get("entry_premium") or 0
        if prem and contracts:
            total_debit = float(prem) * float(contracts) * 100.0
    if mid is not None and total_debit > 0 and contracts:
        cur_val = mid * float(contracts) * 100
        if cur_val >= PROFIT_TARGET_MULT * total_debit:
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
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        equity = float(context.equity or 0.0)
        complacent, vix, pctl = vix_complacent(extra.get("vix_closes") or [])
        st = state.get(HEDGE_UNDERLYING) or {}
        pos = st.get("position")
        gate_on = improve_enabled(extra)
        adopted = False
        if gate_on:
            new_pos = adopt_position(pos, extra)
            adopted = new_pos is not None and (pos is None or new_pos != pos)
            pos = new_pos
        self.last_evaluation = {
            "improve_switch": gate_on, "adopted_import": adopted,
            "paired_record": {"control_position": (
                (state.get(HEDGE_UNDERLYING) or {}).get("position") or {}).get("occ"),
                "treatment_position": (pos or {}).get("occ")}}
        bl = bars.get(HEDGE_UNDERLYING) or []
        spot = float(bl[-1]["c"]) if bl else 0.0
        intents = []
        if pos:
            qty = int(float(pos.get("contracts") or pos.get("qty") or 0))
            if qty > 0:
                q = quotes.get(pos.get("occ")) or {}
                try:
                    mid = (float(q["bid"]) + float(q["ask"])) / 2 \
                        if q.get("bid") and q.get("ask") else None
                except (TypeError, ValueError):
                    mid = None
                dte = None
                try:
                    from datetime import date as _date
                    dte = (_date.fromisoformat(str(pos["expiry"])[:10])
                           - _date.fromisoformat(context.session)).days
                except (ValueError, TypeError, KeyError):
                    pass
                reason = exit_due(pos, dte, mid, vix)
                if reason:
                    intents.append(Intent(
                        "exit", HEDGE_UNDERLYING, qty_hint=qty,
                        price_hint=round(spot, 2) if spot else None,
                        reason="vix_hedge exit: %s occ=%s" % (reason, pos.get("occ"))))
            return intents
        if not complacent or equity <= 0 or spot <= 0:
            return intents
        hedge = pick_hedge_call(chains.get(HEDGE_UNDERLYING), quotes, spot,
                                context.session)
        if not hedge:
            return intents  # no_hedge_vehicle: fail closed, do nothing
        qty = size_contracts(equity, hedge["ask"])
        if qty <= 0:
            return intents
        intents.append(Intent(
            "enter", HEDGE_UNDERLYING, qty_hint=qty, price_hint=round(spot, 2),
            reason="vix_hedge long_call: occ=%s strike=%.2f expiry=%s dte=%d "
                   "ask=%.2f vix=%.2f pctl30=%.1f structure=long_call "
                   "dte_window=%d-%d strike_rule=nearest(1.20*spot) "
                   "brake_exempt=tail_hedge"
                   % (hedge["occ"], hedge["strike"], hedge["expiry"],
                      hedge["dte"], hedge["ask"], vix, pctl,
                      DTE_MIN, DTE_MAX)))
        return intents


def signal(bars, slice_state, context):
    return VixHedge().signal(bars, slice_state, context)
