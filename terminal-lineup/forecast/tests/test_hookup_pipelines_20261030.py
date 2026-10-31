"""Regression blockers for hookup stream 2 (pipelines and refresh),
2026-10-30 second pass. Each test pins one cure at the source.

Fail directions, proven against the pre-cure tree:
- refresh_onepagereport.py carried its receipt as a hardcoded
  string whose figures had drifted from the records it joins
  (unusual volume 61 against 119 listed, earnings dates 73 against
  46 dated, pattern labels 1,817 against 1,816), its earnings
  section text denied any priced move existed while the Earnings
  Calendar shipped 30, and the page render printed the same denial
  for every name regardless of the data.
- refresh_streaktrap.py printed "16 young figures are staked. None
  has matured yet" as a literal while its own record carried
  matured: 1 and the ledger carried 2 grade rows.
- refresh_silentaccumulation.py printed the pre-cure dark-store
  blocker ("per-stock collection has not started") unconditionally,
  after the per-name dark store had landed (683 sessions).
- The hub (site/index.html) full notes and figlines presented
  superseded states as current for at least ten tools (Short
  Volume "collection has not started", Filings "0 companies",
  Echo Lens "0 of 1,838", State Analogue "0 of 126", and more).
- No lane advanced the VIX store (it ended 2026-10-21) and no
  VIX3M series existed, so Engine 1's registered backwardation
  state was hardcoded no_data in refresh_correctedband.py.
"""
import json
import os
import re

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
STORE = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source")


def src(name):
    with open(os.path.join(SITE, name), encoding="utf-8") as fh:
        return fh.read()


def load(slug):
    with open(os.path.join(SITE, slug, "data.json")) as fh:
        return json.load(fh)


def test_onepage_receipt_is_computed_not_literal():
    s = src("refresh_onepagereport.py")
    assert "unusual volume lists 61" not in s
    assert "carries a date for 73" not in s
    assert "for 1,817" not in s
    assert "len(volume['names'])" in s
    assert "earnings['dated_names']" in s


def test_onepage_receipt_recomputes_from_its_own_data():
    d = load("one-page-report")
    r = d["receipt"]
    vol = load("unusual-volume")
    earn = load("earnings-calendar")
    assert f"unusual volume lists {len(vol['names']):,}" in r
    assert f"carries a date for {earn['dated_names']:,}" in r
    labels = sum(1 for e in d["names"].values()
                 if e["chart"] and e["chart"].get("label"))
    assert f"pattern label for {labels:,}" in r


def test_onepage_earnings_moves_flow_from_the_calendar():
    d = load("one-page-report")
    earn = load("earnings-calendar")
    priced = {n["symbol"]: n["expected_move"]
              for n in earn["names"] if n.get("expected_move")}
    assert len(priced) == earn["priced_moves_on_record"] > 0
    for sym, move in priced.items():
        assert d["names"][sym]["earnings"]["expected_move"] == move
    page = src(os.path.join("one-page-report", "index.html"))
    assert "n.expected_move" in page


def test_streaktrap_words_follow_its_record():
    s = src("refresh_streaktrap.py")
    assert "None has matured " not in s.split("stats[\"matured\"]")[0][-200:] \
        or "if not stats[\"matured\"]" in s
    d = load("streak-trap")
    words = d["live_record"]["words"]
    assert words.startswith(
        f"{d['live_record']['triggers_staked']} young figures")
    if d["live_record"]["matured"]:
        assert "None has matured" not in words


def test_silent_accumulation_wait_matches_dark_store():
    s = src("refresh_silentaccumulation.py")
    assert "if dark_gap else" in s
    d = load("silent-accumulation")
    if d["readings"]["dark"]["state"] == "on_record":
        assert "collection has not started" not in d["live"]["wait"]


def test_hub_notes_do_not_present_superseded_states():
    hub = src("index.html")
    for stale in ("daily collection has not started yet",
                  "0 days on record, no stock on record",
                  "0 companies on record, no figure on record",
                  "0 of the 126 recorded days",
                  "no reading from that method is on record yet",
                  "196 entries (56 from The Record",
                  "for Friday, October 23, 2026, the bar pattern"):
        assert stale not in hub, stale
    sv = load("short-volume")
    assert f"{sv['days_on_record']} days on record" in hub


def test_vix_capture_lane_and_store():
    assert os.path.exists(os.path.join(SITE, "capture_vix_daily.py"))
    assert "capture_vix_daily.py" in src("refresh_engines.py")
    from datetime import datetime, timezone
    for name in ("yahoo-vix-daily.json", "yahoo-vix3m-daily.json"):
        doc = json.load(open(os.path.join(STORE, name)))
        r = doc["chart"]["result"][0]
        pts = [(datetime.fromtimestamp(t, tz=timezone.utc)
                .date().isoformat(), c)
               for t, c in zip(r["timestamp"],
                               r["indicators"]["quote"][0]["close"])
               if c is not None]
        assert len(pts) >= 400, (name, len(pts))
        assert pts[-1][0] >= "2026-10-29", (name, pts[-1])


def test_correctedband_reads_vix3m_for_backwardation():
    s = src("refresh_correctedband.py")
    assert "VIX3M_PATH" in s and "load_vix_series" in s
    assert 'backwardation_state = "no_data"\n    backwardation_applied = False\n\n    # ---- Walk-forward' not in s
    d = load("corrected-band")
    b = d["live"]["backwardation"]
    assert b["state"] in ("backwardation", "contango", "stale",
                          "no_data")
    if b["reading"]["date"]:
        assert b["state"] != "no_data"
