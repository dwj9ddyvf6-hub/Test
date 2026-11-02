#!/usr/bin/env python3
"""Refresh the Opening Range Pane data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the real output of the opening-range study that is
on record: the published studies card for the freshest study run,
cross-checked against the published feed's copy of the same study
(the summary) and against the permanent log, whose freshest graded
opening-range entry must match the card exactly. The study was
computed from five-minute prices for SPY, QQQ and IWM over the
90 days of price history on record when it ran, completed trading
days only.

Reconstruction choices, stated as ours: (1) The freshest study run
on record is the one published; older runs (which counted
different breaks) stay in the log and are not mixed in. (2) The
first hour (60 minutes) is the headline range, as the tool's design
names it; the other windows the study counted (first 5, 15 and 30
minutes) are shown too, in order, because the study carries them
and they show how the record changes with a shorter range.
(3) How far past the range price travelled is shown as counts
recomputed from the study's stored shares and the number of days
that broke the range; a stored share must reproduce a whole count
exactly, or the refresh stops. (4) A breakdown cell with fewer
than 30 events is thin: the page shows its counts and no
percentage, because a percentage on a handful of events reads as
far more certain than it is. (5) Trading days per name is shown
only when the event total divides evenly across the names, which
is the shape the study's own counting produces (each name counted
once per trading day); otherwise that figure is left off rather
than guessed.

Non-claims: this page claims nothing about any future day. The
study counts a break the moment price trades past the range, even
if price later comes back inside it, and it does not record
whether a break held, where the day closed, or how far up versus
down the breaks went, so none of those is shown and none is
invented. The three names are counted together, as the study
counts them; no single-name split is shown because the study
carries none.

Fail-closed rules: if the studies card, the published feed's
summary of the same study, and the permanent log's freshest graded
opening-range entry disagree on any figure this page carries, or
if a window's own counts do not add up to its total, or if any
printed share does not recompute from its own counts, the refresh
stops and publishes nothing. All timestamps come from the
sources, never the clock, so running this script twice produces
the same file.

Usage: python3 refresh_openingrange.py
"""

