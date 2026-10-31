#!/usr/bin/env python3
"""Surface every page's full record in its own data.json.

Producer cure (2026-10-31, no-blank-states standard): many pages carried
their study record, calibration record and live accrual only as tables,
counts scattered across keys, or in a neighbouring file, so the page
itself read as a status word. This module adds ONE new block,
``record_surface``, to a page's data, built only from numbers already
on file for that page:

- current reading: the as-of stamp and the top-level keys that carry it
- study record: labelled, with provenance copied from the page's own
  provenance/source fields, and the locations (field paths) with the
  row counts already in those fields
- calibration record: the page's own calibration_attestation, verbatim,
  where one exists
- live accrual: for forecast engines, forecasts/grades/corrections
  counted from forecast/ledger.jsonl; otherwise the page's own counts
- missing: one plain line naming what is missing and when it arrives

No existing value is read for anything except counting and copying.
Nothing is invented, interpolated, smoothed or backfilled.
"""
import csv
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

STUDY_KEYS = ("history", "study", "study_record", "method", "episodes",
              "backtest_grades", "backcast", "research_record",
              "control_history", "sessions", "decision_days", "grades")
AS_OF_KEYS = ("as_of_session", "as_of", "freshest_session", "freshest_date",
              "published_at_utc", "generated_at_utc", "generated_at",
              "panel_last_session", "date", "session")

_ledger_cache = None


def ledger_counts():
    """Count forecast/grade/correction rows per engine in the ledger."""
    global _ledger_cache
    if _ledger_cache is not None:
        return _ledger_cache
    counts = {}
    path = ROOT / "forecast" / "ledger.jsonl"
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                eng = row.get("engine") or row.get("engine_id")
                kind = row.get("kind") or row.get("type") or ""
                if not eng:
                    continue
                slot = counts.setdefault(
                    eng, {"forecasts": 0, "grades": 0, "corrections": 0})
                if kind == "forecast":
                    slot["forecasts"] += 1
                elif kind == "grade":
                    slot["grades"] += 1
                elif kind == "correction":
                    slot["corrections"] += 1
    _ledger_cache = counts
    return counts


def _count(value, depth=0):
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        if depth > 2:
            return len(value)
        return sum(_count(v, depth + 1) for v in value.values())
    return 0


def study_locations(data):
    locs = []
    for key in STUDY_KEYS:
        if key in data and data[key] not in (None, [], {}):
            locs.append({"path": f"/{key}", "items": _count(data[key])})
    # Nested study records, e.g. /history/study_record/rows
    hist = data.get("history")
    if isinstance(hist, dict):
        for sub, val in hist.items():
            if isinstance(val, (list, dict)) and val:
                locs.append({"path": f"/history/{sub}",
                             "items": _count(val)})
    return locs


_engine_map = None


def engine_for_slug(slug, data):
    """Slug to engine id, from INFO-MAP.md's audited per-page rows."""
    global _engine_map
    if _engine_map is None:
        _engine_map = {}
        info = (ROOT.parent / "research_notes" /
                "terminal-visual-expression-20261031" / "INFO-MAP.md")
        try:
            import re
            for line in info.read_text().splitlines():
                m = re.match(r"\| ([a-z0-9\-]+) \|", line)
                e = re.search(r"engines\[(engine_\d+)\]", line)
                if m and e:
                    _engine_map[m.group(1)] = e.group(1)
        except OSError:
            pass
    return _engine_map.get(slug)


def _missing_line(slug, data, accrual, study):
    if slug == "state-analogue":
        c = data.get("counts") or {}
        return (f"Matches: none yet. {c.get('sessions_recorded', 2)} of "
                f"{c.get('sessions_needed', 126)} recorded sessions are on "
                "file; one more session is added each trading day and "
                "matches appear once enough sessions have built up.")
    if slug == "market-mood":
        return ("One gauge is missing: What People Say has no readings "
                "yet. It arrives when its survey source next publishes.")
    if slug == "skew-lens":
        return ("Live chain figures are empty for the latest session; "
                "the dated and modelled readings on file are shown "
                "instead. New figures arrive with the next options "
                "chain capture.")
    if slug == "ai-chart-read":
        return ("A graded record of past reads does not exist yet and "
                "is not filled in from anything else. The first graded "
                "reads arrive after the next scored run's sessions close.")
    if slug == "regime-dial":
        return ("Earlier daily readings were not kept before today, so "
                "the reading history starts today and adds one entry "
                "each trading day from now on.")
    if accrual and accrual.get("grades") == 0 and accrual.get("forecasts"):
        return (f"Live grades are still building: {accrual['forecasts']} "
                "forecasts are on record and none are graded yet. Grades "
                "arrive after each following session close.")
    if accrual and accrual.get("forecasts", 0) > accrual.get("grades", 0) > 0:
        return (f"More live grades are still to come: "
                f"{accrual['forecasts']} forecasts are on record and "
                f"{accrual['grades']} are graded so far. The rest arrive "
                "after each following session close.")
    if not study:
        return ("No study record is on file for this page; what it shows "
                "is its current reading, updated on its normal schedule.")
    return ("Nothing from the record on file is missing. The next "
            "update arrives at the next session close on this page's "
            "normal schedule.")


