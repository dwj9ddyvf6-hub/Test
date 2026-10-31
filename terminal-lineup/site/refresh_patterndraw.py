#!/usr/bin/env python3
"""Refresh the Pattern Draw data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: two published records already on this site, read
exactly as published: the Strat Scanner's per-name bar-pattern
labels (each labelled name's labels for its last 5 sessions on
record, freshest session October 23, 2026, plus the completed
patterns the Scanner counts as finished on that freshest session),
and the AI Chart Read's shipped daily history (1,833 names, 399
sessions from March 25, 2025 to October 23, 2026), whose closes
draw the chart. The reader's browser draws the chart and places
each label marker from these shipped files; nothing is computed
or sent anywhere else.

Reconstruction choices (the exact construction):
- One marker per recorded label: a name's sequence carries one
  label for each of its last 5 sessions on record, and the page
  draws that label at that session's own position on the closes
  chart, on that session's closing price. No marker is drawn for
  any session the record does not cover, and no marker or line
  is drawn past the freshest recorded session (October 23, 2026).
- The Scanner's record carries labels only: its per-name records
  hold a label, a closing colour, a shape, a failed-2 flag, the
  completed pattern names, and the 5-session sequence. No price
  levels, pattern boundaries, triggers or targets are in the
  record, so this page draws label markers only and says plainly
  on the page that no levels are on record. If the record's shape
  ever changes to carry levels, this refresh stops (see below)
  rather than silently dropping them.
- Completed patterns are the Scanner's own names for patterns it
  counts as finished on the freshest session. They are printed
  beside the chart, dated to that session, with no line drawn.
- The non-repaint rule: a label belongs to the session it was
  recorded for and is drawn exactly there. Nothing on the page
  moves, extends, or redraws a past marking when newer data
  arrives, and the page says so in plain words.
- Names in the price history with no labels on record (16) ship
  in a plain list: the page draws their chart and prints a plain
  "no labels on record" line, with no marker.

Fail-closed rules:
- If the Scanner's published header counts disagree with its own
  groups in any check (labelled names, group counts, completed
  pattern count, failed-2 count, hammer and shooter counts), the
  refresh stops.
- If any per-name record carries a field outside the known
  label-only shape, or a sequence that is not exactly 5 sessions
  ending on the freshest session, or a label outside the four
  published labels, the refresh stops.
- If the chart history and the label record disagree (history's
  last session or session count against the Scanner's, the chart
  tool's own label copy against the Scanner's record name by
  name, a labelled name missing from the history, or a sequence
  session falling outside that name's own bars), the refresh
  stops.
- If the labelled and not-labelled counts do not add up to the
  names on record, the refresh stops.

Honesty rules:
- Dates are read off the sources, never from the clock: the
  session and the history's span come from the records
  themselves, so running this script twice produces the same
  file, byte for byte.
- Absence is not zero: a name with no labels on record ships in
  the not-labelled list and shows no marker.

Usage: python3 refresh_patterndraw.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STRAT_PATH = os.path.join(HERE, "strat-scanner", "data.json")
CHART_PATH = os.path.join(HERE, "ai-chart-read", "data.json")
OUT_PATH = os.path.join(HERE, "pattern-draw", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

SOURCE_WORDS = ("Daily closing prices from the consolidated tape "
                "records for the stocks in the daily scoring run, "
                "with the published bar-pattern labels for each "
                "name's last sessions on record")

PROVING_WORDS = "Still being proven"
PROVING_NOTE = ("Still being proven: the labels drawn here are the "
                "scanner's published labels, and they have no "
                "forward record yet. This page only draws each "
                "label on the session it was recorded for; nothing "
                "has graded what happened after a label, and the "
                "page makes no claim about what follows one.")

LEVELS_NOTE = ("No price levels are on record for these patterns. "
               "The record carries labels only, so this page draws "
               "label markers only and draws no pattern lines.")

NONREPAINT_WORDS = ("These markings do not move. Each label was "
                    "recorded for the session printed with it and "
                    "is drawn on that session, at that session's "
                    "closing price. When newer sessions are "
                    "recorded, their labels are added for those "
                    "sessions; a label already drawn is never "
                    "moved, redrawn, or stretched into a later "
                    "session.")

KNOWN_NAME_KEYS = {"symbol", "label", "colour", "shape",
                   "failed_2", "completed", "sequence"}
LABELS = {"1", "2u", "2d", "3"}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Pattern Draw refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (STRAT_PATH, CHART_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    strat = load_json(STRAT_PATH)
    chart = load_json(CHART_PATH)

    if strat.get("state") != "published" or not strat.get("session"):
        return fail("the label record is not published; refusing "
                    "to publish.")
    session = strat["session"]

    # --- Rebuild the label map from the Scanner's groups and
    # check every published count against it.
    labels = {}
    group_total = 0
    completed_total = 0
    failed_total = 0
    shape_counts = {"hammer": 0, "shooter": 0}
    completed_names = 0
    for group in strat.get("groups") or []:
        names = group.get("names") or []
        if group.get("count") != len(names):
            return fail(f"the label record's group "
                        f"{group.get('key')} says "
                        f"{group.get('count')} names but holds "
                        f"{len(names)}; refusing to publish.")
        group_total += len(names)
        for name in names:
            if set(name) != KNOWN_NAME_KEYS:
                return fail(f"{name.get('symbol')} carries fields "
                            f"outside the label-only record "
                            f"({sorted(set(name))}); if the record "
                            "now carries price levels this page "
                            "must be rebuilt to draw them; refusing "
                            "to publish.")
            symbol = name["symbol"]
            if symbol in labels:
                return fail(f"{symbol} appears twice in the label "
                            "record; refusing to publish.")
            seq = name["sequence"]
            if len(seq) != strat["sequence_sessions"]:
                return fail(f"{symbol} carries {len(seq)} sequence "
                            "sessions, not "
                            f"{strat['sequence_sessions']}; refusing "
                            "to publish.")
            if seq[-1]["date"] != session:
                return fail(f"{symbol}'s last labelled session is "
                            f"{seq[-1]['date']}, not the freshest "
                            f"session {session}; refusing to "
                            "publish.")
            dates = [s["date"] for s in seq]
            if dates != sorted(dates) or len(set(dates)) != len(dates):
                return fail(f"{symbol}'s labelled sessions are out "
                            "of order; refusing to publish.")
            for entry in seq:
                if entry["label"] not in LABELS:
                    return fail(f"{symbol} carries a label "
                                f"({entry['label']}) outside the "
                                "four published labels; refusing to "
                                "publish.")
            if name["label"] != seq[-1]["label"]:
                return fail(f"{symbol}'s freshest label disagrees "
                            "with its own sequence; refusing to "
                            "publish.")
            for pattern in name["completed"]:
                if not isinstance(pattern, str):
                    return fail(f"{symbol} carries a completed "
                                "pattern that is not a plain name; "
                                "refusing to publish.")
            completed_total += len(name["completed"])
            if name["completed"]:
                completed_names += 1
            if name["failed_2"]:
                failed_total += 1
            if name["shape"] in shape_counts:
                shape_counts[name["shape"]] += 1
            labels[symbol] = {
                "label": name["label"],
                "colour": name["colour"],
                "shape": name["shape"],
                "failed_2": name["failed_2"],
                "completed": name["completed"],
                "sequence": seq,
            }

    checks = [
        ("names_labelled", len(labels), strat["names_labelled"]),
        ("group names", group_total, strat["names_labelled"]),
        ("completed_patterns_count", completed_total,
         strat["completed_patterns_count"]),
        ("failed_2_count", failed_total, strat["failed_2_count"]),
        ("hammer count", shape_counts["hammer"],
         strat["shape_counts"]["hammer"]),
        ("shooter count", shape_counts["shooter"],
         strat["shape_counts"]["shooter"]),
    ]
    for what, got, published in checks:
        if got != published:
            return fail(f"the label record says {what}="
                        f"{published} but its own groups hold "
                        f"{got}; refusing to publish a mismatched "
                        "page.")

    # --- Cross-check the chart history against the label record.
    dates = chart["dates"]
    bars_in = chart["bars"]
    if chart["history_to"] != session or strat["history_to"] != session:
        return fail("the chart history and the label record end "
                    "on different sessions; refusing to publish.")
    if dates[-1] != session:
        return fail("the chart history's last dated session is "
                    f"{dates[-1]}, not {session}; refusing to "
                    "publish.")
    if len(dates) != strat["history_sessions_on_record"] \
            or len(dates) != chart["history_sessions"]:
        return fail("the chart history's session count disagrees "
                    "with the label record; refusing to publish.")
    if chart["history_from"] != strat["history_from"] \
            or dates[0] != chart["history_from"]:
        return fail("the chart history's first session disagrees "
                    "with the label record; refusing to publish.")
    if len(bars_in) != strat["names_on_record"]:
        return fail(f"the chart history holds {len(bars_in)} "
                    f"names but the label record counts "
                    f"{strat['names_on_record']} on record; "
                    "refusing to publish.")
    if len(labels) + strat["names_not_labelled"] != len(bars_in):
        return fail("the labelled and not-labelled counts do not "
                    "add up to the names on record; refusing to "
                    "publish.")

    # The chart tool's own label copy must match the Scanner's
    # record name by name.
    chart_labels = chart.get("labels") or {}
    if set(chart_labels) != set(labels):
        return fail("the chart history's label copy covers "
                    "different names than the label record; "
                    "refusing to publish.")
    for symbol, entry in labels.items():
        other = chart_labels[symbol]
        if other["sequence"] != entry["sequence"] \
                or other["label"] != entry["label"] \
                or other["completed"] != entry["completed"] \
                or other["shape"] != entry["shape"] \
                or other["failed_2"] != entry["failed_2"] \
                or other["colour"] != entry["colour"]:
            return fail(f"the chart history's label copy for "
                        f"{symbol} disagrees with the label "
                        "record; refusing to publish.")

    # Ship closes only, and check every labelled session falls
    # inside its own name's bars.
    date_pos = {d: i for i, d in enumerate(dates)}
    bars = {}
    for symbol in sorted(bars_in):
        start, closes = bars_in[symbol][0], bars_in[symbol][1]
        if not closes or start < 0 or start + len(closes) > len(dates):
            return fail(f"{symbol}'s closes do not fit the shared "
                        "calendar; refusing to publish.")
        bars[symbol] = [start, [float(c) for c in closes]]
    for symbol, entry in labels.items():
        if symbol not in bars:
            return fail(f"{symbol} is labelled but has no chart "
                        "history; refusing to publish.")
        start, closes = bars[symbol]
        for item in entry["sequence"]:
            pos = date_pos[item["date"]] - start
            if pos < 0 or pos >= len(closes):
                return fail(f"{symbol} has a label for "
                            f"{item['date']}, a session its own "
                            "chart does not cover; refusing to "
                            "publish.")

    unlabelled = sorted(set(bars) - set(labels))
    if len(unlabelled) != strat["names_not_labelled"]:
        return fail("the names with no labels on record do not "
                    "match the label record's count; refusing to "
                    "publish.")

    coverage = (
        f"Labels are on record for {len(labels):,} of the "
        f"{len(bars):,} names in the daily scoring run, for each "
        f"name's last {strat['sequence_sessions']} sessions on "
        f"record, {labels and min(s['date'] for e in labels.values() for s in e['sequence'])} "
        f"to {session}; {len(unlabelled)} names carry no labels "
        f"and show their chart with no marker. The price history "
        f"on record holds {len(dates)} sessions, from {dates[0]} "
        f"to {session}")

    data = {
        "tool": "Pattern Draw",
        "state": "published",
        "session": session,
        "source": SOURCE_WORDS,
        "proving_state": PROVING_WORDS,
        "proving_note": PROVING_NOTE,
        "history_sessions": len(dates),
        "history_from": dates[0],
        "history_to": session,
        "names_on_record": len(bars),
        "names_labelled": len(labels),
        "names_not_labelled": len(unlabelled),
        "sequence_sessions": strat["sequence_sessions"],
        "completed_patterns_count": strat[
            "completed_patterns_count"],
        "completed_names_count": completed_names,
        "failed_2_count": strat["failed_2_count"],
        "shape_counts": strat["shape_counts"],
        "levels_on_record": False,
        "levels_note": LEVELS_NOTE,
        "nonrepaint": NONREPAINT_WORDS,
        "label_meanings": chart["label_meanings"],
        "words": strat["words"],
        "dates": dates,
        "bars": bars,
        "labels": labels,
        "unlabelled": unlabelled,
        "coverage": coverage,
        "receipt": {
            "session": session,
            "source": SOURCE_WORDS,
            "coverage": coverage,
        },
    }

    data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
    blob = json.dumps(data, indent=1, sort_keys=True)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(blob)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (session {session}, "
          f"{len(labels):,} labelled of {len(bars):,}, "
          f"{completed_total} completed patterns over "
          f"{completed_names} names, {len(unlabelled)} with no "
          "labels)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
