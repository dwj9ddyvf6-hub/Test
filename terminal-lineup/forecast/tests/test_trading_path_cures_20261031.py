#!/usr/bin/env python3
"""Regression blockers for the Round 1 trading path cures
(terminal total audit, 2026-10-31). Each test names the defect it
blocks. Live-state tests read the final published files; source
tests pin the class cure so a refactor cannot silently revert it.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(os.path.dirname(HERE))
SITE = os.path.join(LINEUP, "site")
BOOK = os.path.expanduser("~/workspace/midna-book")
WORK = os.path.expanduser("~/workspace")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# D1: Market Mood page and feed must equal the engine state.
def test_market_mood_matches_engine_state():
    state = load(os.path.join(
        LINEUP, "psychology-engine", "output", "state-latest.json"))
    for rel in (os.path.join(SITE, "market-mood", "data.json"),
                os.path.join(LINEUP, "psychology-engine", "output",
                             "feed.json")):
        feed_state = load(rel)["state"]
        assert feed_state["date"] == state["date"], rel
        assert feed_state["composite_percentile"] == \
            state["composite_percentile"], rel


def test_compile_state_renders_page_in_same_run():
    src = read(os.path.join(LINEUP, "psychology-engine",
                            "pipeline.py"))
    publish_block = src.split("write_consumer(state)", 1)[1]
    publish_block = publish_block.split("return state", 1)[0]
    assert "render_page(state)" in publish_block, (
        "compile_state(publish=True) must render the Market Mood "
        "page in the same run (TRADING-PATH-RENDER-20261031)")


# D2: regime family at the freshest completed session on record.
def test_regime_family_sessions_agree():
    breadth = load(os.path.join(SITE, "breadth-meter", "data.json"))
    assert breadth["scored_run_session"] == breadth["session"]
    assert breadth["history_to"] == breadth["session"]
    for name, key in (("sector-rotation", "session"),
                      ("morning-map", "session"),
                      ("board", "session")):
        doc = load(os.path.join(SITE, name, "data.json"))
        assert doc[key] == breadth["session"], name
    regime = load(os.path.join(SITE, "regime-dial", "data.json"))
    assert regime["freshest_session"] == breadth["session"]


# D3: earnings lane universe covers the book's carded names.
def test_earnings_record_covers_carded_names():
    rec = load(os.path.join(SITE, "earnings-calendar",
                            "record.json"))
    assert rec["names_checked"] >= 1000, rec["names_checked"]
    for sym in ("KDP", "CVX", "ABBV", "REGN", "CL", "CBOE"):
        assert sym in rec["entries"], sym
    assert rec["entries"]["KDP"] == "2026-11-03"
    pub = load(os.path.join(SITE, "earnings-calendar", "data.json"))
    assert {"symbol": "KDP", "date": "2026-11-03",
            "expected_move": None} in pub["names"] or any(
        n["symbol"] == "KDP" and n["date"] == "2026-11-03"
        for n in pub["names"])


def test_earnings_fetch_universe_includes_board():
    src = read(os.path.join(SITE, "fetch_earnings_calendar.py"))
    assert "board_full.json" in src
    assert "universe_symbols" in src


# D4: Week Ahead flags eventless weekdays as unverified.
def test_week_ahead_window_flags_unverified_weekdays():
    doc = load(os.path.join(SITE, "week-ahead", "data.json"))
    cov = doc["weekday_coverage"]
    assert cov, "rolling window coverage missing"
    for row in cov:
        if row["events_on_record"] == 0:
            assert row["state"] == \
                "unverified_no_events_on_record", row
        else:
            assert row["state"] == "covered", row
    nov2 = [r for r in cov if r["date"] == "2026-11-02"]
    if nov2:
        assert nov2[0]["state"] == \
            "unverified_no_events_on_record"


# D5: one live band per name, from the chain map only.
def test_expected_move_one_canonical_band_per_name():
    doc = load(os.path.join(SITE, "expected-move", "data.json"))
    canon = {b["symbol"]: b for b in doc["canonical_bands"]}
    chain = {n["symbol"]: n for n in doc["chain_map"]["names"]
             if n.get("state") == "ok"}
    assert set(canon) == set(chain)
    for sym, band in canon.items():
        em = chain[sym]["expected_move"]
        assert band["lower"] == em["lower"]
        assert band["upper"] == em["upper"]
    for entry in doc["names"]:
        if entry.get("state") == "ok":
            assert entry["receipt"]["session"] == doc["session"], \
                entry["name"]
            assert entry.get("band_role") == \
                "filed_archive_not_the_live_band"


# D6: Alpaca 5-minute bars default to SIP and fail closed empty.
def test_alpaca_5min_default_feed_is_sip():
    path = os.path.join(
        WORK, "custom-skills", "local-alpaca-paper", "bin",
        "alpaca_get_bars_5min.py")
    src = read(path)
    assert re.search(r'"--feed", default="sip"', src), (
        "5-minute bars must default to sip (charter fill basis)")
    assert "exit_code=3" in src or "exit 3" in src


# D7: ledger carries the Charter Amendment 1 pod fields.
def test_ledger_pod_accounting_fields():
    ledger = load(os.path.join(BOOK, "ledger.json"))
    pods = ledger.get("pods") or {}
    assert pods, "ledger carries no pods"
    for name, pod in pods.items():
        for field in ("sleeve_capital", "sleeve_high_water",
                      "sleeve_drawdown_pct"):
            assert field in pod, f"{name} missing {field}"
    assert "book_ladder" in ledger


# D8: recovery registers carry the current sentiment, not 24.6.
def test_snapshot_sentiment_is_current():
    state = load(os.path.join(BOOK, "SENTIMENT-STATE.json"))
    snap = read(os.path.join(BOOK, "CONTEXT-SNAPSHOT.md"))
    assert str(state["composite_percentile"]) in snap
    assert "composite percentile 24.6" not in snap


if __name__ == "__main__":
    sys.exit(0)


# --- Round 1 re-audit cures (2026-10-31, second cure pass) ---

# D1R: Holly Ideas session must equal its source Board session,
# and its ideas must be exactly the Board's passed set.
def test_holly_session_equals_board_session():
    holly = load(os.path.join(SITE, "holly-ideas", "data.json"))
    board = load(os.path.join(SITE, "board", "data.json"))
    assert holly["session"] == board["session"], (
        f"Holly {holly['session']} behind Board {board['session']}")
    assert holly["board_session_in_record"] is True
    ideas = {i["symbol"] for i in holly["ideas"]}
    passed = {n["symbol"] for g in board["groups"]
              for n in g["names"] if n.get("passed_every_check")} \
        if "groups" in board else set()
    if not passed:
        # board file carries its names at top level in some shapes
        passed = {n["symbol"] for n in board.get("names", [])
                  if n.get("passed_every_check")}
    assert ideas == passed, (ideas ^ passed)


def test_holly_grading_words_handle_graded_horizons():
    src = read(os.path.join(SITE, "refresh_hollyideas.py"))
    assert "horizon_words" in src, (
        "Holly grading words must state graded and not-yet-graded "
        "horizons (TRADING-PATH-HOLLY-20261031)")


# D2R: the Record must carry the Board's freshest session.
def test_record_carries_board_session():
    rec = load(os.path.join(SITE, "record", "data.json"))
    board = load(os.path.join(SITE, "board", "data.json"))
    sessions = [g["session"] for g in rec["board"]["groups"]]
    assert board["session"] in sessions, (
        f"Record groups end {sessions[-1]}, Board {board['session']}")
    assert sessions == sorted(sessions)


# D4R: vix_close_latest must carry its as-of date everywhere the
# value is published, and the value must trace to the Cboe store.
def test_vix_close_has_as_of_and_traces_to_store():
    import csv as _csv
    store = os.path.join(LINEUP, "psychology-engine", "history",
                         "series", "cboe_vix_daily.csv")
    rows = []
    with open(store, encoding="utf-8") as fh:
        body = [l for l in fh if not l.startswith("#")]
    for r in _csv.DictReader(body):
        rows.append(r)
    last = rows[-1]
    state = load(os.path.join(
        LINEUP, "psychology-engine", "output", "state-latest.json"))
    assert state.get("vix_close_as_of") == last["date"], state.get(
        "vix_close_as_of")
    assert state["vix_close_latest"] == float(last["close"])
    consumer = load(os.path.join(BOOK, "SENTIMENT-STATE.json"))
    assert consumer.get("vix_close_as_of") == last["date"]
    assert consumer["vix_close_latest"] == float(last["close"])


def test_build_state_collects_cboe_before_compile():
    src = read(os.path.join(LINEUP, "psychology-engine", "compiler",
                            "build_state.py"))
    assert 'live_collect("cboe")' in src
    assert src.index('live_collect("cboe")') < src.index(
        "compile_state()")


# D5R: grading records' SPY close must be the SIP bar of record.
def test_benchmark_close_in_reviews_is_sip_value():
    cr = read(os.path.join(WORK, "personal-quant",
                           "close-review-2026-10-30.md"))
    fg = read(os.path.join(WORK, "personal-quant",
                           "friday-grading-2026-10-30.md"))
    assert "close 755.72 against 769.36" in cr
    assert "SPY closed 755.72" in fg
    assert "close 755.78" not in cr
    assert "SPY closed 755.78" not in fg


# D6R: both Alpaca bars scripts default to sip and fail closed.
def test_alpaca_1h_default_feed_is_sip():
    path = os.path.join(
        WORK, "custom-skills", "local-alpaca-paper", "bin",
        "alpaca_get_bars_1h.py")
    src = read(path)
    assert '"--feed", default="sip"' in src, (
        "1-hour bars must default to sip (TRADING-PATH-FEED1H)")
    assert "feed={args.feed}" in src
    assert "exit_code=3" in src
