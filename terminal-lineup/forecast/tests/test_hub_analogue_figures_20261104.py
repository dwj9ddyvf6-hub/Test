"""Regression blocker for HUB-ANALOGUE-FIGURES-20261104.

The hub's State Analogue card carried hand-written figures
from the day the recorded-days count stood at 1 ("1 of the 126
recorded days ... (the 2026-10-29 session)") while the page's
own data counted 3 recorded sessions with its current reading
from 2026-11-02: the card disagreed with the page it points
at. refresh_hub._collection_figures now recomputes the count
and the session from the page's counts on every run, the same
class as HUB-NOTE-FIGURES-20261104.

Fail direction on the pre-cure code: _collection_figures
returns any card without the words "days on record"
untouched, so the stale figures survive and both tests fail;
they pass on the cured code.
"""
import importlib.util
import json
import os

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
spec = importlib.util.spec_from_file_location(
    "refresh_hub", os.path.join(SITE, "refresh_hub.py"))
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)

CARD = (
    '<p class="figline">1 of the 126 recorded days it needs '
    'is on record</p><details><summary>Full note</summary><p>'
    'the history is still being built, with 1 of the 126 '
    'recorded days it needs on record (the 2026-10-29 '
    'session), so the page keeps the honest count and shows '
    'no matches yet.</p></details>')


def test_analogue_figures_recomputed_from_counts(tmp_path,
                                                 monkeypatch):
    monkeypatch.setattr(hub, "HERE", tmp_path)
    mod_dir = tmp_path / "state-analogue"
    mod_dir.mkdir()
    (mod_dir / "data.json").write_text(json.dumps({
        "counts": {"sessions_recorded": 3,
                   "sessions_needed": 126},
        "as_of_session": "2026-11-02"}))
    out = hub._collection_figures("state-analogue", CARD)
    assert "3 of the 126 recorded days it needs is on record" \
        in out
    assert "with 3 of the 126 recorded days it needs on " \
        "record (the 2026-11-02 session)" in out
    assert "2026-10-29" not in out


def test_analogue_card_untouched_without_counts(tmp_path,
                                                monkeypatch):
    monkeypatch.setattr(hub, "HERE", tmp_path)
    mod_dir = tmp_path / "state-analogue"
    mod_dir.mkdir()
    (mod_dir / "data.json").write_text(json.dumps({}))
    out = hub._collection_figures("state-analogue", CARD)
    assert out == CARD
