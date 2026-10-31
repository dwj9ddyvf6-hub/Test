"""Regression blocker for the Fear-Day Forecaster coverage defect
cured 2026-10-30.

The defect: refresh_feardayforecaster.py demanded the Fear Day
List's coverage equal pinned pre-cure figures (23 fear-gauge
readings, September 21 to October 21, 2026, 4 checked sessions).
When the VIX capture cure advanced the list's own record (504
readings, 2024-10-30 to 2026-10-30, counted independently from
the VIX history file on disk), the forecaster refused the healthy
record forever and its page stayed unpublished.

The cure: the forecaster derives its coverage figures from the
list's published record at runtime (derive_coverage) and refuses
only a record that does not hold together on the list's own
counting rule (checked sessions equal the index sessions less
the first one, which has no session before it to compare
against).

Fail direction: the main test feeds a list record whose coverage
is consistent but matches neither the old pins nor today's live
figures; the pre-cure refresher returns 1 on it, the cured one
publishes it. Proven at cure time against a reconstructed
pre-cure module copy.

The list record and the output are fixtures in tmp; the other
source records the refresher cross-checks (Pullback Norm record,
forecast-search evidence) are read from disk, never written.
"""

import importlib.util
import json
import os
import sys

SITE = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "site"))
if SITE not in sys.path:
    sys.path.insert(0, SITE)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "refresh_feardayforecaster",
        os.path.join(SITE, "refresh_feardayforecaster.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DEFINITION = ("A fear day is a day when SPY fell more than 1.5%, "
              "or the fear gauge (the VIX) rose more than 15% in "
              "a day, closed at 25 or higher, or closed at 20 or "
              "higher on a day when SPY or QQQ fell.")

QUALIFYING_DAY = {
    "date": "2026-10-16",
    "fear_gauge_change_pct": 21.4,
    "fear_gauge_close": 19.99,
    "spy_change_pct": -1.1,
    "qqq_change_pct": -2.5,
    "qualified_by": ["the fear gauge rose more than 15% that day"],
}


def fearday_fixture(history):
    return {
        "tool": "Fear Day List",
        "state": "unpublished",
        "definition": DEFINITION,
        "events": 1,
        "follow_through": {"state": "not_counted"},
        "qualifying_days": [dict(QUALIFYING_DAY)],
        "history": history,
        "published_at_utc": "2026-10-29T20:51:16.967158+00:00",
        "studies_as_of": "2026-10-29",
    }


# Consistent on the list's counting rule (5 checked of 6 index
# sessions) and equal to neither the old pins (23 readings,
# 2026-09-21 to 2026-10-21, 4 checked) nor the live record.
ADVANCED_HISTORY = {
    "fear_gauge_readings": 777,
    "fear_gauge_from": "2024-01-02",
    "fear_gauge_to": "2026-10-30",
    "index_sessions": 6,
    "index_from": "2026-10-14",
    "index_to": "2026-10-21",
    "sessions_checked": 5,
}


def run_build(mod, tmp_path, history):
    src = tmp_path / "fearday.json"
    src.write_text(json.dumps(fearday_fixture(history)))
    out = tmp_path / "out" / "data.json"
    mod.FEARDAY_PATH = str(src)
    mod.OUT_PATH = str(out)
    return mod.build(), out


def test_coverage_derived_from_the_list_record(tmp_path):
    mod = load_module()
    rc, out = run_build(mod, tmp_path, ADVANCED_HISTORY)
    assert rc == 0
    data = json.loads(out.read_text())
    local = data["local_record"]
    assert local["fear_gauge_readings"] == 777
    assert local["sessions_checked"] == 5
    assert local["fear_gauge_from"] == "2024-01-02"
    assert local["fear_gauge_to"] == "2026-10-30"
    assert "777 fear-gauge readings" in data["receipt"]["coverage"]
    assert "5 comparable sessions" in data["receipt"]["coverage"]


def test_self_contradictory_coverage_still_refused(tmp_path):
    mod = load_module()
    bad = dict(ADVANCED_HISTORY, sessions_checked=3)
    rc, out = run_build(mod, tmp_path, bad)
    assert rc == 1
    assert not out.exists()


def test_derive_coverage_unit():
    mod = load_module()
    cov = mod.derive_coverage(fearday_fixture(ADVANCED_HISTORY))
    assert cov == {
        "sessions_checked": 5,
        "fear_gauge_readings": 777,
        "fear_gauge_from": "2024-01-02",
        "fear_gauge_to": "2026-10-30",
    }
    missing = fearday_fixture({"fear_gauge_readings": 777})
    assert mod.derive_coverage(missing) is None
    backwards = dict(ADVANCED_HISTORY, fear_gauge_from="2027-01-01")
    assert mod.derive_coverage(fearday_fixture(backwards)) is None


def test_no_pinned_coverage_constants_in_source():
    with open(os.path.join(SITE, "refresh_feardayforecaster.py"),
              encoding="utf-8") as fh:
        src = fh.read()
    assert 'fear_gauge_readings") != 23' not in src
    assert '"2026-09-21"' not in src
    assert "derive_coverage" in src
