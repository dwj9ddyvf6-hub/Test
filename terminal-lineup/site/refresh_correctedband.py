#!/usr/bin/env python3
"""Refresh the Corrected Band Engine (Forecast Engine 1).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   Calibration studies on record, grade B: AD-55 and AD-56 in the
   terminal-lineup evidence record (summarised in
   forecast30-inventory.md), plus V1 (HAR realised-vol forecasting,
   grade A) and V3 (VIX backwardation precedes bigger moves, grade B).
   The live record of this engine itself: none yet; it starts here.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Band spine: HAR realised-vol forecast x sqrt(h/252) x k_h, with
     k_1 = 0.87, k_5 = 0.88, k_21 = 0.91 (AD-56: k fitted on
     2010-2019, read once on 2020+; 68.7/68.0/69.8 percent coverage
     at h = 1/5/21; SPY only for the k values in that study).
   - HAR recipe (desk reconstruction; the study's exact recipe file
     is not on this box, so exact replication is NOT claimed):
     daily log returns on closes; squared-return components over the
     last 1, last 5 and last 22 sessions ending at the as-of close;
     forecast daily variance = the equal-weight mean of the three
     components; annualised vol = sqrt(252 x forecast variance).
     Warm-up: a band is computed only where at least 22 prior
     returns exist.
   - Band levels 50/68/81/95 percent: only the 68 percent band is
     calibrated by AD-56. The other levels are a desk reconstruction:
     each level's half-width = the 68 percent half-width scaled by
     z(level)/z(68) using normal quantiles z = 0.6744898 (50%),
     0.9944579 (68%), 1.3105791 (81%), 1.9599640 (95%).
   - VIX regime input: the published VIX/15.87 construction enters
     ONLY as a regime reading, scaled by 0.73, the desk's single
     fixed choice inside AD-56's measured range 0.71-0.75 for the
     factor a VIX-based band would need. It never sets a band width
     and is never called a 1-sigma band anywhere. The lineage
     note and the page state the VIX store's actual last date at
     issuance (vix_lineage_note below, cure 2026-10-31): the
     reading ships as a named stale state only when that date
     precedes the as-of session, as it did at first build, when
     the newest VIX close on record (2026-10-21) was two sessions
     older than the live as-of close (2026-10-23).
   - Backwardation widening: backwardation is defined as VIX above
     VIX3M (the only definition on record, AD-59). When, and only
     when, that state is known to hold, the 95 percent band alone is
     widened by a fixed factor of 1.25 (its half-width multiplied by
     1.25). Rationale, registered before computing: the corpus names
     no factor, so the desk fixes the smallest round step that
     clearly separates a stressed tail band from the ordinary one, a
     quarter wider, and stakes the 95 percent coverage figures on
     it. (Hookup addendum, 2026-10-30: a VIX3M series is now on
     record beside the VIX file, kept current daily by
     site/capture_vix_daily.py, and the live state below is read
     from it on the freshest shared date at or before the as-of
     session; the walk-forward history study keeps its published
     no-widening basis.)
   - Prices: bands are close x (1 -/+ half-fraction), rounded to
     cents; the rounded prices are what the ledger carries and what
     the history study grades.
   - Panel: the only index panel on record on this box is
     ~/workspace/morgue/data_cache/board_bt_bars.json (SPY and QQQ,
     399 sessions, 2025-03-25 to 2026-10-23). The 2010-2026 span in
     the calibration studies exists only as study summaries, not as
     computable data here, so the history study below runs on the
     399-session panel and says so. Nothing is claimed for 2010-2026
     from this script.

3. NON-CLAIMS
   - No direction is forecast, ever. No claim about any single name
     beyond SPY and QQQ. No exact replication of the AD-56 study
     recipe. The history study is a backfill computed today, not a
     live record; it ledgers nothing. The VIX reading is not a
     1-sigma band. Backwardation widening is not corpus-measured.

=====================================================================
Behaviour: walk-forward history study over the panel (each band from
closes strictly up to its base close only; nothing from the study is
written to the live ledger), then today's live bands ledgered through
forecast/ledger.py append_forecast (never hand-edited), then
data.json written from the panel plus figures recomputed from the
ledger alone. Idempotent: rerunning with the same panel appends
nothing (the ledger dedupes identical forecasts) and rewrites the
same data.json. Fails closed on any count disagreement.
"""

import json

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None
import math
import os
import sys
from datetime import date, timedelta
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/board_bt_bars.json")
VIX_PATH = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source/yahoo-vix-daily.json")
VIX3M_PATH = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source/yahoo-vix3m-daily.json")
OUT_PATH = os.path.join(HERE, "corrected-band", "data.json")

