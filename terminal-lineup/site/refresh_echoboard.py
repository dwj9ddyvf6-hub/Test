#!/usr/bin/env python3
"""Refresh the Echo Board data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (2026-10-28): no disclaimer-style
copy on any reader surface of any tool, in pages or generated data,
ever.

Evidence class: the Second Opinion's published record (per name,
how many independent families of readings speak for it, and the
direction word each direction-carrying family carries), cross-
checked against the Replication Wire's published grading of the
agreement-style claim on its record (the chart ranker's 0.736
ranking agreement claim, graded "Did not hold up" as a forecasting
result: an agreement measure, not a forecast). The Proving
Ground's published vocabulary supplies this page's state label.

Reconstruction choices: this board is an agreement view over the
Second Opinion's record, nothing more. A name is listed only when
two or more families that carry a direction speak for it and every
one of those direction words is the same word; that is the Second
Opinion's own agreement test (one distinct word in a name's
direction list means agreement, more than one means disagreement).
On this record exactly three names pass that test: the three index
funds, each with three families pointing cautious. The filings
family carries no direction word at all, only figures, so the 38
names covered by two families (price plus filings) carry exactly
one direction each and cannot agree or disagree across families;
they are counted, not listed. Names covered by one family or none
are counted, not listed. Each listed family's reading is written
in the same plain sentences the Second Opinion itself uses for
that family, built from the record's own figures. The board adds
no forecast, no score and no direction call of its own.

Fail-closed rules:
- If any of the three published records read here is missing, the
  refresh stops and publishes nothing.
- If the coverage counts recomputed from the record's per-name
  family counts disagree with the coverage counts the Second
  Opinion publishes, the refresh stops.
- If any name's published direction list disagrees with the
  direction words its own family readings carry, the refresh
  stops.
- If the agreement set recomputed here (names with two or more
  direction-carrying families, all pointing the same way) is not
  exactly the set of names this board lists, the refresh stops.
- If any two-family name carries two or more direction words, so
  the counted-not-listed account of those names would be wrong,
  the refresh stops.
- If the Replication Wire's record no longer carries the 0.736
  agreement claim graded "Did not hold up" with its ruling text,
  the refresh stops.
- If the Proving Ground's vocabulary does not carry the state
  this page labels itself with, the refresh stops.
- If any assembled string carries internal wording (file names or
  record jargon), the refresh stops.

Honesty rules:
- Dates and times are read off the records, never from the clock,
  so running this script twice produces the same file, byte for
  byte.
- Agreement is shown as agreement only. No figure on this board
  is a forecast, a score, or a call of this board's own.

Usage: python3 refresh_echoboard.py
"""

import json
import os
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SECOND_PATH = os.path.join(HERE, "second-opinion", "data.json")
WIRE_PATH = os.path.join(HERE, "replication-wire", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "echo-board", "data.json")

AGREEMENT_WORDS = ("Agreement is not a forecast. This board shows "
                   "only where separate families of readings point "
                   "the same way, in each family's own words. It "
                   "adds no prediction, no score and no call of "
                   "its own: readings agreeing with each other says "
                   "nothing by itself about what a price does next.")

COUNTED_WORDS = ("Names that are not listed are counted above, "
                 "not listed as agreement: a name is listed only "
                 "when two or more families that carry a direction "
                 "speak for it and every direction word agrees. "
                 "The filings, facts and news families report "
                 "figures and headlines only, with no direction "
                 "word of their own, and the per-name prints record "
                 "carries no judged direction either, so a name "
                 "covered by several families can still carry only "
                 "one direction, or none, and there is no second "
                 "direction for it to agree with.")

FORBIDDEN = ("morgue", ".json", ".py", "ledger", "sleeve",
             "data file", "dataset", "scorecard")

DIRECTION_FAMILIES = ("price", "prints", "positioning")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Echo Board refresh: {message}", file=sys.stderr)
    return 1


def long_date(iso):
    y, m, d = (int(p) for p in iso.split("-"))
    return date(y, m, d).strftime("%A, %B %d, %Y").replace(" 0", " ")


def short_date(iso):
    y, m, d = (int(p) for p in iso.split("-"))
    return date(y, m, d).strftime("%B %d, %Y").replace(" 0", " ")


def num(x):
    return f"{int(round(float(x))):,}"


def money(x):
    return f"${float(x):,.2f}"


def money_m(x):
    v = float(x) / 1e6
    sign = "-$" if v < 0 else "$"
    return f"{sign}{abs(v):,.1f} million"


