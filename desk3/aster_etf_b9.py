"""Aster R19 ETF engine (batch 9) — faithful port of archive
source/backend/r19_etf.py selection/target logic into the v3 sleeve form.
(Separate module from desk3/aster_etf.py, which serves batch 10's sleeves;
no sleeve id is served by both.)

Source rules preserved (etf_rules.json + r19_etf.py):
- Universe: QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY.
- Score: 126-session log return log(close[-1]/close[-127]); eligibility
  requires >=252 sessions of history (minimum_valid_post_inception_sessions).
  Ties break alphabetically — archive select().
- LEADER1: 100% of gross target to the leader. EXSMH1: SMH excluded.
  CORE25 (policy ends CORE25): 25% to selected leader, 75% to QQQ.
  INTERVAL*: archive strict provider-interval selection over ALPACA +
  YAHOO scores — robust leader only if its interval low beats every
  other interval high; otherwise incumbent if still possible, else QQQ.
  Secondary eligible set must equal the primary set or the sleeve
  refuses (archive PROVIDER_ELIGIBILITY_DISAGREEMENT).
- DRIFT1 / INTERVAL_DRIFT1: selected == incumbent and shares held =>
  desired = current shares (unchanged-share holding; no intents).
- Gross target applied to NAV (slice cash + held value at last close),
  floored to whole shares, NEVER capped in the sleeve (M150 rows target
  $15,000 on the $10,000 slice; the v3 dispatcher's intent-time
  buying-power check governs execution).
- Monthly frequency: positions whose signal_month == latest bar month
  are this month's completed signal — no rebalance.
- Execution window 09:35-09:40 America/New_York (archive _calendar):
  intents only inside the window when a clock time is known (aware
  stamps converted to ET; naive stamps read as ET; date-only = ungated).
- Sell-then-settle: when any holding is above target, ONLY sell intents
  are emitted (archive MONTHLY_TARGET_SELL_THEN_SETTLE); buys follow on
  a later evaluation. No price stop/target — the designed exit is the
  next monthly selection reducing/replacing a holding.
Inputs: bars (primary ALPACA daily histories) + positions; INTERVAL rows
also declare bars_secondary (YAHOO histories). No v3 producer produces
bars_secondary yet, so INTERVAL sleeves land visibly UNFED in the
registry — never fake-fed (FIDELITY-LEDGER ASTER-B9).
"""
from __future__ import annotations
import math
from datetime import datetime, time as _time
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
UNIVERSE = ("QQQ","SPY","SMH","XLB","XLC","XLE","XLF","XLI","XLK","XLP","XLRE","XLU","XLV","XLY")
MIN_SESSIONS = 252

SPECS = {
 "aster_etf_drift1_m150": dict(policy="DRIFT1", gross=1.5, source_id="R19_ETF_DRIFT1_M150"),
 "aster_etf_exsmh1_c098": dict(policy="EXSMH1", gross=0.98, source_id="R19_ETF_EXSMH1_C098"),
 "aster_etf_exsmh1_m150": dict(policy="EXSMH1", gross=1.5, source_id="R19_ETF_EXSMH1_M150"),
 "aster_etf_interval1_c098": dict(policy="INTERVAL1", gross=0.98, source_id="R19_ETF_INTERVAL1_C098"),
 "aster_etf_interval1_m150": dict(policy="INTERVAL1", gross=1.5, source_id="R19_ETF_INTERVAL1_M150"),
 "aster_etf_interval_core25_c098": dict(policy="INTERVAL_CORE25", gross=0.98, source_id="R19_ETF_INTERVAL_CORE25_C098"),
 "aster_etf_interval_core25_m150": dict(policy="INTERVAL_CORE25", gross=1.5, source_id="R19_ETF_INTERVAL_CORE25_M150"),
 "aster_etf_interval_drift1_c098": dict(policy="INTERVAL_DRIFT1", gross=0.98, source_id="R19_ETF_INTERVAL_DRIFT1_C098"),
 "aster_etf_interval_drift1_m150": dict(policy="INTERVAL_DRIFT1", gross=1.5, source_id="R19_ETF_INTERVAL_DRIFT1_M150"),
 "aster_etf_leader1_c098": dict(policy="LEADER1", gross=0.98, source_id="R19_ETF_LEADER1_C098"),
}