sys.path.insert(0, LINEUP)
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402

try:
    import engine_adaptations as _ea
except ImportError:  # pragma: no cover
    _ea = None

ENGINE_ID = "engine_01"
SYMBOLS = ("SPY", "QQQ")
NAMES = {"SPY": "SPY (the big S&P 500 fund)",
         "QQQ": "QQQ (the big Nasdaq-100 fund)"}
K_BY_H = {1: 0.87, 5: 0.88, 21: 0.91}
LEVELS = (50, 68, 81, 95)
VIX_FACTOR = 0.73            # fixed choice inside AD-56's 0.71-0.75
BACKWARDATION_FACTOR = 1.25  # pre-registered above; 95% band only
WARMUP = 22                  # prior returns required
CLAIM_TARGET = 120

_ND = NormalDist()
Z_BY_LEVEL = {p: _ND.inv_cdf(0.5 + p / 200.0) for p in LEVELS}


def fail(msg):
    print(f"Corrected Band refresh: {msg}", file=sys.stderr)
    return 1


def next_sessions(after_iso, count):
    """The next `count` weekdays (Mon-Fri) after the given date."""
    d = date.fromisoformat(after_iso)
    out = []
    while len(out) < count:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


def har_annualised_vol(sq_returns, i):
    """sq_returns[j] is the squared log return into closes[j+1].
    Forecast at base close index i uses returns sq[i-22:i] only."""
    daily = sq_returns[i - 1]
    weekly = sum(sq_returns[i - 5:i]) / 5.0
    monthly = sum(sq_returns[i - WARMUP:i]) / WARMUP
    return math.sqrt(252.0 * (daily + weekly + monthly) / 3.0)


def bands_for(close, vol, h, backwardation_known_true, guard=None):
    """{level: (lower, upper)} in rounded explicit prices. When
    an FE12 session quality guard (DEEP-PASS 3.2 item 10) is
    recorded, every half width is multiplied by the guard's
    band widen factor before rounding; a not_recorded guard
    (the factor is 1.0) leaves the bands exactly as before."""
    widen = 1.0
    if guard is not None and guard.get("deterioration") is not None:
        widen = float(guard["band_widen_factor"])
    half68 = vol * math.sqrt(h / 252.0) * K_BY_H[h] * widen
    out = {}
    for level in LEVELS:
        half = half68 * Z_BY_LEVEL[level] / Z_BY_LEVEL[68]
        if level == 95 and backwardation_known_true:
            half *= BACKWARDATION_FACTOR
        out[level] = (round(close * (1.0 - half), 2),
                      round(close * (1.0 + half), 2),
                      round(half * 100.0, 4))
    return out


SESSION_QUALITY_PATH = os.path.join(
    HERE, "corrected-band", "session_quality_record.json")


def session_quality_guard(as_of=None):
    """The FE12 guard for this refresh's session. The session
    quality record (build_session_quality.py, RC-23 cure
    2026-10-30) supplies the two inputs intraday bars carry:
    realised_vol_z and volume_concentration, read for the
    record's freshest session when it is this refresh's
    session. spread_z and depth_drop_z are in no store this
    terminal holds (no equity quote store, no order book
    store), so they stay unsupplied and the guard names them
    missing itself; its state is partial, never upgraded."""
    if _ea is None:
        return {"state": "not_recorded", "deterioration": None,
                "missing": list(_ea_inputs()), "inputs_used": [],
                "band_widen_factor": 1.0, "tripped": False}
    inputs = {}
    try:
        with open(SESSION_QUALITY_PATH, encoding="utf-8") as fh:
            record = json.load(fh)
        if record.get("freshest_session") == as_of:
            inputs = record.get("freshest_inputs") or {}
    except (OSError, ValueError):
        inputs = {}
    return _ea.fe12_session_quality_guard(
        spread_z=inputs.get("spread_z"),
        depth_drop_z=inputs.get("depth_drop_z"),
        volume_concentration=inputs.get("volume_concentration"),
        realised_vol_z=inputs.get("realised_vol_z"))


def _ea_inputs():
    return ("spread_z", "depth_drop_z", "volume_concentration",
            "realised_vol_z")


