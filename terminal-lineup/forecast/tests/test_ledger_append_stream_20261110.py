"""Blocker for LEDGER-APPEND-STREAM-20261110.

The exceedance (engine_06) and self-analogue (engine_15) legs
append thousands of forecasts under one (engine, issuance)
through append_forecast_declared, whose dedupe re-scans the
whole ledger twice per append. At the 2026-11-10 ledger
(348,927 rows; one iter_rows stream measured at 23s) that is
~46s per append: ~69 hours for exceedance's ~5,400-append
batch and ~13 hours of scanning alone for self-analogue's
batch, on top of its per-name computation. Both legs timed
out or were killed on every 2026-11-09/10 attempt and their
stores stayed at as_of 2026-11-06.

The cure routes both batches through the ledger's existing
streaming append form (append_stream_state +
append_forecast_streaming): one pass seeds the batch's dedupe
keys from the ledger itself, each append is O(1), and a
same-issuance re-run still appends nothing.

These tests pin (a) the source shape: build() in both
refreshers opens a stream state and appends through the
streaming form, with no declared-form call in the live path;
and (b) the semantics the cure relies on: streaming appends
dedupe against rows already on the ledger for the same
(engine, issuance) and the chain still verifies.
"""
import ast
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(os.path.dirname(HERE))
SITE = os.path.join(LINEUP, "site")
sys.path.insert(0, LINEUP)

from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402


def _build_fn(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "build":
            return node
    raise AssertionError(f"no build() in {path}")


def _calls(fn, attr):
    return [n for n in ast.walk(fn)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == attr]


def _check_refresher_streams(path):
    build = _build_fn(path)
    states = _calls(build, "append_stream_state")
    streamed = _calls(build, "append_forecast_streaming")
    declared = _calls(build, "append_forecast_declared")
    assert len(states) == 1, f"{path}: build() must open exactly one stream state"
    assert streamed, f"{path}: build() must append via append_forecast_streaming"
    assert not declared, (
        f"{path}: build() still calls append_forecast_declared "
        "(two full ledger scans per append)")


def test_exceedance_appends_streaming():
    _check_refresher_streams(os.path.join(SITE, "refresh_exceedance.py"))


def test_selfanalogue_appends_streaming():
    _check_refresher_streams(os.path.join(SITE, "refresh_selfanalogue.py"))


def _lineage():
    return {"source_artifacts": [{"path": "blocker", "sha256": "0" * 64}],
            "clocks": {c: "2026-11-10" for c in ledger_mod.CLOCK_FIELDS},
            "note": "blocker test"}


def test_streaming_batch_dedupes_across_states():
    reg = registry_mod.load()
    with tempfile.TemporaryDirectory() as td:
        led = ledger_mod.Ledger(os.path.join(td, "ledger.jsonl"),
                                registry=reg)
        led.append_genesis("blocker")
        kwargs = dict(
            engine_id="engine_06", issued_ts="2026-11-12",
            quantity="size of the 5-session return larger than 1 expected move",
            horizon_open="2026-11-12", horizon_close="2026-11-18",
            lineage=_lineage(), families=["price"],
            outcome={"symbol": "AAA", "kind": "abs_return",
                     "base_date": "2026-11-10", "at_date": "2026-11-18",
                     "threshold_fraction": 0.01})
        state = led.append_stream_state("engine_06", "2026-11-12")
        made = 0
        for sym in ("AAA", "BBB", "CCC"):
            _row, was = led.append_forecast_streaming(
                state, subject=sym, value={"p": 0.5},
                outcome={**kwargs["outcome"], "symbol": sym},
                **{k: v for k, v in kwargs.items() if k != "outcome"})
            made += 1 if was else 0
        assert made == 3
        # A fresh state (a re-run) is seeded from the ledger, so
        # the same batch appends nothing.
        state2 = led.append_stream_state("engine_06", "2026-11-12")
        made2 = 0
        for sym in ("AAA", "BBB", "CCC"):
            _row, was = led.append_forecast_streaming(
                state2, subject=sym, value={"p": 0.5},
                outcome={**kwargs["outcome"], "symbol": sym},
                **{k: v for k, v in kwargs.items() if k != "outcome"})
            made2 += 1 if was else 0
        assert made2 == 0
        assert led.verify_chain_streaming()
        figs = ledger_mod.recompute_figures(led.iter_rows())
        assert figs["engine_06"]["forecasts"] == 3
