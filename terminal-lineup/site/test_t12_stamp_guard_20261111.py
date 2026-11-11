#!/usr/bin/env python3
"""Regression blocker: T12-B0-B3-20261111 (loaded_at_utc stamp +
freshness registry guard).

The defect class (T12-CONTRACTS.md section 1, declaration worklist
steps B0 and B3): the freshness contracts key every SLA to LOAD
time, but the terminal's one shared write path
(terminal_common.write_data_json / stamp_provenance) wrote no load
timestamp at all, so a fresh load of an old reading was
indistinguishable from a stale load except by file mtime, which
copies reset; and nothing checked the contract registry against
the tree, so a served surface could lose (or never gain) its
contract silently.

The cure: stamp_provenance adds a top-level loaded_at_utc at every
stamp, and freshness_guard.py fails closed on any disagreement
among the spec section 2 census set, the registry, and the tree.

Fail direction: the stamp tests fail on the preserved pre-cure
terminal_common.py (~/workspace/.t12fix/pre/), which writes no
loaded_at_utc; the guard's fail directions are proven on fixture
trees mutated from the live registry (a removed contract, an added
contract for a nonexistent surface, a deleted surface directory, a
static exception that grew a data.json, a missing producer), never
by breaking the live registry.

Run standalone or under pytest.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))

import freshness_guard  # noqa: E402
import terminal_common as tc  # noqa: E402


# ---- B0: the loaded_at_utc stamp ---------------------------------

def test_write_data_json_roundtrip_carries_current_loaded_at(tmp_path):
    before = datetime.now(timezone.utc)
    out = tc.write_data_json(str(tmp_path / "data.json"),
                             {"tool": "proof", "figure": 3},
                             feed="filed_records",
                             price_basis="session_record")
    after = datetime.now(timezone.utc)
    disk = json.loads((tmp_path / "data.json").read_text())
    assert disk == out
    ts = tc.parse_ts(disk["loaded_at_utc"])
    assert ts is not None, "loaded_at_utc must be parseable"
    assert before - timedelta(seconds=5) <= ts <= after + timedelta(seconds=5), \
        "loaded_at_utc must be the write moment, not a content date"
    # Existing provenance contract unchanged by the new key.
    assert disk["feed"] == "filed_records"
    assert disk["price_basis"] == "session_record"
    assert disk["execution_pricing"] is False
    assert disk["provenance"]["stamped_by"] == \
        "terminal_common.stamp_provenance"
    assert disk["tool"] == "proof" and disk["figure"] == 3


def test_stamp_for_script_path_also_stamps():
    # The producer path: refresh scripts call stamp_for_script and
    # dump themselves, so the stamp must ride that function too.
    data = {"as_of": "2026-08-14"}
    out = tc.stamp_for_script(data, "refresh_13ftracker.py")
    ts = tc.parse_ts(out["loaded_at_utc"])
    assert ts is not None
    age = abs((datetime.now(timezone.utc) - ts).total_seconds())
    assert age < 60
    assert out["as_of"] == "2026-08-14"  # the reading date is untouched
    assert "loaded_at_utc" not in data  # caller's dict not mutated


def test_stamp_replaces_an_earlier_load_stamp():
    # The anchor names THIS write: re-stamping a doc that already
    # carries a stamp moves the anchor to the new write.
    out = tc.stamp_provenance({"loaded_at_utc": "2020-01-01T00:00:00+00:00"},
                              feed="iex", price_basis="close")
    ts = tc.parse_ts(out["loaded_at_utc"])
    assert ts.year > 2020


def test_reading_date_never_resolves_from_loaded_at():
    # The T12 separation: load time is not a reading date, and the
    # canonical resolver must not treat it as one.
    import freshness
    assert freshness.reading_date(
        {"loaded_at_utc": "2026-11-11T00:00:00+00:00"}) is None


# ---- B3: the registry guard ---------------------------------------

def _fixture_tree(tmp_path, registry):
    """A minimal tree the registry describes: one dir per contract,
    a data.json for produced surfaces, empty producer files, and a
    grok index carrying every contracted href."""
    for contract in registry["contracts"]:
        surface_dir = tmp_path / contract["surface"]
        surface_dir.mkdir(parents=True, exist_ok=True)
        if contract["producer"] != "none":
            (surface_dir / "data.json").write_text("{}\n")
            producer = tmp_path / contract["producer"]
            if not producer.exists():
                producer.write_text("# fixture\n")
    grok = [{"href": c["surface"] + "/"} for c in registry["contracts"]]
    (tmp_path / "grok-index.json").write_text(json.dumps(grok))
    reg_path = tmp_path / "freshness_contracts.json"
    reg_path.write_text(json.dumps(registry))
    return reg_path


def _live_registry():
    return json.loads((SITE / "freshness_contracts.json").read_text())


def test_guard_passes_on_the_live_tree():
    assert freshness_guard.check_registry(str(SITE)) == []


def test_guard_fixture_from_live_registry_passes(tmp_path):
    reg_path = _fixture_tree(tmp_path, _live_registry())
    assert freshness_guard.check_registry(
        str(tmp_path), registry_path=str(reg_path)) == []


def test_guard_fails_when_a_contract_is_removed(tmp_path):
    registry = _live_registry()
    removed = registry["contracts"].pop(0)
    reg_path = _fixture_tree(tmp_path, registry)
    # The surface still exists in the fixture tree (its directory
    # was not the thing removed from the registry copy): rebuild
    # the removed surface's directory so the ONLY defect is the
    # missing contract.
    surface_dir = tmp_path / removed["surface"]
    surface_dir.mkdir(exist_ok=True)
    if removed["producer"] != "none":
        (surface_dir / "data.json").write_text("{}\n")
    breaches = freshness_guard.check_registry(
        str(tmp_path), registry_path=str(reg_path))
    assert any(removed["surface"] in b and "no contract" in b
               for b in breaches), breaches


def test_guard_fails_when_contract_names_a_nonexistent_surface(tmp_path):
    registry = _live_registry()
    ghost = dict(registry["contracts"][0])
    ghost["surface"] = "ghost-surface"
    registry["contracts"].append(ghost)
    reg_path = _fixture_tree(tmp_path, registry)
    breaches = freshness_guard.check_registry(
        str(tmp_path), registry_path=str(reg_path))
    assert any("ghost-surface" in b for b in breaches), breaches


def test_guard_fails_when_a_surface_directory_is_deleted(tmp_path):
    registry = _live_registry()
    reg_path = _fixture_tree(tmp_path, registry)
    import shutil
    shutil.rmtree(tmp_path / "13f-tracker")
    breaches = freshness_guard.check_registry(
        str(tmp_path), registry_path=str(reg_path))
    assert any("13f-tracker" in b and "no longer" in b
               for b in breaches), breaches


def test_guard_fails_when_a_static_exception_grows_a_data_json(tmp_path):
    registry = _live_registry()
    reg_path = _fixture_tree(tmp_path, registry)
    (tmp_path / "greeks-sketch" / "data.json").write_text("{}\n")
    breaches = freshness_guard.check_registry(
        str(tmp_path), registry_path=str(reg_path))
    assert any("greeks-sketch" in b and "data.json" in b
               for b in breaches), breaches


def test_guard_fails_when_a_producer_file_is_missing(tmp_path):
    registry = _live_registry()
    reg_path = _fixture_tree(tmp_path, registry)
    os.remove(tmp_path / "refresh_13ftracker.py")
    breaches = freshness_guard.check_registry(
        str(tmp_path), registry_path=str(reg_path))
    assert any("13f-tracker" in b and "producer" in b
               for b in breaches), breaches


if __name__ == "__main__":
    sys.exit(os.system(
        f"{sys.executable} -m pytest {os.path.abspath(__file__)} -q"))