def vix_lineage_note(vix_last_date, as_of):
    """The ledger lineage sentence for the VIX regime reading
    (cure VIX-LINEAGE-NOTE-20261031). The sentence is built from
    the VIX store's actual last date at issuance, and the stale
    claim is made only when that date precedes the as-of session:
    earlier issuances carried a hardcoded stale claim beside a
    templated date, so a batch issued after the daily capture
    lane (site/capture_vix_daily.py) had advanced the store still
    called its fresh reading stale, and batches issued before
    the lane existed disagreed with the page republished after
    it. One construction, stated from the store, either way."""
    if vix_last_date is None:
        return ("No volatility-index reading is on record for "
                "this forecast; it changed no band.")
    if vix_last_date < as_of:
        return (f"The volatility-index reading on record ends "
                f"{vix_last_date}; it is a stale regime reading "
                f"for this forecast and changed no band.")
    return (f"The volatility-index reading on record ends "
            f"{vix_last_date}; it is the freshest reading on "
            f"record for this forecast and changed no band.")


def load_vix():
    return load_vix_series(VIX_PATH)


def load_vix_series(path):
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    result = doc["chart"]["result"][0]
    from datetime import datetime, timezone
    out = {}
    for ts, close in zip(result["timestamp"],
                         result["indicators"]["quote"][0]["close"]):
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        out[day.isoformat()] = float(close)
    return out