import json
import os
from datetime import datetime
import re
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
CARD_PATH = os.path.join(SOURCE_DIR, "studies_card.json")
FEED_PATH = os.path.join(SOURCE_DIR, "morgue-feed.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
ENGINE_PATH = os.path.expanduser("~/workspace/morgue/studies_card.py")
STUDY_PATH = os.path.expanduser("~/workspace/morgue/studies.py")
OUT_PATH = os.path.join(HERE, "opening-range", "data.json")

MIN_EVENTS_FOR_PERCENT = 30
HEADLINE_WINDOW = 60
EXTENSION_WORDS = {
    "0.5": "Half the range or more",
    "1.0": "A full range or more",
    "1.5": "One and a half ranges or more",
}

SOURCE_WORDS = ("Five-minute prices for SPY, QQQ and IWM over the "
                "90 days of price history on record when the study "
                "ran, completed trading days only")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Opening Range refresh: {message}", file=sys.stderr)
    return 1


def share_cell(count, n):
    # Full precision, the way the study itself stores its shares:
    # rounding here and again on the page would double-round some
    # shares across a display boundary.
    thin = n < MIN_EVENTS_FOR_PERCENT
    return (None if thin else count / n), thin


def build():
    for path in (CARD_PATH, FEED_PATH, LOG_PATH, ENGINE_PATH,
                 STUDY_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    feed = load_json(FEED_PATH)
    orb = card.get("orb_ib") or {}

    # --- The study's universe, history depth and declared windows,
    # from the engines that ran it. ---
    engine_src = open(ENGINE_PATH, encoding="utf-8").read()
    m = re.search(r'INTRADAY_SYMBOLS\s*=\s*\(([^)]*)\)', engine_src)
    names = re.findall(r'"([A-Z]+)"', m.group(1)) if m else []
    m2 = re.search(r'INTRADAY_LOOKBACK_DAYS\s*=\s*(\d+)', engine_src)
    lookback_days = int(m2.group(1)) if m2 else None
    if not names or not lookback_days:
        return fail("the study engine does not declare its names "
                    "and history depth; refusing to publish a page "
                    "whose coverage is undeclared.")
    study_src = open(STUDY_PATH, encoding="utf-8").read()
    mw = re.search(r'WINDOWS\s*=\s*\(([^)]*)\)', study_src)
    windows_declared = [int(x) for x in
                        re.findall(r'\d+', mw.group(1))] if mw else []
    me = re.search(r'EXTENSIONS\s*=\s*\(([^)]*)\)', study_src)
    extensions_declared = [x.strip() for x in
                           me.group(1).split(",")] if me else []
    if not windows_declared or \
            sorted(str(w) for w in windows_declared) != sorted(orb):
        return fail("the windows the study engine declares do not "
                    "match the windows in the study on record; "
                    "refusing to publish a partial breakdown.")
    if sorted(extensions_declared) != sorted(EXTENSION_WORDS):
        return fail("the study engine declares extension steps "
                    "this page does not know; refusing to publish "
                    "a partial breakdown.")

    # --- The summary (the published feed's copy) must agree. ---
    feed_orb = (feed.get("studies") or {}).get("orb_ib")
    if feed_orb != orb:
        return fail("the published summary of the study disagrees "
                    "with the study card; refusing to publish a "
                    "mismatched page.")
    # --- The summary must be a copy of this card, not of an older
    # run: the feed's generation time must not precede the card's.
    # (The feed's as_of_session is the board's session date, a
    # different date kind from the study card's run date; comparing
    # them refused every coherent cycle. Cured 2026-10-30 in the
    # pattern of refresh_earningsdrift.py: exact figure agreement
    # above, plus generation order here.) ---
    try:
        card_ts = datetime.fromisoformat(card["generated_at"])
        feed_ts = datetime.fromisoformat(feed["generated_at_utc"])
        stale = feed_ts < card_ts
    except (KeyError, TypeError, ValueError):
        return fail("the study card and the published summary do "
                    "not both carry a generation time; refusing "
                    "to publish a summary whose run cannot be "
                    "bound to the card.")
    if stale:
        return fail("the published summary was generated "
                    f"{feed.get('generated_at_utc')} before the "
                    f"study card it copies "
                    f"({card.get('generated_at')}); refusing to "
                    "publish a stale summary.")

    # --- The permanent log's freshest graded opening-range entry
    # must match the card exactly. ---
    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]
    graded = [r for r in log_rows
              if r.get("component") == "study-orb-ib"
              and all((r.get("value") or {}).get(str(w), {})
                      .get("state") == "graded"
                      for w in windows_declared)]
    if not graded:
        return fail("the permanent log holds no completed "
                    "opening-range study; refusing to show a study "
                    "that is not on the record.")
    if graded[-1].get("value") != orb:
        return fail("the permanent log's freshest completed "
                    "opening-range study differs from the study "
                    "card; refusing to publish a mismatched page.")

    # --- Each window's own arithmetic must hold together. ---
    windows_out = []
    for w in windows_declared:
        win = orb[str(w)]
        if win.get("state") != "graded":
            return fail(f"the {w}-minute window on record is not "
                        f"a completed count (state "
                        f"{win.get('state')!r}); refusing to "
                        "publish figures that were not counted.")
        if win.get("window_min") != w:
            return fail(f"the study's {w}-minute window labels "
                        f"itself {win.get('window_min')}; refusing "
                        "to publish a mismatched page.")
        n = win["n"]
        one = win["break_one_side"]
        both = win["break_both"]
        none = win["no_break"]
        if n <= 0 or one + both + none != n:
            return fail(f"the {w}-minute window's counts do not "
                        f"add up ({one} one side + {both} both + "
                        f"{none} neither, of {n} days); refusing "
                        "to publish.")
        for key, count in (("break_one_side_rate", one),
                           ("break_both_rate", both),
                           ("no_break_rate", none)):
            if abs(win[key] - count / n) > 1e-9:
                return fail(f"the {w}-minute window's {key} does "
                            "not recompute from its own counts; "
                            "refusing to publish.")
        ext_n = win["extension_n"]
        if ext_n != one + both:
            return fail(f"the {w}-minute window counts extensions "
                        f"over {ext_n} breaking days but its own "
                        f"break counts give {one + both}; refusing "
                        "to publish.")
        extensions_out = []
        for step in extensions_declared:
            rate = win["extension_rates"][step]
            hits_exact = rate * ext_n
            hits = int(round(hits_exact))
            if abs(hits_exact - hits) > 1e-6:
                return fail(f"the {w}-minute window's {step}x "
                            "extension share does not reproduce a "
                            "whole count of days; refusing to "
                            "publish.")
            freq, thin = share_cell(hits, ext_n)
            extensions_out.append({
                "step": step,
                "label": EXTENSION_WORDS[step],
                "hits": hits,
                "n": ext_n,
                "frequency": freq,
                "thin": thin,
            })
        freq_one, thin_one = share_cell(one, n)
        freq_both, thin_both = share_cell(both, n)
        freq_none, thin_none = share_cell(none, n)
        windows_out.append({
            "window_min": w,
            "label": (f"First {w} minutes" if w != HEADLINE_WINDOW
                      else "First hour (60 minutes)"),
            "headline": w == HEADLINE_WINDOW,
            "n": n,
            "break_one_side": one,
            "break_one_side_frequency": freq_one,
            "break_one_side_thin": thin_one,
            "break_both": both,
            "break_both_frequency": freq_both,
            "break_both_thin": thin_both,
            "no_break": none,
            "no_break_frequency": freq_none,
            "no_break_thin": thin_none,
            "breaking_days": ext_n,
            "extensions": extensions_out,
        })

    headline = next(x for x in windows_out
                    if x["window_min"] == HEADLINE_WINDOW)
    n = headline["n"]

    # --- Trading days per name, only in the shape the counting
    # itself guarantees (see the register triple). ---
    days_per_name = None
    if all(x["n"] == n for x in windows_out) and n % len(names) == 0:
        days_per_name = n // len(names)

    data = {
        "tool": "Opening Range Pane",
        "state": "graded",
        "as_of": card["as_of"],
        "published_at_utc": card["generated_at"],
        "source": SOURCE_WORDS,
        "names": names,
        "name_count": len(names),
        "lookback_days": lookback_days,
        "days_per_name": days_per_name,
        "thin_threshold": MIN_EVENTS_FOR_PERCENT,
        "headline_window_min": HEADLINE_WINDOW,
        "windows": windows_out,
        "receipt": {
            "session": card["as_of"],
            "published_at_utc": card["generated_at"],
            "source": SOURCE_WORDS,
            "coverage": (f"{n} trading days counted across "
                         f"{len(names)} names "
                         f"({', '.join(names)}), from the "
                         f"{lookback_days} days of price history "
                         "on record when the study ran"),
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({n} days, headline first hour: "
          f"{headline['break_one_side']} one side, "
          f"{headline['break_both']} both, "
          f"{headline['no_break']} neither, "
          f"{len(names)} names, as of {card['as_of']}, "
          f"published {card['generated_at']})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
