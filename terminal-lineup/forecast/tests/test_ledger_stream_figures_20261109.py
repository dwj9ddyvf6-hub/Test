"""Regression blocker for the streaming-figures cure
(2026-11-09), LEDGER-STREAM-FIGURES-20261109.

Failure of record: the 2026-11-09 17:46 forecast refresh
failed with exceedance, self-analogue and silent-accumulation
each killed (exit -9) and intake-bias failing beside them.
Root cause, measured live that night: the forecast ledger
has grown to 661,722,661 bytes and about 253,000 rows, and
each of those refreshers parsed the whole ledger into memory
repeatedly in one run (verify_chain() loads rows(); a second
rows() for the figures recompute; the declared appends'
dedupe scans load it again per append). One intake-bias run
was watched climbing past 3.9 GB RSS and was OOM-killed at
exit 137 standalone. The streaming machinery to read the
ledger at bounded memory already existed in ledger.py
(iter_rows, verify_chain_streaming, the grading stream state)
since the GRADING-STREAM and PROOFGATE-STREAM cures; these
four refreshers simply never adopted it for their own reads.

Cure pinned here:
- recompute_figures consumes its rows argument exactly
  once, streaming each row into the collection its pass
  needs, so a caller may pass one fresh one-shot stream
  (ledger.iter_rows()) instead of a materialised list; the
  figures are identical either way (proven below against
  the same ledger, list form vs streamed form, deep-equal).
  The pre-cure function walked its argument three times,
  which on a list was merely the third full parse and on a
  one-shot stream silently produced empty figures: the
  equality test below fails on that code for exactly that
  reason.
- Each of the four refreshers' live paths verifies with
  verify_chain_streaming(), recomputes figures from
  iter_rows(), and scans only through streams or
  engine-filtered stream lists; no live path calls
  verify_chain() unbounded or rows() on the real ledger
  (scratch self-test ledgers are exempt and named as such).

Pre-cure behaviour these tests pin against: recompute_figures
iterated its argument three times (two comprehensions plus
the main loop), so a one-shot generator silently produced
empty figures; and each refresher's source carried the
unbounded calls in its live path.
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORECAST = os.path.dirname(HERE)
SITE = os.path.join(os.path.dirname(FORECAST), "site")
sys.path.insert(0, FORECAST)

import ledger as ledger_mod  # noqa: E402

GENESIS = {"type": "genesis", "program": "forecast-engines-30",
           "note": "blocker fixture"}
F1 = {"type": "forecast", "row_id": "f1", "engine_id": "engine_x",
      "subject": "AAA", "value": {"estimate": 1.0}}
F2 = {"type": "forecast", "row_id": "f2", "engine_id": "engine_x",
      "subject": "BBB", "value": {"estimate": 2.0}}
G1 = {"type": "grade", "row_id": "g1", "engine_id": "engine_x",
      "forecast_row_id": "f1",
      "grade": {"scores": {"pinball": 0.25}}}
CORR = {"type": "correction", "row_id": "c1",
        "corrects_row_id": "f2"}
G2 = {"type": "grade", "row_id": "g2", "engine_id": "engine_x",
      "forecast_row_id": "f2",
      "grade": {"scores": {"pinball": 0.5}}}
ROWS = [GENESIS, F1, F2, G1, CORR, G2]


def _stream():
    return (copy.deepcopy(r) for r in ROWS)


def test_figures_from_two_streams_equal_figures_from_list():
    from_list = ledger_mod.recompute_figures(
        [copy.deepcopy(r) for r in ROWS])
    from_stream = ledger_mod.recompute_figures(_stream())
    assert from_stream == from_list
    eng = from_stream["engine_x"]
    assert eng["forecasts"] == 2
    assert eng["forecasts_voided"] == 1
    assert eng["forecasts_valid"] == 1
    assert eng["graded"] == 1
    assert eng["grades_on_voided"] == 1
    assert eng["mean_scores"] == {"pinball": 0.25}


def test_figures_stream_is_consumed_exactly_once():
    """A one-shot generator is the strictest probe: any
    second pass would silently yield nothing and corrupt
    the counts, so the counts themselves prove the
    single-pass contract."""
    gen = _stream()
    figures = ledger_mod.recompute_figures(gen)
    assert figures["engine_x"]["forecasts"] == 2
    assert figures["engine_x"]["graded"] == 1
    assert list(gen) == []


LIVE_FILES = ("refresh_exceedance.py", "refresh_selfanalogue.py",
              "refresh_silentaccumulation.py",
              "refresh_intakebias.py")

# The three legs that publish recompute_figures output; intake-bias
# publishes its own counts from a filtered stream instead and
# never called recompute_figures, before or after the cure.
FIGURES_FILES = ("refresh_exceedance.py", "refresh_selfanalogue.py",
                 "refresh_silentaccumulation.py")


def test_refreshers_live_paths_stream_the_ledger():
    for name in LIVE_FILES:
        with open(os.path.join(SITE, name), encoding="utf-8") as fh:
            src = fh.read()
        assert "verify_chain_streaming()" in src, (
            f"{name}: live verification must stream")
        assert "iter_rows()" in src, (
            f"{name}: live scans must stream the ledger")
        # rows() loads are legitimate only on a scratch
        # self-test ledger, a file the refresher itself just
        # wrote into a temp dir; on the live ledger they are
        # the defect. The binding is textual and conservative:
        # every rows() line must be a scratch call, or a call
        # on `led` inside the self-test builder (whose ledger
        # is Ledger(scratch_ledger...) or Ledger(tmp...)).
        import re as _re
        scratch_ledgers = set(_re.findall(
            r"(\w+)\s*=\s*ledger_mod\.Ledger\((?:scratch|tmp|os\.path\.join\(tmp)",
            src)) | set(_re.findall(
            r"(\w+)\s*=\s*ledger_mod\.Ledger\(os\.path\.join\(td,",
            src))
        for lineno, line in enumerate(src.splitlines(), 1):
            for var in _re.findall(r"(\w+)\.rows\(\)", line):
                if var == "scratch":
                    continue
                if var in scratch_ledgers:
                    continue
                raise AssertionError(
                    f"{name}:{lineno}: a rows() load on a "
                    f"non-scratch ledger survives: {line.strip()}")
    for name in FIGURES_FILES:
        with open(os.path.join(SITE, name), encoding="utf-8") as fh:
            src = fh.read()
        assert "recompute_figures(led.iter_rows())" in src, (
            f"{name}: figures must recompute from a stream")
        for lineno, line in enumerate(src.splitlines(), 1):
            if "verify_chain()" in line and \
                    "verify_chain_streaming" not in line \
                    and "scratch" not in line:
                raise AssertionError(
                    f"{name}:{lineno}: unbounded verify_chain() "
                    f"survives in the live path: {line.strip()}")