# --- ENH-NAVBASE (Edge pass batch 3, 2026-10-24): binding leak = the
# NAV basis. The archive formula nav = slice cash + held value assumed
# slice cash is the sleeve's LIVE uninvested remainder. In v3 the
# snapshot carries no live per-sleeve cash: view["slice"] is the static
# config row (cash_usd = full $10,000) or absent (default $10,000), so
# every rebalance sized targets on phantom cash — gross x (capital +
# held value) instead of gross x NAV. A c098 sleeve holding $9,800
# targeted $19,404 next rebalance (ratchet fixed point
# gross*cash/(1-gross) = $490k, braked only by dispatcher slice-BP);
# m150 targets overshot proportionally and invited BP rejects.
# Cure (sleeves in ENH_NAVBASE_IDS only; aster_etf_leader1_c098 keeps
# the legacy basis exactly): NAV = slice capital (capital_usd when
# the slice row carries it, else the cash figure, which in v3 is the
# capital proxy) — held value is part of that budget, never additive.
# Switch: extra["aster_etf_b9_enh"] {"nav_basis": bool}, default ON;
# OFF restores the legacy cash+held basis exactly. Shadow control: the
# legacy NAV/desired set is computed on every treated evaluation
# (never emits) and a paired record is appended to
# extra["aster_etf_b9_exp_journal"]["records"] when served.
# Exp: ENH-NAVBASE-20261024, proof/enhance/<sleeve>.json.
EXP_ID_NAVBASE = "ENH-NAVBASE-20261024"
ENH_NAVBASE_IDS = frozenset({
 "aster_etf_exsmh1_c098", "aster_etf_exsmh1_m150",
 "aster_etf_interval1_c098", "aster_etf_interval1_m150",
 "aster_etf_interval_core25_c098", "aster_etf_interval_core25_m150"})
# DRIFT1 / INTERVAL_DRIFT1 sleeves are NOT in the set: their
# drift-retain rule (selected == incumbent and held -> no intents) and
# sell-then-settle pre-empt every NAV-sensitive emission, so the
# phantom-cash term never changes an emitted decision for them
# (fixture sweep in tests/test_edge_batch3_blockers.py) — VERIFY-ONLY
# for ENH-NAVBASE, recorded in proof/enhance/<sleeve>.json.


def _navbase_enabled(sleeve_id, extra):
    if sleeve_id not in ENH_NAVBASE_IDS:
        return False
    ov = (extra or {}).get("aster_etf_b9_enh")
    if isinstance(ov, dict) and "nav_basis" in ov:
        return bool(ov["nav_basis"])
    return True


