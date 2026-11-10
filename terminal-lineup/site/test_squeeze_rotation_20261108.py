#!/usr/bin/env python3
"""Regression blocker for the Squeeze Watch rotation refusal
(SQUEEZE-ROTATION-20261108).

Failure class: on 2026-11-08 refresh_squeeze.py refused to
publish because the freshest settlement (2026-10-15) carried
two publication dates. Root cause, proven from the producer:
the gathering stamps each reading with its admission date
(inst_bundle test: "retrieval = admission"), the board it
covers rotates, and the readings file is cumulative across
gathers, so a rotated-in name's backfilled history carries the
later gather's date at every settlement. The refusal assumed
one vintage per settlement, a static board's provenance set,
and days to cover available only from the latest gathering.
A second layer landed the same night: the Nasdaq store's own
collection rewrote the store per run for the current board
only, dropping rotated-out names and their days-to-cover
tables (cure SI-STORE-UNION-20261108 in the morgue tree), so a
rotated-out name is now excluded from the page and named in
the coverage block instead of being carried on a record no
current source maintains.

This blocker drives refresh_squeeze.build() on fixture inputs
and proves: (1) two vintages at the freshest settlement publish
with published_date == the latest of them; (2) a rotated-in
name whose days to cover lives only in the store publishes;
(3) a store share count disagreeing with the readings refuses;
(4) a gathering/store days-to-cover disagreement refuses;
(5) a gathering-carried name absent from the readings refuses;
(6) a name no current record carries is excluded and named as
rotated out. Pre-cure, check (1) refuses on the mixed
publication dates (the exact 2026-11-08 failure) and checks
(2) and (6) refuse on the set-equality rule. Run standalone:
python3 test_squeeze_rotation_20261108.py (exit 0 = pass).
"""
import gzip
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).resolve().parent


