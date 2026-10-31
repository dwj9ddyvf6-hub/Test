#!/usr/bin/env python3
"""Earnings record lane (publication cures B4/B5, 2026-10-30).

The Nasdaq public earnings calendar endpoint already fetched daily
by fetch_earnings_calendar.py returns, per row, the report time
class, the consensus EPS forecast, the reported EPS, the surprise
percent and the estimate count. The calendar lane kept only the
symbol and discarded the rest at the parser, which is the
demonstrated cause behind three named remainders:

- FE17 centre (Engine 12): no report timing record existed, so
  timing quality had no source.
- FE18 PEAD (Engine 12): no standardized earnings surprise record
  existed.
- The dispersion leg of FE17: no estimate record existed at all.

This lane is the single earnings record of the terminal. It stores
dated snapshots of the full row set (site/earnings-record/
snapshots/<date>.json, one file per calendar day fetched, append
only) and one aggregate record (site/earnings-record/record.json)
carrying, per tracked name:

- reports: every reported row in the fetched window with actual
  EPS, pre report consensus EPS and surprise percent as printed by
  the source (never recomputed from a guessed consensus);
- timing: the report time class for the name's next dated report
  and its registered timing quality (a known class, pre market or
  after hours, is 1.0; time-not-supplied is 0.5, a named partial,
  never silently upgraded);
- surprise: a standardized surprise for the latest report,
  (actual minus consensus) divided by the standard deviation of
  the name's own prior forecast errors, computed only when at
  least 4 prior errors exist (the analyst forecast error form of
  SUE, registered here before the first row is consumed);
- forecast_error_dispersion: the standard deviation of the name's
  prior forecast errors, plus its cross sectional z against the
  reporting names in the record. This is forecast error
  dispersion, NOT cross analyst dispersion: no free source found
  carries individual analyst estimates, and this record never
  renames one quantity as the other. Whether FE17 may consume it
  under that definition is a registry ruling, named in the record.

Revision breadth across analysts likewise has no free source:
the consensus point snapshots this lane stores daily are the raw
material for the registered cross series breadth analogue, which
can only accrue forward from the first snapshot. The record states
that state instead of fabricating a breadth.

Usage: python3 earnings_record.py [--past 150] [--forward 60]
"""

import json
import math
import os
import statistics
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "earnings-record")
SNAP_DIR = os.path.join(OUT_DIR, "snapshots")
RECORD_PATH = os.path.join(OUT_DIR, "record.json")
CAL_RECORD = os.path.join(HERE, "earnings-calendar", "record.json")
API = "https://api.nasdaq.com/api/calendar/earnings?date={day}"

TIMING_QUALITY = {"time-pre-market": 1.0, "time-after-hours": 1.0,
                  "time-not-supplied": 0.5}
MIN_PRIOR_ERRORS = 4


