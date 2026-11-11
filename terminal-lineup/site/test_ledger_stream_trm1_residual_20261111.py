"""Regression blocker for LEDGER-STREAM-TRM1-RESIDUAL-20261111
(TOTAL APPLICATION cure wave, census row TRM-1 residual).

Failure of record: after wave W1 cured the nine dead-leg
readers (LEDGER-STREAM-W1-20261110), 14 production refreshers
still read the shared forecast ledger through its
materializing pair, Ledger.rows() / Ledger.verify_chain()
with no argument, which parse and cache the whole ledger
(676 MB on disk, 349,553 rows at the wave's snapshot; the
wave's seam measured the materialized form at 2,649,364 KB
peak RSS against 234,900 KB for the streaming form). That is
the estate's proven contention and OOM class on every
refresh run.

Cure pinned here: on each refresher's LIVE-ledger path the
materializing pair is replaced by the ledger's own streaming
forms, verify_chain_streaming() (identical verdicts by
ledger.py's contract) and iter_rows() (identical rows, one
parsed row resident), following LEDGER-STREAM-REFRESH-20261110
and LEDGER-STREAM-W1-20261110. Multi-pass sites became one
stream pass per former snapshot point; passes that append
against their snapshot collect exactly the filtered subset
they can touch first.

The scan is AST-based and scoped to ledger calls: a .rows()
or .verify_chain() call whose receiver is one of the file's
live-ledger names (led, ledger) fails unless it sits inside
a self_test function. Named exceptions, by design and not
defects:
- refresh_livingrouter.py, refresh_inregimeoracle.py and
  refresh_streaktrap.py keep led.verify_chain() / led.rows()
  inside self_test() only, on throwaway tempfile ledgers of
  a handful of synthetic rows (the bounded-fixture class
  the census excludes).
- refresh_sponsoredreset.py and refresh_pinorescape.py keep
  scratch.rows() / scratch.verify_chain() inside their
  self-tests; the receiver there is the scratch ledger, not
  a live-ledger name, so the scan never sees them.
- refresh_record.py's cure is the caller handing
  led.iter_rows() to grading.abstention_coverage_audit,
  whose single-pass consumption is pinned by a source
  assertion on that call site.
The REG-3 design rows (forecast/run_grading_reports.py,
forecast/refresh_attestations.py, forecast/verify_grade_rows.py)
are outside this blocker's file set by the wave's fence.

These are source assertions: the defect is which ledger API
the refresher calls. The fail direction is exact: every
pre-cure file preserved at ~/workspace/.trm1fix/pre/
contains materializing calls on its live object outside
self_test and fails test_no_materializing_live_ledger_calls;
the cured tree passes.
"""
import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))

CONVERTED = (
    "refresh_halflifeclock.py",
    "refresh_idioliquidity.py",
    "refresh_inregimeoracle.py",
    "refresh_livingrouter.py",
    "refresh_mortalitycurve.py",
    "refresh_pinorescape.py",
    "refresh_record.py",
    "refresh_sponsoredreset.py",
    "refresh_streaktrap.py",
    "refresh_stressreversal.py",
    "refresh_touchsurface.py",
    "refresh_volclock.py",
    "refresh_voltermshape.py",
    "refresh_walllifetime.py",
)

LIVE_NAMES = ("led", "ledger")
MATERIALIZING = ("rows", "verify_chain")


def _materializing_live_calls(src):
    """(function, line, attr) for every .rows()/.verify_chain()
    call on a live-ledger name outside a self_test function."""
    tree = ast.parse(src)
    hits = []

    def walk(node, func):
        for child in ast.iter_child_nodes(node):
            name = func
            if isinstance(child, (ast.FunctionDef,
                                  ast.AsyncFunctionDef)):
                name = child.name
            if isinstance(child, ast.Call) \
                    and isinstance(child.func, ast.Attribute) \
                    and child.func.attr in MATERIALIZING \
                    and isinstance(child.func.value, ast.Name) \
                    and child.func.value.id in LIVE_NAMES \
                    and not (name or "").startswith("self_test"):
                hits.append((name, child.lineno, child.func.attr))
            walk(child, name)

    walk(tree, None)
    return hits


def _src(name, base=HERE):
    with open(os.path.join(base, name), encoding="utf-8") as fh:
        return fh.read()


def test_no_materializing_live_ledger_calls():
    for name in CONVERTED:
        hits = _materializing_live_calls(_src(name))
        assert not hits, (name, hits)


def test_streaming_forms_in_use():
    for name in CONVERTED:
        src = _src(name)
        assert "iter_rows()" in src, name
        if name == "refresh_record.py":
            continue  # its only live call site is the audit hand-off
        assert "verify_chain_streaming()" in src, name


def test_record_audit_handoff_streams():
    src = _src("refresh_record.py")
    assert "led.iter_rows(), grading_mod.PriceSource()" in src
    assert "led.rows()" not in src


def test_selftest_exceptions_stay_in_selftest():
    # The three files whose self-tests drive a throwaway ledger
    # through a live-named variable keep those calls, and only
    # those calls, inside self_test.
    for name in ("refresh_livingrouter.py",
                 "refresh_inregimeoracle.py",
                 "refresh_streaktrap.py"):
        src = _src(name)
        tree = ast.parse(src)
        inside = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) \
                    and isinstance(node.func, ast.Attribute) \
                    and node.func.attr in MATERIALIZING \
                    and isinstance(node.func.value, ast.Name) \
                    and node.func.value.id in LIVE_NAMES:
                inside.append(node.lineno)
        hits = _materializing_live_calls(src)
        assert not hits, (name, hits)
        assert inside, (name, "self-test exception vanished; "
                              "re-check the exception is still "
                              "only a throwaway-ledger read")
