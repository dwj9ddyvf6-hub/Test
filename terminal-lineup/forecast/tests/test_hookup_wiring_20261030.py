"""Regression blockers for the 2026-10-30 hookup (stream 2:
pipelines and refresh). Each test pins one consumer/producer
wiring cure at the source. Fail direction: on the pre-cure tree,
the Pin Watch page read fields its refresher no longer publishes,
the IV Weather and Skew pages had no modelled group or figures at
all, the Echo Lens published no readings, the Filings Wire
published no symbol for any company, the Second Opinion prints /
facts / news families never spoke, the One-Page Report carried a
hardcoded empty filings section, Engine 10 had no per-name heat
source and its outcome kind had no resolver, and Engine 19 counted
the Aperture proof-gate rows as its own weekly windows.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grading as G  # noqa: E402

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
MORGUE = os.path.expanduser("~/workspace/morgue")
LEDGER = os.path.expanduser(
    "~/workspace/terminal-lineup/forecast/ledger.jsonl")


def load(slug):
    with open(os.path.join(SITE, slug, "data.json")) as fh:
        return json.load(fh)


def test_pin_watch_page_fields_exist_in_data():
    d = load("expiry-pin-watch")
    page = open(os.path.join(SITE, "expiry-pin-watch",
                             "index.html")).read()
    assert "pin.strike" in page and "snapshot_day" in page
    n = d["names"][0]
    for key in ("symbol", "spot", "snapshot_day", "oi_date",
                "expiries", "expiry_count_with_oi", "contracts",
                "contracts_with_oi"):
        assert key in n, key
    for key in ("strike", "expiry", "call_oi", "put_oi", "total_oi"):
        assert key in n["pin"], key
    assert n["pin"]["total_oi"] == \
        n["pin"]["call_oi"] + n["pin"]["put_oi"]


def test_iv_weather_modelled_group_is_separate_and_labelled():
    d = load("iv-weather")
    assert len(d["groups"]) == 4
    g4 = d["groups"][3]
    assert "Modelled" in g4["heading"]
    names = {r["symbol"] for g in d["groups"] for r in g["names"]}
    assert {"SPY", "QQQ", "IWM"} <= names
    assert {r["symbol"] for r in g4["names"]} == {"SPY", "QQQ", "IWM"}


def test_skew_modelled_figure_obeys_the_stated_band():
    d = load("skew-lens")
    figs = {f["symbol"]: f for f in d["modelled_figures"]}
    assert "QQQ" in figs
    f = figs["QQQ"]
    assert f["put_strike"] < f["call_strike"]
    assert abs(f["points"] - round(
        f["put_percent"] - f["call_percent"], 1)) < 0.11
    assert set(d["modelled_no_figure"]) == {"SPY", "IWM"}
    # Independent recompute of the band from the modelled ledger:
    # on the figure's date, the chosen strikes must sit inside the
    # page's stated 9 to 11 percent band around the spot.
    rows = {}
    path = os.path.join(MORGUE, "state", "morgue", "chains",
                        "iv_ledger_modelled.jsonl")
    for line in open(path):
        r = json.loads(line)
        rows[(r["date"], r["underlying"], r["occ"])] = r
    day = [r for (dt, s, _), r in rows.items()
           if dt == f["date"] and s == "QQQ"
           and r["expiry"] == f["expiry"]]
    spot = day[0]["spot"]
    put = next(r for r in day if r["side"] == "put"
               and r["strike"] == f["put_strike"])
    call = next(r for r in day if r["side"] == "call"
                and r["strike"] == f["call_strike"])
    assert 0.09 <= (spot - put["strike"]) / spot <= 0.11
    assert 0.09 <= (call["strike"] - spot) / spot <= 0.11


def test_echo_lens_publishes_the_store_readings():
    d = load("echo-lens")
    store_path = os.path.join(MORGUE, "state", "morgue", "echo",
                              d["lens_session"] + ".json")
    with open(store_path) as fh:
        store = json.load(fh)
    assert d["state"] == "on_record"
    assert d["covered_count"] == len(store["readings"])
    assert len(d["readings"]) == len(store["readings"])
    r = d["readings"][0]
    for key in ("symbol", "verdict", "words", "session",
                "session_long"):
        assert key in r, key


def test_filings_wire_joins_every_company_to_a_tracked_symbol():
    d = load("filings-wire")
    assert len(d["companies"]) == 43
    for c in d["companies"]:
        assert c["symbol"], c["company_name"]
        assert c["company_name"]
    oxy = next(c for c in d["companies"] if c["symbol"] == "OXY")
    assert "OCCIDENTAL" in oxy["company_name"]


def test_second_opinion_families_speak_from_the_stores():
    d = load("second-opinion")
    cov = d["coverage"]
    assert cov["prints_names_on_file"] == 52
    assert cov["facts_names_on_file"] == 43
    dist_keys = ("no_family", "one_family", "two_families", "three_families",
                 "four_families", "five_families", "six_families")
    assert sum(cov[k] for k in dist_keys) == len(d["names"])
    speaking = {}
    for fam in ("prints", "facts", "news"):
        speaking[fam] = sum(1 for n in d["names"] if n.get(fam))
    # Speaking counts tie to the stores, not to constants: the
    # news store accrues articles daily, so a pinned 30 went
    # stale the day the store spoke for 32 names (2026-10-30).
    assert speaking["facts"] == cov["facts_names_on_file"]
    assert speaking["prints"] == cov["prints_names_on_file"]
    news_store = json.load(open(os.path.join(
        MORGUE, "state", "morgue", "news",
        cov["news_store_date"] + ".json")))
    with_articles = sum(1 for v in news_store["symbols"].values()
                        if v)
    assert speaking["news"] == with_articles


def test_one_page_report_filings_section_is_populated():
    d = load("one-page-report")
    assert d["filings_names_covered"] == 43
    assert d["names"]["ACN"]["filings"]
    assert sum(d["coverage_distribution"].values()) == 1838


def test_one_page_report_receipt_recomputes_and_moves_pass_through():
    # Semantic audit finding 2 (2026-10-30): the receipt was a
    # hardcoded string (unusual volume 61 against 119 listed,
    # earnings dates 73 against 46, pattern labels 1,817 against
    # 1,816) and the earnings section denied a priced-move record
    # that exists while its join nulled the figure. The receipt
    # must recompute from the page's own shipped sections and the
    # priced moves must pass through from the calendar record.
    src = open(os.path.join(SITE, "refresh_onepagereport.py")).read()
    assert "unusual volume lists 61" not in src
    assert "a date for 73" not in src
    assert "for 1,817" not in src
    d = load("one-page-report")
    ec = load("earnings-calendar")
    uv = load("unusual-volume")
    n_labels = sum(1 for e in d["names"].values()
                   if e["chart"] and e["chart"].get("label"))
    assert f"unusual volume lists {len(uv['names'])}" in d["receipt"]
    assert f"a date for {ec['dated_names']}" in d["receipt"]
    assert f"pattern label for {n_labels:,}" in d["receipt"]
    priced = {n["symbol"]: n["expected_move"] for n in ec["names"]
              if n.get("expected_move")}
    assert priced, "calendar record carries no priced moves to check"
    for sym, mv in priced.items():
        assert d["names"][sym]["earnings"]["expected_move"] == mv, sym
    about = [s for s in d["sections"] if s["id"] == "earnings"][0]
    assert "No priced expected move is on record for any name" \
        not in about["about"]


def test_engine10_pername_heat_source_and_ledger_rows():
    d = load("insider-divergence")
    pn = d["pername_today"]
    assert pn is not None and pn["overlap"]
    assert d["coverage"]["both_pername"] == len(pn["overlap"])
    rows = [json.loads(l) for l in open(LEDGER)]
    e10 = [r for r in rows if r.get("engine_id") == "engine_10"
           and r.get("type") == "forecast"]
    assert e10, "Engine 10 has ledgered no forecasts"
    assert all((r["value"] or {}).get("heat_source")
               == "per-name tape store" for r in e10)
    assert all(r["outcome"]["kind"] == "excess_21s" for r in e10)


def test_engine19_live_record_counts_only_its_own_windows():
    d = load("in-regime-oracle")
    rows = [json.loads(l) for l in open(LEDGER)]
    windows = [r for r in rows if r.get("engine_id") == "engine_19"
               and r.get("type") == "forecast"
               and (r.get("outcome") or {}).get("kind")
               == "next_window_hit_rate_exceeds_trailing"]
    assert d["live_record"]["forecasts_recorded"] == len(windows)
    proof = [r for r in rows if r.get("engine_id") == "engine_19"
             and r.get("type") == "forecast"
             and (r.get("outcome") or {}).get("kind")
             == "provisional_proof_forward_check"]
    assert len(proof) == 4641  # reported in the proof_gate block


class _Prices:
    path = "fixture"

    def __init__(self):
        self.bars = {
            "ACN": {"2026-10-29": (0, 0, 0, 100.0),
                    "2026-11-27": (0, 0, 0, 110.0)},
            "SPY": {"2026-10-29": (0, 0, 0, 200.0),
                    "2026-11-27": (0, 0, 0, 210.0)}}
        self.calendars = {s: sorted(t) for s, t in self.bars.items()}
        self.volumes = {}

    def close(self, sym, date):
        return self.bars[sym][date][3]


def test_excess_21s_resolver_scores_points_against_benchmark():
    realised, binary = G.resolve_outcome(
        {"kind": "excess_21s", "symbol": "ACN", "benchmark": "SPY",
         "base_date": "2026-10-29", "at_date": "2026-11-27"},
        _Prices())
    assert binary is None
    assert abs(realised - 5.0) < 1e-9  # +10% vs +5%, in points
    assert "excess_21s" in G._RESOLVABLE_KINDS


def test_proof_gate_grading_caller_is_wired():
    src = open(os.path.join(os.path.dirname(__file__), "..",
                            "run_grading.py")).read()
    assert "grade_forward_record" in src
    assert "provisional_proof_forward_check" in src


# --- Chain-run cures, 2026-10-30 replay: the full tools chain run
# surfaced four legs that refused on coherent records. Each test
# below fails on the pre-cure tree.

def test_fearday_skips_null_vix_closes():
    # Yahoo's VIX payload carries null closes on market holidays;
    # the unguarded float(close) crashed the leg.
    src = open(os.path.join(SITE, "refresh_fearday.py")).read()
    assert "if close is None:" in src
    d = load("fear-day")
    assert d["state"] == "unpublished"  # honest state preserved


def test_squeeze_provenance_describes_the_pit_vintage():
    # The PIT store is append-only (first vintage wins); the
    # provenance percentage must be computed from the recorded
    # reading, not from a later re-gather's shares basis.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "inst_bundle", os.path.join(MORGUE, "inst_bundle.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    src = open(os.path.join(MORGUE, "inst_bundle.py")).read()
    assert 'recorded["si_shares"]' in src
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        pit = os.path.join(td, "pit.jsonl")
        first = {"symbol": "FTRE", "settlement_date": "2026-10-15",
                 "si_shares": 100.0, "float_shares": 1000.0}
        newer = dict(first, float_shares=2000.0)
        assert mod._pit_append(pit, first)["float_shares"] == 1000.0
        recorded = mod._pit_append(pit, newer)
        assert recorded["float_shares"] == 1000.0  # first vintage


def test_watchlist_speaks_the_six_family_language():
    src = open(os.path.join(SITE, "refresh_watchlistpulse.py")).read()
    assert '"facts", "news")' in src
    assert 'n[k].get("stance")' in src
    d = load("watchlist-pulse")
    so = load("second-opinion")
    assert d["session"] == so["session"]
    cov, scov = d["coverage"], so["coverage"]
    for key in ("no_family", "one_family", "two_families",
                "three_families", "four_families", "five_families",
                "six_families"):
        assert cov[key] == scov[key], key


def test_holly_ideas_joined_record_semantics():
    src = open(os.path.join(SITE, "refresh_hollyideas.py")).read()
    assert "is not a session The " not in src
    assert "board_session_in_record" in src
    d = load("holly-ideas")
    board = load("board")
    assert d["session"] == board["session"]
    assert d["board_session_in_record"] == (
        d["session"] in d["record_sessions"])


def test_proving_ground_checks_the_current_records():
    # The evidence layer pinned the pre-cure empty states (hub
    # set equality, ungraded tape note, 0-of-126 analogue,
    # not-collecting short volume, 0 filings, 0 snapshots, empty
    # skew, 0 pins) and refused every run once those lanes landed.
    src = open(os.path.join(SITE, "refresh_provingground.py")).read()
    assert "classified <= set(hub_links)" in src
    assert "tape_totals" in src
    assert '== "not_yet_collecting"' not in src
    assert '== "no_snapshot_yet"' not in src
    assert '== "no_open_interest_picture_yet"' not in src
    d = load("proving-ground")
    assert d["tools_count"] == 42
    assert sum(d["counts"].values()) == 42
