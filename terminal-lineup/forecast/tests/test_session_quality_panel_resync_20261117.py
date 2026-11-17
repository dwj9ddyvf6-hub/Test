"""Regression blocker for SESSION-QUALITY-PANEL-RESYNC-20261117.

Root cause proven 2026-11-17: build_session_quality.py selects
the sessions it builds from the price panel's own last rows, but
refresh_engines.py ran the session-quality lane BEFORE the
price-panel-advance spine step, in the same pre-advance record
lane block as the other publication records. On 2026-11-16 the
panel still ended at 2026-11-13 when the builder ran (record
built 2026-11-16T22:54:29Z, freshest_session 2026-11-13, all
four guard inputs present), the panel then advanced to
2026-11-16, and refresh_correctedband.py published as of
2026-11-16. Its FE12 guard reads the session quality record
only when the record's freshest session equals the refresh's
as-of session, so the guard flipped to not_recorded with all
four inputs missing even though the record existed and was
complete for its own session: a one-session producer lag, the
same defect class PANEL-RESYNC-20261031 cured for priced-moves.

Cure: the session-quality lane moved out of the pre-advance
record block into the panel-derived publication lanes that run
after the price panel advance, so the builder always builds
from the advanced panel and its freshest session is the
session the engines publish for.

Fail direction: on the pre-cure runner the session-quality
lane precedes the price-panel-advance lane in the runner's own
lane list, so the ordering assertion below fails; the
final-data assertion also failed pre-cure (the published
corrected-band guard stood not_recorded on 2026-11-16).
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.normpath(os.path.join(HERE, "..", ".."))
SITE = os.path.join(LINEUP, "site")


def _runner_lanes():
    with open(os.path.join(SITE, "refresh_engines.py"),
              encoding="utf-8") as fh:
        src = fh.read()
    return re.findall(r'\("([a-z0-9-]+)",\s*\[sys\.executable', src)


def test_session_quality_lane_runs_after_price_panel_advance():
    lanes = _runner_lanes()
    assert "session-quality" in lanes
    assert "price-panel-advance" in lanes
    assert lanes.index("price-panel-advance") < \
        lanes.index("session-quality"), (
            "build_session_quality.py reads its session list "
            "from the price panel, so its lane must run after "
            "the panel advance, never before it")


def test_session_quality_record_matches_published_guard():
    with open(os.path.join(SITE, "corrected-band",
                           "session_quality_record.json"),
              encoding="utf-8") as fh:
        record = json.load(fh)
    with open(os.path.join(SITE, "corrected-band", "data.json"),
              encoding="utf-8") as fh:
        data = json.load(fh)
    # The consumer's own binding, re-proven on the final
    # published state: the record the guard read is the record
    # for the page's as-of session, with every input supplied.
    assert record["freshest_session"] == data["as_of_session"]
    assert all(v is not None
               for v in record["freshest_inputs"].values())
    guard = data["live"]["session_quality_guard"]
    assert guard["state"] == "recorded"
    assert guard["missing"] == []
