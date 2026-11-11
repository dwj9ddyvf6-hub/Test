#!/usr/bin/env python3
"""T12 registry guard (B3, T12-B0-B3-20261111).

Design of record: T12-CONTRACTS.md section 5 item 2 ("A surface with
no contract is itself the defect... Any served site/<slug>/ with a
data.json and no registry entry is reported as a contract-registry
breach") and the declaration worklist's step B3 ("a check that fails
when any served site/<slug>/ with a data.json has no registry
entry"). The build list for this lane is EC-B12 in the
estate-completeness MASTER-LEDGER.

Scope, stated plainly: the T12 contract system covers the 23
surfaces the spec's section 2 census enumerates (the stale and
undated class). The terminal serves many more surfaces than those
23; they carry dated readings resolved by freshness.py and were
never in the T12 census universe, so this guard does not invent
contract breaches for them. The guard's fail-closed universe is
the triangle between three sources, any disagreement among which
is a breach:

  EXPECTED_SURFACES  the 23 slugs from T12-CONTRACTS.md section 2,
                     restated here so that REMOVING a contract from
                     the registry cannot make the guard pass: the
                     surface is still expected, still served, and
                     now unregistered, which is the breach;
  the registry       site/freshness_contracts.json as declared;
  the tree           site/<slug>/ directories, their data.json
                     shape, and the producer files in site/.

Breaches (exit 1, each named):
  - an expected surface has no contract, or the registry carries a
    contract for a surface outside the expected census set;
  - a duplicate contract for one surface;
  - a contract missing any of the 13 spec section 1 fields, with an
    empty value where the spec requires one (producing_lanes may be
    empty only for the static no-producer exceptions);
  - an exception-class contract whose exception object lacks kind,
    authority or re_review_trigger, or a non-exception contract
    carrying an exception object;
  - a contract whose surface directory does not exist, whose
    producer file does not exist, or (producer named) whose surface
    has no data.json;
  - a static no-producer contract (producer "none") whose surface
    HAS grown a data.json: the exception's premise is gone and the
    surface needs a full contract before it may serve figures;
  - a contracted surface with no href in grok-index.json (the spec
    section 1 identity: slug == directory == grok href).

Run standalone (`python3 freshness_guard.py`, exit 0/1) or import
check_registry() from the blocker test. The guard reads only; it
never edits the registry or the tree.
"""
import json
import os
import sys

SITE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(SITE, "freshness_contracts.json")
GROK_INDEX = os.path.join(SITE, "grok-index.json")

# The T12 census universe: T12-CONTRACTS.md section 2 (2a: 4 weekly,
# 2b: 5 forecast-engine incl. the abstention-signal exception,
# 2c: 10 tools chain, 2d: 1 stores lane, 2e: 3 static exceptions;
# 23 in all). Restated, not read from the registry, so a deleted
# contract is itself detectable.
EXPECTED_SURFACES = (
    "13f-tracker", "smart-money-tracker", "filings-wire",
    "insider-wire",
    "grade-a-board", "half-life-clock", "mortality-curve",
    "streak-trap", "abstention-signal",
    "squeeze-watch", "decay-watch", "odds-cards", "week-ahead",
    "expected-move", "signal-feed", "survivors-wire", "echo-lens",
    "one-page-report", "promoted-book",
    "state-analogue",
    "greeks-sketch", "payoff-sketch", "how-it-works",
)

REQUIRED_FIELDS = (
    "surface", "producer", "producing_lanes", "cadence_class",
    "load_anchor", "reading_date_field", "freshness_sla",
    "warn_threshold", "strict_threshold", "serving_on_warn",
    "serving_on_strict", "exception", "quality_rules",
)


