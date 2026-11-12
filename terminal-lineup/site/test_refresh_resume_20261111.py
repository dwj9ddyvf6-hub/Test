"""Regression blocker for REFRESH-RESUME-20261111.

The forecast refresh runner held the whole run in memory and
wrote its proof log only at the end, so any kill burned the
entire run: a 2026-11-10 OOM kill inside self-analogue after
~2.9 hours, and a 2026-11-11 machine restart at
gamma-earnings-trap, after which the next invocation restarted
from zero. The same runner also consumed site/board/data.json
without ever republishing it: the republishing step lived only
in the 19:00 tools refresh, after the 17:46 engine refresh, so
the abstention-signal leg's board freshness check read a
one-generation-stale page and failed closed on a healthy record
(the morgue's card for the just-completed session had been
published at 16:59 ET that day).

The cure makes the runner checkpointed and resumable (per-step
completion for the current session, flushed as each step
finishes; a fresh invocation skips steps proven complete,
retries failed ones, and invalidates the verification tail
whenever an upstream step completes after it), streams the
proof log as lines are produced, serialises invocations with a
flock, and republishes the Board inside its own spine before
the engine loop. These tests pin those semantics and the
preserved summary contract. Set RUNNER_MODULE_DIR to a
directory holding a pre-cure copy of refresh_engines.py to
watch them fail.
"""
import importlib.util
import os
import sys

import pytest

MODULE_DIR = os.environ.get(
    "RUNNER_MODULE_DIR", os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(MODULE_DIR, "refresh_engines.py")

sys.path.insert(0, MODULE_DIR)
spec = importlib.util.spec_from_file_location("refresh_engines", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SOURCE = open(PATH, encoding="utf-8").read()


def _cp(tmp_path, session="2026-11-11"):
    mod.CHECKPOINT = tmp_path / "refresh_checkpoint.json"
    return mod._Checkpoint(session)


def test_checkpoint_records_completion_and_failures(tmp_path):
    cp = _cp(tmp_path)
    cp.mark("deep-panel-advance", 0, 12.0)
    cp.mark("self-analogue", 9, 643.0,
            "self-analogue (refresh_selfanalogue.py exited -9)")
    cp.save()
    again = mod._Checkpoint.load("2026-11-11")
    assert again is not None
    assert again.done("deep-panel-advance") is True
    # A failed step is never skippable, and its failure is the
    # session's failure until a retry clears it.
    assert again.done("self-analogue") is False
    assert again.ordered_failures(["self-analogue"]) == [
        "self-analogue (refresh_selfanalogue.py exited -9)"]
    again.mark("self-analogue", 0, 900.0)
    assert again.done("self-analogue") is True
    assert again.ordered_failures(["self-analogue"]) == []


def test_checkpoint_is_session_keyed_and_completion_closes_it(tmp_path):
    cp = _cp(tmp_path, session="2026-11-10")
    cp.mark("forecast-grading", 0, 127.0)
    cp.save()
    # A different session never resumes another session's run.
    assert mod._Checkpoint.load("2026-11-11") is None
    # A completed run is not resumed either: a deliberate
    # re-run for the session re-proves everything.
    cp.complete = True
    cp.save()
    assert mod._Checkpoint.load("2026-11-10") is None


def test_upstream_completion_invalidates_the_verification_tail(tmp_path):
    cp = _cp(tmp_path)
    for key in mod.FINAL_STEPS:
        cp.mark(key, 0, 1.0)
    assert all(cp.done(k) for k in mod.FINAL_STEPS)
    # A tail step completing invalidates only later tail steps.
    cp.mark("record", 0, 1.0)
    assert cp.done("attestation-refresh-final") is True
    assert cp.done("record") is True
    assert cp.done("smoke") is False
    assert cp.done("publish-live") is False
    # An upstream step completing after the tail voids the whole
    # tail: its proofs described an intermediate tree.
    for key in mod.FINAL_STEPS:
        cp.mark(key, 0, 1.0)
    cp.mark("gap-destiny", 0, 2000.0)
    assert cp.done("gap-destiny") is True
    assert not any(cp.done(k) for k in mod.FINAL_STEPS)


def test_proof_log_streams_as_lines_are_produced(tmp_path):
    log = tmp_path / "refresh_proof.log"
    fh = log.open("w", encoding="utf-8")
    tee = mod._Tee(_NullStdout(), fh)
    tee.write("done abstention-signal in 168s exit 0\n")
    # The evidence is on disk before the run ends: a kill now
    # still leaves this leg's completion readable.
    assert "done abstention-signal" in log.read_text(encoding="utf-8")
    fh.close()


class _NullStdout:
    def write(self, s):
        return len(s)

    def flush(self):
        pass


def test_board_is_republished_inside_the_spine_before_the_engine_loop():
    assert "refresh_board.py" in SOURCE
    board_at = SOURCE.index('"board-republish"')
    loop_at = SOURCE.index("for slug in slugs:")
    assert board_at < loop_at
    # The step is a named, checkpointed step of the runner, not
    # a side script: its failure is collected under its own key.
    assert 'cp.mark("board-republish"' in SOURCE


def test_invocations_serialise_on_the_run_lock():
    assert "refresh_engines.lock" in SOURCE
    assert "LOCK_EX" in SOURCE


def test_printed_summary_contract_is_preserved():
    # The cron job's failure reporting reads these exact lines.
    for needle in ('print(f"engines refreshed: {len(ran)}")',
                   '"record refreshed: "',
                   '"smoke check: "',
                   'print("FAILURES: " + "; ".join(failures))',
                   'print("FAILURES: none")'):
        assert needle in SOURCE
