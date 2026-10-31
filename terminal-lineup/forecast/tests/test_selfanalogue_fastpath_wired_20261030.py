"""Regression blocker for the 2026-10-30 Self-Analogue wiring (G17).

Fail direction: on the pre-cure refresh_selfanalogue.py the live
build loop called the O(n^2) reference self_analogue_forecast for
every qualifying name, so a full Engine 15 refresh over the DEEP
panel's 8,857 qualifying names was a weeks-scale run and the page
stayed at its pre-DEEP state while the ledger held 9 engine_15
forecasts (the exact disagreement Calibration League fail-closes
on). The fast path existed and was equivalence-pinned but was
never called by the build. The cure wires the build to it.
"""
import os

SRC = os.path.expanduser(
    "~/workspace/terminal-lineup/site/refresh_selfanalogue.py")


def test_build_calls_fast_path():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "fc = self_analogue_forecast_fast(panel[sym])" in src
    assert "fc = self_analogue_forecast(panel[sym])" not in src
