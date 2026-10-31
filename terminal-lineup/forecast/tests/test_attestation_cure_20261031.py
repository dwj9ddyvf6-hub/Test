"""Blockers for the 2026-10-31 terminal total audit round 1 cures
(sector engines-a: engines 1 to 15, registry, Record).

ATTESTATION-RECOUNT-20261031: registry and page calibration
attestations disagreed with the ledger valid recount for engines
5, 8, 9, 10, 11, 12, 14, 15 and others, and verify_grade_rows.py
passed because it never compared attestations against the recount.
Fail direction: on the pre-cure tree the recount tests below fail
on 13 registry records and 13 page blocks (the extended verifier
printed 26 mismatches), and the source tests fail because
forecast/refresh_attestations.py did not exist and
refresh_engines.py carried no attestation step.

REFRESH-PROOF-LOG-20261031: refresh_proof.log still held the
2026-10-30 02:57 run because refresh_engines.py never wrote it.
Fail direction: the writer and its wiring are absent pre-cure.

VIX-LINEAGE-NOTE-20261031: Engine 1 ledger lineage notes carried
a hardcoded stale claim beside a templated date, so notes
contradicted the VIX store state at issuance and the engine page
republished after the capture lane advanced the store.
Fail direction: vix_lineage_note does not exist pre-cure.

ATTESTATION-BLOCKER-BASIS-20261031: the recount tests below
compared attestations against the recount's full valid basis
(forecasts_valid / grades_valid), while attestations are stamped
on the attestation basis the verifier itself ties against
(forecasts_valid_own / grades_valid_own: the valid recount
excluding hosted foreign rows and their grades, cure
ORACLE-COUNT-BASIS-20261031). The two bases differ only for
engine_19, which hosts the Aperture proof gate's 31,649
provisional rows, so the blocker failed on that engine alone
while the verifier passed it: the tree's gates disagreed about
the engine_19 contract. Fail direction: on the pre-cure blocker
the two recount tests fail with the sole mismatch
('engine_19', (0, 0), (31649, 0)); after the cure expected()
recounts on the same own basis the attestation stamps and the
verifier ties, and a genuinely re-based or fabricated attestation
still fails (negative control in the cure record).
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORECAST = os.path.dirname(HERE)
ROOT = os.path.dirname(FORECAST)
SITE = os.path.join(ROOT, "site")
sys.path.insert(0, ROOT)
sys.path.insert(0, SITE)

from forecast import verify_grade_rows as V  # noqa: E402


def _load_site_module(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_RECOUNT = None


def recount():
    global _RECOUNT
    if _RECOUNT is None:
        _RECOUNT = V.recount(os.path.join(FORECAST, "ledger.jsonl"))
    return _RECOUNT


def expected(eid):
    # Attestations are stamped and tied on the attestation basis
    # (ORACLE-COUNT-BASIS-20261031): the valid recount excluding
    # hosted foreign rows and their grades, which
    # verify_grade_rows.recount reports as forecasts_valid_own /
    # grades_valid_own and its attestation ties compare against.
    # For engines hosting no foreign rows the own basis equals the
    # full valid basis.
    per = recount()["per_engine"].get(eid) or {}
    return (per.get("forecasts_valid_own",
                    per.get("forecasts_valid", 0)),
            per.get("grades_valid_own",
                    per.get("grades_valid", 0)))


def test_registry_attestations_match_verifier_recount_all_engines():
    reg = json.load(open(os.path.join(FORECAST, "registry.json")))
    assert len(reg["engines"]) == 30
    bad = []
    for eng in reg["engines"]:
        att = eng["calibration_attestation"]
        got = (att["forecasts_recorded"], att["graded_forecasts"])
        if got != expected(eng["id"]):
            bad.append((eng["id"], got, expected(eng["id"])))
    assert bad == [], bad


def test_every_engine_page_attestation_matches_recount():
    bad = []
    seen = 0
    for name in sorted(os.listdir(SITE)):
        path = os.path.join(SITE, name, "data.json")
        if not os.path.isfile(path):
            continue
        data = json.load(open(path, encoding="utf-8"))
        block = data.get("calibration_attestation") or {}
        att = block.get("attestation") or {}
        eid = block.get("engine_id")
        if not eid or "forecasts_recorded" not in att:
            continue
        seen += 1
        got = (att["forecasts_recorded"], att["graded_forecasts"])
        if got != expected(eid):
            bad.append((name, eid, got, expected(eid)))
    assert seen >= 30, seen
    assert bad == [], bad


def test_attestation_record_uses_valid_void_aware_counts():
    from forecast import grading
    figures = {"forecasts": 112, "forecasts_valid": 86, "graded": 0,
               "mean_scores": {}}
    rec = grading.attestation_record({"id": "engine_14"}, figures,
                                     "2026-10-31")
    assert rec["forecasts_recorded"] == 86
    assert "86 recorded" in rec["basis"]


def test_refresh_attestations_module_regenerates_from_recount():
    src = open(os.path.join(FORECAST, "refresh_attestations.py"),
               encoding="utf-8").read()
    assert "recompute_figures" in src
    assert "attestation_record" in src
    assert "recorded_on" in src


def test_runner_regenerates_attestations_after_grading():
    src = open(os.path.join(SITE, "refresh_engines.py"),
               encoding="utf-8").read()
    assert "refresh_attestations.py" in src
    assert src.index("run_grading.py") < src.index(
        "refresh_attestations.py")
    assert src.index("refresh_attestations.py") < src.index(
        "for slug in engine_slugs()")


def test_runner_writes_dated_proof_log_on_every_run():
    mod = _load_site_module("refresh_engines")
    src = open(os.path.join(SITE, "refresh_engines.py"),
               encoding="utf-8").read()
    assert "write_proof_log" in src
    out = os.path.join(HERE, "_proof_log_test.txt")
    try:
        mod.write_proof_log(
            "done corrected-band in 13s exit 0\n"
            "engines refreshed: 1\nFAILURES: none\n", 0,
            path=mod.Path(out))
        text = open(out, encoding="utf-8").read()
    finally:
        if os.path.exists(out):
            os.remove(out)
    assert text.startswith("# refresh_engines.py run finished ")
    assert "exit 0" in text.splitlines()[0]
    assert "done corrected-band in 13s exit 0" in text


def test_vix_lineage_note_states_store_date_and_stale_only_when_stale():
    mod = _load_site_module("refresh_correctedband")
    fresh = mod.vix_lineage_note("2026-10-30", "2026-10-29")
    assert "2026-10-30" in fresh
    assert "stale" not in fresh
    stale = mod.vix_lineage_note("2026-10-21", "2026-10-29")
    assert "2026-10-21" in stale
    assert "stale" in stale
    none_note = mod.vix_lineage_note(None, "2026-10-29")
    assert "No volatility-index reading is on record" in none_note


def test_correctedband_lineage_uses_note_helper_not_hardcoded_stale():
    src = open(os.path.join(SITE, "refresh_correctedband.py"),
               encoding="utf-8").read()
    assert "vix_lineage_note(vix_last_date, as_of)" in src
    assert "it is a stale regime reading for \"\n                 \"this forecast" \
        not in src
    assert "(ending {vix_last_date})" in src
    assert "(ending October 21, 2026)" not in src


def test_verifier_checks_attestations_not_only_live_figures():
    src = open(os.path.join(FORECAST, "verify_grade_rows.py"),
               encoding="utf-8").read()
    assert "registry_mismatches" in src
    assert "calibration_attestation." in src
