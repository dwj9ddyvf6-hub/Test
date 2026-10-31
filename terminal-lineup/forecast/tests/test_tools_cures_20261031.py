"""ROUND-1 tools-a cure blockers (terminal total audit, 2026-10-31).

Each test pins one cured defect class from ROUND-1-AUDIT-tools-a.md:

- IV-LEDGER-SPOT-20261031: the modelled IV ledger producer kept
  appending later same-day captures at a different spot, so one
  (date, underlying) carried two spots and IV Weather / Skew Lens
  failed closed. Producer now keeps the first spot of the day;
  the live ledger carries exactly one spot per (date, name).
- MAP-SPOT-BASIS-20261031: Morning Map (and Gamma Ladder through
  it) published build-time live spots under a close basis. The
  published spot is now the panel session close for every fund,
  with the card spot kept as snapshot_spot, and the flip distance
  recomputed from the published spot.
- EMAP-QQQ-PANEL-20261031: Expected Move QQQ froze at 2026-10-22
  because only the stale Azrael record counted as a price
  record. The panel close now counts (with agreement required
  where both records cover a date), and the filing lane states
  completeness per name.
- PANEL-SAME-DAY-20261031: the panel advance defaulted to
  yesterday, so the panel family republished one session behind
  the tape family every evening. The advance defaults to the
  freshest completed session and the tools chain runs it first.
- REGIME-FEAR-CHAIN-20261031: Regime Dial stood on a superseded
  expected-move record. The dial fails closed when its fear
  session falls more than one session behind the record's
  session, and every expected-move republication chains a dial
  re-run.
- VOLCLOCK-SOURCE-20261031: Vol Clock's source string was
  hardcoded to the original panel and went stale. It is now
  computed from the panel actually read.
"""
import importlib.util
import json
import os
import re
import sys
from collections import defaultdict

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "..", "site"))
sys.path.insert(0, SITE)

PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
LEDGER_PATH = os.path.expanduser(
    "~/workspace/morgue/state/morgue/chains/iv_ledger_modelled.jsonl")


