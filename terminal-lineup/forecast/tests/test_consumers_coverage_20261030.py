"""Regression blockers for the 2026-10-30 remainders wave 2,
fix stream B (consumers and coverage). Each test pins one cure
at the source. Fail direction: on the pre-cure tree, Receipts
counted 18 tools and Proving Ground 42, the sector page carried
335 unmapped names as a bare count with no names and no second
terminal source, the short-interest PIT held 29 rows (2
settlements) against the store's 550, the Squeeze page named
neither basis-gap name, and the bundle builder appended only
the freshest settlement per run."""
import json
import os

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
MORGUE = os.path.expanduser("~/workspace/morgue")


def load(slug):
    with open(os.path.join(SITE, slug, "data.json")) as fh:
        return json.load(fh)


def src(name):
    with open(os.path.join(SITE, name)) as fh:
        return fh.read()


def test_receipts_cover_all_70_tools():
    d = load("receipts")
    assert d["tools_count"] == 70
    assert len(d["receipts"]) == 70
    slugs = [r["slug"] for r in d["receipts"]]
    assert len(set(slugs)) == 70
    for slug in ("receipts", "greeks-sketch", "proving-ground",
                 "momentum-clock", "echo-lens"):
        assert slug in slugs, slug


def test_proving_ground_covers_all_70_tools():
    d = load("proving-ground")
    assert d["tools_count"] == 70
    assert sum(d["counts"].values()) == 70
    assert len(d["tools"]) == 70
    assert "all 70" in d["joining_note"]


def test_proving_ground_states_tie_to_declared_states():
    # The refresher must keep the fail-closed tie between its
    # classification and each added tool's own declared state.
    s = src("refresh_provingground.py")
    assert "WORD_TO_STATE" in s and "declares" in s
    pg = {t["slug"]: t["state"] for t in load("proving-ground")["tools"]}
    words = {"Backed by a finished study": "study",
             "Live record being graded": "live",
             "Still being proven": "proving",
             "Waiting on records": "waiting",
             "A measuring tool, nothing to prove": "measuring"}
    checked = 0
    for slug, state in pg.items():
        try:
            d = load(slug)
        except OSError:
            continue
        declared = d.get("proving_state")
        if isinstance(declared, str) and declared in words:
            assert words[declared] == state, slug
            checked += 1
    assert checked >= 20


def test_sector_unmapped_names_are_named_with_reason():
    d = load("sector-rotation")
    counts = d["counts"]
    assert len(d["unmapped_names"]) == \
        counts["names_without_sector_on_record"]
    assert d["unmapped_note"]
    assert "names_filled_from_terminal_records" in d
    # The refresher adopts sectors from the terminal's own
    # Screener record and fails closed on a disagreement.
    s = src("refresh_rotation.py")
    assert "SCREENER_PATH" in s and "contested sector" in s


def test_squeeze_page_covers_the_store():
    d = load("squeeze-watch")
    cov = d["coverage"]
    assert cov["names_in_store"] == 22
    assert cov["names_covered"] + cov["names_without_float_basis"] \
        == cov["names_in_store"]
    assert cov["with_prior_reading"] == cov["names_covered"]
    assert len(d["settlements_on_record"]) >= 25
    gap = {g["symbol"] for g in d["basis_gap_names"]}
    assert gap == {"CENTA", "PDBC"}
    for g in d["basis_gap_names"]:
        assert g["settlements_on_record"] == 25 and g["reason"]


def test_pit_store_carries_every_settlement():
    pit = [json.loads(ln) for ln in open(
        os.path.join(MORGUE, "output", "short_interest_pit.jsonl"))]
    assert len(pit) == 500
    per_name = {}
    for r in pit:
        per_name.setdefault(r["symbol"], set()).add(
            r["settlement_date"])
    assert len(per_name) == 20
    assert all(len(v) == 25 for v in per_name.values())


def test_bundle_builder_appends_all_settlements():
    with open(os.path.join(MORGUE, "inst_bundle.py")) as fh:
        s = fh.read()
    assert "for row in rows:" in s
    assert "no_float_basis" in s
    assert "settlements_recorded" in s
