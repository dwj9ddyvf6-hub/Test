"""Regression blockers for the terminal total audit round 1
tools-b cures (2026-10-31).

Covered cures:
- VERDICT-VOCAB-20261031: the Replication Wire emits an
  "untestable" verdict; the Router and Survivors Wire consumers
  rejected it and could not refresh at all. One shared vocabulary
  (site/verdict_vocabulary.py) now carries every verdict, each
  consumer imports it, and untestable is counted in its own
  bucket, never folded into partly or not_yet.
- BOARD-POSTCLOSE-20261031: the morgue Board ran only in
  preopen and its bar fetch excluded the run day in UTC, so the
  session that just closed was never scored the same evening and
  every board-fed page published one session behind. The
  postclose cycle now rescores the Board and board_card cuts its
  bars at the freshest completed session in America/New_York.
- MANIFEST-STANDALONE-20261031: standalone republishes skipped
  the manifest rebuild, so smoke_check.py failed on the final
  tree. republish_one.sh routes any standalone republish through
  verify_terminal.sh, and both scheduled chains end there too.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "..", "site"))
MORGUE = os.path.expanduser("~/workspace/morgue")
sys.path.insert(0, SITE)


def _load_json(rel):
    with open(os.path.join(SITE, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _source(name, base=SITE):
    with open(os.path.join(base, name), encoding="utf-8") as fh:
        return fh.read()


# ---- verdict vocabulary contract --------------------------------

def test_vocabulary_carries_every_wire_verdict():
    from verdict_vocabulary import VERDICT_WORDS
    wire = _load_json("replication-wire/data.json")
    emitted = {c["verdict"] for c in wire["claims"]}
    assert emitted <= set(VERDICT_WORDS)
    for c in wire["claims"]:
        assert c["verdict_words"] == VERDICT_WORDS[c["verdict"]]
    recomputed = {"total": len(wire["claims"])}
    for v in VERDICT_WORDS:
        recomputed[v] = sum(1 for c in wire["claims"]
                            if c["verdict"] == v)
    assert wire["counts"] == recomputed
    assert recomputed["untestable"] == 6


def test_consumers_import_shared_vocabulary():
    for name in ("refresh_router.py", "refresh_survivorswire.py",
                 "refresh_replicationwire.py"):
        assert "verdict_vocabulary" in _source(name), name


def test_survivors_counts_untestable_in_own_bucket():
    data = _load_json("survivors-wire/data.json")
    counts = data["counts"]
    assert counts["untestable"] == 6
    assert data["untestable_total"] == 6
    wire_line = [r for r in data["per_record"]
                 if "Replication Wire" in r["name"]][0]
    assert wire_line["untestable"] == 6
    assert wire_line["tested"] == (wire_line["held"] if "held" in wire_line
                                    else wire_line["standing"]) \
        + wire_line["partly"] + wire_line["not_standing"]
    assert counts["standing"] + counts["partly"] \
        + counts["not_standing"] + counts["not_yet"] \
        + counts["untestable"] == counts["examined"]
    assert counts["tested"] == counts["examined"] \
        - counts["not_yet"] - counts["untestable"]


def test_router_wire_entry_is_untestable():
    data = _load_json("router/data.json")
    assert data["wire"]["verdict_words"] == \
        "Cannot be tested on the records on hand"
    src = _source("refresh_router.py")
    assert '"untestable"' in src or "!= \"untestable\"" in src


def test_survivors_page_renders_untestable_bucket():
    html = _source(os.path.join("survivors-wire", "index.html"))
    assert "counts.untestable" in html
    assert "untestable_total" in html
    assert "Cannot be tested on the records on hand" in html


# ---- board postclose ---------------------------------------------

def test_daily_cycle_postclose_rescores_board():
    src = _source("daily_cycle.py", base=MORGUE)
    postclose = src.split('mode == "postclose"')[1]
    assert 'run_step("board_card", ["board_card.py"])' in postclose


def test_board_card_cutoff_is_completed_session_et():
    src = _source("board_card.py", base=MORGUE)
    assert "completed_session_cutoff" in src
    assert "America/New_York" in src
    assert "if d >= today:" not in src
    assert "if d > today:" in src


def test_board_full_session_is_freshest_completed():
    from completed_session import freshest_completed_session
    board = json.load(open(os.path.join(
        MORGUE, "output", "board_full.json"), encoding="utf-8"))
    assert board["as_of_session"] == freshest_completed_session()


# ---- manifest routing ---------------------------------------------

def test_republish_wrapper_routes_through_verify():
    src = _source("republish_one.sh")
    assert "verify_terminal.sh" in src
    assert "python3" in src


def test_scheduled_chains_end_with_verify():
    for name in ("refresh_tools.py", "refresh_engines.py"):
        assert "verify_terminal.sh" in _source(name), name


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-q"]))
