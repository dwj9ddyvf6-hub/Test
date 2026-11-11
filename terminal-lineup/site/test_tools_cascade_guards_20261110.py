"""Regression blocker for TOOLS-CORE-CASCADE-20261110 (Wave W2).

Failure of record: the 19:00 tools refresh failed three
consecutive nights (2026-11-08, 11-09, 11-10) with a persistent
core of eight refreshers. W2's root-cause pass (census SYS-1)
traced four of the eight to a cascade, not to defects in their
own code: the postclose Morning Map card was published with its
FINRA dark-pool (DIX) leg null (two successive morgue map_dix
transport defects, MAP-DIX-TRANSPORT-ERROR-20261109 and
MAP-DIX-RESUME-READ-20261110, both cured at source in the morgue
with their own blockers), and the consumers refused to publish
against the defective card:

- refresh_gammaladder: "the positioning card is dated None, not
  the published session" (its top-level dix_date check);
- refresh_second_opinion: its named Null-DIX guard (2026-11-04)
  "the positioning card carries no dark pool reading for SPY";
- refresh_morning_map: its chained Gamma Ladder re-run failed
  on the same card check;
- refresh_intakebias: refused on the same card's short-share
  date (the forecast lane's leg; guarded by that lane's tests).

Those refusals are the fail-closed design working: a consumer
that published anyway would have served figures built on a
missing leg. This blocker pins the two refusal mechanisms that
live in this directory, exercised through the modules' real
build() entry points with only their input paths redirected
into a fixture directory (Gamma Ladder) or, for Second Opinion,
with load_json redirected at the one defective input and every
other input at the live file of record. Each test asserts the
named refusal fires on the defective card shape of record; a
future "fix the nightly red" pass that softens either guard
into publishing on a null DIX leg fails here.

Fail direction: verified 2026-11-11 on a /tmp copy of the
site tree with the Null-DIX guard block deleted from
refresh_second_opinion.py: the Second Opinion test fails
there (the build crashes on round(None) instead of refusing,
the exact 2026-11-04 failure the guard was written for), and
all three tests pass on the cured tree. The pre-cure record
agrees: these guards are what produced the 11-09/11-10
refusals.
"""
import importlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DEFECTIVE_CARDS = [{"underlying": s, "dix_ratio": None,
                    "dix_date": None, "spot": 1.0}
                   for s in ("SPY", "QQQ", "IWM")]


def _write(path, doc):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)


def test_gammaladder_refuses_null_dix_card(tmp_path, capsys):
    mod = importlib.import_module("refresh_gammaladder")
    # A minimal Morning Map published record at session
    # 2026-11-10, naming all three funds, so build() reaches the
    # positioning-card date check (the refusal of record).
    _write(str(tmp_path / "map_data.json"), {
        "session": "2026-11-10", "generated_at_utc": "T0",
        "contract": {"source_session": {"value": "2026-11-10"}},
        "indexes": [{"symbol": s} for s in ("SPY", "QQQ", "IWM")]})
    _write(str(tmp_path / "card.json"), {
        "dix_date": None, "built_utc": "T0", "cards": DEFECTIVE_CARDS})
    for name in ("pinwatch.json", "proving.json"):
        _write(str(tmp_path / name), {})
    mod.MAP_DATA_PATH = str(tmp_path / "map_data.json")
    mod.CARD_PATH = str(tmp_path / "card.json")
    mod.PINWATCH_PATH = str(tmp_path / "pinwatch.json")
    mod.PROVING_PATH = str(tmp_path / "proving.json")
    assert mod.build() == 1
    err = capsys.readouterr().err
    assert "positioning card is dated None" in err, err


def test_second_opinion_null_dix_guard_fires(tmp_path, monkeypatch):
    mod = importlib.import_module("refresh_second_opinion")
    live = mod.load_json(mod.MAP_PATH)
    defective = json.loads(json.dumps(live))
    for c in defective["cards"]:
        c["dix_ratio"] = None
        c["dix_date"] = None
    real_load = mod.load_json

    def redirected(path):
        if os.path.abspath(path) == os.path.abspath(mod.MAP_PATH):
            return defective
        return real_load(path)

    monkeypatch.setattr(mod, "load_json", redirected)
    assert mod.build() == 1


def test_morning_map_still_chains_gammaladder():
    # Morning Map has no card check of its own; its guard is the
    # chain: it re-runs Gamma Ladder on republication and
    # propagates the failure. Pin that the chain still exists.
    with open(os.path.join(HERE, "refresh_morning_map.py"),
              encoding="utf-8") as fh:
        src = fh.read()
    assert "refresh_gammaladder.py" in src, (
        "Morning Map no longer chains the Gamma Ladder re-run; "
        "its 2026-11-09/10 failure mode (the chained refusal) "
        "would become a silent stale ladder instead")