def _navbase_paired(extra, record):
    j = (extra or {}).get("aster_etf_b9_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)


def inputs_for(sleeve_id):
    if SPECS[sleeve_id]["policy"].startswith("INTERVAL"):
        return ("bars", "bars_secondary", "positions")
    return ("bars", "positions")

PRODUCERS = ({"name": "bars", "outputs": ("bars",), "freshness_sla_s": 900},
             {"name": "broker_readback", "outputs": ("positions",), "freshness_sla_s": 900})
# NOTE: bars_secondary has NO v3 producer yet -> INTERVAL sleeves UNFED by design.

def _bars_map(view, key):
    m = view.get(key) or {}
    out = {}
    for sym in UNIVERSE:
        for k in (f"{sym}|1Day", f"{sym}|1D", sym):
            if m.get(k):
                out[sym] = m[k]; break
    return out

def _scores(barsmap, exclude=()):
    scores, closes = {}, {}
    for sym, rows in barsmap.items():
        if sym in exclude or len(rows) < MIN_SESSIONS:
            continue
        cs = [float(r["c"]) for r in rows[-MIN_SESSIONS:]]
        if any(c <= 0 for c in cs):
            continue
        closes[sym] = cs[-1]
        scores[sym] = math.log(cs[-1] / cs[-127])
    return scores, closes

def select(policy, own, other=None, incumbent=None):
    """Archive r19_etf.select, verbatim in substance."""
    if policy == "EXSMH1":
        own = {s: v for s, v in own.items() if s != "SMH"}
    if not own:
        raise ValueError("NO_ELIGIBLE_SCORE")
    if not policy.startswith("INTERVAL"):
        return min(own, key=lambda s: (-own[s], s))
    if other is None or set(other) != set(own) or "QQQ" not in own:
        raise ValueError("PROVIDER_ELIGIBILITY_DISAGREEMENT")
    bounds = {s: [min(own[s], other[s]), max(own[s], other[s])] for s in sorted(own)}
    highest_low = max(v[0] for v in bounds.values())
    possible = [s for s, v in bounds.items() if v[1] >= highest_low]
    robust = [s for s, v in bounds.items() if all(v[0] > w[1] for t, w in bounds.items() if s != t)]
    return robust[0] if len(robust) == 1 else incumbent if incumbent in possible else "QQQ"

def _in_window(view, ctx):
    raw = view.get("now") or (ctx or {}).get("now")
    if not raw:
        return True
    if isinstance(raw, datetime):
        dt = raw
    else:
        s = str(raw)
        if "T" not in s and " " not in s:
            return True
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return True
    if dt.time().isoformat() == "00:00:00":
        return True
    local = dt.astimezone(ET) if dt.tzinfo else dt
    return _time(9, 35) <= local.time() < _time(9, 40)

def evaluate(sleeve_id, view, ctx=None):
    view = view or {}; ctx = ctx or {}
    spec = SPECS[sleeve_id]; policy = spec["policy"]; gross = spec["gross"]
    if not _in_window(view, ctx):
        return []
    barsmap = _bars_map(view, "bars")
    if not barsmap:
        return []
    exclude = ("SMH",) if policy == "EXSMH1" else ()
    own, closes = _scores(barsmap, exclude=exclude)
    if not own:
        return []
    positions = [p for p in (view.get("positions") or []) if float(p.get("qty") or 0) != 0]
    held = {p["symbol"]: float(p["qty"]) for p in positions}
    incumbent = None
    for p in positions:
        if p.get("incumbent") or p.get("selected"):
            incumbent = p.get("incumbent") or p.get("selected"); break
    if incumbent is None and held:
        def _val(s):
            px = closes.get(s)
            if px is None:
                px = float(next((p.get("avg_price") or 0) for p in positions if p["symbol"] == s))
            return held[s] * px
        incumbent = max(held, key=_val)
    other = None
    if policy.startswith("INTERVAL"):
        sec = _bars_map(view, "bars_secondary")
        if not sec:
            return []
        other, _ = _scores(sec, exclude=exclude)
    try:
        selected = select(policy, own, other, incumbent)
    except ValueError:
        return []
    last_dates = [str(barsmap[s][-1].get("t", ""))[:10] for s in own if barsmap.get(s)]
    signal_month = max(last_dates)[:7] if last_dates else ""
    if positions and signal_month and all(str(p.get("signal_month") or "") == signal_month for p in positions):
        return []
    weights = {selected: 1.0}
    if policy.endswith("CORE25"):
        weights = {selected: 0.25}
        weights["QQQ"] = weights.get("QQQ", 0.0) + 0.75
    price = {}
    for s in set(held) | set(weights):
        if s in closes:
            price[s] = closes[s]
        elif barsmap.get(s):
            price[s] = float(barsmap[s][-1]["c"])
        else:
            price[s] = float(next((p.get("avg_price") or 0) for p in positions if p["symbol"] == s))
    if any(price.get(s, 0) <= 0 for s in set(held) | set(weights)):
        return []
    sl = view.get("slice") or (ctx.get("slice") if isinstance(ctx, dict) else None) or {}
    cash = float(sl.get("cash_usd", 10000.0))
    held_value = sum(q * price[s] for s, q in held.items())
    legacy_nav = cash + held_value
    _extra = {}
    if isinstance(ctx, dict):
        _extra.update(ctx.get("extra") or {})
    _extra.update(view.get("extra") or {})
    _enh = _navbase_enabled(sleeve_id, _extra)
    if _enh:
        capital = sl.get("capital_usd")
        nav = float(capital) if capital is not None else cash
    else:
        nav = legacy_nav
    if nav <= 0:
        return []
    if policy in ("DRIFT1", "INTERVAL_DRIFT1") and selected == incumbent and held.get(selected, 0) > 0:
        return []
    desired = {s: int(math.floor(weights.get(s, 0.0) * gross * nav / price[s]))
               for s in set(held) | set(weights)}
    if _enh:  # shadow control: legacy basis on the same opportunity, never emits
        _control_desired = {s: int(math.floor(weights.get(s, 0.0) * gross * legacy_nav / price[s]))
                            for s in set(held) | set(weights)}
        _navbase_paired(_extra, {"exp_id": EXP_ID_NAVBASE, "sleeve": sleeve_id,
            "treatment": "capital_nav_basis", "treatment_nav": round(nav, 2),
            "control_nav": round(legacy_nav, 2),
            "treatment_desired": desired,
            "control_desired": _control_desired})
    stamp = str(view.get("now") or ctx.get("now") or signal_month).replace(":", "").replace("-", "")[:13]
    out = []; n = 0
    def intent(kind, sym, side, qty, reason):
        nonlocal n; n += 1
        return {"intent_id": f"{sleeve_id}-{signal_month}-{stamp[-4:]}-{n}-{sym}-{side}",
                "kind": kind, "symbol": sym, "side": side, "qty": int(qty),
                "order_type": "market", "limit_price": None, "stop_price": None,
                "reason": reason, "time_in_force": "day",
                "position_intent": "buy_to_open" if kind == "entry" else "sell_to_close",
                "price_hint": float(price[sym])}
    sells = []
    for s in sorted(desired):
        if held.get(s, 0) > desired[s]:
            sells.append(intent("exit", s, "sell", held[s] - desired[s],
                                f"{spec['source_id']} monthly target sell-then-settle: {s} {int(held[s])}->{desired[s]} selected={selected}"))
    if sells:
        return sells
    for s in sorted(desired):
        if desired[s] > held.get(s, 0):
            out.append(intent("entry", s, "buy", desired[s] - int(held.get(s, 0)),
                              f"{spec['source_id']} monthly leader target: selected={selected} policy={policy} gross={gross} nav={nav:.2f}"))
    return out
