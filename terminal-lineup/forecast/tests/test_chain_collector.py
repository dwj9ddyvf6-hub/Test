"""Regression blockers for the chain snapshot collector
(site/collect_chains.py): payload validation, snapshot shaping and
manifest lines, on fixture payloads only (no network, no keys)."""

import importlib.util
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "site")
_spec = importlib.util.spec_from_file_location(
    "collect_chains", os.path.join(SITE, "collect_chains.py"))
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)


def fixture_payload(symbol="SPY"):
    return {"data": {"items": [{
        "underlying-symbol": symbol,
        "expirations": [
            {"expiration-date": "2026-10-30", "strikes": [
                {"strike-price": "750.0",
                 "call": f"{symbol}   261030C00750000",
                 "put": f"{symbol}   261030P00750000"},
                {"strike-price": "755.0",
                 "call": f"{symbol}   261030C00755000",
                 "put": f"{symbol}   261030P00755000"}]},
            {"expiration-date": "2026-11-06", "strikes": [
                {"strike-price": "750.0",
                 "call": f"{symbol}   261106C00750000",
                 "put": f"{symbol}   261106P00750000"}]},
        ]}]}}


def test_validate_good_payload_counts_and_normalizes():
    stats = cc.validate_chain_payload(fixture_payload(), "SPY")
    assert stats["expirations"] == 2
    assert stats["strikes"] == 3
    assert stats["contracts"] == 6
    assert "SPY261030C00750000" in stats["rows"]
    assert all(" " not in r for r in stats["rows"])


def test_validate_rejects_wrong_underlying():
    with pytest.raises(ValueError):
        cc.validate_chain_payload(fixture_payload("QQQ"), "SPY")


def test_validate_rejects_no_expirations():
    doc = fixture_payload()
    doc["data"]["items"][0]["expirations"] = []
    with pytest.raises(ValueError):
        cc.validate_chain_payload(doc, "SPY")


def test_validate_rejects_empty_strikes():
    doc = fixture_payload()
    doc["data"]["items"][0]["expirations"][0]["strikes"] = []
    with pytest.raises(ValueError):
        cc.validate_chain_payload(doc, "SPY")


def test_validate_rejects_missing_occ():
    doc = fixture_payload()
    del doc["data"]["items"][0]["expirations"][0]["strikes"][0]["put"]
    with pytest.raises(ValueError):
        cc.validate_chain_payload(doc, "SPY")


def test_validate_rejects_unparseable_occ():
    doc = fixture_payload()
    doc["data"]["items"][0]["expirations"][0]["strikes"][0]["call"] = \
        "NOTANOCC"
    with pytest.raises(ValueError):
        cc.validate_chain_payload(doc, "SPY")


def test_validate_rejects_duplicate_occ():
    doc = fixture_payload()
    doc["data"]["items"][0]["expirations"][1]["strikes"][0]["call"] = \
        "SPY   261030C00750000"
    with pytest.raises(ValueError):
        cc.validate_chain_payload(doc, "SPY")


def test_snapshot_doc_matches_consumer_shape():
    stats = cc.validate_chain_payload(fixture_payload(), "SPY")
    doc = cc.build_snapshot_doc("SPY", "2026-10-29", 769.36, "src",
                                stats["rows"], "u", "e")
    assert doc["underlying"] == "SPY" and doc["day"] == "2026-10-29"
    assert doc["spot"] > 0
    assert doc["columns"][:1] == ["occ"]
    assert {"oi", "volume", "iv"} <= set(doc["columns"][1:])
    assert len(doc["rows"]) == 6
    for row in doc["rows"]:
        assert len(row) == len(doc["columns"])
        assert cc.OCC_RE.match(row[0])
        # absent data is null, never a fabricated zero
        assert row[1] is None and row[2] is None and row[3] is None


def test_manifest_ok_and_error_lines():
    stats = {"expirations": 2, "strikes": 3, "contracts": 6}
    ok = cc.manifest_line("2026-10-29T22:40:00Z", "2026-10-29T18:40:00-0400",
                          "SPY", "ok", stats=stats, nbytes=123,
                          sha256="ab" * 32, path="/x/SPY.json.gz")
    assert ok["status"] == "ok" and ok["expirations"] == 2
    assert ok["strikes"] == 3 and ok["bytes"] == 123
    assert ok["sha256"] == "ab" * 32 and ok["ts_et"].endswith("-0400")
    err = cc.manifest_line("u", "e", "QQQ", "error",
                           error="ValueError: no expirations")
    assert err["status"] == "error" and "no expirations" in err["error"]


def test_market_window():
    et = ZoneInfo("America/New_York")
    thu_10am = datetime(2026, 10, 29, 10, 0, tzinfo=et)
    thu_7pm = datetime(2026, 10, 29, 19, 0, tzinfo=et)
    sat_10am = datetime(2026, 10, 31, 10, 0, tzinfo=et)
    assert cc.in_market_window(thu_10am)
    assert not cc.in_market_window(thu_7pm)
    assert not cc.in_market_window(sat_10am)
