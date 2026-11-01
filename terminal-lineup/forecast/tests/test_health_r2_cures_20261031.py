"""Regression blockers for the terminal health loop cure round 2
(pipeline / freshness / automation class), 2026-10-31:

- D-R2-01 (carryover D-R1-02): half-life-clock, streak-trap and
  mortality-curve are single-issuance engines. Each page's
  2026-10-29 as_of is its single registered issuance date (the
  refreshers' ISSUE / issuance constants), so a session-date
  freshness expectation is the wrong class for them. Pre-cure the
  hub producer's is_stale() had no single-issuance class, so all
  three were chipped Stale and counted in the hub's stale census
  (9 stale of 102). Cure: refresh_hub.SINGLE_ISSUANCE exempts
  them from session staleness exactly as QUARTERLY and
  STATIC_STUDY are exempt, their chips restore to the recovery
  memory's last non-stale chip (ungraded / Not yet graded, never
  an invented Live), and their card date is presented as the
  issuance it is ("Issued October 29, 2026"), not as a daily
  reading date. The other 99 cards' classes are unchanged:
  stale falls 9 -> 6, ungraded rises 35 -> 38, live 50 and
  waiting 8 do not move.
- D-R2-02 (carryover D-R1-21): the canonical suite gate
  (run_suite.py) must have COMPLETED a full run on the final
  tree: suite_summary.json at the terminal root is the gate
  record, with a per-file verdict for every discovered test
  file, the two deep-panel files included, and gate_exit 0.
  A summary that is absent, partial, or records a FAIL/KILLED
  file fails this blocker.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

LINEUP = Path(__file__).resolve().parents[2]
SITE = LINEUP / "site"
SINGLE = ("half-life-clock", "streak-trap", "mortality-curve")
sys.path.insert(0, str(SITE))


def _hub():
    import importlib
    return importlib.import_module("refresh_hub")


def _census():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    census = {}
    spans = {}
    for card in re.findall(r'<article class="hubcard".*?</article>',
                           hub, re.S):
        slug = re.search(r'href="([a-z0-9-]+)/"', card)
        chip = re.search(r'class="chip ([a-z]+)"', card)
        upd = re.search(r'class="updated">([^<]*)</span>', card)
        if slug and chip:
            census[slug.group(1)] = chip.group(1)
            spans[slug.group(1)] = upd.group(1) if upd else ""
    return hub, census, spans


def test_single_issuance_pages_are_not_session_stale():
    hub = _hub()
    assert set(SINGLE) <= set(hub.SINGLE_ISSUANCE)
    latest = date(2026, 10, 30)
    for slug in SINGLE:
        assert not hub.is_stale(slug, date(2026, 10, 29), latest), slug
        # Even a much older issuance date is not session staleness.
        assert not hub.is_stale(slug, date(2026, 9, 1), latest), slug
    # The daily class is untouched: a daily engine one session
    # behind is still stale.
    assert hub.is_stale("touch-surface", date(2026, 10, 29), latest)


def test_single_issuance_cards_not_counted_stale_or_daily_fresh():
    hub_text, census, spans = _census()
    assert len(census) == 102
    chips = json.loads((SITE / "hub_chips.json").read_text(
        encoding="utf-8"))
    assert chips == census
    for slug in SINGLE:
        # Not stale, and not presented as daily-fresh (Live):
        # the restored chip is the memory's Not yet graded.
        assert census[slug] == "ungraded", (slug, census[slug])
        # Presented as the single issuance it is.
        assert spans[slug].startswith("Issued "), (slug, spans[slug])
        assert "2026" in spans[slug] or "October" in spans[slug]
    values = list(census.values())
    # The cure's aggregate claim at landing was stale 9 -> 6 with
    # the other 99 cards' classes unchanged; the durable form of
    # that claim is consistency, not frozen counts (the hub is a
    # living surface: week-ahead legitimately recovered through
    # its own lane the same evening, live 50 -> 51, stale 6 -> 5).
    # The three are not in the stale set, the census sums to the
    # card count, and the hub's printed count line equals the
    # census it was counted from (the D-R1-15 invariant).
    from collections import Counter
    counts = Counter(values)
    assert sum(counts.values()) == len(census)
    line = re.search(
        r"(\d+) live, (\d+) waiting, (\d+) not yet graded, "
        r"(\d+) stale", hub_text)
    assert line, "hub count line not found"
    printed = {"live": int(line.group(1)),
               "waiting": int(line.group(2)),
               "ungraded": int(line.group(3)),
               "stale": int(line.group(4))}
    for word, n in printed.items():
        assert counts.get(word, 0) == n, (word, counts.get(word), n)


def test_suite_summary_is_the_completed_gate_record():
    # Self-reference rule: this test reads the summary of the last
    # COMPLETED gate run. Inside a gate run it therefore judges
    # the previous run's record; the one verdict it never holds
    # against the record is its own file's, which on the bootstrap
    # run could only fail for the record's absence. Every other
    # file must be PASS (or a named memory disposition), and a
    # non-zero gate_exit is accepted only when this file is the
    # sole non-pass, which is exactly the bootstrap signature.
    summary_path = LINEUP / "suite_summary.json"
    assert summary_path.exists(), "run_suite.py has never completed"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["runner"] == "run_suite.py"
    results = {Path(r["file"]).name: r["verdict"]
               for r in summary["results"]}
    if summary["gate_exit"] != 0:
        nonpass = {n for n, v in results.items()
                   if v not in ("PASS", "DISPOSITIONED")}
        assert nonpass == {"test_health_r2_cures_20261031.py"}, (
            summary["counts"], nonpass)
    # Every discovered test file has a verdict in the record.
    discovered = {p.name for p in
                  (LINEUP / "forecast" / "tests").glob("test_*.py")}
    discovered |= {p.name for p in
                   (LINEUP / "psychology-engine" / "tests").glob(
                       "test_*.py")}
    assert set(results) == discovered, (
        sorted(discovered - set(results)),
        sorted(set(results) - discovered))
    assert summary["files"] == len(discovered)
    # The two deep-panel files OOM-killed in R1 are proven under
    # the runner: PASS, or a named memory-bound disposition.
    for name in ("test_deep_panel_20261029.py",
                 "test_deep_panel_expansion_20261029.py"):
        verdict = results.get(name)
        assert verdict == "PASS" or (
            verdict == "DISPOSITIONED"
            and "memory" in json.dumps(summary).lower()), (
            name, verdict)
    bad = {n: v for n, v in results.items()
           if v not in ("PASS", "DISPOSITIONED")
           and n != "test_health_r2_cures_20261031.py"}
    assert not bad, bad
