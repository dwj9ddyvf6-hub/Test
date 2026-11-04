"""Regression blocker for ECHO-BOARD-ZERO-PUBLISH-20261104.

The Echo Board producer refused to publish any session whose
Second Opinion record honestly contained zero names with two
or more direction-carrying families agreeing, so the page stood
at 2026-10-30 while the record advanced to 2026-11-03. Ruling
2026-11-04: a true zero-agreement board IS the session's data;
the producer now publishes it with an empty name list and the
zero state in plain words. A genuinely missing input (no names
on the record at all, a coverage mismatch) still fails closed.

Fail direction on the pre-cure code: build() returns 1 on the
zero-agreement fixture ("refusing to publish a board with
agreement filled in"), so test_zero_agreement_session_publishes
fails; the fail-closed tests pass on both versions.
"""
import importlib.util
import json
import os

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
spec = importlib.util.spec_from_file_location(
    "refresh_echoboard", os.path.join(SITE, "refresh_echoboard.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

FAMILIES = [{"id": "price", "name": "Price readings"},
            {"id": "prints", "name": "Print readings"},
            {"id": "positioning", "name": "Positioning readings"},
            {"id": "filings", "name": "Filings"}]


def _second(names, coverage):
    return {
        "session": "2026-11-03",
        "board_published_at_utc": "2026-11-04T02:00:00Z",
        "filings_as_of": "2026-11-03",
        "source": "the record behind the Second Opinion",
        "families": FAMILIES,
        "names": names,
        "coverage": coverage,
        "receipt": {"coverage": "fixture coverage"},
    }


def _wire():
    return {"claims": [{
        "claim": "the ranker agreed 0.736 of the time",
        "verdict_words": "Did not hold up",
        "result": "Agreement is not a prediction of what a "
                  "price does next.",
        "sample": "the recorded sessions"}]}


def _proving():
    return {"states": [{"key": "measuring",
                        "words": "Measuring",
                        "definition": "This page measures and "
                                      "reports; it makes no claim "
                                      "of its own."}]}


def _zero_fixture():
    names = [
        {"symbol": "AAA", "families_speaking": 2,
         "directional": ["bold", "cautious"],
         "price": {"stance": "cautious"},
         "prints": {"stance": "bold"}},
        {"symbol": "BBB", "families_speaking": 1,
         "directional": ["cautious"],
         "price": {"stance": "cautious"}},
        {"symbol": "CCC", "families_speaking": 0,
         "directional": []},
    ]
    coverage = {"names_on_record": 3, "two_families": 1,
                "one_family": 1, "no_family": 1}
    return _second(names, coverage)


def _point_at(mod_, tmp_path, second):
    paths = {}
    for key, payload in (("second", second), ("wire", _wire()),
                         ("proving", _proving())):
        p = tmp_path / f"{key}.json"
        p.write_text(json.dumps(payload), encoding="utf-8")
        paths[key] = str(p)
    mod_.SECOND_PATH = paths["second"]
    mod_.WIRE_PATH = paths["wire"]
    mod_.PROVING_PATH = paths["proving"]
    out = tmp_path / "out.json"
    mod_.OUT_PATH = str(out)
    return out


def test_zero_agreement_session_publishes(tmp_path):
    out = _point_at(mod, tmp_path, _zero_fixture())
    assert mod.build() == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["session"] == "2026-11-03"
    assert data["names"] == []
    assert data["zero_words"]
    assert "empty for this day" in data["zero_words"]
    assert data["names_on_record"] == 3


def test_no_names_on_record_still_refuses(tmp_path):
    second = _second([], {"names_on_record": 0, "no_family": 0})
    _point_at(mod, tmp_path, second)
    assert mod.build() == 1


def test_coverage_mismatch_still_refuses(tmp_path):
    second = _zero_fixture()
    second["coverage"] = {"names_on_record": 3, "two_families": 2,
                           "one_family": 1, "no_family": 0}
    _point_at(mod, tmp_path, second)
    assert mod.build() == 1