def _load_json(rel):
    with open(os.path.join(SITE, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _source(name):
    with open(os.path.join(SITE, name), encoding="utf-8") as fh:
        return fh.read()


def _panel():
    with open(PANEL_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# ---- IV ledger -------------------------------------------------

def test_iv_ledger_producer_keeps_first_spot_of_day(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "collect_chains", os.path.join(SITE, "collect_chains.py"))
    cc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cc)
    ledger = tmp_path / "iv.jsonl"
    cc.IV_LEDGER_PATH = str(ledger)
    occ_a = "SPY261106C00750000"
    occ_b = "SPY261106P00750000"
    quotes = {occ_a: {"bid": 1.0, "ask": 1.2, "mid": 1.1},
              occ_b: {"bid": 0.9, "ask": 1.1, "mid": 1.0}}
    rows_a = [(occ_a, None, None, 0.2)]
    rows_b = [(occ_b, None, None, 0.21)]
    assert cc.append_iv_ledger(
        "SPY", "2026-10-30", "2026-10-30T10:00:00Z", 100.0,
        rows_a, quotes) == 1
    # A later same-day capture at a different spot adds nothing.
    assert cc.append_iv_ledger(
        "SPY", "2026-10-30", "2026-10-30T15:00:00Z", 101.5,
        rows_b, quotes) == 0
    # A later capture at the same spot still adds new contracts.
    assert cc.append_iv_ledger(
        "SPY", "2026-10-30", "2026-10-30T16:00:00Z", 100.0,
        rows_b, quotes) == 1
    spots = {json.loads(line)["spot"]
             for line in ledger.read_text().splitlines()}
    assert spots == {100.0}


def test_iv_ledger_live_one_spot_per_day_name():
    spots = defaultdict(set)
    with open(LEDGER_PATH, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            spots[(row["date"], row["underlying"])].add(row["spot"])
    bad = {k: v for k, v in spots.items() if len(v) != 1}
    assert bad == {}


def test_iv_pages_live_freshest_modelled_2026_10_30():
    ivw = _load_json("iv-weather/data.json")
    assert ivw["freshest_date"] == "2026-10-30"
    modelled = ivw["groups"][-1]  # the modelled chain group
    assert {n["symbol"] for n in modelled["names"]} == {
        "SPY", "QQQ", "IWM"}
    assert {n["date"] for n in modelled["names"]} == {"2026-10-30"}
    skew = _load_json("skew-lens/data.json")
    assert skew["modelled_freshest_date"] == "2026-10-30"


# ---- Morning Map / Gamma Ladder --------------------------------

def test_morning_map_spot_is_panel_session_close():
    data = _load_json("morning-map/data.json")
    panel = _panel()
    closes = {sym: {r[0]: float(r[4]) for r in panel[sym]}
              for sym in ("SPY", "QQQ", "IWM")}
    for index in data["indexes"]:
        if index.get("state") != "ok":
            continue
        sym = index["symbol"]
        assert index["spot"] == closes[sym][data["session"]]
        assert "snapshot_spot" in index
        flip = index["flip"]
        if flip.get("state") == "ok":
            expect = round(
                (flip["value"] - index["spot"]) / index["spot"]
                * 100.0, 2)
            assert flip["distance_pct"] == expect


def test_gamma_ladder_matches_morning_map_basis():
    morning = _load_json("morning-map/data.json")
    ladder = _load_json("gamma-ladder/data.json")
    spots = {i["symbol"]: i["spot"] for i in morning["indexes"]}
    for fund in ladder["funds"]:
        assert fund["spot"] == spots[fund["symbol"]]
        expect = round(
            (fund["flip"] - fund["spot"]) / fund["spot"] * 100.0, 2)
        assert fund["flip_distance_pct"] == expect


def test_morning_map_source_reads_panel():
    src = _source("refresh_morning_map.py")
    assert "panel_session_close" in src
    assert "board_bt_bars.json" in src


# ---- Expected Move ----------------------------------------------

def test_expected_move_qqq_current_and_lane_per_name():
    data = _load_json("expected-move/data.json")
    lane = data["filing_lane"]
    latest = lane["latest_completed_session"]
    assert lane["names"]["QQQ"]["newest_session"] == latest
    assert lane["names"]["QQQ"]["missing_sessions"] == []
    assert lane["names"]["SPY"]["newest_session"] == latest
    qqq = [n for n in data["names"] if n["symbol"] == "QQQ"][0]
    assert qqq["receipt"]["session"] == latest


def test_expected_move_source_uses_panel_and_names():
    src = _source("refresh_expected_move.py")
    assert "qqq_covered_sessions" in src
    assert '"names": lane_names' in src


# ---- Panel advance -----------------------------------------------

def test_panel_advance_defaults_to_completed_session():
    assert "freshest_completed_session" in _source(
        "advance_price_panel.py")
    assert "freshest_completed_session" in _source(
        "completed_session.py")
    tools = _source("refresh_tools.py")
    assert 'run_one("advance_price_panel.py")' in tools


def test_panel_session_matches_tape_session():
    panel = _panel()
    panel_last = max(rows[-1][0] for rows in panel.values() if rows)
    premium = _load_json("premium-meter/data.json")
    assert panel_last == premium["freshest_session"]


# ---- Regime Dial ---------------------------------------------------

def test_regime_source_fail_closed_and_chained():
    regime = _source("refresh_regime.py")
    assert "sessions_behind(fear_session, em_session)" in regime
    emap = _source("refresh_expected_move.py")
    assert "refresh_regime.py" in emap
    assert "def main():" in emap


def test_regime_fear_check_current_and_counting():
    dial = _load_json("regime-dial/data.json")
    emap = _load_json("expected-move/data.json")
    spy = [n for n in emap["names"] if n["symbol"] == "SPY"][0]
    fear = [c for c in dial["checks"] if c["id"] == "fear"][0]
    assert fear["session"] == spy["receipt"]["measured_from"]
    assert fear["value"] == spy["vix_close"]
    assert fear["counts"] is True


# ---- Vol Clock -------------------------------------------------------

def test_volclock_source_string_matches_panel():
    data = _load_json("vol-clock/data.json")
    as_of = data["as_of_session"]
    from datetime import date
    long_end = date.fromisoformat(as_of).strftime("%B %d, %Y") \
        .replace(" 0", " ")
    assert f"to {long_end})" in data["source"]
    m = re.search(r"at most (\d+) trading days", data["source"])
    assert m is not None
    panel = _panel()
    assert int(m.group(1)) == max(len(r) for r in panel.values())


def test_volclock_source_computed_not_hardcoded():
    src = _source("refresh_volclock.py")
    assert "max_sessions" in src
    assert '"record (1,833 names, at most 399 trading days "' \
        not in src


# ---- Round 2 tools-a cures (2026-10-31) -------------------------
# MAP-LADDER-CHAIN-20261031, VOLTERM-PANEL-20261031,
# CORR-RUN-DATE-20261031: see BUGLOG_2026-10-31.md.

def test_gamma_ladder_session_matches_morning_map():
    morning = _load_json("morning-map/data.json")
    ladder = _load_json("gamma-ladder/data.json")
    assert ladder["session"] == morning["session"]


def test_static_gex_modelled_ladder_matches_gamma_ladder():
    ladder = _load_json("gamma-ladder/data.json")
    static = _load_json("static-gex/data.json")
    by_sym = {f["symbol"]: f for f in ladder["funds"]}
    for fund in static["funds"]:
        if fund.get("state") != "ok":
            continue
        modelled = fund.get("modelled_ladder") or {}
        rung = by_sym[fund["underlying"]]
        assert fund.get("day") == ladder["session"]
        assert modelled.get("flip") == rung["flip"]
        assert modelled.get("spot") == rung["spot"]
        assert modelled.get("net") == rung["positioning_net"]
        assert modelled.get("call_wall") == rung["call_wall"]
        assert modelled.get("put_wall") == rung["put_wall"]


def test_morning_map_chains_ladder_then_static_gex():
    src = _source("refresh_morning_map.py")
    assert "def main():" in src
    assert "refresh_gammaladder.py" in src
    assert "refresh_staticgex.py" in src
    assert src.index("refresh_gammaladder.py") < src.index(
        "refresh_staticgex.py")


def test_voltermshape_as_of_matches_panel_last_session():
    data = _load_json("vol-term-shape/data.json")
    panel = _panel()
    panel_last = panel["SPY"][-1][0]
    assert data["as_of_session"] == panel_last
    assert f"({len(panel['SPY'])} trading days" in data["source"]
    assert panel_last in data["source"]


def test_engines_runner_records_failure_output():
    src = _source("refresh_engines.py")
    assert "failure output" in src
    assert "write_proof_log" in src


def test_correlation_coverage_date_matches_session():
    data = _load_json("correlation-web/data.json")
    words = (data.get("coverage") or {}).get("words", "")
    m = re.search(r"for (\d{4}-\d{2}-\d{2}) and scored", words)
    assert m is not None
    assert m.group(1) == data["session"]
    assert data.get("scored_run_session") == data["session"]


def test_correlation_source_fails_closed_on_session_mismatch():
    src = _source("refresh_correlation.py")
    assert "run_session != calendar[-1]" in src
    assert "CORR-RUN-DATE-20261031" in src


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
