"""Regression blockers for WEEK-READINESS-R2-20261102 Cure 1.

Classes covered:
E. Replication Wire exact-state pin: the 5-day board grades landing
   on schedule refused every refresh forever ("wording is stale").
   The wording is now built from the record's actual horizon
   states. Fail-first: pre-cure source carried the exact
   not_yet_graded pin for 5d/21d and a hard-coded landing sentence.
F. Band chart overlap: VisualKit.band drew the row label on the
   same line as the bar, left of the plot, so the widest band ran
   into its label (Corrected Band nit). Label now sits on its own
   line above a full-width bar; the Corrected Band adapter labels
   each row with its band level.
G. Morning Map lead drew only the first index and read as an
   empty chart. It now draws one levels ladder per index.
H. Headline as_of: 13f-tracker, smart-money-tracker and
   odds-cards carried no canonical as_of; promoted-book and
   one-page-report carried none and were census gaps. Producers
   now stamp a true date, or an explicit honest null with a note.
I. Wall chain agreement: wall-check's published card count must
   equal the grading record's card count (the stale 18 vs 21
   split refused Wall Lifetime).
J. Proof gate recount: the gate file's ledger_rows must recount
   against the forecast ledger (the stale 31,649 vs 34,316 split
   refused In-Regime Oracle).
"""
import json
import pathlib
import sys

SITE = pathlib.Path(__file__).resolve().parents[2] / "site"
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SITE))


def _src(name):
    return (SITE / name).read_text()


def _data(page):
    return json.loads((SITE / page / "data.json").read_text())


# ---- E: replication wire ----
def test_replication_no_exact_state_pin():
    src = _src("refresh_replicationwire.py")
    assert 'pub["5d"]["state"] != "not_yet_graded"' not in src
    assert "grades have landed, so this page's wording is stale" not in src
    assert "_horizon_words" in src


def test_replication_live_wording_matches_scorecard():
    sc = json.loads(pathlib.Path(
        "/home/hatch/workspace/morgue/output/scorecard.json"
    ).read_text())
    pub = sc["board"]["published"]["horizons"]
    d = _data("replication-wire")
    claims = d.get("claims") or []
    live = [c for c in claims
            if "live published stock calls" in (c.get("claim") or "")]
    assert live, "live board claim missing"
    result = live[0]["result"]
    if pub["5d"]["state"] == "graded":
        assert f"At 5 days: {pub['5d']['n_mature']} published calls graded" in result
    if pub["21d"]["state"] == "not_yet_graded":
        assert "21 days grades are" in result


# ---- F: band overlap ----
def test_band_label_on_own_line():
    src = _src("visual.js")
    assert "var plotL = 0, plotR = 470;" in src
    assert '(y + 17)' in src  # bar below the label line


def test_corrected_band_rows_carry_level():
    src = _src("engine-visual.js")
    assert 'b.level + " percent band"' in src


# ---- G: morning map ----
def test_morning_map_draws_every_index():
    src = _src("tool-visual.js")
    assert "(d.indexes || []).forEach" in src
    assert 'var idx = (d.indexes || [])[0];' not in src


# ---- H: headline as_of stamps ----
def test_asof_producer_stamps():
    assert '"as_of": max((h.get("filed")' in _src("refresh_13ftracker.py")
    assert '"as_of": cur_filed[-1] if cur_filed else None' in \
        _src("refresh_smartmoney.py")
    assert '"as_of": "2026-10-27"' in _src("refresh_oddscards.py")
    assert '"as_of": None' in _src("refresh_promotedbook.py")
    assert '"as_of": None' in _src("refresh_onepagereport.py")
    assert "as_of_note" in _src("refresh_promotedbook.py")
    assert "as_of_note" in _src("refresh_onepagereport.py")


def test_asof_live_values():
    d = _data("13f-tracker")
    filed = [h.get("filed") for h in d["holders"] if h.get("filed")]
    assert d.get("as_of") == max(filed)
    d = _data("smart-money-tracker")
    assert d.get("as_of") == d.get("current_filed_last")
    d = _data("odds-cards")
    assert d.get("as_of") == "2026-10-27"
    for page in ("promoted-book", "one-page-report"):
        d = _data(page)
        assert "as_of" in d and d["as_of"] is None
        assert d.get("as_of_note")


def test_gap_split_sums_every_band():
    src = _src("refresh_replicationwire.py")
    assert 'sum(b["n"] for b in bands.values())' in src
    assert "extra_bands" in src


def test_wall_spot_compared_on_card_basis():
    src = _src("refresh_walllifetime.py")
    assert 'e.get("snapshot_spot"' in src


# ---- I: wall chain agreement ----
def test_wallcheck_agrees_with_scorecard():
    sc = json.loads(pathlib.Path(
        "/home/hatch/workspace/morgue/output/scorecard.json"
    ).read_text())
    wc = _data("wall-check")
    assert wc["cards_of_record"] == sc["counters"]["map_cards_of_record"]
    assert wc["totals"]["tests"] == len(sc["map"]["grades"])


# ---- J: proof gate recount ----
def test_proof_gate_recounts():
    from proof_gate_block import recount_forward_rows
    gate = _data("proof-gate")
    ledger = ROOT / "forecast" / "ledger.jsonl"
    distinct, total = recount_forward_rows(str(ledger))
    fwd = gate["forward_ledger"]
    assert fwd["created"] == distinct
    assert fwd["ledger_rows"] == total


# ---- M: session history same-session replacement ----
def test_session_history_replaces_same_session(tmp_path):
    import session_history as sh
    store = str(tmp_path / "session-history.json")
    sh.append_session(store, "2026-10-30", [{"symbol": "SPY", "flip": 1.0}])
    out = sh.append_session(store, "2026-10-30",
                            [{"symbol": "SPY", "flip": 2.0}])
    assert len(out) == 1
    assert out[0]["values"][0]["flip"] == 2.0
    out = sh.append_session(store, "2026-11-02",
                            [{"symbol": "SPY", "flip": 3.0}])
    assert [s["session"] for s in out] == ["2026-10-30", "2026-11-02"]


def test_session_history_live_stores_have_no_duplicate_sessions():
    for page in ("morning-map", "gamma-ladder", "agent-debate",
                 "sponsored-reset"):
        path = SITE / page / "session-history.json"
        if not path.exists():
            continue
        sessions = json.loads(path.read_text())["sessions"]
        dates = [s["session"] for s in sessions]
        assert len(dates) == len(set(dates)), page


# ---- N: attestation resync wired into the engine runner ----
def test_attestation_resync_wired_after_engine_loop():
    src = _src("refresh_engines.py")
    assert "attestation-refresh-final" in src
    assert "reattach_attestations.py" in src
    # the resync must sit after the per-engine loop, not before it
    assert src.index("attestation-refresh-final") > src.index(
        "for slug in engine_slugs()")
