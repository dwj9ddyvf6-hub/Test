"""CONV123-REVIVAL-20261116: the CONV-123 revival basket, live.

Conversion Register CONV-123 (register[111], WATCH): an
equal-weight basket over whichever Graveyard pulse families
have fired their frozen revival rule, each family traded in
its published direction and published form (turn-of-month
window form, pairs Gatev form, PEAD drift form), on desk
paper. No family is revived early and no buried form is
edited; a family that never fires its rule never enters.

The frozen revival rule (byte-identical in
config/revival_basket_20261116.json and in each ledger's
genesis row, served by desk3/revival_producers.py): 250 active
days, or 100 events for PEAD, published-direction mean
positive at t at or above 2, read in the forward window alone
and frozen at the count. Accrual counts from Mon 2026-11-16,
so at this landing every family reads "accruing" with count 0
and the basket is flat; the sleeve is rostered live so each
family can fire the moment its count crosses, with no further
landing in between.

Sizing (the register row, byte-identical in the registry
file): one standard desk sleeve slice for the basket, split
equally across fired families; a single fired family carries
the whole slice only at half weight until a second family
fires.

Family trade forms (Lane B's port construction,
BUGLOG_2026-11-15.md GOING-LIVE-VARIATIONS-20261115):

- TOM (turn-of-month window form): long SPY on the last
  trading day of a month and the first three trading days of
  the next, flat otherwise. The desk decides "last trading
  day" on the business-day calendar (weekdays minus the
  registered holidays carried in params, defaulting to the
  overnight baskets' holiday list): a holiday that moves a
  month-end is the named approximation against the foundry's
  bar-calendar form, whose leg series is reproduced exactly
  by tom_leg_series below on the held panel.
- PAIRS (Gatev form): the rolling-z variant of Gatev,
  Goetzmann and Rouwenhorst (2006) on XOM/CVX, JPM/BAC,
  WMT/COST, MA/V, ported verbatim in substance from
  foundry/c3_graveyard.py (the same code the accrual script
  runs): log-price ratio, 252-session trailing z decided at
  the close (window spread[max(0, i-252):i], decision gate
  i >= 120), enter a convergence position at |z| above 2
  (z above 0: spread rich, short A long B), exit at |z| under
  0.5 or after 20 sessions, 10bp charged per pair on each
  entry and exit day in the leg series. The evaluator is
  stateless: it replays the served bar history through the
  construction on every evaluation, exactly as the accrual
  rebuilds its series deterministically each run, and trades
  to the replay's current position. Fewer than 130 common
  sessions served means no position (the construction cannot
  decide), never a guessed one.
- PEAD (drift form): Item 2.02 events served by the revival
  producer from the w7 ledger. Terciles are assigned by
  surprise over the whole forward event pool (the foundry
  form: terciles over the pooled events, never a partial-pool
  assignment at ledger time). An event is active from the
  session after its event session (the desk enters once the
  event close is known; the foundry measures drift from the
  event close itself, and that one-session entry lag is the
  named desk-form difference) through +21 sessions on the SPY
  bar calendar: top tercile long, bottom tercile short,
  middle flat, the family's allocation split equally across
  the active positioned events.

Entries and exits ride the standard dispatcher and journal as
ordinary Intent objects. The basket carries own_book_view, so
it trades exactly its own book: any held symbol no fired
family currently wants is exited in full, and a family's
symbols are partitioned by construction (SPY for TOM, the
eight pair names for PAIRS, event names for PEAD; the pair
names and the PEAD Focus filers do not overlap).
"""
from __future__ import annotations

import math
import statistics
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from .contract import Intent
from .overnight_baskets import (DEFAULT_HOLIDAYS_ET, _now,
                                close_ref)
from .revival_producers import pead_leg_stats  # noqa: F401

ET = ZoneInfo("America/New_York")
ET_HOLIDAYS_DEFAULT = DEFAULT_HOLIDAYS_ET
SLICE = 10000.0

