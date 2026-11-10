#!/usr/bin/env python3
"""Regression blocker: SQUEEZE-ROTATION-20261108.

The Squeeze Watch readings file is cumulative across gathers
while the gathering's board rotates, the provenance record
describes only the latest gather, and the short-interest store
is rewritten by its own collection for the current names only.
On 2026-11-08 the weekly gather rotated the board: the
freshest settlement carried two gather vintages (so the old
one-publication-date rule refused), and fifteen rotated-out
names were carried by no current record (so the old
every-name-cross-checked rule refused on their days to cover).

The cure: the page lists the names at least one current
record carries, cross-checked against every record that
carries them, with the published date the LATEST vintage at
the freshest settlement and each row keeping its own vintage.
A name no current record carries is rotated out: not listed,
counted and named in coverage. A carried name whose records
carry no usable days to cover still refuses.

Fail-first: on the pre-cure refresher the mixed-vintage
fixture refuses (publication dates) and the rotated fixture
refuses (no days-to-cover carrier for the rotated name).

Run standalone or under pytest.
"""
import gzip
import json
import os
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))

import refresh_squeeze as rs  # noqa: E402

S1, S2 = "2026-09-30", "2026-10-15"
SV_DAY = "2026-11-07"
CAL = {"top10_plus20_in_5_sessions": 1, "top10_minus20_in_5_sessions": 2,
       "base_plus20": 3, "base_minus20": 4, "top10_median_5d_return": 0.5}


def _write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


def build_fixture(tmp, prov_dtc_new=4.0, store_has_new=True):
    pit = [
        {"symbol": "KEEP1", "settlement_date": S1, "si_shares": 190,
         "float_shares": 1000, "publication_date": "2026-10-26"},
        {"symbol": "KEEP1", "settlement_date": S2, "si_shares": 200,
         "float_shares": 1000, "publication_date": "2026-10-26"},
        {"symbol": "NEW1", "settlement_date": S1, "si_shares": 90,
         "float_shares": 1000, "publication_date": "2026-11-08"},
        {"symbol": "NEW1", "settlement_date": S2, "si_shares": 100,
         "float_shares": 1000, "publication_date": "2026-11-08"},
        {"symbol": "GONE1", "settlement_date": S1, "si_shares": 50,
         "float_shares": 1000, "publication_date": "2026-10-26"},
        {"symbol": "GONE1", "settlement_date": S2, "si_shares": 60,
         "float_shares": 1000, "publication_date": "2026-10-26"},
    ]
    pit_path = tmp / "pit.jsonl"
    with open(pit_path, "w", encoding="utf-8") as fh:
        for r in pit:
            fh.write(json.dumps(r) + "\n")
    prov = {
        "_meta": {"as_of": "2026-11-08", "symbols": 3},
        "KEEP1": {"si": {"settlement_date": S2,
                         "si_pct_of_shares_out": 20.0,
                         "days_to_cover": 5.0}},
        "NEW1": {"si": {"settlement_date": S2,
                        "si_pct_of_shares_out": 10.0,
                        "days_to_cover": prov_dtc_new}},
        "GAPCO": {},
    }
    store_names = {
        "KEEP1": [{"settlement_date": S2, "si_shares": 200,
                   "days_to_cover": 5.0}],
        "GAPCO": [{"settlement_date": S2, "si_shares": 50,
                   "days_to_cover": 2.0}],
    }
    if store_has_new:
        store_names["NEW1"] = [{"settlement_date": S2,
                                "si_shares": 100,
                                "days_to_cover": 4.0}]
    pane = {"state": "no_data", "rows": [],
            "vendor_calibration": CAL}
    sv_dir = tmp / "shortvol"
    sv_dir.mkdir(parents=True, exist_ok=True)
    with gzip.open(sv_dir / f"{SV_DAY}.json.gz", "wt",
                   encoding="utf-8") as fh:
        json.dump({"date": SV_DAY,
                   "names": {"KEEP1": [10, 100]}}, fh)
    paths = {
        "PIT_PATH": str(pit_path),
        "PROVENANCE_PATH": str(tmp / "prov.json"),
        "STUDIES_PATH": str(tmp / "studies.json"),
        "FEED_PATH": str(tmp / "feed.json"),
        "LOG_PATH": str(tmp / "ledger.jsonl"),
        "SHORTVOL_DIR": str(sv_dir),
        "SI_STORE_PATH": str(tmp / "store.json"),
        "OUT_PATH": str(tmp / "out" / "data.json"),
    }
    _write(tmp / "prov.json", prov)
    _write(tmp / "studies.json", {"squeeze": pane})
    _write(tmp / "feed.json", {
        "squeeze": pane,
        "generated_at_utc": "2026-11-08T00:00:00Z",
        "lanes": {"lanes": {"short_volume": {
            "status": "ok", "days": 1,
            "first_date": SV_DAY, "last_date": SV_DAY}}}})
    _write(tmp / "store.json", {"names": store_names})
    with open(tmp / "ledger.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"component": "squeeze-pane",
                             "value": {"state": "no_data",
                                       "gated_n": 0}}) + "\n")
    return paths


def run_build(tmp, **kw):
    paths = build_fixture(tmp, **kw)
    saved = {k: getattr(rs, k) for k in paths}
    saved_tc = rs._tc
    try:
        for k, v in paths.items():
            setattr(rs, k, v)
        rs._tc = None
        rc = rs.build()
        out = None
        if os.path.exists(paths["OUT_PATH"]):
            out = json.load(open(paths["OUT_PATH"]))
        return rc, out
    finally:
        for k, v in saved.items():
            setattr(rs, k, v)
        rs._tc = saved_tc


def test_mixed_vintages_and_rotation_publish(tmp_path):
    rc, out = run_build(tmp_path)
    assert rc == 0
    assert {n["symbol"] for n in out["names"]} == {"KEEP1", "NEW1"}
    assert out["published_date"] == "2026-11-08"
    by = {n["symbol"]: n for n in out["names"]}
    assert by["KEEP1"]["published_date"] == "2026-10-26"
    assert by["NEW1"]["published_date"] == "2026-11-08"
    assert by["KEEP1"]["days_to_cover"] == 5.0
    cov = out["coverage"]
    assert cov["names_covered"] == 2
    assert cov["names_rotated_out"] == 1
    assert out["rotated_out_names"] == ["GONE1"]
    assert [g["symbol"] for g in out["basis_gap_names"]] == ["GAPCO"]


def test_carried_name_without_days_to_cover_refuses(tmp_path):
    # NEW1 stays carried by the provenance record, but its days
    # to cover is unusable there and the store does not carry
    # it: a genuine carrier gap, still a refusal.
    rc, _ = run_build(tmp_path, prov_dtc_new=0,
                      store_has_new=False)
    assert rc == 1


def main() -> int:
    import tempfile
    for t in (test_mixed_vintages_and_rotation_publish,
              test_carried_name_without_days_to_cover_refuses):
        with tempfile.TemporaryDirectory() as d:
            t(Path(d))
        print(f"PASS {t.__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
