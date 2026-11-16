"""Overnight basket sleeves, live: GOING-LIVE-BASKETS-20261115.

Owner ruling Sun 2026-11-15 22:35 ET: "no shadow sleeves allowed
they have to be live". This module is the one overnight basket
engine for the Conversion Program's overnight family, rostered
as live paper sleeves on the standard $10,000 slice:

- overnight_focus29 (CONV-01): the Focus 29 basket, equal weight
  over the names present that night, at least the registered
  10-name floor or flat that night.
- overnight_energy8 (CONV-02): FLNC, EOSE, FCEL, BE, OKLO, VST,
  CEG, XLE; at least 6 of 8 present or flat that night.
- overnight_basket8 (CONV-03): SMH, SOXX, SNDK, MU, CRDO, ALAB,
  AAOI, AXTI; at least 6 of 8 present or flat that night.
- overnight_semis12 (CONV-04): SMH, SOXX, NVDA, AVGO, AMD, MRVL,
  ARM, TSM, AMAT, MU, SNDK, WDC; at least 9 of 12 present or
  flat that night.
- overnight_focus29_ex_rklb (CONV-163): the Focus 29 basket
  minus RKLB, equal weight over the survivors, same engine,
  exclusion variant; the CONV-01 basket is never edited into
  it.

Components riding CONV-01's live form (no separate sleeves;
registered in config/overnight_baskets_20261115.json): CONV-05
(the carry5 print core: SNDK, CRWV, RKLB, NVDA, AMD are members
of overnight_focus29 at basket weight), CONV-06 (the per-name
clearers ride as basket members), CONV-119 (FCEL as a member
only, never standalone).

Form, each session: long the basket equal weight at the close,
exit at the next session's open, flat every morning after the
exit. Entries emit only inside the closing window (15:50 to
16:00 ET) and only for names whose bars resolve for that
session (a 1Day bar dated today, or a 1Hour bar dated today);
a name whose bars are unavailable that night is dropped and
never crossed to a stale price, and a basket below its floor
stays flat that night. Exits emit only inside the morning
window (09:30 to 10:00 ET) for the sleeve's own held names
(the sleeves carry own_book_view, so each basket exits exactly
its own book, never another sleeve's position in the same
name), at the held quantity, so the sleeve is flat after the
open. Entries and exits ride the standard dispatcher and
journal as ordinary Intent objects, exactly like every other
desk sleeve.

BASIS NOTE (printed here and in the BUGLOG entry, per the
landing order): auction prints are the grading basis (the
falsifier tracker grades prints); the desk's paper execution
form is the dispatcher fill at the close and open bars, which
is the faithful live form available on this desk tonight. No
auction-print fill is claimed anywhere in this landing.

Falsifiers and kill rules for every rostered basket and every
riding component are registered byte-identical to their
Conversion Register rows in
config/overnight_baskets_20261115.json.

Blocked rows, named in the same registry file: CONV-104 (the
anti-Focus residue basket) is BLOCKED because its membership
rule needs the night-study panel as a desk-readable source
and no such source exists on the desk (the falsifier tracker
carries only its hardcoded carry5 and nonfocus18 populations;
the AA119 residue panel is enumerated in no desk-readable
file). CONV-86 (the LS7 called-names basket) is BLOCKED
because the nightly forecast-ledger plus bars join produces
no artifact the desk can read (no file in the book or the
desk state carries the night's qualifying oversold
joint-below calls; the only join record is the historical
6-row computation in pass2/LEAD-STACKING.md). Neither blocked
row is built on an invented list or a second join.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from .contract import Intent

ET = ZoneInfo("America/New_York")
SLICE = 10000.0

# The Focus 29 set: the Focus 30 set minus SIVE (unmeasurable
# on book routes), in the falsifier accrual's own order
# (keepgoing2/wave4/v1_shadow_accrual.py FOCUS).
FOCUS29 = ["SMH", "SOXX", "NVDA", "AVGO", "AMD", "MRVL", "ARM",
           "TSM", "AMAT", "MU", "SNDK", "WDC", "AAOI", "COHR",
           "LITE", "CRDO", "ALAB", "AXTI", "CRWV", "PLTR",
           "RKLB", "FLNC", "EOSE", "FCEL", "BE", "OKLO", "VST",
           "CEG", "XLE"]

ENERGY8 = ["FLNC", "EOSE", "FCEL", "BE", "OKLO", "VST", "CEG",
           "XLE"]
BASKET8 = ["SMH", "SOXX", "SNDK", "MU", "CRDO", "ALAB", "AAOI",
           "AXTI"]
SEMIS12 = ["SMH", "SOXX", "NVDA", "AVGO", "AMD", "MRVL", "ARM",
           "TSM", "AMAT", "MU", "SNDK", "WDC"]

SPECS = {
    "overnight_focus29": dict(
        conv="CONV-01", names=tuple(FOCUS29), min_names=10),
    "overnight_energy8": dict(
        conv="CONV-02", names=tuple(ENERGY8), min_names=6),
    "overnight_basket8": dict(
        conv="CONV-03", names=tuple(BASKET8), min_names=6),
    "overnight_semis12": dict(
        conv="CONV-04", names=tuple(SEMIS12), min_names=9),
    "overnight_focus29_ex_rklb": dict(
        conv="CONV-163",
        names=tuple(s for s in FOCUS29 if s != "RKLB"),
        min_names=10),
}

INPUTS = ("bars", "positions")
PRODUCERS = ({"name": "bars", "outputs": ("bars",),
              "freshness_sla_s": 900},
             {"name": "broker_readback", "outputs": ("positions",),
              "freshness_sla_s": 900})

ENTRY_START = time(15, 50)
ENTRY_END = time(16, 0)
EXIT_START = time(9, 30)
EXIT_END = time(10, 0)

# OVERNIGHT-AUCTION-20261116 (spec ON-PAPER-IMPLEMENTATION-SPEC-
# 2026-11-15 sections 4.3, 5, 6): the auction form of this same
# engine. It engages ONLY when the sleeve's params carry
# auction_form (staged activation: the post-close config step
# named in BUGLOG_2026-11-16.md); without that key every basket
# evaluates in the bar-price form above, byte-identical to the
# pre-cure engine. In auction form: entries are market orders
# with tif "cls" inside [close minus 20 minutes, close minus 10
# minutes) — 15:40:00 to 15:49:59 ET on a regular session, the
# 15:50 broker cutoff carried as auction_deadline_et — sized in
# WHOLE shares by the spec section 6.2 algorithm against 98
# percent of the slice cash (the dispatcher's 2 percent buying
# power buffer stays inside the slice); exits are market orders
# with tif "opg" for the held quantity exactly, in the primary
# window 19:05 to 19:30 ET on the entry evening (queued by the
# broker for the next session's opening auction) or the
# fallback window 08:00 to 09:27:59 ET the next session when no
# opg order for the name is resting. No other order shape
# exists in this form: a name that cannot use the auction is
# dropped by the same resolution rule as the bar form, never
# crossed. Stop line E (spec section 12): a plan investing
# under 70 percent of its budget is stood down before
# submission.
AUCTION_BUDGET_FRAC = 0.98
AUCTION_MIN_INVESTED_FRAC = 0.70
MOO_PRIMARY_START = time(19, 5)
MOO_PRIMARY_END = time(19, 30)
MOO_FALLBACK_START = time(8, 0)
MOO_FALLBACK_END = time(9, 28)
DEFAULT_HOLIDAYS_ET = ("2026-11-26", "2026-12-25", "2027-01-01",
                       "2027-01-18")
DEFAULT_EARLY_CLOSES_ET = {"2026-11-27": "13:00",
                           "2026-12-24": "13:00"}


def _auction_params(view, ctx):
    for src in ((ctx or {}), (view or {})):
        p = (src or {}).get("params") or {}
        if "auction_form" in p:
            return p
    return {}


def _et_offset(date_str):
    d = datetime.fromisoformat(date_str).date()
    off = datetime(d.year, d.month, d.day, 12, tzinfo=ET).utcoffset()
    total = int(off.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return f"{sign}{total // 3600:02d}:{total % 3600 // 60:02d}"


def _next_session(date_str, holidays):
    d = datetime.fromisoformat(date_str).date() + timedelta(days=1)
    while d.weekday() >= 5 or d.isoformat() in holidays:
        d += timedelta(days=1)
    return d.isoformat()


def auction_plan(present, budget, min_names):
    """Spec section 6.2, deterministic: one share for every
    eligible name, then top up the largest dollar deficit toward
    the equal-weight target while shares fit the budget. The
    budget edge drops names in descending price order (ties by
    symbol, ascending) until one share each fits. Returns a dict
    with the plan ({symbol: whole qty}), its cost, the budget
    drops, the invested fraction, and stand_down (None, "floor"
    or "invested_fraction")."""
    E = list(present)
    dropped = []
    while E and sum(p for _, p in E) > budget:
        victim = sorted(E, key=lambda r: (-r[1], r[0]))[0]
        E.remove(victim)
        dropped.append((victim[0],
                        "budget_cannot_cover_one_share_each"))
    if len(E) < min_names:
        return {"plan": {}, "cost": 0.0, "dropped": dropped,
                "invested_fraction": 0.0, "stand_down": "floor"}
    target = budget / len(E)
    prices = dict(E)
    qty = {s: 1 for s, _ in E}
    spent = sum(p for _, p in E)
    while True:
        cands = sorted(((target - qty[s] * p, s) for s, p in E
                        if qty[s] * p < target),
                       key=lambda r: (-r[0], r[1]))
        progressed = False
        for _deficit, s in cands:
            if spent + prices[s] <= budget:
                qty[s] += 1
                spent += prices[s]
                progressed = True
                break
        if not progressed:
            break
    frac = spent / budget if budget > 0 else 0.0
    if frac < AUCTION_MIN_INVESTED_FRAC:
        return {"plan": {}, "cost": spent, "dropped": dropped,
                "invested_fraction": frac,
                "stand_down": "invested_fraction"}
    return {"plan": qty, "cost": spent, "dropped": dropped,
            "invested_fraction": frac, "stand_down": None}


def _evaluate_auction(sid, view, ctx, spec, et, today, clock,
                      held):
    params = _auction_params(view, ctx)
    holidays = set(params.get("holidays_et")
                   or DEFAULT_HOLIDAYS_ET)
    early = params.get("early_closes_et") or DEFAULT_EARLY_CLOSES_ET
    if today in holidays:
        return []
    if held:
        in_primary = MOO_PRIMARY_START <= clock < MOO_PRIMARY_END
        in_fallback = MOO_FALLBACK_START <= clock < MOO_FALLBACK_END
        if not (in_primary or in_fallback):
            return []
        resting = set()
        if in_fallback:
            resting = {o.get("symbol")
                       for o in (view.get("open_orders") or [])
                       if o.get("time_in_force") == "opg"
                       and o.get("side") == "sell"}
        exit_date = today if in_fallback else _next_session(
            today, holidays)
        deadline = f"{exit_date}T09:28:00{_et_offset(exit_date)}"
        out = []
        for p in sorted(held, key=lambda r: r["symbol"]):
            sym = p["symbol"]
            if sym in resting:
                continue
            out.append(Intent(
                kind="exit", symbol=sym,
                qty=abs(float(p["qty"])),
                price_hint=_exit_price(view, sym, today),
                reason=f"{sid} auction exit: overnight basket "
                       f"MOO {spec['conv']} entry session open "
                       f"auction {exit_date}",
                side="sell", position_intent="sell_to_close",
                order_type="market", time_in_force="opg",
                auction_deadline_et=deadline))
        return out
    close_s = early.get(today)
    if close_s:
        hh, mm = (int(x) for x in str(close_s).split(":"))
        close_t = time(hh, mm)
    else:
        close_t = time(16, 0)
    base = datetime(2000, 1, 1, close_t.hour, close_t.minute)
    win_start = (base - timedelta(minutes=20)).time()
    win_end = (base - timedelta(minutes=10)).time()
    if not (win_start <= clock < win_end):
        return []
    present, _enters = basket_plan(sid, view, today)
    cash = float((view.get("slice") or {}).get("cash_usd")
                 or SLICE)
    plan = auction_plan(present, cash * AUCTION_BUDGET_FRAC,
                        spec["min_names"])
    if plan["stand_down"]:
        return []
    deadline = (f"{today}T{win_end.isoformat()}"
                f"{_et_offset(today)}")
    prices = dict(present)
    out = []
    for sym in sorted(plan["plan"]):
        out.append(Intent(
            kind="enter", symbol=sym, qty=plan["plan"][sym],
            price_hint=prices[sym],
            reason=f"{sid} auction entry: overnight basket MOC "
                   f"{spec['conv']} {len(plan['plan'])} names "
                   f"{today}",
            side="buy", position_intent="buy_to_open",
            order_type="market", time_in_force="cls",
            auction_deadline_et=deadline))
    return out


def _now(view, ctx=None):
    raw = (view or {}).get("now") or (view or {}).get("now_iso")
    if raw is None and isinstance(ctx, dict):
        raw = ctx.get("now")
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), timezone.utc)
    try:
        d = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except Exception:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _bar_date(row):
    t = _now({"now": row.get("t")}) if row.get("t") is not None else None
    if t is None:
        return None
    return t.astimezone(ET).date().isoformat()


def _rows(view, sym, tf):
    bars = (view or {}).get("bars") or {}
    if tf == "1Day":
        return bars.get(f"{sym}|1Day") or bars.get(sym) or []
    return bars.get(f"{sym}|{tf}") or []


def close_ref(view, sym, today):
    """Tonight's close reference for one name, or None when the
    name does not resolve for this session: a 1Day bar dated
    today wins; else the last 1Hour bar dated today. A name
    whose newest bar is stale (dated before today) never
    resolves, so it is dropped rather than crossed to a stale
    price."""
    daily = _rows(view, sym, "1Day")
    if daily and _bar_date(daily[-1]) == today:
        c = float(daily[-1].get("c") or 0)
        return c if c > 0 else None
    hourly = [r for r in _rows(view, sym, "1Hour")
              if _bar_date(r) == today]
    if hourly:
        c = float(hourly[-1].get("c") or 0)
        return c if c > 0 else None
    return None


def resolved_names(view, names, today):
    """[(symbol, close)] for the names resolving tonight, in
    basket order. This is the live-view resolution proof surface
    the blockers and the landing census read."""
    out = []
    for sym in names:
        px = close_ref(view, sym, today)
        if px is not None:
            out.append((sym, px))
    return out


def _exit_price(view, sym, today):
    daily = _rows(view, sym, "1Day")
    if daily and _bar_date(daily[-1]) == today:
        o = float(daily[-1].get("o") or 0)
        if o > 0:
            return o
    hourly = [r for r in _rows(view, sym, "1Hour")
              if _bar_date(r) == today]
    if hourly:
        o = float(hourly[0].get("o") or 0)
        if o > 0:
            return o
    if daily:
        c = float(daily[-1].get("c") or 0)
        if c > 0:
            return c
    return None


def basket_plan(sid, view, today):
    """(present, enters) for the entry leg: present is the
    resolved [(symbol, close)] list; enters is True only when
    the resolved count meets the basket's registered floor."""
    spec = SPECS[sid]
    present = resolved_names(view, spec["names"], today)
    return present, len(present) >= spec["min_names"]