PAIRS = [("XOM", "CVX"), ("JPM", "BAC"), ("WMT", "COST"),
         ("MA", "V")]
PAIR_SYMBOLS = tuple(s for p in PAIRS for s in p)
FAMILIES = ("tom", "pairs", "pead")

SPECS = {
    "revival_basket": dict(conv="CONV-123", families=FAMILIES),
}

INPUTS = ("bars", "positions", "revival_tom", "revival_pairs",
          "revival_pead")
PRODUCERS = ({"name": "bars", "outputs": ("bars",),
              "freshness_sla_s": 900},
             {"name": "broker_readback", "outputs": ("positions",),
              "freshness_sla_s": 900},
             {"name": "revival_tom", "outputs": ("revival_tom",),
              "freshness_sla_s": 400000},
             {"name": "revival_pairs",
              "outputs": ("revival_pairs",),
              "freshness_sla_s": 400000},
             {"name": "revival_pead", "outputs": ("revival_pead",),
              "freshness_sla_s": 400000})


# ------------------------------------------------------------- TOM form
def tom_active_dates(grid):
    """The foundry/accrual TOM day set over a session grid: the
    last session of each month and the first three of the next."""
    months = {}
    for d in grid:
        months.setdefault(d[:7], []).append(d)
    out = set()
    for ds in months.values():
        out.add(ds[-1])
        out.update(ds[:3])
    return out


def tom_leg_series(closes):
    """[(date, ret)] for the priced TOM days, the accrual
    script's own convention (the grid's first day has no prior
    close and is skipped; the foundry stats count it as a zero,
    the one named difference from c3_results.json)."""
    grid = sorted(closes)
    tom = tom_active_dates(grid)
    out = []
    for i, d in enumerate(grid):
        if i == 0 or d not in tom:
            continue
        out.append((d, closes[d] / closes[grid[i - 1]] - 1.0))
    return out


def _is_business_day(d, holidays):
    return d.weekday() < 5 and d.isoformat() not in holidays


def is_tom_day(d, holidays=ET_HOLIDAYS_DEFAULT):
    """Desk calendar form of the TOM window: d is a business
    day and is either among the first three business days of
    its month or the last business day of its month."""
    hol = set(holidays or ())
    if not _is_business_day(d, hol):
        return False
    first = date(d.year, d.month, 1)
    count = 0
    cur = first
    while cur <= d:
        if _is_business_day(cur, hol):
            count += 1
        cur += timedelta(days=1)
    if count <= 3:
        return True
    cur = d + timedelta(days=1)
    while cur.month == d.month:
        if _is_business_day(cur, hol):
            return False
        cur += timedelta(days=1)
    return True


# ----------------------------------------------------------- PAIRS form
def pairs_replay(closes_by_sym, grid):
    """The foundry Gatev construction, verbatim in substance
    (identical to w7d_pairs_accrual.pairs_series). Returns
    (leg, positions, trades, per_pair_pnl): leg is {date: ret}
    over active days (equal-weight mean across the four pairs,
    flat pairs contributing 0.0 on days another pair is
    active), positions is {"A/B": pos} at the grid's end,
    trades counts entries per pair."""
    pair_series = []
    positions = {}
    trades = {}
    for a, b in PAIRS:
        ca, cb = closes_by_sym.get(a, {}), closes_by_sym.get(b, {})
        common = sorted(set(ca) & set(cb) & set(grid))
        key = f"{a}/{b}"
        if len(common) < 2:
            pair_series.append({})
            positions[key] = 0
            trades[key] = 0
            continue
        la = [math.log(ca[d]) for d in common]
        lb = [math.log(cb[d]) for d in common]
        spread = [x - y for x, y in zip(la, lb)]
        rets_a = {common[i]: la[i] - la[i - 1]
                  for i in range(1, len(common))}
        rets_b = {common[i]: lb[i] - lb[i - 1]
                  for i in range(1, len(common))}
        pos, held, pnl, n_trades = 0, 0, {}, 0
        for i in range(1, len(common)):
            d = common[i]
            if pos != 0:
                pnl[d] = -pos * (rets_a[d] - rets_b[d])
                held += 1
            if i >= 120:
                win = spread[max(0, i - 252):i]
                sd = statistics.stdev(win) if len(win) >= 2 else 0.0
                z = ((spread[i - 1] - statistics.mean(win)) / sd
                     if sd > 0 else 0.0)
                if pos == 0 and abs(z) > 2:
                    pos = 1 if z > 0 else -1
                    held = 0
                    n_trades += 1
                    pnl[d] = pnl.get(d, 0.0) - 0.0010
                elif pos != 0 and (abs(z) < 0.5 or held >= 20):
                    pos = 0
                    pnl[d] = pnl.get(d, 0.0) - 0.0010
        pair_series.append(pnl)
        positions[key] = pos
        trades[key] = n_trades
    all_days = sorted({d for p in pair_series for d in p})
    leg = {}
    for d in all_days:
        if any(d in p for p in pair_series):
            leg[d] = float(statistics.mean(
                [p.get(d, 0.0) for p in pair_series]))
    per_pair = {f"{a}/{b}": pair_series[i]
                for i, (a, b) in enumerate(PAIRS)}
    return leg, positions, trades, per_pair