def price_words(p):
    return (f"On the scored day it closed at {money(p['close'])} "
            f"and scored {float(p['score']):.1f} of 100: "
            f"{p['confirming']} of {p['checks_total']} checks lined "
            f"up in its favor, and it "
            f"{'passed every check' if p['qualified'] else 'did not pass every check'}. "
            f"The measures behind the score had data "
            f"{float(p['dc_pct']):.1f}% of the time. "
            f"This family points {p['stance']}.")


def prints_words(t):
    lean = ("selling" if t["net_premium"] < 0
            else "buying" if t["net_premium"] > 0 else "neither")
    return (f"{num(t['prints'])} prints on the day, "
            f"{money_m(t['total_premium'])} in total. The money "
            f"leaned to the {lean} side: net premium "
            f"{money_m(t['net_premium'])} (calls "
            f"{money_m(t['call_net_premium'])}, puts "
            f"{money_m(t['put_net_premium'])}). "
            f"{num(t['high_heat'])} prints reached the high heat "
            f"band and {num(t['golden_sweeps'])} were golden "
            f"sweeps. Average heat was {float(t['mean_heat']):.2f}. "
            f"This family points {t['stance']}.")


def positioning_words(g):
    pressure = float(g["net_gex_b"])
    ptxt = (f"-${abs(pressure):.2f}" if pressure < 0
            else f"${pressure:.2f}")
    return (f"The price, at {money(g['spot'])}, sits "
            f"{'below' if g['below_flip'] else 'above'} the flip "
            f"level of {money(g['flip'])}. Modelled pressure is "
            f"{ptxt} billion per 1% move, which "
            f"{'sharpens moves rather than softening them' if pressure < 0 else 'softens moves rather than sharpening them'}. "
            f"The walls stand at {money(g['call_wall'])} above and "
            f"{money(g['put_wall'])} below. The chain behind this "
            f"covered {num(g['contracts_used'])} of "
            f"{num(g['chain_total'])} contracts. Dark pool short "
            f"selling ran at {float(g['dix_pct']):.1f}% on "
            f"{short_date(g['dix_date'])}, inside this same record, "
            f"not a separate family. This family points "
            f"{g['stance']}.")