def evaluate(sid, view, ctx=None):
    view = view or {}
    spec = SPECS[sid]
    now = _now(view, ctx)
    if now is None:
        return []
    et = now.astimezone(ET)
    today = et.date().isoformat()
    clock = et.time()
    names = set(spec["names"])
    held = [p for p in (view.get("positions") or [])
            if p.get("symbol") in names
            and float(p.get("qty") or 0) > 0]

    # OVERNIGHT-AUCTION-20261116: the auction form, engaged only
    # by the sleeve's auction_form param (staged activation; no
    # live row carries it in this landing, so the bar-price form
    # below runs today's session untouched).
    if _auction_params(view, ctx).get("auction_form"):
        return _evaluate_auction(sid, view, ctx, spec, et, today,
                                 clock, held)

    # Exits first, morning window only: every held name exits at
    # the open at its held quantity, so the sleeve is flat
    # every morning after the exit.
    if held:
        if not (EXIT_START <= clock < EXIT_END):
            return []
        out = []
        for p in sorted(held, key=lambda r: r["symbol"]):
            sym = p["symbol"]
            qty = abs(float(p["qty"]))
            px = _exit_price(view, sym, today)
            out.append(Intent(
                kind="exit", symbol=sym, qty=qty,
                price_hint=px,
                reason=f"{sid} exit: overnight basket open exit "
                       f"{spec['conv']} {today}",
                side="sell", position_intent="sell_to_close"))
        return out

    # Entries, closing window only, floor-gated, equal weight
    # over the names present tonight on the standard slice.
    if not (ENTRY_START <= clock < ENTRY_END):
        return []
    present, enters = basket_plan(sid, view, today)
    if not enters:
        return []
    cash = float((view.get("slice") or {}).get("cash_usd")
                 or SLICE)
    per_name = cash / len(present)
    out = []
    for sym, px in present:
        qty = round(per_name / px, 6)
        if qty <= 0:
            continue
        out.append(Intent(
            kind="enter", symbol=sym, qty=qty, price_hint=px,
            reason=f"{sid} entry: overnight basket close entry "
                   f"{spec['conv']} equal weight "
                   f"{len(present)} names {today}",
            side="buy", position_intent="buy_to_open"))
    return out


