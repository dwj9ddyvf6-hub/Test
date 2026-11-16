#!/usr/bin/env python3
"""Regression blocker for COT-TFF-FAILURE-NAMING-20261109.

Failure of record: cot_tff_weekly succeeded 2026-11-04 and
2026-11-05 (850 rows, all 17 annual files), then failed
2026-11-06 and 2026-11-09 with the bare note "no TFF index
rows parsed". Probed 2026-11-09 in isolation: cftc.gov
answers this client 403 for the annual zips, so every year's
fetch failed and the walker's per-year swallow (except:
continue) erased the cause, leaving a message
indistinguishable from a CFTC format change. The two causes
need opposite responses (wait out a refusal vs repair a
parser), so the failure must name which one happened.

Cure pinned here: bf_cot_tff counts the years whose fetch
failed and names the count (and the years that did parse)
in the raised error, which is what the pull log records.
The external 403 itself is not curable from here; the
stored series is preserved by preserve_series as before.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

import psychology_engine  # noqa: E402
import pipeline  # noqa: E402


def _dead_fetch(url, timeout=60, binary=False):
    raise RuntimeError("curl exit 22 for " + url)


def test_cot_tff_failure_names_fetch_failures(
        tmp_path, monkeypatch):
    monkeypatch.setattr(psychology_engine, "SERIES",
                        str(tmp_path / "series"))
    monkeypatch.setattr(psychology_engine, "PROV",
                        str(tmp_path / "PULL-LOG.md"))
    monkeypatch.setattr(psychology_engine, "RAW",
                        str(tmp_path / "raw"))
    monkeypatch.setattr(pipeline, "fetch", _dead_fetch)

    res = pipeline.bf_cot_tff()
    assert not res["ok"], res
    assert "fetch_failed_years=17" in res["detail"], res
