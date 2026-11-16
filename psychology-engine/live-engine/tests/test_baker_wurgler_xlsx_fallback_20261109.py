#!/usr/bin/env python3
"""Regression blocker for BAKER-WURGLER-XLSX-20261109.

Failure of record: baker_wurgler_monthly failed every live
run with "curl exit 22 for
https://pages.stern.nyu.edu/~jwurgler/data/SENTIMENT.xls".
Probed 2026-11-09: that URL is a genuine 404 (the file is
gone), while SENTIMENT.xlsx in the same directory answers
200 (130,146 bytes). The collector discovers the workbook
from the author's index pages first, but those pages refuse
this client (403), so the hardcoded fallback decides the
outcome, and the fallback still named the dead .xls. The
parser already reads the workbook with openpyxl, so the
.xlsx successor is a drop-in.

Cure pinned here: the fallback URL is SENTIMENT.xlsx.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

import openpyxl  # noqa: E402
import psychology_engine  # noqa: E402
import pipeline  # noqa: E402


def _xlsx_bytes():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["DATE", "SENTIM", "SENTIMo"])
    ws.append([196507, 0.123, 0.100])
    ws.append([196508, -0.050, -0.020])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _fake_fetch(url, timeout=60, binary=False):
    if url.endswith("SENTIMENT.xls"):
        raise RuntimeError("curl exit 22 for " + url)
    if url.endswith("SENTIMENT.xlsx"):
        return _xlsx_bytes()
    raise RuntimeError("curl exit 22 for " + url)


def test_baker_wurgler_fallback_uses_the_live_xlsx(
        tmp_path, monkeypatch):
    monkeypatch.setattr(psychology_engine, "SERIES",
                        str(tmp_path / "series"))
    monkeypatch.setattr(psychology_engine, "PROV",
                        str(tmp_path / "PULL-LOG.md"))
    monkeypatch.setattr(psychology_engine, "RAW",
                        str(tmp_path / "raw"))
    monkeypatch.setattr(pipeline, "TODAY", "2026-11-09")
    monkeypatch.setattr(pipeline, "fetch", _fake_fetch)

    res = pipeline.bf_baker_wurgler()
    assert res["ok"], res
    rows = psychology_engine.read_series(
        "baker_wurgler_monthly.csv")
    assert len(rows) == 2, rows
    assert rows[0]["date"] == "1965-07-01"


def _real_shape_xlsx_bytes():
    """The workbook as the author actually publishes it
    (probed live 2026-11-09): a README sheet first, then a
    DATA sheet headed yearmo/SENT/SENT_ORTH, with SENT empty
    before 1965-07."""
    wb = openpyxl.Workbook()
    readme = wb.active
    readme.title = "README"
    readme.append(["INVESTOR SENTIMENT DATA", None])
    readme.append(["GENERAL NOTES", None])
    data = wb.create_sheet("DATA")
    data.append(["yearmo", "SENT", "SENT_ORTH", "pdnd", "indpro"])
    # SENT empty but indpro populated, exactly as published:
    # this row must NOT be stored as a sentiment reading.
    data.append([195801, None, None, None, 20.1956])
    data.append([196507, -1.9777, -2.2221, 0.5, 41.0])
    data.append([196508, -1.9775, -2.2406, 0.6, 41.2])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _fake_fetch_real_shape(url, timeout=60, binary=False):
    if url.endswith("SENTIMENT.xlsx"):
        return _real_shape_xlsx_bytes()
    raise RuntimeError("curl exit 22 for " + url)


def test_baker_wurgler_parses_the_published_workbook_shape(
        tmp_path, monkeypatch):
    monkeypatch.setattr(psychology_engine, "SERIES",
                        str(tmp_path / "series"))
    monkeypatch.setattr(psychology_engine, "PROV",
                        str(tmp_path / "PULL-LOG.md"))
    monkeypatch.setattr(psychology_engine, "RAW",
                        str(tmp_path / "raw"))
    monkeypatch.setattr(pipeline, "TODAY", "2026-11-09")
    monkeypatch.setattr(pipeline, "fetch", _fake_fetch_real_shape)

    res = pipeline.bf_baker_wurgler()
    assert res["ok"], res
    rows = psychology_engine.read_series(
        "baker_wurgler_monthly.csv")
    assert len(rows) == 2, rows
    assert rows[0]["date"] == "1965-07-01"
    assert abs(float(rows[0]["value_latest"]) - (-1.9777)) < 1e-9
    assert abs(float(rows[0]["orthogonalised"]) - (-2.2221)) < 1e-9