def config_rows():
    rows = []
    for sid in SPECS:
        rows.append({
            "id": sid, "module": f"adapters3.{sid}",
            "cadence_s": 300, "session": "24h",
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "bp_buffer_frac": 0.02, "flat_by_close": False,
            "flatten_time_et": None,
            # OVERNIGHT-AUCTION-20261116: the ACTIVATION form of
            # the row (spec section 4.1/4.3): session "24h" so the
            # 19:05 ET MOO step is evaluated at all, and the
            # auction_form param that engages the engine's
            # auction form. The live config/sleeves.json rows are
            # NOT rewritten by this landing (mid-session); the
            # coordinator applies these rows post-close as the
            # staged activation named in the BUGLOG.
            "params": {"auction_form": True,
                       "holidays_et": list(DEFAULT_HOLIDAYS_ET),
                       "early_closes_et":
                           dict(DEFAULT_EARLY_CLOSES_ET)},
            "costs": {"fill_timing": "next_bar",
                      "commission_per_share": 0.0,
                      "commission_bps": 0.0,
                      "min_commission_per_order": 0.0,
                      "slippage_model": "forecast_per_name",
                      "slippage_bps": None},
            "rebalance_policy": {
                "frequency": "signal_driven", "drift_threshold": None,
                "drift_type": None, "partial_rebalance": False,
                "tracking_error_threshold": None,
                "tracking_error_window_days": None,
                "max_annual_turnover": None,
                "signal_change_rebalance": True,
                "execution_timing": "on_evaluation",
                "enforcement": "declared_not_enforced",
                "status": "ESCALATED_FOR_RULING",
                "enforced_dimensions": []},
            "inputs": list(INPUTS), "parked": False,
            "own_book_view": True,
        })
    return rows
