"""Regression blocker for SECOND-OPINION-SPOT-PRECISION-20261119.

Defect (session 2026-11-19, tools lane): refresh_second_opinion.py
refused to publish with "the published summary's positioning spot
for QQQ (645.095) disagrees with the positioning card (645.1)",
which blocked Agent Debate in the tape family (agent-debate/
data.json stayed at 2026-11-18 vs tape 2026-11-19).

Root cause: the morgue feed publishes the positioning spot at
2-decimal precision (morgue/publish_feed.py _map_row:
"spot": round(c["spot"], 2)) — the precision the whole feed
carries — while the positioning card legitimately carries a
third decimal (QQQ spot 645.095). The Second Opinion compared
feed spot to card spot with exact equality, so any card spot
with a non-zero third decimal that rounds at 2dp refused every
coherent run; a re-snapshot returned the identical print, so
no producer re-run could cure it.

Cure: the spot check in refresh_second_opinion.py compares on
the published basis — both operands rounded to 2 decimal
places before equality — exactly as the same file's flip check
already rounds its comparison (to 1dp, the feed's flip
precision). No tolerance is widened beyond the published
precision: a genuine spot disagreement at 2dp still refuses.

Fail direction: against the pre-cure code (exact equality),
test_published_precision_spot_publishes fails (build() == 1 on
the 645.095 vs 645.1 fixture); both tests pass on the cured
code, and the genuine-disagreement test passes on both, proving
the check still stops publication on a real mismatch.

Exercised through the module's real build() entry point, with
load_json redirected at the map card and the feed (the pattern
of test_tools_cascade_guards_20261110.py) and OUT_PATH pointed
at a temp file; every other input is the live file of record.
"""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _run_with_spots(mod, monkeypatch, tmp_path, card_spot, feed_spot):
    """Run build() with QQQ's card spot and feed spot set to the
    given values; all other figures stay as published, so the
    spot check is the only check whose outcome can change."""
    live_map = mod.load_json(mod.MAP_PATH)
    map_fixture = json.loads(json.dumps(live_map))
    for c in map_fixture["cards"]:
        if c["underlying"] == "QQQ":
            c["spot"] = card_spot
    live_feed = mod.load_json(mod.FEED_PATH)
    feed_fixture = json.loads(json.dumps(live_feed))
    for m in feed_fixture["map"]:
        if m["symbol"] == "QQQ":
            m["spot"] = feed_spot
    real_load = mod.load_json

    def redirected(path):
        apath = os.path.abspath(path)
        if apath == os.path.abspath(mod.MAP_PATH):
            return map_fixture
        if apath == os.path.abspath(mod.FEED_PATH):
            return feed_fixture
        return real_load(path)

    monkeypatch.setattr(mod, "load_json", redirected)
    monkeypatch.setattr(mod, "OUT_PATH", str(tmp_path / "data.json"))
    return mod.build()


def test_published_precision_spot_publishes(tmp_path, monkeypatch):
    # The 2026-11-19 case of record: card spot 645.095, feed
    # spot 645.1 == round(645.095, 2), the precision the feed
    # publishes. This must publish.
    mod = importlib.import_module("refresh_second_opinion")
    assert _run_with_spots(mod, monkeypatch, tmp_path,
                           card_spot=645.095, feed_spot=645.1) == 0
    assert os.path.exists(str(tmp_path / "data.json"))


def test_genuine_spot_disagreement_still_refuses(tmp_path, monkeypatch,
                                                  capsys):
    # A real disagreement at published precision (645.095 on the
    # card vs 650.00 in the feed) must still stop publication.
    mod = importlib.import_module("refresh_second_opinion")
    assert _run_with_spots(mod, monkeypatch, tmp_path,
                           card_spot=645.095, feed_spot=650.00) == 1
    err = capsys.readouterr().err
    assert "positioning spot for QQQ" in err, err
    assert not os.path.exists(str(tmp_path / "data.json"))
