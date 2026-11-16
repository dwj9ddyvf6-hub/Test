"""Shared intraday segment engine + the CONV-88 / CONV-108 live
sleeves: SEGMENT-CONSTRUCTION-20261116 (Mon 2026-11-16 total
audit; the construction named on the GOING-LIVE-2026-11-15 rows
for CONV-80, CONV-88 and CONV-108).

Segment definitions are KG-4's own (KG-4-PHASE-DECOMPOSITION /
kg4_compute seg_bounds, minutes ET): OPEN_DRIVE 09:30-10:30,
MIDDAY 10:30-15:00, CLOSE_HOUR 15:00-16:00, OVERNIGHT prev
close -> open. A segment's return is priced at the segment
joints: the open of the 09:30 bar, the close of the 10:29 bar
(the price at 10:30), the close of the 14:59 bar (the price at
15:00) and the close of the 15:59 bar. A session is complete on
the KG-4 rule (>= 380 RTH bars stamped 09:30-15:59 ET); an
incomplete session prices NO segment (fail-closed, never a
partial-window substitute). Bars resolve from the live view's
bars:<SYM>:1Min slices (served by desk3/warm.py +
desk3/producers_g4.py since this landing) or, for the grader,
from the ONE offline 1Min cache the weekend program widened
(cache/bars/<SYM>/1Min.jsonl, DH3) — the same row shape
({t,o,h,l,c,v}, ISO stamps) in both places, so this engine is
the single segment implementation for sleeves and grader alike.

Live sleeves (paper, standard $10,000 slice, intraday only):

- ls9_midday_short (CONV-88, LS9): on a Focus name whose morning
  segment prints an up drive (OPEN_DRIVE return > 0), short the
  name for the midday segment only, flat before the close
  segment; after a down drive, no trade. Equal weight across the
  session's qualifying names. Entries emit in the window after
  the drive completes ([10:30, 11:00) ET) at the drive's closing
  joint price; covers emit at the start of the close hour
  ([15:00, 16:00) ET) at the held quantity exactly.
- b3_midday_fade_var (CONV-108, C03 midday leg; the register's
  own proposed id): short the Focus 29 basket equal weight at
  the end of the open-drive segment and cover at the start of
  the close hour, on sessions where the full basket is present
  (every name's drive segment computable); a session with any
  name missing stays flat.

Falsifiers and kill rules are registered byte-identical to
their Conversion Register rows in
config/segment_sleeves_20261116.json. No parent sleeve is
edited: CONV-88's conditioner is the entry rule of a NEW sleeve
and CONV-108 is an additional variation beside its parents, per
their register rows.
"""
from __future__ import annotations

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from .contract import Intent
from .overnight_baskets import FOCUS29

ET = ZoneInfo("America/New_York")
SLICE = 10000.0

# KG-4 segment boundaries, minutes ET (kg4_compute seg_bounds):
# OVERNIGHT (None, 570), OPEN_DRIVE (570, 630), MIDDAY (630, 900),
# CLOSE_HOUR (900, 960).
SEGMENT_BOUNDS_MIN = (("OPEN_DRIVE", 570, 630),
                      ("MIDDAY", 630, 900),
                      ("CLOSE_HOUR", 900, 960))
SEGMENTS = tuple(name for name, _a, _b in SEGMENT_BOUNDS_MIN)
RTH_START_MIN = 570
RTH_END_MIN = 960
# KG-4 day_marks completeness rule: a session is carried only
# with at least 380 RTH bars.
MIN_RTH_BARS = 380

ENTRY_START = time(10, 30)
ENTRY_END = time(11, 0)
EXIT_START = time(15, 0)
EXIT_END = time(16, 0)


def _stamp_minute_et(row):
    """(ET date iso, ET minute-of-day) for a bar row, or None."""
    t = row.get("t")
    if t is None:
        return None
    try:
        d = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    except Exception:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    et = d.astimezone(ET)
    return et.date().isoformat(), et.hour * 60 + et.minute


def session_rth_rows(rows, date):
    """The session's RTH bars (09:30-15:59 ET stamps) sorted by
    minute, from a 1Min row list in either served or cache form."""
    out = []
    for r in rows or []:
        got = _stamp_minute_et(r)
        if got is None:
            continue
        d, m = got
        if d == date and RTH_START_MIN <= m < RTH_END_MIN:
            out.append((m, r))
    out.sort(key=lambda x: x[0])
    return out


def _joint_prices(rth):
    """Segment joint prices from sorted RTH (minute, row) bars:
    open of the 09:30 bar, close of the 10:29 bar, close of the
    14:59 bar, close of the 15:59 bar. None when any joint bar is
    absent."""
    by_min = {}
    for m, r in rth:
        by_min.setdefault(m, r)
    try:
        open_px = float(by_min[570]["o"])
        drive_px = float(by_min[629]["c"])
        mid_px = float(by_min[899]["c"])
        close_px = float(by_min[959]["c"])
    except (KeyError, TypeError, ValueError):
        return None
    if min(open_px, drive_px, mid_px, close_px) <= 0:
        return None
    return {"open": open_px, "drive_end": drive_px,
            "midday_end": mid_px, "close": close_px}


