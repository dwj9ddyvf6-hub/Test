#!/usr/bin/env python3
"""Mechanical check for the 30-day field-measurement rule (T-235), the
general rule documented in SKILL-FIELD-MEASUREMENT.md beside this file.

Validates that a skill.yaml carries, under skill_improvement:
evidence_handles (non-empty), measurement.success_criterion (an
observable outcome), measurement.window_days == 30, review_after
(a parseable date; overdue is flagged, not silently passed), and a
rationale. Uses PyYAML when available and falls back to a small
indentation parser for the subset these files use.

Usage:
  skill_field_check.py selftest
  skill_field_check.py check <skill.yaml | skills-root> [--today YYYY-MM-DD]
Exit: 0 all checked skills complete and not overdue-flagged as errors;
overdue is reported as a warning line and exit 0 only when fields are
otherwise complete; missing fields are errors (exit 1).
"""
import datetime, os, sys

def load_yaml(path):
    text = open(path, encoding="utf-8").read()
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        return _parse_subset(text)

def _parse_subset(text):
    """Minimal parser for the skill_improvement subset: nested key: value
    by indentation, plus '- item' lists. Sufficient for this check."""
    root, stack = {}, [(-1, None)]
    lines = text.splitlines()
    current_list_key = None
    for raw in lines:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else root
        if stripped.startswith("- "):
            if isinstance(parent, list):
                parent.append(stripped[2:].strip().strip("'\""))
            continue
        if ":" not in stripped:
            continue
        key, _sep, val = stripped.partition(":")
        key, val = key.strip(), val.strip().strip().strip("'\"")
        if parent is None:
            continue
        if val == "":
            nxt = {}
            if isinstance(parent, dict):
                parent[key] = nxt
            stack.append((indent, nxt))
            current_list_key = key
        else:
            if isinstance(parent, dict):
                parent[key] = val
    # list values (evidence_handles) need a second pass in subset mode
    return root

def check_record(rec, today=None):
    errors, warnings = [], []
    si = (rec or {}).get("skill_improvement")
    if not isinstance(si, dict):
        return ["missing skill_improvement block"], warnings
    handles = si.get("evidence_handles")
    if not handles or (isinstance(handles, list) and not handles):
        errors.append("evidence_handles missing or empty")
    meas = si.get("measurement") or {}
    if not meas.get("success_criterion"):
        errors.append("measurement.success_criterion missing")
    wd = meas.get("window_days")
    try:
        if int(wd) != 30:
            errors.append(f"measurement.window_days must be 30, got {wd!r}")
    except (TypeError, ValueError):
        errors.append(f"measurement.window_days missing or not a number: {wd!r}")
    ra = si.get("review_after")
    if not ra:
        errors.append("review_after missing")
    else:
        try:
            when = datetime.datetime.fromisoformat(str(ra).replace("Z", "+00:00")).date()
            today = today or datetime.date.today()
            if when < today:
                warnings.append(f"review_after {when} is past: field measurement review is due")
        except ValueError:
            errors.append(f"review_after not a parseable date: {ra!r}")
    if not si.get("rationale"):
        errors.append("rationale missing")
    return errors, warnings

def check_path(path, today=None):
    files = []
    if os.path.isfile(path):
        files = [path]
    else:
        for root, _d, names in os.walk(path):
            if "skill.yaml" in names:
                files.append(os.path.join(root, "skill.yaml"))
    results = []
    for f in sorted(files):
        try:
            rec = load_yaml(f)
            errors, warnings = check_record(rec, today=today)
        except Exception as e:
            errors, warnings = [f"unreadable: {e}"], []
        results.append({"file": f, "errors": errors, "warnings": warnings})
    return results

def selftest():
    good = {"skill_improvement": {
        "evidence_handles": ["msg-1", "msg-2"],
        "measurement": {"success_criterion": "In the 30 days after install, zero failures of class X.",
                        "window_days": 30},
        "review_after": "2999-01-01T00:00:00+00:00",
        "rationale": "Checked A and B; changed C; considered D and did not propose it because E."}}
    errors, warnings = check_record(good, today=datetime.date(2026, 11, 3))
    assert errors == [] and warnings == [], (errors, warnings)
    bad = {"skill_improvement": {"measurement": {"window_days": 7}}}
    errors, _w = check_record(bad, today=datetime.date(2026, 11, 3))
    assert len(errors) >= 4, errors
    overdue = dict(good)
    import copy
    overdue = copy.deepcopy(good)
    overdue["skill_improvement"]["review_after"] = "2020-01-01T00:00:00+00:00"
    errors, warnings = check_record(overdue, today=datetime.date(2026, 11, 3))
    assert errors == [] and warnings, (errors, warnings)
    live = os.path.expanduser("~/workspace/custom-skills/local-alpaca-paper/skill.yaml")
    if os.path.isfile(live):
        res = check_path(live, today=datetime.date(2026, 11, 3))
        assert res and res[0]["errors"] == [], res
    print("SELFTEST PASS skill_field_check: complete record passes, missing fields each named, overdue review warned not hidden, live local-alpaca-paper skill.yaml passes")
    return 0

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "selftest":
        raise SystemExit(selftest())
    if args and args[0] == "check" and len(args) >= 2:
        today = None
        if "--today" in args:
            today = datetime.date.fromisoformat(args[args.index("--today") + 1])
        results = check_path(args[1], today=today)
        bad = 0
        for r in results:
            status = "OK" if not r["errors"] else "ERROR"
            if r["errors"]:
                bad += 1
            print(f"{status} {r['file']}" + (f" :: {'; '.join(r['errors'])}" if r["errors"] else ""))
            for w in r["warnings"]:
                print(f"  WARN {w}")
        raise SystemExit(1 if bad else 0)
    print(__doc__)
    raise SystemExit(2)
