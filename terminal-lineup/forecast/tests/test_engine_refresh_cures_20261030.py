"""Regression blockers for the 2026-10-30 forecast engine refresh
cure (15 refreshers down on the first scheduled refresh_engines.py
run; record: research_notes/remainders-fix-20261030/
ENGINE-REFRESH-CURE-20261030.md).

Defect classes pinned here:

1. Grade-append identity (the one code break). RC-21 froze a label
   identity onto every forecast issued through
   append_forecast_declared, and ledger.append_grade refuses a
   grade append that does not repeat it. Five engine refreshers
   still appended grades bare and broke (streak-trap in its
   self-test; the other four on latent production paths). The
   tests below pin the ledger contract and assert every direct
   append_grade call site in the consumer refreshers repeats the
   frozen identity, the pattern grading.py and calibration-league
   already used.

2. Insider producer totals. The RC-16 widening republished
   insider-wire with 100 names on the page while
   totals.names_covered still counted only the 50 board names, so
   four engine consumers refused the record on their recount
   guards. The producer now publishes names_covered as the count
   of the names it publishes; the invariant is pinned against the
   page on disk.

3. Engine 1 guard widening. Corrected Band's published bands
   carry the FE12 session-quality widening factor by registered
   construction. Family Fracture and Wall Lifetime cross-checked
   the published bands against the raw recipe and refused them.
   Their cross-checks now apply the band page's own published
   factor; the factor's presence on the band page is pinned.

4. Calendar ordering. Earnings Distribution recounts the
   calendar's published moves exactly from the priced move
   record; the engine runner regenerates that record in its own
   pre-steps, so the calendar must be republished from the fresh
   record inside the same cycle. The runner's pre-step order is
   pinned.

5. Vol Term Shape carried record. Its per-name block described
   the retired Bilbo lane (60 names); IV Weather now reads the
   modelled IV ledger. The published block must carry the IV
   page's own figures, pinned against the page on disk.

Census and register re-takes (abstention-signal, half-life-clock,
in-regime-oracle, living-router, sponsored-reset's fear count,
replication-wire's golden-sweep claim) are guarded by the
refreshers' own fail-closed checks and the scheduled full run;
their recounts are recorded in the cure record, not duplicated
here.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "..", "site"))
FORECAST = os.path.abspath(os.path.join(HERE, ".."))
for p in (SITE, FORECAST):
    if p not in sys.path:
        sys.path.insert(0, p)


def _read_site_json(rel):
    with open(os.path.join(SITE, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _read_site_source(name):
    with open(os.path.join(SITE, name), encoding="utf-8") as fh:
        return fh.read()


# ------------------------------------------------------------------
# 1. Grade-append identity
# ------------------------------------------------------------------

def test_grade_append_must_repeat_frozen_label_identity(tmp_path):
    from ledger import Ledger, frozen_label_identity
    from registry import Registry

    reg = Registry(os.path.join(FORECAST, "registry.json"))
    led = Ledger(str(tmp_path / "ledger.jsonl"), registry=reg)
    led.append_genesis("engine refresh cure contract test")
    clocks = {c: "2026-10-30" for c in (
        "event_time", "publication_time", "first_available_time",
        "ingestion_time", "decision_as_of")}
    row, created = led.append_forecast_declared(
        engine_id="engine_28", issued_ts="2026-10-30",
        subject="TEST", quantity="gap_outcome_distribution",
        value={"p_up": 0.5}, horizon_open="2026-11-02",
        horizon_close="2026-11-03",
        lineage={"clocks": clocks}, families=["price"],
        outcome={"kind": "gap_outcome", "symbol": "TEST"})
    assert created
    assert frozen_label_identity(row), (
        "a declared forecast must carry its frozen label identity")
    grade = {"rule_id": "brier", "scores": {"brier": 0.25}}
    try:
        led.append_grade(forecast_row=row, grade=grade)
    except Exception:
        pass
    else:
        raise AssertionError(
            "append_grade accepted a grade that does not repeat the "
            "frozen label identity; the RC-21 refusal is gone")
    grow = led.append_grade(
        forecast_row=row, grade=grade,
        **(frozen_label_identity(row) or {}))
    assert grow["type"] == "grade"


def test_streaktrap_self_test_grades_declared_rows():
    import importlib
    from registry import Registry

    mod = importlib.import_module("refresh_streaktrap")
    reg = Registry(os.path.join(FORECAST, "registry.json"))
    result = mod.self_test(reg)
    assert isinstance(result, dict)


def _call_args(src, start):
    """The argument text of the call whose opening paren ends at
    start, by balanced parens."""
    depth = 1
    i = start
    while i < len(src) and depth:
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
        i += 1
    return src[start:i - 1]


def test_every_direct_append_grade_site_repeats_the_identity():
    offenders = []
    for name in ("refresh_streaktrap.py", "refresh_feardaytriangulation.py",
                 "refresh_silentaccumulation.py", "refresh_sponsoredreset.py",
                 "refresh_inregimeoracle.py", "refresh_calibrationleague.py"):
        src = _read_site_source(name)
        for m in re.finditer(r"append_grade\(", src):
            args = _call_args(src, m.end())
            if "frozen_label_identity(row)" not in args \
                    and "ledger_frozen_identity(row)" not in args:
                offenders.append(f"{name}@{src[:m.start()].count(chr(10)) + 1}")
    assert not offenders, (
        "append_grade call sites that do not repeat the frozen "
        f"label identity: {offenders}")


# ------------------------------------------------------------------
# 2. Insider producer totals
# ------------------------------------------------------------------

def test_insider_page_totals_agree_with_its_names():
    page = _read_site_json(os.path.join("insider-wire", "data.json"))
    names = page["names"]
    totals = page["totals"]
    assert totals["names_covered"] == len(names), (
        "totals.names_covered must count the names the page "
        "publishes (the RC-16 widening publishes board plus "
        "store-only names)")
    with_summary = [n for n in names if n.get("summary")]
    without = [n for n in names if not n.get("summary")]
    assert totals["names_with_summary"] == len(with_summary)
    assert totals["names_not_on_record"] == len(without)
    assert totals["open_buys"] == sum(
        n["summary"]["buys"]["count"] for n in with_summary)
    assert totals["open_sells"] == sum(
        n["summary"]["sells"]["count"] for n in with_summary)


# ------------------------------------------------------------------
# 3. Engine 1 guard widening is published on the band page
# ------------------------------------------------------------------

def test_corrected_band_page_publishes_its_guard_factor():
    band = _read_site_json(os.path.join("corrected-band", "data.json"))
    guard = band["live"]["session_quality_guard"]
    assert isinstance(guard["band_widen_factor"], (int, float))
    assert guard["band_widen_factor"] > 0
    for name in ("refresh_familyfracture.py", "refresh_walllifetime.py"):
        src = _read_site_source(name)
        assert "session_quality_guard" in src, (
            f"{name} must read Engine 1's published guard factor "
            "in its band cross-check")


# ------------------------------------------------------------------
# 4. Calendar ordering inside the engine runner
# ------------------------------------------------------------------

def test_engine_runner_republishes_calendar_after_priced_moves():
    src = _read_site_source("refresh_engines.py")
    lanes = re.findall(r'\("([a-z0-9-]+)",\s*\[sys\.executable', src)
    assert "priced-moves" in lanes and "earnings-calendar" in lanes
    assert lanes.index("priced-moves") < lanes.index("earnings-calendar"), (
        "the earnings calendar must be republished from the fresh "
        "priced move record inside the engine cycle, after the "
        "priced-moves lane and before the engines run")


# ------------------------------------------------------------------
# 5. Vol Term Shape carries the IV page's own figures
# ------------------------------------------------------------------

def test_voltermshape_carries_the_iv_pages_own_name_count():
    iv = _read_site_json(os.path.join("iv-weather", "data.json"))
    page = _read_site_json(os.path.join("vol-term-shape", "data.json"))
    carried = page["live"]["per_name"]
    assert carried["names_on_record"] == iv["distinct_names"]
    assert carried["freshest_date"] == iv["freshest_date"]


def test_sponsoredreset_holds_no_settled_count_pin():
    src = _read_site_source("refresh_sponsoredreset.py")
    assert "len(fear_days) != 22" not in src, (
        "the settled fear-day count pin measured on the truncated "
        "gauge record is back; the check is membership in the "
        "price history, not a count")
    assert "not in spy_dates" in src


# ------------------------------------------------------------------
# 6. Proof gate recount (run-context failure, found by the first
# full run after the cure: the gate's publisher had appended the
# 2026-10-29 forward rows but its republication never landed, so
# every consumer embedding the gate block refused it)
# ------------------------------------------------------------------

def test_proof_gate_record_recounts_against_the_ledger():
    sys.path.insert(0, SITE)
    import proof_gate_block

    gate = _read_site_json(os.path.join("proof-gate", "data.json"))
    forward = gate["forward_ledger"]
    ledger_path = os.path.join(FORECAST, "ledger.jsonl")
    distinct, total = proof_gate_block.recount_forward_rows(ledger_path)
    assert forward["created"] == distinct, (
        "the proof gate's published created count does not recount "
        "against the ledger's Engine 19 forward rows")
    assert forward["ledger_rows"] == total, (
        "the proof gate's published ledger_rows does not recount "
        "against the ledger's Engine 19 forward rows")