def load_module():
    spec = importlib.util.spec_from_file_location(
        "refresh_squeeze_rotation_test", SITE / "refresh_squeeze.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def reading(sym, settlement, shares, float_shares, pub):
    return {"symbol": sym, "settlement_date": settlement,
            "si_shares": shares, "float_shares": float_shares,
            "publication_date": pub}


def prov_entry(settlement, si_pct, dtc):
    return {"si": {"settlement_date": settlement,
                   "si_pct_of_shares_out": si_pct,
                   "days_to_cover": dtc}}


def store_row(settlement, shares, dtc):
    return {"settlement_date": settlement, "si_shares": shares,
            "adv": 1000.0, "days_to_cover": dtc}


PATH_CONSTS = ("PIT_PATH", "PROVENANCE_PATH", "STUDIES_PATH",
               "FEED_PATH", "LOG_PATH", "SHORTVOL_DIR",
               "SI_STORE_PATH", "OUT_PATH")


def run_case(mod, tmp, readings, prov, store_names):
    pit = tmp / "pit.jsonl"
    pit.write_text("".join(json.dumps(r) + "\n" for r in readings),
                   encoding="utf-8")
    (tmp / "prov.json").write_text(json.dumps(prov),
                                   encoding="utf-8")
    pane = {"state": "no_data", "rows": [],
            "vendor_calibration": {
                "top10_plus20_in_5_sessions": 3,
                "top10_minus20_in_5_sessions": 1,
                "base_plus20": 0.1, "base_minus20": 0.2,
                "top10_median_5d_return": 0.01}}
    (tmp / "studies.json").write_text(
        json.dumps({"squeeze": pane}), encoding="utf-8")
    (tmp / "feed.json").write_text(json.dumps({
        "squeeze": pane, "generated_at_utc": "2026-11-09T00:00:00Z",
        "lanes": {"lanes": {"short_volume": {
            "status": "ok", "days": 1, "first_date": "2026-11-06",
            "last_date": "2026-11-06"}}}}), encoding="utf-8")
    (tmp / "log.jsonl").write_text(json.dumps({
        "component": "squeeze-pane",
        "value": {"state": "no_data", "gated_n": 0}}) + "\n",
        encoding="utf-8")
    sv_dir = tmp / "shortvol"
    sv_dir.mkdir(exist_ok=True)
    with gzip.open(sv_dir / "2026-11-06.json.gz", "wt",
                   encoding="utf-8") as fh:
        json.dump({"date": "2026-11-06", "names": {}}, fh)
    (tmp / "store.json").write_text(
        json.dumps({"names": store_names}), encoding="utf-8")
    out = tmp / "out.json"
    orig = {k: getattr(mod, k) for k in PATH_CONSTS}
    mod.PIT_PATH = str(pit)
    mod.PROVENANCE_PATH = str(tmp / "prov.json")
    mod.STUDIES_PATH = str(tmp / "studies.json")
    mod.FEED_PATH = str(tmp / "feed.json")
    mod.LOG_PATH = str(tmp / "log.jsonl")
    mod.SHORTVOL_DIR = str(sv_dir)
    mod.SI_STORE_PATH = str(tmp / "store.json")
    mod.OUT_PATH = str(out)
    try:
        rc = mod.build()
    finally:
        for k, v in orig.items():
            setattr(mod, k, v)
    return rc, (json.loads(out.read_text(encoding="utf-8"))
                if rc == 0 else None)


def base_case():
    """AAA admitted by the first gather (publication 2026-10-26,
    provenance-carried); BBB rotated in by the second gather
    (publication 2026-11-08, store-carried only)."""
    readings = [
        reading("AAA", "2026-09-30", 900.0, 10000.0, "2026-10-26"),
        reading("AAA", "2026-10-15", 1000.0, 10000.0, "2026-10-26"),
        reading("BBB", "2026-09-30", 1800.0, 10000.0, "2026-11-08"),
        reading("BBB", "2026-10-15", 2000.0, 10000.0, "2026-11-08"),
    ]
    prov = {"_meta": {"as_of": "2026-11-09"},
            "AAA": prov_entry("2026-10-15", 10.0, 5.0)}
    store = {"AAA": [store_row("2026-10-15", 1000.0, 5.0)],
             "BBB": [store_row("2026-10-15", 2000.0, 4.0)]}
    return readings, prov, store


def main() -> int:
    fails = []
    mod = load_module()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # (1)+(2): mixed vintages and a store-only carrier pass.
        rc, data = run_case(mod, tmp, *base_case())
        if rc != 0:
            fails.append("sound rotated case refused (rc=%d)" % rc)
        else:
            if data["published_date"] != "2026-11-08":
                fails.append("published_date %r, want the latest "
                             "vintage 2026-11-08"
                             % data["published_date"])
            names = {n["symbol"]: n for n in data["names"]}
            if set(names) != {"AAA", "BBB"}:
                fails.append("names %r" % sorted(names))
            elif names["BBB"]["days_to_cover"] != 4.0:
                fails.append("BBB days_to_cover %r, want the "
                             "store's 4.0"
                             % names["BBB"]["days_to_cover"])
            if data["coverage"]["names_cross_checked"] != 1:
                fails.append("cross_checked %r, want 1 (AAA only)"
                             % data["coverage"]["names_cross_checked"])
        # (3): store share count disagreement refuses.
        readings, prov, store = base_case()
        store["BBB"] = [store_row("2026-10-15", 9999.0, 4.0)]
        rc, _ = run_case(mod, tmp, readings, prov, store)
        if rc == 0:
            fails.append("store si_shares disagreement published")
        # (4): gathering vs store days-to-cover disagreement.
        readings, prov, store = base_case()
        store["AAA"] = [store_row("2026-10-15", 1000.0, 9.0)]
        rc, _ = run_case(mod, tmp, readings, prov, store)
        if rc == 0:
            fails.append("days-to-cover disagreement published")
        # (5): a gathering-carried name absent from the readings.
        readings, prov, store = base_case()
        prov["ZZZ"] = prov_entry("2026-10-15", 10.0, 5.0)
        rc, _ = run_case(mod, tmp, readings, prov, store)
        if rc == 0:
            fails.append("provenance-only name published")
        # (6): rotated out: carried by no current record, so
        # excluded and named, never silently dropped.
        readings, prov, store = base_case()
        readings.append(reading("OLD", "2026-10-15", 500.0,
                                10000.0, "2026-10-26"))
        rc, data = run_case(mod, tmp, readings, prov, store)
        if rc != 0:
            fails.append("rotated-out case refused (rc=%d)" % rc)
        else:
            if data["rotated_out_names"] != ["OLD"]:
                fails.append("rotated_out_names %r"
                             % data["rotated_out_names"])
            if "OLD" in {n["symbol"] for n in data["names"]}:
                fails.append("rotated-out name listed")
    for f in fails:
        print("FAIL: " + f)
    print("squeeze rotation tests: %s (%d failures)"
          % ("PASS" if not fails else "FAIL", len(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