def segment_marks(rows, date, prev_close=None):
    """{segment: decimal return} for one session on the KG-4
    basis, or None when the session is incomplete (< 380 RTH
    bars or a missing joint). OVERNIGHT is present only when
    prev_close (the prior session's close) is supplied."""
    rth = session_rth_rows(rows, date)
    if len(rth) < MIN_RTH_BARS:
        return None
    joints = _joint_prices(rth)
    if joints is None:
        return None
    out = {"OPEN_DRIVE": joints["drive_end"] / joints["open"] - 1,
           "MIDDAY": joints["midday_end"] / joints["drive_end"] - 1,
           "CLOSE_HOUR": joints["close"] / joints["midday_end"] - 1}
    if prev_close:
        out["OVERNIGHT"] = joints["open"] / float(prev_close) - 1
    return out


def drive_marks(rows, date):
    """(open_px, drive_end_px, drive_return) once the open drive
    has completed (bars through the 10:29 stamp present), else
    None. This is the live entry-time read: the full-session
    completeness rule cannot apply before the session ends, so
    the drive read requires exactly the drive's own bars
    (09:30 through 10:29 stamps, >= 55 of the 60)."""
    rth = session_rth_rows(rows, date)
    drive = [(m, r) for m, r in rth if m < 630]
    if len(drive) < 55:
        return None
    by_min = {}
    for m, r in drive:
        by_min.setdefault(m, r)
    try:
        open_px = float(by_min[570]["o"])
        end_px = float(by_min[629]["c"])
    except (KeyError, TypeError, ValueError):
        return None
    if open_px <= 0 or end_px <= 0:
        return None
    return open_px, end_px, end_px / open_px - 1


# ------------------------------------------------------------ sleeves
SPECS = {
    "ls9_midday_short": dict(conv="CONV-88", conditioned=True),
    "b3_midday_fade_var": dict(conv="CONV-108", conditioned=False),
}

INPUTS = tuple(["bars", "bars_1min"]
               + [f"bars:{s}:1Min" for s in FOCUS29]
               + ["positions"])
PRODUCERS = ({"name": "bars", "outputs": ("bars",),
              "freshness_sla_s": 900},
             {"name": "broker_readback", "outputs": ("positions",),
              "freshness_sla_s": 900})


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


def _rows(view, sym):
    bars = (view or {}).get("bars") or {}
    return bars.get(f"{sym}|1Min") or []


def evaluate(sid, view, ctx=None):
    view = view or {}
    spec = SPECS[sid]
    now = _now(view, ctx)
    if now is None:
        return []
    et = now.astimezone(ET)
    today = et.date().isoformat()
    clock = et.time()
    held = [p for p in (view.get("positions") or [])
            if p.get("symbol") in FOCUS29
            and float(p.get("qty") or 0) < 0]

    # Covers first, at the start of the close hour: every held
    # short covers at its held quantity, so the sleeve is flat
    # before the close segment, per both register rows.
    if held:
        if not (EXIT_START <= clock < EXIT_END):
            return []
        out = []
        for p in sorted(held, key=lambda r: r["symbol"]):
            sym = p["symbol"]
            rth = session_rth_rows(_rows(view, sym), today)
            px = None
            if rth:
                try:
                    px = float(rth[-1][1].get("c") or 0) or None
                except (TypeError, ValueError):
                    px = None
            out.append(Intent(
                kind="exit", symbol=sym,
                qty=abs(float(p["qty"])), price_hint=px,
                reason=f"{sid} cover: midday segment end "
                       f"{spec['conv']} {today}",
                side="buy", position_intent="buy_to_close"))
        return out

    # Entries, after the open drive completes and before the
    # entry window closes, priced at the drive's closing joint.
    if not (ENTRY_START <= clock < ENTRY_END):
        return []
    drives = {}
    for sym in FOCUS29:
        dm = drive_marks(_rows(view, sym), today)
        if dm is not None:
            drives[sym] = dm
    if spec["conditioned"]:
        # CONV-88: only names whose drive printed UP qualify;
        # after a down drive, no trade (the control is the
        # grader's/log's business, never an entry here).
        names = [(s, dm[1]) for s, dm in sorted(drives.items())
                 if dm[2] > 0]
    else:
        # CONV-108: the full basket must be present, per its row.
        if len(drives) < len(FOCUS29):
            return []
        names = [(s, drives[s][1]) for s in FOCUS29]
    if not names:
        return []
    cash = float((view.get("slice") or {}).get("cash_usd")
                 or SLICE)
    per_name = cash / len(names)
    out = []
    for sym, px in names:
        qty = round(per_name / px, 6)
        if qty <= 0:
            continue
        out.append(Intent(
            kind="enter", symbol=sym, qty=qty, price_hint=px,
            reason=f"{sid} entry: short midday segment "
                   f"{spec['conv']} {len(names)} names {today}",
            side="sell", position_intent="sell_to_open"))
    return out


def config_rows():
    rows = []
    for sid in SPECS:
        rows.append({
            "id": sid, "module": f"adapters3.{sid}",
            "cadence_s": 300, "session": "rth",
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "bp_buffer_frac": 0.02, "flat_by_close": True,
            "flatten_time_et": "15:55",
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
        })
    return rows