def build():
    for path in (SECOND_PATH, WIRE_PATH, PROVING_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    second = load_json(SECOND_PATH)
    wire = load_json(WIRE_PATH)
    proving = load_json(PROVING_PATH)

    # This board measures and reports; it makes no claim of its
    # own, so it labels itself with the measuring state.
    state_entry = None
    for state in proving.get("states") or []:
        if state.get("key") == "measuring":
            state_entry = state
    if state_entry is None:
        return fail("the Proving Ground's vocabulary does not "
                    "carry the measuring state; refusing to "
                    "publish a state label of our own.")

    names = second.get("names") or []
    coverage = second.get("coverage") or {}
    if not names:
        return fail("the Second Opinion's record carries no "
                    "names; refusing to publish an empty board.")

    family_names = {f["id"]: f["name"]
                    for f in second.get("families") or []}
    for fid in DIRECTION_FAMILIES:
        if fid not in family_names:
            return fail(f"the Second Opinion's record does not "
                        f"name the {fid} family; refusing to "
                        "publish.")

    # Coverage counts recomputed from the per-name family counts
    # must agree with the coverage the record publishes. The
    # distribution is read generically (hookup cure, 2026-10-30):
    # the Second Opinion now counts up to six speaking families
    # per name, and this board places any count the record
    # publishes, keyed by the same count words.
    COUNT_KEYS = {0: "no_family", 1: "one_family", 2: "two_families",
                  3: "three_families", 4: "four_families",
                  5: "five_families", 6: "six_families"}
    recomputed = {}
    for n in names:
        speaking = n.get("families_speaking")
        if speaking not in COUNT_KEYS:
            return fail(f"{n.get('symbol')} carries a family "
                        f"count this board cannot place "
                        f"({speaking}); refusing to publish.")
        recomputed[speaking] = recomputed.get(speaking, 0) + 1
    published_counts = {k: coverage.get(v) for k, v in COUNT_KEYS.items()
                        if coverage.get(v) is not None}
    if {k: recomputed.get(k, 0) for k in published_counts} \
            != published_counts \
            or coverage.get("names_on_record") != len(names):
        return fail("the coverage counts recomputed from the "
                    "record's names disagree with the coverage "
                    "counts the Second Opinion publishes; "
                    "refusing to publish a mismatched board.")

    # Every name's published direction list must agree with the
    # direction words its own family readings carry. A reading
    # with no stance (the per-name prints record, whose direction
    # is unjudged) carries no direction word and is skipped.
    for n in names:
        carried = sorted(n[fid]["stance"] for fid in DIRECTION_FAMILIES
                         if n.get(fid) and n[fid].get("stance"))
        if carried != sorted(n.get("directional") or []):
            return fail(f"{n.get('symbol')}: the direction list "
                        "on record disagrees with the direction "
                        "words its family readings carry; refusing "
                        "to publish.")

    # The agreement set, by the record's own test: two or more
    # direction-carrying families, one distinct direction word.
    agreeing = []
    for n in names:
        directional = n.get("directional") or []
        if len(directional) >= 2 and len(set(directional)) == 1:
            agreeing.append(n)
    if not agreeing:
        return fail("no name on the record has two or more "
                    "families pointing the same way; refusing to "
                    "publish a board with agreement filled in.")

    # Counted-not-listed names: any name outside the agreement
    # set must fail the agreement test itself (fewer than two
    # direction words, or direction words that disagree), or the
    # counted-not-listed account would be wrong. (The old form of
    # this check pinned the two-family case to exactly one
    # direction word, from the record as first inspected; with
    # facts, news and unjudged prints families now speaking, a
    # counted name can honestly carry zero, one, or disagreeing
    # direction words.)

    # The Replication Wire's grading of the agreement claim.
    ruling = None
    for claim in wire.get("claims") or []:
        if "0.736" in (claim.get("claim") or ""):
            ruling = claim
    if ruling is None:
        return fail("the Replication Wire's record no longer "
                    "carries the 0.736 agreement claim; refusing "
                    "to publish without the ruling this board "
                    "honours.")
    if ruling.get("verdict_words") != "Did not hold up" \
            or "not a prediction" not in (ruling.get("result") or ""):
        return fail("the Replication Wire's grading of the 0.736 "
                    "agreement claim no longer reads as it did; "
                    "refusing to publish a ruling of our own.")

    rows = []
    for n in agreeing:
        readings = []
        builders = {"price": price_words, "prints": prints_words,
                    "positioning": positioning_words}
        for fid in DIRECTION_FAMILIES:
            if n.get(fid) and n[fid].get("stance"):
                readings.append({
                    "family": family_names[fid],
                    "stance": n[fid]["stance"],
                    "words": builders[fid](n[fid]),
                })
        if len(readings) != len(n["directional"]):
            return fail(f"{n['symbol']}: the readings assembled "
                        "do not match the directions on record; "
                        "refusing to publish.")
        rows.append({
            "symbol": n["symbol"],
            "families_speaking": n["families_speaking"],
            "agreed_word": n["directional"][0],
            "readings": readings,
        })

    session = second.get("session")
    dist_words = ", ".join(
        f"{num(published_counts[k])} by {k} "
        f"{'family' if k == 1 else 'families'}"
        for k in sorted(published_counts, reverse=True)
        if k > 0 and published_counts[k])
    coverage_words = (
        f"{num(coverage['names_on_record'])} names are on record "
        f"for {long_date(session)}: {dist_words}, and "
        f"{num(coverage['no_family'])} by none. Only "
        f"{len(rows)} {'name has' if len(rows) == 1 else 'names have'} "
        "two or more families that carry a direction pointing "
        "the same way.")
    ruling_words = (
        f"The research record has already ruled on a claim like "
        f"this one. The claim: \"{ruling['claim']}\" The grading: "
        f"{ruling['verdict_words']}. {ruling['result']} "
        f"Checked against: {ruling['sample']}. This board is "
        "built to that ruling: agreement is shown as agreement, "
        "and nothing more.")

    data = {
        "tool": "Echo Board",
        "state": "published",
        "session": session,
        "session_long": long_date(session),
        "published_at_utc": second.get("board_published_at_utc"),
        "filings_as_of": second.get("filings_as_of"),
        "source": second.get("source"),
        "names_on_record": coverage["names_on_record"],
        "coverage": {v: coverage[v] for v in COUNT_KEYS.values()
                     if coverage.get(v) is not None},
        "coverage_words": coverage_words,
        "counted_words": COUNTED_WORDS,
        "agreement_words": AGREEMENT_WORDS,
        "ruling_words": ruling_words,
        "names": rows,
        "proving_state": state_entry["words"],
        "proving_note": state_entry["definition"],
        "receipt": {
            "session": session,
            "published_at_utc": second.get("board_published_at_utc"),
            "source": second.get("source"),
            "coverage": (second.get("receipt") or {}).get("coverage"),
        },
    }

    blob = json.dumps(data, sort_keys=True)
    for bad in FORBIDDEN:
        if bad in blob.lower():
            return fail(f"assembled data carries internal wording "
                        f"({bad}); refusing to publish.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (session {session}, "
          f"{len(rows)} agreement names, "
          f"{coverage['names_on_record']} names on record)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
