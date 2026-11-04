"""Regression blockers for PROOFGATE-HARDEN-20261104 and
COMPLETION-CLOCK-L2L-20261104.

Three hardening cures from the 2026-11-04 census open rows:

1. The proof gate block's recount comparison is a floor, not an
   exact equality. The gate file is a snapshot; the append-only
   ledger keeps moving, and an append interrupted mid-scan (the
   2026-11-02 instance, 271 of 15,815 names in) leaves the
   ledger ahead of the snapshot on a healthy record. T1: a
   ledger ahead of the gate publishes, with the ahead count
   named. T2: a ledger BELOW the gate (rows the gate vouches
   for are missing) still refuses. These are the census's T1/T2
   staleness tests: the two directions a gate snapshot can be
   stale against its ledger.
2. refresh_proofgate's own recount filters on the frozen rule's
   ledger engine, exactly as the consuming pages' recount does;
   the two recounts of one record are the same recount.
3. The Completion Clock's Engine 1 cross-check compares like
   for like at the band's own session, not at the panel's
   freshest session, so runner order can no longer refuse a
   healthy record (2026-11-03: 2.9868 vs 5.1376 freshest-side,
   exact agreement at the band's session).

Fail directions on the pre-cure code: the block raises
ProofGateError on the T1 fixture (exact equality); the gate
recount counts a foreign engine's rows; band_em_cross_check
does not exist.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
FORECAST = os.path.expanduser("~/workspace/terminal-lineup/forecast")
sys.path.insert(0, FORECAST)
sys.path.insert(0, SITE)


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pgb = _load("proof_gate_block", "proof_gate_block.py")
pg = _load("refresh_proofgate", "refresh_proofgate.py")
cc = _load("refresh_completionclock", "refresh_completionclock.py")

FQ = pgb.FORWARD_QUANTITY


def _gate_file(tmp_path, created, ledger_rows):
    site_dir = tmp_path / "site"
    gate_dir = site_dir / "proof-gate"
    gate_dir.mkdir(parents=True)
    gate = {
        "as_of": "2026-11-03",
        "consuming_engines": ["engine_19", "engine_20"],
        "counts": {"names_scanned": 10,
                   "by_state": {"MIXED": 10}},
        "forward_ledger": {"created": created,
                           "ledger_rows": ledger_rows,
                           "duplicates": 0},
    }
    (gate_dir / "data.json").write_text(
        json.dumps(gate), encoding="utf-8")
    return str(site_dir)


def _ledger_file(tmp_path, subjects, extra_rows=0,
                 engine="engine_19"):
    path = tmp_path / "ledger.jsonl"
    lines = []
    rows = []
    for s in subjects:
        rows.append(s)
    for i in range(extra_rows):
        rows.append(subjects[i % len(subjects)])
    for s in rows:
        lines.append(json.dumps({
            "type": "forecast", "engine_id": engine,
            "quantity": FQ, "subject": s}))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def test_t1_ledger_ahead_of_gate_publishes_and_names_it(tmp_path):
    # Gate snapshot: 5 names, 7 rows. Ledger since: 6 distinct
    # names, 8 rows (a later scan appended ahead).
    site_dir = _gate_file(tmp_path, created=5, ledger_rows=7)
    ledger = _ledger_file(
        tmp_path, ["A", "B", "C", "D", "E", "F"], extra_rows=2)
    block = pgb.build_proof_gate_block(
        site_dir, "engine_19", "2026-11-03", ledger)
    assert block["forward_records_created"] == 5
    assert block["ledger_rows_recounted"] == 6
    assert block["ledger_ahead_names"] == 1
    assert block["ledger_ahead_rows"] == 1
    assert "since the gate last published" in block["words"]


def test_t2_ledger_below_gate_still_refuses(tmp_path):
    import pytest
    site_dir = _gate_file(tmp_path, created=5, ledger_rows=7)
    ledger = _ledger_file(tmp_path, ["A", "B", "C", "D"],
                          extra_rows=3)
    with pytest.raises(pgb.ProofGateError):
        pgb.build_proof_gate_block(
            site_dir, "engine_19", "2026-11-03", ledger)


def test_t2_row_shortfall_still_refuses(tmp_path):
    import pytest
    site_dir = _gate_file(tmp_path, created=2, ledger_rows=9)
    ledger = _ledger_file(tmp_path, ["A", "B"], extra_rows=2)
    with pytest.raises(pgb.ProofGateError):
        pgb.build_proof_gate_block(
            site_dir, "engine_19", "2026-11-03", ledger)


def test_gate_recount_filters_on_the_ledger_engine(tmp_path):
    path = tmp_path / "ledger.jsonl"
    lines = []
    for s in ("A", "B"):
        lines.append(json.dumps({
            "type": "forecast", "engine_id": "engine_19",
            "quantity": pg.PG.FORWARD_QUANTITY, "subject": s}))
    for s in ("X", "Y", "Z"):
        lines.append(json.dumps({
            "type": "forecast", "engine_id": "engine_99",
            "quantity": pg.PG.FORWARD_QUANTITY, "subject": s}))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    old = pg.LEDGER_PATH
    pg.LEDGER_PATH = str(path)
    try:
        counts = pg.recount_forward_record("engine_19")
    finally:
        pg.LEDGER_PATH = old
    assert counts == {"created": 2, "ledger_rows": 2,
                      "duplicate_rows": 0}


def _closes_with_regime_shift(n_calm=80, n_hot=40):
    closes = [100.0]
    for i in range(n_calm - 1):
        closes.append(closes[-1] * (1.001 if i % 2 else 0.999))
    for i in range(n_hot):
        closes.append(closes[-1] * (1.03 if i % 2 else 0.97))
    return closes


def test_band_check_compares_at_the_band_session():
    closes = _closes_with_regime_shift()
    dates = [f"d{i:03d}" for i in range(len(closes))]
    pos = {d: i for i, d in enumerate(dates)}
    band_session = dates[90]
    theirs = cc.em21_pct(closes, pos[band_session])
    mine, err = cc.band_em_cross_check(
        closes, pos, band_session, theirs, 1.0)
    assert err is None
    assert abs(mine - theirs) < 1e-9
    # And the freshest-session figure really is a different
    # quantity on this series, so the old comparison would
    # have refused this healthy pair.
    freshest = cc.em21_pct(closes, len(closes) - 1)
    assert abs(freshest - theirs) > 0.01


def test_band_check_still_refuses_a_real_disagreement():
    closes = _closes_with_regime_shift()
    dates = [f"d{i:03d}" for i in range(len(closes))]
    pos = {d: i for i, d in enumerate(dates)}
    band_session = dates[90]
    theirs = cc.em21_pct(closes, pos[band_session]) * 1.5
    mine, err = cc.band_em_cross_check(
        closes, pos, band_session, theirs, 1.0)
    assert mine is None
    assert "disagrees" in err


def test_band_check_names_a_band_session_the_panel_lacks():
    closes = _closes_with_regime_shift()
    pos = {f"d{i:03d}": i for i in range(len(closes))}
    mine, err = cc.band_em_cross_check(
        closes, pos, "1999-01-04", 1.0, 1.0)
    assert mine is None
    assert "not a session the panel carries" in err
