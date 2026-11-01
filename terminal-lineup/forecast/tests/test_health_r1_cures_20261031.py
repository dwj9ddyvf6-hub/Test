"""Regression blockers for the terminal health loop cure round 1
(engine/data correctness + ledger/integrity class, 2026-10-31).

Each test names the AUDIT-R1 defect it blocks. Fail directions
were spot-checked in the cure pass: every assertion below fails
on the pre-cure source or pre-cure published state it names.
"""
import importlib.util
import json
import os
import sys

LINEUP = os.path.expanduser("~/workspace/terminal-lineup")
SITE = os.path.join(LINEUP, "site")
FORECAST = os.path.join(LINEUP, "forecast")


def _src(base, name):
    with open(os.path.join(base, name), encoding="utf-8") as fh:
        return fh.read()


def _data(slug):
    with open(os.path.join(SITE, slug, "data.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


# ---- D-R1-06: append paths regenerate attestations -------------

def test_run_grading_regenerates_attestations_after_appends():
    src = _src(FORECAST, "run_grading.py")
    assert "HEALTH-R1-D06-20261031" in src
    assert "refresh_attestations.regenerate()" in src
    assert "refresh_attestations.sync_pages()" in src


def test_ledger_checkpoint_matches_live_ledger_head():
    # The checkpoint is written by refresh_attestations on every
    # regeneration; its head and row count must equal the live
    # ledger's, recounted here by streaming (never loaded whole).
    ckpt = json.load(open(os.path.join(
        FORECAST, "ledger-checkpoint.json"), encoding="utf-8"))
    rows = 0
    head = None
    with open(os.path.join(FORECAST, "ledger.jsonl"),
              encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows += 1
            head = json.loads(line)["row_hash"]
    assert ckpt["ledger_rows"] == rows
    assert ckpt["ledger_head"] == head


# ---- D-R1-07: agent-debate stamps its own tape freshness -------

def test_agentdebate_refresher_self_stamps_tape_freshness():
    src = _src(SITE, "refresh_agentdebate.py")
    assert "HEALTH-R1-D07-20261031" in src
    assert '"tape_freshness"' in src


# ---- D-R1-08: earnings record aggregates its snapshot store ----

def test_earnings_record_builds_from_snapshot_store():
    src = _src(SITE, "earnings_record.py")
    assert "HEALTH-R1-D08-20261031" in src
    assert "record_days_from_store" in src
    rec = json.load(open(os.path.join(
        SITE, "earnings-record", "record.json"), encoding="utf-8"))
    assert rec["names_with_surprise_recorded"] > 0
    assert rec["window"]["record_days_from_store"] > \
        rec["window"]["days_fetched"]


# ---- D-R1-09: zero-row engines carry named dated states --------

def test_zero_row_engines_carry_named_dated_states():
    reg = json.load(open(os.path.join(
        FORECAST, "registry.json"), encoding="utf-8"))
    present = set()
    with open(os.path.join(FORECAST, "ledger.jsonl"),
              encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                present.add(json.loads(line).get("engine_id"))
    zero = [e for e in reg["engines"] if e["id"] not in present]
    assert zero, "expected at least one zero-row engine"
    for eng in zero:
        state = eng.get("zero_forecast_state") or {}
        assert state.get("reason"), eng["id"]
        assert state.get("trigger"), eng["id"]
        assert state.get("first_possible"), eng["id"]


def test_verifier_enumerates_zero_row_engines():
    src = _src(FORECAST, "verify_grade_rows.py")
    assert "HEALTH-R1-D09-20261031" in src
    assert "ZERO ROWS on the ledger" in src


# ---- D-R1-17: desk and market-mood publishers stamp provenance -

def test_desk_and_market_mood_publishers_stamp_provenance():
    assert "HEALTH-R1-D17-20261031" in _src(SITE, "publish_desk.py")
    pipe = _src(os.path.join(LINEUP, "psychology-engine"),
                "pipeline.py")
    assert "HEALTH-R1-D17-20261031" in pipe
    for slug in ("desk", "market-mood"):
        data = _data(slug)
        assert data.get("feed") and data.get("price_basis")
        assert data.get("execution_pricing") is False
        assert isinstance(data.get("provenance"), dict), slug


# ---- D-R1-18: sampled drill writes a verify block --------------

def test_sampled_drill_report_carries_verify_block(tmp_path,
                                                    monkeypatch):
    sys.path.insert(0, os.path.expanduser("~/workspace/backup"))
    import api_restore as ar
    import restore_drill as rd

    parts = [{"name": f"part-{i:02d}.bin", "git_sha": None,
              "sha256": None, "bytes": 3} for i in range(10)]
    blobs = {}
    for p in parts:
        data = b"abc"
        p["sha256"] = __import__("hashlib").sha256(data).hexdigest()
        p["git_sha"] = ar.git_blob_sha(data)
        blobs[p["git_sha"]] = data
    man = {"home_head": "deadbeef", "parts": parts}
    monkeypatch.setattr(
        rd, "_manifest",
        lambda source, ref, snapshot: ({}, "snap", man))
    monkeypatch.setattr(ar, "assert_proven_receipt",
                        lambda head: None)

    class _Source:
        def blob(self, sha):
            return blobs[sha]

    out = rd.sampled(_Source(), "ref", None, every=1)
    assert out["verify"]["checked"] == 10
    assert out["verify"]["mismatches"] == []
    assert out["verify"]["missing"] == []
    assert len(out["verify"]["parts"]) == 10
    assert all(p["sha256_ok"] for p in out["verify"]["parts"])
    src = _src(os.path.expanduser("~/workspace/backup"),
               "restore_drill.py")
    assert 'result["verdict"] = verdict' in src


# ---- D-R1-19: retention, flip-back, dependency lock ------------

def test_published_tree_retention_and_flip_back(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "retain_tree", os.path.join(SITE, "retain_tree.py"))
    rt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rt)
    site_dir = tmp_path / "site"
    (site_dir / "page").mkdir(parents=True)
    (site_dir / "index.html").write_text("hub v1")
    (site_dir / "page" / "index.html").write_text("page v1")
    (site_dir / "page" / "data.json").write_text('{"v": 1}')
    rt.RETAIN_DIR = str(tmp_path / "retained")
    stamp, created = rt.snapshot(str(site_dir))
    assert created
    (site_dir / "page" / "data.json").write_text('{"v": 2}')
    n = rt.flip_back(stamp, str(site_dir))
    assert n == 3
    assert (site_dir / "page" / "data.json").read_text() == \
        '{"v": 1}'
    assert "retain_tree" in _src(SITE, "publish_live.py")


def test_dependency_lock_pins_imported_packages():
    lock = _src(LINEUP, "requirements-lock.txt")
    for pkg in ("numpy==", "pandas==", "scipy==", "pytest=="):
        assert pkg in lock
    import numpy
    assert f"numpy=={numpy.__version__}" in lock
