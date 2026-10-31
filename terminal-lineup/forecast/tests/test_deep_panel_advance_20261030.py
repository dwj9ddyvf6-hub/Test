"""Regression blocker: DEEP panel daily advance (cure G3 scheduling,
2026-10-30).

Pre-cure state: no advance lane existed for deep_bars.json at all
(the module under test did not exist), so Engines 3 and 15 aged on
the frozen 2026-10-28 panel forever. These tests pin the lane's
contract on a fixture panel in the panel's own byte form: appends
land strictly after each symbol's own last date, untouched symbols
keep their bytes, the result re-parses as the same JSON shape, and
a second run is an idempotent no-op.
"""
import json
import os
import sys

sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup/site"))

import advance_deep_panel as adp


PANEL = {
    "AAA": [["2026-10-27", 1.0, 1.1, 0.9, 1.05, 100],
            ["2026-10-28", 1.05, 1.2, 1.0, 1.15, 110]],
    "BBB": [["2026-10-28", 2.0, 2.1, 1.9, 2.05, 200]],
    "CCC": [],
}


def _write_panel(tmp_path):
    p = tmp_path / "deep_bars.json"
    p.write_text(json.dumps(PANEL), encoding="utf-8")
    return str(p)


def test_scan_reads_last_dates_without_loading_rows(tmp_path):
    path = _write_panel(tmp_path)
    import mmap
    with open(path, "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        scan = adp.scan_panel(mm)
        mm.close()
    assert scan["AAA"][2] == 2 and scan["AAA"][3] == "2026-10-28"
    assert scan["BBB"][2] == 1 and scan["BBB"][3] == "2026-10-28"
    assert scan["CCC"][2] == 0 and scan["CCC"][3] is None


def test_advance_appends_only_newer_rows_per_symbol(tmp_path):
    path = _write_panel(tmp_path)
    fetched = {
        "AAA": {"2026-10-28": ["2026-10-28", 9, 9, 9, 9, 9],
                "2026-10-29": ["2026-10-29", 1.15, 1.3, 1.1, 1.25, 120]},
        "BBB": {},
        "CCC": {"2026-10-29": ["2026-10-29", 3.0, 3.1, 2.9, 3.05, 300]},
    }
    code, msg = adp.advance_panel_file(path, fetched, "2026-10-29")
    assert code == 0, msg
    after = json.loads(open(path, encoding="utf-8").read())
    # the stale 2026-10-28 row for AAA is never overwritten or duped
    assert [r[0] for r in after["AAA"]] == [
        "2026-10-27", "2026-10-28", "2026-10-29"]
    assert after["AAA"][-1] == ["2026-10-29", 1.15, 1.3, 1.1, 1.25, 120]
    assert after["BBB"] == PANEL["BBB"]          # no bars: untouched
    assert after["CCC"] == [["2026-10-29", 3.0, 3.1, 2.9, 3.05, 300]]
    # idempotent: a second run at the same through date is a no-op
    code2, msg2 = adp.advance_panel_file(path, fetched, "2026-10-29")
    assert code2 == 0 and "already at" in msg2
    assert json.loads(open(path, encoding="utf-8").read()) == after


def test_advance_with_no_new_bars_fails_closed(tmp_path):
    path = _write_panel(tmp_path)
    before = open(path, "rb").read()
    code, msg = adp.advance_panel_file(path, {"AAA": {}, "BBB": {}},
                                       "2026-10-29")
    assert code == 1 and "no new bars" in msg
    assert open(path, "rb").read() == before     # panel untouched
