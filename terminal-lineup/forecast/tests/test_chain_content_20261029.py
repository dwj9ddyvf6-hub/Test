"""Regression blockers for the chain content cure (2026-10-29):
measured OI/volume wired into snapshots, MODELLED IV inverted
from quote midpoints, Pin Watch pins from real OI, the chain
expected move, and the fresh earnings record. Fixture data only.

Fail direction: every test here imports chain_content (which did
not exist pre-cure) or exercises snapshot fields the pre-cure
collector always stored as null, so the suite fails pre-cure.
"""

import importlib.util
import math
import os

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "site")


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ccx = _load("chain_content_test", "chain_content.py")
cc = _load("collect_chains_content_test", "collect_chains.py")
pw = _load("refresh_pinwatch_content_test", "refresh_pinwatch.py")
emr = _load("refresh_expected_move_content_test",
            "refresh_expected_move.py")
fec = _load("fetch_earnings_content_test",
            "fetch_earnings_calendar.py")


def test_bs_roundtrip_recovers_known_iv():
    for sigma in (0.12, 0.25, 0.60):
        price = ccx.bs_price(100.0, 105.0, 0.25, sigma, True, 0.01)
        got = ccx.implied_vol(price, 100.0, 105.0, 0.25, True, 0.01)
        assert got is not None and abs(got - sigma) < 1e-3
        price = ccx.bs_price(100.0, 95.0, 0.25, sigma, False, 0.01)
        got = ccx.implied_vol(price, 100.0, 95.0, 0.25, False, 0.01)
        assert got is not None and abs(got - sigma) < 1e-3


def test_iv_refuses_uninvertible_quotes():
    # at/below intrinsic: no vol can produce it
    assert ccx.implied_vol(4.9, 100.0, 95.0, 0.25, True) is None
    # one-sided / crossed quotes have no honest midpoint
    assert ccx.quote_mid(0, 5.0) is None
    assert ccx.quote_mid(5.0, 0) is None
    assert ccx.quote_mid(6.0, 5.0) is None
    assert ccx.quote_mid(4.0, 6.0) == 5.0


def test_merge_content_keeps_absent_null_and_measured_zero():
    rows, cov = ccx.merge_content(
        ["SPY261030C00770000", "SPY261030P00770000"],
        {"SPY261030C00770000": 0},
        {"SPY261030P00770000": 1234}, {})
    by = {r[0]: r for r in rows}
    assert by["SPY261030C00770000"][1] == 0        # measured zero
    assert by["SPY261030P00770000"][1] is None     # absent, not 0
    assert by["SPY261030P00770000"][2] == 1234
    assert cov == {"contracts": 2, "with_oi": 1,
                   "with_volume": 1, "with_iv": 0}


def test_snapshot_doc_carries_content_and_labels_iv_modelled():
    doc = cc.build_snapshot_doc(
        "SPY", "2026-10-29", 770.0, "src",
        ["SPY261030C00770000", "SPY261030P00700000"],
        "u", "e",
        oi_by_occ={"SPY261030C00770000": 4321},
        volume_by_occ={"SPY261030C00770000": 99},
        iv_by_occ={"SPY261030P00700000": 0.31},
        oi_date="2026-10-27")
    rows = {r[0]: r for r in doc["rows"]}
    assert rows["SPY261030C00770000"][1] == 4321
    assert rows["SPY261030P00700000"][3] == 0.31
    assert rows["SPY261030P00700000"][1] is None
    assert doc["oi_date"] == "2026-10-27"
    assert "MODELLED" in doc["field_sources"]["iv"]
    assert doc["field_coverage"]["with_oi"] == 1
    assert doc["options_gate"]["iv_states"]["ok"] == 1


def test_heaviest_strike_and_pin_inputs_from_real_oi():
    rows = [["SPY261030C00770000", 100, None, None],
            ["SPY261030P00770000", 900, None, None],
            ["SPY261030C00780000", 5000, None, None],
            ["SPY261030P00780000", 10, None, None],
            ["SPY261030C00790000", None, None, None]]
    h = ccx.heaviest_strikes_by_expiry(rows)
    assert h["2026-10-30"]["strike"] == 780.0
    assert h["2026-10-30"]["total_oi"] == 5010
    assert h["2026-10-30"]["put_oi"] == 10


def test_skew_pair_uses_sided_modelled_rows():
    rows = []
    for strike, civ in ((840.0, 0.20), (847.0, 0.19)):
        rows.append([f"SPY261106C{int(strike*1000):08d}", None, None, civ])
    for strike, piv in ((693.0, 0.30), (700.0, 0.28)):
        rows.append([f"SPY261106P{int(strike*1000):08d}", None, None, piv])
    sk = ccx.skew_pair(rows, 770.0, "2026-10-29")
    assert sk is not None
    assert sk["put_strike"] == 693.0 and sk["call_strike"] == 847.0
    assert sk["skew_points"] == round((0.30 - 0.19) * 100.0, 2)
    assert sk["iv_basis"] == "MODELLED"


def test_chain_expected_move_from_modelled_atm_iv():
    rows = [["SPY261106C00770000", 10, 5, 0.20],
            ["SPY261106P00770000", 10, 5, 0.22],
            ["SPY261106C00850000", 10, 5, 0.19]]
    mv = ccx.chain_expected_move(rows, 770.0, "2026-10-29")
    assert mv is not None and mv["expiry"] == "2026-11-06"
    assert mv["atm_strike"] == 770.0
    assert abs(mv["atm_iv"] - 0.21) < 1e-9
    t = 8.0 / 365.0
    assert abs(mv["points"] - round(770.0 * 0.21 * math.sqrt(t), 2)) < 0.51


def test_earnings_parse_day_payload():
    doc = {"data": {"rows": [{"symbol": "AAPL"}, {"symbol": "ZZZZ"},
                             {"symbol": " msft "}]}}
    out = fec.parse_day_payload(doc, {"AAPL", "MSFT"})
    assert set(out) == {"AAPL", "MSFT"}