def check_registry(site_dir, registry_path=None, expected=EXPECTED_SURFACES):
    """Return the list of registry breaches (empty == guard passes).

    ``site_dir`` is the tree the registry describes (the directory
    holding freshness_contracts.json, the surface directories, the
    producer scripts and grok-index.json). Tests pass a fixture
    tree; production passes SITE.
    """
    breaches = []
    registry_path = registry_path or os.path.join(
        site_dir, "freshness_contracts.json")
    try:
        with open(registry_path, encoding="utf-8") as fh:
            registry = json.load(fh)
    except (OSError, ValueError) as exc:
        return [f"registry unreadable: {registry_path}: {exc}"]
    contracts = registry.get("contracts")
    if not isinstance(contracts, list):
        return ["registry carries no contracts list"]

    by_surface = {}
    for contract in contracts:
        surface = contract.get("surface")
        if surface in by_surface:
            breaches.append(f"duplicate contract: {surface}")
        by_surface[surface] = contract

    expected_set = set(expected)
    for surface in sorted(expected_set - set(by_surface)):
        breaches.append(
            f"served surface has no contract: {surface} "
            "(expected by T12-CONTRACTS.md section 2)")
    for surface in sorted(set(by_surface) - expected_set):
        breaches.append(
            f"contract names a surface outside the T12 census set: "
            f"{surface}")

    grok_hrefs = set()
    try:
        with open(os.path.join(site_dir, "grok-index.json"),
                  encoding="utf-8") as fh:
            grok_hrefs = {entry.get("href", "").rstrip("/")
                          for entry in json.load(fh)}
    except (OSError, ValueError) as exc:
        breaches.append(f"grok-index.json unreadable: {exc}")

    for surface in sorted(expected_set & set(by_surface)):
        contract = by_surface[surface]
        for field in REQUIRED_FIELDS:
            if field not in contract:
                breaches.append(f"{surface}: contract field missing: "
                                f"{field}")
            elif field != "exception" and field != "producing_lanes" \
                    and not contract[field]:
                breaches.append(f"{surface}: contract field empty: "
                                f"{field}")
        if contract.get("cadence_class") == "exception":
            exc = contract.get("exception")
            if not isinstance(exc, dict) or not all(
                    exc.get(k) for k in
                    ("kind", "authority", "re_review_trigger")):
                breaches.append(
                    f"{surface}: exception-class contract lacks a "
                    "complete exception object (kind, authority, "
                    "re_review_trigger)")
        elif contract.get("exception") is not None:
            breaches.append(
                f"{surface}: non-exception contract carries an "
                "exception object")

        surface_dir = os.path.join(site_dir, surface)
        if not os.path.isdir(surface_dir):
            breaches.append(
                f"{surface}: contract names a surface that no longer "
                "exists (no site directory)")
            continue
        if surface not in grok_hrefs:
            breaches.append(
                f"{surface}: no grok-index.json href for the "
                "contracted surface")
        producer = contract.get("producer")
        data_json = os.path.join(surface_dir, "data.json")
        if producer == "none":
            if contract.get("producing_lanes"):
                breaches.append(
                    f"{surface}: static contract names producing "
                    "lanes but no producer")
            if os.path.exists(data_json):
                breaches.append(
                    f"{surface}: static no-producer exception now "
                    "has a data.json; it needs a full contract "
                    "before serving figures")
        else:
            if not producer or not os.path.isfile(
                    os.path.join(site_dir, producer)):
                breaches.append(
                    f"{surface}: producer file does not exist: "
                    f"{producer}")
            if not os.path.exists(data_json):
                breaches.append(
                    f"{surface}: contracted surface has no data.json")
    return breaches


def main():
    breaches = check_registry(SITE)
    if breaches:
        print(f"T12 REGISTRY GUARD: FAIL ({len(breaches)} breach(es))")
        for breach in breaches:
            print(f"  BREACH {breach}")
        return 1
    print(f"T12 REGISTRY GUARD: PASS ({len(EXPECTED_SURFACES)} "
          "contracts matched to surfaces, no orphans either way)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