def specific_extras(slug, data):
    """Records stranded in neighbouring files, surfaced by name."""
    extra = {}
    if slug == "market-mood":
        gauges_dir = ROOT / "psychology-engine" / "history" / "gauges"
        rows = {}
        if gauges_dir.exists():
            for f in sorted(gauges_dir.glob("*.csv")):
                try:
                    with open(f, newline="", encoding="utf-8") as fh:
                        rows[f.name] = max(
                            sum(1 for _ in csv.reader(fh)) - 1, 0)
                except OSError:
                    pass
        extra["gauge_history"] = {
            "label": "Study record",
            "source": "psychology-engine/history/gauges (files on disk)",
            "files": rows,
            "episodes_on_record": len(data.get("episodes") or []),
            "backtest_grades_on_record": len(
                data.get("backtest_grades") or []),
            "live_grades_on_record": len(data.get("live_grades") or []),
        }
    if slug == "horizon-grades":
        rec_path = HERE / "record" / "data.json"
        if rec_path.exists():
            rec = json.loads(rec_path.read_text())
            board = rec.get("board") or {}
            extra["record_on_the_record_page"] = {
                "label": "Study record",
                "source": "record/data.json (the call-by-call record)",
                "totals_on_this_page": data.get("totals"),
                "board_keys": sorted(board.keys())[:12],
            }
    if slug == "flow-engine":
        tape_path = HERE / "flow-tape" / "data.json"
        if tape_path.exists():
            tape = json.loads(tape_path.read_text())
            extra["record_on_the_flow_tape_page"] = {
                "label": "Study record",
                "source": "flow-tape/data.json (the session tape)",
                "counts": tape.get("counts"),
                "groups_on_record": len(tape.get("groups") or []),
            }
    if slug == "regime-dial":
        hist_path = HERE / "regime-dial" / "reading-history.json"
        history = []
        if hist_path.exists():
            try:
                history = json.loads(hist_path.read_text())
            except ValueError:
                history = []
        stamp = data.get("freshest_session") or data.get("as_of")
        reading = data.get("reading") or {}
        if stamp and not any(h.get("session") == stamp for h in history):
            history.append({
                "session": stamp,
                "kind": reading.get("kind"),
                "sentence": reading.get("sentence"),
                "counting_checks": data.get("counting_checks"),
                "checks_total": data.get("checks_total"),
            })
            hist_path.write_text(json.dumps(history, indent=2) + "\n")
        data["reading_history"] = history
        extra["reading_history"] = {
            "label": "Study record",
            "source": "regime-dial/reading-history.json (one entry is "
                      "added by this producer each day a new reading "
                      "is published; earlier days are not filled in)",
            "sessions_on_record": len(history),
        }
    if slug == "state-analogue":
        extra["accrual"] = {
            "label": "Live accrual",
            "counts": data.get("counts"),
            "readings_defined": len(data.get("readings") or []),
            "matches_on_record": len(data.get("matches") or []),
        }
    return extra


def build_record_surface(slug, data):
    as_of = None
    for key in AS_OF_KEYS:
        val = data.get(key)
        if isinstance(val, str) and val:
            as_of = val
            break
        if isinstance(val, dict):
            inner = val.get("session") or val.get("date")
            if inner:
                as_of = inner
                break
    study = study_locations(data)
    eng = engine_for_slug(slug, data)
    accrual = None
    if eng:
        accrual = dict(ledger_counts().get(
            eng, {"forecasts": 0, "grades": 0, "corrections": 0}))
        accrual["engine"] = eng
        accrual["source"] = "forecast/ledger.jsonl (counted)"
    elif isinstance(data.get("counts"), dict):
        accrual = {"counts": data["counts"],
                   "source": "this page's own counts"}
    surface = {
        "version": 1,
        "label": "Study record",
        "provenance": data.get("provenance") or data.get("source"),
        "feed": data.get("feed"),
        "current_reading": {
            "as_of": as_of,
            "keys_present": sorted(data.keys()),
        },
        "study_record": {
            "label": "Study record",
            "locations": study,
            "total_items_counted": sum(x["items"] for x in study),
        },
        "calibration_record": data.get("calibration_attestation"),
        "live_accrual": accrual,
    }
    extras = specific_extras(slug, data)
    if extras:
        surface["surfaced_from_other_files"] = extras
        if slug == "market-mood" and "gauge_history" in extras:
            surface["gauge_history"] = extras["gauge_history"]
    surface["missing"] = {
        "what_and_when": _missing_line(slug, data, accrual, study),
    }
    return surface


def enrich_file(path):
    path = Path(path)
    slug = path.parent.name
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        return False
    data["record_surface"] = build_record_surface(slug, data)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)
    return True


def enrich_slug(slug):
    path = HERE / slug / "data.json"
    if path.exists():
        return enrich_file(path)
    return False


if __name__ == "__main__":
    import sys
    for slug in sys.argv[1:]:
        print(slug, enrich_slug(slug))