def parse_money(raw):
    """'$2.01' -> 2.01; '($0.31)' / '-$0.31' -> -0.31; else None."""
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "").replace("$", "")
    if not s or s in ("N/A", "--"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def parse_pct(raw):
    if raw is None:
        return None
    s = str(raw).strip().replace("%", "")
    if not s or s in ("N/A", "--"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_day_rows(doc, day_iso):
    """Full rows for one calendar day. Pure: the report date is
    the request day by the API's one file per day contract."""
    rows = ((doc or {}).get("data") or {}).get("rows") or []
    out = []
    for row in rows:
        sym = (row.get("symbol") or "").strip().upper()
        if not sym:
            continue
        try:
            n_est = int(row.get("noOfEsts"))
        except (TypeError, ValueError):
            n_est = None
        out.append({
            "symbol": sym,
            "report_date": day_iso,
            "time_class": (row.get("time") or "time-not-supplied"),
            "eps_actual": parse_money(row.get("eps")),
            "eps_forecast": parse_money(row.get("epsForecast")),
            "surprise_pct": parse_pct(row.get("surprise")),
            "no_of_ests": n_est,
            "fiscal_quarter_ending": row.get("fiscalQuarterEnding"),
        })
    return out


def timing_quality(time_class):
    return TIMING_QUALITY.get(time_class, 0.5)


def standardized_surprise(reports):
    """SUE, analyst forecast error form. reports: chronological
    rows with eps_actual and eps_forecast present. The latest
    report's error is divided by the sd of the PRIOR errors;
    fewer than MIN_PRIOR_ERRORS priors is a named not_recorded."""
    errs = [r["eps_actual"] - r["eps_forecast"] for r in reports
            if r.get("eps_actual") is not None
            and r.get("eps_forecast") is not None]
    if len(errs) < MIN_PRIOR_ERRORS + 1:
        return {"state": "not_recorded", "sue_z": None,
                "prior_errors": max(0, len(errs) - 1),
                "missing": ["at_least_4_prior_forecast_errors"]}
    prior = errs[:-1]
    sd = statistics.pstdev(prior)
    if sd <= 0:
        return {"state": "not_recorded", "sue_z": None,
                "prior_errors": len(prior),
                "missing": ["nonzero_prior_error_dispersion"]}
    return {"state": "recorded",
            "sue_z": round(errs[-1] / sd, 4),
            "prior_errors": len(prior),
            "prior_error_sd": round(sd, 4), "missing": []}


def build_record(day_rows, tracked, today_iso):
    """Aggregate per tracked name from {day_iso: [rows]}."""
    by_sym = {}
    for day in sorted(day_rows):
        for r in day_rows[day]:
            if r["symbol"] in tracked:
                by_sym.setdefault(r["symbol"], []).append(r)
    names = {}
    dispersions = {}
    for sym, rows in sorted(by_sym.items()):
        reported = [r for r in rows if r["eps_actual"] is not None]
        future = [r for r in rows if r["report_date"] >= today_iso]
        sue = standardized_surprise(reported)
        if sue["state"] == "recorded":
            dispersions[sym] = sue["prior_error_sd"]
        nxt = future[0] if future else None
        names[sym] = {
            "reports_on_record": len(reported),
            "reports": reported[-8:],
            "next_report": ({"date": nxt["report_date"],
                             "time_class": nxt["time_class"],
                             "eps_forecast": nxt["eps_forecast"],
                             "no_of_ests": nxt["no_of_ests"]}
                            if nxt else None),
            "timing_quality": (timing_quality(nxt["time_class"])
                               if nxt else None),
            "surprise": sue,
        }
    if len(dispersions) >= 3:
        vals = list(dispersions.values())
        mu, sd = statistics.fmean(vals), statistics.pstdev(vals)
        for sym, v in dispersions.items():
            names[sym]["forecast_error_dispersion"] = {
                "state": "recorded", "sd": v,
                "cross_section_z": (round((v - mu) / sd, 4)
                                    if sd > 0 else None),
                "definition": ("forecast error dispersion: sd of "
                               "the name's own prior forecast "
                               "errors, z scored across reporting "
                               "names. Not cross analyst "
                               "dispersion."),
            }
    for sym in names:
        names[sym].setdefault(
            "forecast_error_dispersion",
            {"state": "not_recorded", "sd": None,
             "cross_section_z": None,
             "definition": ("forecast error dispersion: sd of "
                            "the name's own prior forecast "
                            "errors, z scored across reporting "
                            "names. Not cross analyst "
                            "dispersion.")})
    return names


def fetch_day(day_iso):
    out = subprocess.run(
        ["curl", "-sS", "--fail", "-m", "30", "-A", "Mozilla/5.0",
         "-H", "Accept: application/json", API.format(day=day_iso)],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"nasdaq fetch failed for {day_iso}: "
                           f"{out.stderr.strip()[:160]}")
    return json.loads(out.stdout)


def tracked_symbols():
    with open(CAL_RECORD, encoding="utf-8") as fh:
        doc = json.load(fh)
    return set(doc["entries"])


def main(argv):
    past, forward = 150, 60
    if "--past" in argv:
        past = int(argv[argv.index("--past") + 1])
    if "--forward" in argv:
        forward = int(argv[argv.index("--forward") + 1])
    today = datetime.now(timezone.utc).date()
    tracked = tracked_symbols()
    os.makedirs(SNAP_DIR, exist_ok=True)
    day_rows = {}
    fetched = failed = 0
    for offset in range(-past, forward):
        day = today + timedelta(days=offset)
        if day.weekday() >= 5:
            continue
        iso = day.isoformat()
        snap = os.path.join(SNAP_DIR, iso + ".json")
        if os.path.exists(snap):
            with open(snap, encoding="utf-8") as fh:
                rows = json.load(fh)["rows"]
        else:
            try:
                rows = parse_day_rows(fetch_day(iso), iso)
            except Exception as exc:  # noqa: BLE001 - named, counted
                print(f"earnings_record: {iso} failed: {exc}")
                failed += 1
                continue
            tmp = snap + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(
                    {"date": iso,
                     "fetched_at": datetime.now(timezone.utc)
                     .strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "rows": rows}, indent=1) + "\n")
            os.replace(tmp, snap)
        fetched += 1
        day_rows[iso] = rows
    names = build_record(day_rows, tracked, today.isoformat())
    record = {
        "updated_ts": datetime.now(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": ("nasdaq public earnings calendar api "
                   "(api.nasdaq.com/api/calendar/earnings), full "
                   "rows kept by earnings_record.py"),
        "window": {"past_days": past, "forward_days": forward,
                   "days_fetched": fetched, "days_failed": failed},
        "names_tracked": len(tracked),
        "names_with_reports": sum(
            1 for n in names.values() if n["reports_on_record"]),
        "names_with_surprise_recorded": sum(
            1 for n in names.values()
            if n["surprise"]["state"] == "recorded"),
        "names_with_timing": sum(
            1 for n in names.values()
            if n["timing_quality"] is not None),
        "revision_breadth": {
            "state": "accruing_forward",
            "detail": ("Analyst revision breadth has no free "
                       "source. The registered analogue, cross "
                       "series revision breadth, is computed from "
                       "this lane's daily consensus snapshots and "
                       "can only accrue forward from the first "
                       "snapshot (today); no breadth is fabricated "
                       "from a single snapshot.")},
        "names": names,
    }
    tmp = RECORD_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
    os.replace(tmp, RECORD_PATH)
    print(f"earnings_record: {fetched} days ({failed} failed), "
          f"{record['names_with_reports']} names with reports, "
          f"{record['names_with_surprise_recorded']} surprise "
          f"recorded, {record['names_with_timing']} with timing")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