def build():
    for path in (PANEL_PATH, VIX_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)

    series = {}
    for sym in SYMBOLS:
        rows = panel.get(sym) or []
        if len(rows) != len(panel[SYMBOLS[0]]):
            return fail(f"panel count disagreement: {sym} has "
                        f"{len(rows)} sessions, expected "
                        f"{len(panel[SYMBOLS[0]])} (the panel's own "
                        f"session count; cure G2 2026-10-29)")
        dates = [r[0] for r in rows]
        closes = [float(r[4]) for r in rows]
        if dates != sorted(dates) or len(set(dates)) != len(dates):
            return fail(f"panel dates for {sym} are not a clean "
                        f"increasing session list")
        series[sym] = (dates, closes)
    span = (series["SPY"][0][0], series["SPY"][0][-1])
    if (series["QQQ"][0][0], series["QQQ"][0][-1]) != span:
        return fail("panel span disagreement between SPY and QQQ")
    as_of = span[1]

    vix = load_vix()
    vix_last_date = max(vix) if vix else None
    # Backwardation (AD-59: VIX above VIX3M), hookup cure
    # 2026-10-30: the VIX3M series is now on record beside the VIX
    # file (site/capture_vix_daily.py keeps both current daily).
    # The state is read on the freshest date at or before the as-of
    # session that both series carry; the widening applies to the
    # live bands only, exactly as registered, and the walk-forward
    # history study below keeps its published basis (no widening).
    backwardation_state = "no_data"
    backwardation_applied = False
    backwardation_reading = {"date": None, "vix": None, "vix3m": None}
    if os.path.exists(VIX3M_PATH):
        vix3m = load_vix_series(VIX3M_PATH)
        common = [d for d in vix if d in vix3m and d <= as_of]
        if common:
            d = max(common)
            backwardation_reading = {"date": d, "vix": vix[d],
                                     "vix3m": vix3m[d]}
            if d < as_of:
                backwardation_state = "stale"
            elif vix[d] > vix3m[d]:
                backwardation_state = "backwardation"
                backwardation_applied = True
            else:
                backwardation_state = "contango"

    # ---- Walk-forward history study (ledgers nothing) ----
    cells = []
    total_graded = 0
    for sym in SYMBOLS:
        dates, closes = series[sym]
        rets = [math.log(closes[i] / closes[i - 1])
                for i in range(1, len(closes))]
        sq = [r * r for r in rets]
        for h in (1, 5, 21):
            hits = {p: 0 for p in LEVELS}
            graded = 0
            for i in range(WARMUP, len(closes) - h):
                vol = har_annualised_vol(sq, i)
                # History study basis: no widening, as published.
                b = bands_for(closes[i], vol, h, False)
                graded += 1
                for level in LEVELS:
                    lo, hi, _ = b[level]
                    if lo <= closes[i + h] <= hi:
                        hits[level] += 1
            for level in LEVELS:
                cells.append({
                    "symbol": sym, "horizon": h, "level": level,
                    "graded": graded, "hits": hits[level],
                    "coverage_pct": (round(hits[level] / graded * 100.0, 1)
                                     if graded >= 30 else None),
                })
            total_graded += graded
    # Expected cell counts, fail closed: bases WARMUP..len-h-1.
    n_sessions = len(series[SYMBOLS[0]][0])
    expect = {h: n_sessions - h - WARMUP for h in (1, 5, 21)}
    for c in cells:
        if c["graded"] != expect[c["horizon"]]:
            return fail(f"history count disagreement for {c['symbol']} "
                        f"h={c['horizon']}: {c['graded']} != "
                        f"{expect[c['horizon']]}")

    # ---- Live bands from the freshest close ----
    guard = session_quality_guard(as_of)
    future = next_sessions(as_of, 21)
    horizon_open = future[0]
    live = []
    for sym in SYMBOLS:
        dates, closes = series[sym]
        rets = [math.log(closes[i] / closes[i - 1])
                for i in range(1, len(closes))]
        sq = [r * r for r in rets]
        vol = har_annualised_vol(sq, len(closes) - 1)
        horizons = []
        for h in (1, 5, 21):
            b = bands_for(closes[-1], vol, h, backwardation_applied,
                          guard=guard)
            horizons.append({
                "sessions": h,
                "horizon_close": future[h - 1],
                "bands": [{"level": level,
                           "lower": b[level][0], "upper": b[level][1],
                           "half_pct": b[level][2]}
                          for level in LEVELS],
            })
        live.append({
            "symbol": sym, "name": NAMES[sym], "close": closes[-1],
            "close_date": as_of,
            "recent_movement_forecast_pct": round(vol * 100.0, 2),
            "horizons": horizons,
        })

    # ---- Ledger the live forecasts (API only, never by hand) ----
    reg = registry_mod.load()
    led = ledger_mod.Ledger(
        os.path.join(LINEUP, "forecast", "ledger.jsonl"), registry=reg)
    if not led.verify_chain():
        return fail("the forecast record does not verify; refusing "
                    "to add to it")
    panel_hash = ledger_mod.file_sha256(PANEL_PATH)
    vix_hash = ledger_mod.file_sha256(VIX_PATH)
    lineage = {
        "source_artifacts": [
            {"path": PANEL_PATH, "sha256": panel_hash},
            {"path": VIX_PATH, "sha256": vix_hash},
        ] + ([{"path": VIX3M_PATH,
               "sha256": ledger_mod.file_sha256(VIX3M_PATH)}]
             if os.path.exists(VIX3M_PATH) else []),
        "clocks": {
            "event_time": as_of,
            "publication_time": horizon_open,
            "first_available_time": as_of,
            "ingestion_time": as_of,
            "decision_as_of": as_of,
        },
        "note": ("Bands from the close of the as-of session, for the "
                 "sessions starting on the horizon open date. "
                 + vix_lineage_note(vix_last_date, as_of)),
    }
    created = 0
    for entry in live:
        for hz in entry["horizons"]:
            quantiles = {}
            for band in hz["bands"]:
                tail = (100 - band["level"]) / 200.0
                quantiles[f"{tail:.3f}"] = band["lower"]
                quantiles[f"{1 - tail:.3f}"] = band["upper"]
            row, was_created = led.append_forecast_declared(
                engine_id=ENGINE_ID,
                issued_ts=horizon_open,
                subject=entry["symbol"],
                quantity=(f"close-to-close move band, "
                          f"{hz['sessions']} sessions"),
                value={"quantiles": quantiles},
                horizon_open=horizon_open,
                horizon_close=hz["horizon_close"],
                lineage=lineage,
                families=["distributional_volatility", "price"],
                outcome={"symbol": entry["symbol"], "kind": "close",
                         "at_date": hz["horizon_close"]},
            )
            created += 1 if was_created else 0

    # ---- Figures recomputed from the ledger alone ----
    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    issue_days = len({
        r["lineage"]["clocks"]["decision_as_of"]
        for r in rows
        if r.get("type") == "forecast" and r.get("engine_id") == ENGINE_ID})
    # Count issuance slots, not raw rows (cure 2026-10-30, the
    # RC-05 duplicate class): on 2026-10-29 two issuance runs
    # stand on the append only record, the second run's revised
    # bands superseding the first run's for the same
    # (day, subject, quantity) slots, so the raw row count is
    # 18 against 12 slots and a raw equality check refuses a
    # healthy record forever. The check binds the slot count;
    # the superseded rows are named in the live record, never
    # absorbed silently.
    slots = {
        (r["lineage"]["clocks"]["decision_as_of"], r.get("subject"),
         r.get("quantity"))
        for r in rows
        if r.get("type") == "forecast" and r.get("engine_id") == ENGINE_ID}
    duplicate_rows = mine["forecasts"] - len(slots)
    if len(slots) != 6 * issue_days:
        return fail(f"ledger count disagreement: {len(slots)} "
                    f"forecast slots for {issue_days} issue days, "
                    f"expected {6 * issue_days}")
    if issue_days < 1:
        return fail("no live forecast was recorded")

    vix_last = vix.get(vix_last_date) if vix_last_date else None
    regime = {
        "state": "stale" if vix_last_date and vix_last_date < as_of
                 else "present",
        "volatility_index_close": (round(vix_last, 2)
                                   if vix_last is not None else None),
        "volatility_index_date": vix_last_date,
        "scaled_reading_pct": (round(vix_last / 15.87 * VIX_FACTOR, 2)
                               if vix_last is not None else None),
        "effect": ("Reading only. It changed no band on this "
                   "forecast."),
    }

    data = {
        "tool": "Corrected Band Engine",
        "state": "proving",
        "as_of_session": as_of,
        "next_session": horizon_open,
        "source": ("Daily closing prices for SPY and QQQ from the "
                   "price history on record (399 trading days, "
                   "March 25, 2025 to October 23, 2026), and the "
                   "daily closes of the volatility index on record "
                   f"(ending {vix_last_date})."),
        "live": {
            "issue_days": issue_days,
            "claim_target": CLAIM_TARGET,
            "forecasts_recorded": len(slots),
            "ledger_rows_total": mine["forecasts"],
            "superseded_duplicate_rows": duplicate_rows,
            "forecasts_graded": mine["graded"],
            "claim": ("The 68 percent band will contain the closing "
                      "price in 63 to 73 percent of cases at 5 "
                      "sessions, over its first 120 live forecast "
                      "days (120 forecasts of that band)."),
            "names": live,
            "regime_reading": regime,
            "backwardation": {
                "state": backwardation_state,
                "applied": backwardation_applied,
                "reading": backwardation_reading,
                "note": (("The volatility index sat above its "
                          "three-month reading on %s (%s against "
                          "%s), so the 95 percent band alone was "
                          "widened by the registered quarter step "
                          "in this forecast."
                          % (backwardation_reading["date"],
                             backwardation_reading["vix"],
                             backwardation_reading["vix3m"]))
                         if backwardation_applied else
                         ("The volatility index sat at or below its "
                          "three-month reading on the freshest "
                          "shared date on record, so no band was "
                          "widened for it in this forecast."
                          if backwardation_state == "contango" else
                          "Whether the volatility index sits above "
                          "its three-month reading is not on record "
                          "for the as-of session, so no band was "
                          "widened for it in this forecast.")),
            },
            "session_quality_guard": {
                **guard,
                "note": ("FE12 session quality guard (DEEP-PASS "
                         "3.2 item 10): a one sided liquidity "
                         "deterioration flag consumed as a band "
                         "widener and abstention raiser. "
                         + (("For this session the intraday bar "
                             "record supplies "
                             + ", ".join(guard.get("inputs_used")
                                         or [])
                             + "; the guard is partial because "
                             "spread and book depth are in no "
                             "store this terminal holds (no equity "
                             "quote store and no order book store "
                             "exists on disk), and those two "
                             "inputs stay named missing. The "
                             "recorded inputs widen the live "
                             "bands by the guard's own factor and "
                             "raise the abstention threshold the "
                             "same way.")
                            if guard.get("state") in ("partial",
                                                      "recorded")
                            else ("No intraday reading is on "
                                  "record for this session, so "
                                  "the guard is not recorded, no "
                                  "band was widened by it, and no "
                                  "threshold was raised."))),
            },
        },
        "history": {
            "label": "History, not live forecasts",
            "span_start": span[0], "span_end": span[1],
            "sessions": n_sessions,
            "graded_forecasts_total": total_graded,
            "note": ("Worked out day by day over the price history "
                     "on record: each day's band used only the "
                     "closing prices up to that day, then was "
                     "checked against the closing price 1, 5 or 21 "
                     "trading days later. These are study figures "
                     "from the past, not the live record above."),
            "cells": cells,
        },
        "kill_criterion": (
            "This tool is retired if, after 120 graded live "
            "forecasts, the share of closing prices inside the 68 "
            "percent band at any horizon falls outside the range "
            "chance alone would explain for a true 68 percent band, "
            "or if a simpler band built from recent movement alone "
            "beats it on accuracy at the same width."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: live as of {as_of}, {mine['forecasts']} "
          f"recorded forecasts ({created} new), {issue_days} of "
          f"{CLAIM_TARGET} issue days; history {total_graded} graded "
          f"per symbol-horizon set over {span[0]} to {span[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