def pairs_desired(closes_by_sym, grid, alloc):
    """Desired signed notionals from the replay's end state:
    pos +1 (spread rich) is short A / long B, pos -1 the
    mirror; each active pair carries alloc/4, split half long
    and half short (dollar-neutral Gatev form)."""
    if len(grid) < 130:
        return {}
    _leg, positions, _trades, _per = pairs_replay(
        closes_by_sym, grid)
    out = {}
    per_pair = alloc / len(PAIRS)
    for (a, b) in PAIRS:
        pos = positions[f"{a}/{b}"]
        if pos == 0:
            continue
        half = per_pair / 2.0
        out[a] = out.get(a, 0.0) + (-half if pos > 0 else half)
        out[b] = out.get(b, 0.0) + (half if pos > 0 else -half)
    return out


# ------------------------------------------------------------ PEAD form
def pead_desired(events, calendar, today, alloc):
    """Desired signed notionals for the drift form: events
    active from the session after their event session through
    +21 sessions on the SPY calendar; terciles by surprise
    over the whole forward pool with a known surprise; top
    tercile long, bottom tercile short, allocation split
    equally across active positioned events."""
    pool = [e for e in events or []
            if e.get("surprise_bp") is not None
            and e.get("event_date")]
    if len(pool) < 3 or today not in calendar:
        return {}
    idx = {d: i for i, d in enumerate(calendar)}
    ti = idx[today]
    ranked = sorted(pool, key=lambda e: e["surprise_bp"])
    n = len(ranked)
    k = n // 3
    bottom = {id(e) for e in ranked[:k]}
    top = {id(e) for e in ranked[-k:]} if k else set()
    active = []
    for e in pool:
        ei = idx.get(e["event_date"])
        if ei is None:
            continue
        age = ti - ei
        if 1 <= age <= 21:
            if id(e) in top:
                active.append((e["symbol"], 1))
            elif id(e) in bottom:
                active.append((e["symbol"], -1))
    if not active:
        return {}
    per = alloc / len(active)
    out = {}
    for sym, sign in active:
        out[sym] = out.get(sym, 0.0) + sign * per
    return out


# --------------------------------------------------------------- engine
def _closes(view, sym):
    bars = (view or {}).get("bars") or {}
    rows = bars.get(f"{sym}|1Day") or bars.get(sym) or []
    out = {}
    for r in rows:
        t = r.get("t")
        if t is None:
            continue
        d = str(t)[:10]
        try:
            c = float(r.get("c") or 0)
        except (TypeError, ValueError):
            continue
        if c > 0:
            out[d] = c
    return out


def fired_families(view):
    out = []
    for fam in FAMILIES:
        state = (view or {}).get(f"revival_{fam}") or {}
        if state.get("revival_state") == "REVIVED":
            out.append(fam)
    return out


def family_allocations(view, cash):
    """Register sizing: the slice split equally across fired
    families; a single fired family at half weight."""
    fired = fired_families(view)
    if not fired:
        return {}
    if len(fired) == 1:
        return {fired[0]: cash * 0.5}
    return {fam: cash / len(fired) for fam in fired}


def desired_positions(sid, view, today, cash):
    """{symbol: signed notional USD} the basket wants to hold
    after this evaluation, over fired families only."""
    allocs = family_allocations(view, cash)
    desired = {}
    if "tom" in allocs:
        params = (view or {}).get("params") or {}
        holidays = params.get("holidays_et") or ET_HOLIDAYS_DEFAULT
        if is_tom_day(date.fromisoformat(today), holidays):
            desired["SPY"] = desired.get("SPY", 0.0) \
                + allocs["tom"]
    if "pairs" in allocs:
        closes = {s: _closes(view, s)
                  for s in PAIR_SYMBOLS + ("SPY",)}
        grid = sorted(closes.get("SPY") or {})
        for sym, notion in pairs_desired(closes, grid,
                                         allocs["pairs"]).items():
            desired[sym] = desired.get(sym, 0.0) + notion
    if "pead" in allocs:
        state = (view or {}).get("revival_pead") or {}
        calendar = sorted(_closes(view, "SPY"))
        for sym, notion in pead_desired(
                state.get("events"), calendar, today,
                allocs["pead"]).items():
            desired[sym] = desired.get(sym, 0.0) + notion
    return desired


def evaluate(sid, view, ctx=None):
    view = view or {}
    now = _now(view, ctx)
    if now is None:
        return []
    et = now.astimezone(ET)
    today = et.date().isoformat()
    cash = float((view.get("slice") or {}).get("cash_usd")
                 or SLICE)
    desired = desired_positions(sid, view, today, cash)
    held = {}
    for p in view.get("positions") or []:
        qty = float(p.get("qty") or 0)
        if qty != 0:
            held[p["symbol"]] = qty
    out = []
    for sym in sorted(set(desired) | set(held)):
        px = close_ref(view, sym, today)
        if px is None:
            continue  # never cross to a stale or absent price
        want_qty = (desired.get(sym, 0.0) / px) if sym in desired \
            else 0.0
        have_qty = held.get(sym, 0.0)
        delta = want_qty - have_qty
        if abs(delta) < 1e-9:
            continue

        def _exit(q):
            return Intent(
                kind="exit", symbol=sym, qty=round(abs(q), 6),
                price_hint=px,
                reason=f"{sid} exit: revival basket CONV-123 "
                       f"rebalance {sym} {today}",
                side="sell" if q > 0 else "buy",
                position_intent="sell_to_close" if q > 0
                else "buy_to_close")

        def _enter(q):
            return Intent(
                kind="enter", symbol=sym, qty=round(abs(q), 6),
                price_hint=px,
                reason=f"{sid} entry: revival basket CONV-123 "
                       f"fired family form {sym} {today}",
                side="buy" if q > 0 else "sell",
                position_intent="buy_to_open" if q > 0
                else "sell_to_open")

        if have_qty == 0:
            out.append(_enter(delta))
        elif want_qty == 0:
            out.append(_exit(have_qty))
        elif (want_qty > 0) == (have_qty > 0):
            # Same side: add on an enter, trim on a partial exit.
            out.append(_enter(delta) if delta > 0
                       else _exit(-delta))
        else:
            # Side flip: close the held side in full, then open.
            out.append(_exit(have_qty))
            out.append(_enter(want_qty))
    return out


def config_rows():
    return [{
        "id": "revival_basket",
        "module": "adapters3.revival_basket",
        "cadence_s": 300, "session": "rth",
        "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
        "bp_buffer_frac": 0.02, "flat_by_close": False,
        "flatten_time_et": None,
        "params": {},
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
    }]
